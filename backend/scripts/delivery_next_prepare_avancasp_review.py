"""Prepare, but do not approve, the pending AVANCASP document review case."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, "/app")

from app.tenderproof.continuous_store import get_continuous_store
from app.tenderproof.review_cases import prepare
from app.tenderproof.store import get_store


RUN_ID = "tp-tcj-11c94e0888d15070a71c65b32bd7c98d-1"
ROOT = Path("/var/lib/observador/tenderproof")
OUTPUT = ROOT / "product-completion/delivery-next-avancasp-review-20260909.json"


def main() -> None:
    store = get_store()
    queue = get_continuous_store()
    run = store.get_run(RUN_ID)
    if run is None:
        raise RuntimeError("run AVANCASP preservado ausente")
    result = prepare(queue, store, run)
    documents = []
    for item in result.get("documents", []):
        artifact = item.get("artifact") or {}
        documents.append({
            "kind": (item.get("document") or {}).get("kind"),
            "title": (item.get("document") or {}).get("title"),
            "artifact_sha256": artifact.get("sha256"),
            "pages": len(item.get("pages") or []),
            "ocr_review_required": item.get("ocr_review_required", False),
            "scope": item.get("scope"),
            "fields": item.get("fields"),
        })
    report = {
        "generated_at": "2026-09-09",
        "run_id": RUN_ID,
        "case_id": result["id"],
        "revision_hash": result["revision_hash"],
        "approval_performed": False,
        "application_performed": False,
        "documents": documents,
        "real_gaps": [
            "O caso foi preparado pelo fluxo normal; nenhuma decisão documental foi aprovada.",
            "A proposta de publicação continua bloqueada até a comparação dos três documentos posteriores.",
        ],
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(OUTPUT), "case_id": result["id"], "revision_hash": result["revision_hash"], "documents": len(documents)}))


if __name__ == "__main__":
    main()
