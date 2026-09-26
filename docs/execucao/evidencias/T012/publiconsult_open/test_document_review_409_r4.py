"""Read-only reproduction of the preserved-review 409 ordering."""
from pathlib import Path
from app.tenderproof.contracts import Artifact
from app.tenderproof.store import TenderProofStore

PDF = Path(__file__).with_name("document-taf-681.pdf")
SHA = "d358bb8a61fb4e9dcc9c1bf101d28b364af951f0180f3ba8bf0a4c6866732bb7"


def test_prepare_preserved_requires_registered_blob_before_revalidation(tmp_path, monkeypatch):
    content = PDF.read_bytes()
    monkeypatch.setenv("TENDERPROOF_ARTIFACT_DIR", str(tmp_path / "artifacts"))
    artifact = Artifact(artifact_id="publiconsult-open-taf-681-r2", sha256=SHA,
        byte_len=341466, url_requested="https://gsistbucket.s3.amazonaws.com/publiconsult/Anexos/681/PM%20VOTUPORANGA%20-%20PS%201-2026%20-EDITAL%20DE%20CONVOCA%C3%87%C3%83O%20TAF.pdf",
        url_final="https://gsistbucket.s3.amazonaws.com/publiconsult/Anexos/681/PM%20VOTUPORANGA%20-%20PS%201-2026%20-EDITAL%20DE%20CONVOCA%C3%87%C3%83O%20TAF.pdf",
        downloaded_at="2026-09-13T13:48:30Z", storage_path="document-taf-681.pdf")
    store = TenderProofStore()
    assert store.load_artifact_bytes(artifact) is None
    stored = store.save_artifact_file(artifact, content)
    assert store.load_artifact_bytes(stored) == content
