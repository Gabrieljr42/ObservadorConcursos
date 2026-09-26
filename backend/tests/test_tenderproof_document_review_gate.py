"""Controlled complementary-document changes; disposable databases, no network."""
import hashlib
import json

import pytest
from fastapi import HTTPException
from sqlalchemy import func, select

from test_tenderproof_publication import env
from app.models import ConcursoVersion
from app.tenderproof import publication as pub
from app.tenderproof.continuous_store import ContinuousStore, SourcePolicy
from app.tenderproof.source_adapter_base import ListingPage
from app.tenderproof.publication_models import PublicationOutbox, PublicationProposal
from app.models import Notification


def checkpoint(env, documents, now=100, *, owner=1, mode=None, finish=True):
    run = env[4]
    candidate = run.candidates[0]
    queue = ContinuousStore()
    mode = mode or run.mode
    queue.configure(owner, candidate.source, SourcePolicy(enabled=True, mode=mode, max_attempts=1), now=now)
    cycle = queue.enqueue(owner, candidate.source, ['https://novo.ibgpconcursos.com.br/'], force=True, now=now)
    listing = next(j['job_id'] for j in queue.cycle(cycle,owner)['jobs'] if j['kind']=='listing')
    lease = queue.claim(listing, now=now)
    queue.complete_listing(lease, 'controlled listing', ListingPage(candidates=[candidate],terminal_evidence='controlled end'), now=now+1)
    detail = next(j['job_id'] for j in queue.cycle(cycle,owner)['jobs'] if j['kind']=='detail')
    lease = queue.claim(detail, now=now+2)
    queue.set_run_id(lease, run.run_id, now=now+2)
    queue.detail_checkpoint(lease, 'controlled detail', documents, now=now+2)
    if finish:
        signature=hashlib.sha256(json.dumps(documents,sort_keys=True).encode()).hexdigest()
        queue.complete_detail(lease,run.run_id,signature,{'validation_status':'valid','documents':documents},now=now+3)
    return queue, lease


def manifest(env):
    return [{'title':env[4].document.title,'url':env[4].document.url_requested,'kind':'edital'}]


EXTRA={'title':'Retificação 01 — prazo de inscrição','url':'https://novo.ibgpconcursos.com.br/retificacao42.pdf','kind':'outro'}


def test_initial_explicit_consolidated_and_amendment_require_review(env):
    docs=manifest(env)
    docs[0]['kind']='consolidado'
    amendment=dict(EXTRA,kind='retificacao')
    queue,_=checkpoint(env,docs+[amendment])
    review=queue.review_for_run(env[4])
    assert review['pending'] and review['documents']==docs+[amendment]


def test_manual_consolidated_cannot_bypass_review_without_checkpoint(env):
    db,_,user,contest,run,store=env
    run.document.kind='consolidado'
    with pytest.raises(HTTPException,match='revisão explícita'):
        pub.create_proposal(db,run=run,concurso_id=contest.id,user=user,store=store)


def test_pending_is_separate_durable_deduplicated_and_survives_disappearance(env):
    original=manifest(env)
    queue,_=checkpoint(env,original)
    assert not queue.review_for_run(env[4])['pending']
    for now in (4000,8000):
        queue,_=checkpoint(env,original+[EXTRA],now)
    review=ContinuousStore(queue.path).review_for_run(env[4])
    assert review['pending'] and review['documents']==[EXTRA] and review['detected_at']==4002
    observations=queue.observations(1)
    assert len(observations)==2
    assert all(o['summary']['validation_status']=='valid' and o['summary']['document_review']['pending'] for o in observations)
    checkpoint(env,original,12000)
    assert queue.review_for_run(env[4])==review


