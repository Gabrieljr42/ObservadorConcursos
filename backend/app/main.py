from contextlib import asynccontextmanager
import logging

from fastapi import Depends, FastAPI, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.crawl_lock import (
    CrawlLockUnavailable,
    acquire_crawl_all_lock,
    release_crawl_all_lock,
)
from app.config import get_settings
from app.connectors import seed_master_sources
from app.database import Base, engine, get_db
from app.models import Concurso, ConcursoPublication, ConcursoVersion, CrawlRun, Source
from app.schemas import (
    ConcursoOut,
    ConcursoPublicationOut,
    ConcursoVersionOut,
    CrawlRunOut,
    SourceCreate,
    SourceMasterSeedOut,
    SourceOut,
    UpdateOut,
)
from app.schema_migrations import ensure_runtime_schema
from app.tasks import crawl_active_sources, crawl_source

settings = get_settings()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    ensure_runtime_schema(engine)
    yield


app = FastAPI(title=settings.app_name, lifespan=lifespan)


@app.get('/health')
def healthcheck() -> dict:
    return {
        'status': 'ok',
        'app': settings.app_name,
        'env': settings.app_env,
    }


def _version_to_update(version: ConcursoVersion) -> dict:
    concurso = version.concurso
    return {
        'id': version.id,
        'concurso_id': version.concurso_id,
        'change_type': version.change_type,
        'change_summary': version.change_summary,
        'captured_at': version.captured_at,
        'titulo': concurso.titulo if concurso else '',
        'banca': concurso.banca if concurso else '',
        'orgao': concurso.orgao if concurso else None,
        'cidade': concurso.cidade if concurso else None,
        'uf': concurso.uf if concurso else None,
        'area': concurso.area if concurso else None,
        'status': concurso.status if concurso else None,
    }


def _matches_user_preferences(preferences, concurso: Concurso) -> bool:
    if preferences is None:
        return True

    if preferences.ufs and (concurso.uf or '').upper() not in {str(uf).upper() for uf in preferences.ufs}:
        return False
    if preferences.bancas and not any(str(banca).lower() in (concurso.banca or '').lower() for banca in preferences.bancas):
        return False
    if preferences.cidades and not any(str(cidade).lower() in (concurso.cidade or '').lower() for cidade in preferences.cidades):
        return False

    haystack_parts = [
        concurso.titulo or '', concurso.orgao or '', concurso.cargo or '', concurso.area or '',
        concurso.cidade or '', concurso.uf or '', concurso.resumo or '',
    ]
    raw_data = concurso.raw_data or {}
    cargo_candidates = raw_data.get('cargo_candidates') or []
    if isinstance(cargo_candidates, list):
        haystack_parts.append(' '.join(str(item) for item in cargo_candidates[:100]))
    haystack = ' '.join(haystack_parts).lower()

    if preferences.areas:
        areas = {str(area).lower() for area in preferences.areas}
        current_area = (concurso.area or '').lower()
        if current_area not in areas and not any(area in haystack for area in areas):
            return False
    if preferences.cargo_keywords:
        if not any(str(keyword).lower() in haystack for keyword in preferences.cargo_keywords):
            return False
    if preferences.only_open and not is_concurso_open(concurso):
        return False
    return True


@app.get('/sources', response_model=list[SourceOut])
def list_sources(db: Session = Depends(get_db)):
    return db.execute(select(Source).order_by(Source.id.desc())).scalars().all()


@app.post('/sources', response_model=SourceOut, status_code=201)
def create_source(payload: SourceCreate, db: Session = Depends(get_db)):
    source = Source(
        name=payload.name,
        base_url=str(payload.base_url),
        list_url=str(payload.list_url) if payload.list_url else None,
        source_type=payload.source_type,
        active=payload.active,
        frequency_minutes=payload.frequency_minutes,
    )
    db.add(source)
    db.commit()
    db.refresh(source)
    return source


