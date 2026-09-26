import hashlib
import json
from pathlib import Path
import shutil

import pytest

from app.tenderproof.batch60_recovered_adapters import BATCH60_RECOVERED_ADAPTERS
from app.tenderproof.contracts import Artifact, PageText
from app.tenderproof.fields import extract_fields
from app.tenderproof.reviewed_run_import import ReviewedRun, import_reviewed_run
from app.tenderproof.store import TenderProofStore


ROOT = Path(__file__).resolve().parents[2]
FIX = ROOT / "backend/tests/fixtures/tenderproof_batch60_blockers"
PDF = ROOT / "backend/.tenderproof/r60rec/artifacts/art-18bef50e17-db9c6d26a285102ae051761500d893c81616b07b69a086ec5353307d5975d79c.pdf"
OUT = ROOT / "backend/.tenderproof/r60rec/processing/fa88d374b9cf5e059fad4a2fe406feae4c49cbf4803083ec521d3c75ee22557c/2c457bf16fb24e7997de5634496f02b5/output.json"


def _case():
    adapter = BATCH60_RECOVERED_ADAPTERS["apta_open"]
    listing = (FIX / "apta_open-cycle1-listing-279172bb39.html").read_text(encoding="utf-8")
    detail = (FIX / "apta_open-cycle1-detail-1d6799692c.html").read_text(encoding="utf-8")
    candidate = next(c for c in adapter.parse_listing(listing, adapter.listing_urls[0]).candidates if c.external_id == "708")
    adapter.confirm_identity(candidate, detail, candidate.detail_url_observed)
    document = adapter.choose_document(adapter.documents(detail, candidate))
    raw = PDF.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == "db9c6d26a285102ae051761500d893c81616b07b69a086ec5353307d5975d79c"
    processed = json.loads(OUT.read_text(encoding="utf-8"))
    # The integrated source dispatcher revalidates the pinned bytes from the
    # canonical artifact store.  Keep this historical fixture on that same
    # path instead of exercising the old metadata-only shape.
    artifact = Artifact(artifact_id="art-18bef50e17", sha256=hashlib.sha256(raw).hexdigest(), byte_len=len(raw), url_requested=document.url_requested, url_final=document.url_requested, content_type="application/pdf", downloaded_at="2026-09-08T14:13:29.857615Z", storage_path=str(PDF))
    pages = [PageText(artifact_id=artifact.artifact_id, page_number=p["page_number"], text=p["text"], char_count=len(p["text"]), extractor_version=processed["extractor_version"]) for p in processed["pages"]]
    return adapter, candidate, document, artifact, pages


def test_apta_reviewed_selection_extracts_provenanced_public_fields():
    _, candidate, document, artifact, pages = _case()
    fields = {f.field_name: f for f in extract_fields(candidate=candidate, artifact=artifact, pages=pages)}
    assert document.kind == "edital"
    assert fields["titulo"].state.value == "supported"
    assert fields["orgao"].state.value == "supported"
    assert fields["edital_numero"].state.value == "supported"
    assert set(fields) == {"titulo", "orgao", "edital_numero"}
    assert "cargos" not in fields
    assert all(e.document_sha256 == artifact.sha256 for f in fields.values() for e in f.evidence)


def test_apta_identity_and_artifact_drift_fail_closed():
    adapter, candidate, document, artifact, _ = _case()
    with pytest.raises(ValueError):
        adapter.validate_document_url(document.url_requested.replace("00708", "00707"), candidate)
    assert artifact.byte_len == 362093
    assert artifact.sha256 != "0" * 64


def test_apta_reviewed_envelope_matches_import_schema_after_canonical_allocation(tmp_path, monkeypatch):
    """A null target is the reviewed CREATE handoff; apply allocates canonically."""
    # R6 is the current restricted-field envelope; the older unversioned
    # envelope still records the pre-dispatch remuneration-only shape.
    envelope_path = ROOT / "docs/execucao/evidencias/T012/apta_open/apta-reviewed-envelope-r6.json"
    payload = json.loads(envelope_path.read_text(encoding="utf-8"))
    isolated_artifact = tmp_path / "apta.pdf"
    shutil.copyfile(PDF, isolated_artifact)
    payload["artifact"]["content_path"] = str(isolated_artifact)
    monkeypatch.setenv("TENDERPROOF_ARTIFACT_DIR", str(tmp_path / "store"))
    model = ReviewedRun.model_validate(payload)
    assert model.concurso_id is None
    assert [field.field_name for field in model.fields] == ["titulo", "orgao", "edital_numero"]
    result = import_reviewed_run(payload, TenderProofStore(), dry_run=True)
    assert result["status"] == "validated"
    assert result["dry_run"] is True
    assert result["fields"] == ["titulo", "orgao", "edital_numero"]

    payload["concurso_id"] = 0
    with pytest.raises(ValueError):
        ReviewedRun.model_validate(payload)