def test_prepare_replays_preserved_case_when_listing_disappears(env, monkeypatch):
    from app.tenderproof import review_cases
    from app.tenderproof.contracts import Artifact
    db, _, _, _, run, store = env
    queue, _ = checkpoint(env, manifest(env))
    checkpoint(env, manifest(env) + [EXTRA], now=4000)
    body = b"preserved amendment bytes"
    artifact = Artifact(artifact_id="review-id16-amendment", sha256=hashlib.sha256(body).hexdigest(),
                        byte_len=len(body), url_requested=EXTRA["url"], url_final=EXTRA["url"],
                        downloaded_at="2026-09-12T00:00:00Z")
    store.save_artifact_file(artifact, body)
    with queue._db() as db:
        current_revision = review_cases.revision(queue, run, db)
    case = {"id": "drc-preserved", "run_id": run.run_id, "identity": list(review_cases.identity(run)),
            "revision": current_revision, "revision_hash": "x",
            "documents": [{"document": EXTRA, "artifact": artifact.model_dump(mode="json")}],
            "approved_at": None}
    monkeypatch.setattr(review_cases, "current", lambda *_: case)
    def no_live_listing(*args, **kwargs):
        raise AssertionError("live listing must not be reopened for a preserved case")
    assert review_cases.prepare(queue, store, run, driver_factory=no_live_listing) is case


def test_prepare_does_not_replay_preserved_case_from_foreign_host(env, monkeypatch):
    from app.tenderproof import review_cases
    from app.tenderproof.contracts import Artifact
    _, _, _, _, run, store = env
    queue, _ = checkpoint(env, manifest(env))
    checkpoint(env, manifest(env) + [EXTRA], now=4000)
    body = b"preserved foreign bytes"
    foreign = dict(EXTRA, url="https://evil.example/retificacao.pdf")
    artifact = Artifact(artifact_id="review-foreign", sha256=hashlib.sha256(body).hexdigest(),
                        byte_len=len(body), url_requested=foreign["url"], url_final=foreign["url"],
                        downloaded_at="2026-09-12T00:00:00Z")
    store.save_artifact_file(artifact, body)
    with queue._db() as db:
        current_revision = review_cases.revision(queue, run, db)
    case = {"id": "drc-foreign", "run_id": run.run_id, "identity": list(review_cases.identity(run)),
            "revision": current_revision, "revision_hash": "x",
            "documents": [{"document": foreign, "artifact": artifact.model_dump(mode="json")}],
            "approved_at": None}
    monkeypatch.setattr(review_cases, "current", lambda *_: case)
    with pytest.raises(AssertionError, match="live listing"):
        review_cases.prepare(queue, store, run, driver_factory=lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("live listing")))


def test_prepare_does_not_replay_case_when_document_url_differs_from_artifact(env, monkeypatch):
    from app.tenderproof import review_cases
    from app.tenderproof.contracts import Artifact
    _, _, _, _, run, store = env
    queue, _ = checkpoint(env, manifest(env))
    checkpoint(env, manifest(env) + [EXTRA], now=4000)
    body = b"preserved mismatched-url bytes"
    artifact = Artifact(artifact_id="review-url-mismatch", sha256=hashlib.sha256(body).hexdigest(),
                        byte_len=len(body), url_requested=EXTRA["url"] + "?sig=other",
                        url_final=EXTRA["url"] + "?sig=other", downloaded_at="2026-09-12T00:00:00Z")
    store.save_artifact_file(artifact, body)
    with queue._db() as db:
        current_revision = review_cases.revision(queue, run, db)
    case = {"id": "drc-url-mismatch", "run_id": run.run_id, "identity": list(review_cases.identity(run)),
            "revision": current_revision, "revision_hash": "x",
            "documents": [{"document": EXTRA, "artifact": artifact.model_dump(mode="json")}],
            "approved_at": None}
    monkeypatch.setattr(review_cases, "current", lambda *_: case)
    with pytest.raises(AssertionError, match="live listing"):
        review_cases.prepare(queue, store, run, driver_factory=lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("live listing")))


