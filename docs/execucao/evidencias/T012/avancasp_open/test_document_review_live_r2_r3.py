import hashlib
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[5]
EVIDENCE = ROOT / "docs/execucao/evidencias/T012/avancasp_open"
sys.path.insert(0, str(ROOT / "backend"))
sys.path.insert(0, str(EVIDENCE))

from app.tenderproof.contracts import Artifact  # noqa: E402
from app.tenderproof.pdf_text import extract_pages  # noqa: E402
from app.tenderproof.store import TenderProofStore  # noqa: E402
import avancasp_parser as old_parser  # noqa: E402
import avancasp_parser_r3_pin as r3_parser  # noqa: E402


PDF = EVIDENCE / "avancasp-open-272-bbc8f6fc-a0a1-49ef-aa1d-7d5d2403f7ce.pdf"


def test_staging_is_exact_first_manifest_and_old_failure_is_stale_pin():
    receipt = json.loads(
        (EVIDENCE / "document-review-live-r2-first-artifact-receipt-20260913.json").read_text(encoding="utf-8")
    )
    raw = PDF.read_bytes()
    staging = receipt["staging"]
    assert staging["sha256"] == hashlib.sha256(raw).hexdigest()
    assert staging["byte_len"] == len(raw) == 750381
    assert staging["pages"] == 48
    assert receipt["prepare"]["stored_sha256"] == staging["sha256"]
    assert receipt["prepare"]["failure_reason"].endswith("artifact is not pinned")
    manifest = json.loads(
        (EVIDENCE / "live-proposal-receipt-20260913.json").read_text(encoding="utf-8")
    )
    pending = next(doc for doc in manifest["pending_documents"] if doc["url"].endswith("bbc8f6fc-a0a1-49ef-aa1d-7d5d2403f7ce.pdf"))
    assert pending["title"] == "EDITAL COMPLETO 04/09/2026"
    assert pending["kind"] == "edital"
    assert pending["url"].endswith("bbc8f6fc-a0a1-49ef-aa1d-7d5d2403f7ce.pdf")
    with pytest.raises(ValueError, match="artifact drift"):
        old_parser.preflight(raw)
    assert old_parser.DOCUMENT_URL != pending["url"]


def test_r3_pin_accepts_staging_and_rejects_old_and_sibling_artifacts():
    raw = PDF.read_bytes()
    assert r3_parser.preflight(raw)["sha256"] == r3_parser.EXPECTED_SHA256
    r3_parser.validate_document_binding(
        title="EDITAL COMPLETO 04/09/2026", kind="edital", url=r3_parser.DOCUMENT_URL
    )
    old_pdf = (EVIDENCE / "avancasp-open-edital-272.pdf").read_bytes()
    sibling = (EVIDENCE / "avancasp-open-272-6d52089a-0ad3-4a18-bef5-306c27315785.pdf").read_bytes()
    with pytest.raises(ValueError, match="artifact drift"):
        r3_parser.preflight(old_pdf)
    with pytest.raises(ValueError, match="artifact drift"):
        r3_parser.preflight(sibling)
    with pytest.raises(ValueError, match="manifest mismatch"):
        r3_parser.validate_document_binding(title="EDITAL COMPLETO 04/09/2026", kind="outro", url=r3_parser.DOCUMENT_URL)


def test_old_and_staged_pdfs_have_same_identity_but_are_not_content_substitutions():
    old_raw = (EVIDENCE / "avancasp-open-edital-272.pdf").read_bytes()
    staged_raw = PDF.read_bytes()
    assert old_raw != staged_raw
    old_pages, *_ = extract_pages(old_raw, artifact_id="old-b0ba")
    staged_pages, *_ = extract_pages(staged_raw, artifact_id="staged-c60")
    assert len(old_pages) == len(staged_pages) == 48
    for pages in (old_pages, staged_pages):
        first = pages[0].text
        assert "CONCURSO PÚBLICO 01/2026" in first
        assert "PREFEITURA MUNICIPAL DE CABRE" in first
    assert hashlib.sha256(old_raw).hexdigest() != hashlib.sha256(staged_raw).hexdigest()


def test_save_commit_preserves_exact_hash_and_hash_addressed_basename(tmp_path, monkeypatch):
    monkeypatch.setenv("TENDERPROOF_ARTIFACT_DIR", str(tmp_path / "artifacts"))
    raw = PDF.read_bytes()
    artifact = Artifact(
        artifact_id="avancasp-open-edital-272-bbc8f6fc",
        sha256=r3_parser.EXPECTED_SHA256,
        byte_len=r3_parser.EXPECTED_BYTES,
        url_requested=r3_parser.DOCUMENT_URL,
        url_final=r3_parser.DOCUMENT_URL,
        content_type="application/pdf",
        downloaded_at="2026-09-13T00:00:00Z",
    )
    store = TenderProofStore()
    saved = store.save_artifact_file(artifact, raw)
    assert Path(saved.storage_path).name.endswith(f"-{r3_parser.EXPECTED_SHA256}.pdf")
    assert store.load_artifact_bytes(saved) == raw
