"""Bounded live FAPEAM contract run against the current public AJAX route."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.tenderproof.fapeam_adapter import FapeamAdapter, LIVE_LISTING  # noqa: E402
from app.tenderproof.http_driver import BoundedHTTPDriver  # noqa: E402


OUTPUT = ROOT / ".tenderproof/product-completion/delivery-failed-sources-20260909/fapeam-live-adapter-run.json"


def sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def main() -> int:
    adapter = FapeamAdapter()
    driver = BoundedHTTPDriver(adapter.source)
    try:
        listing = driver.open_listing(LIVE_LISTING)
        page = adapter.parse_listing(listing, LIVE_LISTING, limit=5)
        if not page.candidates:
            raise ValueError("listagem FAPEAM vigente sem candidato")
        candidate = page.candidates[0]
        driver.set_candidate(candidate)
        detail = driver.open_detail(candidate.detail_url_observed)
        documents = adapter.documents(detail, candidate)
        for document in documents:
            adapter.validate_document_url(document.url_requested, candidate)
        chosen = adapter.choose_document(documents)
        pdf = driver.download(chosen.url_requested, max_bytes=8 * 1024 * 1024)
        result = {
            "schema": "delivery_failed_fapeam_live_adapter_run",
            "observed_at": "2026-09-09T20:40:00Z",
            "listing_url": LIVE_LISTING,
            "listing_sha256": sha256(listing.encode()),
            "listing_bytes": len(listing.encode()),
            "candidate": {
                "external_id": candidate.external_id,
                "title": candidate.title_observed,
                "detail_url": candidate.detail_url_observed,
            },
            "detail_sha256": sha256(detail.encode()),
            "detail_bytes": len(detail.encode()),
            "documents": [
                {"title": item.title, "kind": item.kind, "url": item.url_requested}
                for item in documents
            ],
            "chosen_document": {
                "title": chosen.title,
                "kind": chosen.kind,
                "url": chosen.url_requested,
                "pdf_sha256": sha256(pdf.content),
                "pdf_bytes": len(pdf.content),
            },
            "publication": False,
            "login": False,
        }
    finally:
        driver.close()
    OUTPUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "contract_validated", "source": "fapeam_selection", "output": str(OUTPUT)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
