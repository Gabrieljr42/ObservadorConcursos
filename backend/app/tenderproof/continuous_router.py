"""Authenticated owner-scoped configuration, coverage and review observations."""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field
from typing import Literal

from app.auth import get_current_user
from app.database import get_db
from app.models import User
from app.tenderproof.continuous import CollectionPaused, ContinuousEngine, continuous_enabled, operator_authorized
from app.tenderproof.continuous_store import SOURCES, SourcePolicy, get_continuous_store
from app.tenderproof.source_adapters import SOURCE_ADAPTERS
from app.connectors.registry import MASTER_SOURCES
from app.tenderproof.contracts import Artifact

router=APIRouter(prefix="/tenderproof/continuous",tags=["tenderproof-continuous"])


def _source(source):
    if source not in SOURCES:
        raise HTTPException(422,"fonte ainda sem adaptador contínuo aprovado")


def _operator(user: User=Depends(get_current_user)):
    if not operator_authorized(user.id):
        raise HTTPException(403,"coleta contínua exige usuário na lista operacional TENDERPROOF_CONTINUOUS_OPERATOR_USER_IDS")
    return user


@router.get("/status")
def status(user: User=Depends(get_current_user)):
    return {"operationally_enabled":continuous_enabled(),"operator_authorized":operator_authorized(user.id),"publication_enabled":False,
            "sources":get_continuous_store().status(user.id)}


@router.get("/catalogue")
def catalogue(user: User=Depends(get_current_user)):
    """All catalogue entries, including those that cannot yet be collected."""
    return [{"number": index, "source": item.source_type, "name": item.name,
             "category": item.category, "listing_urls": list(item.list_urls),
             "adapter_registered": item.source_type in SOURCE_ADAPTERS,
             "adapter_implemented": item.source_type in SOURCE_ADAPTERS and getattr(SOURCE_ADAPTERS[item.source_type], "implementation_state", "implemented") == "implemented",
             "implementation_state": getattr(SOURCE_ADAPTERS[item.source_type], "implementation_state", "implemented") if item.source_type in SOURCE_ADAPTERS else "pending",
             "implementation_scope": getattr(SOURCE_ADAPTERS.get(item.source_type), "implementation_scope", None),
             "adapter": type(SOURCE_ADAPTERS[item.source_type]).__name__ if item.source_type in SOURCE_ADAPTERS else None,
             "homologation": "see_validation_matrix" if item.source_type in SOURCE_ADAPTERS else "pending_adapter",
             "mock_available": item.source_type in ("ibgp_open", "imeso_open")}
            for index, item in enumerate(MASTER_SOURCES, 1)]


@router.get("/metrics")
def metrics(user: User=Depends(get_current_user)):
    return get_continuous_store().metrics(user.id)


@router.put("/sources/{source}")
def configure(source: str,policy: SourcePolicy,user: User=Depends(_operator)):
    _source(source)
    try:
        return get_continuous_store().configure(user.id,source,policy)
    except ValueError as exc:
        raise HTTPException(422,str(exc)) from exc


