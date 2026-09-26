"""Behavioral verification of durable work, coverage, retries and isolation."""
from dataclasses import replace
import json
import os
import sqlite3
import subprocess
import sys
import time

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.auth import get_current_user
from app.models import User
from app.tenderproof.continuous import ContinuousEngine
from app.tenderproof.continuous_router import router
from app.tenderproof.continuous_store import ContinuousStore, LeaseLost, SourcePolicy
from app.tenderproof.contracts import ExecutionStatus
from app.tenderproof.mock_demo import build_mock_driver
from app.tenderproof.source_adapters import ListingPage, get_source_adapter
from app.tenderproof.store import get_store

SOURCE="ibgp_open"
URL="https://novo.ibgpconcursos.com.br/inscricoes_abertas.jsp"
URL2=URL+"?page=2"
DETAIL="https://novo.ibgpconcursos.com.br/concurso.jsp?cod=42"
ONE='<a href="/concurso.jsp?cod=42">Concurso Prefeitura Municipal de Exemplo MG cod 42</a>'
END='<ul class="pagination"><li class="next disabled">Próxima</li></ul>'
EMPTY='<p>Nenhum concurso com inscrições abertas no momento.</p>'


@pytest.fixture(autouse=True)
def operator_allowlist(monkeypatch):
    monkeypatch.setenv("TENDERPROOF_CONTINUOUS_OPERATOR_USER_IDS","1")


def policy(**kwargs):
    return SourcePolicy(enabled=True,mode="mock",min_request_gap_s=0,retry_base_s=1,**kwargs)


def setup_queue(tmp_path,**kwargs):
    queue=ContinuousStore(tmp_path/"continuous.sqlite3")
    queue.configure(1,SOURCE,policy(**kwargs),now=1000)
    return queue


def test_capacity_wait_does_not_starve_source_behind_large_backlog(tmp_path):
    queue=setup_queue(tmp_path)
    queue.configure(1,'fepese_open',policy().model_copy(update={'mode':'real'}),now=1000)
    first=queue.enqueue(1,SOURCE,[URL,URL2],now=1000)
    second=queue.enqueue(1,'fepese_open',['https://fepese.org.br/concursos/'],now=1000)
    a,b=queue.cycle(first,1)['jobs'];waiting=queue.cycle(second,1)['jobs'][0]
    with queue._db(write=True) as db:
        db.execute("UPDATE jobs SET status='succeeded',attempts=1,updated_at=1050 WHERE job_id=?",(a['job_id'],))
        db.execute("UPDATE jobs SET status='retry',attempts=0,error='acquisition_busy',available_at=1060,updated_at=1059 WHERE job_id=?",(waiting['job_id'],))
    ready=queue.ready_jobs(now=1060)
    assert ready[0]==waiting['job_id']
    assert b['job_id'] in ready


def test_listing_precedes_older_detail_within_source(tmp_path):
    queue=setup_queue(tmp_path)
    cycle=queue.enqueue(1,SOURCE,[URL,URL2],now=1000)
    a,b=queue.cycle(cycle,1)['jobs']
    with queue._db(write=True) as db:
        db.execute("UPDATE jobs SET kind='detail',available_at=999 WHERE job_id=?",(a['job_id'],))
    assert queue.ready_jobs(now=1000)==[b['job_id']]


def one_driver(source,settings,allow_browser=False):
    driver=build_mock_driver()
    driver._listing_html=ONE+END
    return driver


def drain(engine,cycle,limit=20):
    results=[]
    for _ in range(limit):
        jobs=engine.queue.ready_jobs()
        if not jobs:
            break
        results.append(engine.process_job(jobs[0]))
    return results


