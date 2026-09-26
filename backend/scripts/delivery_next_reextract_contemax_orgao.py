"""Re-extract the preserved CONTEMAX Cubati PDF with the corrected orgao rule.

The historical run and its artifact remain untouched. A new completed run is
written from the same immutable bytes, then passed through normal proposal
creation so the corrected field is reviewable without approving or applying it.
"""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, "/app")

from app.database import SessionLocal
from app.models import User
from app.tenderproof import publication
from app.tenderproof.acquisition import new_run_id
from app.tenderproof.contracts import ComparisonResult, ExecutionStatus
from app.tenderproof.fields import extract_fields, semantic_hash
from app.tenderproof.processing import extract_pages_isolated
from app.tenderproof.store import get_store
from app.tenderproof.validation import validate_identity


ROOT = Path("/var/lib/observador/tenderproof")
OUTPUT = ROOT / "product-completion/delivery-next-reextract-contemax-orgao-20260909.json"
PARENT_RUN_ID = "tp-tcj-8ab7bff262fa52d4a80aa00058905974-1"
AUTHORIZATION = {
    "actor_kind": "delegated_automation",
    "human_read": False,
    "delegation_reference": "user-attachment:6b86284b-154e-4ef6-88a1-6318513307e3/pasted-text-1.txt",
    "delegation_sha256": "a8d5f58a652eaed76d186385e12dadf9cbc4acf71cca71d5535a1797aca059f6",
}


def main() -> None:
    store = get_store()
    original = store.get_run(PARENT_RUN_ID)
    if original is None or original.artifact is None:
        raise RuntimeError("run CONTEMAX original ou artifact ausente")
    content = store.load_artifact_bytes(original.artifact)
    digest = hashlib.sha256(content).hexdigest()
    if digest != original.artifact.sha256:
        raise RuntimeError("hash do PDF preservado diverge do manifesto original")
    pages, total, processed, truncated, errors = extract_pages_isolated(
        content,
        artifact_id=original.artifact.artifact_id,
        owner_id=str(original.owner_user_id),
        max_bytes=max(len(content), 30 * 1024 * 1024),
        max_pages=200,
        reuse_completed=True,
    )
    if truncated or errors or total != processed:
        raise RuntimeError("reextração isolada CONTEMAX incompleta")
    candidate = next(c for c in original.candidates if c.candidate_id == original.selected_candidate_id)
    validation = validate_identity(
        candidate=candidate,
        pages=pages,
        document_title=original.document.title if original.document else "",
        document_url=(original.document.url_final or original.document.url_requested) if original.document else original.artifact.url_final,
        document_kind=original.document.kind if original.document else "edital",
    )
    fields = extract_fields(candidate=candidate, artifact=original.artifact, pages=pages)
    new_run = original.model_copy(deep=True, update={
        "run_id": new_run_id(),
        "execution_status": ExecutionStatus.COMPLETED,
        "validation_status": validation.status,
        "comparison_status": "pending",
        "comparison": ComparisonResult(),
        "total_pages": total,
        "processed_pages": processed,
        "truncated": truncated,
        "page_errors": errors,
        "fields": fields,
        "validation": validation,
        "semantic_hash": semantic_hash(fields),
        "diagnostics": [*original.diagnostics, f"reextract_of={original.run_id}; fields.py orgao normative-tail fix"],
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    })
    orgao = next(field for field in fields if field.field_name == "orgao")
    if orgao.value != "Prefeitura Municipal De Cubati":
        raise RuntimeError(f"normalização inesperada de orgao: {orgao.value!r}")
    store.put_run(new_run)
    with SessionLocal() as db:
        user = db.get(User, new_run.owner_user_id)
        if user is None:
            raise RuntimeError("owner do run ausente")
        publication.authorize(user)
        proposal = publication.create_proposal(
            db,
            run=new_run,
            user=user,
            store=store,
            authorization=AUTHORIZATION,
        )
        report = {
            "generated_at": "2026-09-09",
            "method": "normal_reextract_preserved_pdf_new_run_then_create_proposal",
            "original_run_preserved": True,
            "parent_run_id": original.run_id,
            "new_run_id": new_run.run_id,
            "artifact_sha256": new_run.artifact.sha256,
            "pages": processed,
            "validation_status": validation.status.value,
            "identity": {
                "candidate_key": candidate.external_id,
                "title": candidate.title_observed,
                "orgao": orgao.value,
                "edital_numero": next((f.value for f in fields if f.field_name == "edital_numero"), None),
            },
            "orgao_evidence": [
                {
                    "page": evidence.page_number,
                    "sha256": evidence.document_sha256,
                    "snippet": evidence.snippet,
                }
                for evidence in orgao.evidence
            ],
            "proposal": {
                "id": proposal["id"],
                "proposal_hash": proposal["proposal_hash"],
                "state": proposal["state"],
                "eligible_fields": proposal.get("eligible_fields"),
                "blocked_fields": proposal.get("blocked_fields"),
                "authorization": proposal.get("authorization"),
            },
            "publication_performed": False,
            "approval_performed": False,
            "application_performed": False,
            "real_gaps": [
                "A proposta anterior do run original permanece preservada e não deve ser aprovada; esta proposta usa o run novo corrigido.",
                "Cargos não foram inventados; o extrator preservado não materializou o quadro como campo cargos.",
                "Remuneração continua bloqueada no merge canônico da publicação, embora haja valores por cargo nas páginas 19–20.",
                "prova_data continua unknown no run reextraído.",
            ],
        }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")
    print(json.dumps({
        "output": str(OUTPUT),
        "parent_run_id": original.run_id,
        "new_run_id": new_run.run_id,
        "proposal_id": proposal["id"],
        "state": proposal["state"],
        "orgao": orgao.value,
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
