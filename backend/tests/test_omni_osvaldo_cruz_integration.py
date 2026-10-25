from io import BytesIO
from pathlib import Path

from pypdf import PdfReader

from app.tenderproof.contracts import Artifact, DiscoveredCandidate, PageText
from app.tenderproof.fields import extract_fields
from app.tenderproof.omni_osvaldo_cruz_jobs import (
    EXPECTED_BYTES, EXPECTED_SHA256, ARTIFACT_ID, DOCUMENT_URL,
    build_reviewed_payload,
)
from app.tenderproof.reviewed_run_import import ReviewedRun, _run_id, import_reviewed_run
from app.tenderproof.store import TenderProofStore

PDF = (Path(__file__).resolve().parents[2] / "docs/execucao/evidencias/T010/id16.pdf")


def test_id16_extract_fields_uses_pinned_parser_and_relative_store_path(monkeypatch, tmp_path):
    content = PDF.read_bytes()
    monkeypatch.setenv("TENDERPROOF_ARTIFACT_DIR", str(tmp_path))
    stored = tmp_path / "id16.pdf"
    stored.write_bytes(content)
    pages = [PageText(artifact_id=ARTIFACT_ID, page_number=i + 1, text=page.extract_text() or "")
             for i, page in enumerate(PdfReader(BytesIO(content)).pages)]
    artifact = Artifact(artifact_id=ARTIFACT_ID, sha256=EXPECTED_SHA256, byte_len=EXPECTED_BYTES,
                        url_requested=DOCUMENT_URL, url_final=DOCUMENT_URL,
                        content_type="application/pdf", downloaded_at="2026-09-13T00:00:00Z",
                        storage_path=stored.name)
    candidate = DiscoveredCandidate(candidate_id="omni-246", title_observed="Osvaldo Cruz",
        detail_url_observed="https://portal.omniconcursospublicos.com.br/informacoes/246/",
        external_id="246", observed_at="2026-09-13T00:00:00Z", source="omni_open")
    fields = extract_fields(candidate=candidate, artifact=artifact, pages=pages)
    cargos = next(field for field in fields if field.field_name == "cargos")
    assert cargos.state.value == "supported"
    assert len(cargos.value) == 18
    assert cargos.value[0]["nome"] == "Bibliotecário"
    assert cargos.value[0]["remuneracao"] == "2327.96"
    assert all(e.artifact_id == ARTIFACT_ID for e in cargos.evidence)


def test_id16_identity_or_sha_drift_never_promotes_cargos(tmp_path, monkeypatch):
    content = PDF.read_bytes()
    monkeypatch.setenv("TENDERPROOF_ARTIFACT_DIR", str(tmp_path))
    (tmp_path / "id16.pdf").write_bytes(content)
    pages = [PageText(artifact_id=ARTIFACT_ID, page_number=1, text="")]
    artifact = Artifact(artifact_id=ARTIFACT_ID, sha256="0" * 64, byte_len=EXPECTED_BYTES,
                        url_requested=DOCUMENT_URL, url_final=DOCUMENT_URL,
                        downloaded_at="2026-09-13T00:00:00Z", storage_path="id16.pdf")
    candidate = DiscoveredCandidate(candidate_id="omni-246", title_observed="Osvaldo Cruz",
        detail_url_observed="https://portal.omniconcursospublicos.com.br/informacoes/246/",
        external_id="246", observed_at="2026-09-13T00:00:00Z", source="omni_open")
    fields = extract_fields(candidate=candidate, artifact=artifact, pages=pages)
    cargos = next(field for field in fields if field.field_name == "cargos")
    assert cargos.state.value != "supported"


def test_id16_reviewed_envelope_is_deterministic_for_same_stored_artifact():
    content = PDF.read_bytes()
    payload_1 = build_reviewed_payload(content, observed_at="2026-09-13T00:00:00Z")
    payload_2 = build_reviewed_payload(content, observed_at="2026-09-13T00:00:00Z")
    assert _run_id(ReviewedRun.model_validate(payload_1)) == "tp-reviewed-31aab6eedecc18062fb5469e42d194d6"
    assert _run_id(ReviewedRun.model_validate(payload_1)) == _run_id(ReviewedRun.model_validate(payload_2))
    other_owner = build_reviewed_payload(content, owner_user_id=2, observed_at="2026-09-13T00:00:00Z")
    assert _run_id(ReviewedRun.model_validate(payload_1)) != _run_id(ReviewedRun.model_validate(other_owner))
    assert import_reviewed_run(payload_1, TenderProofStore(), dry_run=True)["run_id"] == _run_id(ReviewedRun.model_validate(payload_1))
