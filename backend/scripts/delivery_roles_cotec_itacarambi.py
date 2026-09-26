"""Acquire COTEC Anexo I, reprocess a new run, and create a cargos proposal.

The main edital run remains immutable.  The annex URL is copied from the
preserved COTEC detail capture; download and SHA checks are deliberately
bounded to this one document.
"""

from __future__ import annotations

import hashlib
import json
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.database import SessionLocal
from app.models import User
from app.tenderproof import publication
from app.tenderproof.contracts import Artifact, ComparisonResult, DocumentCandidate, SupplementaryDocument
from app.tenderproof.cotec_itacarambi_jobs import (
    EXPECTED_ARTIFACT_SHA256 as ANNEX_SHA256,
    EXPECTED_URL as ANNEX_URL,
    extract_itacarambi_jobs,
)
from app.tenderproof.fields import _evidence, extract_fields, semantic_hash
from app.tenderproof.processing import extract_pages_isolated
from app.tenderproof.security import TenderProofSettings
from app.tenderproof.store import artifact_dir, get_store
from app.tenderproof.supplementary_fields import supplement_fields
from app.tenderproof.validation import validate_identity


SOURCE_RUN_ID = "tp-tcj-3b345fb2c6ac57ba83731ab67cd7af45-1"
SOURCE = "cotec_open"
EXTERNAL_ID = "32"
MAIN_SHA256 = "b6f8fcb5ec3f1ff27269f93175ac5bc7c0f807c503522935dcfc5c7c12dc3626"
CONCURSO_ID = 27
NEW_RUN_ID = "delivery-roles-cotec-itacarambi-20260909-v2-" + ANNEX_SHA256[:16]
AUTHORIZATION = {
    "actor_kind": "delegated_automation",
    "human_read": False,
    "delegation_reference": "user-attachment:6b86284b-154e-4ef6-88a1-6318513307e3/pasted-text-1.txt",
    "delegation_sha256": "a8d5f58a652eaed76d186385e12dadf9cbc4acf71cca71d5535a1797aca059f6",
}


def _download_annex() -> bytes:
    request = urllib.request.Request(ANNEX_URL, headers={"User-Agent": "ObservadorDeCursos/1.0"})
    with urllib.request.urlopen(request, timeout=30) as response:
        if response.geturl() != ANNEX_URL or response.headers.get_content_type() != "application/pdf":
            raise RuntimeError("Anexo I COTEC redirecionado ou tipo inesperado")
        content = response.read()
    if not content.startswith(b"%PDF") or hashlib.sha256(content).hexdigest() != ANNEX_SHA256:
        raise RuntimeError("SHA do Anexo I COTEC divergente")
    return content