def test_prepare_does_not_replay_case_with_cross_identity_payload(env, monkeypatch):
    from app.tenderproof import review_cases
    from app.tenderproof.contracts import Artifact
    _, _, _, _, run, store = env
    queue, _ = checkpoint(env, manifest(env))
    checkpoint(env, manifest(env) + [EXTRA], now=4000)
    body = b"cross identity bytes"
    artifact = Artifact(artifact_id="review-cross-identity", sha256=hashlib.sha256(body).hexdigest(),
                        byte_len=len(body), url_requested=EXTRA["url"], url_final=EXTRA["url"],
                        downloaded_at="2026-09-12T00:00:00Z")
    store.save_artifact_file(artifact, body)
    with queue._db() as db:
        current_revision = review_cases.revision(queue, run, db)
    case = {"id": "drc-cross-identity", "run_id": run.run_id,
            "identity": [999, run.source, run.mode, "foreign-candidate"],
            "revision": current_revision, "revision_hash": "x",
            "documents": [{"document": EXTRA, "artifact": artifact.model_dump(mode="json")}],
            "approved_at": None}
    monkeypatch.setattr(review_cases, "current", lambda *_: case)
    with pytest.raises(AssertionError, match="live listing"):
        review_cases.prepare(queue, store, run, driver_factory=lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("live listing")))


def test_prepare_does_not_replay_case_with_document_outside_pending(env, monkeypatch):
    from app.tenderproof import review_cases
    from app.tenderproof.contracts import Artifact
    _, _, _, _, run, store = env
    queue, _ = checkpoint(env, manifest(env))
    checkpoint(env, manifest(env) + [EXTRA], now=4000)
    body = b"extra document bytes"
    extra = dict(EXTRA, title="Other document", url="https://novo.ibgpconcursos.com.br/other.pdf")
    artifact = Artifact(artifact_id="review-extra-document", sha256=hashlib.sha256(body).hexdigest(),
                        byte_len=len(body), url_requested=extra["url"], url_final=extra["url"],
                        downloaded_at="2026-09-12T00:00:00Z")
    store.save_artifact_file(artifact, body)
    with queue._db() as db:
        current_revision = review_cases.revision(queue, run, db)
    case = {"id": "drc-extra-document", "run_id": run.run_id,
            "identity": list(review_cases.identity(run)), "revision": current_revision, "revision_hash": "x",
            "documents": [{"document": extra, "artifact": artifact.model_dump(mode="json")}],
            "approved_at": None}
    monkeypatch.setattr(review_cases, "current", lambda *_: case)
    with pytest.raises(AssertionError, match="live listing"):
        review_cases.prepare(queue, store, run, driver_factory=lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("live listing")))


def test_prepare_preserved_local_artifact_is_authenticated_idempotent_and_noop(env, monkeypatch):
    from app.tenderproof import review_cases
    from app.tenderproof.contracts import Artifact
    from app.tenderproof.mock_demo import PDF_PAGE_1, make_text_pdf
    db, _, _, _, run, store = env
    queue, _ = checkpoint(env, manifest(env))
    checkpoint(env, manifest(env) + [EXTRA], now=4000)
    content = make_text_pdf([PDF_PAGE_1])
    artifact = Artifact(artifact_id='review-local-id16', sha256=hashlib.sha256(content).hexdigest(),
                        byte_len=len(content), url_requested=EXTRA['url'], url_final=EXTRA['url'],
                        downloaded_at=run.artifact.downloaded_at, content_type='application/pdf')
    store.save_artifact_file(artifact, content)
    before = tuple(db.scalar(select(func.count()).select_from(model)) for model in
                   (PublicationProposal, ConcursoVersion, PublicationOutbox, Notification))
    first = review_cases.prepare_preserved(queue, store, run, document=EXTRA, artifact=artifact, expected_page_count=1)
    old_method = review_cases.METHOD_VERSION
    monkeypatch.setattr(review_cases, 'METHOD_VERSION', old_method + '-r22')
    recomputed = review_cases.prepare_preserved(queue, store, run, document=EXTRA, artifact=artifact, expected_page_count=1)
    second = review_cases.prepare_preserved(queue, store, run, document=EXTRA, artifact=artifact, expected_page_count=1)
    with pytest.raises(HTTPException, match='(diferente|divergente)'):
        review_cases.prepare_preserved(queue, store, run, document=EXTRA,
                                      artifact=artifact.model_copy(update={'sha256': 'a' * 64}), expected_page_count=1)
    after = tuple(db.scalar(select(func.count()).select_from(model)) for model in
                  (PublicationProposal, ConcursoVersion, PublicationOutbox, Notification))
    assert first['id'] != recomputed['id'] == second['id']
    assert recomputed['extraction_method_version'] == old_method + '-r22'
    assert first['documents'][0]['artifact']['sha256'] == artifact.sha256
    assert after == before == (0, 0, 0, 0)


