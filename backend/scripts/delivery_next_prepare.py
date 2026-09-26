"""Prepare a bounded, read-only next delivery lot from preserved TenderProof runs.

This script is intentionally limited to evidence preparation.  It never creates a
proposal, approves a proposal, changes the catalogue, or acquires a document.
Run it in the API container so the operational volume and canonical database are
available.  The output is a review packet that can be inspected before any
publication action is considered.
"""

from __future__ import annotations

import argparse
import json
import re
import sqlite3
import sys
from datetime import date
from pathlib import Path
from unicodedata import combining, normalize as unicode_normalize

sys.path.insert(0, "/app")

from sqlalchemy import text

from app.database import engine


ROOT = Path("/var/lib/observador/tenderproof")
DEFAULT_OUTPUT = Path("/app/.tenderproof/product-completion/delivery-next-20260909.json")
AS_OF = date(2026, 9, 9)
DETAILED_PENDING_SOURCES = {"fumarc_open", "legalle_open"}


def ro_reader(name: str) -> sqlite3.Connection:
    connection = sqlite3.connect((ROOT / name).as_uri() + "?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    return connection


def evidence_for(field: dict) -> list[dict]:
    return [
        {
            "page": item.get("page_number"),
            "snippet": item.get("snippet"),
            "document_sha256": item.get("document_sha256"),
            "source_url": item.get("source_url"),
            "method": item.get("method"),
        }
        for item in field.get("evidence", [])
    ]


def identity_token(value: object) -> str:
    text_value = unicode_normalize("NFKD", str(value or ""))
    text_value = "".join(char for char in text_value if not combining(char))
    return re.sub(r"[^a-z0-9]+", "", text_value.lower())


def year_score(candidate: dict, supported: dict) -> int:
    """Use edital/date/observation years to rank recent material deterministically."""
    edital_values = [
        supported.get("edital_numero"),
        supported.get("edital_data"),
        candidate.get("title_observed"),
    ]
    years = [
        int(match)
        for value in edital_values
        for match in re.findall(r"(?:20|19)\d{2}", str(value or ""))
        if 1900 <= int(match) <= AS_OF.year + 1
    ]
    if years:
        return max(years)
    observed_years = [
        int(match)
        for match in re.findall(r"(?:20|19)\d{2}", str(candidate.get("observed_at") or ""))
        if 1900 <= int(match) <= AS_OF.year + 1
    ]
    return max(observed_years, default=0)


def candidate_payload(
    row: sqlite3.Row,
    run: dict,
    pending: list | None,
    source_id: int | None,
    recency: str,
    ranking: dict,
    acquired_documents: list[dict],
) -> dict:
    fields = []
    for field in run.get("fields", []):
        item = {
            "name": field.get("field_name"),
            "state": field.get("state"),
            "value": field.get("value"),
            "original_value": field.get("original_value"),
            "reason": field.get("reason"),
            "evidence": evidence_for(field),
        }
        fields.append(item)
    candidate = json.loads(row["candidate"])
    artifact = run.get("artifact") or {}
    pending_documents = pending or []
    if row["source"] not in DETAILED_PENDING_SOURCES:
        # Keep count/kind headers for deferred review while omitting publication
        # titles and URLs that may contain applicant names or birth data.
        pending_documents = [
            {"kind": document.get("kind"), "status": "title_and_url_omitted_from_packet"}
            for document in pending_documents
        ]
    return {
        "source": row["source"],
        "source_id": source_id,
        "candidate_key": row["candidate_key"],
        "run_id": row["last_run_id"],
        "identity": {
            "external_id": candidate.get("external_id"),
            "title_observed": candidate.get("title_observed"),
            "detail_url_observed": candidate.get("detail_url_observed"),
            "selection_label_observed": candidate.get("selection_label_observed"),
            "observed_at": candidate.get("observed_at"),
        },
        "document": {
            "url": artifact.get("url_final"),
            "sha256": artifact.get("sha256"),
            "pages": artifact.get("pages"),
            "title": artifact.get("title"),
        },
        "execution": {
            "status": run.get("execution_status"),
            "validation": run.get("validation_status"),
            "sample_note": run.get("sample_note"),
        },
        "fields": fields,
        "pending_documents": pending_documents,
        "pending_document_count": len(pending or []),
        "acquired_documents": acquired_documents,
        "publication_state": "absent_from_catalogue",
        "recency": recency,
        "ranking": ranking,
        "scope_review": (
            "selection_source; confirm whether this is an employment selection before mapping salary or vacancies"
            if row["source"].endswith("_selection")
            else "public selection document; confirm applicable employment fields from the document"
        ),
    }


def ranking_sort_key(item: dict) -> tuple:
    """Order live/upcoming material, then edital year, then recency detail.

    A missing registration end is intentionally represented by recency_rank=0,
    but that signal comes after year_score.  Thus a 2026 candidate whose date
    was not extracted remains ahead of an old 2018/2014 candidate, while a
    known current registration still wins over an otherwise equal-year
    unknown candidate.
    """
    return (
        item["active_priority"],
        item["year_score"],
        item["recency_rank"],
        item["registration_end"][:10] if item["registration_end"] else "",
        item["registration_start"][:10] if item["registration_start"] else "",
        item["field_score"],
        item["source"],
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=8)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    if not 1 <= args.limit <= 8:
        raise SystemExit("--limit must be between 1 and 8")

    continuous = ro_reader("continuous.sqlite3")
    operational = ro_reader("operational.sqlite3")

    with engine.connect() as connection:
        source_rows = connection.execute(text("SELECT id, source_type FROM sources")).mappings().all()
        source_ids = {row["source_type"]: row["id"] for row in source_rows}
        published = connection.execute(
            text("SELECT source_id, external_id, titulo, orgao, edital_numero, link_pagina FROM concursos")
        ).mappings().all()
    published_pairs = {(row["source_id"], str(row["external_id"])) for row in published if row["external_id"]}
    published_source_ids = {row["source_id"] for row in published}
    published_identity_keys = {
        (
            identity_token(row["titulo"]),
            identity_token(row["orgao"]),
            identity_token(row["edital_numero"]),
        )
        for row in published
        if row["titulo"] and row["orgao"] and row["edital_numero"]
    }
    published_urls = {row["link_pagina"] for row in published if row["link_pagina"]}
    acquired_by_candidate: dict[tuple[str, str], list[dict]] = {}
    for row in continuous.execute(
        "SELECT source, candidate_key, document_key, document, sha256, run_id "
        "FROM acquired_document_state ORDER BY source, candidate_key, document_key"
    ):
        document = row["document"]
        try:
            document = json.loads(document)
        except (TypeError, json.JSONDecodeError):
            document = {"raw": document}
        acquired_by_candidate.setdefault((row["source"], row["candidate_key"]), []).append(
            {
                "document_key": row["document_key"],
                "document": document,
                "sha256": row["sha256"],
                "run_id": row["run_id"],
            }
        )

    eligible: list[dict] = []
    rejected: list[dict] = []
    for row in continuous.execute("SELECT * FROM known_candidates ORDER BY source, candidate_key"):
        source_id = source_ids.get(row["source"])
        run_row = operational.execute(
            "SELECT payload FROM runs WHERE run_id = ?", (row["last_run_id"],)
        ).fetchone()
        if not run_row:
            continue
        run = json.loads(run_row["payload"])
        review_row = continuous.execute(
            "SELECT pending_documents FROM document_review_state "
            "WHERE source = ? AND candidate_key = ? AND owner = ? AND mode = ?",
            (row["source"], row["candidate_key"], row["owner"], row["mode"]),
        ).fetchone()
        pending = json.loads(review_row["pending_documents"]) if review_row else None
        fields = {field["field_name"]: field for field in run.get("fields", [])}
        supported = {
            name: field.get("value")
            for name, field in fields.items()
            if field.get("state") == "supported"
        }
        candidate = json.loads(row["candidate"])
        external_id = candidate.get("external_id")
        reason = None
        # A completed run with a preserved artifact is eligible for the normal
        # publication revalidation path even when its historical validation
        # status is partial/pending.  The publication gate re-reads the bytes
        # and validates the current identity; requiring historical `valid`
        # here would hide candidates that have three supported identity fields
        # and only need that ordinary revalidation.
        if run.get("execution_status") != "completed":
            reason = "run_not_completed"
        elif not run.get("artifact"):
            reason = "completed_run_without_preserved_artifact"
        elif not all(supported.get(name) for name in ("titulo", "orgao", "edital_numero")):
            reason = "identity_fields_incomplete"
        elif not all(fields[name].get("evidence") for name in ("titulo", "orgao", "edital_numero")):
            reason = "identity_fields_without_documentary_evidence"
        elif source_id is None:
            reason = "source_identity_not_mapped"
        elif source_id in published_source_ids:
            reason = "source_already_represented_in_catalogue"
        elif (source_id, str(external_id)) in published_pairs:
            reason = "already_in_catalogue"
        elif (
            identity_token(supported.get("titulo")),
            identity_token(supported.get("orgao")),
            identity_token(supported.get("edital_numero")),
        ) in published_identity_keys:
            reason = "identity_already_represented_in_catalogue"
        elif candidate.get("detail_url_observed") in published_urls:
            reason = "detail_url_already_in_catalogue"
        if reason:
            if reason == "already_in_catalogue":
                continue
            rejected.append({
                "source": row["source"],
                "candidate_key": row["candidate_key"],
                "run_id": row["last_run_id"],
                "reason": reason,
            })
            continue

        end = supported.get("inscricao_fim") or ""
        start = supported.get("inscricao_inicio") or ""
        active = bool(end and end[:10] >= AS_OF.isoformat())
        registration_end = supported.get("inscricao_fim") or ""
        if not registration_end:
            recency = "unknown"
        elif registration_end[:10] >= AS_OF.isoformat():
            recency = "current_or_upcoming"
        else:
            recency = "historical"
        supported_count = sum(1 for field in run.get("fields", []) if field.get("state") == "supported")
        has_jobs = bool(supported.get("cargos"))
        has_compensation = bool(supported.get("remuneracao"))
        has_exam = bool(supported.get("prova_data"))
        ranking = {
            "active_priority": 1 if active else 0,
            "recency_rank": 2 if recency == "current_or_upcoming" else 1 if recency == "historical" else 0,
            "year_score": year_score(candidate, supported),
            "registration_end": registration_end or None,
            "field_score": [supported_count, has_jobs, has_compensation, has_exam],
        }
        eligible.append({
            "active_priority": active,
            "recency_rank": ranking["recency_rank"],
            "year_score": ranking["year_score"],
            "field_score": tuple(ranking["field_score"]),
            "registration_end": registration_end,
            "registration_start": start,
            "source": row["source"],
            "payload": candidate_payload(
                row,
                run,
                pending,
                source_id,
                recency,
                ranking,
                acquired_by_candidate.get((row["source"], row["candidate_key"]), []),
            ),
        })

    eligible.sort(
        key=ranking_sort_key,
        reverse=True,
    )

    selected: list[dict] = []
    sources_seen: set[str] = set()
    for item in eligible:
        if item["source"] in sources_seen:
            continue
        selected.append(item["payload"])
        sources_seen.add(item["source"])
        if len(selected) >= args.limit:
            break

    ranked_alternatives = [
        {
            "source": item["payload"]["source"],
            "candidate_key": item["payload"]["candidate_key"],
            "run_id": item["payload"]["run_id"],
            "title": item["payload"]["identity"]["title_observed"],
            "recency": item["payload"]["recency"],
            "ranking": item["payload"]["ranking"],
            "pending_documents": item["payload"]["pending_documents"],
            "pending_document_count": item["payload"]["pending_document_count"],
        }
        for item in eligible[:32]
    ]

    report = {
        "generated_at": "2026-09-09",
        "as_of": AS_OF.isoformat(),
        "method": "read_only_preserved_runs_and_catalogue_identity",
        "publication_performed": False,
        "acquisition_performed": False,
        "candidate_count_before_source_deduplication": len(eligible),
        "eligible_source_count": len({item["source"] for item in eligible}),
        "eligible_sources": sorted({item["source"] for item in eligible}),
        "eligible_current_or_upcoming_count": sum(1 for item in eligible if item["active_priority"]),
        "selected_count": len(selected),
        "selected_current_or_upcoming_count": sum(
            1 for item in selected if item["recency"] == "current_or_upcoming"
        ),
        "selected": selected,
        "ranked_alternatives_before_source_deduplication": ranked_alternatives,
        "selection_rule": [
            "execution_status=completed with a preserved artifact; historical validation may be partial/pending because the normal revalidation path re-reads the artifact",
            "titulo, orgao and edital_numero supported with page/snippet/hash evidence",
            "pending documents are retained and enumerated for delegated document review",
            "source/external_id absent from canonical catalogue",
            "source_id has no existing catalogue record (sources already represented are deferred)",
            "normalized title, organ and edital identity is not already in the catalogue",
            "at most one candidate per source; current/future first, then edital/observation year, then registration end, then fields",
        ],
        "rejected_or_deferred": rejected,
        "real_gaps": [
            "Candidates without inscription end are ranked as recency unknown, never silently treated as historical.",
            "No proposal, approval, application, sync or app verification is included in this packet.",
            "Unknown fields remain unknown; absence of extracted evidence is not documentary absence.",
            "Retifications or later documents are not inferred; any pending documents remain explicit for delegated review.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "output": str(args.output),
        "selected": [
            {"source": item["source"], "run_id": item["run_id"], "title": item["identity"]["title_observed"]}
            for item in selected
        ],
        "candidate_count_before_source_deduplication": len(eligible),
        "rejected_or_deferred_count": len(rejected),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
