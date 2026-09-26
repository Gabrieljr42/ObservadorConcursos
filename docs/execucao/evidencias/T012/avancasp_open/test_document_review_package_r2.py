import hashlib
import json
from pathlib import Path

import pytest

from app.tenderproof.contracts import Artifact, TenderProofRun
from app.tenderproof.store import TenderProofStore


ROOT = Path(__file__).resolve().parents[5]
EVIDENCE = ROOT / "docs/execucao/evidencias/T012/avancasp_open"
PACKAGE = EVIDENCE / "document-review-package-r2.json"


def test_manifest_matcher_owner_title_kind_url_blob_and_hash_basename(tmp_path, monkeypatch):
    package = json.loads(PACKAGE.read_text(encoding="utf-8"))
    assert package["owner_user_id"] == 1
    assert package["run_id"] == "tp-reviewed-d3f322671865f3ceea32af3be85ede50"
    monkeypatch.setenv("TENDERPROOF_ARTIFACT_DIR", str(tmp_path / "artifacts"))
    store = TenderProofStore()

    for index, document in enumerate(package["documents"], start=1):
        assert document["title"] == package["manifest_binding"]["title"]
        assert document["kind"] == package["manifest_binding"]["kind"]
        assert document["url"].startswith(
            "https://anexos-r2.selecao.net.br/uploads/301/concursos/272/anexos/"
        )
        source = EVIDENCE / Path(document["preserved_source"]).name
        content = source.read_bytes()
        assert len(content) == document["byte_len"]
        assert hashlib.sha256(content).hexdigest() == document["sha256"]
        artifact = Artifact(
            artifact_id=document["artifact_id"],
            sha256=document["sha256"],
            byte_len=document["byte_len"],
            url_requested=document["url"],
            url_final=document["url"],
            content_type="application/pdf",
            downloaded_at="2026-09-13T00:00:00Z",
        )
        saved = store.save_artifact_file(artifact, content)
        expected_basename = document["basename"]
        assert Path(saved.storage_path).name == expected_basename
        assert store.load_artifact_bytes(saved) == content

        # Exercise the complete commit path in the same isolated store without
        # claiming a shared/live run; each sibling gets an ephemeral child id.
        run = TenderProofRun(
            run_id=f"tp-reviewed-d3f322671865f3ceea32af3be85ede50-doc{index}",
            owner_user_id=package["owner_user_id"],
            source=package["source"],
            artifact=saved,
        )
        committed = store.commit_run_artifact(run, content)
        assert committed.artifact is not None
        assert Path(committed.artifact.storage_path).name == expected_basename
        assert store.load_artifact_bytes(committed.artifact) == content


def test_siblings_are_distinct_revisions_and_match_exact_pending_manifest():
    package = json.loads(PACKAGE.read_text(encoding="utf-8"))
    docs = package["documents"]
    assert len(docs) == 2
    assert all(d["title"] == "EDITAL COMPLETO 04/09/2026" for d in docs)
    assert all(d["kind"] == "edital" for d in docs)
    assert docs[0]["url"] != docs[1]["url"]
    assert docs[0]["sha256"] != docs[1]["sha256"]
    assert docs[0]["byte_len"] != docs[1]["byte_len"]
    assert docs[0]["pages"] != docs[1]["pages"]
    assert all(d["duplicate_of_sibling"] is False for d in docs)


def test_hash_addressed_basename_cannot_hide_a_mismatch():
    package = json.loads(PACKAGE.read_text(encoding="utf-8"))
    for document in package["documents"]:
        assert document["basename"].endswith(f"-{document['sha256']}.pdf")
        assert document["basename"].startswith(document["artifact_id"] + "-")