def test_checkpoints_atomic_and_new_process_sees_continuation(tmp_path):
    queue=setup_queue(tmp_path)
    cycle=queue.enqueue(1,SOURCE,[URL],now=1000)
    job=queue.ready_jobs(now=1000)[0]
    lease=queue.claim(job,now=1000)
    page=get_source_adapter(SOURCE).parse_listing(ONE+f'<a href="{URL2}">2</a>',URL)
    # An interrupted transaction may not publish continuation without snapshot.
    with sqlite3.connect(queue.path) as db:
        db.execute("CREATE TRIGGER interrupt BEFORE UPDATE OF status ON jobs WHEN NEW.status='succeeded' BEGIN SELECT RAISE(ABORT,'simulated power loss'); END;")
    with pytest.raises(sqlite3.IntegrityError):
        queue.complete_listing(lease,ONE,page,now=1001)
    assert queue.snapshot(job,1) is None
    assert len(queue.cycle(cycle,1)["jobs"])==1
    with sqlite3.connect(queue.path) as db:
        db.execute("DROP TRIGGER interrupt")
    queue.complete_listing(lease,ONE,page,now=1001)
    code="from app.tenderproof.continuous_store import ContinuousStore; import sys,json; q=ContinuousStore(sys.argv[1]); print(json.dumps(q.cycle(sys.argv[2],1)))"
    child=subprocess.run([sys.executable,"-c",code,str(queue.path),cycle],capture_output=True,text=True,check=True)
    recovered=json.loads(child.stdout)
    assert len(recovered["jobs"])==3
    assert sum(j["status"]=="succeeded" for j in recovered["jobs"])==1
    assert queue.snapshot(job,1)["sha256"]


def test_fencing_reclaims_killed_worker_without_double_results(tmp_path):
    queue=setup_queue(tmp_path,max_attempts=2,job_timeout_s=10)
    cycle=queue.enqueue(1,SOURCE,[URL],now=1000)
    job=queue.ready_jobs(now=1000)[0]
    first=queue.claim(job,now=1000)
    assert queue.claim(job,now=1001) is None
    second=ContinuousStore(queue.path).claim(job,now=first.lease_until+1)
    assert second.fence==2 and second.attempts==2
    with pytest.raises(LeaseLost):
        queue.complete_listing(first,EMPTY,ListingPage(empty_evidence="vazio"),now=first.lease_until+2)
    queue.complete_listing(second,EMPTY,ListingPage(empty_evidence="vazio"),now=first.lease_until+2)
    assert queue.cycle(cycle,1)["status"]=="completed"
    assert queue.claim(job,now=first.lease_until+3) is None


def test_failures_backoff_exhaust_and_other_source_continues(tmp_path):
    queue=setup_queue(tmp_path,max_attempts=2)
    cycle=queue.enqueue(1,SOURCE,[URL],now=1000)
    job=queue.ready_jobs(now=1000)[0]
    lease=queue.claim(job,now=1000)
    queue.fail(lease,"network_timeout",now=1001)
    assert queue.ready_jobs(now=1001)==[]
    lease=queue.claim(job,now=1002)
    queue.fail(lease,"network_timeout",now=1003)
    assert queue.cycle(cycle,1)["status"]=="partial"
    queue.configure(1,"imeso_open",policy(),now=1003)
    other=queue.enqueue(1,"imeso_open",["https://portal.imeso.com.br/edital"],now=1003)
    assert queue.ready_jobs(now=1003)
    assert queue.cycle(other,1)["status"]=="active"


def test_known_remains_due_after_explicit_empty_listing(tmp_path):
    queue=setup_queue(tmp_path,interval_s=60)
    first=queue.enqueue(1,SOURCE,[URL],now=1000)
    listing=queue.claim(queue.ready_jobs(now=1000)[0],now=1000)
    page=get_source_adapter(SOURCE).parse_listing(ONE+END,URL)
    queue.complete_listing(listing,ONE+END,page,now=1001)
    detail=queue.claim(queue.ready_jobs(now=1001)[0],now=1001)
    queue.detail_checkpoint(detail,"detail",[],now=1002)
    queue.complete_detail(detail,"run-good","same",{"validation_status":"valid"},now=1002)
    second=queue.enqueue(1,SOURCE,[URL],now=1063)
    jobs=queue.cycle(second,1)["jobs"]
    assert sorted(j["kind"] for j in jobs)==["detail","listing"]
    detail_id=next(j["job_id"] for j in jobs if j["kind"]=="detail")
    listing_id=next(j["job_id"] for j in jobs if j["kind"]=="listing")
    lease=queue.claim(listing_id,now=1063)
    queue.complete_listing(lease,EMPTY,ListingPage(empty_evidence="vazio"),now=1064)
    lease=queue.claim(detail_id,now=1064)
    queue.fail(lease,"portal_failure",retryable=False,now=1065)
    assert len(queue.observations(1))==1
    with sqlite3.connect(queue.path) as db:
        assert db.execute("SELECT last_valid_run_id FROM known_candidates").fetchone()[0]=="run-good"


