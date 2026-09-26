"""Prove real Redis/Celery delivery, crash recovery and cross-process evidence.

Run against a dedicated disposable localhost Redis. Only synthetic official-site
fixtures are acquired. Work and test-only clock advances stay in --root, which
must be a fresh directory. The script never flushes Redis or reads the catalog.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import time
from urllib.parse import urlsplit


def wait_for(predicate,description,seconds=45):
    deadline=time.monotonic()+seconds
    while time.monotonic()<deadline:
        result=predicate()
        if result:
            return result
        time.sleep(0.25)
    raise RuntimeError("timed out: "+description)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--root",type=Path,required=True)
    parser.add_argument("--broker-url",default="redis://127.0.0.1:16497/14")
    parser.add_argument("--report",type=Path)
    args=parser.parse_args()
    target=urlsplit(args.broker_url)
    if target.scheme!="redis" or target.hostname not in ("localhost","127.0.0.1") or target.port==6379 or target.path!="/14":
        raise ValueError("probe requires a dedicated localhost Redis on a non-default port, DB 14")
    root=args.root.resolve()
    root.mkdir(parents=True,exist_ok=False)
    backend=Path(__file__).resolve().parents[1]
    sys.path.insert(0,str(backend))
    os.environ.update(TENDERPROOF_ARTIFACT_DIR=str(root/"artifacts"),TENDERPROOF_PROCESSING_DIR=str(root/"processing"),
        TENDERPROOF_CONTINUOUS_ENABLED="true",TENDERPROOF_CONTINUOUS_OPERATOR_USER_IDS="1",
        TENDERPROOF_BROWSER_LIVE_ENABLED="false",TENDERPROOF_PROBE_ROOT=str(root),
        DATABASE_URL="sqlite:///:memory:",CELERY_BROKER_URL=args.broker_url,
        CELERY_RESULT_BACKEND=args.broker_url.rsplit("/",1)[0]+"/15",
        SECRET_KEY="isolated-continuous-probe-only",PYTHONPATH=str(backend))
    os.environ.pop("SOLARI_API_KEY",None)
    import redis
    from app.worker import celery_app
    from app.tenderproof.continuous import ContinuousEngine
    from app.tenderproof.continuous_store import ContinuousStore,SourcePolicy
    from app.tenderproof.continuous_tasks import continuous_job,continuous_tick
    from app.tenderproof.store import get_store,operational_db_path
    assert redis.Redis.from_url(args.broker_url).ping()
    queue=ContinuousStore()
    queue.configure(1,"ibgp_open",SourcePolicy(enabled=True,mode="mock",interval_s=3600,
        min_request_gap_s=0,max_attempts=3,retry_base_s=1,job_timeout_s=30))
    cycle=ContinuousEngine(queue=queue).enqueue(1,"ibgp_open")
    log_handles=[]
    processes=[]
    def worker(number):
        log=(root/f"worker-{number}.log").open("w",encoding="utf-8")
        log_handles.append(log)
        process=subprocess.Popen([sys.executable,"-m","celery","-A","scripts.tenderproof_continuous_probe_worker:celery_app",
            "worker","--pool=solo","--concurrency=1","-Q","tenderproof","--loglevel=WARNING",
            "--without-gossip","--without-mingle","--without-heartbeat"],cwd=root,env=os.environ.copy(),
            stdout=log,stderr=subprocess.STDOUT,creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0))
        processes.append(process)
        return process
    report={"synthetic":True,"canonical_database_used":False,"root":str(root),"cycle_id":cycle,"checks":{}}
    try:
        initial=queue.ready_jobs()[0]
        first=worker(1)
        continuous_job.apply_async(args=[initial],queue="tenderproof")
        continuous_job.apply_async(args=[initial],queue="tenderproof")
        wait_for(lambda:queue.cycle(cycle,1)["jobs"][0]["status"]=="succeeded","duplicate listing delivery")
        report["checks"]["duplicate_delivery_single_claim"]=queue.cycle(cycle,1)["jobs"][0]["attempts"]==1
        detail=next(job["job_id"] for job in queue.cycle(cycle,1)["jobs"] if job["kind"]=="detail")
        (root/"crash-gate").write_text("kill fixture only",encoding="utf-8")
        continuous_job.apply_async(args=[detail],queue="tenderproof")
        wait_for(lambda:(root/"download-barrier-reached").exists(),"detail checkpoint barrier")
        before=queue.snapshot(detail,1)
        report["checks"]["checkpoint_before_download"]=bool(before and before["metadata"]["documents"])
        first.kill()
        first.wait(timeout=10)
        report["killed_worker_exit_code"]=first.returncode
        report["checks"]["worker_confirmed_dead"]=first.poll() is not None
        # Deterministic test clock: only AFTER confirming process death, expire
        # that test's leases to avoid a 150-second wait. No production DB touched.
        with sqlite3.connect(queue.path) as db:
            db.execute("UPDATE jobs SET lease_until=0 WHERE job_id=? AND status='running'",(detail,))
        with sqlite3.connect(operational_db_path()) as db:
            db.execute("UPDATE execution_leases SET expires_at=0")
        (root/"crash-gate").unlink()
        second=worker(2)
        dispatched=continuous_tick.run()
        report["checks"]["durable_tick_redispatch"]=dispatched["dispatched"]==1
        wait_for(lambda:queue.cycle(cycle,1)["status"]!="active","restarted worker finishes acquisition")
        final=queue.cycle(cycle,1)
        observations=queue.observations(1)
        report["checks"]["cycle_completed"]=final["status"]=="completed"
        report["checks"]["one_review_observation"]=len(observations)==1
        detail_row=next(job for job in final["jobs"] if job["kind"]=="detail")
        report["checks"]["fence_incremented_after_worker_death"]=detail_row["fence"]==2 and detail_row["attempts"]==2
        continuous_job.apply_async(args=[detail],queue="tenderproof")
        # A separate reader (API-equivalent) verifies durable PDF bytes + run.
        code="from app.tenderproof.continuous_store import ContinuousStore; from app.tenderproof.store import get_store; import json; q=ContinuousStore(); obs=q.observations(1); run=get_store().get_run(obs[0]['run_id']); print(json.dumps({'observations':len(obs),'pdf_valid':get_store().load_artifact_bytes(run.artifact).startswith(b'%PDF'),'status':run.execution_status.value,'owner':run.owner_user_id}))"
        reader=subprocess.run([sys.executable,"-c",code],cwd=root,env=os.environ.copy(),capture_output=True,text=True,check=True)
        reader_data=json.loads(reader.stdout)
        report["checks"]["separate_process_reads_run_pdf"]=reader_data=={"observations":1,"pdf_valid":True,"status":"completed","owner":1}
        report["status"]=final["status"]
        report["jobs"]=final["jobs"]
        report["browser_reserved_s"]=final["browser_reserved_s"]
        report["clock_fixture"]="After confirmed worker death only, leases expired in isolated test databases; no production time or data changed."
        report["passed"]=all(report["checks"].values())
        if not report["passed"]:
            raise AssertionError(report)
    finally:
        for process in processes:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=5)
        for log in log_handles:
            log.close()
        report["worker_processes_stopped"]=all(process.poll() is not None for process in processes)
        destination=args.report.resolve() if args.report else root/"report.json"
        destination.parent.mkdir(parents=True,exist_ok=True)
        destination.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(report,ensure_ascii=False,indent=2))


if __name__=="__main__":
    main()