@router.post("/sources/{source}/collect",status_code=202)
def collect(source: str,user: User=Depends(_operator)):
    _source(source)
    try:
        cycle=ContinuousEngine().enqueue(user.id,source,force=True)
    except CollectionPaused as exc:
        raise HTTPException(409,str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(422,str(exc)) from exc
    # The next scheduled tick dispatches the durable request. API success does
    # not depend on Redis availability and never opens a browser synchronously.
    return {"cycle_id":cycle,"status":"queued"}


class TrackInput(BaseModel):
    model_config=ConfigDict(extra="forbid")
    url: str=Field(max_length=2000)
    title: str | None=Field(default=None,max_length=500)


@router.post("/sources/{source}/tracked",status_code=201)
def track(source: str,payload: TrackInput,user: User=Depends(_operator)):
    _source(source)
    try:
        return {"candidate_key":ContinuousEngine().track(user.id,source,payload.url,payload.title)}
    except Exception as exc:
        raise HTTPException(422,"candidato conhecido precisa de URL oficial e configuração da fonte") from exc


@router.post("/sources/{source}/browser/reconcile")
def reconcile(source: str,user: User=Depends(_operator)):
    _source(source)
    try:
        return ContinuousEngine().reconcile_browser(user.id,source)
    except ValueError as exc:
        raise HTTPException(409,str(exc)) from exc


@router.get("/cycles/{cycle_id}")
def cycle(cycle_id: str,user: User=Depends(get_current_user)):
    result=get_continuous_store().cycle(cycle_id,user.id)
    if not result:
        raise HTTPException(404,"ciclo não encontrado")
    return result


def _recollection_run(run_id, user):
    from app.tenderproof.store import get_store
    run = get_store().get_run(run_id)
    if run is None or run.owner_user_id != user.id:
        raise HTTPException(404, 'execução não encontrada')
    return run


@router.get('/runs/{run_id}/recollection')
def recollection_status(run_id: str, user: User=Depends(get_current_user)):
    _recollection_run(run_id, user)
    return get_continuous_store().recollection(user.id, run_id)


@router.post('/runs/{run_id}/recollection', status_code=202)
def recollect_run(run_id: str, user: User=Depends(_operator)):
    run = _recollection_run(run_id, user)
    if not continuous_enabled():
        raise HTTPException(409, 'coleta contínua pausada')
    if run.execution_status not in ('completed', 'failed') or not run.selected_candidate_id:
        raise HTTPException(409, 'aguarde a conclusão da coleta e selecione um candidato')
    candidate = next((c for c in run.candidates if c.candidate_id == run.selected_candidate_id), None)
    if candidate is None or candidate.source != run.source:
        raise HTTPException(409, 'candidato da coleta anterior não corresponde à fonte')
    _source(run.source)
    try:
        SOURCE_ADAPTERS[run.source].validate_detail_url(candidate.detail_url_observed)
        return get_continuous_store().enqueue_recollection(user.id, run_id, candidate, run.mode)
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc


@router.get("/snapshots/{job_id}")
def snapshot(job_id: str,user: User=Depends(get_current_user)):
    result=get_continuous_store().snapshot(job_id,user.id)
    if not result:
        raise HTTPException(404,"snapshot não encontrado")
    # HTML is returned as JSON data, never rendered as trusted application HTML.
    return result


@router.get("/observations")
def observations(source: str | None=None,limit: int=Query(default=100,ge=1,le=200),
                 offset: int=Query(default=0,ge=0),user: User=Depends(get_current_user)):
    if source:
        _source(source)
    return get_continuous_store().observations(user.id,source=source,limit=limit,offset=offset)


@router.get('/document-review/{run_id}')
def document_review(run_id: str, user: User=Depends(get_current_user)):
    from app.tenderproof.store import get_store
    run = get_store().get_run(run_id)
    if run is None or run.owner_user_id != user.id:
        raise HTTPException(404, 'observação não encontrada')
    return get_continuous_store().review_for_run(run)


class DocumentEffectDecision(BaseModel):
    model_config = ConfigDict(extra='forbid')
    sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    page: int = Field(ge=1,le=1000)
    snippet: str = Field(min_length=20,max_length=6000)
    reason: str = Field(min_length=20,max_length=2000)
    effect: Literal['reflected_in_selected_document','no_field_change','field_changes']
    changes: list[dict] | None = Field(default=None, max_length=3)
    region_id: str | None = Field(default=None, pattern=r'^ocr-region-[a-f0-9]{64}$')
  
  
class DocumentEffectApproval(BaseModel):
    model_config = ConfigDict(extra='forbid')
    revision_hash: str = Field(pattern=r'^[a-f0-9]{64}$')
    decisions: list[DocumentEffectDecision] = Field(min_length=1,max_length=100)


class DocumentEffectDraftDecision(BaseModel):
    model_config = ConfigDict(extra='forbid')
    sha256: str = Field(pattern=r'^[a-f0-9]{64}$')
    page: int | None = Field(default=None, ge=1, le=1000)
    snippet: str = Field(default='', max_length=6000)
    reason: str = Field(default='', max_length=2000)
    effect: Literal['reflected_in_selected_document','no_field_change','field_changes'] | None = None
    changes: list[dict] | None = Field(default=None, max_length=3)
    region_id: str | None = Field(default=None, pattern=r'^ocr-region-[a-f0-9]{64}$')


class DocumentEffectDraft(BaseModel):
    model_config = ConfigDict(extra='forbid')
    revision_hash: str = Field(pattern=r'^[a-f0-9]{64}$')
    draft_revision: int = Field(ge=0)
    decisions: list[DocumentEffectDraftDecision] = Field(max_length=100)


def _review_run(run_id,user):
    from app.tenderproof.publication import authorize, _writes_enabled
    from app.tenderproof.store import get_store
    authorize(user)
    _writes_enabled()
    run=get_store().get_run(run_id)
    if run is None or run.owner_user_id!=user.id:
        raise HTTPException(404,'Observação não encontrada')
    return run


@router.post('/document-review/{run_id}/prepare')
def prepare_document_effects(run_id: str,user: User=Depends(_operator)):
    from app.tenderproof.review_cases import prepare
    from app.tenderproof.store import get_store
    return prepare(get_continuous_store(),get_store(),_review_run(run_id,user))


class PreservedReviewDocument(BaseModel):
    model_config = ConfigDict(extra='forbid')
    title: str = Field(min_length=1, max_length=500)
    url: str = Field(min_length=8, max_length=4000)
    kind: Literal['edital', 'consolidado', 'retificacao', 'prorrogacao', 'anexo', 'resultado', 'gabarito', 'outro']
    acquisition_request: dict | None = None
    file_format: Literal['pdf', 'xlsx'] = 'pdf'


class PreservedReviewRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    document: PreservedReviewDocument
    artifact: Artifact
    expected_page_count: int = Field(ge=1, le=1000)


@router.post('/document-review/{run_id}/prepare-preserved')
def prepare_preserved_document(run_id: str, body: PreservedReviewRequest, user: User=Depends(_operator)):
    from app.tenderproof.review_cases import prepare_preserved
    from app.tenderproof.store import get_store
    return prepare_preserved(get_continuous_store(), get_store(), _review_run(run_id, user),
                             document=body.document.model_dump(exclude_none=True), artifact=body.artifact,
                             expected_page_count=body.expected_page_count)


@router.get('/document-review/{run_id}/current')
def current_document_effects(run_id: str,user: User=Depends(_operator)):
    from app.tenderproof.review_cases import current
    return current(get_continuous_store(),_review_run(run_id,user))


class OCRRegionRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    revision_hash: str = Field(pattern=r'^[a-f0-9]{64}$')
    artifact_id: str = Field(min_length=1,max_length=128)
    page_number: int = Field(ge=1,le=1000)
    bounds: list[int] = Field(min_length=4,max_length=4)


@router.post('/document-review/{run_id}/cases/{case_id}/ocr-regions')
def prepare_ocr_region(run_id: str,case_id: str,body: OCRRegionRequest,user: User=Depends(_operator)):
    from app.tenderproof.ocr_regions import create_region
    from app.tenderproof.store import get_store
    return create_region(get_continuous_store(),get_store(),_review_run(run_id,user),case_id,
                         body.revision_hash,body.artifact_id,body.page_number,body.bounds)


@router.post('/document-review/{run_id}/cases/{case_id}/approve')
def approve_document_effects(run_id: str,case_id: str,body: DocumentEffectApproval,user: User=Depends(_operator)):
    from app.tenderproof.review_cases import approve
    from app.tenderproof.store import get_store
    return approve(get_continuous_store(),get_store(),_review_run(run_id,user),case_id,body.revision_hash,
                     [d.model_dump(exclude_none=True) for d in body.decisions])


class RegistrationTargetRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    revision_hash: str = Field(pattern=r'^[a-f0-9]{64}$')
    region_id: str = Field(pattern=r'^ocr-region-[a-f0-9]{64}$')


@router.post('/document-review/{run_id}/cases/{case_id}/registration-targets')
def compare_registration_targets(run_id: str, case_id: str, body: RegistrationTargetRequest,
                                 user: User=Depends(_operator), db=Depends(get_db)):
    from app.tenderproof.registration_targets import compare_catalogue
    from app.tenderproof.store import get_store
    return compare_catalogue(db, get_continuous_store(), get_store(), _review_run(run_id,user),
                             case_id, body.revision_hash, body.region_id)


@router.put('/document-review/{run_id}/cases/{case_id}/draft')
def save_document_effect_draft(run_id: str, case_id: str, body: DocumentEffectDraft, user: User=Depends(_operator)):
    from app.tenderproof.review_cases import save_draft
    return save_draft(get_continuous_store(), _review_run(run_id,user), case_id, body.revision_hash,
        body.draft_revision, [d.model_dump(exclude_none=True) for d in body.decisions])

class PreservedDocumentSelection(BaseModel):
    model_config = ConfigDict(extra='forbid')
    revision_hash: str = Field(pattern=r'^[a-f0-9]{64}$')
    artifact_id: str = Field(min_length=1,max_length=128)
    reason: str = Field(min_length=20,max_length=2000)


@router.post('/document-review/{run_id}/cases/{case_id}/select-document')
def select_review_document(run_id: str, case_id: str, body: PreservedDocumentSelection, user: User=Depends(_operator)):
    from app.tenderproof.document_selection import select_preserved
    from app.tenderproof.processing import ProcessingError
    from app.tenderproof.store import get_store
    try:
        return select_preserved(get_continuous_store(), get_store(), _review_run(run_id,user),
            case_id, body.revision_hash, body.artifact_id, body.reason)
    except ProcessingError as exc:
        if str(exc) == 'concurrency_limit':
            raise HTTPException(409, 'Há outro PDF em processamento. Aguarde e tente novamente; a extração anterior está preservada.') from exc
        raise HTTPException(409, 'Não foi possível processar integralmente os documentos preservados; a revisão permanece pendente.') from exc
