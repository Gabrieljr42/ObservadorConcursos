"""Reprocess IBAM Caruaru and create a normal, proposal-only cargo run.

The base edital and Anexo I are stored as separate immutable artifacts.  The
script uses the normal PDF processor for both documents, records a new run,
and calls ``publication.create_proposal``.  It never approves or applies the
proposal and never changes the original run.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.database import SessionLocal
from app.models import User
from app.tenderproof import publication
from app.tenderproof.contracts import Artifact, DocumentCandidate, SupplementaryDocument, ExecutionStatus
from app.tenderproof.fields import extract_fields, semantic_hash
from app.tenderproof.ibam_caruaru_jobs import (
    ANEXO_I_URL,
    EXPECTED_ANNEX_ARTIFACT_SHA256,
    EXPECTED_ARTIFACT_SHA256,
    EXPECTED_EXTERNAL_ID,
    EXPECTED_SOURCE,
)
from app.tenderproof.processing import extract_pages_isolated
from app.tenderproof.security import TenderProofSettings
from app.tenderproof.store import get_store
from app.tenderproof.supplementary_fields import supplement_fields
from app.tenderproof.validation import validate_identity


SOURCE_RUN = "tp-tcj-828fe3e4f0f45800a4e0b50dbdb4c0c3-1"
BASE_URL = "https://www.ibam-concursos.org.br/documento/ed-pmc0126f.pdf"
ANNEX_ARTIFACT_ID = "ibam-364-anexo1-" + EXPECTED_ANNEX_ARTIFACT_SHA256[:16]


def _normal_pages(content: bytes, *, artifact_id: str, owner_id: int, settings):
    pages, total, processed, truncated, errors = extract_pages_isolated(
        content, artifact_id=artifact_id, owner_id=str(owner_id),
        max_bytes=settings.limits.max_download_bytes, max_pages=settings.limits.max_pages,
        reuse_completed=True,
    )
    if not pages or truncated or errors or total != processed:
        raise RuntimeError(f"processamento normal incompleto: total={total}, processadas={processed}, erros={errors}")
    return pages


def prepare(*, annex_file: Path, output: Path) -> dict:
    store = get_store()
    original = store.get_run(SOURCE_RUN)
    if original is None or original.artifact is None or original.document is None:
        raise RuntimeError(f"run original ausente: {SOURCE_RUN}")
    if original.source != EXPECTED_SOURCE or original.artifact.sha256 != EXPECTED_ARTIFACT_SHA256:
        raise RuntimeError("run original não corresponde ao tuple IBAM Caruaru preservado")
    candidate = next((item for item in original.candidates if item.candidate_id == original.selected_candidate_id), None)
    if candidate is None or candidate.external_id != EXPECTED_EXTERNAL_ID:
        raise RuntimeError("candidato IBAM Caruaru ausente ou divergente")
    owner_id = original.owner_user_id
    if owner_id is None:
        raise RuntimeError("owner do run original ausente")

    annex = annex_file.read_bytes()
    annex_sha = hashlib.sha256(annex).hexdigest()
    if annex_sha != EXPECTED_ANNEX_ARTIFACT_SHA256:
        raise RuntimeError(f"SHA do Anexo I divergente: {annex_sha}")
    annex_artifact = Artifact(
        artifact_id=ANNEX_ARTIFACT_ID, sha256=annex_sha, byte_len=len(annex),
        url_requested=ANEXO_I_URL, url_final=ANEXO_I_URL, content_type="application/pdf",
        downloaded_at=datetime.now(timezone.utc),
    )
    store.save_artifact_file(annex_artifact, annex)
    annex_document = DocumentCandidate(
        doc_id="ibam_open-anexo1-364",
        title="ANEXO I - CARGOS, VAGAS, REQUISITOS, JORNADA DE TRABALHO, VENCIMENTOS E ATRIBUIÇÕES TÍPICAS",
        url_requested=ANEXO_I_URL, url_final=ANEXO_I_URL, kind="anexo",
        reason_chosen="Anexo I oficial vinculado à página documental de Caruaru/PE - 01/2026; tabela separada do edital principal.",
    )
    settings = TenderProofSettings.from_env()
    base = store.load_artifact_bytes(original.artifact)
    if not base or hashlib.sha256(base).hexdigest() != EXPECTED_ARTIFACT_SHA256:
        raise RuntimeError("bytes do edital-base ausentes ou divergentes")
    base_pages = _normal_pages(base, artifact_id=original.artifact.artifact_id, owner_id=owner_id, settings=settings)
    identity = validate_identity(candidate=candidate, pages=base_pages,
        document_title=original.document.title, document_url=original.artifact.url_final,
        document_kind=original.document.kind)
    if identity.status.value != "valid":
        raise RuntimeError(f"identidade do edital-base inválida: {identity.status.value}")
    fields = extract_fields(candidate=candidate, artifact=original.artifact, pages=base_pages)
    extra = SupplementaryDocument(document=annex_document, artifact=annex_artifact)
    fields = supplement_fields(candidate, fields, [extra], store, settings, owner_id)
    if not any(field.field_name == "cargos" and field.state.value == "supported" for field in fields):
        raise RuntimeError("cargos IBAM não suportados após revalidação do anexo")

    # Keep the corrected CR semantics in a fresh immutable run.  A prior v1
    # proposal was generated before the independent review established that
    # the annex does not confirm the existence or absence of a general CR.
    new_run_id = "delivery-roles-ibam-caruaru-20260909-" + EXPECTED_ANNEX_ARTIFACT_SHA256[:16] + "-v3"
    new_run = original.model_copy(deep=True, update={
        "run_id": new_run_id, "execution_status": ExecutionStatus.COMPLETED,
        "fields": fields, "supplementary_documents": [extra],
        "total_pages": len(base_pages), "processed_pages": len(base_pages),
        "truncated": False, "page_errors": [], "validation": identity,
        "validation_status": identity.status, "comparison_status": "pending",
        "semantic_hash": semantic_hash(fields),
        "diagnostics": [*original.diagnostics, "ibam_caruaru_roles_normal_reextract: base + SupplementaryDocument Anexo I; run original intacto"],
        "created_at": datetime.now(timezone.utc), "updated_at": datetime.now(timezone.utc),
    })
    persisted = store.put_run_if_absent(new_run)
    authorization = {
        "actor_kind": "delegated_automation", "human_read": False,
        "delegation_reference": "user-attachment:6b86284b-154e-4ef6-88a1-6318513307e3/pasted-text-1.txt",
        "delegation_sha256": "a8d5f58a652eaed76d186385e12dadf9cbc4acf71cca71d5535a1797aca059f6",
    }
    with SessionLocal() as db:
        user = db.get(User, owner_id)
        if user is None:
            raise RuntimeError(f"owner não encontrado: {owner_id}")
        result = publication.create_proposal(db, run=persisted, user=user, store=store, authorization=authorization)
    report = {
        "created_at": datetime.now(timezone.utc).isoformat(), "source_run_id": SOURCE_RUN,
        "new_run_id": new_run_id, "source": EXPECTED_SOURCE, "external_id": EXPECTED_EXTERNAL_ID,
        "base_artifact_sha256": EXPECTED_ARTIFACT_SHA256,
        "annex_artifact_sha256": EXPECTED_ANNEX_ARTIFACT_SHA256, "annex_artifact_id": ANNEX_ARTIFACT_ID,
        "annex_pages": len(_normal_pages(annex, artifact_id=ANNEX_ARTIFACT_ID, owner_id=owner_id, settings=settings)),
        "proposal": result, "publication_performed": False, "approval_performed": False,
        "application_performed": False,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--annex-file", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = prepare(annex_file=args.annex_file, output=args.output)
    print(json.dumps({"output": str(args.output), "run_id": report["new_run_id"],
                      "proposal_id": report["proposal"]["id"], "state": report["proposal"]["state"],
                      "publication_performed": False}, ensure_ascii=False))


if __name__ == "__main__":
    main()
