"""Prepare T005 Barra Longa evidence; never imports or publishes."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from app.tenderproof.barra_longa_parser import (
    DOCUMENT_URL, EXPECTED_SHA256, EXPECTED_BYTES, ARTIFACT_ID, parse, preflight,
    derive, build_reviewed_payload,
)
from app.tenderproof.reviewed_run_import import ReviewedRun, _run_id, build_run

ROOT = Path(__file__).resolve().parents[2]
PDF = ROOT / "docs/execucao/evidencias/T005/artifacts/T005-concurso32-art-07b137af65.pdf"
OUT = ROOT / "docs/execucao/evidencias/T005"


def main() -> None:
    content = PDF.read_bytes()
    pf = preflight(content)
    parsed = parse(content)
    d1 = derive(parsed)
    d2 = derive(json.loads(json.dumps(parsed, ensure_ascii=False)))
    if d1 != d2:
        raise ValueError("derivation mismatch")
    payload = build_reviewed_payload(content, owner_user_id=1)
    # Use a portable workspace path, keeping the PDF itself the immutable
    # source of bytes rather than duplicating it in the receipt.
    payload["artifact"].pop("content_base64", None)
    payload["artifact"]["content_path"] = str(PDF.relative_to(ROOT))
    model = ReviewedRun.model_validate(payload)
    run = build_run(model, content)
    dry = {"status": "validated", "dry_run": True, "run_id": _run_id(model),
           "fields": [f.field_name for f in run.fields], "catalogue_mutated": False}
    proposal = {"schema": "t005.isolated-reference-proposal.v1", "state": "prepared",
                "apply": False, "catalogue_mutated": False, "concurso_id": 32,
                "source_id": 47, "external_id": "129", "run_id": _run_id(model),
                "reference_only": True, "eligible_fields": dry["fields"],
                "blocked_fields": {"retificacoes": "nenhuma comprovada no artefato", "publicacoes": "nenhuma comprovada no artefato"},
                "artifact_sha256": EXPECTED_SHA256}
    (OUT / "T005-concurso32-preflight.json").write_text(json.dumps(pf, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (OUT / "T005-concurso32-derivation-a.json").write_text(json.dumps(d1, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    (OUT / "T005-concurso32-derivation-b.json").write_text(json.dumps(d2, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    (OUT / "T005-concurso32-reviewed-run-owner1.json").write_text(json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    (OUT / "T005-concurso32-dry-run.json").write_text(json.dumps(dry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (OUT / "T005-concurso32-isolated-proposal.json").write_text(json.dumps(proposal, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    receipt = {"schema": "t005.review-receipt.v1", "revision": "r2", "contest": 32, "source": "elo_open", "source_id": 47,
               "artifact_id": ARTIFACT_ID, "sha256": EXPECTED_SHA256, "byte_len": EXPECTED_BYTES,
               "parser": "app.tenderproof.barra_longa_parser", "run_id": _run_id(model),
               "preflight": "passed", "derivations": "equal", "cargo_schedule_applicability": "each_cargo_evidence_pages_18_and_23", "baseline_catalogue": {"concurso_id": 32, "cargos": None, "inscricao_dates_match": True, "prova_data_canonical": False, "taxa_publishable": False}, "expected_proposed_fields": ["cargos"], "dry_run": dry,
               "proposal": "prepared_isolated_no_apply", "network": False, "catalogue_mutated": False,
               "review_required": True}
    (OUT / "T005-concurso32-receipt.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt, ensure_ascii=False))


if __name__ == "__main__":
    main()