def _get_or_create_source(
    db: Session,
    *,
    name: str,
    base_url: str,
    list_url: str,
    source_type: str,
    frequency_minutes: int = 180,
) -> Source:
    existing = db.execute(
        select(Source).where(Source.source_type == source_type, Source.list_url == list_url)
    ).scalar_one_or_none()
    if existing:
        return existing
    source = Source(
        name=name,
        base_url=base_url,
        list_url=list_url,
        source_type=source_type,
        active=True,
        frequency_minutes=frequency_minutes,
    )
    db.add(source)
    db.commit()
    db.refresh(source)
    return source


@app.post('/sources/presets/ibfc-open', response_model=SourceOut, status_code=201)
def create_ibfc_open_preset(db: Session = Depends(get_db)):
    existing = db.execute(
        select(Source).where(Source.source_type == 'ibfc_open', Source.list_url == 'https://concursos.ibfc.org.br/index/abertos/')
    ).scalar_one_or_none()
    if existing:
        return existing

    source = Source(
        name='IBFC - Inscrições Abertas',
        base_url='https://concursos.ibfc.org.br',
        list_url='https://concursos.ibfc.org.br/index/abertos/',
        source_type='ibfc_open',
        active=True,
        frequency_minutes=180,
    )
    db.add(source)
    db.commit()
    db.refresh(source)
    return source


@app.post('/sources/presets/ibgp-open', response_model=SourceOut, status_code=201)
def create_ibgp_open_preset(db: Session = Depends(get_db)):
    return _get_or_create_source(
        db,
        name='IBGP - Inscrições Abertas',
        base_url='https://novo.ibgpconcursos.com.br',
        list_url='https://novo.ibgpconcursos.com.br/inscricoes_abertas.jsp',
        source_type='ibgp_open',
        frequency_minutes=180,
    )


@app.post('/sources/presets/ibgp-ongoing', response_model=SourceOut, status_code=201)
def create_ibgp_ongoing_preset(db: Session = Depends(get_db)):
    return _get_or_create_source(
        db,
        name='IBGP - Em Andamento',
        base_url='https://novo.ibgpconcursos.com.br',
        list_url='https://novo.ibgpconcursos.com.br/inscricoes_em_andamento.jsp',
        source_type='ibgp_ongoing',
        frequency_minutes=360,
    )


@app.post('/sources/presets/imeso-open', response_model=SourceOut, status_code=201)
def create_imeso_open_preset(db: Session = Depends(get_db)):
    return _get_or_create_source(
        db,
        name='IMESO - Concursos e Seletivos',
        base_url='https://portal.imeso.com.br',
        list_url='https://portal.imeso.com.br/edital',
        source_type='imeso_open',
        frequency_minutes=240,
    )


@app.post('/sources/presets/fundep-open', response_model=SourceOut, status_code=201)
def create_fundep_open_preset(db: Session = Depends(get_db)):
    return _get_or_create_source(
        db,
        name='FUNDEP - Gestão de Concursos',
        base_url='https://www.gestaodeconcursos.com.br',
        list_url='https://www.gestaodeconcursos.com.br/site/site/default.aspx',
        source_type='fundep_open',
        frequency_minutes=360,
    )



@app.post('/sources/presets/aocp-open', response_model=SourceOut, status_code=201)
def create_aocp_open_preset(db: Session = Depends(get_db)):
    return _get_or_create_source(
        db,
        name='Instituto AOCP - Inscrições Abertas',
        base_url='https://www.institutoaocp.org.br',
        list_url='https://www.institutoaocp.org.br',
        source_type='aocp_open',
        frequency_minutes=360,
    )


@app.post('/sources/presets/idecan-open', response_model=SourceOut, status_code=201)
def create_idecan_open_preset(db: Session = Depends(get_db)):
    return _get_or_create_source(
        db,
        name='IDECAN - Inscrições Abertas',
        base_url='https://idecan.org.br',
        list_url='https://idecan.org.br/category/concursos/inscricoes-abertas/',
        source_type='idecan_open',
        frequency_minutes=360,
    )


@app.post('/sources/presets/consulplan-open', response_model=SourceOut, status_code=201)
def create_consulplan_open_preset(db: Session = Depends(get_db)):
    return _get_or_create_source(
        db,
        name='CONSULPLAN - Concursos',
        base_url='https://institutoconsulplan.org.br',
        list_url='https://institutoconsulplan.org.br',
        source_type='consulplan_open',
        frequency_minutes=360,
    )