def test_limits_mark_partial_and_paid_reservation_survives_crash(tmp_path):
    queue=setup_queue(tmp_path,max_candidates=1,max_listing_pages=1,allow_browser=True,max_browser_seconds=180)
    cycle=queue.enqueue(1,SOURCE,[URL],now=1000)
    lease=queue.claim(queue.ready_jobs(now=1000)[0],now=1000)
    assert lease.allow_browser
    page=get_source_adapter(SOURCE).parse_listing(ONE+'<a href="/concurso.jsp?cod=77">Concurso Outro 77</a>'+f'<a href="{URL2}">2</a>',URL)
    queue.complete_listing(lease,ONE,page,now=1001)
    detail=queue.claim(queue.ready_jobs(now=1001)[0],now=1001)
    assert not detail.allow_browser
    queue.fail(detail,"test",retryable=False,now=1002)
    result=queue.cycle(cycle,1)
    assert result["browser_reserved_s"]==180
    assert "candidate_limit" in result["reasons"] and "listing_page_limit" in result["reasons"]
    assert result["status"]=="partial"


def test_cycle_deadline_stops_new_work_but_retains_snapshot(tmp_path):
    queue=setup_queue(tmp_path,cycle_timeout_s=60)
    cycle=queue.enqueue(1,SOURCE,[URL],now=1000)
    lease=queue.claim(queue.ready_jobs(now=1000)[0],now=1000)
    queue.complete_listing(lease,ONE+END,get_source_adapter(SOURCE).parse_listing(ONE+END,URL),now=1001)
    assert queue.ready_jobs(now=1061)==[]
    assert queue.cycle(cycle,1)["status"]=="partial"
    assert queue.snapshot(lease.job_id,1)


def test_auth_owner_limits_and_manual_enqueue_survive_broker_down(monkeypatch,tmp_path):
    monkeypatch.setenv("TENDERPROOF_CONTINUOUS_ENABLED","true")
    app=FastAPI()
    app.include_router(router)
    client=TestClient(app)
    assert client.get("/tenderproof/continuous/status").status_code in (401,403)
    app.dependency_overrides[get_current_user]=lambda:User(id=1,name="One",email="1@example.test",password_hash="x")
    assert client.put("/tenderproof/continuous/sources/unknown",json=policy().model_dump()).status_code==422
    assert client.put(f"/tenderproof/continuous/sources/{SOURCE}",json=policy().model_dump()).status_code==200
    response=client.post(f"/tenderproof/continuous/sources/{SOURCE}/collect")
    assert response.status_code==202  # no Redis operation in the API
    cycle=response.json()["cycle_id"]
    assert client.get(f"/tenderproof/continuous/cycles/{cycle}").status_code==200
    app.dependency_overrides[get_current_user]=lambda:User(id=2,name="Two",email="2@example.test",password_hash="x")
    assert client.get(f"/tenderproof/continuous/cycles/{cycle}").status_code==404
    assert client.get("/tenderproof/continuous/observations").json()==[]
    assert client.get("/tenderproof/continuous/status").json()["sources"]==[]


