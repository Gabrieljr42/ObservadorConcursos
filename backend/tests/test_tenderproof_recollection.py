from concurrent.futures import ThreadPoolExecutor
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.auth import get_current_user
from app.models import User
from app.tenderproof.continuous_store import ContinuousStore, SourcePolicy
from app.tenderproof.source_adapters import get_source_adapter
from app.tenderproof.contracts import TenderProofRun, ExecutionStatus
from app.tenderproof.store import get_store
from app.tenderproof.continuous import ContinuousEngine
from app.tenderproof.mock_demo import build_mock_driver

SOURCE='ibgp_open'
URL='https://novo.ibgpconcursos.com.br/concurso.jsp?cod=42'

@pytest.fixture
def setup(monkeypatch):
    monkeypatch.setenv('TENDERPROOF_CONTINUOUS_ENABLED','true')
    monkeypatch.setenv('TENDERPROOF_CONTINUOUS_OPERATOR_USER_IDS','1')
    q=ContinuousStore()
    q.configure(1,SOURCE,SourcePolicy(enabled=True,mode='mock',min_request_gap_s=0))
    candidate=get_source_adapter(SOURCE).candidate_from_url(URL,'Concurso Prefeitura Municipal de Exemplo MG cod 42')
    run=TenderProofRun(run_id='previous',owner_user_id=1,source=SOURCE,mode='mock',
        execution_status=ExecutionStatus.COMPLETED,candidates=[candidate],selected_candidate_id=candidate.candidate_id)
    get_store().put_run(run)
    return q,run,candidate

def test_concurrent_requests_reuse_durable_job_and_preserve_prior_run(setup):
    q,run,candidate=setup
    before=get_store().get_run(run.run_id).model_dump_json()
    with ThreadPoolExecutor(max_workers=4) as pool:
        values=list(pool.map(lambda _:q.enqueue_recollection(1,run.run_id,candidate,'mock'), range(4)))
    assert len({v['job_id'] for v in values})==1
    assert len(q.cycle(values[0]['cycle_id'],1)['jobs'])==1
    assert ContinuousStore(q.path).recollection(1,run.run_id)==values[0]
    assert q.recollection(2,run.run_id) is None
    assert get_store().get_run(run.run_id).model_dump_json()==before

def test_processing_uses_normal_pipeline_and_keeps_source_scope_incomplete(setup):
    q,old,candidate=setup
    request=q.enqueue_recollection(1,old.run_id,candidate,'mock')
    engine=ContinuousEngine(queue=q,driver_factory=lambda *a,**kw:build_mock_driver())
    assert engine.process_job(request['job_id'])['status']=='succeeded'
    saved=q.recollection(1,old.run_id)
    new=get_store().get_run(saved['run_id'])
    assert new.run_id!=old.run_id and new.artifact and new.execution_status=='completed'
    assert new.coverage['parent_run_id']==old.run_id
    assert q.cycle(request['cycle_id'],1)['status']=='partial'
    assert q.observations(1)[0]['status']=='pending_review'
    assert q.enqueue_recollection(1,old.run_id,candidate,'mock')==saved

def test_active_cycle_and_limits_are_preserved(setup):
    q,old,candidate=setup
    q.configure(1,SOURCE,SourcePolicy(enabled=True,mode='mock',max_candidates=1))
    cycle=q.enqueue(1,SOURCE,get_source_adapter(SOURCE).listing_urls)
    request=q.enqueue_recollection(1,old.run_id,candidate,'mock')
    assert request['cycle_id']==cycle
    with pytest.raises(ValueError,match='limite'):
        q.enqueue_recollection(1,'another',candidate,'mock')
    assert len(q.cycle(cycle,1)['jobs'])==2

def test_requested_refresh_precedes_backlog_after_listing(setup):
    q,old,candidate=setup
    q.track(1,SOURCE,candidate)
    cycle=q.enqueue(1,SOURCE,get_source_adapter(SOURCE).listing_urls)
    request=q.enqueue_recollection(1,old.run_id,candidate,'mock')
    jobs=q.cycle(cycle,1)['jobs']
    listing=next(j for j in jobs if j['kind']=='listing')
    assert q.ready_jobs()[0]==listing['job_id']
    with q._db(write=True) as db:
        db.execute("UPDATE jobs SET status='succeeded' WHERE job_id=?",(listing['job_id'],))
    assert q.ready_jobs()[0]==request['job_id']

@pytest.mark.parametrize('enabled,mode',[(False,'mock'),(True,'real')])
def test_disabled_or_changed_mode_cannot_start(setup,enabled,mode):
    q,old,candidate=setup
    q.configure(1,SOURCE,SourcePolicy(enabled=enabled,mode=mode))
    with pytest.raises(ValueError):q.enqueue_recollection(1,old.run_id,candidate,'mock')
    assert q.recollection(1,old.run_id) is None

def test_api_owner_operator_and_terminal_state_guards(setup):
    import app.tenderproof.continuous_router as routes
    q,run,candidate=setup
    app=FastAPI();app.include_router(routes.router)
    client=TestClient(app)
    endpoint='/tenderproof/continuous/runs/previous/recollection'
    assert client.post(endpoint).status_code==401
    app.dependency_overrides[get_current_user]=lambda:User(id=2,email='other@example.test',password_hash='x')
    assert client.get(endpoint).status_code==404
    assert client.post(endpoint).status_code==403
    app.dependency_overrides[get_current_user]=lambda:User(id=1,email='owner@example.test',password_hash='x')
    run.execution_status=ExecutionStatus.PROCESSING;get_store().put_run(run)
    assert client.post(endpoint).status_code==409
    run.execution_status=ExecutionStatus.COMPLETED;get_store().put_run(run)
    first=client.post(endpoint)
    assert first.status_code==202
    assert client.post(endpoint).json()==first.json()
    assert client.get(endpoint).json()==first.json()

