"""Create new cargo-field observations from preserved edital bytes.

This is a bounded, offline delivery step.  It clones each selected completed
run under a new run id, reuses its immutable artifact, and replaces only the
``cargos`` field with an extractor result.  It never changes the source run,
downloads a document, or calls publication.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.tenderproof.cebraspe_ponta_pora_jobs import extract_ponta_pora_jobs
from app.tenderproof.contracts import PageText, TenderProofRun
from app.tenderproof.fields import _evidence, semantic_hash
from app.tenderproof.fepese_caxambu_jobs import extract_caxambu_jobs
from app.tenderproof.jcm_carmo_cachoeira_jobs import extract_carmo_cachoeira_jobs
from app.tenderproof.processing import extract_pages_isolated
from app.tenderproof.store import TenderProofStore, artifact_dir


TARGETS = {
    "tp-tcj-e57a86e6e2ff5da5868acf49a60ac403-4": extract_carmo_cachoeira_jobs,
    "tp-tcj-2b58bacc0b6a5a028ffc292908b9b6da-1": extract_ponta_pora_jobs,
    "tp-tcj-8c4428c810c45812a92132a23bf42958-1": extract_caxambu_jobs,
}
DELIVERY_VERSION = "v3"


def _pages(run: TenderProofRun, raw: bytes) -> list[PageText]:
    # Reuse the production processor and its normalizer.  Evidence generated
    # from raw pypdf text can differ only in whitespace and then fail the
    # publication reproduction gate.
    pages, total, processed, truncated, errors = extract_pages_isolated(
        raw,
        artifact_id=run.artifact.artifact_id,
        owner_id=str(run.owner_user_id),
        max_pages=max(60, run.total_pages or 60),
        max_bytes=30 * 1024 * 1024,
        reuse_completed=True,
    )
    if errors or truncated or processed != total:
        raise RuntimeError(f"processamento normal incompleto: total={total} processadas={processed} erros={errors}")
    return pages


def _evidence_report(field) -> list[dict]:
    return [
        {
            "page": item.page_number,
            "document_sha256": item.document_sha256,
            "snippet": item.snippet,
            "method": item.method,
            "method_version": item.method_version,
        }
        for item in field.evidence
    ]


def _clone_with_roles(old: TenderProofRun, field, *, page_count: int):
    new = old.model_copy(deep=True)
    new.run_id = f"delivery-roles-20260909-{DELIVERY_VERSION}-{old.artifact.sha256[:16]}"
    new.fields = [item for item in old.fields if item.field_name != "cargos"] + [field]
    new.semantic_hash = semantic_hash(new.fields)
    # Preserve the physical PDF count from the source observation; an
    # evidence-count proxy would be incorrect for repeated fee evidence.
    new.total_pages = page_count
    new.processed_pages = page_count
    new.updated_at = datetime.now().astimezone()
    new.diagnostics = [
        *new.diagnostics,
        f"delivery_roles_20260909_{DELIVERY_VERSION}: cargos reextraído com processamento normal de bytes preservados; run original intacto",
    ]
    return new


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-id", action="append", dest="run_ids", choices=sorted(TARGETS))
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    store = TenderProofStore()
    run_ids = args.run_ids or list(TARGETS)
    report = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "scope": "three preserved published editais; cargos only",
        "network_requests": 0,
        "publication_performed": False,
        "observation_mutated": False,
        "runs": [],
    }
    for run_id in run_ids:
        old = store.get_run(run_id)
        if old is None or old.artifact is None:
            raise RuntimeError(f"run/artifact preservado não encontrado: {run_id}")
        original_payload_sha256 = hashlib.sha256(old.model_dump_json().encode()).hexdigest()
        raw = store.load_artifact_bytes(old.artifact)
        if raw is None:
            raise RuntimeError(f"bytes preservados não encontrados: {run_id}")
        pages = _pages(old, raw)
        candidate = next(
            item for item in old.candidates if item.candidate_id == old.selected_candidate_id
        )
        field = TARGETS[run_id](
            old.artifact,
            pages,
            lambda **kwargs: _evidence(**kwargs),
            source=old.source,
            external_id=candidate.external_id,
        )
        if field is None or field.state.value != "supported":
            reason = field.reason if field is not None else "extrator não aplicável"
            raise RuntimeError(f"cargos não suportado para {run_id}: {reason}")
        new = _clone_with_roles(old, field, page_count=len(pages))
        existing = store.get_run(new.run_id)
        if existing is None:
            store.put_run(new)
        elif existing.semantic_hash != new.semantic_hash:
            raise RuntimeError(f"run de entrega divergente já existe: {new.run_id}")
        report["runs"].append({
            "source_run_id": old.run_id,
            "new_run_id": new.run_id,
            "source": old.source,
            "selected_candidate_id": old.selected_candidate_id,
            "artifact_id": old.artifact.artifact_id,
            "document_sha256": old.artifact.sha256,
            "byte_len": old.artifact.byte_len,
            "pages": len(pages),
            "cargo_count": len(field.value),
            "cargo_field_state": field.state.value,
            "cargos": field.value,
            "evidence": _evidence_report(field),
            "original_run_payload_sha256": original_payload_sha256,
            "source_run_unchanged": store.get_run(old.run_id).model_dump_json() == old.model_dump_json(),
        })

    output = args.output or artifact_dir().parent / "product-completion" / f"delivery-roles-20260909-{DELIVERY_VERSION}.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")
    print(json.dumps({
        "output": str(output),
        "runs": [{"new_run_id": item["new_run_id"], "source": item["source"], "cargo_count": item["cargo_count"]} for item in report["runs"]],
        "publication_performed": False,
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
