from unittest.mock import MagicMock, patch
import pytest

pytestmark = pytest.mark.usefixtures('legacy_crawler_enabled')

from sqlalchemy import create_engine, insert, select
from sqlalchemy.orm import sessionmaker

from app.crawl_lock import (
    CRAWL_ALL_LOCK_KEY,
    acquire_crawl_all_lock,
    refresh_crawl_all_lock,
    release_crawl_all_lock,
)
from app.connectors.base import CrawlResult, CrawlRunData
from app.connectors.dedicated.fumarc import FumarcConnector
from app.database import Base
from app.models import Concurso, ConcursoPublication, CrawlRun, Source
from app.services import CrawlService
from app.tasks import crawl_active_sources


def _item(external_id: str, *, publication_hash: str | None = None) -> dict:
    publications = []
    if publication_hash:
        publications = [{
            'title': 'Convocação',
            'publication_type': 'convocacao',
            'publication_date': '2026-08-01T00:00:00+00:00',
            'link': f'https://example.com/{publication_hash}.pdf',
            'content_hash': publication_hash,
        }]
    return {
        'external_id': external_id,
        'banca': 'Test Banca',
        'orgao': 'Prefeitura de Teste',
        'titulo': f'Concurso Público {external_id}',
        'modalidade': 'Concurso Público',
        'cargo': 'Analista Administrativo',
        'area': 'administrativa',
        'cidade': 'Teste City',
        'uf': 'MG',
        'status': 'Inscrições abertas',
        'vagas': 10,
        'salario_min': None,
        'salario_max': None,
        'escolaridade': 'Superior',
        'taxa': None,
        'prova_data': None,
        'edital_numero': f'{external_id}/2026',
        'edital_data': None,
        'inscricao_inicio': None,
        'inscricao_fim': None,
        'link_pagina': f'https://example.com/concurso/{external_id}',
        'link_edital': None,
        'link_inscricao': None,
        'resumo': 'Concurso teste',
        'raw_data': {'publications': publications},
        'content_hash': f'concurso_hash_{external_id}',
        'fetched_at': None,
    }


def _make_db():
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def _add_source(db, name: str) -> Source:
    source = Source(
        name=name,
        base_url='https://example.com',
        list_url=f'https://example.com/{name.lower().replace(" ", "-")}',
        source_type='test_open',
        active=True,
    )
    db.add(source)
    db.commit()
    db.refresh(source)
    return source


def test_publication_pending_session_is_deduplicated():
    db = _make_db()
    try:
        source = _add_source(db, 'Pending Source')
        concurso = Concurso(source_id=source.id, **_item('pending'))
        db.add(concurso)
        db.commit()
        db.refresh(concurso)

        pending = ConcursoPublication(
            concurso_id=concurso.id,
            title='Convocação',
            content_hash='pending_hash',
        )
        db.add(pending)

        created = CrawlService(db)._sync_publications(
            concurso,
            _item('pending', publication_hash='pending_hash'),
        )

        assert created == []
        db.flush()
        assert db.execute(select(ConcursoPublication)).scalars().all() == [pending]
    finally:
        db.close()


def test_publication_unique_constraint_is_preserved():
    constraint_names = {
        constraint.name
        for constraint in ConcursoPublication.__table__.constraints
    }
    assert 'uq_concurso_publication_hash' in constraint_names


def test_fumarc_content_identity_ignores_sharepoint_transport_metadata():
    first = {
        'Id': 54,
        'Title': 'Concurso Público CREA - MG',
        'Modified': '2026-08-19T18:45:58Z',
        'OData__UIVersionString': '12.0',
        '__metadata': {'etag': '"12"', 'uri': 'https://example.test/items(54)'},
        'Edital': {
            'Url': 'https://example.test/edital.pdf',
            '__metadata': {'type': 'SP.FieldUrlValue'},
        },
    }
    second = {
        **first,
        'OData__UIVersionString': '16.0',
        '__metadata': {'etag': '"16"', 'uri': 'https://example.test/items(54)'},
    }

    assert FumarcConnector._stable_sharepoint_value(first) == FumarcConnector._stable_sharepoint_value(second)


def test_failed_source_rolls_back_and_next_source_can_run_without_pending_rollback():
    db = _make_db()
    try:
        failed_source = _add_source(db, 'Failed Source')
        next_source = _add_source(db, 'Next Source')
        failed_item = _item('failed')
        next_item = _item('next')

        connector = MagicMock()
        connector.crawl_with_diagnostics.side_effect = [
            CrawlResult(
                items=[failed_item],
                run_data=CrawlRunData(candidates_found=1, status='success'),
            ),
            CrawlResult(
                items=[next_item],
                run_data=CrawlRunData(candidates_found=1, status='success'),
            ),
        ]

        first_service = CrawlService(db)
        original_sync = first_service._sync_publications
        fail_once = True

        def force_publication_integrity_error(concurso, item):
            nonlocal fail_once
            if fail_once:
                fail_once = False
                first = ConcursoPublication(
                    concurso_id=concurso.id,
                    title='Convocação',
                    content_hash='forced_hash',
                )
                db.add(first)
                db.flush()
                db.add(ConcursoPublication(
                    concurso_id=concurso.id,
                    title='Convocação duplicada',
                    content_hash='forced_hash',
                ))
                db.flush()
            return original_sync(concurso, item)

        with patch('app.services.get_connector', return_value=connector):
            with patch.object(first_service, '_sync_publications', side_effect=force_publication_integrity_error):
                failed_result = first_service.crawl_source(failed_source.id)

            assert failed_result['status'] == 'failed'
            assert 'PendingRollbackError' not in failed_result['error']
            assert db.execute(select(Concurso).where(Concurso.source_id == failed_source.id)).scalars().all() == []

            next_result = first_service.crawl_source(next_source.id)

        assert next_result['status'] == 'success'
        assert db.execute(select(Concurso).where(Concurso.source_id == next_source.id)).scalars().all()
        runs = db.execute(select(CrawlRun).order_by(CrawlRun.id)).scalars().all()
        assert [run.status for run in runs] == ['failed', 'success']
    finally:
        db.close()