def test_engine_real_pdf_roundtrip_dedup_and_no_discovery_cap(monkeypatch,tmp_path):
    monkeypatch.setenv("TENDERPROOF_CONTINUOUS_ENABLED","true")
    queue=ContinuousStore()
    queue.configure(1,SOURCE,policy())
    engine=ContinuousEngine(queue=queue,driver_factory=one_driver)
    cycle=engine.enqueue(1,SOURCE)
    results=drain(engine,cycle)
    assert queue.cycle(cycle,1)["status"]=="completed", (results,queue.cycle(cycle,1))
    observations=queue.observations(1)
    assert len(observations)==1
    run=get_store().get_run(observations[0]["run_id"])
    assert run.execution_status==ExecutionStatus.COMPLETED and run.artifact
    assert run.is_synthetic_sample
    assert get_store().load_artifact_bytes(run.artifact).startswith(b"%PDF")
    cycle2=engine.enqueue(1,SOURCE,force=True)
    drain(engine,cycle2)
    assert len(queue.observations(1))==1


def test_duplicate_broker_delivery_no_network_and_dispatch_failure_retries(monkeypatch):
    monkeypatch.setenv("TENDERPROOF_CONTINUOUS_ENABLED","true")
    queue=ContinuousStore()
    queue.configure(1,SOURCE,policy())
    calls=[]
    def factory(*args,**kwargs):
        calls.append(1)
        return one_driver(*args,**kwargs)
    engine=ContinuousEngine(queue=queue,driver_factory=factory)
    engine.enqueue(1,SOURCE)
    job=queue.ready_jobs()[0]
    assert engine.process_job(job)["status"]=="succeeded"
    assert engine.process_job(job)["status"]=="not_claimed"
    assert len(calls)==1
    import app.tenderproof.continuous_tasks as tasks
    monkeypatch.setattr(tasks,"ContinuousEngine",lambda:engine)
    def offline(*args,**kwargs):
        raise OSError("broker unavailable")
    monkeypatch.setattr(tasks.continuous_job,"apply_async",offline)
    result=tasks.continuous_tick.run()
    assert result["dispatch_failures"]==1
    assert queue.ready_jobs()  # durable job unaffected


def test_unknown_empty_keeps_snapshot_and_retries(monkeypatch):
    monkeypatch.setenv("TENDERPROOF_CONTINUOUS_ENABLED","true")
    queue=ContinuousStore()
    queue.configure(1,SOURCE,policy())
    def factory(*args,**kwargs):
        driver=build_mock_driver()
        driver._listing_html="<h1>Site em manutenção</h1>"
        return driver
    engine=ContinuousEngine(queue=queue,driver_factory=factory)
    cycle=engine.enqueue(1,SOURCE)
    job=queue.ready_jobs()[0]
    assert engine.process_job(job)["status"]=="retry_or_failed"
    assert queue.snapshot(job,1)["html"]=="<h1>Site em manutenção</h1>"
    assert queue.cycle(cycle,1)["jobs"][0]["status"]=="retry"


def test_completed_run_is_adopted_after_queue_commit_failure(monkeypatch):
    monkeypatch.setenv("TENDERPROOF_CONTINUOUS_ENABLED","true")
    queue=ContinuousStore()
    queue.configure(1,SOURCE,policy())
    engine=ContinuousEngine(queue=queue,driver_factory=one_driver)
    cycle=engine.enqueue(1,SOURCE)
    engine.process_job(queue.ready_jobs()[0])
    detail=queue.ready_jobs()[0]
    original=queue.complete_detail
    def fail_commit(*args,**kwargs):
        raise OSError("simulated disk disruption")
    monkeypatch.setattr(queue,"complete_detail",fail_commit)
    engine.process_job(detail)
    job=next(j for j in queue.cycle(cycle,1)["jobs"] if j["job_id"]==detail)
    assert get_store().get_run(job["run_id"]).execution_status==ExecutionStatus.COMPLETED
    monkeypatch.setattr(queue,"complete_detail",original)
    def no_driver(*args,**kwargs):
        raise AssertionError("a committed result must not trigger another download")
    engine.driver_factory=no_driver
    with sqlite3.connect(queue.path) as db:
        db.execute("UPDATE jobs SET available_at=0 WHERE job_id=?",(detail,))
    result=engine.process_job(detail)
    assert result["recovered"] and len(queue.observations(1))==1


