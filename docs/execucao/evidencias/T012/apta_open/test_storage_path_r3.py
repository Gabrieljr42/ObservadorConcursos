"""Offline source-scoped proof of the APTA artifact-path contract.

The production resolver accepts a deployment-local basename, not a preserved
workspace-relative directory.  The test copies the pinned PDF into an
isolated configured artifact root and proves hash/byte validation plus the
canonical storage name without importing or publishing anything.
"""
from hashlib import sha256
from pathlib import Path

from app.tenderproof.contracts import Artifact
from app.tenderproof.store import TenderProofStore


ROOT = Path(__file__).resolve().parents[5]
PDF = ROOT / "backend/.tenderproof/r60rec/artifacts/art-18bef50e17-db9c6d26a285102ae051761500d893c81616b07b69a086ec5353307d5975d79c.pdf"
SHA = "db9c6d26a285102ae051761500d893c81616b07b69a086ec5353307d5975d79c"


def test_apta_pinned_pdf_uses_configured_artifact_root(tmp_path, monkeypatch):
    content = PDF.read_bytes()
    assert len(content) == 362093
    assert sha256(content).hexdigest() == SHA
    artifact_root = tmp_path / "artifacts"
    monkeypatch.setenv("TENDERPROOF_ARTIFACT_DIR", str(artifact_root))
    artifact = Artifact(
        artifact_id="art-18bef50e17", sha256=SHA, byte_len=len(content),
        url_requested="https://cdn-arquivo.concursos.srv.br/APTA/00708/PUBLICACOES/Edital_Completo_2026_07_31_09_13_43.pdf",
        url_final="https://cdn-arquivo.concursos.srv.br/APTA/00708/PUBLICACOES/Edital_Completo_2026_07_31_09_13_43.pdf",
        downloaded_at="2026-09-13T00:00:00Z",
        storage_path="r60rec/artifacts/foreign.pdf",
    )
    stored = TenderProofStore().save_artifact_file(artifact, content)
    expected = f"art-18bef50e17-{SHA}.pdf"
    assert stored.storage_path == expected
    assert (artifact_root / expected).read_bytes() == content
    assert TenderProofStore().load_artifact_bytes(stored) == content
