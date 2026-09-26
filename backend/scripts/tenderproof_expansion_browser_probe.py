"""One bounded IBGP listing through the continuous engine, in an isolated store.

Uses one acquisition attempt, at most one Browser launch, and executes no detail
jobs. The durable journal records intent/ID/confirmed closure. No scheduler or
canonical database is started. Never reuse the same output directory.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, required=True)
    args = parser.parse_args()
    root = args.directory.resolve()
    if root == BACKEND / ".tenderproof" or not root.is_relative_to((BACKEND / ".tenderproof").resolve()):
        parser.error("directory must be a fresh child of backend/.tenderproof")
    from dotenv import dotenv_values
    key = dotenv_values(BACKEND / ".env").get("SOLARI_API_KEY")
    if not key:
        parser.error("local SOLARI_API_KEY missing")
    root.mkdir(parents=True, exist_ok=False)
    owner = 9100710
    os.environ.update({"TENDERPROOF_ARTIFACT_DIR": str(root / "artifacts"),
        "TENDERPROOF_PROCESSING_DIR": str(root / "processing"),
        "TENDERPROOF_CONTINUOUS_ENABLED": "true", "TENDERPROOF_CONTINUOUS_OPERATOR_USER_IDS": str(owner),
        "TENDERPROOF_PUBLICATION_ENABLED": "false", "TENDERPROOF_BROWSER_LIVE_ENABLED": "true",
        "SOLARI_API_KEY": key, "SOLARI_BASE_URL": "https://api.getsolari.com", "SOLARI_REGION": "us-west",
        "TENDERPROOF_RECORDING": "true", "TENDERPROOF_STEALTH": "false", "TENDERPROOF_CAPTCHA": "false"})
    os.environ.pop("TENDERPROOF_PROXY", None)
    from app.tenderproof.continuous import ContinuousEngine
    from app.tenderproof.continuous_store import ContinuousStore, SourcePolicy
    from app.tenderproof.store import TenderProofStore
    source = "ibgp_open"
    queue, runs = ContinuousStore(), TenderProofStore()
    policy = SourcePolicy(enabled=True, mode="real", max_listing_pages=1, max_candidates=200,
        max_attempts=1, job_timeout_s=180, cycle_timeout_s=360, allow_browser=True, max_browser_seconds=180)
    queue.configure(owner, source, policy)
    engine = ContinuousEngine(queue, runs)
    cycle_id = engine.enqueue(owner, source, force=True)
    report = {"scope": "one_real_ibgp_listing", "started_at": datetime.now(timezone.utc).isoformat(),
              "cycle_id": cycle_id, "max_browser_launches": 1, "detail_jobs_executed": 0,
              "canonical_writes": 0, "scheduler_started": False}
    try:
        job_id = engine.ready_jobs()[0]
        report["result"] = engine.process_job(job_id)
        cycle = queue.cycle(cycle_id, owner)
        job = next(job for job in cycle["jobs"] if job["job_id"] == job_id)
        run = runs.get_run(job["run_id"]) if job.get("run_id") else None
        report.update(job_id=job_id, run_id=job.get("run_id"), job_status=job["status"],
            candidates=len(run.candidates) if run else 0, browser_sessions=len(run.sessions) if run else 0,
            all_sessions_confirmed_closed=bool(run and run.sessions and all(s.closed for s in run.sessions)),
            browser_journal_pending=len(queue.open_browser_attempts(owner, source)),
            coverage_complete=False, coverage_note="Uma listagem; abas e detalhes não executados nesta prova.")
    except Exception as exc:
        report.update(error_type=type(exc).__name__)
        raise
    finally:
        queue.configure(owner, source, policy.model_copy(update={"enabled": False}))
        report["completed_at"] = datetime.now(timezone.utc).isoformat()
        report["source_paused_after_probe"] = True
        (root / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    main()