def test_unknown_browser_closure_holds_only_paid_fallback(tmp_path):
    queue=setup_queue(tmp_path,allow_browser=True,max_browser_seconds=360)
    cycle=queue.enqueue(1,SOURCE,[URL],now=1000)
    job=queue.ready_jobs(now=1000)[0]
    lease=queue.claim(job,now=1000)
    assert lease.allow_browser
    queue.fail(lease,"unknown_close",now=1001)
    queue.hold_browser(1,SOURCE,"run:unconfirmed")
    retry=queue.claim(job,now=1002)
    assert not retry.allow_browser
    queue.clear_browser_hold(1,SOURCE,"run:wrong")
    assert queue.configuration(1,SOURCE)["browser_hold"]
    queue.clear_browser_hold(1,SOURCE,"run:unconfirmed")
    assert queue.configuration(1,SOURCE)["browser_hold"] is None


def test_revoked_operator_cannot_schedule_or_consume_existing_job(monkeypatch):
    monkeypatch.setenv("TENDERPROOF_CONTINUOUS_ENABLED","true")
    queue=ContinuousStore()
    queue.configure(1,SOURCE,policy())
    engine=ContinuousEngine(queue=queue,driver_factory=one_driver)
    cycle=engine.enqueue(1,SOURCE)
    job=queue.ready_jobs()[0]
    monkeypatch.setenv("TENDERPROOF_CONTINUOUS_OPERATOR_USER_IDS","")
    assert engine.process_job(job)["status"]=="operator_revoked"
    assert engine.schedule_due()==[]
    assert engine.ready_jobs()==[]
    assert queue.cycle(cycle,1)["jobs"][0]["attempts"]==0


def test_completed_listing_replays_checkpoint_without_second_fetch(monkeypatch):
    monkeypatch.setenv("TENDERPROOF_CONTINUOUS_ENABLED","true")
    queue=ContinuousStore()
    queue.configure(1,SOURCE,policy())
    engine=ContinuousEngine(queue=queue,driver_factory=one_driver)
    cycle=engine.enqueue(1,SOURCE)
    job=queue.ready_jobs()[0]
    original=queue.complete_listing
    def fail_commit(*args,**kwargs):
        raise OSError("simulated queue commit failure")
    monkeypatch.setattr(queue,"complete_listing",fail_commit)
    engine.process_job(job)
    assert queue.snapshot(job,1)["html"]==ONE+END
    row=queue.cycle(cycle,1)["jobs"][0]
    assert get_store().get_run(row["run_id"]).execution_status==ExecutionStatus.COMPLETED
    monkeypatch.setattr(queue,"complete_listing",original)
    def no_network(*args,**kwargs):
        raise AssertionError("listing checkpoint must be replayed locally")
    engine.driver_factory=no_network
    with sqlite3.connect(queue.path) as db:
        db.execute("UPDATE jobs SET available_at=0 WHERE job_id=?",(job,))
    assert engine.process_job(job)["recovered"]
    assert len(queue.cycle(cycle,1)["jobs"])==2


def test_busy_does_not_spend_attempts_or_browser_budget(monkeypatch):
    monkeypatch.setenv("TENDERPROOF_CONTINUOUS_ENABLED","true")
    queue=ContinuousStore()
    queue.configure(1,SOURCE,policy(allow_browser=True,max_browser_seconds=540))
    queue.configure(1,"imeso_open",policy(allow_browser=True,max_browser_seconds=540))
    engine=ContinuousEngine(queue=queue)
    first=engine.enqueue(1,SOURCE)
    second=engine.enqueue(1,"imeso_open")
    token=get_store().acquire_execution_lease(600)
    try:
        for cycle in (first,second):
            job=queue.cycle(cycle,1)["jobs"][0]["job_id"]
            for _ in range(4):
                assert engine.process_job(job)["status"]=="acquisition_busy"
                with sqlite3.connect(queue.path) as db:
                    db.execute("UPDATE jobs SET available_at=0 WHERE job_id=?",(job,))
            result=queue.cycle(cycle,1)
            assert result["status"]=="active"
            assert result["jobs"][0]["attempts"]==0
            assert result["browser_reserved_s"]==0
    finally:
        get_store().release_execution_lease(token)


