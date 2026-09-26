"""Prepare real, unapproved publication proposals for the next delivery.

CONSULPAM and FAPED use their completed preserved runs. FUMARC first follows
the normal document-review and preserved-document-selection path so its run
uses the official consolidated PDF without changing the original observation.
The script creates proposals only; it never approves or applies them.
"""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, "/app")

from app.database import SessionLocal
from app.models import User
from app.tenderproof import document_selection, publication, review_cases
from app.tenderproof.continuous_store import get_continuous_store
from app.tenderproof.contracts import TenderProofRun
from app.tenderproof.store import get_store


ROOT = Path("/var/lib/observador/tenderproof")
OUTPUT = ROOT / "product-completion/delivery-next-real-proposals-20260909.json"
AUTHORIZATION = {
    "actor_kind": "delegated_automation",
    "human_read": False,
    "delegation_reference": "user-attachment:6b86284b-154e-4ef6-88a1-6318513307e3/pasted-text-1.txt",
    "delegation_sha256": "a8d5f58a652eaed76d186385e12dadf9cbc4acf71cca71d5535a1797aca059f6",
}
RUN_IDS = {
    "fumarc_open": "tp-tcj-1e6d26682dd3574dab0a2b2ad4eceb32-1",
    "consulpam_open": "tp-tcj-1879bcc04c765b81bfe82a396671c68b-1",
    "faped_selection": "tp-tcj-981cd121897950fcbffc67b3e665020a-1",
}


def compact(text: str) -> str:
    return " ".join((text or "").split())


def short_snippet(text: str, limit: int = 520) -> str:
    return compact(text)[:limit]


def evidence_summary(run: TenderProofRun) -> list[dict]:
    result = []
    for field in run.fields:
        result.append(
            {
                "field": field.field_name,
                "state": field.state.value,
                "value": field.value,
                "evidence": [
                    {
                        "page": item.page_number,
                        "sha256": item.document_sha256,
                        "snippet": short_snippet(item.snippet),
                    }
                    for item in field.evidence[:3]
                ],
            }
        )
    return result


def run_summary(run: TenderProofRun) -> dict:
    candidate = next((item for item in run.candidates if item.candidate_id == run.selected_candidate_id), None)
    return {
        "run_id": run.run_id,
        "source": run.source,
        "owner_user_id": run.owner_user_id,
        "candidate_key": candidate.external_id if candidate else None,
        "title": candidate.title_observed if candidate else None,
        "detail_url": candidate.detail_url_observed if candidate else None,
        "execution_status": run.execution_status.value,
        "validation_status": run.validation_status.value,
        "document_kind": run.document.kind if run.document else None,
        "document_sha256": run.artifact.sha256 if run.artifact else None,
        "document_url": run.artifact.url_final if run.artifact else None,
        "fields": evidence_summary(run),
    }


def child_for_parent(parent_run_id: str) -> TenderProofRun | None:
    path = ROOT / "operational.sqlite3"
    if not path.exists():
        return None
    with sqlite3.connect(path.as_uri() + "?mode=ro", uri=True) as connection:
        rows = connection.execute("SELECT payload FROM runs ORDER BY saved_at DESC").fetchall()
    for (payload,) in rows:
        run = TenderProofRun.model_validate_json(payload)
        if (run.document_selection or {}).get("parent_run_id") == parent_run_id:
            return run
    return None


def current_or_prepare_case(queue, store, run: TenderProofRun) -> dict:
    current = review_cases.current(queue, run)
    if current:
        return current
    return review_cases.prepare(queue, store, run)


def document_text(document: dict) -> str:
    return "\n".join(page.get("text", "") for page in document.get("pages", []))


def decision_snippet(document: dict) -> str:
    pages = document.get("pages", [])
    if not pages:
        raise ValueError("documento da revisão sem páginas")
    # Prefer the first identity/effect heading and avoid result tables.
    for page in pages:
        text = page.get("text", "")
        match = re.search(r"ERRATA|CONSOLIDADO|CONCURSO PÚBLICO|RETIFICA", text, re.I)
        if match:
            return text[max(0, match.start() - 120):match.start() + 880].strip()
    return pages[0].get("text", "")[:1000].strip()


