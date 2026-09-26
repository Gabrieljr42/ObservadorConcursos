from types import SimpleNamespace
import pytest
from fastapi import HTTPException
from sqlalchemy import func, select
from app.tenderproof.contracts import DocumentCandidate
from app.tenderproof.solari_adapter import DownloadedBytes
from app.tenderproof import review_cases as review
from app.tenderproof import publication
from app.models import ConcursoVersion, Notification
from app.tenderproof.publication_models import PublicationOutbox, PublicationProposal
from test_tenderproof_publication import env
from test_tenderproof_document_review_gate import checkpoint, manifest, EXTRA


def setup_case(env, existing_queue=None):
    _,_,_,_,run,store=env
    run.document.kind='consolidado'
    docs=manifest(env);docs[0]['kind']='consolidado'
    docs.append(dict(EXTRA,kind='retificacao'))
    queue = existing_queue or checkpoint(env,docs)[0]
    content=store.load_artifact_bytes(run.artifact)
    class Driver:
        settings=SimpleNamespace(limits=SimpleNamespace(max_download_bytes=30_000_000))
        adapter=SimpleNamespace(confirm_identity=lambda *args:None,
            documents=lambda *args:[DocumentCandidate(doc_id=str(i),title=d['title'],url_requested=d['url'],kind=d['kind']) for i,d in enumerate(docs)])
        def __init__(self,source,settings): pass
        def open_detail(self,url): return 'fixture'
        def download(self,url,**kwargs): return DownloadedBytes(url,url,content)
        def close(self): pass
    case=review.prepare(queue,store,run,driver_factory=Driver)
    decisions=[{'sha256':run.artifact.sha256,'page':1,'snippet':case['documents'][0]['pages'][0]['text'][:60],
        'effect':'reflected_in_selected_document','reason':'Os campos conferidos constam no edital consolidado preservado.'}]
    return queue,case,decisions


def test_interrupted_preparation_reuses_completed_processing_on_resume(env, monkeypatch):
    from app.tenderproof import processing
    from app.tenderproof.continuous_store import ContinuousStore
    original_extract=review.extract_pages_isolated
    original_execute=processing.ProcessingService.execute
    calls=[];executions=[]
    def interrupted(*args,**kwargs):
        calls.append(kwargs)
        if len(calls)==2:
            raise TimeoutError('interrupted after first document')
        return original_extract(*args,**kwargs)
    def counted(self,*args,**kwargs):
        executions.append(args[0])
        return original_execute(self,*args,**kwargs)
    monkeypatch.setattr(review,'extract_pages_isolated',interrupted)
    monkeypatch.setattr(processing.ProcessingService,'execute',counted)
    with pytest.raises(HTTPException,match='retomar') as failure:
        setup_case(env)
    assert failure.value.status_code==409 and len(executions)==1
    queue=ContinuousStore()
    assert review.current(queue,env[4]) is None
    queue,case,_=setup_case(env,existing_queue=queue)
    assert len(executions)==1  # Both fixture documents contain identical bytes.
    assert len(case['documents'])==2 and case['approved_at'] is None
    assert queue.review_for_run(env[4])['pending']


def test_approval_clears_only_reviewed_revision_and_is_idempotent(env):
    queue,case,decisions=setup_case(env);run=env[4];store=env[5]
    result=review.approve(queue,store,run,case['id'],case['revision_hash'],decisions)
    assert not queue.review_for_run(run)['pending']
    assert review.approve(queue,store,run,case['id'],case['revision_hash'],decisions)==result
    publication._assert_document_review_clear(run,queue=queue)
    checkpoint(env,manifest(env)+[EXTRA,dict(EXTRA,url=EXTRA['url']+'?new=1')],now=4000)
    with pytest.raises(HTTPException):publication._assert_document_review_clear(run,queue=queue)


def test_approved_review_noop_does_not_create_publication_or_notifications(env):
    queue, case, decisions = setup_case(env)
    db = env[0]
    before = tuple(db.scalar(select(func.count()).select_from(model)) for model in
                   (PublicationProposal, ConcursoVersion, PublicationOutbox, Notification))
    review.approve(queue, env[5], env[4], case['id'], case['revision_hash'], decisions)
    after = tuple(db.scalar(select(func.count()).select_from(model)) for model in
                  (PublicationProposal, ConcursoVersion, PublicationOutbox, Notification))
    assert after == before == (0, 0, 0, 0)


