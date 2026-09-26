"""Bounded delegated review of pending PDFs in the next-lot packet.

Only pending URLs already recorded in the packet are inspected. Downloads go
through the source adapter and BoundedHTTPDriver, preserving host, redirect,
byte, and source-specific TLS contracts. The script does not mutate state or
publish.

Detailed review is bounded to FUMARC 2026 and the next Legalle candidate.
Other selected candidates are represented by source/key headers and counts only
so pending publication titles cannot reproduce applicant names.
"""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, "/app")

from app.tenderproof.contracts import DiscoveredCandidate
from app.tenderproof.http_driver import BoundedHTTPDriver


INPUT = Path("/app/.tenderproof/product-completion/delivery-next-20260909.json")
OUTPUT = Path("/app/.tenderproof/product-completion/delivery-next-pending-review-20260909.json")
MAX_BYTES = 20 * 1024 * 1024
REVIEW_SOURCES = {"fumarc_open", "legalle_open"}


def pdf_pages(data: bytes) -> list[str]:
    try:
        from pypdf import PdfReader
    except ImportError:
        return []
    reader = PdfReader(BytesIO(data))
    return [(page.extract_text() or "") for page in reader.pages]


def excerpt(text: str, terms: list[str]) -> str | None:
    compact = " ".join(text.split())
    lower = compact.lower()
    for term in terms:
        if not term:
            continue
        position = lower.find(term.lower())
        if position >= 0:
            start = max(0, position - 180)
            return compact[start : min(len(compact), position + 520)]
    return compact[:700] if compact else None


def effect_assessment(title: str, excerpts: list[dict]) -> str:
    lower = title.lower()
    text = " ".join((item.get("excerpt") or "") for item in excerpts).lower()
    if "classificação final" in lower:
        return "classification/result document; no registration or exam-date effect identified in extracted text"
    if "cronograma" in lower:
        return "schedule publication date effect; verify that registration and exam events remain unchanged"
    if "retificação" in lower and ("carga horária" in text or "vencimento" in text or "remuneração" in text):
        return "cargo/workload or remuneration effect detected; review field-level change before applying"
    return "document effect requires field-level review"


def candidate_for_driver(candidate: dict) -> DiscoveredCandidate:
    identity = candidate.get("identity") or {}
    observed = identity.get("observed_at") or datetime.now(timezone.utc).isoformat()
    return DiscoveredCandidate(
        candidate_id=f"{candidate.get('source')}-{candidate.get('candidate_key')}",
        source=candidate["source"],
        external_id=str(identity.get("external_id") or candidate.get("candidate_key")),
        title_observed=identity.get("title_observed"),
        selection_label_observed=identity.get("selection_label_observed"),
        detail_url_observed=identity["detail_url_observed"],
        observed_at=observed,
    )


def fetched_pdf(candidate: dict, url: str) -> tuple[bytes, str, list[str], list[str]]:
    driver = BoundedHTTPDriver(candidate["source"])
    try:
        driver.set_candidate(candidate_for_driver(candidate))
        result = driver.download(url, max_bytes=MAX_BYTES)
        pages = pdf_pages(result.content) if result.content.startswith(b"%PDF") else []
        return result.content, result.content_type or "", pages, driver.diagnostics()
    finally:
        driver.close()


def preserved_fumarc_support(candidate: dict) -> dict | None:
    if candidate.get("source") != "fumarc_open" or candidate.get("candidate_key") != "54":
        return None
    packet_fields = [field for field in candidate.get("fields", []) if field.get("state") == "supported"]
    if packet_fields:
        return {
            "status": "packet_field_evidence",
            "source": "delivery-next packet",
            "fields": [
                {
                    "field_name": field.get("name"),
                    "value": field.get("value"),
                    "evidence": field.get("evidence", []),
                }
                for field in packet_fields
            ],
        }
    paths = (
        Path("/var/lib/observador/tenderproof/product-completion/fumarc/supplementary-service/combined-fields.json"),
        Path("/app/.tenderproof/product-completion/fumarc/supplementary-service/combined-fields.json"),
    )
    path = next((item for item in paths if item.exists()), None)
    if path is None:
        return {"status": "preserved_reference_missing", "paths_checked": [str(item) for item in paths]}
    fields = json.loads(path.read_text(encoding="utf-8"))
    supported = []
    for field in fields:
        if field.get("state") != "supported":
            continue
        supported.append(
            {
                "field_name": field.get("field_name"),
                "value": field.get("value"),
                "evidence": [
                    {
                        "page": evidence.get("page_number"),
                        "sha256": evidence.get("document_sha256"),
                        "url": evidence.get("source_url"),
                        "snippet": evidence.get("snippet"),
                    }
                    for evidence in field.get("evidence", [])
                ],
            }
        )
    return {"status": "preserved_field_evidence", "path": str(path), "fields": supported}