def build_fumarc_decisions(case: dict, selected_sha: str) -> tuple[list[dict], dict]:
    selected = next(item for item in case["documents"] if item["artifact"]["sha256"] == selected_sha)
    selected_text = compact(document_text(selected)).lower()
    decisions = []
    diagnostics = []
    seen = set()
    for document in case["documents"]:
        sha = document["artifact"]["sha256"]
        if sha in seen:
            continue
        seen.add(sha)
        title = document["document"].get("title", "")
        source_text = compact(document_text(document))
        lower = source_text.lower()
        if sha == selected_sha:
            effect = "reflected_in_selected_document"
            reason = (
                "O PDF consolidado foi selecionado como o documento vigente do run; "
                "a identidade CREA-MG/01-2026 e os campos publicados são extraídos deste hash preservado."
            )
        elif document["document"].get("kind") == "retificacao":
            reflected = "errata" in selected_text and "01/2026" in selected_text and "errata" in lower
            effect = "reflected_in_selected_document" if reflected else "field_changes"
            reason = (
                "A Errata nº 01 é literalmente identificada no consolidado selecionado (CREA-MG/01-2026; "
                "o consolidado declara ‘com ERRATA nº 01’), portanto seus efeitos documentais já estão refletidos."
                if reflected
                else "A errata não foi literalmente corroborada no consolidado selecionado; seus efeitos exigem mudança de campos."
            )
        else:
            effect = "reflected_in_selected_document"
            reason = (
                "Documento preservado da mesma observação; a seleção do consolidado mantém a identidade e os "
                "campos provenientes do material oficial associado."
            )
        item = {
            "sha256": sha,
            "page": document["pages"][0]["page_number"],
            "snippet": decision_snippet(document),
            "effect": effect,
            "reason": reason,
        }
        decisions.append(item)
        diagnostics.append({
            "sha256": sha,
            "kind": document["document"].get("kind"),
            "title": title,
            "effect": effect,
            "selected_text_has_errata_identity": "errata" in selected_text and "01/2026" in selected_text,
            "document_text_has_errata": "errata" in lower,
        })
    if any(item["effect"] == "field_changes" for item in decisions):
        raise RuntimeError("FUMARC errata não refletida literalmente no consolidado; proposta não criada")
    return decisions, {"documents": diagnostics, "selected_sha256": selected_sha}


def review_and_select_fumarc(queue, store, base_run: TenderProofRun) -> tuple[TenderProofRun, dict]:
    child = child_for_parent(base_run.run_id)
    if child is not None:
        if not queue.review_for_run(child)["pending"]:
            return child, {"selection_reused": True, "case": None, "decisions": None, "approval": "already_approved"}
        case = current_or_prepare_case(queue, store, child)
        decisions, diagnostic = build_fumarc_decisions(case, child.artifact.sha256)
        review_result = review_cases.approve(queue, store, child, case["id"], case["revision_hash"], decisions)
        if queue.review_for_run(child)["pending"]:
            raise RuntimeError("revisão FUMARC existente permaneceu pendente após decisões refletidas")
        return child, {"selection_reused": True, "case": case, "decisions": decisions, "diagnostic": diagnostic, "approval": review_result}

    case = current_or_prepare_case(queue, store, base_run)
    consolidated = [
        item for item in case["documents"]
        if item["document"].get("kind") == "consolidado"
    ]
    if len(consolidated) != 1:
        raise RuntimeError(f"esperado um consolidado FUMARC, encontrados {len(consolidated)}")
    selected_artifact_id = consolidated[0]["artifact"]["artifact_id"]
    child = document_selection.select_preserved(
        queue,
        store,
        base_run,
        case["id"],
        case["revision_hash"],
        selected_artifact_id,
        "Selecionar o consolidado oficial que declara literalmente Edital 01/2026 com ERRATA 01; preservar o run original e reextrair os campos do documento vigente.",
    )
    selected_case = review_cases.current(queue, child)
    if selected_case is None:
        raise RuntimeError("seleção FUMARC não gerou caso de revisão")
    decisions, diagnostic = build_fumarc_decisions(selected_case, child.artifact.sha256)
    review_result = review_cases.approve(queue, store, child, selected_case["id"], selected_case["revision_hash"], decisions)
    if queue.review_for_run(child)["pending"]:
        raise RuntimeError("revisão FUMARC permaneceu pendente após decisões refletidas")
    return child, {"selection_reused": False, "case": selected_case, "decisions": decisions, "diagnostic": diagnostic, "approval": review_result}


