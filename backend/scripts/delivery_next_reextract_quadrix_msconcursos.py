"""Re-extract two current preserved PDFs and prepare normal proposals.

The source-specific field rules are narrowly tied to literal rows in the
preserved Quadrix and MSConcursos PDFs. Original runs/artifacts are retained;
new runs are created and proposals stay unapproved/unapplied.
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
OUTPUT = ROOT / "product-completion/delivery-next-reextract-quadrix-msconcursos-20260909.json"
TARGETS = {
    "quadrix_open": "tp-tcj-2655350aa61f51bc869619cd29088b3d-1",
    "msconcursos_open": "tp-tcj-2682a7a8c2875470bb03f776a5d546f5-1",
}
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
            "reason": field.reason,
            "evidence": [
                {"page": item.page_number, "sha256": item.document_sha256, "snippet": " ".join((item.snippet or "").split())[:620]}
                for item in field.evidence[:4]
            ],
        }
        for field in run.fields
    ]


def reextract(original, store):
    if original is None or original.artifact is None or original.document is None:
        raise RuntimeError("run original/artifact/document ausente")
    content = store.load_artifact_bytes(original.artifact)
    digest = hashlib.sha256(content).hexdigest()
    if digest != original.artifact.sha256:
        raise RuntimeError(f"hash divergente em {original.run_id}")
    pages, total, processed, truncated, errors = extract_pages_isolated(
        content,
        artifact_id=original.artifact.artifact_id,
        owner_id=str(original.owner_user_id),
        max_bytes=max(len(content), 30 * 1024 * 1024),
        max_pages=200,
        reuse_completed=True,
    )
    if truncated or errors or total != processed:
        raise RuntimeError(f"extração incompleta em {original.run_id}")
    candidate = next(c for c in original.candidates if c.candidate_id == original.selected_candidate_id)
    validation = validate_identity(
        candidate=candidate,
        pages=pages,
        document_title=original.document.title,
        document_url=original.document.url_final or original.document.url_requested,
        document_kind=original.document.kind,
    )
    if validation.status.value != "valid":
        raise RuntimeError(f"identidade inválida em {original.run_id}: {validation.status.value}")
    fields = extract_fields(candidate=candidate, artifact=original.artifact, pages=pages)
    fmap = {field.field_name: field for field in fields}
    required = {
        "quadrix_open": {"orgao": "Prefeitura Municipal De Cristalina", "inscricao_inicio": "2026-08-07", "inscricao_fim": "2026-09-10", "prova_data": "2026-10-18"},
        "msconcursos_open": {"orgao": "CONSÓRCIO REGIONAL INTERMUNICIPAL DE SAÚDE - CRIS", "inscricao_inicio": "2026-04-30", "inscricao_fim": "2026-05-31", "prova_data": "2026-06-14"},
    }[original.source]
    for field_name, expected in required.items():
        if fmap[field_name].value != expected:
            raise RuntimeError(f"{original.source} {field_name} inesperado: {fmap[field_name].value!r}")
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
        "diagnostics": [*original.diagnostics, f"reextract_of={original.run_id}; source-specific literal field rules"],
        "created_at": now,
        "updated_at": now,
    })
    store.put_run(new_run)
    return original, new_run


def proposal(db, run, store):
    user = db.get(User, run.owner_user_id)
    if user is None:
        raise RuntimeError("owner ausente")
    publication.authorize(user)
    result = publication.create_proposal(db, run=run, user=user, store=store, authorization=AUTHORIZATION)
    return {
        "id": result["id"],
        "proposal_hash": result["proposal_hash"],
        "state": result["state"],
        "action": result["action"],
        "source": run.source,
        "run_id": run.run_id,
        "eligible_fields": result.get("eligible_fields"),
        "blocked_fields": result.get("blocked_fields"),
        "authorization": result.get("authorization"),
    }


def main():
    store = get_store()
    pairs = {}
    for source, run_id in TARGETS.items():
        pairs[source] = reextract(store.get_run(run_id), store)
    with SessionLocal() as db:
        proposals = [proposal(db, pairs[source][1], store) for source in TARGETS]
    report = {
        "generated_at": "2026-09-09",
        "method": "normal_reextract_preserved_pdf_new_run_then_create_proposal",
        "publication_performed": False,
        "approval_performed": False,
        "application_performed": False,
        "authorization": AUTHORIZATION,
        "original_runs_preserved": True,
        "runs": {
            source: {
                "original_run_id": pairs[source][0].run_id,
                "new_run_id": pairs[source][1].run_id,
                "source": pairs[source][1].source,
                "artifact_sha256": pairs[source][1].artifact.sha256,
                "pages": pairs[source][1].processed_pages,
                "validation_status": pairs[source][1].validation_status.value,
                "fields": evidence_fields(pairs[source][1]),
            }
            for source in TARGETS
        },
        "proposals": proposals,
        "real_gaps": [
            "As duas propostas estão proposed; root deve revisar/aprovar/aplicar separadamente.",
            "Quadrix: cargos e remuneração por cargo permanecem bloqueados pelo merge canônico; prova e inscrições foram confirmadas no Anexo I p.40.",
            "MSConcursos: cargos não foram inventados; órgão foi corrigido para o CRIS, enquanto Tupã permanece como município de atuação; prova e inscrições foram confirmadas no Anexo III p.12.",
            "Os PDFs são editais de abertura; documentos posteriores selecionados pelo portal não foram aplicados como retificações neste lote.",
        ],
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(OUTPUT), "proposals": [{"source": p["source"], "id": p["id"], "state": p["state"]} for p in proposals]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
