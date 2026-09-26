"""Prepare by default. Execution requires explicit authorization for this operation.

At most one detail/download Browser session per fixed source; no discovery session,
no canonical database, no automatic retry, no bypass of rejected documents.
"""
from __future__ import annotations

import argparse
import asyncio
from datetime import datetime, timezone
import hashlib
import json
import os
import re
from pathlib import Path
import sys

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))
OPERATION = "browser-two-source-20260907-v4"
OUTPUT = BACKEND / ".tenderproof" / OPERATION
OFFICIAL_API = "https://api.getsolari.com"
OWNER = 9100704
FIXED_CANDIDATES = {"ibgp_open": "704", "imeso_open": "139"}


def equivalent_document_url(observed, approved):
    """Only URL-encoding equivalence; source host/path/query values stay exact."""
    from urllib.parse import urlsplit, parse_qsl, unquote
    def parts(url):
        parsed = urlsplit(url)
        return (parsed.scheme, parsed.netloc, unquote(parsed.path),
                sorted(parse_qsl(parsed.query, keep_blank_values=True)))
    return parts(observed) == parts(approved)


def save(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    temporary.replace(path)


def public_html(url):
    """Read-only bounded HTTP. Never send provider credentials or follow silently."""
    import httpx
    from app.tenderproof.security import validate_destination
    for _ in range(4):
        validate_destination(url)
        with httpx.stream("GET", url, timeout=20, follow_redirects=False) as response:
            if response.is_redirect:
                from urllib.parse import urljoin
                url = urljoin(url, response.headers["Location"])
                continue
            response.raise_for_status()
            chunks, size = [], 0
            for chunk in response.iter_bytes(16384):
                size += len(chunk)
                if size > 1024 * 1024:
                    raise ValueError("public HTML size limit")
                chunks.append(chunk)
            raw = b"".join(chunks)
            return raw.decode(response.encoding or "utf-8"), {
                "url": url, "status": response.status_code,
                "sha256": hashlib.sha256(raw).hexdigest(),
                "observed_at": datetime.now(timezone.utc).isoformat(), "origin": "public_HTTP_no_Solari",
            }
    raise ValueError("public redirect limit")


def prepare(output=OUTPUT):
    from app.tenderproof.sources import IMESO_LISTING, imeso_candidates, imeso_documents
    from app.tenderproof.acquisition import choose_edital
    historical = BACKEND / ".tenderproof/review/runs/tpr-c84fdce378eb.json"
    data = json.loads(historical.read_text(encoding="utf-8"))
    ibgp = next(c for c in data["candidates"] if c["external_id"] == "704")
    plan = {"operation": OPERATION, "created_at": datetime.now(timezone.utc).isoformat(),
            "authorization": "not_granted_by_preparation", "max_sessions": 2,
            "per_session_seconds": 180, "close_seconds": 30, "attempts_per_source": 1,
            "recording": True, "stealth": False, "proxy": False, "captcha": False,
            "official_api": OFFICIAL_API, "sources": [{"source": "ibgp_open", "candidate": ibgp,
                "candidate_origin": "preserved_historical_snapshot_not_account_reconciled",
                "eligible": True, "document": data["document"],
                "document_origin": "historical_selected_document_rechecked_in_Browser"}]}
    listing, listing_origin = public_html(IMESO_LISTING)
    output.mkdir(parents=True, exist_ok=True)
    (output / "imeso-listing.html").write_text(listing, encoding="utf-8")
    inspected = []
    for candidate in imeso_candidates(listing, IMESO_LISTING)[:4]:
        detail, detail_origin = public_html(candidate.detail_url_observed)
        docs = imeso_documents(detail, candidate)
        source = {"source": "imeso_open", "candidate": candidate.model_dump(mode="json"),
                  "candidate_origin": listing_origin, "detail_origin": detail_origin,
                  "documents": [d.model_dump() for d in docs], "eligible": False}
        try:
            principal = [d for d in docs if re.match(r"^edital\b", d.title.strip(), re.I)
                         and not re.search(r"retifica|errata|anexo|julgamento|impugna|recurso|resultado", d.title, re.I)]
            document, _ = choose_edital(principal)
            source.update(eligible=True, document=document.model_dump())
        except ValueError as exc:
            source["blocked_reason"] = str(exc)
        inspected.append(source)
        (output / f"imeso-detail-{candidate.external_id}.html").write_text(detail, encoding="utf-8")
        if source["eligible"]:
            break
    plan["sources"].append(inspected[-1])
    plan["imeso_preflight"] = inspected
    plan["fixed_candidates"] = {s["source"]: s["candidate"]["external_id"] for s in plan["sources"]}
    save(output / "prepared.json", plan)
    return plan


def claim_attempt(output, source):
    if source not in ("ibgp_open", "imeso_open"):
        raise ValueError("source outside authorized operation")
    marker = output / f"{source}.attempted"
    # O_EXCL is process-safe and survives restart; failure spends the attempt.
    with marker.open("x", encoding="utf-8") as stream:
        stream.write(datetime.now(timezone.utc).isoformat())


def configured_adapter():
    from dotenv import dotenv_values
    from app.tenderproof.security import TenderProofLimits, TenderProofSettings
    from app.tenderproof.solari_adapter import SolariBrowserAdapter, SolariConfig
    key = dotenv_values(BACKEND / ".env").get("SOLARI_API_KEY")
    if not key:
        raise ValueError("key missing in backend/.env")
    config = SolariConfig(api_key=key, base_url=OFFICIAL_API, region="us-west", recording=True,
                          stealth=False, proxy=None, captcha=False)
    settings = TenderProofSettings(limits=TenderProofLimits(total_timeout_s=180,
        max_attempts=1, max_candidates=1, max_documents=10, max_download_bytes=30*1024*1024,
        max_pages=60, replay_deadline_s=0, replay_poll_interval_s=1))

    class SingleSessionAdapter(SolariBrowserAdapter):
        def _new_client(self):
            from solari_browser import Solari
            return Solari(api_key=self.config.api_key, base_url=OFFICIAL_API, region="us-west",
                          max_attempts=1, timeout_ms=30000)

        def _launch_kwargs(self):
            return {**super()._launch_kwargs(), "retries": 0}

        def open_listing(self, url):
            raise RuntimeError("discovery Browser session is forbidden for this operation")

        def open_detail(self, url):
            html = super().open_detail(url)
            (OUTPUT / f"captured-detail-{self.capture_id}.html").write_text(html, encoding="utf-8")
            return html

        def download(self, url, *, max_bytes):
            try:
                if not equivalent_document_url(url, self.approved_document_url):
                    save(OUTPUT / "document-url-mismatch-private.json", {"approved": self.approved_document_url, "observed": url})
                    raise ValueError("document differs from preflight selection; no download authorized")
                return super().download(url, max_bytes=max_bytes)
            finally:
                # Do not bill browser time while parsing PDF locally.
                self.close()

    return SingleSessionAdapter(config, settings), settings


async def provider_readonly(config, session_ids):
    """GET and replay only, never release/create. 404 remains unknown."""
    from solari_browser import Solari
    from urllib.parse import quote
    results = []
    async with Solari(api_key=config.api_key, base_url=OFFICIAL_API, region="us-west",
                      max_attempts=1, timeout_ms=10000) as client:
        for session_id in session_ids:
            record = {"session_id_sha256": hashlib.sha256(session_id.encode()).hexdigest(), "queried_at": datetime.now(timezone.utc).isoformat()}
            for label, suffix in (("session", ""), ("replay", "/replay-url")):
                try:
                    response = await asyncio.wait_for(client.request("GET", "/sessions/" + quote(session_id, safe="") + suffix), timeout=10)
                    record[label] = {"http_status": response.status_code, "state": "unknown"}
                    if response.status_code == 200:
                        body = response.json()
                        state = body.get("status")
                        if label == "session" and state in ("active", "released", "expired", "unknown"):
                            record[label]["state"] = state
                        org = body.get("org")
                        if isinstance(org, str):
                            record[label]["org_sha256"] = hashlib.sha256(org.encode()).hexdigest()
                        if label == "replay":
                            record[label]["available"] = isinstance(body.get("url"), str)
                except Exception as exc:
                    record[label] = {"http_status": getattr(exc, "status", None), "state": "unknown",
                                     "error_type": type(exc).__name__}
            results.append(record)
    return results


def execute(plan, *, authorized=False, output=OUTPUT, only_source=None):
    if not authorized:
        raise PermissionError("specific user authorization required before Browser creation")
    if only_source not in (None, "ibgp_open", "imeso_open"):
        raise ValueError("source outside fixed operation")
    if plan.get("operation") != OPERATION or len(plan.get("sources", [])) != 2:
        raise ValueError("unexpected operation plan")
    if plan.get("fixed_candidates") != FIXED_CANDIDATES:
        raise ValueError("fixed candidates differ from reviewed operation")
    if {s["source"] for s in plan["sources"]} != set(FIXED_CANDIDATES):
        raise ValueError("source set differs from reviewed operation")
    # Fail before any resource if a required selected document is not eligible.
    if not all(s.get("eligible") for s in plan["sources"]):
        raise ValueError("preflight blocked: required source lacks eligible principal notice")
    os.environ["TENDERPROOF_ARTIFACT_DIR"] = str(output / "artifacts")
    os.environ["DATABASE_URL"] = "sqlite:///" + str(output / "isolated.sqlite3")
    from app.tenderproof.contracts import DiscoveredCandidate, TenderProofRun, ExecutionStatus
    from app.tenderproof.service import TenderProofService
    from app.tenderproof.store import TenderProofStore
    store = TenderProofStore()
    outcomes = []
    for source in plan["sources"]:
        if only_source and source["source"] != only_source:
            continue
        expected = plan["fixed_candidates"][source["source"]]
        candidate = DiscoveredCandidate.model_validate(source["candidate"])
        if candidate.external_id != expected or candidate.source != source["source"]:
            raise ValueError("fixed candidate identity changed")
        adapter, settings = configured_adapter()
        adapter.capture_id = expected
        adapter.approved_document_url = source["document"]["url_requested"]
        claim_attempt(output, source["source"])
        run = TenderProofRun(run_id=f"tpr-{OPERATION}-{expected}", owner_user_id=OWNER,
            source=source["source"], mode="real", is_synthetic_sample=False,
            candidates=[candidate], execution_status=ExecutionStatus.AWAITING_SELECTION,
            diagnostics=["Discovery seeded: " + str(source["candidate_origin"])])
        store.put_run(run)
        baseline = None
        origin = "no corresponding real baseline available"
        if expected == "704":
            path = BACKEND / ".tenderproof/real-baseline-704.json"
            if path.exists():
                saved = json.loads(path.read_text(encoding="utf-8"))
                if str(saved.get("snapshot", {}).get("external_id")) == "704":
                    baseline = saved["snapshot"]
                    origin = "preserved real connector baseline 704; not canonical publication"
        run = TenderProofService(store, settings).select_and_process(run.run_id, candidate.candidate_id,
            adapter, mode="real", baseline=baseline, baseline_origin=origin)
        try:
            reads = asyncio.run(provider_readonly(adapter.config, [s.session_id for s in run.sessions if s.session_id]))
        except Exception as exc:
            reads = [{"state": "unknown", "error_type": type(exc).__name__}]
        outcome = {"run_id": run.run_id, "execution_status": run.execution_status,
                   "validation_status": run.validation_status, "sessions": len(run.sessions),
                   "provider_readonly": reads, "cost_confirmed": None,
                   "catalog_publication": False, "artifact_sha256": run.artifact.sha256 if run.artifact else None}
        outcomes.append(outcome)
        save(output / "result.json", {"operation": OPERATION, "outcomes": outcomes})
        if run.execution_status == ExecutionStatus.FAILED or any(not s.closed for s in run.sessions):
            break  # no further spend after failure/unknown closure
    return outcomes


def reprocess_preserved_imeso():
    """Local-only correction, new snapshot/artifact copy; original remains intact."""
    from app.tenderproof.contracts import TenderProofRun
    from app.tenderproof.fields import extract_fields, semantic_hash
    from app.tenderproof.compare import compare
    from app.tenderproof.processing import extract_pages_isolated
    from app.tenderproof.store import TenderProofStore
    from app.tenderproof.validation import validate_identity
    original_root = BACKEND / ".tenderproof/browser-two-source-20260907-v3"
    original_path = original_root / "runs/tpr-browser-two-source-20260907-v3-139.json"
    run = TenderProofRun.model_validate_json(original_path.read_text(encoding="utf-8"))
    original_sha = hashlib.sha256(original_path.read_bytes()).hexdigest()
    before = run.field_map()["remuneracao"].model_dump(mode="json")
    content = (original_root / "artifacts" / Path(run.artifact.storage_path).name).read_bytes()
    if hashlib.sha256(content).hexdigest() != run.artifact.sha256:
        raise ValueError("preserved PDF hash mismatch")
    correction_root = BACKEND / ".tenderproof/browser-live-corrections-20260907"
    os.environ["TENDERPROOF_ARTIFACT_DIR"] = str(correction_root / "artifacts")
    store = TenderProofStore()
    store.save_artifact_file(run.artifact, content)
    pages, *_ = extract_pages_isolated(content, artifact_id=run.artifact.artifact_id,
                                      owner_id=str(OWNER), max_pages=60, max_bytes=30*1024*1024)
    run.run_id += "-corrected-offline"
    candidate = next(c for c in run.candidates if c.candidate_id == run.selected_candidate_id)
    run.fields = extract_fields(candidate=candidate, artifact=run.artifact, pages=pages)
    run.validation = validate_identity(candidate=candidate, pages=pages,
        document_title=run.document.title, document_url=run.document.url_final or run.document.url_requested)
    run.validation_status = run.validation.status
    run.semantic_hash = semantic_hash(run.fields)
    run.comparison = compare(baseline=None, baseline_collected_at=None,
        baseline_origin="No matching baseline; corrected offline extraction", fields=run.fields)
    run.updated_at = datetime.now(timezone.utc)
    run.diagnostics.append("Offline correction of table fee mistaken as salary; original snapshot retained; no new Browser")
    store.put_run(run)
    report = {"original_snapshot_sha256": original_sha, "corrected_run_id": run.run_id,
              "document_sha256": run.artifact.sha256, "new_resources_created": 0,
              "before": before, "after": run.field_map()["remuneracao"].model_dump(mode="json")}
    save(correction_root / "correction.json", report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute-authorized", action="store_true")
    parser.add_argument("--source", choices=tuple(FIXED_CANDIDATES))
    parser.add_argument("--reprocess-preserved-imeso", action="store_true")
    args = parser.parse_args()
    if args.reprocess_preserved_imeso:
        report = reprocess_preserved_imeso()
        print(json.dumps({"run_id": report["corrected_run_id"], "remuneracao": report["after"]["state"], "new_resources_created": 0}))
    elif args.execute_authorized:
        plan = json.loads((OUTPUT / "prepared.json").read_text(encoding="utf-8"))
        print(json.dumps(execute(plan, authorized=True, only_source=args.source), default=str))
    else:
        plan = prepare()
        print(json.dumps({"operation": OPERATION, "max_sessions": 2,
            "eligible": [{"source": s["source"], "eligible": s["eligible"], "reason": s.get("blocked_reason")} for s in plan["sources"]]}))


if __name__ == "__main__":
    main()
