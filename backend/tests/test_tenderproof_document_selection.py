from types import SimpleNamespace
import pytest
from fastapi import HTTPException
from test_tenderproof_publication import env
from test_tenderproof_document_review_gate import checkpoint, manifest
from app.tenderproof import review_cases as review
from app.tenderproof.document_selection import select_preserved
from app.tenderproof.contracts import DocumentCandidate
from app.tenderproof.solari_adapter import DownloadedBytes


def prepared(env):
    run,store=env[4:]
    store.put_run(run)
    docs=manifest(env)+[{'title':'Edital consolidado','url':run.artifact.url_requested+'?consolidado=1','kind':'consolidado'}]
    queue,_=checkpoint(env,docs)
    original=store.load_artifact_bytes(run.artifact)
    class Driver:
        settings=SimpleNamespace(limits=SimpleNamespace(max_download_bytes=30_000_000))
        adapter=SimpleNamespace(confirm_identity=lambda *a:None,
            documents=lambda *a:[DocumentCandidate(doc_id=str(i),title=d['title'],kind=d['kind'],url_requested=d['url']) for i,d in enumerate(docs)])
        def __init__(self,*a):pass
        def open_detail(self,*a):return 'fixture'
        def download(self,url,**kw):return DownloadedBytes(url,url,original+(b'\n%consolidated\n' if 'consolidado=1' in url else b''))
        def close(self):pass
    case=review.prepare(queue,store,run,driver_factory=Driver)
    target=next(d for d in case['documents'] if d['document']['kind']=='consolidado')
    return queue,case,target


def test_selection_keeps_original_and_requires_new_review(env):
    queue,case,target=prepared(env)
    run,store=env[4:]
    before=store.get_run(run.run_id).model_dump(mode='json')
    selected=select_preserved(queue,store,run,case['id'],case['revision_hash'],target['artifact']['artifact_id'],
        'Consolidado escolhido para conferir os efeitos da retificação.')
    assert selected.run_id != run.run_id
    assert selected.artifact.sha256 == target['artifact']['sha256']
    assert store.get_run(run.run_id).model_dump(mode='json') == before
    assert selected.document_selection['parent_run_id'] == run.run_id
    assert queue.review_for_run(selected)['pending']
    new_case=review.current(queue,selected)
    assert new_case and new_case['approved_at'] is None and new_case['id'] != case['id']
    assert new_case['selected_document_sha256'] == selected.artifact.sha256
    from app.tenderproof.publication import _assert_document_review_clear
    with pytest.raises(HTTPException): _assert_document_review_clear(selected,queue=queue)


@pytest.mark.parametrize('mutation',['artifact','revision','reason','kind'])
def test_selection_rejects_unreviewable_requests(env,mutation):
    queue,case,target=prepared(env)
    run,store=env[4:]
    artifact_id=target['artifact']['artifact_id']
    review_hash=case['revision_hash']
    reason='Consolidado escolhido para conferir as alterações publicadas.'
    if mutation=='artifact':artifact_id='foreign-artifact'
    if mutation=='revision':review_hash='b'*64
    if mutation=='reason':reason='curto'
    if mutation=='kind':artifact_id=case['documents'][0]['artifact']['artifact_id']
    with pytest.raises(HTTPException):select_preserved(queue,store,run,case['id'],review_hash,artifact_id,reason)
    assert queue.review_for_run(run)['pending']

@pytest.mark.parametrize('title,kind,accepted',[
    ('Edital consolidado com Errata n. 01','consolidado',True),
    ('Errata n. 01','consolidado',False),
    ('Edital com Errata n. 01','consolidado',False),
    ('Edital consolidado com Errata n. 01','edital',False),
    ('Resultado - Edital consolidado com Errata n. 01','consolidado',False),
])
def test_consolidation_reference_is_distinct_from_standalone_amendment(env,title,kind,accepted):
    from app.tenderproof.pdf_text import extract_pages
    from app.tenderproof.validation import validate_identity
    run,store=env[4:]
    pages,*_=extract_pages(store.load_artifact_bytes(run.artifact),artifact_id=run.artifact.artifact_id)
    result=validate_identity(candidate=run.candidates[0],pages=pages,document_title=title,
        document_url=run.artifact.url_final,document_kind=kind)
    assert (not result.errors) == accepted

