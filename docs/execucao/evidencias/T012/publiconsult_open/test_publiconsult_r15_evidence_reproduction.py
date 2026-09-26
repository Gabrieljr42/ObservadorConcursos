"""R15 reproduction of stored-vs-active Publiconsult evidence drift."""
import json
from datetime import datetime, timezone
from pathlib import Path

from app.tenderproof.contracts import Artifact
from app.tenderproof.publiconsult_t012 import fields_for_run

ROOT = Path(__file__).resolve().parents[5]
BASE = ROOT / "docs/execucao/evidencias/T012/publiconsult_open"
PDF = ROOT / "backend/.tenderproof/r30bytes/publiconsult_open/artifacts/art-30169711bf-7e3bc67ae2d209679dabaa791d7d63fb12369dd53e1da85cda9831721bd9917f.pdf"


def test_r15_active_evidence_is_pinned_but_not_r12_stored_evidence():
    envelope = json.loads((BASE / "reviewed-run-r12.json").read_text(encoding="utf-8"))
    spec = envelope["artifact"]
    artifact = Artifact(artifact_id=spec["artifact_id"], sha256=spec["sha256"],
                        byte_len=spec["byte_len"], url_requested=spec["url_requested"],
                        url_final=spec["url_final"], content_type="application/pdf",
                        downloaded_at=datetime.now(timezone.utc), storage_path=str(PDF))
    fields, validation, _ = fields_for_run(PDF.read_bytes(), artifact,
                                           source="publiconsult_open", external_id="681")
    assert validation.status.value == "valid"
    assert [field.field_name for field in fields] == ["titulo", "orgao", "edital_numero"]
    for active, stored in zip(fields, envelope["fields"]):
        active_evidence = active.evidence[0]
        stored_evidence = stored["evidence"][0]
        assert active.value == stored["value"]
        assert active_evidence.artifact_id == stored_evidence["artifact_id"]
        assert active_evidence.document_sha256 == stored_evidence["document_sha256"]
        assert active_evidence.source_url == stored_evidence["source_url"]
        assert active_evidence.page_number == stored_evidence["page_number"] == 1
        assert active_evidence.snippet != stored_evidence["snippet"]
        assert active_evidence.method == "publiconsult-source-parser"
        assert active_evidence.method_version == "t012-publiconsult-r4"
        assert stored_evidence["method"] == "preserved-pdf-review"
        assert stored_evidence["method_version"] == "t012/r12"
