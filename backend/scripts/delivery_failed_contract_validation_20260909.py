"""Validate one bounded current candidate per source against existing adapters.

This consumes the read-only official captures made by
delivery_failed_sources_20260909.py. It performs the same listing, identity,
document extraction and destination validation used by the source contracts;
it does not publish, log in, or start a paid session.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

from bs4 import UnicodeDammit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.tenderproof.source_adapters import SOURCE_ADAPTERS


CAPTURE = ROOT / ".tenderproof/product-completion/delivery-failed-sources-20260909"
OUTPUT = CAPTURE / "adapter-contract-validation.json"
TARGETS = (
    "admtec_open",
    "rbo_open",
    "fatec_selection",
    "fapese_selection",
    "fapesb_selection",
    "fapesp_selection",
    "fapergs_selection",
)


def _html(path: Path) -> str:
    return UnicodeDammit(path.read_bytes(), is_html=True).unicode_markup or ""


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    report = json.loads((CAPTURE / "report.json").read_text(encoding="utf-8"))
    by_source = {item["source"]: item for item in report["sources"]}
    results = []
    for source in TARGETS:
        adapter = SOURCE_ADAPTERS[source]
        capture = by_source[source]
        listing = capture["listing"][0]
        listing_path = CAPTURE / listing["file"]
        result = {
            "source": source,
            "listing_url": listing["requested_url"],
            "listing_file": listing["file"],
            "listing_sha256": _sha(listing_path),
            "adapter": type(adapter).__name__,
        }
        try:
            listing_html = _html(listing_path)
            page = adapter.parse_listing(listing_html, listing["requested_url"], limit=20)
            if not page.candidates:
                raise ValueError("nenhum candidato observável na listagem capturada")
            candidate = page.candidates[0]
            details = capture.get("details", [])
            detail_capture = next(
                (item for item in details if item["url"] == candidate.detail_url_observed),
                None,
            )
            if detail_capture:
                detail_path = CAPTURE / detail_capture["file"]
                detail_html = _html(detail_path)
                detail_url = detail_capture["url"]
                result.update({
                    "detail_file": detail_capture["file"],
                    "detail_sha256": _sha(detail_path),
                })
            else:
                detail_path = listing_path
                detail_html = listing_html
                detail_url = candidate.detail_url_observed
            adapter.confirm_identity(candidate, detail_html, detail_url)
            documents = adapter.documents(detail_html, candidate)
            for document in documents:
                adapter.validate_document_url(document.url_requested, candidate)
            result.update({
                "status": "contract_validated",
                "candidate_external_id": candidate.external_id,
                "candidate_title": candidate.title_observed,
                "detail_url": candidate.detail_url_observed,
                "documents": [
                    {
                        "title": document.title,
                        "kind": document.kind,
                        "url": document.url_requested,
                    }
                    for document in documents
                ],
            })
            try:
                chosen = adapter.choose_document(documents)
            except ValueError as exc:
                result["document_choice_error"] = str(exc)
            else:
                result["chosen_document"] = {
                    "title": chosen.title,
                    "kind": chosen.kind,
                    "url": chosen.url_requested,
                }
        except Exception as exc:  # report every bounded source without stopping the batch
            result.update({"status": "contract_failed", "error": f"{type(exc).__name__}: {exc}"})
        results.append(result)
    OUTPUT.write_text(
        json.dumps(
            {
                "schema": "delivery_failed_adapter_contract_validation",
                "observed_at": "2026-09-09T20:29:57Z",
                "scope": "one candidate per source from existing bounded official captures",
                "publication": False,
                "login": False,
                "sources": results,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"validated": sum(item["status"] == "contract_validated" for item in results), "total": len(results), "output": str(OUTPUT)}, ensure_ascii=False))
    return 0 if all(item["status"] == "contract_validated" for item in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
