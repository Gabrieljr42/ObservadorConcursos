"""TenderProof persistent document jobs, local executor and remote boundary.

SQLite is an operational job ledger, not a second contest catalog. All public
access requires the authenticated owner supplied by the application. Remote
capabilities remain internal; public job views contain only their hashes.
"""
from __future__ import annotations

from app.tenderproof.pdf_header import has_pdf_header

import hashlib
import json
import math
import os
import sqlite3
import subprocess
import sys
import time
import uuid
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable, Protocol

VERSION = 'tenderproof-pdf-v2'
OCR_VERSION = 'tenderproof-ocr-v1'
TERMINAL = ('succeeded', 'failed', 'cancelled')


class ProcessingError(ValueError):
    pass


@dataclass(frozen=True)
class ProcessingLimits:
    max_bytes: int = 10_000_000
    max_pages: int = 60
    total_seconds: float = 60
    operation_seconds: float = 30
    max_output_bytes: int = 1_000_000
    max_attempts: int = 1
    budget_usd: float = 0

    def __post_init__(self):
        for name in ('max_bytes', 'max_pages', 'max_output_bytes', 'max_attempts'):
            value = getattr(self, name)
            if type(value) is not int or value < 1:
                raise ProcessingError('invalid_limits')
        for value in (self.total_seconds, self.operation_seconds):
            if not math.isfinite(value) or value <= 0:
                raise ProcessingError('invalid_limits')
        if self.operation_seconds > self.total_seconds or self.max_attempts > 3:
            raise ProcessingError('invalid_limits')
        if not math.isfinite(self.budget_usd) or self.budget_usd < 0:
            raise ProcessingError('invalid_budget')


class RemoteProcessor(Protocol):
    """Implementations must bound each I/O and never accept client commands.

    create uses persistent idempotency key. Unknown creation must be reconciled
    by that key, never retried with a different resource identity.
    """
    hourly_usd: float
    tariff_source: str
    def create(self, key: str, limits: ProcessingLimits) -> str: ...
    def process(self, resource: str, content: bytes, limits: ProcessingLimits,
                cancelled: Callable[[], bool]) -> bytes: ...
    def close(self, resource: str) -> bool: ...
    def status(self, resource: str) -> str: ...