@app.post('/sources/presets/fumarc-open', response_model=SourceOut, status_code=201)
def create_fumarc_open_preset(db: Session = Depends(get_db)):
    return _get_or_create_source(
        db,
        name='FUMARC - Concursos',
        base_url='https://www.fumarc.com.br',
        list_url='https://www.fumarc.com.br/SitePages/Home.aspx',
        source_type='fumarc_open',
        frequency_minutes=720,
    )


@app.post('/sources/presets/next-bancas', response_model=list[SourceOut], status_code=201)
def create_next_bancas_presets(db: Session = Depends(get_db)):
    presets = [
        _get_or_create_source(
            db,
            name='Instituto AOCP - Inscrições Abertas',
            base_url='https://www.institutoaocp.org.br',
            list_url='https://www.institutoaocp.org.br',
            source_type='aocp_open',
            frequency_minutes=360,
        ),
        _get_or_create_source(
            db,
            name='IDECAN - Inscrições Abertas',
            base_url='https://idecan.org.br',
            list_url='https://idecan.org.br/category/concursos/inscricoes-abertas/',
            source_type='idecan_open',
            frequency_minutes=360,
        ),
        _get_or_create_source(
            db,
            name='CONSULPLAN - Concursos',
            base_url='https://institutoconsulplan.org.br',
            list_url='https://institutoconsulplan.org.br',
            source_type='consulplan_open',
            frequency_minutes=360,
        ),
        _get_or_create_source(
            db,
            name='FUMARC - Concursos',
            base_url='https://www.fumarc.com.br',
            list_url='https://www.fumarc.com.br/SitePages/Home.aspx',
            source_type='fumarc_open',
            frequency_minutes=720,
        ),
    ]
    return presets


@app.post('/sources/presets/mg-priority', response_model=list[SourceOut], status_code=201)
def create_mg_priority_presets(db: Session = Depends(get_db)):
    presets = [
        _get_or_create_source(
            db,
            name='IBGP - Inscrições Abertas',
            base_url='https://novo.ibgpconcursos.com.br',
            list_url='https://novo.ibgpconcursos.com.br/inscricoes_abertas.jsp',
            source_type='ibgp_open',
            frequency_minutes=180,
        ),
        _get_or_create_source(
            db,
            name='IMESO - Concursos e Seletivos',
            base_url='https://portal.imeso.com.br',
            list_url='https://portal.imeso.com.br/edital',
            source_type='imeso_open',
            frequency_minutes=240,
        ),
        _get_or_create_source(
            db,
            name='FUNDEP - Gestão de Concursos',
            base_url='https://www.gestaodeconcursos.com.br',
            list_url='https://www.gestaodeconcursos.com.br/site/site/default.aspx',
            source_type='fundep_open',
            frequency_minutes=360,
        ),
    ]
    return presets


@app.post('/sources/presets/seed-all', response_model=SourceMasterSeedOut, status_code=201)
def seed_all_master_sources(db: Session = Depends(get_db)):
    """Seed or synchronize all 99 master sources defined in the catalog into the database."""
    return seed_master_sources(db)


@app.get('/sources/{source_id}/runs', response_model=list[CrawlRunOut])
def list_source_runs(
    source_id: int,
    limit: int = Query(default=30, ge=1, le=100),
    db: Session = Depends(get_db),
):
    source = db.get(Source, source_id)
    if not source:
        raise HTTPException(status_code=404, detail='Fonte não encontrada')
    query = (
        select(CrawlRun)
        .where(CrawlRun.source_id == source_id)
        .order_by(CrawlRun.started_at.desc(), CrawlRun.id.desc())
        .limit(limit)
    )
    return db.execute(query).scalars().all()


