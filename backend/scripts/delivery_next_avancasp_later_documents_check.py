"""Check preserved AVANCASP follow-up documents for objective-date resolution.

This is evidence-only: it reads the existing review case and does not create,
approve, or apply a proposal.  It records only date/term counts and hashes so
candidate names from the practical-exam roster are not reproduced.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, "/app")

from app.tenderproof import review_cases
from app.tenderproof.continuous_store import get_continuous_store
from app.tenderproof.store import get_store


RUN_ID = "tp-tcj-11c94e0888d15070a71c65b32bd7c98d-1"
CASE_ID = "drc-12bd9c8d22a1416b97c8b920813dfaaf"
ROOT = Path("/var/lib/observador/tenderproof")
OUTPUT = ROOT / "product-completion/delivery-next-avancasp-later-documents-20260909.json"
DATE_RE = re.compile(r"\b\d{2}/\d{2}/2026\b")
OBJECTIVE_RE = re.compile(r"prova\s+objetiva", re.IGNORECASE)
PRACTICAL_RE = re.compile(r"prova\s+pr[aá]tica", re.IGNORECASE)


def main() -> None:
    store = get_store()
    run = store.get_run(RUN_ID)
    if run is None or run.artifact is None:
        raise RuntimeError("run AVANCASP preservado ausente")
    content = store.load_artifact_bytes(run.artifact)
    if hashlib.sha256(content).hexdigest() != run.artifact.sha256:
        raise RuntimeError("hash do edital-base preservado divergente")
    case = review_cases.read(get_continuous_store(), CASE_ID, run.owner_user_id)
    documents = []
    for item in case.get("documents", []):
        document = item.get("document") or {}
        if document.get("kind") == "edital":
            continue
        pages = item.get("pages") or []
        text = " ".join(page.get("text", "") if isinstance(page, dict) else page.text for page in pages)
        dates = sorted(set(DATE_RE.findall(text)))
        documents.append({
            "kind": document.get("kind"),
            "title": document.get("title"),
            "artifact_sha256": (item.get("artifact") or {}).get("sha256"),
            "pages": len(pages),
            "objective_term_count": len(OBJECTIVE_RE.findall(text)),
            "objective_date_tokens": [date for date in dates if date in text and OBJECTIVE_RE.search(text[max(0, text.find(date) - 100):text.find(date) + 100])],
            "practical_term_count": len(PRACTICAL_RE.findall(text)),
            "date_tokens": dates,
        })
    report = {
        "generated_at": "2026-09-09",
        "run_id": RUN_ID,
        "case_id": CASE_ID,
        "base_artifact_sha256": run.artifact.sha256,
        "later_documents": documents,
        "resolution": {
            "status": "unresolved",
            "reason": "Os documentos posteriores preservados tratam de prorrogação de inscrições e retificações da prova prática; não há termo/data explícito de prova objetiva que resolva o conflito p41=22/05 versus p6=31/05.",
            "next_authority_action": "Obter do AVANÇASP/município uma retificação ou cronograma oficial que declare expressamente a data da prova objetiva; manter prova_data bloqueada até essa confirmação.",
        },
        "proposal_created": False,
        "approval_performed": False,
        "application_performed": False,
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(OUTPUT), "status": "unresolved", "proposal_created": False}))


if __name__ == "__main__":
    main()
