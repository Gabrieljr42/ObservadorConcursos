"""Reprocess the preserved Consulpam Maranguape edital and propose cargos only."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.database import SessionLocal
from app.models import User
from app.tenderproof import publication
from app.tenderproof.consulpam_maranguape_jobs import extract_maranguape_jobs
from app.tenderproof.fields import _evidence, semantic_hash
from app.tenderproof.processing import extract_pages_isolated
from app.tenderproof.store import TenderProofStore, artifact_dir


SOURCE_RUN_ID = "tp-tcj-1879bcc04c765b81bfe82a396671c68b-1"
SOURCE = "consulpam_open"
EXTERNAL_ID = "777"
SHA256 = "c6731e75b83cb25671c4b3630a5c2cce86eb2e16a21ed28ee64d56019917837d"
AUTHORIZATION = {
    "actor_kind": "delegated_automation",
    "human_read": False,
    "delegation_reference": "user-attachment:6b86284b-154e-4ef6-88a1-6318513307e3/pasted-text-1.txt",
    "delegation_sha256": "a8d5f58a652eaed76d186385e12dadf9cbc4acf71cca71d5535a1797aca059f6",
}


def main() -> None:
    store = TenderProofStore()
    old = store.get_run(SOURCE_RUN_ID)
    if old is None or old.artifact is None or old.artifact.sha256 != SHA256:
        raise RuntimeError("run Consulpam ou SHA preservado não encontrado")
    candidate = next(c for c in old.candidates if c.candidate_id == old.selected_candidate_id)
    if candidate.source != SOURCE or candidate.external_id != EXTERNAL_ID:
        raise RuntimeError("identidade Consulpam preservada divergente")
    raw = store.load_artifact_bytes(old.artifact)
    if raw is None:
        raise RuntimeError("bytes Consulpam preservados não encontrados")
    pages, total, processed, truncated, errors = extract_pages_isolated(
        raw,
        artifact_id=old.artifact.artifact_id,
        owner_id=str(old.owner_user_id),
        max_pages=max(60, old.total_pages or 60),
        max_bytes=30 * 1024 * 1024,
        reuse_completed=True,
    )
    if errors or truncated or total != processed:
        raise RuntimeError(f"processamento normal incompleto: {total=} {processed=} {errors=}")
    field = extract_maranguape_jobs(
        old.artifact, pages, _evidence, source=SOURCE, external_id=EXTERNAL_ID,
    )
    if field is None or field.state.value != "supported" or len(field.value) != 43:
        raise RuntimeError(f"transcrição Consulpam não suportada: {field.reason if field else 'none'}")

    new = old.model_copy(deep=True)
    new.run_id = f"delivery-roles-consulpam-20260909-v2-{SHA256[:16]}"
    new.fields = [item for item in old.fields if item.field_name != "cargos"] + [field]
    new.semantic_hash = semantic_hash(new.fields)
    new.total_pages = total
    new.processed_pages = processed
    new.updated_at = datetime.now().astimezone()
    new.diagnostics = [
        *new.diagnostics,
        "delivery_roles_consulpam_maranguape: cargos reextraído por processamento normal; run original intacto",
    ]
    if store.get_run(new.run_id) is None:
        store.put_run(new)
    elif store.get_run(new.run_id).semantic_hash != new.semantic_hash:
        raise RuntimeError("run Consulpam de entrega já existe com semântica divergente")

    with SessionLocal() as db:
        user = db.get(User, new.owner_user_id)
        if user is None:
            raise RuntimeError("owner do run Consulpam não encontrado")
        proposal = publication.create_proposal(
            db, run=new, concurso_id=11, user=user, store=store, authorization=AUTHORIZATION,
        )

    report = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source_run_id": old.run_id,
        "new_run_id": new.run_id,
        "source": SOURCE,
        "external_id": EXTERNAL_ID,
        "document_sha256": SHA256,
        "pages": total,
        "cargo_count": len(field.value),
        "source_run_unchanged": store.get_run(old.run_id).model_dump_json() == old.model_dump_json(),
        "publication_performed": False,
        "proposal": {
            "id": proposal["id"],
            "proposal_hash": proposal["proposal_hash"],
            "state": proposal["state"],
            "action": proposal["action"],
            "eligible_fields": proposal.get("eligible_fields"),
            "blocked_fields": proposal.get("blocked_fields"),
            "authorization": proposal.get("authorization"),
        },
        "cargos": field.value,
        "evidence": [
            {"page": item.page_number, "sha256": item.document_sha256, "snippet": item.snippet,
             "method": item.method, "method_version": item.method_version}
            for item in field.evidence
        ],
    }
    output = artifact_dir().parent / "product-completion" / "delivery-roles-consulpam-maranguape-20260909-v2.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(output), "new_run_id": new.run_id, "proposal": report["proposal"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