class ProcessingService:
    def __init__(self, root: Path, *, concurrency: int = 1, budget_usd: float = 0,
                 remote: RemoteProcessor | None = None):
        if concurrency < 1 or not math.isfinite(budget_usd) or budget_usd < 0:
            raise ProcessingError('invalid_configuration')
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.concurrency, self.budget_usd, self.remote = concurrency, budget_usd, remote
        self.db_path = self.root / 'jobs.sqlite3'
        with self._db() as db:
            db.execute('CREATE TABLE IF NOT EXISTS processing_jobs (id TEXT PRIMARY KEY, owner TEXT NOT NULL, data TEXT NOT NULL)')

    @contextmanager
    def _db(self):
        db = sqlite3.connect(self.db_path, timeout=10)
        try:
            db.execute('BEGIN IMMEDIATE')
            yield db
            db.commit()
        except BaseException:
            db.rollback()
            raise
        finally:
            db.close()

    def _read(self, db, job_id, owner):
        row = db.execute('SELECT data FROM processing_jobs WHERE id=? AND owner=?', (job_id, str(owner))).fetchone()
        if not row:
            raise ProcessingError('job_not_found')
        return json.loads(row[0])

    def _save(self, db, job):
        job['updated_at'] = time.time()
        db.execute('UPDATE processing_jobs SET data=? WHERE id=?', (json.dumps(job), job['id']))

    def _mutate(self, job_id, owner, **changes):
        with self._db() as db:
            job = self._read(db, job_id, owner)
            job.update(changes)
            self._save(db, job)
            return job

    def _directory(self, job):
        # Both segments are application-generated: never interpolate owner input.
        return self.root / hashlib.sha256(job['owner'].encode()).hexdigest() / job['id']

    @staticmethod
    def _atomic(path, data):
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_name(path.name + '.' + uuid.uuid4().hex + '.tmp')
        try:
            with temporary.open('xb') as handle:
                handle.write(data)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, path)
        finally:
            temporary.unlink(missing_ok=True)

    def enqueue(self, owner_id: str, content: bytes, *, limits: ProcessingLimits | None = None,
                mode: str = 'local', operation: str = 'extract_pdf') -> dict:
        limits = limits or ProcessingLimits()
        if not str(owner_id) or mode not in ('local', 'solari') or operation not in ('extract_pdf', 'ocr_pdf'):
            raise ProcessingError('invalid_job')
        if operation == 'ocr_pdf' and mode != 'local':
            raise ProcessingError('provider_unavailable')
        if len(content) > limits.max_bytes:
            raise ProcessingError('input_limit')
        if not has_pdf_header(content):
            raise ProcessingError('invalid_document')
        if mode == 'solari' and self.remote is None:
            raise ProcessingError('provider_unavailable')
        estimate = (self.remote.hourly_usd * (limits.total_seconds + 10) / 3600 * limits.max_attempts
                    if mode == 'solari' else 0)
        if not math.isfinite(estimate) or estimate < 0 or estimate > limits.budget_usd:
            raise ProcessingError('budget_exceeded')
        now = time.time()
        job = dict(id=uuid.uuid4().hex, owner=str(owner_id), operation=operation, mode=mode,
                   input_sha256=hashlib.sha256(content).hexdigest(), extractor_version=OCR_VERSION if operation == 'ocr_pdf' else VERSION,
                   state='queued', limits=asdict(limits), attempts=0, resources_created=0,
                   resource=None, creation_unknown=False, close_requested=False, close_confirmed=False,
                   cancel_requested=False, error=None, output_sha256=None, created_at=now, updated_at=now,
                   observed_seconds=0, estimate_usd=estimate, confirmed_cost_usd=None,
                   tariff_source=self.remote.tariff_source if mode == 'solari' else 'local; no provider resource',
                   reserved_usd=estimate, artifacts_deleted=False, started_at=None)
        with self._db() as db:
            reserved = sum(json.loads(row[0])['reserved_usd'] for row in db.execute('SELECT data FROM processing_jobs'))
            if reserved + estimate > self.budget_usd:
                raise ProcessingError('budget_exceeded')
            self._atomic(self._directory(job) / 'input.pdf', content)
            db.execute('INSERT INTO processing_jobs VALUES (?,?,?)', (job['id'], job['owner'], json.dumps(job)))
        return self.get(job['id'], owner_id)

    def get(self, job_id: str, owner_id: str) -> dict:
        with self._db() as db:
            job = self._read(db, job_id, owner_id)
        resource = job.pop('resource')
        job['resource_sha256'] = hashlib.sha256(resource.encode()).hexdigest() if resource else None
        return job

    def cancel(self, job_id: str, owner_id: str) -> dict:
        with self._db() as db:
            job = self._read(db, job_id, owner_id)
            if job['state'] not in TERMINAL:
                job['cancel_requested'] = True
                if job['state'] == 'queued':
                    job['state'] = 'cancelled'
                self._save(db, job)
        return self.get(job_id, owner_id)

    def execute(self, job_id: str, owner_id: str) -> dict:
        with self._db() as db:
            job = self._read(db, job_id, owner_id)
            if job['state'] in TERMINAL:
                return self._public(job)
            if job['state'] != 'queued':
                raise ProcessingError('job_already_claimed')
            others = [json.loads(row[0]) for row in db.execute('SELECT data FROM processing_jobs')]
            active = sum(j['state'] == 'running' or j['creation_unknown'] or
                         bool(j['resource'] and not j['close_confirmed']) for j in others)
            if active >= self.concurrency:
                raise ProcessingError('concurrency_limit')
            job.update(state='running', attempts=job['attempts'] + 1, started_at=time.time())
            self._save(db, job)
        started = time.monotonic()
        limits = ProcessingLimits(**job['limits'])
        state, error = 'failed', None
        try:
            source = self._directory(job) / 'input.pdf'
            content = source.read_bytes()
            if hashlib.sha256(content).hexdigest() != job['input_sha256']:
                raise ProcessingError('input_hash_mismatch')
            cancelled = lambda: self.get(job_id, owner_id)['cancel_requested']
            if cancelled():
                raise ProcessingError('cancelled')
            if job['mode'] == 'local':
                output = self._local(job, limits, cancelled)
            else:
                if self.remote is None:
                    raise ProcessingError('provider_unavailable')
                self._mutate(job_id, owner_id, creation_unknown=True)
                resource = self.remote.create(job_id, limits)
                job = self._mutate(job_id, owner_id, resource=resource, resources_created=1,
                                   creation_unknown=False)
                output = self.remote.process(resource, content, limits, cancelled)
            if cancelled():
                raise ProcessingError('cancelled')
            if time.monotonic() - started > limits.total_seconds:
                raise ProcessingError('timeout')
            if len(output) > limits.max_output_bytes:
                raise ProcessingError('output_limit')
            parsed = json.loads(output)
            if parsed.get('error'):
                code = parsed['error']
                raise ProcessingError(code if code in ('page_limit', 'output_limit', 'invalid_document', 'dependency_unavailable', 'timeout') else 'invalid_output')
            if parsed.get('input_sha256') != job['input_sha256'] or parsed.get('extractor_version') != job['extractor_version']:
                raise ProcessingError('output_hash_mismatch')
            pages = parsed.get('pages')
            if not isinstance(pages, list) or len(pages) > limits.max_pages or parsed.get('total_pages') != len(pages):
                raise ProcessingError('invalid_output')
            if any(not isinstance(p, dict) or p.get('page_number') != i + 1 or not isinstance(p.get('text'), str)
                   for i, p in enumerate(pages)):
                raise ProcessingError('invalid_output')
            self._atomic(self._directory(job) / 'output.json', output)
            self._mutate(job_id, owner_id, output_sha256=hashlib.sha256(output).hexdigest())
            state = 'succeeded'
        except ProcessingError as exc:
            safe = {'input_hash_mismatch', 'cancelled', 'timeout', 'output_limit', 'invalid_document',
                    'page_limit', 'invalid_output', 'output_hash_mismatch', 'provider_unavailable',
                    'live_authorization_required', 'provider_failure', 'dependency_unavailable'}
            error = str(exc) if str(exc) in safe else 'processing_failed'
            if error == 'live_authorization_required':
                self._mutate(job_id, owner_id, creation_unknown=False)
            state = 'cancelled' if error == 'cancelled' else 'failed'
        except Exception:
            error = 'processing_failed'  # Never serialize exception text, PDF content or URL.
        finally:
            with self._db() as db:
                current = self._read(db, job_id, owner_id)
            if current['resource']:
                self._mutate(job_id, owner_id, close_requested=True)
                confirmed = False
                try:
                    confirmed = bool(self.remote and self.remote.close(current['resource']))
                except Exception:
                    pass
                self._mutate(job_id, owner_id, close_confirmed=confirmed)
            self._mutate(job_id, owner_id, state=state, error={'code': error} if error else None,
                         observed_seconds=time.monotonic() - started)
        return self.get(job_id, owner_id)

    @staticmethod
    def _public(job):
        result = dict(job)
        resource = result.pop('resource')
        result['resource_sha256'] = hashlib.sha256(resource.encode()).hexdigest() if resource else None
        return result

    def _local(self, job, limits, cancelled):
        directory = self._directory(job)
        output = directory / 'worker-output.json'
        ocr = job['operation'] == 'ocr_pdf'
        worker = Path(__file__).with_name('ocr_processing_worker.py' if ocr else 'processing_worker.py')
        # Only OS runtime variables. In particular no .env, API keys, database or proxy credentials.
        env = {name: os.environ[name] for name in ('SYSTEMROOT', 'WINDIR', 'TEMP', 'TMP') if name in os.environ}
        working_directory = directory
        # CreateProcess can reject a long current directory even though Python
        # successfully reads/writes the same absolute document paths. The fixed
        # worker uses absolute paths exclusively; retain its evidence directory
        # and use a shorter existing ancestor only as its Windows launch cwd.
        if os.name == 'nt':
            while len(str(working_directory)) > 240 and working_directory.parent != working_directory:
                working_directory = working_directory.parent
        command = [sys.executable, '-I', str(worker), str(directory / 'input.pdf'),
                   str(output), str(limits.max_pages), str(limits.max_output_bytes)]
        if ocr:
            command.append(str(min(limits.total_seconds, limits.operation_seconds)))
        process = subprocess.Popen(command,
                                   cwd=working_directory, env=env, stdin=subprocess.DEVNULL,
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                   start_new_session=ocr and os.name == 'posix')
        deadline = time.monotonic() + min(limits.total_seconds, limits.operation_seconds)
        try:
            while process.poll() is None:
                if cancelled():
                    raise ProcessingError('cancelled')
                if time.monotonic() >= deadline:
                    raise ProcessingError('timeout')
                if output.exists() and output.stat().st_size > limits.max_output_bytes:
                    raise ProcessingError('output_limit')
                time.sleep(0.025)
            if not output.is_file():
                raise ProcessingError('invalid_document')
            if output.stat().st_size > limits.max_output_bytes:
                raise ProcessingError('output_limit')
            return output.read_bytes()
        finally:
            if process.poll() is None:
                if ocr and os.name == 'posix':
                    import signal
                    try:
                        os.killpg(process.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                else:
                    process.kill()
            process.wait(timeout=5)
            output.unlink(missing_ok=True)

    def completed_local(self, owner_id, content, operation, limits):
        """Reuse only verified successful work for identical bytes and limits.

        The caller still acquires the current official document. No remote work
        or another owner's processing can satisfy this local checkpoint.
        """
        if len(content) > limits.max_bytes:
            raise ProcessingError('input_limit')
        expected = hashlib.sha256(content).hexdigest()
        version = OCR_VERSION if operation == 'ocr_pdf' else VERSION
        with self._db() as db:
            rows = db.execute('SELECT data FROM processing_jobs WHERE owner=? ORDER BY rowid DESC',
                              (str(owner_id),)).fetchall()
        for row in rows:
            job = json.loads(row[0])
            if (job['state'] != 'succeeded' or job['mode'] != 'local' or job['artifacts_deleted']
                    or job['operation'] != operation or job['input_sha256'] != expected
                    or job['extractor_version'] != version or job['limits'] != asdict(limits)):
                continue
            try:
                data = self.result(job['id'], str(owner_id))
            except ProcessingError as exc:
                if str(exc) == 'artifact_unavailable':
                    continue
                raise
            if data.get('input_sha256') != expected or data.get('extractor_version') != version:
                raise ProcessingError('artifact_hash_mismatch')
            return job, data
        return None

    def result(self, job_id: str, owner_id: str) -> dict:
        with self._db() as db:
            job = self._read(db, job_id, owner_id)
        if job['state'] != 'succeeded' or job['artifacts_deleted']:
            raise ProcessingError('artifact_unavailable')
        path = self._directory(job) / 'output.json'
        if not path.is_file():
            raise ProcessingError('artifact_unavailable')
        output = path.read_bytes()
        if hashlib.sha256(output).hexdigest() != job['output_sha256']:
            raise ProcessingError('artifact_hash_mismatch')
        return json.loads(output)

    def recover_local(self, *, grace_seconds: float = 120) -> int:
        """Reconcile expired fixed local executors, never remote reservations.

        Native commands have enforced deadlines. An additional grace period
        allows termination and result persistence before a stale claim is freed.
        Re-read and update in one transaction so a completed job stays complete.
        """
        if not math.isfinite(grace_seconds) or grace_seconds < 120:
            raise ProcessingError('invalid_recovery_grace')
        recovered = 0
        with self._db() as db:
            for row in db.execute('SELECT data FROM processing_jobs').fetchall():
                job = json.loads(row[0])
                if (job['mode'] != 'local' or job['state'] != 'running'
                        or job['resource'] or job['creation_unknown']
                        or time.time() - job['updated_at'] <= job['limits']['total_seconds'] + grace_seconds):
                    continue
                job.update(state='failed', error={'code':'interrupted'})
                self._save(db, job)
                recovered += 1
        return recovered

    def recover(self, *, older_than_seconds: float = 120, owner_id: str | None = None) -> int:
        """Operator restart sweep. No resource creation or automatic retry.

        Only stale jobs whose entire configured execution window has elapsed.
        Unknown remote creations hold admission until externally reconciled.
        """
        recovered = 0
        with self._db() as db:
            jobs = [json.loads(r[0]) for r in db.execute('SELECT data FROM processing_jobs')]
        for job in jobs:
            if owner_id is not None and job['owner'] != str(owner_id):
                continue
            if job['state'] != 'running' or time.time() - job['updated_at'] <= max(older_than_seconds, job['limits']['total_seconds']):
                continue
            confirmed = False
            if job['resource'] and self.remote:
                try:
                    confirmed = self.remote.status(job['resource']) in ('gone', 'released')
                except Exception:
                    pass
            self._mutate(job['id'], job['owner'], state='failed', error={'code': 'interrupted'},
                         close_confirmed=confirmed)
            recovered += 1
        return recovered

    def reconcile_close(self, job_id: str, owner_id: str, *, request_close: bool = False) -> dict:
        with self._db() as db:
            job = self._read(db, job_id, owner_id)
        if job['resource'] and self.remote and not job['close_confirmed']:
            confirmed = False
            try:
                if request_close:
                    self._mutate(job_id, owner_id, close_requested=True)
                    confirmed = self.remote.close(job['resource'])
                else:
                    confirmed = self.remote.status(job['resource']) in ('gone', 'released')
            except Exception:
                pass
            self._mutate(job_id, owner_id, close_confirmed=bool(confirmed))
        return self.get(job_id, owner_id)

    def retry(self, job_id: str, owner_id: str) -> dict:
        with self._db() as db:
            job = self._read(db, job_id, owner_id)
            if job['state'] != 'failed' or job['attempts'] >= job['limits']['max_attempts']:
                raise ProcessingError('retry_limit')
            # Remote retries deliberately fail closed until creation/cleanup is reconciled.
            if job['mode'] != 'local' or job['creation_unknown']:
                raise ProcessingError('remote_retry_requires_reconciliation')
            job.update(state='queued', error=None, cancel_requested=False)
            self._save(db, job)
        return self.get(job_id, owner_id)

    def cleanup(self, *, retention_seconds: float = 86400) -> int:
        if retention_seconds < 0:
            raise ProcessingError('invalid_retention')
        removed = 0
        with self._db() as db:
            for row in db.execute('SELECT data FROM processing_jobs').fetchall():
                job = json.loads(row[0])
                if (job['state'] not in TERMINAL or job['artifacts_deleted'] or job['creation_unknown'] or
                    (job['resource'] and not job['close_confirmed']) or
                    time.time() - job['updated_at'] < retention_seconds):
                    continue
                for filename in ('input.pdf', 'output.json', 'worker-output.json'):
                    (self._directory(job) / filename).unlink(missing_ok=True)
                job['artifacts_deleted'] = True
                self._save(db, job)
                removed += 1
        return removed


def get_processing_service() -> ProcessingService:
    """Local-only API/service default; env config never opts into billable work."""
    from app.tenderproof.store import artifact_dir
    root = Path(os.environ['TENDERPROOF_PROCESSING_DIR']) if os.getenv('TENDERPROOF_PROCESSING_DIR') else artifact_dir().parent / 'processing'
    return ProcessingService(root, concurrency=int(os.getenv('TENDERPROOF_PROCESSING_CONCURRENCY', '1')))


ID8_SOURCE = "idib_open"
ID8_EXTERNAL_ID = "362"
ID8_SHA256 = "fef17aa38c078810cbfedfa999782c3d02318bd9e5fa764502b5c4bb116ab28a"
ID8_BYTE_LEN = 1_048_994
ID8_PAGE_COUNT = 75


def pinned_page_limit(source: str | None, external_id: str | None, sha256: str | None,
                      byte_len: int | None, default: int = 60) -> int:
    """Return the sole audited exception to the global 60-page limit."""
    if (source, external_id, sha256, byte_len) == (ID8_SOURCE, ID8_EXTERNAL_ID, ID8_SHA256, ID8_BYTE_LEN):
        return ID8_PAGE_COUNT
    return default


def is_pinned_id8(source: str | None, external_id: str | None, sha256: str | None,
                  byte_len: int | None, page_count: int) -> bool:
    return (pinned_page_limit(source, external_id, sha256, byte_len) == ID8_PAGE_COUNT
            and page_count == ID8_PAGE_COUNT)


def extract_pages_isolated(content: bytes, *, artifact_id: str, owner_id: str,
                           max_pages: int = 60, max_bytes: int = 10_000_000,
                           capacity_wait_s: float = 0, operation: str = 'extract_pdf',
                           ocr_timeout_s: float = 120, reuse_completed: bool = False):
    """Drop-in extraction tuple for TenderProofService; exceeds pages fail closed.

    Unlike old partial page truncation this operation rejects oversized PDFs.
    Local process isolation does not imply an OS security sandbox.
    """
    from app.tenderproof.contracts import PageText
    from app.tenderproof.pdf_text import _normalize
    if not 0 <= capacity_wait_s <= 60:
        raise ValueError('espera de capacidade deve estar entre zero e 60 segundos')
    if not math.isfinite(ocr_timeout_s) or not 10 <= ocr_timeout_s <= 600:
        raise ValueError('prazo OCR deve estar entre 10 e 600 segundos')
    service = get_processing_service()
    limits = ProcessingLimits(max_pages=max_pages, max_bytes=max_bytes,
                              total_seconds=float(os.getenv('TENDERPROOF_PROCESSING_TOTAL_SECONDS', '60')),
                              operation_seconds=float(os.getenv('TENDERPROOF_PROCESSING_OPERATION_SECONDS', '30')),
                              max_output_bytes=int(os.getenv('TENDERPROOF_PROCESSING_MAX_OUTPUT_BYTES', '1000000')))
    if operation == 'ocr_pdf':
        limits = ProcessingLimits(max_pages=max_pages, max_bytes=max_bytes,
                                  total_seconds=ocr_timeout_s, operation_seconds=max(1, ocr_timeout_s-10),
                                  max_output_bytes=8_000_000)
    completed = service.completed_local(str(owner_id), content, operation, limits) if reuse_completed else None
    if completed:
        job, data = completed
    else:
        job = service.enqueue(str(owner_id), content, limits=limits, operation=operation)
        deadline = time.monotonic() + capacity_wait_s
        while True:
            try:
                result = service.execute(job['id'], str(owner_id))
                break
            except ProcessingError as exc:
                if str(exc) != 'concurrency_limit':
                    raise
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    # Only cancel this synchronous caller's unstarted job.
                    service.cancel(job['id'], str(owner_id))
                    raise
                time.sleep(min(0.5, remaining))
        if result['state'] != 'succeeded':
            raise ProcessingError((result.get('error') or {}).get('code', 'processing_failed'))
        data = service.result(job['id'], str(owner_id))
    pages = []
    for item in data['pages']:
        text = _normalize(item['text'])
        pages.append(PageText(artifact_id=artifact_id, page_number=item['page_number'], text=text,
                              char_count=len(text), truncated=False, error=None,
                              extraction_method=item.get('method', 'pdf_text'),
                              processing_job_id=job['id'], extractor_version=data['extractor_version'],
                              ocr=({**data.get('ocr', {}), **{k: v for k, v in item.items()
                                   if k not in ('text', 'page_number', 'method')}}
                                   if item.get('method') == 'ocr_tesseract' else None)))
    errors = [] if any(p.text.strip() for p in pages) else ['documento sem texto extraível']
    return pages, data['total_pages'], len(pages), False, errors
