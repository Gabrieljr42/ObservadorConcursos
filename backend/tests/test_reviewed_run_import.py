import base64
import hashlib

import pytest

from app.tenderproof.reviewed_run_import import import_reviewed_run
from app.tenderproof.store import TenderProofStore


def envelope(content=b"reviewed edital"):
    digest = hashlib.sha256(content).hexdigest()
    return {
        "schema": "tenderproof.reviewed-run.v1", "source": "contemax_open",
        "concurso_id": 17, "external_id": "c-17", "title": "Edital 001/2024",
        "detail_url": "https://example.test/17", "observed_at": "2026-09-12T20:00:00Z",
        "reference_only": True, "pending_fields": [],
        "owner_user_id": 42,
        "artifact": {"artifact_id": "art-17", "sha256": digest, "byte_len": len(content),
                      "url_requested": "https://example.test/17.pdf", "url_final": "https://example.test/17.pdf",
                      "downloaded_at": "2026-09-12T20:00:00Z",
                      "content_base64": base64.b64encode(content).decode()},
        "fields": [{"field_name": "cargos", "value": [{"nome": "Agente", "vagas": 1, "unidade": "40h"}], "units": {"carga_horaria": "h/semana"},
                    "evidence": [{"evidence_id": "e1", "artifact_id": "art-17",
                                  "document_sha256": digest, "source_url": "https://example.test/17.pdf",
                                  "page_number": 8, "snippet": "ANEXO I", "method": "manual",
                                  "method_version": "review-1"}]},
                   {"field_name": "vagas", "value": 1,
                    "evidence": [{"evidence_id": "e2", "artifact_id": "art-17",
                                  "document_sha256": digest, "source_url": "https://example.test/17.pdf",
                                  "page_number": 8, "snippet": "1 vaga", "method": "manual",
                                  "method_version": "review-1"}]}]
    }


def test_reviewed_import_dry_run_apply_repeat_and_conflict(tmp_path, monkeypatch):
    monkeypatch.setenv("TENDERPROOF_ARTIFACT_DIR", str(tmp_path / "artifacts"))
    store = TenderProofStore()
    payload = envelope()
    dry = import_reviewed_run(payload, store, dry_run=True)
    assert dry["status"] == "validated" and store.get_run(dry["run_id"]) is None
    applied = import_reviewed_run(payload, store, dry_run=False)
    assert applied["status"] == "imported"
    assert import_reviewed_run(payload, store, dry_run=False)["status"] == "idempotent"
    conflict = envelope(b"different")
    conflict["artifact"]["artifact_id"] = "art-other"
    monkeypatch.setattr("app.tenderproof.reviewed_run_import._run_id", lambda _: dry["run_id"])
    with pytest.raises(ValueError):
        import_reviewed_run(conflict, store, dry_run=False)
    # A different run cannot repoint the already claimed artifact_id either.
    conflict["artifact"]["artifact_id"] = "art-17"
    monkeypatch.setattr("app.tenderproof.reviewed_run_import._run_id", lambda _: "tp-reviewed-other")
    with pytest.raises(ValueError, match="artifact_id"):
        import_reviewed_run(conflict, store, dry_run=False)


def test_reviewed_import_rejects_pending_and_bad_bytes_without_persisting(tmp_path, monkeypatch):
    monkeypatch.setenv("TENDERPROOF_ARTIFACT_DIR", str(tmp_path / "artifacts"))
    store = TenderProofStore()
    payload = envelope()
    payload["pending_fields"] = ["prova_data"]
    with pytest.raises(ValueError, match="pending_fields"):
        import_reviewed_run(payload, store, dry_run=False)
    payload = envelope()
    payload["artifact"]["content_base64"] = base64.b64encode(b"tampered").decode()
    with pytest.raises(ValueError, match="sha256"):
        import_reviewed_run(payload, store, dry_run=False)
    assert list((tmp_path / "artifacts").glob("**/*")) == []


