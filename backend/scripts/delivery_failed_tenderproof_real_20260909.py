"""Bounded real TenderProof runs for the currently viable delivery sources.

This script deliberately uses the durable TenderProofService flow: discovery is
committed, an observed candidate is selected, the principal PDF is acquired,
pages and fields are persisted, and a review manifest is written from the
persisted run plus the complete document list observed in the same detail.
It never writes canonical catalogue tables or publishes a result.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / ".tenderproof" / "product-completion" / "delivery-failed-tenderproof-20260909"
ROOT.mkdir(parents=True, exist_ok=True)
os.environ["TENDERPROOF_ARTIFACT_DIR"] = str(ROOT / "artifacts")
os.environ["TENDERPROOF_PROCESSING_DIR"] = str(ROOT / "processing")
os.environ["TENDERPROOF_PROCESSING_MODE"] = "local"
os.environ["TENDERPROOF_BROWSER_LIVE_ENABLED"] = "false"

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.tenderproof.contracts import TenderProofRun
from app.tenderproof.document_identity import document_manifest
from app.tenderproof.http_driver import BoundedHTTPDriver
from app.tenderproof.security import TenderProofLimits, TenderProofSettings
from app.tenderproof.service import TenderProofService
from app.tenderproof.source_adapters import get_source_adapter
from app.tenderproof.store import TenderProofStore


TARGETS = {
    "rbo_open": "203",
    "fatec_selection": "2026/3010088-01",
    "fapese_selection": "007/2026",
    "fapesb_selection": "https://www.fapesb.ba.gov.br/wp-content/uploads/2019/08/EDITAL_DEFINITIVO_REDA_2026.pdf",
    "fapesp_selection": "4470",
    "fapergs_selection": "selecao-2025",
    "fapeam_selection": "321428",
}


class CapturingDriver(BoundedHTTPDriver):
    """Retain the identity-confirmed detail for the review manifest only."""

    def __init__(self, source, settings):
        super().__init__(source, settings)
        self.last_detail_html = None
        self.last_detail_url = None

    def open_detail(self, url):
        html = super().open_detail(url)
        self.last_detail_html = html
        self.last_detail_url = url
        return html


def settings_for(adapter):
    # FAPESB currently exposes 29 links in one REDA section. Keeping this
    # ceiling above the observed count preserves the full manifest and makes
    # any future excess an explicit failure instead of silent truncation.
    limits = TenderProofLimits(
        max_candidates=5,
        max_navigations=12,
        max_attempts=2,
        max_download_bytes=30 * 1024 * 1024,
        max_documents=40,
        max_concurrency=1,
        total_timeout_s=300,
        max_pages=120,
    )
    return TenderProofSettings(allowlist_hosts=tuple(adapter.allowed_hosts), limits=limits)


def find_candidate(run, expected):
    for candidate in run.candidates:
        if candidate.external_id == expected:
            return candidate
    # FAPEAM's current JSON parser preserves the numeric ID as a string; this
    # fallback is only for a harmless leading-zero representation.
    for candidate in run.candidates:
        if str(candidate.external_id).lstrip("0") == str(expected).lstrip("0"):
            return candidate
    return None


def fields_manifest(run):
    return [
        {
            "field_name": field.field_name,
            "state": field.state.value,
            "value": field.value,
            "reason": field.reason,
            "evidence": [e.model_dump(mode="json") for e in field.evidence],
        }
        for field in run.fields
    ]


def run_one(source, expected, listing_url=None):
    adapter = get_source_adapter(source)
    settings = settings_for(adapter)
    store = TenderProofStore()
    service = TenderProofService(store, settings)
    listing_driver = CapturingDriver(source, settings)
    listing = service.start_discovery(
        listing_driver,
        source=source,
        listing_url=listing_url or adapter.listing_urls[0],
        mode="real",
        owner_user_id=1,
    )
    durable_listing = store.get_run(listing.run_id)
    row = {
        "source": source,
        "owner_user_id": 1,
        "listing_url": listing_url or adapter.listing_urls[0],
        "listing_run_id": listing.run_id,
        "listing_persisted": durable_listing is not None,
        "listing_status": listing.execution_status.value,
        "listing_error": listing.error,
        "candidate_count": len(listing.candidates),
        "candidate_ids": [c.external_id for c in listing.candidates],
        "selection_expected": expected,
        "publication": False,
        "login": False,
    }
    if durable_listing is None:
        row["status"] = "failed_persistence"
        return row
    candidate = find_candidate(durable_listing, expected)
    if candidate is None:
        row["status"] = "candidate_not_in_bounded_sample"
        return row

    detail_driver = CapturingDriver(source, settings)
    processed = service.select_and_process(durable_listing.run_id, candidate.candidate_id, detail_driver)
    durable = store.get_run(processed.run_id)
    row.update(
        run_id=processed.run_id,
        run_persisted=durable is not None,
        execution_status=processed.execution_status.value,
        validation_status=processed.validation_status.value,
        error=processed.error,
        selected_candidate=candidate.model_dump(mode="json"),
        document=processed.document.model_dump(mode="json") if processed.document else None,
        artifact=processed.artifact.model_dump(mode="json") if processed.artifact else None,
        total_pages=processed.total_pages,
        processed_pages=processed.processed_pages,
        truncated=processed.truncated,
        validation=processed.validation.model_dump(mode="json"),
        fields=fields_manifest(processed),
        field_count=len(processed.fields),
    )
    if processed.artifact:
        content = store.load_artifact_bytes(processed.artifact)
        row["artifact_durable"] = content is not None and hashlib.sha256(content).hexdigest() == processed.artifact.sha256

    observed = []
    if detail_driver.last_detail_html is not None:
        try:
            observed = adapter.documents(detail_driver.last_detail_html, candidate)
        except Exception as exc:  # the durable run remains authoritative
            row["manifest_error"] = f"{type(exc).__name__}: {exc}"
    row["observed_documents"] = [document_manifest(doc) for doc in observed]
    selected_identity = document_manifest(processed.document) if processed.document else None
    pending = [doc for doc in row["observed_documents"] if doc != selected_identity]
    row["review_manifest"] = {
        "run_id": processed.run_id,
        "source": source,
        "owner_user_id": 1,
        "execution_status": processed.execution_status.value,
        "validation_status": processed.validation_status.value,
        "selected_document": selected_identity,
        "artifact_sha256": processed.artifact.sha256 if processed.artifact else None,
        "fields": row["fields"],
        "documents": row["observed_documents"],
        "documents_truncated": False,
        "pending_documents": pending,
        "pending_count": len(pending),
        "review_required": bool(pending) or processed.validation_status.value != "valid",
    }
    manifest_path = ROOT / "review-manifests" / f"{source}-{processed.run_id}.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(row["review_manifest"], ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    row["review_manifest_path"] = str(manifest_path)
    row["status"] = "completed" if processed.execution_status.value == "completed" else "failed"
    return row


def main():
    began = time.monotonic()
    results = []
    for source, expected in TARGETS.items():
        listing_url = None
        if source == "fapeam_selection":
            listing_url = "https://www.fapeam.am.gov.br/editais/?aba=vigentes&p=1"
        try:
            result = run_one(source, expected, listing_url)
        except Exception as exc:
            result = {"source": source, "owner_user_id": 1, "status": "unhandled_error", "error": f"{type(exc).__name__}: {exc}"}
        results.append(result)
        print(source, result.get("run_id"), result.get("status"), result.get("execution_status"), result.get("validation_status"), result.get("error"), flush=True)
    report = {
        "schema": "delivery_failed_tenderproof_real_20260909",
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "scope": "one explicit public candidate per viable source; durable TenderProofService flow; no publication",
        "owner_user_id": 1,
        "root": str(ROOT),
        "duration_s": round(time.monotonic() - began, 3),
        "sources": results,
    }
    report_path = ROOT / "tenderproof-real-runs.json"
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    print(report_path, flush=True)


if __name__ == "__main__":
    main()