def test_prepare_preserved_rejects_cross_run_pending_and_hash_drift(env):
    from app.tenderproof import review_cases
    from app.tenderproof.contracts import Artifact
    from app.tenderproof.mock_demo import make_text_pdf
    _, _, _, _, run, store = env
    queue, _ = checkpoint(env, manifest(env))
    checkpoint(env, manifest(env) + [EXTRA], now=4000)
    content = b'not a registered preserved PDF'
    artifact = Artifact(artifact_id='review-local-bad', sha256=hashlib.sha256(content).hexdigest(),
                        byte_len=len(content), url_requested=EXTRA['url'], url_final=EXTRA['url'],
                        downloaded_at=run.artifact.downloaded_at, content_type='application/pdf')
    with pytest.raises(HTTPException, match='Artefato preservado'):
        review_cases.prepare_preserved(queue, store, run, document=EXTRA, artifact=artifact, expected_page_count=1)
    other_pdf = make_text_pdf(['Outro concurso municipal, edital 99/2026, sem vínculo com a observação'])
    other = Artifact(artifact_id='review-local-other-contest', sha256=hashlib.sha256(other_pdf).hexdigest(),
                     byte_len=len(other_pdf), url_requested=EXTRA['url'], url_final=EXTRA['url'],
                     downloaded_at=run.artifact.downloaded_at, content_type='application/pdf')
    store.save_artifact_file(other, other_pdf)
    with pytest.raises(HTTPException, match='não corresponde'):
        review_cases.prepare_preserved(queue, store, run, document=EXTRA, artifact=other, expected_page_count=1)
    with pytest.raises(HTTPException, match='manifesto pendente'):
        review_cases.prepare_preserved(queue, store, run, document=dict(EXTRA, url=EXTRA['url'] + '?foreign=1'),
                                       artifact=artifact, expected_page_count=1)
    with pytest.raises(HTTPException, match='Coleta documental'):
        review_cases.prepare_preserved(queue, store, run.model_copy(update={'owner_user_id': 2}),
                                       document=EXTRA, artifact=artifact, expected_page_count=1)


def test_initial_historical_manifest_and_other_owner_do_not_block(env):
    checkpoint(env,manifest(env)+[EXTRA])
    assert not ContinuousStore().review_for_run(env[4])['pending']
    checkpoint(env,manifest(env),owner=2)
    checkpoint(env,manifest(env)+[EXTRA],4000,owner=2)
    assert not ContinuousStore().review_for_run(env[4])['pending']


