"""Prepare a corrected FACET proposal with a canonical title dash.

The prior FACET run/proposal remains immutable and referenced as superseded.
This script reuses the same preserved PDF, runs normal extraction and identity
validation, then creates a new proposal without approval or application.
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
OUTPUT = ROOT / "product-completion/delivery-next-reextract-facet-title-20260909.json"
PARENT_RUN_ID = "tp-tcj-e34b795398cb56cc8260c5df21b3e3e4-1"
SUPERSEDED_RUN_ID = "tpr-d14495aa6c31"
SUPERSEDED_PROPOSAL_ID = "tpp-78e155f2de4e8e674fee05d3922798ca"
AUTHORIZATION = {
    "actor_kind": "delegated_automation",
    "human_read": False,
    "delegation_reference": "user-attachment:6b86284b-154e-4ef6-88a1-6318513307e3/pasted-text-1.txt",
    "delegation_sha256": "a8d5f58a652eaed76d186385e12dadf9cbc4acf71cca71d5535a1797aca059f6",
}


def evidence_fields(run):
    return [
        {
            "field": field.field_name,
            "state": field.state.value,
            "value": field.value,
            "original_value": field.original_value,
            "reason": field.reason,
            "evidence": [
                {"page": item.page_number, "sha256": item.document_sha256, "snippet": " ".join((item.snippet or "").split())[:620]}
                for item in field.evidence[:4]
            ],
        }
        for field in run.fields
    ]


def main():
    store = get_store()
    original = store.get_run(PARENT_RUN_ID)
    if original is None or original.artifact is None or original.document is None:
        raise RuntimeError("run FACET original/artifact/document ausente")
    content = store.load_artifact_bytes(original.artifact)
    digest = hashlib.sha256(content).hexdigest()
    if digest != original.artifact.sha256:
        raise RuntimeError("hash do PDF FACET preservado diverge do manifesto original")
    pages, total, processed, truncated, errors = extract_pages_isolated(
        content,
        artifact_id=original.artifact.artifact_id,
        owner_id=str(original.owner_user_id),
        max_bytes=max(len(content), 30 * 1024 * 1024),
        max_pages=200,
        reuse_completed=True,
    )
    if truncated or errors or total != processed:
        raise RuntimeError("reextração isolada FACET incompleta")
    candidate = next(c for c in original.candidates if c.candidate_id == original.selected_candidate_id)
    validation = validate_identity(
        candidate=candidate,
        pages=pages,
        document_title=original.document.title,
        document_url=original.document.url_final or original.document.url_requested,
        document_kind=original.document.kind,
    )
    if validation.status.value != "valid":
        raise RuntimeError(f"identidade FACET inválida: {validation.status.value}")
    fields = extract_fields(candidate=candidate, artifact=original.artifact, pages=pages)
    title = next(field for field in fields if field.field_name == "titulo")
    if title.value != "Prefeitura de Floresta/PE – 2026" or "\x96" not in (title.original_value or ""):
        raise RuntimeError(f"normalização FACET inesperada: value={title.value!r} original={title.original_value!r}")
    now = datetime.now(timezone.utc)
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
        "diagnostics": [*original.diagnostics, f"reextract_of={original.run_id}; FACET U+0096 title canonicalization"],
        "created_at": now,
        "updated_at": now,
    })
    store.put_run(new_run)
    with SessionLocal() as db:
        user = db.get(User, new_run.owner_user_id)
        if user is None:
            raise RuntimeError("owner FACET ausente")
        publication.authorize(user)
        proposal = publication.create_proposal(db, run=new_run, user=user, store=store, authorization=AUTHORIZATION)
    report = {
        "generated_at": "2026-09-09",
        "method": "normal_reextract_preserved_pdf_new_run_then_create_proposal",
        "publication_performed": False,
        "approval_performed": False,
        "application_performed": False,
        "authorization": AUTHORIZATION,
        "original_run_preserved": True,
        "superseded": {"run_id": SUPERSEDED_RUN_ID, "proposal_id": SUPERSEDED_PROPOSAL_ID},
        "run": {
            "original_run_id": original.run_id,
            "new_run_id": new_run.run_id,
            "source": new_run.source,
            "artifact_sha256": new_run.artifact.sha256,
            "pages": processed,
            "validation_status": validation.status.value,
            "fields": evidence_fields(new_run),
        },
        "proposal": {
            "id": proposal["id"],
            "proposal_hash": proposal["proposal_hash"],
            "state": proposal["state"],
            "eligible_fields": proposal.get("eligible_fields"),
            "blocked_fields": proposal.get("blocked_fields"),
            "authorization": proposal.get("authorization"),
        },
        "real_gaps": [
            "A proposta FACET anterior permanece preservada e superseded; usar somente a nova proposta após revisão.",
            "Cargos não foram inventados; permanecem fora do merge canônico.",
            "Remuneração permanece bloqueada quando observada por cargo.",
        ],
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(OUTPUT), "new_run_id": new_run.run_id, "proposal_id": proposal["id"], "state": proposal["state"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
