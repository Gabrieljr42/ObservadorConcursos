"""Write a read-only summary of the preserved FUMARC review cases.

This is an audit artifact only. It does not approve, reopen, mutate, or
regenerate any proposal or review case.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path


ROOT = Path("/var/lib/observador/tenderproof")
OUTPUT = ROOT / "product-completion/delivery-next-fumarc-review-summary-20260909.json"
CHILD_RUN = "tp-review-3c7743a37b6e48c48f3996ba75db1fa7"
PARENT_RUN = "tp-tcj-1e6d26682dd3574dab0a2b2ad4eceb32-1"
APPROVED_CASE = "drc-cccf21d5791c401fbb6ac57e46d7fb62"


def safe_document(document: dict, artifact: dict) -> dict:
    return {
        "sha256": artifact.get("sha256"),
        "kind": document.get("kind"),
        "title": document.get("title"),
        "page_count": None,
        "url": artifact.get("url_final"),
    }


def main() -> None:
    path = ROOT / "continuous.sqlite3"
    with sqlite3.connect(path.as_uri() + "?mode=ro", uri=True) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            "SELECT id,payload,approved_at,decisions FROM document_effect_cases "
            "WHERE run_id=? OR id=? ORDER BY rowid",
            (CHILD_RUN, APPROVED_CASE),
        ).fetchall()

    approved = None
    open_cases = []
    for row in rows:
        payload = json.loads(row["payload"])
        decisions = json.loads(row["decisions"]) if row["decisions"] else None
        documents = [safe_document(item["document"], item["artifact"]) for item in payload.get("documents", [])]
        item = {
            "case_id": row["id"],
            "run_id": payload.get("run_id"),
            "revision_hash": payload.get("revision_hash"),
            "selected_document_sha256": payload.get("selected_document_sha256"),
            "approved_at": row["approved_at"],
            "documents": documents,
            "decision_count": len(decisions or []),
        }
        if row["id"] == APPROVED_CASE:
            item["decisions"] = [
                {
                    "sha256": decision.get("sha256"),
                    "page": decision.get("page"),
                    "effect": decision.get("effect"),
                    "reason": decision.get("reason"),
                    "snippet_header": (
                        "CREA-MG / CONCURSO PÚBLICO N° 01/2026 / consolidado com ERRATA nº 01"
                        if decision.get("sha256") == "6f9b94aa7605244dd5f4ee0696ed4dfc825cffd953c919f636d5db5aaeca327e"
                        else "ERRATA nº 01 / itens 1.13 e 1.13.1"
                        if decision.get("sha256") == "116bccb271ab5881d69c55a25ab0fabf2f2180d8af41a1aedba36d15d902a026"
                        else "ANEXO I / quadro de cargos, vagas, salários base e carga horária"
                    ),
                }
                for decision in (decisions or [])
            ]
            item["decision_origin"] = "delegated_automation_prior_approval"
            item["independent_effect_audit_required"] = True
            approved = item
        else:
            item["status"] = "unapproved_case_preserved_for_followup"
            item["payload_run_id_missing"] = payload.get("run_id") is None
            open_cases.append(item)

    report = {
        "generated_at": "2026-09-09",
        "read_only": True,
        "mutated_state": False,
        "proposals_regenerated": False,
        "parent_run": PARENT_RUN,
        "selected_run": CHILD_RUN,
        "selected_document": {
            "kind": "consolidado",
            "sha256": "6f9b94aa7605244dd5f4ee0696ed4dfc825cffd953c919f636d5db5aaeca327e",
            "original_parent_preserved": True,
        },
        "approved_case": approved,
        "other_preserved_cases": open_cases,
        "real_gap": "A conferência independente deve comparar os efeitos da Errata nº 01 com o texto consolidado e o Anexo I por campo, substituindo a decisão automática apenas se os trechos sustentarem efeito distinto.",
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "output": str(OUTPUT),
        "approved_case_id": approved.get("case_id") if approved else None,
        "approved_review_hash": approved.get("revision_hash") if approved else None,
        "open_case_count": len(open_cases),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
