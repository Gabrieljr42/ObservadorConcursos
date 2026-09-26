"""Compose read-only review cases from the next-lot packet and PDF review.

This creates reviewable payloads for the first four ranked sources. It does not
call the publication service, write the catalogue, or approve a proposal.
"""

from __future__ import annotations

import json
from pathlib import Path


INPUT = Path("/app/.tenderproof/product-completion/delivery-next-20260909.json")
PENDING_REVIEW = Path("/app/.tenderproof/product-completion/delivery-next-pending-review-20260909.json")
OUTPUT = Path("/app/.tenderproof/product-completion/delivery-next-review-cases-20260909.json")
LIMIT = 4


def main() -> None:
    packet = json.loads(INPUT.read_text(encoding="utf-8"))
    pending_report = json.loads(PENDING_REVIEW.read_text(encoding="utf-8"))
    selected = packet.get("selected", [])[:LIMIT]
    reviewed = pending_report.get("results", [])
    cases = []
    for candidate in selected:
        source = candidate.get("source")
        key = candidate.get("candidate_key")
        identity = candidate.get("identity") or {}
        fields = {field.get("name"): field for field in candidate.get("fields", [])}
        docs = [
            item
            for item in reviewed
            if item.get("source") == source and str(item.get("candidate_key")) == str(key)
        ]
        cases.append(
            {
                "case_id": f"delivery-next-{source}-{key}",
                "status": "ready_for_normal_revalidation",
                "approval_state": "not_approved",
                "publication_performed": False,
                "state_mutation_performed": False,
                "candidate": {
                    "source": source,
                    "source_id": candidate.get("source_id"),
                    "candidate_key": key,
                    "identity": candidate.get("identity"),
                    "document": candidate.get("document"),
                    "fields": candidate.get("fields"),
                    "acquired_documents": candidate.get("acquired_documents"),
                    "ranking": candidate.get("ranking"),
                    "recency": candidate.get("recency"),
                    "publication_state": candidate.get("publication_state"),
                },
                "proposal_payload": {
                    "source_id": candidate.get("source_id"),
                    "source": source,
                    "external_id": identity.get("external_id"),
                    "titulo": (fields.get("titulo") or {}).get("value"),
                    "orgao": (fields.get("orgao") or {}).get("value"),
                    "edital_numero": (fields.get("edital_numero") or {}).get("value"),
                    "inscricao_inicio": (fields.get("inscricao_inicio") or {}).get("value"),
                    "inscricao_fim": (fields.get("inscricao_fim") or {}).get("value"),
                    "detail_url": identity.get("detail_url_observed"),
                    "document_url": (candidate.get("document") or {}).get("url"),
                    "document_sha256": (candidate.get("document") or {}).get("sha256"),
                    "fields": candidate.get("fields"),
                    "document_candidates": [
                        {
                            "kind": item.get("kind"),
                            "title": item.get("title"),
                            "url": item.get("url"),
                            "sha256": item.get("sha256"),
                            "status": item.get("status"),
                            "identity_match": item.get("identity_match"),
                        }
                        for item in docs
                    ],
                },
                "pending_document_review": {
                    "pending_document_count": candidate.get("pending_document_count", len(candidate.get("pending_documents") or [])),
                    "registered_documents": candidate.get("pending_documents"),
                    "bounded_results": docs,
                },
                "real_gaps": [
                    "Normal revalidation must re-read the preserved artifact and current identity before any proposal is approved.",
                    "Unknown fields remain unknown and are not filled from absence of evidence.",
                ],
            }
        )
    report = {
        "generated_at": "2026-09-09",
        "method": "read_only_composition_from_preserved_packet_and_bounded_pending_review",
        "limit": LIMIT,
        "publication_performed": False,
        "state_mutation_performed": False,
        "cases": cases,
        "real_gaps": [
            "This file contains review payloads only; it does not create publication proposals.",
            "FUMARC Errata effect still requires field-level comparison before approval.",
            "Legalle classification and schedule documents are evidentiary updates; list rows are intentionally omitted from this packet.",
            "FAPED remains subject to positive employment-selection scope confirmation before salary/vacancy mapping.",
        ],
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(OUTPUT), "cases": len(cases), "sources": [case["candidate"]["source"] for case in cases]}))


if __name__ == "__main__":
    main()
