import copy
import hashlib
import json
import os
import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

ROOT = Path(__file__).resolve().parents[5]
EVIDENCE = ROOT / "docs/execucao/evidencias/T012/klc_open"
sys.path.insert(0, str(ROOT / "backend"))

from app.tenderproof.reviewed_run_import import ReviewedRun, import_reviewed_run  # noqa: E402
from app.tenderproof.store import TenderProofStore  # noqa: E402


def _payload():
    return json.loads((EVIDENCE / "klc-632-reviewed-run-r3.json").read_text(encoding="utf-8"))


def test_formal_reviewed_run_schema_has_no_operational_extras_and_validates():
    payload = _payload()
    allowed = {
        "schema", "source", "concurso_id", "external_id", "title", "detail_url",
        "artifact", "fields", "pending_fields", "reference_only", "owner_user_id", "observed_at",
    }
    assert set(payload) == allowed
    assert payload["schema"] == "tenderproof.reviewed-run.v1"
    assert payload["concurso_id"] is None
    assert payload["owner_user_id"] == 1
    assert "source_number" not in payload
    assert "run_id" not in payload
    assert "proposal_target" not in payload
    assert "operation" not in payload and "status" not in payload
    model = ReviewedRun.model_validate(payload)
    assert model.concurso_id is None
    assert [field.field_name for field in model.fields] == [
        "titulo", "orgao", "edital_numero", "inscricao_inicio", "inscricao_fim", "cargos"
    ]


def test_import_dry_run_is_validated_and_derives_run_without_serializing_it(tmp_path, monkeypatch):
    payload = _payload()
    # Isolate the read-only store lookup from any deployment database.
    monkeypatch.setenv("TENDERPROOF_ARTIFACT_DIR", str(tmp_path / "artifacts"))
    result = import_reviewed_run(payload, TenderProofStore(), dry_run=True)
    assert result == {
        "run_id": "tp-reviewed-600b17424a6e39e5c30c73f152fb0caf",
        "status": "validated",
        "dry_run": True,
        "fields": ["titulo", "orgao", "edital_numero", "inscricao_inicio", "inscricao_fim", "cargos"],
    }
    assert "run_id" not in payload
    assert payload["artifact"]["byte_len"] == 348300
    content = Path(payload["artifact"]["content_path"]).read_bytes()
    assert len(content) == payload["artifact"]["byte_len"]
    assert hashlib.sha256(content).hexdigest() == payload["artifact"]["sha256"]


@pytest.mark.parametrize("extra", [
    {"source_number": 57}, {"run_id": None}, {"proposal_target": None},
    {"operation": "CREATE"}, {"status": "READY_FOR_REVIEW"},
])
def test_formal_schema_rejects_operational_metadata_extras(extra):
    payload = _payload()
    payload.update(extra)
    with pytest.raises(ValidationError):
        ReviewedRun.model_validate(payload)


def test_handoff_keeps_operational_metadata_separate():
    handoff = json.loads((EVIDENCE / "create-envelope-r3-handoff.json").read_text(encoding="utf-8"))
    receipt = json.loads((EVIDENCE / "create-envelope-r3-receipt.json").read_text(encoding="utf-8"))
    assert handoff["source_number"] == receipt["source_number"] == 57
    assert handoff["derived_run_id"] == receipt["dry_run"]["derived_run_id"]
    assert handoff["proposal_target"] is None
    formal = _payload()
    assert "source_number" not in formal and "run_id" not in formal
