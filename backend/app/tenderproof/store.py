"""Durable TenderProof runs, artifacts and acquisition coordination.

The operational SQLite database and immutable PDF files stay outside the
canonical catalog. Processes in one deployment must share the same local
directory (a Docker named volume is suitable; a network filesystem is not).
``TENDERPROOF_ARTIFACT_DIR`` retains its historical meaning: the PDF directory;
the database and legacy ``runs/`` directory live immediately beside it.
"""

from __future__ import annotations

from contextlib import contextmanager
import hashlib
import math
import os
from pathlib import Path
import re
import sqlite3
from threading import Lock
import time
from typing import Callable, Iterator
import uuid

from app.tenderproof.contracts import Artifact, TenderProofRun

_ARTIFACT_DIR_ENV = "TENDERPROOF_ARTIFACT_DIR"
_IDENTIFIER = re.compile(r"[A-Za-z0-9_-]{1,128}")
_BUSY_TIMEOUT_MS = 30_000
_SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
    run_id TEXT PRIMARY KEY,
    payload TEXT NOT NULL,
    saved_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS blobs (
    artifact_id TEXT PRIMARY KEY,
    storage_path TEXT NOT NULL,
    sha256 TEXT NOT NULL,
    byte_len INTEGER NOT NULL CHECK (byte_len >= 0)
);
CREATE TABLE IF NOT EXISTS execution_leases (
    name TEXT PRIMARY KEY CHECK (name = 'acquisition'),
    token TEXT NOT NULL,
    expires_at REAL NOT NULL
);
"""


class TenderProofStoreCorruptionError(ValueError):
    """A persisted run cannot be trusted; this is not a missing run."""


def artifact_dir() -> Path:
    configured = os.getenv(_ARTIFACT_DIR_ENV)
    base = Path(configured) if configured else Path(__file__).resolve().parents[2] / ".tenderproof" / "artifacts"
    base.mkdir(parents=True, exist_ok=True)
    return base


def runs_dir() -> Path:
    """Legacy JSON snapshots, imported on demand without modifying originals."""
    base = artifact_dir().parent / "runs"
    base.mkdir(parents=True, exist_ok=True)
    return base


def operational_db_path() -> Path:
    return artifact_dir().parent / "operational.sqlite3"


def _require_identifier(value: str) -> None:
    if not _IDENTIFIER.fullmatch(value):
        raise ValueError("identificador TenderProof inválido")


def _matches(content: bytes, *, sha256: str, byte_len: int) -> bool:
    return len(content) == byte_len and hashlib.sha256(content).hexdigest() == sha256


def _storage_name(value: str) -> str:
    # Older snapshots can contain Windows or Unix paths. Only the basename
    # inside the configured artifact directory is ever read.
    return Path(value.replace("\\", "/")).name


def _write_bytes_atomic(path: Path, content: bytes) -> None:
    temporary = path.with_suffix(f".{uuid.uuid4().hex}.tmp")
    try:
        with temporary.open("xb") as output:
            output.write(content)
            output.flush()
            os.fsync(output.fileno())
        temporary.replace(path)
        # Windows does not allow opening directories for fsync. The file is
        # flushed before replace on all supported systems.
        if os.name != "nt":
            directory_fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
    finally:
        temporary.unlink(missing_ok=True)


class TenderProofStore:
    # No in-memory run/byte cache and no connection held across calls: API,
    # worker, scheduler and restarted processes see committed data. Resolve
    # the directory per operation to preserve scoped demo/test environments.
    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(
            operational_db_path(), timeout=_BUSY_TIMEOUT_MS / 1000,
            isolation_level=None,
        )
        try:
            connection.row_factory = sqlite3.Row
            connection.execute(f"PRAGMA busy_timeout = {_BUSY_TIMEOUT_MS}")
            connection.execute("PRAGMA journal_mode = WAL")
            connection.execute("PRAGMA synchronous = FULL")
            connection.executescript(_SCHEMA)
            yield connection
        except BaseException:
            if connection.in_transaction:
                connection.rollback()
            raise
        finally:
            connection.close()

    @staticmethod
    def _decode_run(payload: str, run_id: str, *, origin: str) -> TenderProofRun:
        try:
            run = TenderProofRun.model_validate_json(payload)
        except ValueError as exc:
            raise TenderProofStoreCorruptionError(
                f"execução {run_id}: registro inválido em {origin}"
            ) from exc
        if run.run_id != run_id:
            raise TenderProofStoreCorruptionError(
                f"execução {run_id}: identificador divergente em {origin}"
            )
        return run

    def put_run(self, run: TenderProofRun) -> None:
        """Commit a complete run or raise; success never means memory-only."""
        _require_identifier(run.run_id)
        payload = run.model_dump_json()
        with self._connection() as connection:
            connection.execute(
                "INSERT INTO runs (run_id, payload, saved_at) VALUES (?, ?, ?) "
                "ON CONFLICT(run_id) DO UPDATE SET payload=excluded.payload, saved_at=excluded.saved_at",
                (run.run_id, payload, time.time()),
            )

    def put_run_if_absent(self, run: TenderProofRun) -> TenderProofRun:
        """Keep the first committed result of a repeatable operation."""
        _require_identifier(run.run_id)
        with self._connection() as connection:
            connection.execute(
                'INSERT OR IGNORE INTO runs (run_id,payload,saved_at) VALUES (?,?,?)',
                (run.run_id, run.model_dump_json(), time.time()))
            return self._load_run(connection, run.run_id)

    def commit_run_artifact(self, run: TenderProofRun, content: bytes) -> TenderProofRun:
        """Atomically claim a reviewed run and its artifact pointer.

        The run and artifact-id claim are checked under the same write lock;
        an existing artifact id can never be repointed to a different SHA.
        The content path is hash-addressed, so a failed transaction can only
        leave an unreferenced file, never a mismatched registered blob.
        """
        _require_identifier(run.run_id)
        if not run.artifact or not _matches(content, sha256=run.artifact.sha256, byte_len=run.artifact.byte_len):
            raise ValueError("artefato não corresponde ao run")
        extension = 'xlsx' if (run.artifact.content_type or '').split(';')[0].strip().lower() == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' else 'pdf'
        path = artifact_dir() / f"{run.artifact.artifact_id}-{run.artifact.sha256}.{extension}"
        _write_bytes_atomic(path, content)
        run.artifact.storage_path = path.name
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute("SELECT payload FROM runs WHERE run_id=?", (run.run_id,)).fetchone()
            if row is not None:
                connection.commit()
                return self._decode_run(row['payload'], run.run_id, origin='SQLite')
            blob = connection.execute("SELECT sha256 FROM blobs WHERE artifact_id=?", (run.artifact.artifact_id,)).fetchone()
            if blob is not None and blob['sha256'] != run.artifact.sha256:
                raise ValueError("conflito forte: artifact_id já aponta para outro SHA")
            connection.execute(
                "INSERT OR IGNORE INTO blobs (artifact_id, storage_path, sha256, byte_len) VALUES (?, ?, ?, ?)",
                (run.artifact.artifact_id, path.name, run.artifact.sha256, run.artifact.byte_len),
            )
            connection.execute("INSERT INTO runs (run_id,payload,saved_at) VALUES (?,?,?)", (run.run_id, run.model_dump_json(), time.time()))
            connection.commit()
            return run

    def get_run(self, run_id: str) -> TenderProofRun | None:
        if not _IDENTIFIER.fullmatch(run_id):
            return None
        with self._connection() as connection:
            return self._load_run(connection, run_id)

    def _load_run(self, connection: sqlite3.Connection, run_id: str) -> TenderProofRun | None:
        row = connection.execute("SELECT payload FROM runs WHERE run_id=?", (run_id,)).fetchone()
        if row is not None:
            return self._decode_run(row["payload"], run_id, origin="SQLite")

        snapshot = runs_dir() / f"{run_id}.json"
        try:
            payload = snapshot.read_text(encoding="utf-8")
        except FileNotFoundError:
            return None
        except UnicodeError as exc:
            raise TenderProofStoreCorruptionError(
                f"execução {run_id}: codificação inválida no snapshot JSON"
            ) from exc
        run = self._decode_run(payload, run_id, origin="snapshot JSON")
        # Never replace a newer run persisted by a concurrent API/worker while
        # the historical snapshot was being read outside a write transaction.
        connection.execute(
            "INSERT OR IGNORE INTO runs (run_id, payload, saved_at) VALUES (?, ?, ?)",
            (run_id, run.model_dump_json(), time.time()),
        )
        row = connection.execute("SELECT payload FROM runs WHERE run_id=?", (run_id,)).fetchone()
        return self._decode_run(row["payload"], run_id, origin="SQLite")

    def update_run(self, run_id: str, mutator: Callable[[TenderProofRun], None]) -> TenderProofRun:
        """Atomically mutate the latest committed run and return its snapshot.

        Use this for replay/session/comparison updates made after external I/O.
        The callback must only change the supplied model; do not perform network
        I/O or call store methods inside it, because the write lock is held.
        Callback, validation and persistence errors roll back the whole update,
        including any on-demand import of an original historical snapshot.
        """
        if not _IDENTIFIER.fullmatch(run_id):
            raise KeyError(f"execução {run_id} não encontrada")
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            run = self._load_run(connection, run_id)
            if run is None:
                raise KeyError(f"execução {run_id} não encontrada")
            mutator(run)
            payload = run.model_dump_json()
            validated = self._decode_run(payload, run_id, origin="atualização")
            connection.execute(
                "UPDATE runs SET payload=?, saved_at=? WHERE run_id=?",
                (payload, time.time(), run_id),
            )
            connection.commit()
            return validated

    def put_blob(self, artifact_id: str, content: bytes, *, extension: str = 'pdf') -> None:
        """Durably replace an artifact's bytes; declared hashes validate later.

        Files include their content hash so a failed database write cannot
        destroy the previous artifact. SQLite atomically switches the pointer;
        an interrupted write can only leave an unreferenced PDF on disk.
        """
        _require_identifier(artifact_id)
        if extension not in ('pdf','xlsx'):
            raise ValueError('extensão de artefato não suportada')
        digest = hashlib.sha256(content).hexdigest()
        path = artifact_dir() / f"{artifact_id}-{digest}.{extension}"
        _write_bytes_atomic(path, content)
        with self._connection() as connection:
            connection.execute(
                "INSERT INTO blobs (artifact_id, storage_path, sha256, byte_len) VALUES (?, ?, ?, ?) "
                "ON CONFLICT(artifact_id) DO UPDATE SET storage_path=excluded.storage_path, "
                "sha256=excluded.sha256, byte_len=excluded.byte_len",
                (artifact_id, path.name, digest, len(content)),
            )

    def get_blob(self, artifact_id: str) -> bytes | None:
        if not _IDENTIFIER.fullmatch(artifact_id):
            return None
        with self._connection() as connection:
            row = connection.execute("SELECT * FROM blobs WHERE artifact_id=?", (artifact_id,)).fetchone()
            if row is None:
                return None
            return self._read_registered_blob(row)

    @staticmethod
    def _read_registered_blob(row: sqlite3.Row) -> bytes | None:
        path = artifact_dir() / _storage_name(row["storage_path"])
        try:
            content = path.read_bytes()
        except FileNotFoundError:
            return None
        if not _matches(content, sha256=row["sha256"], byte_len=row["byte_len"]):
            return None
        return content

    def save_artifact_file(self, artifact: Artifact, content: bytes) -> Artifact:
        if not _matches(content, sha256=artifact.sha256, byte_len=artifact.byte_len):
            raise ValueError("artefato não corresponde ao hash/tamanho declarado")
        extension = 'xlsx' if (artifact.content_type or '').split(';')[0].strip().lower() == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' else 'pdf'
        if extension == 'xlsx' and not content.startswith(b'PK\x03\x04'):
            raise ValueError('artefato XLSX não contém pacote ZIP')
        self.put_blob(artifact.artifact_id, content, extension=extension)
        artifact.storage_path = f"{artifact.artifact_id}-{artifact.sha256}.{extension}"
        return artifact

    def load_artifact_bytes(self, artifact: Artifact) -> bytes | None:
        if not _IDENTIFIER.fullmatch(artifact.artifact_id):
            return None
        with self._connection() as connection:
            row = connection.execute(
                "SELECT * FROM blobs WHERE artifact_id=?", (artifact.artifact_id,),
            ).fetchone()
            if row is not None:
                content = self._read_registered_blob(row)
                return content if content is not None and _matches(
                    content, sha256=artifact.sha256, byte_len=artifact.byte_len,
                ) else None

            # Historical PDFs have no SQLite index. Validate against the
            # preserved Artifact before making them available via get_blob.
            if not artifact.storage_path:
                return None
            path = artifact_dir() / _storage_name(artifact.storage_path)
            try:
                content = path.read_bytes()
            except FileNotFoundError:
                return None
            if not _matches(content, sha256=artifact.sha256, byte_len=artifact.byte_len):
                return None
            connection.execute(
                "INSERT OR IGNORE INTO blobs (artifact_id, storage_path, sha256, byte_len) VALUES (?, ?, ?, ?)",
                (artifact.artifact_id, path.name, artifact.sha256, artifact.byte_len),
            )
            # Honor a concurrent put_blob instead of returning superseded
            # historical bytes after its atomic pointer update.
            row = connection.execute("SELECT * FROM blobs WHERE artifact_id=?", (artifact.artifact_id,)).fetchone()
            content = self._read_registered_blob(row)
            return content if content is not None and _matches(
                content, sha256=artifact.sha256, byte_len=artifact.byte_len,
            ) else None

    @staticmethod
    def _lease_ttl(ttl_seconds: float) -> float:
        ttl = float(ttl_seconds)
        if not math.isfinite(ttl) or ttl <= 0:
            raise ValueError("TTL da execução deve ser positivo e finito")
        return ttl

    def acquire_execution_lease(self, ttl_seconds: float = 600) -> str | None:
        """Claim the deployment-wide acquisition lease, or return busy.

        Callers must renew during execution, stop if renewal fails, and release
        in finally. Expiration permits recovery after a dead worker. Lease
        times use the shared host's wall clock, not a process-local clock.
        """
        ttl = self._lease_ttl(ttl_seconds)
        token = uuid.uuid4().hex
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            now = time.time()
            result = connection.execute(
                "INSERT INTO execution_leases (name, token, expires_at) VALUES ('acquisition', ?, ?) "
                "ON CONFLICT(name) DO UPDATE SET token=excluded.token, expires_at=excluded.expires_at "
                "WHERE execution_leases.expires_at<=?",
                (token, now + ttl, now),
            )
            acquired = result.rowcount == 1
            connection.commit()
            return token if acquired else None

    def renew_execution_lease(self, token: str, ttl_seconds: float = 600) -> bool:
        """Extend only a matching live token; an expired owner cannot revive."""
        ttl = self._lease_ttl(ttl_seconds)
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            now = time.time()
            result = connection.execute(
                "UPDATE execution_leases SET expires_at=? "
                "WHERE name='acquisition' AND token=? AND expires_at>?",
                (now + ttl, token, now),
            )
            renewed = result.rowcount == 1
            connection.commit()
            return renewed

    def release_execution_lease(self, token: str) -> None:
        """A stale owner's release cannot delete the next owner's lease."""
        with self._connection() as connection:
            connection.execute("DELETE FROM execution_leases WHERE name='acquisition' AND token=?", (token,))


_store: TenderProofStore | None = None
_store_lock = Lock()


def get_store() -> TenderProofStore:
    global _store
    with _store_lock:
        if _store is None:
            _store = TenderProofStore()
        return _store