@app.get('/runs/recent', response_model=list[CrawlRunOut])
def list_recent_runs(
    limit: int = Query(default=50, ge=1, le=200),
    status: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    query = select(CrawlRun).order_by(CrawlRun.started_at.desc(), CrawlRun.id.desc())
    if status:
        query = query.where(CrawlRun.status == status)
    return db.execute(query.limit(limit)).scalars().all()



@app.get('/concursos', response_model=list[ConcursoOut])
def list_concursos(
    source_id: int | None = Query(default=None),
    banca: str | None = Query(default=None),
    status: str | None = Query(default=None),
    uf: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    query = select(Concurso).order_by(Concurso.updated_at.desc(), Concurso.id.desc())

    if source_id is not None:
        query = query.where(Concurso.source_id == source_id)
    if banca:
        query = query.where(Concurso.banca.ilike(f'%{banca}%'))
    if status:
        query = query.where(Concurso.status.ilike(f'%{status}%'))
    if uf:
        query = query.where(Concurso.uf == uf.upper())

    query = query.limit(limit)
    return db.execute(query).scalars().all()


@app.get('/updates/recent', response_model=list[UpdateOut])
def list_recent_updates(
    limit: int = Query(default=50, ge=1, le=200),
    change_type: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    query = select(ConcursoVersion).order_by(ConcursoVersion.captured_at.desc(), ConcursoVersion.id.desc())
    if change_type:
        query = query.where(ConcursoVersion.change_type == change_type)
    versions = db.execute(query.limit(limit)).scalars().all()
    return [_version_to_update(version) for version in versions]


@app.get('/concursos/versions/recent', response_model=list[ConcursoVersionOut])
def list_recent_concurso_versions(
    limit: int = Query(default=50, ge=1, le=200),
    change_type: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    query = select(ConcursoVersion).order_by(ConcursoVersion.captured_at.desc(), ConcursoVersion.id.desc())
    if change_type:
        query = query.where(ConcursoVersion.change_type == change_type)
    return db.execute(query.limit(limit)).scalars().all()


@app.get('/concursos/{concurso_id}/versions', response_model=list[ConcursoVersionOut])
def list_concurso_versions(
    concurso_id: int,
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    concurso = db.get(Concurso, concurso_id)
    if not concurso:
        raise HTTPException(status_code=404, detail='Concurso não encontrado')
    query = (
        select(ConcursoVersion)
        .where(ConcursoVersion.concurso_id == concurso_id)
        .order_by(ConcursoVersion.captured_at.desc(), ConcursoVersion.id.desc())
        .limit(limit)
    )
    return db.execute(query).scalars().all()


@app.get('/concursos/{concurso_id}/publications', response_model=list[ConcursoPublicationOut])
def list_concurso_publications(
    concurso_id: int,
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    concurso = db.get(Concurso, concurso_id)
    if not concurso:
        raise HTTPException(status_code=404, detail='Concurso não encontrado')
    query = (
        select(ConcursoPublication)
        .where(ConcursoPublication.concurso_id == concurso_id)
        .order_by(ConcursoPublication.publication_date.desc().nullslast(), ConcursoPublication.created_at.desc())
        .limit(limit)
    )
    return db.execute(query).scalars().all()


@app.get('/concursos/{concurso_id}', response_model=ConcursoOut)
def get_concurso(concurso_id: int, db: Session = Depends(get_db)):
    concurso = db.get(Concurso, concurso_id)
    if not concurso:
        raise HTTPException(status_code=404, detail='Concurso não encontrado')
    return concurso


@app.delete('/sources/{source_id}/concursos')
def delete_concursos_from_source(source_id: int, db: Session = Depends(get_db)):
    source = db.get(Source, source_id)
    if not source:
        raise HTTPException(status_code=404, detail='Fonte não encontrada')
    concursos = db.execute(select(Concurso).where(Concurso.source_id == source_id)).scalars().all()
    deleted = len(concursos)
    for concurso in concursos:
        db.delete(concurso)
    db.commit()
    return {
        'source_id': source_id,
        'source_name': source.name,
        'deleted': deleted,
    }


@app.post('/crawl/all')
def enqueue_crawl_all(db: Session = Depends(get_db)):
    try:
        lock_token = acquire_crawl_all_lock()
    except CrawlLockUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    if lock_token is None:
        return {
            'status': 'already_running',
            'message': 'Já existe um crawl-all em execução',
        }

    try:
        # The database is the runtime source list.  Keep it aligned with the
        # 99-source catalog before snapshotting active sources so a fresh or
        # partially initialized installation cannot silently crawl only a
        # stale subset.
        seed_master_sources(db)
        task = crawl_active_sources.delay(lock_token)
    except Exception:
        db.rollback()
        try:
            release_crawl_all_lock(lock_token)
        except CrawlLockUnavailable:
            logger.exception('Could not release crawl-all reservation after enqueue failure')
        raise

    return {
        'status': 'queued',
        'message': 'Coleta de todas as fontes ativas enfileirada',
        'task_id': task.id,
    }


@app.post('/crawl/all/sync')
def run_crawl_all_sync(db: Session = Depends(get_db)):
    from app.services import CrawlService

    try:
        lock_token = acquire_crawl_all_lock()
    except CrawlLockUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    if lock_token is None:
        return {
            'status': 'already_running',
            'processed_sources': 0,
            'results': [],
            'success': [],
            'failed': [],
        }

    try:
        seed_master_sources(db)
        source_snapshots = [
            (source.id, source.name, source.source_type)
            for source in db.execute(
                select(Source).where(Source.active.is_(True)).order_by(Source.id.asc())
            ).scalars().all()
        ]
        results = []
        totals = {
            'processed': 0,
            'inserted': 0,
            'updated': 0,
            'unchanged': 0,
            'versions_created': 0,
            'notifications_created': 0,
            'failed': 0,
        }
        for source_id, source_name, source_type in source_snapshots:
            service = CrawlService(db)
            try:
                result = service.crawl_source(source_id)
            except Exception as exc:
                # Roll back before handling the next source.  Do not inspect
                # the ORM source snapshot after a failed transaction.
                db.rollback()
                result = {
                    'source_id': source_id,
                    'source_name': source_name,
                    'source_type': source_type,
                    'status': 'failed',
                    'error': f'{exc.__class__.__name__}: {str(exc)}',
                }

            results.append(result)
            if result.get('status') in {'failed', 'error'}:
                totals['failed'] += 1
            for key in totals:
                if key != 'failed':
                    totals[key] += int(result.get(key, 0) or 0)

        failed = [result for result in results if result.get('status') in {'failed', 'error'}]
        successful = [
            result for result in results
            if result.get('status') not in {'failed', 'error'}
        ]
        return {
            'status': 'partial_failure' if failed else 'success',
            'processed_sources': len(source_snapshots),
            **totals,
            'results': results,
            'success': successful,
            'failed': failed,
        }
    finally:
        try:
            release_crawl_all_lock(lock_token)
        except CrawlLockUnavailable:
            logger.exception('Could not release crawl-all sync lock')


# Alias without a dynamic path segment, useful for clients and to avoid route conflicts.
@app.post('/crawl-all')
def enqueue_crawl_all_alias(db: Session = Depends(get_db)):
    return enqueue_crawl_all(db)


@app.post('/crawl-all/sync')
def run_crawl_all_sync_alias(db: Session = Depends(get_db)):
    return run_crawl_all_sync(db)


@app.post('/crawl/{source_id}')
def enqueue_crawl(source_id: int, db: Session = Depends(get_db)):
    source = db.get(Source, source_id)
    if not source:
        raise HTTPException(status_code=404, detail='Fonte não encontrada')

    task = crawl_source.delay(source_id)
    return {
        'message': 'Coleta enfileirada',
        'task_id': task.id,
        'source_id': source_id,
    }


@app.post('/crawl/{source_id}/sync')
def run_crawl_sync(source_id: int, db: Session = Depends(get_db)):
    source = db.get(Source, source_id)
    if not source:
        raise HTTPException(status_code=404, detail='Fonte não encontrada')

    source_id = source.id
    source_name = source.name
    source_type = source.source_type

    from app.services import CrawlService

    service = CrawlService(db)
    try:
        result = service.crawl_source(source_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        db.rollback()
        return {
            'source_id': source_id,
            'source_name': source_name,
            'source_type': source_type,
            'status': 'failed',
            'error': f'{exc.__class__.__name__}: {str(exc)}',
            'processed': 0,
            'inserted': 0,
            'updated': 0,
            'unchanged': 0,
            'versions_created': 0,
            'notifications_created': 0,
        }
    return result


# -----------------------------------------------------------------------------
# User/Auth module - MVP backend for login, preferences, favorites and alerts
# -----------------------------------------------------------------------------
from datetime import datetime, timezone

from sqlalchemy.exc import IntegrityError

from app.auth import create_access_token, create_refresh_token, exchange_refresh_token, get_current_user, hash_password, verify_password
from app.models import Alert, FavoriteConcurso, Notification, User, UserPreference
from app.notifications import alert_matches_concurso, is_concurso_open, run_alerts_for_user
from app.schemas import (
    AlertCreate,
    AlertOut,
    AlertRunResult,
    AlertUpdate,
    AuthToken,
    FavoriteOut,
    NotificationOut,
    RefreshTokenIn,
    SyncCheckpointOut,
    UserLogin,
    UserOut,
    UserPreferenceIn,
    UserPreferenceOut,
    UserRegister,
)


def _normalize_email(email: str) -> str:
    return email.strip().lower()


def _normalize_uf(uf: str | None) -> str | None:
    return uf.strip().upper()[:2] if uf else None


def _is_concurso_open(concurso: Concurso) -> bool:
    return is_concurso_open(concurso)


def _alert_matches_concurso(alert: Alert, concurso: Concurso) -> bool:
    return alert_matches_concurso(alert, concurso)


@app.post('/auth/register', response_model=AuthToken, status_code=201)
def register_user(payload: UserRegister, db: Session = Depends(get_db)):
    email = _normalize_email(payload.email)
    if '@' not in email:
        raise HTTPException(status_code=422, detail='E-mail inválido')
    try:
        password_hash = hash_password(payload.password)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    user = User(name=payload.name.strip(), email=email, password_hash=password_hash)
    db.add(user)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail='E-mail já cadastrado') from exc
    db.refresh(user)

    token = create_access_token(user.id)
    refresh_token = create_refresh_token(db, user.id)
    return {'access_token': token, 'refresh_token': refresh_token, 'token_type': 'bearer', 'user': user}


@app.post('/auth/login', response_model=AuthToken)
def login_user(payload: UserLogin, db: Session = Depends(get_db)):
    email = _normalize_email(payload.email)
    user = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail='E-mail ou senha inválidos')
    if not user.is_active:
        raise HTTPException(status_code=403, detail='Usuário inativo')

    token = create_access_token(user.id)
    refresh_token = create_refresh_token(db, user.id)
    return {'access_token': token, 'refresh_token': refresh_token, 'token_type': 'bearer', 'user': user}


@app.post('/auth/refresh', response_model=AuthToken)
def refresh_access_token(payload: RefreshTokenIn, db: Session = Depends(get_db)):
    token, user = exchange_refresh_token(db, payload.refresh_token)
    return {'access_token': token, 'refresh_token': payload.refresh_token, 'token_type': 'bearer', 'user': user}


@app.get('/auth/me', response_model=UserOut)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@app.get('/sync/checkpoint', response_model=SyncCheckpointOut)
def get_sync_checkpoint(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Return one server snapshot for offline-first clients without starting a crawl."""
    concursos = db.execute(
        select(Concurso).order_by(Concurso.updated_at.desc(), Concurso.id.desc())
    ).scalars().all()
    publications = db.execute(
        select(ConcursoPublication).order_by(ConcursoPublication.created_at.desc(), ConcursoPublication.id.desc())
    ).scalars().all()
    versions = db.execute(
        select(ConcursoVersion)
        .options(selectinload(ConcursoVersion.concurso))
        .order_by(ConcursoVersion.captured_at.desc(), ConcursoVersion.id.desc())
    ).scalars().all()
    preferences = db.execute(
        select(UserPreference).where(UserPreference.user_id == current_user.id)
    ).scalar_one_or_none()
    favorites = db.execute(
        select(FavoriteConcurso)
        .options(selectinload(FavoriteConcurso.concurso))
        .where(FavoriteConcurso.user_id == current_user.id)
        .order_by(FavoriteConcurso.created_at.desc())
    ).scalars().all()
    alerts = db.execute(
        select(Alert).where(Alert.user_id == current_user.id).order_by(Alert.created_at.desc())
    ).scalars().all()
    notifications = db.execute(
        select(Notification)
        .options(selectinload(Notification.concurso))
        .where(Notification.user_id == current_user.id)
        .order_by(Notification.created_at.desc())
    ).scalars().all()

    recent_updates = [_version_to_update(version) for version in versions]
    active_alerts = [alert for alert in alerts if alert.active]
    my_updates: list[dict] = []
    for version in versions:
        concurso = version.concurso
        if not concurso:
            continue
        if active_alerts:
            if not any(alert_matches_concurso(alert, concurso) for alert in active_alerts):
                continue
        elif not _matches_user_preferences(preferences, concurso):
            continue
        my_updates.append(_version_to_update(version))

    return {
        'generated_at': datetime.now(timezone.utc),
        'user': current_user,
        'preferences': preferences,
        'concursos': concursos,
        'publications': publications,
        'versions': versions,
        'recent_updates': recent_updates,
        'my_updates': my_updates,
        'favorites': favorites,
        'alerts': alerts,
        'notifications': notifications,
    }


@app.get('/me/preferences', response_model=UserPreferenceOut | None)
def get_my_preferences(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.execute(select(UserPreference).where(UserPreference.user_id == current_user.id)).scalar_one_or_none()


@app.put('/me/preferences', response_model=UserPreferenceOut)
def upsert_my_preferences(
    payload: UserPreferenceIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    preferences = db.execute(select(UserPreference).where(UserPreference.user_id == current_user.id)).scalar_one_or_none()
    normalized_ufs = [uf.strip().upper() for uf in payload.ufs] if payload.ufs else None
    data = payload.model_dump()
    data['ufs'] = normalized_ufs

    if preferences is None:
        preferences = UserPreference(user_id=current_user.id, **data)
        db.add(preferences)
    else:
        for key, value in data.items():
            setattr(preferences, key, value)

    db.commit()
    db.refresh(preferences)
    return preferences


@app.get('/me/favorites', response_model=list[FavoriteOut])
def list_my_favorites(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.execute(
        select(FavoriteConcurso)
        .where(FavoriteConcurso.user_id == current_user.id)
        .order_by(FavoriteConcurso.created_at.desc())
    ).scalars().all()


@app.post('/me/favorites/{concurso_id}', response_model=FavoriteOut, status_code=201)
def add_my_favorite(
    concurso_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    concurso = db.get(Concurso, concurso_id)
    if not concurso:
        raise HTTPException(status_code=404, detail='Concurso não encontrado')

    existing = db.execute(
        select(FavoriteConcurso).where(
            FavoriteConcurso.user_id == current_user.id,
            FavoriteConcurso.concurso_id == concurso_id,
        )
    ).scalar_one_or_none()
    if existing:
        return existing

    favorite = FavoriteConcurso(user_id=current_user.id, concurso_id=concurso_id)
    db.add(favorite)
    db.commit()
    db.refresh(favorite)
    return favorite


@app.delete('/me/favorites/{concurso_id}', status_code=204)
def remove_my_favorite(
    concurso_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    favorite = db.execute(
        select(FavoriteConcurso).where(
            FavoriteConcurso.user_id == current_user.id,
            FavoriteConcurso.concurso_id == concurso_id,
        )
    ).scalar_one_or_none()
    if favorite:
        db.delete(favorite)
        db.commit()
    return None


@app.get('/me/alerts', response_model=list[AlertOut])
def list_my_alerts(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.execute(select(Alert).where(Alert.user_id == current_user.id).order_by(Alert.created_at.desc())).scalars().all()


@app.post('/me/alerts', response_model=AlertOut, status_code=201)
def create_my_alert(
    payload: AlertCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    alert = Alert(
        user_id=current_user.id,
        name=payload.name.strip(),
        active=payload.active,
        uf=_normalize_uf(payload.uf),
        cidade=payload.cidade.strip() if payload.cidade else None,
        banca=payload.banca.strip() if payload.banca else None,
        area=payload.area.strip() if payload.area else None,
        cargo_keyword=payload.cargo_keyword.strip() if payload.cargo_keyword else None,
        status=payload.status.strip() if payload.status else None,
        only_open=payload.only_open,
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert


@app.patch('/me/alerts/{alert_id}', response_model=AlertOut)
def update_my_alert(
    alert_id: int,
    payload: AlertUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    alert = db.execute(select(Alert).where(Alert.id == alert_id, Alert.user_id == current_user.id)).scalar_one_or_none()
    if not alert:
        raise HTTPException(status_code=404, detail='Alerta não encontrado')

    data = payload.model_dump(exclude_unset=True)
    if 'uf' in data:
        data['uf'] = _normalize_uf(data['uf'])
    for key, value in data.items():
        setattr(alert, key, value.strip() if isinstance(value, str) else value)

    db.commit()
    db.refresh(alert)
    return alert


@app.delete('/me/alerts/{alert_id}', status_code=204)
def delete_my_alert(
    alert_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    alert = db.execute(select(Alert).where(Alert.id == alert_id, Alert.user_id == current_user.id)).scalar_one_or_none()
    if alert:
        db.delete(alert)
        db.commit()
    return None


@app.get('/me/notifications', response_model=list[NotificationOut])
def list_my_notifications(
    unread_only: bool = Query(default=False),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = select(Notification).where(Notification.user_id == current_user.id).order_by(Notification.created_at.desc())
    if unread_only:
        query = query.where(Notification.read_at.is_(None))
    return db.execute(query).scalars().all()


@app.get('/me/updates', response_model=list[UpdateOut])
def list_my_updates(
    limit: int = Query(default=50, ge=1, le=200),
    change_type: str | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    alerts = db.execute(
        select(Alert).where(Alert.user_id == current_user.id, Alert.active.is_(True))
    ).scalars().all()
    preferences = db.execute(
        select(UserPreference).where(UserPreference.user_id == current_user.id)
    ).scalar_one_or_none()

    query = select(ConcursoVersion).order_by(ConcursoVersion.captured_at.desc(), ConcursoVersion.id.desc())
    if change_type:
        query = query.where(ConcursoVersion.change_type == change_type)

    # Pull extra rows and filter in Python because alert/preferences matching uses
    # raw_data.cargo_candidates and multi-area heuristics.
    versions = db.execute(query.limit(min(limit * 6, 500))).scalars().all()
    updates: list[dict] = []
    for version in versions:
        concurso = version.concurso
        if not concurso:
            continue
        if alerts:
            if not any(alert_matches_concurso(alert, concurso) for alert in alerts):
                continue
        else:
            if not _matches_user_preferences(preferences, concurso):
                continue
        updates.append(_version_to_update(version))
        if len(updates) >= limit:
            break
    return updates


@app.post('/me/notifications/{notification_id}/read', response_model=NotificationOut)
def mark_notification_read(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    notification = db.execute(
        select(Notification).where(Notification.id == notification_id, Notification.user_id == current_user.id)
    ).scalar_one_or_none()
    if not notification:
        raise HTTPException(status_code=404, detail='Notificação não encontrada')
    if notification.read_at is None:
        notification.read_at = datetime.utcnow()
        db.commit()
        db.refresh(notification)
    return notification


@app.post('/me/notifications/read-all')
def mark_all_notifications_read(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    notifications = db.execute(
        select(Notification).where(Notification.user_id == current_user.id, Notification.read_at.is_(None))
    ).scalars().all()
    now = datetime.utcnow()
    for notification in notifications:
        notification.read_at = now
    db.commit()
    return {'updated': len(notifications)}


@app.post('/me/alerts/run/sync', response_model=AlertRunResult)
def run_my_alerts_sync(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    alerts = db.execute(select(Alert).where(Alert.user_id == current_user.id, Alert.active.is_(True))).scalars().all()
    concursos = db.execute(select(Concurso).order_by(Concurso.updated_at.desc()).limit(500)).scalars().all()

    created = run_alerts_for_user(db, user_id=current_user.id, concursos=concursos)
    db.commit()
    return {'processed_alerts': len(alerts), 'created_notifications': created}