def test_old_interpretation_cannot_approve_or_reuse_clearance(env, monkeypatch):
    queue,case,decisions=setup_case(env);run=env[4];store=env[5]
    original=review.METHOD_VERSION
    monkeypatch.setattr(review,'METHOD_VERSION','next-interpretation')
    assert review.current(queue,run) is None
    with pytest.raises(HTTPException,match='interpretação'):
        review.approve(queue,store,run,case['id'],case['revision_hash'],decisions)
    monkeypatch.setattr(review,'METHOD_VERSION',original)
    review.approve(queue,store,run,case['id'],case['revision_hash'],decisions)
    monkeypatch.setattr(review,'METHOD_VERSION','next-interpretation')
    assert queue.review_for_run(run)['pending']
    with pytest.raises(HTTPException):publication._assert_document_review_clear(run,queue=queue)
    with queue._db() as db:
        assert review.approved_case(queue,run,db) is None
    # A fresh preparation and decision provide an ordinary UI resolution path.
    _, fresh, fresh_decisions=setup_case(env, existing_queue=queue)
    review.approve(queue,store,run,fresh['id'],fresh['revision_hash'],fresh_decisions)
    assert not queue.review_for_run(run)['pending']


def test_approval_without_annex_cannot_cover_later_supplementary_bytes(env):
    from app.tenderproof.contracts import SupplementaryDocument
    queue,case,decisions=setup_case(env)
    run,store=env[4],env[5]
    review.approve(queue,store,run,case['id'],case['revision_hash'],decisions)
    with queue._db() as db:
        assert review.approved_case(queue,run,db)
    run.supplementary_documents=[SupplementaryDocument(
        document=DocumentCandidate(doc_id='annex',title='Anexo I - Quadro de cargos',kind='anexo',url_requested=run.artifact.url_requested),
        artifact=run.artifact.model_copy(update={'artifact_id':'annex'}))]
    with queue._db() as db:
        before=review.revision(queue,run,db)
        assert not review.approved_case(queue,run,db)
        run.supplementary_documents[0].artifact.sha256='b'*64
        after=review.revision(queue,run,db)
        assert before != after and review.digest(before) != review.digest(after)


def test_reviewed_consolidated_notice_can_reach_publication_proposal(env):
    env[4].document.title += ' - Retificado'
    queue,case,decisions=setup_case(env)
    db,_,user,contest,run,store=env
    review.approve(queue,store,run,case['id'],case['revision_hash'],decisions)
    proposal=publication.create_proposal(db,run=run,concurso_id=contest.id,user=user,store=store)
    assert 'titulo' in proposal['eligible_fields']
    assert proposal['state']=='proposed'


@pytest.mark.parametrize('tamper',['hash','snippet','missing','page'])
def test_invalid_review_cannot_clear_pending(env,tamper):
    queue,case,decisions=setup_case(env)
    if tamper=='hash':decisions[0]['sha256']='f'*64
    if tamper=='snippet':decisions[0]['snippet']='Texto não existente no documento preservado'
    if tamper=='page':decisions[0]['page']=999
    if tamper=='missing':decisions=[]
    with pytest.raises(HTTPException):review.approve(queue,env[5],env[4],case['id'],case['revision_hash'],decisions)
    assert queue.review_for_run(env[4])['pending']


def test_source_change_or_other_owner_cannot_approve_old_case(env):
    queue,case,decisions=setup_case(env)
    with pytest.raises(HTTPException):review.read(queue,case['id'],2)
    checkpoint(env,manifest(env)+[EXTRA,dict(EXTRA,url=EXTRA['url']+'?new=1')],now=4000)
    with pytest.raises(HTTPException):review.approve(queue,env[5],env[4],case['id'],case['revision_hash'],decisions)