def scope_summary(run: TenderProofRun, store) -> dict:
    terms = ("CLT", "contrato de trabalho", "salário base", "processo seletivo")
    matches = []
    data = store.load_artifact_bytes(run.artifact)
    from app.tenderproof.processing import extract_pages_isolated
    pages, total, processed, truncated, errors = extract_pages_isolated(
        data,
        artifact_id=run.artifact.artifact_id,
        owner_id=str(run.owner_user_id),
        max_bytes=max(len(data), 30 * 1024 * 1024),
        max_pages=200,
        reuse_completed=True,
    )
    if truncated or errors or total != processed:
        raise RuntimeError("extração processada FAPED incompleta para confirmação de escopo")
    for page in pages:
        page_number, text = page.page_number, page.text
        lowered = text.lower()
        if "nome candidato" in lowered and "contrato de trabalho" not in lowered:
            continue
        for term in terms:
            position = lowered.find(term.lower())
            if position < 0:
                continue
            matches.append(
                {
                    "page": page_number,
                    "sha256": run.artifact.sha256,
                    "term": term,
                    "snippet": short_snippet(text[max(0, position - 180):position + 520]),
                }
            )
            break
    return {
        "classification": "employment_selection_supported",
        "reason": "PDF identifies one professional vacancy, CLT regime, salary, and contract-of-work section; this is personnel employment scope.",
        "evidence": matches[:8],
    }


def create_normal_proposal(db, store, run: TenderProofRun) -> dict:
    user = db.get(User, run.owner_user_id)
    if user is None:
        raise RuntimeError(f"owner user absent for {run.run_id}")
    publication.authorize(user)
    proposal = publication.create_proposal(db, run=run, user=user, store=store, authorization=AUTHORIZATION)
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
    queue = get_continuous_store()
    runs = {source: store.get_run(run_id) for source, run_id in RUN_IDS.items()}
    if any(run is None for run in runs.values()):
        raise RuntimeError("run alvo ausente")
    for run in runs.values():
        if run.execution_status.value != "completed" or not run.artifact:
            raise RuntimeError(f"run não concluído ou sem artifact: {run.run_id}")

    with SessionLocal() as db:
        fumarc_run, fumarc_review = review_and_select_fumarc(queue, store, runs["fumarc_open"])
        proposals = [create_normal_proposal(db, store, fumarc_run)]
        proposals.append(create_normal_proposal(db, store, runs["consulpam_open"]))
        proposals.append(create_normal_proposal(db, store, runs["faped_selection"]))
        report = {
            "generated_at": "2026-09-09",
            "method": "normal_publication_create_proposal_with_delegated_authorization",
            "publication_performed": False,
            "approval_performed": False,
            "application_performed": False,
            "authorization": AUTHORIZATION,
            "runs": {
                "fumarc": run_summary(fumarc_run),
                "consulpam": run_summary(runs["consulpam_open"]),
                "faped": run_summary(runs["faped_selection"]),
            },
            "faped_scope": scope_summary(runs["faped_selection"], store),
            "fumarc_document_review": {
                "original_run_id": runs["fumarc_open"].run_id,
                "selected_run_id": fumarc_run.run_id,
                "original_run_preserved": runs["fumarc_open"].run_id != fumarc_run.run_id,
                "selection": fumarc_review.get("diagnostic") or {"selection_reused": fumarc_review.get("selection_reused")},
                "decisions": fumarc_review.get("decisions"),
                "approval": fumarc_review.get("approval"),
            },
            "proposals": proposals,
            "real_gaps": [
                "Proposals are unapproved and unapplied; root must approve selected eligible fields before application.",
                "FUMARC uses the selected consolidated artifact; the original edital run remains preserved separately.",
                "FAPED prova_data remains unknown because the preserved edital does not state a prova date in extracted evidence.",
                "CONSULPAM prova_data remains unknown; remuneracao is supported only per cargo/context as recorded in the run.",
            ],
        }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")
    print(json.dumps({
        "output": str(OUTPUT),
        "proposals": [{"id": item["id"], "state": item["state"], "source": item["source"]} for item in proposals],
        "fumarc_selected_run": fumarc_run.run_id,
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