@pytest.mark.parametrize('operation',['create','approve','apply'])
def test_current_pending_blocks_new_and_prepared_proposals_without_side_effects(env,operation):
    db,_,user,contest,run,store=env
    checkpoint(env,manifest(env))
    proposal=None
    if operation!='create':
        proposal=pub.create_proposal(db,run=run,concurso_id=contest.id,user=user,store=store)
    if operation=='apply':
        proposal=pub.approve_proposal(db,proposal_id=proposal['id'],proposal_hash=proposal['proposal_hash'],fields=['inscricao_fim'],user=user,store=store)
    checkpoint(env,manifest(env)+[EXTRA],4000,finish=False)
    with pytest.raises(HTTPException,match='') as exc:
        if operation=='create':
            pub.create_proposal(db,run=run,concurso_id=contest.id,user=user,store=store)
        elif operation=='approve':
            pub.approve_proposal(db,proposal_id=proposal['id'],proposal_hash=proposal['proposal_hash'],fields=['inscricao_fim'],user=user,store=store)
        else:
            pub.apply_proposal(db,proposal_id=proposal['id'],proposal_hash=proposal['proposal_hash'],user=user,store=store)
    assert exc.value.status_code==409
    db.refresh(contest)
    assert contest.inscricao_fim.day==19
    assert db.scalar(select(func.count()).select_from(ConcursoVersion))==0
    assert db.scalar(select(func.count()).select_from(PublicationOutbox))==0
    if proposal:
        current=pub.get_proposal(db,proposal['id'],user)
        assert current['document_review']['documents']==[EXTRA] and current['blockers']


def test_final_commit_rechecks_change_after_pdf_revalidation(env,monkeypatch):
    db,_,user,contest,run,store=env
    checkpoint(env,manifest(env))
    original=pub._commit_with_document_gate
    def race(db,run):
        checkpoint(env,manifest(env)+[EXTRA],4000)
        original(db,run)
    monkeypatch.setattr(pub,'_commit_with_document_gate',race)
    with pytest.raises(HTTPException) as exc:
        pub.create_proposal(db,run=run,concurso_id=contest.id,user=user,store=store)
    assert exc.value.status_code==409


def test_expiring_signed_link_is_not_document_change(env):
    doc=dict(EXTRA,url=EXTRA['url']+'?X-Amz-Signature=old&X-Amz-Expires=30')
    checkpoint(env,manifest(env)+[doc])
    checkpoint(env,manifest(env)+[dict(doc,url=EXTRA['url']+'?X-Amz-Signature=new&X-Amz-Expires=60')],4000)
    assert not ContinuousStore().review_for_run(env[4])['pending']


def test_review_endpoint_requires_auth_and_owns_the_run(env):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from app.auth import get_current_user
    from app.models import User
    from app.tenderproof.continuous_router import router
    from app.tenderproof.store import get_store
    app=FastAPI(); app.include_router(router)
    get_store().put_run(env[4])
    url='/tenderproof/continuous/document-review/'+env[4].run_id
    client=TestClient(app)
    assert client.get(url).status_code==401
    app.dependency_overrides[get_current_user]=lambda:env[2]
    assert client.get(url).json()=={'pending':False,'documents':[],'reason':'','detected_at':None}
    checkpoint(env,manifest(env))
    checkpoint(env,manifest(env)+[EXTRA],4000)
    assert client.get(url).json()['documents']==[EXTRA]
    app.dependency_overrides[get_current_user]=lambda:User(id=2)
    assert client.get(url).status_code==404


def test_upgrade_uses_existing_observation_manifest(env):
    queue,_=checkpoint(env,manifest(env))
    with queue._db(write=True) as db:
        db.execute('DROP TABLE document_review_state')
    # Constructor performs an additive upgrade; historical observation survives.
    queue=ContinuousStore(queue.path)
    checkpoint(env,manifest(env)+[EXTRA],4000)
    assert queue.review_for_run(env[4])['documents']==[EXTRA]


def test_checkpoint_transaction_failure_does_not_leave_false_pending(env,monkeypatch):
    queue,lease=checkpoint(env,manifest(env),finish=False)
    def fail(*args,**kwargs):
        raise OSError('controlled snapshot write failure')
    monkeypatch.setattr(queue,'_snapshot',fail)
    # Existing lease remains authoritative; the pending update must roll back
    # with the snapshot, not survive independently of its evidence.
    # checkpoint returned the lease in the original transaction.
    from app.tenderproof.continuous_store import LeaseLost
    with pytest.raises(LeaseLost):
        queue.detail_checkpoint(lease, 'new detail', manifest(env)+[EXTRA],now=10000)
    assert not queue.review_for_run(env[4])['pending']
    with pytest.raises(OSError):
        queue.detail_checkpoint(lease, 'new detail', manifest(env)+[EXTRA],now=104)
    assert not queue.review_for_run(env[4])['pending']


