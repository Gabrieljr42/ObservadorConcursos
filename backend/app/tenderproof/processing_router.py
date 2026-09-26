"""Authenticated local processing of an already-acquired owner artifact."""
import hashlib
from typing import Literal

from pydantic import BaseModel, ConfigDict

from fastapi import APIRouter, Depends, HTTPException

from app.auth import get_current_user
from app.models import User
from app.tenderproof.processing import ProcessingError, ProcessingLimits, get_processing_service
from app.tenderproof.store import get_store

router = APIRouter(prefix='/tenderproof/processing', tags=['tenderproof'])


class ProcessingRequest(BaseModel):
    model_config = ConfigDict(extra='forbid')
    operation: Literal['extract_pdf', 'ocr_pdf'] = 'extract_pdf'


def _call(method, *args, **kwargs):
    try:
        return method(*args, **kwargs)
    except ProcessingError as exc:
        code = str(exc)
        status = 404 if code in ('job_not_found', 'artifact_unavailable') else 409
        raise HTTPException(status_code=status, detail=code) from None


@router.post('/from-run/{run_id}', status_code=201)
def from_run(run_id: str, request: ProcessingRequest | None = None, user: User = Depends(get_current_user)):
    store = get_store()
    run = store.get_run(run_id)
    if not run or run.owner_user_id != user.id:
        raise HTTPException(status_code=404, detail='run_not_found')
    if not run.artifact:
        raise HTTPException(status_code=409, detail='artifact_unavailable')
    content = store.load_artifact_bytes(run.artifact)
    if content is None or hashlib.sha256(content).hexdigest() != run.artifact.sha256:
        raise HTTPException(status_code=409, detail='artifact_hash_mismatch')
    service = get_processing_service()
    operation = request.operation if request else 'extract_pdf'
    options = {'operation': operation}
    if operation == 'ocr_pdf':
        options['limits'] = ProcessingLimits(max_pages=200, max_bytes=30*1024*1024,
            total_seconds=120, operation_seconds=110, max_output_bytes=8*1024*1024)
    job = _call(service.enqueue, str(user.id), content, **options)
    service._mutate(job['id'], str(user.id), source_run_id=run_id)
    return service.get(job['id'], str(user.id))


@router.post('/recover')
def recover(user: User = Depends(get_current_user)):
    return {'recovered': get_processing_service().recover(owner_id=str(user.id))}


@router.get('/{job_id}')
def get_job(job_id: str, user: User = Depends(get_current_user)):
    return _call(get_processing_service().get, job_id, str(user.id))


@router.get('/{job_id}/result')
def result(job_id: str, user: User = Depends(get_current_user)):
    return _call(get_processing_service().result, job_id, str(user.id))


@router.post('/{job_id}/execute')
def execute(job_id: str, user: User = Depends(get_current_user)):
    return _call(get_processing_service().execute, job_id, str(user.id))


@router.post('/{job_id}/cancel')
def cancel(job_id: str, user: User = Depends(get_current_user)):
    return _call(get_processing_service().cancel, job_id, str(user.id))
