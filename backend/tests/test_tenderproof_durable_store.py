"""Disposable persistence tests, including independent OS processes."""

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import time

import pytest

from app.tenderproof.contracts import Artifact, SessionRecord, TenderProofRun
from app.tenderproof.store import (
    TenderProofStore,
    TenderProofStoreCorruptionError,
    artifact_dir,
    operational_db_path,
    runs_dir,
)


BACKEND = Path(__file__).resolve().parents[1]
PDF = b"%PDF-1.4\noriginal evidence\n%%EOF\n"


def artifact(content=PDF, artifact_id="durable-artifact", **kwargs):
    return Artifact(
        artifact_id=artifact_id, sha256=hashlib.sha256(content).hexdigest(),
        byte_len=len(content), url_requested="https://example.test/edital.pdf",
        url_final="https://example.test/edital.pdf", downloaded_at=datetime.now(timezone.utc),
        **kwargs,
    )


def child(code: str, *args: str):
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join(filter(None, [str(BACKEND), env.get("PYTHONPATH")]))
    result = subprocess.run(
        [sys.executable, "-c", code, *args], cwd=BACKEND, env=env,
        capture_output=True, text=True, timeout=40,
    )
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


def test_workbook_persistence_preserves_extension_hash_and_pdf_compatibility():
    store=TenderProofStore()
    content=b'PK\x03\x04immutable workbook'
    saved=artifact(content,artifact_id='workbook-evidence',content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    store.save_artifact_file(saved,content)
    assert saved.storage_path.endswith('.xlsx')
    assert (artifact_dir()/saved.storage_path).read_bytes()==content
    assert TenderProofStore().load_artifact_bytes(saved)==content
    assert store.load_artifact_bytes(saved.model_copy(update={'sha256':'0'*64})) is None
    pdf=artifact(artifact_id='original-pdf')
    store.save_artifact_file(pdf,PDF)
    assert pdf.storage_path.endswith('.pdf') and store.load_artifact_bytes(pdf)==PDF
    invalid=artifact(b'<html>login</html>',artifact_id='invalid-workbook',content_type=saved.content_type)
    with pytest.raises(ValueError):store.save_artifact_file(invalid,b'<html>login</html>')
    assert store.get_blob('invalid-workbook') is None
    with pytest.raises(ValueError):store.put_blob('escape',content,extension='../xlsx')


def test_runs_and_blobs_survive_process_exit_and_are_fresh_in_existing_reader():
    reader = TenderProofStore()
    assert reader.get_run("process-run") is None
    script = """
import json, sys
from app.tenderproof.contracts import TenderProofRun
from app.tenderproof.store import TenderProofStore
store = TenderProofStore()
store.put_run(TenderProofRun(run_id='process-run', diagnostics=[sys.argv[1]]))
store.put_blob('process-artifact', sys.argv[1].encode())
print(json.dumps(store.get_run('process-run').diagnostics))
"""
    assert child(script, "before restart") == ["before restart"]
    assert reader.get_run("process-run").diagnostics == ["before restart"]
    assert reader.get_blob("process-artifact") == b"before restart"
    assert child(script, "after restart") == ["after restart"]
    assert reader.get_run("process-run").diagnostics == ["after restart"]
    assert reader.get_blob("process-artifact") == b"after restart"


def test_get_returns_detached_committed_run_and_uses_isolated_wal():
    store = TenderProofStore()
    original = TenderProofRun(run_id="detached", diagnostics=["saved"])
    store.put_run(original)
    original.diagnostics.append("not saved")
    loaded = store.get_run(original.run_id)
    loaded.diagnostics.append("also not saved")
    assert store.get_run(original.run_id).diagnostics == ["saved"]
    assert operational_db_path() == artifact_dir().parent / "operational.sqlite3"
    with store._connection() as connection:
        assert connection.execute("PRAGMA journal_mode").fetchone()[0] == "wal"
        assert connection.execute("PRAGMA synchronous").fetchone()[0] == 2
        assert connection.execute("PRAGMA busy_timeout").fetchone()[0] == 30_000
        assert {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")} == {
            "runs", "blobs", "execution_leases",
        }


def test_update_run_mutates_latest_snapshot_and_returns_committed_result():
    store = TenderProofStore()
    store.put_run(TenderProofRun(run_id="atomic-update", diagnostics=["saved"]))
    result = store.update_run("atomic-update", lambda run: run.diagnostics.append("updated"))
    assert result.diagnostics == ["saved", "updated"]
    result.diagnostics.append("not committed")
    assert store.get_run("atomic-update").diagnostics == ["saved", "updated"]
    with pytest.raises(KeyError):
        store.update_run("missing", lambda run: None)
    with pytest.raises(KeyError):
        store.update_run("../escape", lambda run: None)


def test_update_run_rolls_back_callback_failure_or_changed_identity():
    store = TenderProofStore()
    store.put_run(TenderProofRun(run_id="rollback-update", diagnostics=["saved"]))
    def failing_mutation(run):
        run.diagnostics.append("must roll back")
        raise RuntimeError("injected callback failure")
    with pytest.raises(RuntimeError, match="callback failure"):
        store.update_run("rollback-update", failing_mutation)
    with pytest.raises(TenderProofStoreCorruptionError, match="identificador divergente"):
        store.update_run("rollback-update", lambda run: setattr(run, "run_id", "different-run"))
    assert store.get_run("rollback-update").diagnostics == ["saved"]
    assert store.get_run("different-run") is None


def test_update_run_imports_legacy_snapshot_without_changing_original():
    run = TenderProofRun(run_id="legacy-update", diagnostics=["historical"])
    snapshot = runs_dir() / "legacy-update.json"
    snapshot.write_text(run.model_dump_json(), encoding="utf-8")
    preserved = snapshot.read_bytes()
    result = TenderProofStore().update_run(run.run_id, lambda run: run.diagnostics.append("current"))
    assert result.diagnostics == ["historical", "current"]
    assert snapshot.read_bytes() == preserved
    assert TenderProofStore().get_run(run.run_id).diagnostics == result.diagnostics


def test_session_update_after_external_work_does_not_erase_concurrent_process_completion():
    store = TenderProofStore()
    store.put_run(TenderProofRun(
        run_id="replay-completion-race", execution_status="awaiting_selection",
        sessions=[SessionRecord(phase="discovery", session_id="session-race")],
    ))
    session_script = """
import json, time
from app.tenderproof.store import TenderProofStore, artifact_dir
store = TenderProofStore()
stale = store.get_run('replay-completion-race')
assert stale.execution_status.value == 'awaiting_selection'
(artifact_dir().parent / 'replay-read.signal').write_text('ready')
deadline = time.monotonic() + 10
while not (artifact_dir().parent / 'completed.signal').exists():
    assert time.monotonic() < deadline, 'completion process did not commit'
    time.sleep(.01)
def apply_session_update(latest):
    latest.sessions[0].replay_status = 'available'
    latest.sessions[0].replay_url = 'https://example.test/replay'
updated = store.update_run(stale.run_id, apply_session_update)
print(json.dumps({'status': updated.execution_status.value, 'diagnostics': updated.diagnostics}))
"""
    completion_script = """
import json, time
from app.tenderproof.contracts import ExecutionStatus
from app.tenderproof.store import TenderProofStore, artifact_dir
deadline = time.monotonic() + 10
while not (artifact_dir().parent / 'replay-read.signal').exists():
    assert time.monotonic() < deadline, 'replay process did not read'
    time.sleep(.01)
store = TenderProofStore()
run = store.get_run('replay-completion-race')
run.execution_status = ExecutionStatus.COMPLETED
run.diagnostics = ['completed by the acquisition process']
run.semantic_hash = 'a' * 64
store.put_run(run)
(artifact_dir().parent / 'completed.signal').write_text('committed')
print(json.dumps(True))
"""
    with ThreadPoolExecutor(max_workers=2) as pool:
        session = pool.submit(child, session_script)
        completion = pool.submit(child, completion_script)
        assert completion.result() is True
        assert session.result() == {"status": "completed", "diagnostics": ["completed by the acquisition process"]}
    result = store.get_run("replay-completion-race")
    assert result.execution_status.value == "completed"
    assert result.semantic_hash == "a" * 64
    assert result.sessions[0].replay_url == "https://example.test/replay"


def test_concurrent_transactional_updates_never_lose_each_others_fields():
    store = TenderProofStore()
    store.put_run(TenderProofRun(run_id="many-updates"))
    script = """
import json, sys
from app.tenderproof.store import TenderProofStore
store = TenderProofStore()
for revision in range(6):
    note = sys.argv[1] + ':' + str(revision)
    store.update_run('many-updates', lambda run: run.diagnostics.append(note))
print(json.dumps(True))
"""
    with ThreadPoolExecutor(max_workers=4) as pool:
        assert all(pool.map(lambda worker: child(script, str(worker)), range(4)))
    assert set(store.get_run("many-updates").diagnostics) == {
        f"{worker}:{revision}" for worker in range(4) for revision in range(6)
    }


def test_legacy_snapshot_and_pdf_import_preserves_files_and_prefers_new_database_state():
    store = TenderProofStore()
    pdf_path = artifact_dir() / "legacy.pdf"
    pdf_path.write_bytes(PDF)
    saved = artifact(storage_path="C:\\old-machine\\artifacts\\legacy.pdf")
    run = TenderProofRun(run_id="legacy-run", artifact=saved, diagnostics=["historical"])
    snapshot = runs_dir() / "legacy-run.json"
    snapshot.write_text(run.model_dump_json(), encoding="utf-8")
    preserved = snapshot.read_bytes()
    loaded = store.get_run("legacy-run")
    assert loaded.diagnostics == ["historical"]
    assert store.load_artifact_bytes(loaded.artifact) == PDF
    assert TenderProofStore().get_blob(saved.artifact_id) == PDF
    loaded.diagnostics = ["current database"]
    store.put_run(loaded)
    assert TenderProofStore().get_run(run.run_id).diagnostics == ["current database"]
    assert snapshot.read_bytes() == preserved
    assert pdf_path.read_bytes() == PDF
    snapshot.unlink()
    assert store.get_run(run.run_id).diagnostics == ["current database"]


def test_legacy_import_does_not_overwrite_a_concurrent_process_update(monkeypatch):
    run = TenderProofRun(run_id="legacy-race", diagnostics=["historical"])
    snapshot = runs_dir() / "legacy-race.json"
    snapshot.write_text(run.model_dump_json(), encoding="utf-8")
    original_read = Path.read_text
    def read_then_concurrent_update(path, *args, **kwargs):
        payload = original_read(path, *args, **kwargs)
        if path == snapshot:
            child("""
import json
from app.tenderproof.contracts import TenderProofRun
from app.tenderproof.store import TenderProofStore
TenderProofStore().put_run(TenderProofRun(run_id='legacy-race', diagnostics=['newer process']))
print(json.dumps(True))
""")
        return payload
    monkeypatch.setattr(Path, "read_text", read_then_concurrent_update)
    assert TenderProofStore().get_run(run.run_id).diagnostics == ["newer process"]


def test_legacy_import_write_failure_is_visible():
    store = TenderProofStore()
    assert store.get_run("legacy-write-failure") is None
    run = TenderProofRun(run_id="legacy-write-failure")
    (runs_dir() / "legacy-write-failure.json").write_text(run.model_dump_json(), encoding="utf-8")
    with sqlite3.connect(operational_db_path()) as connection:
        connection.execute("CREATE TRIGGER deny_import BEFORE INSERT ON runs BEGIN SELECT RAISE(ABORT, 'injected import failure'); END")
    with pytest.raises(sqlite3.IntegrityError, match="injected import failure"):
        store.get_run(run.run_id)


@pytest.mark.parametrize("payload", [b"{broken", b"\xff", b'{"run_id":"wrong-id"}'])
def test_corrupt_legacy_run_is_visible_and_not_imported(payload):
    (runs_dir() / "corrupt.json").write_bytes(payload)
    store = TenderProofStore()
    with pytest.raises(TenderProofStoreCorruptionError, match="corrupt"):
        store.get_run("corrupt")
    with sqlite3.connect(operational_db_path()) as connection:
        assert connection.execute("SELECT COUNT(*) FROM runs").fetchone()[0] == 0


def test_database_corruption_is_not_hidden_by_previous_read_or_legacy_snapshot():
    store = TenderProofStore()
    run = TenderProofRun(run_id="corrupt-sqlite")
    store.put_run(run)
    assert store.get_run(run.run_id).run_id == run.run_id
    (runs_dir() / f"{run.run_id}.json").write_text(run.model_dump_json(), encoding="utf-8")
    with sqlite3.connect(operational_db_path()) as connection:
        connection.execute("UPDATE runs SET payload='invalid' WHERE run_id=?", (run.run_id,))
    with pytest.raises(TenderProofStoreCorruptionError, match="SQLite"):
        store.get_run(run.run_id)


@pytest.mark.parametrize("damage", ["same_length_corruption", "deletion"])
def test_artifact_disk_damage_is_detected_after_successful_reads(damage):
    store = TenderProofStore()
    saved = store.save_artifact_file(artifact(), PDF)
    assert store.load_artifact_bytes(saved) == store.get_blob(saved.artifact_id) == PDF
    path = artifact_dir() / saved.storage_path
    if damage == "deletion":
        path.unlink()
    else:
        path.write_bytes(b"!" * len(PDF))
    assert store.get_blob(saved.artifact_id) is None
    assert store.load_artifact_bytes(saved) is None
    assert TenderProofStore().load_artifact_bytes(saved) is None


def test_artifact_expected_hash_and_length_are_checked_and_put_blob_replaces_bytes():
    store = TenderProofStore()
    saved = store.save_artifact_file(artifact(), PDF)
    assert store.load_artifact_bytes(saved.model_copy(update={"sha256": "0" * 64})) is None
    assert store.load_artifact_bytes(saved.model_copy(update={"byte_len": len(PDF) + 1})) is None
    store.put_blob(saved.artifact_id, b"tampered")
    assert store.get_blob(saved.artifact_id) == b"tampered"
    assert store.load_artifact_bytes(saved) is None
    assert (artifact_dir() / saved.storage_path).read_bytes() == PDF
    with pytest.raises(ValueError, match="hash/tamanho"):
        store.save_artifact_file(artifact(artifact_id="bad-declaration"), b"different")
    assert store.get_blob("bad-declaration") is None


def test_run_write_failure_is_raised_and_previous_run_stays_committed():
    store = TenderProofStore()
    run = TenderProofRun(run_id="write-failure", diagnostics=["previous"])
    store.put_run(run)
    with sqlite3.connect(operational_db_path()) as connection:
        connection.execute("CREATE TRIGGER deny_run_write BEFORE INSERT ON runs BEGIN SELECT RAISE(ABORT, 'injected storage failure'); END")
    run.diagnostics = ["must not appear persisted"]
    with pytest.raises(sqlite3.IntegrityError, match="injected storage failure"):
        store.put_run(run)
    with pytest.raises(sqlite3.IntegrityError):
        store.put_run(TenderProofRun(run_id="never-persisted"))
    assert store.get_run(run.run_id).diagnostics == ["previous"]
    assert store.get_run("never-persisted") is None


def test_file_replace_failure_preserves_previous_artifact_and_removes_temporary(monkeypatch):
    store = TenderProofStore()
    saved = store.save_artifact_file(artifact(), PDF)
    def fail_replace(self, target):
        raise OSError("injected atomic replace failure")
    monkeypatch.setattr(Path, "replace", fail_replace)
    with pytest.raises(OSError, match="atomic replace failure"):
        store.put_blob(saved.artifact_id, b"new bytes")
    assert store.load_artifact_bytes(saved) == PDF
    assert not list(artifact_dir().glob("*.tmp"))


def test_failed_blob_pointer_write_does_not_destroy_previous_file():
    store = TenderProofStore()
    saved = store.save_artifact_file(artifact(), PDF)
    with sqlite3.connect(operational_db_path()) as connection:
        connection.execute("CREATE TRIGGER deny_blob_write BEFORE INSERT ON blobs BEGIN SELECT RAISE(ABORT, 'injected blob failure'); END")
    with pytest.raises(sqlite3.IntegrityError, match="injected blob failure"):
        store.put_blob(saved.artifact_id, b"new bytes")
    assert store.load_artifact_bytes(saved) == PDF
    assert (artifact_dir() / saved.storage_path).read_bytes() == PDF


@pytest.mark.parametrize("identifier", ["../outside", "..\\outside", "absolute/name", "", "x" * 129])
def test_invalid_identifiers_cannot_escape_store(identifier):
    store = TenderProofStore()
    assert store.get_run(identifier) is None
    assert store.get_blob(identifier) is None
    with pytest.raises(ValueError, match="identificador"):
        store.put_run(TenderProofRun(run_id=identifier))
    with pytest.raises(ValueError, match="identificador"):
        store.put_blob(identifier, b"x")


def test_independent_processes_concurrently_persist_runs_and_only_one_acquires_global_lease():
    script = """
import json, sys
from app.tenderproof.contracts import TenderProofRun
from app.tenderproof.store import TenderProofStore
store = TenderProofStore()
for revision in range(8):
    store.put_run(TenderProofRun(run_id='worker-' + sys.argv[1], diagnostics=[str(revision)]))
token = store.acquire_execution_lease(ttl_seconds=30)
print(json.dumps(token))
"""
    with ThreadPoolExecutor(max_workers=6) as pool:
        tokens = list(pool.map(lambda worker: child(script, str(worker)), range(6)))
    acquired = [token for token in tokens if token is not None]
    assert len(acquired) == 1
    store = TenderProofStore()
    for worker in range(6):
        assert store.get_run(f"worker-{worker}").diagnostics == ["7"]
    assert store.acquire_execution_lease() is None
    store.release_execution_lease("wrong-owner")
    assert store.acquire_execution_lease() is None
    store.release_execution_lease(acquired[0])
    next_token = store.acquire_execution_lease()
    assert next_token and next_token != acquired[0]
    store.release_execution_lease(next_token)


def test_dead_process_lease_expires_and_stale_owner_cannot_release_or_renew_successor():
    script = """
import json
from app.tenderproof.store import TenderProofStore
print(json.dumps(TenderProofStore().acquire_execution_lease(ttl_seconds=0.4)))
"""
    old_token = child(script)
    store = TenderProofStore()
    assert old_token
    # The child has exited without release. Its persisted TTL, rather than
    # process-local state, is what permits another process to recover work.
    deadline = time.monotonic() + 4
    new_token = None
    while time.monotonic() < deadline:
        new_token = store.acquire_execution_lease(ttl_seconds=30)
        if new_token:
            break
        time.sleep(0.025)
    assert new_token and new_token != old_token
    assert store.renew_execution_lease(old_token) is False
    store.release_execution_lease(old_token)
    assert store.acquire_execution_lease() is None
    assert store.renew_execution_lease(new_token, ttl_seconds=40) is True
    store.release_execution_lease(new_token)


def test_expired_token_cannot_be_revived_before_another_acquisition(monkeypatch):
    import app.tenderproof.store as module
    monkeypatch.setattr(module.time, "time", lambda: 1000.0)
    store = TenderProofStore()
    token = store.acquire_execution_lease(ttl_seconds=10)
    assert token
    monkeypatch.setattr(module.time, "time", lambda: 1011.0)
    assert store.renew_execution_lease(token) is False
    assert store.acquire_execution_lease() != token


@pytest.mark.parametrize("ttl", [0, -1, float("nan"), float("inf")])
def test_lease_rejects_invalid_ttl(ttl):
    store = TenderProofStore()
    with pytest.raises(ValueError, match="TTL"):
        store.acquire_execution_lease(ttl)
    with pytest.raises(ValueError, match="TTL"):
        store.renew_execution_lease("not-an-owner", ttl)