def test_second_principal_blocks_old_approved_proposal(env):
    db,_,user,contest,run,store=env
    checkpoint(env,manifest(env))
    proposal=pub.create_proposal(db,run=run,concurso_id=contest.id,user=user,store=store)
    proposal=pub.approve_proposal(db,proposal_id=proposal['id'],proposal_hash=proposal['proposal_hash'],fields=['inscricao_fim'],user=user,store=store)
    extra=dict(EXTRA,title='Edital de abertura adicional',kind='edital')
    queue,_=checkpoint(env,manifest(env)+[extra],4000,finish=False)
    assert queue.review_for_run(run)['documents']==[extra]
    with pytest.raises(HTTPException) as exc:
        pub.apply_proposal(db,proposal_id=proposal['id'],proposal_hash=proposal['proposal_hash'],user=user,store=store)
    assert exc.value.status_code==409


def test_mock_pending_cannot_leak_into_real_context(env):
    queue,_=checkpoint(env,manifest(env))
    checkpoint(env,manifest(env)+[EXTRA],4000)
    assert queue.review_for_run(env[4])['pending']
    assert not queue.review_for_run(env[4].model_copy(update={'mode':'real'}))['pending']


def finish_bytes(env, digest, now, *, selected=None):
    docs=manifest(env)
    queue,lease=checkpoint(env,docs,now,finish=False)
    summary={'validation_status':'valid','documents':docs,'artifact_sha256':digest}
    if selected:summary['selected_document']=selected
    queue.complete_detail(lease,'controlled-bytes-'+digest[:8],digest,summary,now=now+3)
    return queue


def test_same_url_changed_bytes_blocks_old_approval_and_deduplicates(env):
    db,_,user,contest,run,store=env
    first=run.artifact.sha256
    queue=finish_bytes(env,first,100)
    assert not queue.review_for_run(run)['pending']
    proposal=pub.create_proposal(db,run=run,concurso_id=contest.id,user=user,store=store)
    proposal=pub.approve_proposal(db,proposal_id=proposal['id'],proposal_hash=proposal['proposal_hash'],fields=['inscricao_fim'],user=user,store=store)
    second=hashlib.sha256(b'controlled changed acquired bytes').hexdigest()
    finish_bytes(env,second,4000)
    finish_bytes(env,second,8000)
    review=ContinuousStore(queue.path).review_for_run(run)
    assert len(review['documents'])==1
    change=review['documents'][0]
    assert change['url']==run.document.url_requested and change['change']=='bytes_changed'
    assert change['previous_sha256']==first and change['sha256']==second
    assert len(queue.observations(user.id))==2
    with pytest.raises(HTTPException) as exc:
        pub.apply_proposal(db,proposal_id=proposal['id'],proposal_hash=proposal['proposal_hash'],user=user,store=store)
    assert exc.value.status_code==409
    assert db.scalar(select(func.count()).select_from(ConcursoVersion))==0


def test_same_url_hash_upgrade_and_atomic_rollback(env):
    import sqlite3
    run=env[4]
    queue=finish_bytes(env,run.artifact.sha256,100)
    # Old volume has an observation with hash, but no byte-state table.
    with queue._db(write=True) as db:db.execute('DROP TABLE acquired_document_state')
    queue,lease=checkpoint(env,manifest(env),4000,finish=False)
    changed=hashlib.sha256(b'controlled new bytes').hexdigest()
    summary={'validation_status':'valid','documents':manifest(env),'artifact_sha256':changed}
    with queue._db(write=True) as db:
        db.execute("CREATE TRIGGER break_observation BEFORE INSERT ON observations BEGIN SELECT RAISE(ABORT,'controlled commit failure'); END")
    with pytest.raises(sqlite3.IntegrityError):
        queue.complete_detail(lease,'changed',changed,summary,now=4003)
    assert not queue.review_for_run(run)['pending']
    with queue._db(write=True) as db:
        assert db.execute('SELECT COUNT(*) FROM acquired_document_state').fetchone()[0]==0
        db.execute('DROP TRIGGER break_observation')
    queue.complete_detail(lease,'changed',changed,summary,now=4004)
    assert queue.review_for_run(run)['documents'][0]['previous_sha256']==run.artifact.sha256