def test_http_processing_busy_does_not_exhaust_source_attempts(monkeypatch):
    from app.tenderproof.processing import ProcessingError
    monkeypatch.setenv('TENDERPROOF_CONTINUOUS_ENABLED','true')
    queue=ContinuousStore()
    queue.configure(1,SOURCE,policy())
    engine=ContinuousEngine(queue=queue,driver_factory=one_driver)
    cycle=engine.enqueue(1,SOURCE)
    listing=queue.cycle(cycle,1)['jobs'][0]['job_id']
    assert engine.process_job(listing)['status']=='succeeded'
    job=next(j['job_id'] for j in queue.cycle(cycle,1)['jobs'] if j['kind']=='detail')
    def busy(*args,**kwargs):
        raise ProcessingError('concurrency_limit')
    monkeypatch.setattr('app.tenderproof.service.extract_pages_isolated',busy)
    for _ in range(3):
        with sqlite3.connect(queue.path) as db:
            db.execute('UPDATE jobs SET available_at=0 WHERE job_id=?',(job,))
        assert engine.process_job(job)['status']=='acquisition_busy'
    current=queue.cycle(cycle,1)
    detail=next(j for j in current['jobs'] if j['job_id']==job)
    assert detail['status']=='retry' and detail['attempts']==0
    assert current['status']=='active'
    assert get_store().get_run(detail['run_id']).artifact


def test_browser_intent_without_id_survives_crash_and_blocks_new_launch(tmp_path):
    queue=setup_queue(tmp_path,allow_browser=True,max_browser_seconds=540,job_timeout_s=10)
    cycle=queue.enqueue(1,SOURCE,[URL],now=1000)
    job=queue.ready_jobs(now=1000)[0]
    lease=queue.claim(job,now=1000)
    attempt=queue.browser_creating(lease,now=1001)
    restarted=ContinuousStore(queue.path)
    after=restarted.claim(job,now=lease.lease_until+1)
    assert after and not after.allow_browser
    assert restarted.configuration(1,SOURCE)["browser_hold"]=="journal"
    assert restarted.open_browser_attempts(1,SOURCE)[0]["session_id"] is None
    # A late provider acknowledgment persists the ID; only confirmed closure
    # clears the hold. Expiry of either worker lease never clears it.
    restarted.browser_created(attempt,"session-after-crash",now=lease.lease_until+2)
    assert restarted.open_browser_attempts(1,SOURCE)[0]["state"]=="active"
    restarted.browser_closed(attempt,"session-after-crash",now=lease.lease_until+3)
    assert restarted.configuration(1,SOURCE)["browser_hold"] is None


@pytest.mark.parametrize("terminal,expected",[(False,"partial"),(True,"completed")])
def test_pagination_cycle_needs_reachable_terminal(tmp_path,terminal,expected):
    queue=setup_queue(tmp_path)
    cycle=queue.enqueue(1,SOURCE,[URL],now=1000)
    first=queue.claim(queue.ready_jobs(now=1000)[0],now=1000)
    queue.complete_listing(first,"first",ListingPage(next_urls=[URL2]),now=1001)
    second=queue.claim(queue.ready_jobs(now=1001)[0],now=1001)
    queue.complete_listing(second,"second",ListingPage(next_urls=[URL],terminal_evidence="fim" if terminal else None),now=1002)
    assert queue.cycle(cycle,1)["status"]==expected