def identity_terms(candidate: dict) -> list[str]:
    source = candidate.get("source")
    if source == "fumarc_open":
        return ["CREA-MG", "01/2026"]
    if source == "legalle_open":
        return ["GARIBALDI", "04/2025"]
    identity = candidate.get("identity") or {}
    return [identity.get("title_observed") or "", identity.get("external_id") or ""]


def page_is_safe_for_excerpt(text: str) -> bool:
    lowered = text.lower()
    # Classification annex pages contain names, registration numbers and birth
    # dates. Keep the document identity header, but do not reproduce list rows.
    return not any(
        marker in lowered
        for marker in ("data nasc.", "data nasc", "inscrição candidato nota", "candidato nota final")
    )


def detailed_review(candidate: dict, pending: dict) -> dict:
    identity = candidate.get("identity") or {}
    title = pending.get("title") or ""
    terms = identity_terms(candidate)
    item = {
        "source": candidate.get("source"),
        "candidate_key": candidate.get("candidate_key"),
        "run_id": candidate.get("run_id"),
        "candidate_header": identity.get("title_observed"),
        "kind": pending.get("kind"),
        "title": title,
        "url": pending.get("url"),
        "host": urlparse(pending.get("url") or "").hostname,
    }
    try:
        data, content_type, pages, diagnostics = fetched_pdf(candidate, pending["url"])
        full_text = "\n".join(pages)
        excerpts = [
            {"page": index + 1, "excerpt": excerpt(text, terms)}
            for index, text in enumerate(pages)
            if page_is_safe_for_excerpt(text) and excerpt(text, terms)
        ][:3]
        item.update(
            {
                "status": "fetched_and_extracted" if pages else "fetched_extraction_unavailable",
                "http_content_type": content_type,
                "sha256": hashlib.sha256(data).hexdigest(),
                "bytes": len(data),
                "pages": len(pages),
                "identity_match": any(term and term.lower() in full_text.lower() for term in terms),
                "page_excerpts": excerpts,
                "effect_assessment": effect_assessment(title, excerpts),
                "driver_diagnostics": diagnostics,
            }
        )
    except Exception as error:  # bounded diagnostic; no response body or secrets
        item.update(
            {
                "status": "fetch_or_extract_failed",
                "error_type": type(error).__name__,
                "error": str(error),
                "effect_assessment": "unresolved because the registered PDF could not be fetched or extracted",
            }
        )
    return item


def main() -> None:
    packet = json.loads(INPUT.read_text(encoding="utf-8"))
    results = []
    pending_total = 0
    reviewed_total = 0
    deferred_headers = []
    for candidate in packet.get("selected", []):
        pending_documents = candidate.get("pending_documents") or []
        pending_total += len(pending_documents)
        if candidate.get("source") not in REVIEW_SOURCES:
            deferred_headers.append(
                {
                    "source": candidate.get("source"),
                    "candidate_key": candidate.get("candidate_key"),
                    "run_id": candidate.get("run_id"),
                    "pending_document_count": len(pending_documents),
                    "status": "deferred_out_of_bounded_review",
                    "reason": "detailed review limited to FUMARC 2026 and next Legalle candidate; titles omitted",
                }
            )
            continue
        for pending in pending_documents:
            results.append(detailed_review(candidate, pending))
            reviewed_total += 1

    report = {
        "generated_at": "2026-09-09",
        "method": "bounded_source_adapter_fetch_of_registered_pending_urls",
        "publication_performed": False,
        "state_mutation_performed": False,
        "bounded_review_sources": sorted(REVIEW_SOURCES),
        "selected_pending_document_count": pending_total,
        "reviewed_document_count": reviewed_total,
        "deferred_candidate_headers": deferred_headers,
        "preserved_support": [
            support
            for candidate in packet.get("selected", [])
            if (support := preserved_fumarc_support(candidate)) is not None
        ],
        "results": results,
        "real_gaps": [
            "This evidence does not approve or apply field changes.",
            "A fetched PDF with identity_match=false must not be associated with the candidate.",
            "Deferred candidates retain their pending counts; their publication titles are omitted from this packet.",
            "Pending documents without extracted text remain unresolved and need a compatible parser or directed delegated review.",
        ],
    }
    OUTPUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "output": str(OUTPUT),
        "selected_pending_documents": pending_total,
        "reviewed_documents": reviewed_total,
        "statuses": [item["status"] for item in results],
    }))


if __name__ == "__main__":
    main()