@pytest.mark.parametrize('mutation',['bytes','source_revision','other_owner'])
def test_selection_rejects_changed_evidence_or_context(env,monkeypatch,mutation):
    queue,case,target=prepared(env)
    run,store=env[4:]
    if mutation=='bytes':
        load=store.load_artifact_bytes
        monkeypatch.setattr(store,'load_artifact_bytes',lambda a: b'changed' if a.artifact_id==target['artifact']['artifact_id'] else load(a))
    elif mutation=='source_revision':
        checkpoint(env,manifest(env)+[{'title':'Nova retificação','url':run.artifact.url_requested+'&new=1','kind':'retificacao'}],now=4000)
    else:
        run=run.model_copy(update={'owner_user_id':2})
    with pytest.raises(HTTPException):
        select_preserved(queue,store,run,case['id'],case['revision_hash'],target['artifact']['artifact_id'],
            'Consolidado escolhido para conferência dos campos e alterações.')


def test_retry_preserves_first_result_and_single_review(env):
    queue,case,target=prepared(env)
    run,store=env[4:]
    args=(queue,store,run,case['id'],case['revision_hash'],target['artifact']['artifact_id'],
          'Consolidado escolhido para conferência dos campos e alterações.')
    first=select_preserved(*args)
    first_case=review.current(queue,first)
    again=select_preserved(*args)
    assert again.model_dump(mode='json') == first.model_dump(mode='json')
    assert review.current(queue,again) == first_case
    with queue._db() as db:
        assert db.execute('SELECT count(*) FROM document_effect_cases WHERE run_id=?',(first.run_id,)).fetchone()[0] == 1


def test_retry_recovers_failure_between_run_and_review_commits(env,monkeypatch):
    queue,case,target=prepared(env)
    run,store=env[4:]
    args=(queue,store,run,case['id'],case['revision_hash'],target['artifact']['artifact_id'],
          'Consolidado escolhido para conferência dos campos e alterações.')
    schema=review._schema
    def fail(db):raise RuntimeError('simulated interruption')
    monkeypatch.setattr(review,'_schema',fail)
    with pytest.raises(RuntimeError,match='simulated interruption'):select_preserved(*args)
    with store._connection() as db:
        row=db.execute("SELECT payload FROM runs WHERE run_id LIKE 'tp-review-%'").fetchone()
    assert row
    from app.tenderproof.contracts import TenderProofRun
    committed=TenderProofRun.model_validate_json(row['payload'])
    monkeypatch.setattr(review,'_schema',schema)
    recovered=select_preserved(*args)
    assert recovered.model_dump(mode='json') == committed.model_dump(mode='json')
    assert review.current(queue,recovered)['approved_at'] is None


def test_simultaneous_selection_commits_only_one_result(env,monkeypatch):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier
    queue,case,target=prepared(env)
    run,store=env[4:]
    barrier=Barrier(2)
    # Exercise simultaneous commits independently of the one-job PDF sandbox.
    # Sequential/recovery tests above use the real isolated processor.
    from app.tenderproof.pdf_text import extract_pages
    monkeypatch.setattr('app.tenderproof.document_selection.extract_pages_isolated',
        lambda content, **kw: extract_pages(content, artifact_id=kw['artifact_id'], max_pages=kw['max_pages']))
    put=store.put_run_if_absent
    def coordinated(result):
        barrier.wait(timeout=30)
        return put(result)
    monkeypatch.setattr(store,'put_run_if_absent',coordinated)
    def select():
        return select_preserved(queue,store,run,case['id'],case['revision_hash'],target['artifact']['artifact_id'],
            'Consolidado escolhido para conferência dos campos e alterações.')
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures=[pool.submit(select) for _ in range(2)]
        errors=[f.exception(timeout=60) for f in futures]
        assert not any(errors), repr(errors)
        first,second=[f.result() for f in futures]
    assert first.model_dump(mode='json') == second.model_dump(mode='json')
    with queue._db() as db:
        assert db.execute('SELECT count(*) FROM document_effect_cases WHERE run_id=?',(first.run_id,)).fetchone()[0] == 1


def test_processing_busy_returns_retryable_message_without_new_run(env,monkeypatch):
    from app.tenderproof import continuous_router
    from app.tenderproof.processing import ProcessingError
    run,store=env[4:]
    monkeypatch.setattr(continuous_router,'_review_run',lambda *args:run)
    def busy(*args):raise ProcessingError('concurrency_limit')
    monkeypatch.setattr('app.tenderproof.document_selection.select_preserved',busy)
    body=continuous_router.PreservedDocumentSelection(revision_hash='a'*64,artifact_id='review-doc',
        reason='Consolidado escolhido para conferência dos campos e alterações.')
    with pytest.raises(HTTPException) as caught:
        continuous_router.select_review_document(run.run_id,'review-case',body,env[2])
    assert caught.value.status_code == 409 and 'Aguarde e tente novamente' in caught.value.detail