def test_final_attempt_expired_adopts_completed_listing_without_new_attempt(monkeypatch):
    monkeypatch.setenv("TENDERPROOF_CONTINUOUS_ENABLED","true")
    queue=ContinuousStore()
    queue.configure(1,SOURCE,policy(max_attempts=1))
    engine=ContinuousEngine(queue=queue,driver_factory=one_driver)
    cycle=engine.enqueue(1,SOURCE)
    job=queue.ready_jobs()[0]
    original=queue.complete_listing
    def crash_after_run(*args,**kwargs):
        raise SystemExit("worker died after run commit")
    monkeypatch.setattr(queue,"complete_listing",crash_after_run)
    with pytest.raises(SystemExit):
        engine.process_job(job)
    with sqlite3.connect(queue.path) as db:
        db.execute("UPDATE jobs SET lease_until=0 WHERE job_id=?",(job,))
    assert queue.ready_jobs()==[job]
    monkeypatch.setattr(queue,"complete_listing",original)
    engine.driver_factory=lambda *args,**kwargs:pytest.fail("no new network after attempt limit")
    assert engine.process_job(job)["recovered"]
    row=next(j for j in queue.cycle(cycle,1)["jobs"] if j["job_id"]==job)
    assert row["status"]=="succeeded" and row["attempts"]==1 and row["fence"]==2


def test_final_attempt_without_result_fails_without_another_acquisition(monkeypatch):
    monkeypatch.setenv("TENDERPROOF_CONTINUOUS_ENABLED","true")
    queue=ContinuousStore()
    queue.configure(1,SOURCE,policy(max_attempts=1))
    engine=ContinuousEngine(queue=queue)
    cycle=engine.enqueue(1,SOURCE)
    job=queue.ready_jobs()[0]
    queue.claim(job)
    with sqlite3.connect(queue.path) as db:
        db.execute("UPDATE jobs SET lease_until=0 WHERE job_id=?",(job,))
    engine.driver_factory=lambda *args,**kwargs:pytest.fail("attempt limit must prevent acquisition")
    assert engine.process_job(job)["status"]=="failed"
    assert queue.cycle(cycle,1)["status"]=="partial"


def test_final_session_sync_preserves_concurrent_comparison_and_closure(monkeypatch):
    from app.tenderproof.contracts import SessionRecord,TenderProofRun
    from app.tenderproof.solari_adapter import SessionRecord as DriverSession
    monkeypatch.setenv("TENDERPROOF_CONTINUOUS_ENABLED","true")
    queue=ContinuousStore()
    queue.configure(1,SOURCE,policy())
    engine=ContinuousEngine(queue=queue)
    engine.enqueue(1,SOURCE)
    lease=queue.claim(queue.ready_jobs()[0])
    old=TenderProofRun(run_id="old-sync",owner_user_id=1,execution_status=ExecutionStatus.COMPLETED,
        sessions=[SessionRecord(phase="detail",session_id="s1",closed=False)])
    get_store().put_run(old)
    def concurrent(current):
        current.sessions[0].closed=True
        current.sessions[0].replay_status="available"
        current.sessions[0].replay_url="https://replay.example/confirmed"
        current.comparison.baseline_origin="new comparison from API"
    get_store().update_run(old.run_id,concurrent)
    driver=build_mock_driver()
    driver.session_records=lambda:[DriverSession(phase="detail",session_id="s1",closed=False)]
    engine._record_sessions(lease,driver,old)
    persisted=get_store().get_run(old.run_id)
    assert persisted.sessions[0].closed
    assert persisted.sessions[0].replay_url=="https://replay.example/confirmed"
    assert persisted.comparison.baseline_origin=="new comparison from API"


def test_document_navigation_budget_respects_source_policy_and_remaining_deadline():
    engine = object.__new__(ContinuousEngine)
    policy = SourcePolicy(max_documents=25, job_timeout_s=300)
    settings = engine._settings(policy, remaining_s=90)
    assert settings.limits.max_navigations == 116
    assert settings.limits.max_documents == 25
    assert settings.limits.total_timeout_s == 90
    assert settings.limits.max_attempts == 1