def test_current_case_restores_prepared_bytes_but_not_other_owner_or_revision(env):
    queue,case,_=setup_case(env);run=env[4]
    assert review.current(queue,run)['documents']==case['documents']
    assert review.current(queue,run)['id']==case['id']
    assert review.current(queue,run.model_copy(update={'owner_user_id':2})) is None
    checkpoint(env,manifest(env)+[EXTRA,dict(EXTRA,url=EXTRA['url']+'?new=1')],now=4000)
    assert review.current(queue,run) is None


def test_current_case_does_not_offer_already_approved_documents(env):
    queue,case,decisions=setup_case(env);run=env[4]
    review.approve(queue,env[5],run,case['id'],case['revision_hash'],decisions)
    assert review.current(queue,run) is None


def test_prepared_fields_are_bound_to_each_preserved_document(env):
    queue,case,_=setup_case(env)
    assert case['extraction_method_version'] == review.METHOD_VERSION
    for document in case['documents']:
        assert document['fields']
        pages = {p['page_number']:p['text'] for p in document['pages']}
        for field in document['fields']:
            for evidence in field['evidence']:
                assert evidence['artifact_id'] == document['artifact']['artifact_id']
                assert evidence['document_sha256'] == document['artifact']['sha256']
                assert evidence['snippet'] in pages[evidence['page_number']]
    assert case['approved_at'] is None
    assert queue.review_for_run(env[4])['pending']


def test_scanned_review_keeps_ocr_provenance_without_native_field_claims(env, monkeypatch):
    from app.tenderproof.contracts import PageText
    operations = []
    def scanned(content, *, artifact_id, operation='extract_pdf', **kwargs):
        operations.append(operation)
        if operation == 'extract_pdf':
            return [PageText(artifact_id=artifact_id,page_number=1)],1,1,False,['sem texto']
        text = 'Inscrições de outro órgão: 16/08/2024 a 30/08/2024. Diário com atos em colunas.'
        return [PageText(artifact_id=artifact_id,page_number=1,text=text,char_count=len(text),
            extraction_method='ocr_tesseract',extractor_version='tenderproof-ocr-v1',
            processing_job_id='ocr-job',ocr={'review_required':True,'words':[{'text':'Inscrições','bbox':[10,20,30,40]}]})],1,1,False,[]
    monkeypatch.setattr(review,'extract_pages_isolated',scanned)
    queue,case,_ = setup_case(env)
    for document in case['documents']:
        assert document['ocr_review_required']
        page = document['pages'][0]
        assert page['processing_job_id'] == 'ocr-job'
        assert page['ocr']['words'][0]['bbox'] == [10,20,30,40]
        assert all(f['state'] != 'unknown' for f in document['fields'])
        assert not any(e.get('snippet') for f in document['fields'] for e in f['evidence'])
    assert operations == ['extract_pdf','ocr_pdf'] * len(case['documents'])
    assert case['approved_at'] is None
    assert queue.review_for_run(env[4])['pending']


def test_busy_processing_is_actionable_and_cannot_approve_review(env,monkeypatch):
    from app.tenderproof.processing import ProcessingError
    def busy(*args,**kwargs):
        assert kwargs['capacity_wait_s']==15
        raise ProcessingError('concurrency_limit')
    monkeypatch.setattr(review,'extract_pages_isolated',busy)
    with pytest.raises(HTTPException) as failure:
        setup_case(env)
    assert failure.value.status_code==409
    assert 'Processamento ocupado' in failure.value.detail


def test_review_respects_global_acquisition_and_preserves_other_lease(env,monkeypatch):
    from app.tenderproof import service
    original=service._ExecutionLease
    monkeypatch.setattr(service,'_ExecutionLease',lambda store,driver,**kw:original(store,driver))
    store=env[5]
    token=store.acquire_execution_lease(ttl_seconds=120)
    assert token
    try:
        with pytest.raises(HTTPException) as failure:
            setup_case(env)
        assert failure.value.status_code==409
        assert 'Outra coleta' in failure.value.detail
        assert store.renew_execution_lease(token,ttl_seconds=120)
    finally:
        store.release_execution_lease(token)
    available=store.acquire_execution_lease(ttl_seconds=120)
    assert available
    store.release_execution_lease(available)