def test_acquired_signed_url_rotation_with_same_hash_is_not_change(env):
    run=env[4]
    doc=manifest(env)[0]
    delimiter='&' if '?' in doc['url'] else '?'
    first=dict(doc,url=doc['url']+delimiter+'X-Amz-Signature=old')
    second=dict(doc,url=doc['url']+delimiter+'X-Amz-Signature=new')
    finish_bytes(env,run.artifact.sha256,100,selected=first)
    queue=finish_bytes(env,run.artifact.sha256,4000,selected=second)
    assert not queue.review_for_run(run)['pending']
    with queue._db() as db:
        assert db.execute('SELECT COUNT(*) FROM acquired_document_state').fetchone()[0]==1


def test_changed_preserved_bytes_hold_survives_processing_failure(env):
    from app.tenderproof.continuous_store import LeaseLost
    run=env[4]
    queue=finish_bytes(env,run.artifact.sha256,100)
    with queue._db() as db:
        previous=db.execute('SELECT last_valid_run_id FROM known_candidates').fetchone()[0]
    queue,lease=checkpoint(env,manifest(env),4000,finish=False)
    summary={'artifact_sha256':hashlib.sha256(b'controlled malformed replacement').hexdigest(),'selected_document':manifest(env)[0]}
    with pytest.raises(LeaseLost):
        queue.acquired_document_checkpoint(lease,'preserved-failed-run',summary,now=10000)
    assert not queue.review_for_run(run)['pending']
    queue.acquired_document_checkpoint(lease,'preserved-failed-run',summary,now=4003)
    queue.fail(lease,'processing_failed',retryable=False,now=4004)
    assert queue.review_for_run(run)['pending']
    with queue._db() as db:
        assert db.execute('SELECT last_valid_run_id FROM known_candidates').fetchone()[0]==previous


def test_supplementary_bytes_changed_with_main_unchanged_requires_review(env):
    run = env[4]
    annex = {'title':'Anexo I - Quadro de cargos','url':'https://novo.ibgpconcursos.com.br/anexo42.pdf','kind':'anexo'}
    docs = manifest(env) + [annex]
    old_hash = hashlib.sha256(b'old annex').hexdigest()
    new_hash = hashlib.sha256(b'changed annex').hexdigest()
    for now, digest in ((100,old_hash),(4000,old_hash),(8000,new_hash)):
        queue, lease = checkpoint(env,docs,now,finish=False)
        summary = {'documents':docs, 'selected_document':docs[0], 'artifact_sha256':run.artifact.sha256,
                   'supplementary_documents':[{'document':annex,'artifact_sha256':digest}]}
        queue.acquired_document_checkpoint(lease,run.run_id,summary,now=now+3)
        if digest == old_hash:
            assert not queue.review_for_run(run)['pending']
            queue.complete_detail(lease,run.run_id,str(now),summary,now=now+4)
        else:
            queue.fail(lease,'annex_processing_failed',retryable=False,now=now+4)
    review = ContinuousStore(queue.path).review_for_run(run)
    assert review['pending'] and len(review['documents'])==1
    change = review['documents'][0]
    assert change['url']==annex['url'] and change['change']=='bytes_changed'
    assert change['previous_sha256']==old_hash and change['sha256']==new_hash
    with queue._db() as db:
        assert db.execute('SELECT COUNT(*) FROM acquired_document_state').fetchone()[0]==2
