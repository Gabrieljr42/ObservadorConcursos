"""Verify and prepare the next three normal publication proposals.

This script reuses preserved TenderProof runs, re-extracts their PDF pages with
the normal isolated processor, checks the documented identity/date/scope terms,
and calls the normal publication.create_proposal flow. It never approves or
applies a proposal and writes a fresh receipt.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, "/app")

from app.database import SessionLocal
from app.models import User
from app.tenderproof import publication
from app.tenderproof.contracts import TenderProofRun
from app.tenderproof.processing import extract_pages_isolated
from app.tenderproof.store import get_store


ROOT = Path("/var/lib/observador/tenderproof")
OUTPUT = ROOT / "product-completion/delivery-next-proposals-ibade-omni-contemax-20260909.json"
AUTHORIZATION = {
    "actor_kind": "delegated_automation",
    "human_read": False,
    "delegation_reference": "user-attachment:6b86284b-154e-4ef6-88a1-6318513307e3/pasted-text-1.txt",
    "delegation_sha256": "a8d5f58a652eaed76d186385e12dadf9cbc4acf71cca71d5535a1797aca059f6",
}
TARGETS = {
    "ibade_open": {
        "run_id": "tp-tcj-ced2f8d528395ba290136630d4b7dc7a-1",
        "identity_terms": ["FLORIANÓPOLIS", "005/2025", "PROCESSO SELETIVO"],
        "date_terms": ["07 de abril de 2025", "22 de abril de 2025"],
        "scope_terms": ["SUBSTITUTOS", "SECRETARIA MUNICIPAL DE EDUCAÇÃO"],
    },
    "omni_open": {
        "run_id": "tp-tcj-59347827080f515f92f18723759a231d-1",
        "identity_terms": ["OSVALDO CRUZ", "002/2024", "CONCURSO PÚBLICO"],
        "date_terms": ["27/11/2024", "29/12/2024"],
        "scope_terms": ["CARGOS", "PROVA OBJETIVA"],
    },
    "contemax_open": {
        "run_id": "tp-tcj-8ab7bff262fa52d4a80aa00058905974-1",
        "identity_terms": ["CUBATI", "001/2024", "CONCURSO PÚBLICO"],
        "date_terms": ["05/07/2024", "14/08/2024"],
        "scope_terms": ["CARGOS", "REMUNERAÇÃO", "VAGAS"],
    },
}


def normalize(value: str) -> str:
    return " ".join((value or "").upper().split())


def short(text: str, limit: int = 600) -> str:
    return " ".join((text or "").split())[:limit]


def field_evidence(run: TenderProofRun) -> list[dict]:
    rows = []
    for field in run.fields:
        rows.append(
            {
                "field": field.field_name,
                "state": field.state.value,
                "value": field.value,
                "reason": field.reason,
                "evidence": [
                    {
                        "page": evidence.page_number,
                        "sha256": evidence.document_sha256,
                        "snippet": short(evidence.snippet),
                    }
                    for evidence in field.evidence[:3]
                ],
            }
        )
    return rows


def verify_pdf(run: TenderProofRun, target: dict, store) -> dict:
    if run.execution_status.value != "completed" or not run.artifact:
        raise RuntimeError(f"run incompleto ou sem artifact: {run.run_id}")
    data = store.load_artifact_bytes(run.artifact)
    digest = hashlib.sha256(data).hexdigest()
    if digest != run.artifact.sha256:
        raise RuntimeError(f"hash do artifact diverge: {run.run_id}")
    pages, total, processed, truncated, errors = extract_pages_isolated(
        data,
        artifact_id=run.artifact.artifact_id,
        owner_id=str(run.owner_user_id),
        max_bytes=max(len(data), 30 * 1024 * 1024),
        max_pages=200,
        reuse_completed=True,
    )
    if truncated or errors or total != processed:
        raise RuntimeError(f"extração isolada incompleta: {run.run_id}")
    text = normalize("\n".join(page.text for page in pages))
    identity_matches = {term: normalize(term) in text for term in target["identity_terms"]}
    date_matches = {term: normalize(term) in text for term in target["date_terms"]}
    scope_matches = {term: normalize(term) in text for term in target["scope_terms"]}
    missing = [
        *(f"identity:{term}" for term, ok in identity_matches.items() if not ok),
        *(f"date:{term}" for term, ok in date_matches.items() if not ok),
        *(f"scope:{term}" for term, ok in scope_matches.items() if not ok),
    ]
    if missing:
        raise RuntimeError(f"trechos esperados ausentes em {run.run_id}: {', '.join(missing)}")
    excerpts = []
    for term in [*target["identity_terms"], *target["date_terms"], *target["scope_terms"]]:
        for page in pages:
            page_text = normalize(page.text)
            position = page_text.find(normalize(term))
            if position >= 0:
                excerpts.append(
                    {
                        "term": term,
                        "page": page.page_number,
                        "sha256": run.artifact.sha256,
                        "snippet": short(page.text[max(0, position - 120) : position + 520]),
                    }
                )
                break
    return {
        "artifact_id": run.artifact.artifact_id,
        "sha256": run.artifact.sha256,
        "bytes": len(data),
        "pages": processed,
        "identity_matches": identity_matches,
        "date_matches": date_matches,
        "scope_matches": scope_matches,
        "excerpts": excerpts,
        "supported_fields": [f.field_name for f in run.fields if f.state.value == "supported"],
        "blocked_or_unknown_fields": [
            {"field": f.field_name, "state": f.state.value, "reason": f.reason}
            for f in run.fields
            if f.state.value != "supported"
        ],
    }


def run_summary(run: TenderProofRun, verification: dict) -> dict:
    candidate = next((item for item in run.candidates if item.candidate_id == run.selected_candidate_id), None)
    return {
        "run_id": run.run_id,
        "source": run.source,
        "candidate_key": candidate.external_id if candidate else None,
        "title": candidate.title_observed if candidate else None,
        "detail_url": candidate.detail_url_observed if candidate else None,
        "execution_status": run.execution_status.value,
        "validation_status": run.validation_status.value,
        "document_kind": run.document.kind if run.document else None,
        "document_sha256": run.artifact.sha256 if run.artifact else None,
        "document_url": run.artifact.url_final if run.artifact else None,
        "verification": verification,
        "fields": field_evidence(run),
    }


def create_proposal(db, run: TenderProofRun, store) -> dict:
    user = db.get(User, run.owner_user_id)
    if user is None:
        raise RuntimeError(f"owner ausente: {run.run_id}")
    publication.authorize(user)
    proposal = publication.create_proposal(
        db,
        run=run,
        user=user,
        store=store,
        authorization=AUTHORIZATION,
    )
    return {
        "id": proposal["id"],
        "proposal_hash": proposal["proposal_hash"],
        "state": proposal["state"],
        "action": proposal["action"],
        "source": run.source,
        "run_id": run.run_id,
        "eligible_fields": proposal.get("eligible_fields"),
        "blocked_fields": proposal.get("blocked_fields"),
        "authorization": proposal.get("authorization"),
    }


def main() -> None:
    store = get_store()
    runs = {}
    verifications = {}
    for source, target in TARGETS.items():
        run = store.get_run(target["run_id"])
        if run is None:
            raise RuntimeError(f"run alvo ausente: {target['run_id']}")
        runs[source] = run
        verifications[source] = verify_pdf(run, target, store)

    with SessionLocal() as db:
        proposals = [create_proposal(db, runs[source], store) for source in TARGETS]
        report = {
            "generated_at": "2026-09-09",
            "method": "normal_publication_create_proposal_after_isolated_pdf_revalidation",
            "publication_performed": False,
            "approval_performed": False,
            "application_performed": False,
            "authorization": AUTHORIZATION,
            "runs": {source: run_summary(runs[source], verifications[source]) for source in TARGETS},
            "proposals": proposals,
            "real_gaps": [
                "Propostas criadas em estado proposed; aprovação e aplicação permanecem para root.",
                "IBADE e OMNI não tiveram cargos publicados porque o run preservado não traz campo cargos suportado.",
                "CONTEMAX traz remuneração por cargo no PDF, mas a lista de cargos não foi inventada quando o extrator não a materializou como campo cargos.",
                "prova_data permanece unknown nos três runs por ausência de evidência cronológica canônica no extrator preservado.",
                "Amostra histórica; não certifica a cobertura integral das três fontes nem ausência de retificações posteriores.",
            ],
        }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")
    print(json.dumps({
        "output": str(OUTPUT),
        "proposals": [{"id": item["id"], "state": item["state"], "source": item["source"]} for item in proposals],
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