def test_cli_defaults_to_dry_run(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("TENDERPROOF_ARTIFACT_DIR", str(tmp_path / "artifacts"))
    envelope_path = tmp_path / "reviewed.json"
    import json
    envelope_path.write_text(json.dumps(envelope(envelope_path.read_bytes() if False else b"reviewed edital")), encoding="utf-8")
    from scripts.import_reviewed_run import main
    assert main([str(envelope_path)]) == 0
    output = json.loads(capsys.readouterr().out)
    assert output["status"] == "validated"
    assert not (tmp_path / "artifacts" / "operational.sqlite3").exists()


def test_evidence_id_is_not_semantic_but_snippet_value_and_units_are(tmp_path, monkeypatch):
    monkeypatch.setenv("TENDERPROOF_ARTIFACT_DIR", str(tmp_path / "artifacts"))
    store = TenderProofStore()
    first = envelope()
    second = envelope()
    second["fields"][0]["evidence"][0]["evidence_id"] = "different-random-id"
    from app.tenderproof.reviewed_run_import import _run_id, ReviewedRun
    assert _run_id(ReviewedRun.model_validate(first)) == _run_id(ReviewedRun.model_validate(second))
    assert import_reviewed_run(first, store, dry_run=False)["status"] == "imported"
    assert import_reviewed_run(second, store, dry_run=False)["status"] == "idempotent"
    changed = envelope()
    changed["fields"][0]["evidence"][0]["snippet"] = "different snippet"
    assert _run_id(ReviewedRun.model_validate(changed)) != _run_id(ReviewedRun.model_validate(first))
    changed_value = envelope()
    changed_value["fields"][0]["value"][0]["vagas"] = 2
    assert _run_id(ReviewedRun.model_validate(changed_value)) != _run_id(ReviewedRun.model_validate(first))
    changed_units = envelope()
    changed_units["fields"][0]["units"] = {"carga_horaria": "h/dia"}
    assert _run_id(ReviewedRun.model_validate(changed_units)) != _run_id(ReviewedRun.model_validate(first))
    changed_method = envelope()
    changed_method["fields"][0]["evidence"][0]["method_version"] = "fafipa-4208-r14"
    assert _run_id(ReviewedRun.model_validate(changed_method)) != _run_id(ReviewedRun.model_validate(first))


def test_run_id_is_owner_scoped_and_owner_replay_is_idempotent(tmp_path, monkeypatch):
    monkeypatch.setenv("TENDERPROOF_ARTIFACT_DIR", str(tmp_path / "artifacts"))
    from app.tenderproof.reviewed_run_import import _run_id, ReviewedRun
    first = envelope()
    other = envelope()
    other["owner_user_id"] = 901
    left = _run_id(ReviewedRun.model_validate(first))
    right = _run_id(ReviewedRun.model_validate(other))
    assert left != right
    store = TenderProofStore()
    assert import_reviewed_run(first, store, dry_run=False)["status"] == "imported"
    assert import_reviewed_run(first, store, dry_run=False)["status"] == "idempotent"
    assert store.get_run(left).owner_user_id == 42
    assert store.get_run(right) is None


def test_null_target_is_valid_create_handoff_but_nonpositive_is_rejected():
    from app.tenderproof.reviewed_run_import import ReviewedRun
    payload = envelope()
    payload["concurso_id"] = None
    assert ReviewedRun.model_validate(payload).concurso_id is None
    payload["concurso_id"] = 0
    with pytest.raises(ValueError):
        ReviewedRun.model_validate(payload)
    payload["concurso_id"] = -4
    with pytest.raises(ValueError):
        ReviewedRun.model_validate(payload)


def test_run_id_ignores_runtime_paths_but_binds_artifact_pins(tmp_path):
    from app.tenderproof.reviewed_run_import import _run_id, ReviewedRun
    first = envelope()
    raw = b"reviewed edital"
    left = tmp_path / "Windows" / "artifact.pdf"
    right = tmp_path / "CodexSandboxOffline" / "container" / "artifact.pdf"
    left.parent.mkdir(parents=True)
    right.parent.mkdir(parents=True)
    left.write_bytes(raw)
    right.write_bytes(raw)
    for payload, path in ((first, left), (second := envelope(), right)):
        payload["artifact"].pop("content_base64")
        payload["artifact"]["content_path"] = str(path)
    assert _run_id(ReviewedRun.model_validate(first)) == _run_id(ReviewedRun.model_validate(second))
    changed_url = envelope()
    changed_url["artifact"]["url_final"] += "?revision=2"
    assert _run_id(ReviewedRun.model_validate(changed_url)) != _run_id(ReviewedRun.model_validate(envelope()))
    changed_artifact = envelope()
    changed_artifact["artifact"]["artifact_id"] = "art-other"
    assert _run_id(ReviewedRun.model_validate(changed_artifact)) != _run_id(ReviewedRun.model_validate(envelope()))
    changed_page = envelope()
    changed_page["fields"][0]["evidence"][0]["page_number"] = 9
    assert _run_id(ReviewedRun.model_validate(changed_page)) != _run_id(ReviewedRun.model_validate(envelope()))


def test_legacy_run_replay_is_read_only_and_deduplicated(tmp_path, monkeypatch):
    from app.tenderproof import reviewed_run_import as importer
    payload = envelope()
    monkeypatch.setenv("TENDERPROOF_ARTIFACT_DIR", str(tmp_path / "artifacts"))
    store = TenderProofStore()
    legacy_id = importer._legacy_run_id(importer.ReviewedRun.model_validate(payload))
    current_id = importer._run_id
    monkeypatch.setattr(importer, "_run_id", lambda _: legacy_id)
    assert importer.import_reviewed_run(payload, store, dry_run=False)["status"] == "imported"
    monkeypatch.setattr(importer, "_run_id", current_id)
    replay = importer.import_reviewed_run(payload, store, dry_run=False)
    assert replay["status"] == "idempotent_legacy" and replay["run_id"] == legacy_id