def test_crawl_all_sync_reports_isolated_failure_and_continues(monkeypatch):
    from app.main import run_crawl_all_sync

    db = _make_db()
    try:
        failed_source = _add_source(db, 'Sync Failed Source')
        next_source = _add_source(db, 'Sync Next Source')
        calls = []

        class FakeService:
            def __init__(self, session):
                self.db = session

            def crawl_source(self, source_id):
                calls.append(source_id)
                if source_id == failed_source.id:
                    # Leave the Session in failed state; the endpoint must
                    # rollback before touching the next source.
                    self.db.execute(insert(Source).values(
                        id=source_id,
                        name='duplicate',
                        base_url='https://duplicate.example',
                        list_url='https://duplicate.example',
                        source_type='test_open',
                        active=True,
                        frequency_minutes=360,
                    ))
                return {
                    'source_id': source_id,
                    'source_name': 'next',
                    'source_type': 'test_open',
                    'status': 'success',
                    'processed': 1,
                    'inserted': 1,
                    'updated': 0,
                    'unchanged': 0,
                    'versions_created': 1,
                    'notifications_created': 0,
                }

        monkeypatch.setattr('app.main.acquire_crawl_all_lock', lambda: 'sync-token')
        monkeypatch.setattr('app.main.release_crawl_all_lock', lambda token: None)
        monkeypatch.setattr('app.main.seed_master_sources', lambda session: None)
        monkeypatch.setattr('app.services.CrawlService', FakeService)

        result = run_crawl_all_sync(db)

        assert calls == [failed_source.id, next_source.id]
        assert result['status'] == 'partial_failure'
        assert len(result['success']) == 1
        assert result['success'][0]['source_id'] == next_source.id
        assert len(result['failed']) == 1
        assert result['failed'][0]['source_id'] == failed_source.id
        assert 'PendingRollbackError' not in result['failed'][0]['error']
    finally:
        db.close()


def test_celery_crawl_all_reports_isolated_failure_and_continues(monkeypatch):
    db = _make_db()
    try:
        failed_source = _add_source(db, 'Celery Failed Source')
        next_source = _add_source(db, 'Celery Next Source')
        failed_source_id = failed_source.id
        next_source_id = next_source.id
        calls = []

        class FakeService:
            def __init__(self, session):
                self.db = session

            def crawl_source(self, source_id):
                calls.append(source_id)
                if source_id == failed_source_id:
                    self.db.execute(insert(Source).values(
                        id=source_id,
                        name='duplicate',
                        base_url='https://duplicate.example',
                        list_url='https://duplicate.example',
                        source_type='test_open',
                        active=True,
                        frequency_minutes=360,
                    ))
                return {'source_id': source_id, 'status': 'success'}

        monkeypatch.setattr('app.tasks.SessionLocal', lambda: db)
        monkeypatch.setattr('app.tasks.acquire_crawl_all_lock', lambda token=None: 'celery-token')
        monkeypatch.setattr('app.tasks.release_crawl_all_lock', lambda token: None)
        monkeypatch.setattr('app.tasks.seed_master_sources', lambda session: None)
        monkeypatch.setattr('app.tasks.CrawlService', FakeService)

        result = crawl_active_sources.run()

        assert calls == [failed_source_id, next_source_id]
        assert result['status'] == 'partial_failure'
        assert [entry['source_id'] for entry in result['failed']] == [failed_source_id]
        assert [entry['source_id'] for entry in result['success']] == [next_source_id]
    finally:
        db.close()


class _FakeRedis:
    def __init__(self):
        self.value = None

    def get(self, key):
        return self.value if key == CRAWL_ALL_LOCK_KEY else None

    def set(self, key, value, *, nx, ex):
        if nx and self.value is not None:
            return None
        self.value = value
        return True

    def eval(self, script, number_of_keys, key, token, *args):
        if 'expire' in script:
            return 1 if self.value == token else 0
        if self.value == token:
            self.value = None
            return 1
        return 0


def test_crawl_all_lock_is_exclusive_and_token_owned(monkeypatch):
    fake_redis = _FakeRedis()
    monkeypatch.setattr('app.crawl_lock.get_redis_client', lambda: fake_redis)

    first_token = acquire_crawl_all_lock()
    assert first_token
    assert acquire_crawl_all_lock() is None
    assert refresh_crawl_all_lock(first_token)

    release_crawl_all_lock('wrong-token')
    assert fake_redis.value == first_token
    release_crawl_all_lock(first_token)
    assert fake_redis.value is None
    assert acquire_crawl_all_lock()


def test_enqueue_crawl_all_reserves_lock_and_transfers_token(monkeypatch):
    from app.main import enqueue_crawl_all

    task = MagicMock(id='task-id')
    celery_task = MagicMock()
    celery_task.delay.return_value = task
    monkeypatch.setattr('app.main.acquire_crawl_all_lock', lambda: 'reservation-token')
    seed = MagicMock()
    monkeypatch.setattr('app.main.seed_master_sources', seed)
    monkeypatch.setattr('app.main.crawl_active_sources', celery_task)

    db = MagicMock()
    result = enqueue_crawl_all(db)

    assert result == {
        'status': 'queued',
        'message': 'Coleta de todas as fontes ativas enfileirada',
        'task_id': 'task-id',
    }
    seed.assert_called_once_with(db)
    celery_task.delay.assert_called_once_with('reservation-token')
