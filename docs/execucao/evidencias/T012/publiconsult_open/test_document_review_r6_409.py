"""Offline reproduction of the R6 store-bound 409 path."""
from pathlib import Path

from app.tenderproof.contracts import Artifact
from app.tenderproof.document_identity import document_identity
from app.tenderproof.store import TenderProofStore


PDF = Path(__file__).with_name("document-taf-681.pdf")
SHA = "d358bb8a61fb4e9dcc9c1bf101d28b364af951f0180f3ba8bf0a4c6866732bb7"
URL = "https://gsistbucket.s3.amazonaws.com/publiconsult/Anexos/681/PM%20VOTUPORANGA%20-%20PS%201-2026%20-EDITAL%20DE%20CONVOCA%C3%87%C3%83O%20TAF.pdf?raw=1"
TITLE = "Edital de Convocação para o Teste de Aptidão Física para o cargo Técnico em Educação X – Desenvolvimento Infantil II"


def test_r6_payload_is_exact_but_unregistered_api_blob_is_409_precondition(tmp_path, monkeypatch):
    content = PDF.read_bytes()
    monkeypatch.setenv("TENDERPROOF_ARTIFACT_DIR", str(tmp_path / "artifacts"))
    artifact = Artifact(artifact_id="publiconsult-open-taf-681-r2", sha256=SHA,
        byte_len=341466, url_requested=URL, url_final=URL,
        downloaded_at="2026-09-13T13:48:30Z",
        storage_path="publiconsult-open-taf-681-r2-d358bb8a61fb4e9dcc9c1bf101d28b364af951f0180f3ba8bf0a4c6866732bb7.pdf")
    document = {"title": TITLE, "url": URL, "kind": "outro"}
    assert document_identity(document)[3] == (("raw", "1"),)
    store = TenderProofStore()
    # This is the server-side precondition checked before page/identity validation.
    assert store.load_artifact_bytes(artifact) is None
    stored = store.save_artifact_file(artifact, content)
    assert stored.storage_path.endswith(f"{SHA}.pdf")
    assert store.load_artifact_bytes(stored) == content
