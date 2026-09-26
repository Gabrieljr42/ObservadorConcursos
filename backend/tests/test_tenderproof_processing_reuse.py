import json
from dataclasses import replace
import pytest
from app.tenderproof import processing
from app.tenderproof.demo_pdf import make_text_pdf


def test_completed_processing_survives_service_reopen_and_rebinds_artifact(tmp_path, monkeypatch):
    monkeypatch.setenv('TENDERPROOF_PROCESSING_DIR',str(tmp_path))
    content=make_text_pdf(['Documento oficial legível com texto suficiente.'])
    first=processing.extract_pages_isolated(content,artifact_id='first',owner_id='one',reuse_completed=True)
    def no_execution(*args,**kwargs):
        pytest.fail('completed bytes were processed again')
    monkeypatch.setattr(processing.ProcessingService,'execute',no_execution)
    second=processing.extract_pages_isolated(content,artifact_id='new-download',owner_id='one',reuse_completed=True)
    assert second[0][0].processing_job_id==first[0][0].processing_job_id
    assert second[0][0].artifact_id=='new-download'
    assert second[0][0].text==first[0][0].text


def test_checkpoint_requires_owner_bytes_operation_version_and_limits(tmp_path):
    service=processing.ProcessingService(tmp_path)
    content=make_text_pdf(['A preserved notice.'])
    limits=processing.ProcessingLimits()
    job=service.enqueue('owner',content,limits=limits)
    assert service.execute(job['id'],'owner')['state']=='succeeded'
    assert service.completed_local('owner',content,'extract_pdf',limits)
    assert service.completed_local('other',content,'extract_pdf',limits) is None
    assert service.completed_local('owner',make_text_pdf(['Changed notice']),'extract_pdf',limits) is None
    assert service.completed_local('owner',content,'ocr_pdf',limits) is None
    assert service.completed_local('owner',content,'extract_pdf',replace(limits,max_pages=1)) is None
    service._mutate(job['id'],'owner',extractor_version='obsolete')
    assert service.completed_local('owner',content,'extract_pdf',limits) is None


def test_corrupted_checkpoint_is_never_returned(tmp_path):
    service=processing.ProcessingService(tmp_path);limits=processing.ProcessingLimits()
    content=make_text_pdf(['Original document'])
    job=service.enqueue('owner',content,limits=limits)
    assert service.execute(job['id'],'owner')['state']=='succeeded'
    (service._directory(job)/'output.json').write_text(json.dumps({'pages':[]}))
    with pytest.raises(processing.ProcessingError,match='artifact_hash_mismatch'):
        service.completed_local('owner',content,'extract_pdf',limits)
