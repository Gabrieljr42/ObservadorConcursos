"""Bounded, read-only evidence for stages 9/10; never starts the scheduler."""
from __future__ import annotations

import argparse
from dataclasses import replace
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    root = args.directory.resolve()
    allowed = Path(__file__).resolve().parents[1] / ".tenderproof"
    if not root.is_relative_to(allowed.resolve()):
        parser.error("directory must be inside backend/.tenderproof")
    root.mkdir(parents=True, exist_ok=True)
    os.environ["TENDERPROOF_ARTIFACT_DIR"] = str(root / "artifacts")
    os.environ["TENDERPROOF_PROCESSING_DIR"] = str(root / "processing")
    os.environ["TENDERPROOF_BROWSER_LIVE_ENABLED"] = "false"
    os.environ["TENDERPROOF_CONTINUOUS_ENABLED"] = "false"
    os.environ["TENDERPROOF_PUBLICATION_ENABLED"] = "false"
    from app.tenderproof.contracts import TenderProofRun, ExecutionStatus
    from app.tenderproof.http_driver import build_continuous_driver
    from app.tenderproof.security import TenderProofSettings
    from app.tenderproof.service import TenderProofService
    from app.tenderproof.source_adapters import SOURCE_ADAPTERS
    from app.tenderproof.store import TenderProofStore
    store = TenderProofStore()
    report_path = root / "report.json"
    if args.verify_only:
        report = json.loads(report_path.read_text(encoding="utf-8"))
        checks = []
        for source in report["sources"]:
            if not source.get("run_id"):
                continue
            run = store.get_run(source["run_id"])
            raw = store.load_artifact_bytes(run.artifact) if run and run.artifact else None
            checks.append({"source": source["source"], "run_persisted": run is not None,
                           "artifact_valid": bool(raw and hashlib.sha256(raw).hexdigest() == run.artifact.sha256),
                           "status": run.execution_status if run else "missing"})
        (root / "restart-verification.json").write_text(json.dumps(checks, indent=2), encoding="utf-8")
        print(json.dumps(checks))
        return
    if report_path.exists():
        parser.error("report already exists; use --verify-only to avoid reacquisition")
    settings = TenderProofSettings()
    settings.limits = replace(settings.limits, max_candidates=200, max_documents=100,
                              total_timeout_s=60, replay_deadline_s=0)
    report = {"started_at": datetime.now(timezone.utc).isoformat(), "scope": "bounded_two_source_http",
              "browser_resources_created": 0, "canonical_writes": 0, "sources": []}
    for source, adapter in SOURCE_ADAPTERS.items():
        result = {"source": source, "pages": [], "diagnostics": []}
        candidates, pending, visited = {}, list(adapter.listing_urls), set()
        while pending and len(visited) < 6:
            url = pending.pop(0)
            if url in visited:
                continue
            visited.add(url)
            driver = build_continuous_driver(source, settings, allow_browser=False)
            try:
                html = driver.open_listing(url)
                page = adapter.parse_listing(html, url, 200)
                digest = hashlib.sha256(html.encode()).hexdigest()
                (root / f"{source}-{digest}.html").write_text(html, encoding="utf-8")
                result["pages"].append({"url": url, "sha256": digest, "candidates": len(page.candidates),
                                        "next_urls": page.next_urls, "terminal_evidence": page.terminal_evidence,
                                        "empty_evidence": page.empty_evidence, "truncated": page.truncated})
                candidates.update({c.candidate_id: c for c in page.candidates})
                pending.extend(target for target in page.next_urls if target not in visited and target not in pending)
            except Exception as exc:
                result["diagnostics"].append({"url": url, "error_type": type(exc).__name__, "message": str(exc)[:300]})
            finally:
                driver.close()
        result["observed_candidates"] = len(candidates)
        result["remaining_listing_urls"] = pending
        # One already-known historical candidate when visible, otherwise one
        # actual observed candidate. Never invent an ID absent from discovery.
        preferred = "cand-704" if source == "ibgp_open" else "imeso-139"
        chosen = candidates.get(preferred) or next(iter(candidates.values()), None)
        if chosen:
            run = TenderProofRun(run_id=f"tp-expansion-{source}", source=source, owner_user_id=1,
                                mode="real", candidates=[chosen], execution_status=ExecutionStatus.AWAITING_SELECTION,
                                sample_note="Uma amostra documental; listagens limitadas a seis páginas.")
            store.put_run(run)
            driver = build_continuous_driver(source, settings, allow_browser=False)
            run = TenderProofService(store, settings).select_and_process(run.run_id, chosen.candidate_id, driver, mode="real")
            result.update(run_id=run.run_id, selected_candidate=chosen.external_id,
                          execution_status=run.execution_status, error=run.error,
                          validation_status=run.validation_status,
                          artifact_sha256=run.artifact.sha256 if run.artifact else None,
                          pdf_pages=run.total_pages, fields={f.field_name: f.state for f in run.fields})
        report["sources"].append(result)
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    report["completed_at"] = datetime.now(timezone.utc).isoformat()
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"report": str(report_path), "sources": [{k: v for k, v in s.items() if k not in ("pages", "diagnostics")} for s in report["sources"]]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