def main() -> None:
    store = get_store()
    old = store.get_run(SOURCE_RUN_ID)
    if old is None or old.artifact is None or old.artifact.sha256 != MAIN_SHA256:
        raise RuntimeError("run COTEC principal ou SHA preservado não encontrado")
    candidate = next(c for c in old.candidates if c.candidate_id == old.selected_candidate_id)
    if (candidate.source, candidate.external_id) != (SOURCE, EXTERNAL_ID):
        raise RuntimeError("identidade COTEC/Itacarambi divergente")
    original_json = old.model_dump_json()
    main_bytes = store.load_artifact_bytes(old.artifact)
    if not main_bytes or hashlib.sha256(main_bytes).hexdigest() != MAIN_SHA256:
        raise RuntimeError("bytes do edital principal ausentes ou divergentes")
    pages, total, processed, truncated, errors = extract_pages_isolated(
        main_bytes, artifact_id=old.artifact.artifact_id, owner_id=str(old.owner_user_id),
        max_pages=max(60, old.total_pages or 60), max_bytes=30 * 1024 * 1024,
        reuse_completed=True,
    )
    if truncated or errors or total != processed:
        raise RuntimeError(f"processamento principal incompleto: {total=} {processed=} {errors=}")
    validation = validate_identity(
        candidate=candidate, pages=pages, document_title=old.document.title,
        document_url=old.artifact.url_final, document_kind=old.document.kind,
    )
    if validation.status.value != "valid":
        raise RuntimeError(f"identidade principal inválida: {validation.status.value}")
    fields = extract_fields(candidate=candidate, artifact=old.artifact, pages=pages)

    annex_bytes = _download_annex()
    annex_artifact = Artifact(
        artifact_id="art-cotec-itacarambi-anexo1",
        sha256=ANNEX_SHA256,
        byte_len=len(annex_bytes),
        url_requested=ANNEX_URL,
        url_final=ANNEX_URL,
        content_type="application/pdf",
        downloaded_at=datetime.now(timezone.utc),
    )
    store.save_artifact_file(annex_artifact, annex_bytes)
    annex_document = DocumentCandidate(
        doc_id="cotec_open-doc-itacarambi-anexo-i-20260626",
        title="ANEXO I - ESPECIFICAÇÃO DOS CARGOS",
        url_requested=ANNEX_URL,
        url_final=ANNEX_URL,
        kind="anexo",
        reason_chosen=(
            "v2: Documento suplementar observado no detalhe COTEC/32; tabela de cargos "
            "do edital 01/2026, com escopo separado da reserva PcD."
        ),
    )
    supplement = SupplementaryDocument(document=annex_document, artifact=annex_artifact)
    settings = TenderProofSettings.from_env()
    fields = supplement_fields(candidate, fields, [supplement], store, settings, old.owner_user_id)
    cargo = next((item for item in fields if item.field_name == "cargos"), None)
    if cargo is None or cargo.state.value != "supported" or len(cargo.value or []) != 7:
        raise RuntimeError("Anexo I COTEC não produziu os sete cargos suportados")

    now = datetime.now(timezone.utc)
    new = old.model_copy(deep=True, update={
        "run_id": NEW_RUN_ID,
        "fields": fields,
        "supplementary_documents": [supplement],
        "total_pages": total,
        "processed_pages": processed,
        "truncated": False,
        "page_errors": [],
        "validation": validation,
        "validation_status": validation.status,
        "comparison_status": "pending",
        "comparison": ComparisonResult(),
        "semantic_hash": semantic_hash(fields),
        "created_at": now,
        "updated_at": now,
        "diagnostics": [
            *old.diagnostics,
            "delivery_roles_cotec_itacarambi: Anexo I adquirido pela URL observada e reprocessado; run original intacto",
        ],
    })
    existing = store.get_run(NEW_RUN_ID)
    if existing is None:
        store.put_run(new)
    elif existing.semantic_hash != new.semantic_hash:
        raise RuntimeError("run novo existente com semântica divergente")

    with SessionLocal() as db:
        user = db.get(User, new.owner_user_id)
        if user is None:
            raise RuntimeError("owner do run COTEC não encontrado")
        proposal = publication.create_proposal(
            db, run=new, concurso_id=CONCURSO_ID, user=user, store=store,
            authorization=AUTHORIZATION,
        )

    output = artifact_dir().parent / "product-completion" / "delivery-roles-cotec-itacarambi-20260909-v2.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    report = {
        "created_at": now.isoformat(),
        "source_run_id": SOURCE_RUN_ID,
        "new_run_id": NEW_RUN_ID,
        "source": SOURCE,
        "external_id": EXTERNAL_ID,
        "main_sha256": MAIN_SHA256,
        "annex_url": ANNEX_URL,
        "annex_sha256": ANNEX_SHA256,
        "main_pages": total,
        "annex_pages": 1,
        "cargo_count": len(cargo.value),
        "source_run_unchanged": store.get_run(SOURCE_RUN_ID).model_dump_json() == original_json,
        "publication_performed": False,
        "approval_performed": False,
        "application_performed": False,
        "authorization": AUTHORIZATION,
        "proposal": {
            "id": proposal["id"],
            "proposal_hash": proposal["proposal_hash"],
            "state": proposal["state"],
            "action": proposal["action"],
            "eligible_fields": proposal.get("eligible_fields"),
            "blocked_fields": proposal.get("blocked_fields"),
            "authorization": proposal.get("authorization"),
        },
        "cargos": cargo.value,
        "evidence": [
            {
                "page": item.page_number,
                "artifact_id": item.artifact_id,
                "sha256": item.document_sha256,
                "source_url": item.source_url,
                "snippet": item.snippet,
                "method": item.method,
                "method_version": item.method_version,
            }
            for item in cargo.evidence
        ],
    }
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(output), "new_run_id": NEW_RUN_ID, "proposal": report["proposal"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
