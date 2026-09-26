"""Durable, fenced acquisition queue. This database never writes the catalogue.

SQLite is the source of truth; Redis deliveries are expendable wake-up signals.
Page snapshots and continuation jobs commit in the same transaction. A worker
must present its live fencing token for every checkpoint/result transition.
"""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import sqlite3
import time
from typing import Literal
import uuid
from urllib.parse import parse_qsl, urlsplit

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.tenderproof.contracts import DiscoveredCandidate
from app.tenderproof.store import artifact_dir

from app.tenderproof.source_adapters import SOURCE_ADAPTERS

SOURCES = SOURCE_ADAPTERS.keys()


class SourcePolicy(BaseModel):
    model_config = ConfigDict(extra="forbid")
    enabled: bool = False
    mode: Literal["real", "mock"] = "real"
    interval_s: int = Field(default=3600, ge=60, le=2592000)
    max_listing_pages: int = Field(default=30, ge=1, le=500)
    max_candidates: int = Field(default=100, ge=1, le=2000)
    max_attempts: int = Field(default=3, ge=1, le=5)
    retry_base_s: int = Field(default=30, ge=1, le=3600)
    min_request_gap_s: float = Field(default=2, ge=0, le=300)
    job_timeout_s: int = Field(default=180, ge=10, le=600)
    cycle_timeout_s: int = Field(default=7200, ge=60, le=86400)
    max_download_bytes: int = Field(default=30*1024*1024, ge=1024, le=64*1024*1024)
    max_pdf_pages: int = Field(default=60, ge=1, le=200)
    max_documents: int = Field(default=100, ge=1, le=500)
    allow_browser: bool = False
    max_browser_seconds: int = Field(default=0, ge=0, le=7200)

    @model_validator(mode="after")
    def browser_budget(self):
        if self.allow_browser and self.max_browser_seconds < self.job_timeout_s:
            raise ValueError("browser exige reserva de pelo menos uma janela job_timeout_s")
        return self


class LeaseLost(RuntimeError):
    pass


@dataclass(frozen=True)
class JobLease:
    job_id: str
    cycle_id: str
    owner_user_id: int
    source: str
    kind: str
    payload: dict
    token: str
    fence: int
    attempts: int
    previous_run_id: str | None
    policy: SourcePolicy
    allow_browser: bool
    lease_until: float
    cycle_deadline: float
    recovery_only: bool = False


def _json(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def candidate_key(candidate: DiscoveredCandidate) -> str:
    return candidate.external_id or candidate.detail_url_observed.split("#", 1)[0]


class ContinuousStore:
    def __init__(self, path: Path | str | None = None):
        self.path = Path(path) if path else artifact_dir().parent / "continuous.sqlite3"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._db() as db:
            db.execute("PRAGMA journal_mode=WAL")
            db.executescript("""
                CREATE TABLE IF NOT EXISTS source_config (
                    owner INTEGER NOT NULL, source TEXT NOT NULL, policy TEXT NOT NULL,
                    enabled INTEGER NOT NULL, mode TEXT NOT NULL, next_due REAL NOT NULL,
                    next_request REAL NOT NULL DEFAULT 0, browser_hold TEXT,
                    updated_at REAL NOT NULL, PRIMARY KEY(owner,source));
                CREATE TABLE IF NOT EXISTS cycles (
                    cycle_id TEXT PRIMARY KEY, owner INTEGER NOT NULL, source TEXT NOT NULL,
                    mode TEXT NOT NULL, policy TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'active',
                    created_at REAL NOT NULL, deadline REAL NOT NULL, finished_at REAL,
                    browser_reserved_s REAL NOT NULL DEFAULT 0, reasons TEXT NOT NULL DEFAULT '[]');
                CREATE UNIQUE INDEX IF NOT EXISTS one_active_cycle ON cycles(owner,source) WHERE status='active';
                CREATE TABLE IF NOT EXISTS jobs (
                    job_id TEXT PRIMARY KEY, cycle_id TEXT NOT NULL REFERENCES cycles(cycle_id),
                    kind TEXT NOT NULL, resource_key TEXT NOT NULL, payload TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'queued', attempts INTEGER NOT NULL DEFAULT 0,
                    available_at REAL NOT NULL, lease_until REAL, lease_token TEXT, fence INTEGER NOT NULL DEFAULT 0,
                    run_id TEXT, error TEXT, updated_at REAL NOT NULL,
                    UNIQUE(cycle_id,kind,resource_key));
                CREATE INDEX IF NOT EXISTS ready_jobs ON jobs(status,available_at,lease_until);
                CREATE TABLE IF NOT EXISTS known_candidates (
                    owner INTEGER NOT NULL, source TEXT NOT NULL, mode TEXT NOT NULL,
                    candidate_key TEXT NOT NULL, candidate TEXT NOT NULL, first_seen REAL NOT NULL,
                    last_seen_listing REAL, last_checked REAL, next_check REAL NOT NULL DEFAULT 0,
                    last_run_id TEXT, last_valid_run_id TEXT,
                    PRIMARY KEY(owner,source,mode,candidate_key));
                CREATE TABLE IF NOT EXISTS snapshots (
                    job_id TEXT PRIMARY KEY REFERENCES jobs(job_id), url TEXT NOT NULL,
                    html TEXT NOT NULL, sha256 TEXT NOT NULL, captured_at REAL NOT NULL,
                    metadata TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS observations (
                    observation_id TEXT PRIMARY KEY, owner INTEGER NOT NULL, source TEXT NOT NULL,
                    mode TEXT NOT NULL, candidate_key TEXT NOT NULL, signature TEXT NOT NULL,
                    run_id TEXT NOT NULL, first_seen REAL NOT NULL, last_seen REAL NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending_review', summary TEXT NOT NULL,
                    UNIQUE(owner,source,mode,candidate_key,signature));
                CREATE TABLE IF NOT EXISTS browser_attempts (
                    attempt_id TEXT PRIMARY KEY, job_id TEXT NOT NULL REFERENCES jobs(job_id),
                    fence INTEGER NOT NULL, owner INTEGER NOT NULL, source TEXT NOT NULL,
                    session_id TEXT, state TEXT NOT NULL DEFAULT 'creating',
                    created_at REAL NOT NULL, updated_at REAL NOT NULL);
                CREATE TABLE IF NOT EXISTS document_review_state (
                    owner INTEGER NOT NULL, source TEXT NOT NULL, mode TEXT NOT NULL,
                    candidate_key TEXT NOT NULL, manifest TEXT NOT NULL,
                    pending_documents TEXT NOT NULL DEFAULT '[]', detected_at REAL,
                    PRIMARY KEY(owner,source,mode,candidate_key));
                CREATE TABLE IF NOT EXISTS acquired_document_state (
                    owner INTEGER NOT NULL, source TEXT NOT NULL, mode TEXT NOT NULL,
                    candidate_key TEXT NOT NULL, document_key TEXT NOT NULL,
                    document TEXT NOT NULL, sha256 TEXT NOT NULL, run_id TEXT NOT NULL,
                    updated_at REAL NOT NULL,
                    PRIMARY KEY(owner,source,mode,candidate_key,document_key));
            """)

    @contextmanager
    def _db(self, *, write=False):
        db = sqlite3.connect(str(self.path), timeout=20, isolation_level=None)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys=ON")
        db.execute("PRAGMA busy_timeout=20000")
        db.execute("PRAGMA synchronous=FULL")
        try:
            if write:
                db.execute("BEGIN IMMEDIATE")
            yield db
            if write:
                db.commit()
        except BaseException:
            if write:
                db.rollback()
            raise
        finally:
            db.close()

    def configure(self, owner: int, source: str, policy: SourcePolicy, *, now=None):
        if owner < 1 or source not in SOURCES:
            raise ValueError("owner/fonte contínua inválido")
        if policy.mode == "mock" and source not in ("ibgp_open", "imeso_open"):
            raise ValueError("fonte sem demonstração sintética registrada; use aquisição real")
        now = time.time() if now is None else now
        with self._db(write=True) as db:
            old = db.execute("SELECT mode FROM source_config WHERE owner=? AND source=?", (owner,source)).fetchone()
            if old and old["mode"] != policy.mode and db.execute(
                "SELECT 1 FROM cycles WHERE owner=? AND source=? LIMIT 1", (owner,source)).fetchone():
                raise ValueError("modo vinculado ao histórico; não misture observações sintéticas e reais")
            db.execute("""INSERT INTO source_config(owner,source,policy,enabled,mode,next_due,updated_at)
                VALUES (?,?,?,?,?,?,?) ON CONFLICT(owner,source) DO UPDATE SET policy=excluded.policy,
                enabled=excluded.enabled, mode=excluded.mode, updated_at=excluded.updated_at""",
                (owner,source,policy.model_dump_json(),int(policy.enabled),policy.mode,now,now))
        return self.configuration(owner,source)

    def configuration(self, owner, source):
        with self._db() as db:
            row = db.execute("SELECT * FROM source_config WHERE owner=? AND source=?", (owner,source)).fetchone()
        if not row:
            return None
        value = dict(row)
        value["policy"] = json.loads(value["policy"])
        value["enabled"] = bool(value["enabled"])
        return value

    def configurations(self, owner=None):
        with self._db() as db:
            rows = db.execute("SELECT owner,source FROM source_config" + (" WHERE owner=?" if owner is not None else ""),
                              (owner,) if owner is not None else ()).fetchall()
        return [self.configuration(r["owner"],r["source"]) for r in rows]

    def track(self, owner, source, candidate: DiscoveredCandidate, *, now=None):
        config = self.configuration(owner,source)
        if not config or candidate.source != source:
            raise ValueError("candidato/fonte sem configuração correspondente")
        now = time.time() if now is None else now
        with self._db(write=True) as db:
            self._remember(db, owner,source,config["mode"],candidate,now,listing=False)
        return candidate_key(candidate)

    @staticmethod
    def _remember(db, owner,source,mode,candidate,now,*,listing):
        db.execute("""INSERT INTO known_candidates(owner,source,mode,candidate_key,candidate,first_seen,last_seen_listing)
            VALUES (?,?,?,?,?,?,?) ON CONFLICT(owner,source,mode,candidate_key) DO UPDATE SET
            candidate=excluded.candidate, last_seen_listing=COALESCE(excluded.last_seen_listing,known_candidates.last_seen_listing)""",
            (owner,source,mode,candidate_key(candidate),candidate.model_dump_json(),now,now if listing else None))

    @staticmethod
    def _job(db, cycle, kind, key, payload, now):
        job_id = "tcj-" + uuid.uuid5(uuid.NAMESPACE_URL, f"{cycle}:{kind}:{key}").hex
        db.execute("INSERT OR IGNORE INTO jobs(job_id,cycle_id,kind,resource_key,payload,available_at,updated_at) VALUES(?,?,?,?,?,?,?)",
                   (job_id,cycle,kind,key,_json(payload),now,now))
        return job_id

    @staticmethod
    def _reason(db, cycle, reason):
        row = db.execute("SELECT reasons FROM cycles WHERE cycle_id=?",(cycle,)).fetchone()
        reasons = json.loads(row[0])
        if reason not in reasons:
            reasons.append(reason)
            db.execute("UPDATE cycles SET reasons=? WHERE cycle_id=?",(_json(reasons),cycle))

    def enqueue(self, owner, source, listing_urls, *, force=False, now=None):
        now = time.time() if now is None else now
        with self._db(write=True) as db:
            config = db.execute("SELECT * FROM source_config WHERE owner=? AND source=?",(owner,source)).fetchone()
            if not config or not config["enabled"]:
                raise ValueError("fonte não habilitada para este usuário")
            existing = db.execute("SELECT cycle_id FROM cycles WHERE owner=? AND source=? AND status='active'",(owner,source)).fetchone()
            if existing:
                return existing[0]
            if not force and config["next_due"] > now:
                return None
            policy = SourcePolicy.model_validate_json(config["policy"])
            cycle = "tcc-"+uuid.uuid4().hex
            db.execute("INSERT INTO cycles(cycle_id,owner,source,mode,policy,created_at,deadline) VALUES(?,?,?,?,?,?,?)",
                       (cycle,owner,source,policy.mode,config["policy"],now,now+policy.cycle_timeout_s))
            known = db.execute("""SELECT candidate_key,candidate FROM known_candidates WHERE owner=? AND source=? AND mode=?
                AND next_check<=? ORDER BY COALESCE(last_checked,0),candidate_key LIMIT ?""",
                (owner,source,policy.mode,now,policy.max_candidates+1)).fetchall()
            if len(known) > policy.max_candidates:
                self._reason(db,cycle,"known_candidate_limit")
            for item in known[:policy.max_candidates]:
                self._job(db,cycle,"detail",item["candidate_key"],json.loads(item["candidate"]),now)
            # A cycle deadline is a work bound, not permission to forget a
            # published pagination cursor. Only resume the latest unresolved
            # attempt for this owner/source/mode; retain the old cycle intact.
            deferred = db.execute("""WITH latest AS (
                SELECT j.resource_key,j.status,j.error,j.cycle_id,c.created_at,
                       ROW_NUMBER() OVER (PARTITION BY j.resource_key
                           ORDER BY c.created_at DESC,j.updated_at DESC,j.rowid DESC) AS rank
                FROM jobs j JOIN cycles c USING(cycle_id)
                WHERE c.owner=? AND c.source=? AND c.mode=? AND j.kind='listing')
                SELECT resource_key,cycle_id FROM latest
                WHERE rank=1 AND status='deferred' AND error='cycle_time_limit'
                ORDER BY created_at,resource_key LIMIT ?""",
                (owner,source,policy.mode,policy.max_listing_pages+1)).fetchall()
            continuations={r['resource_key']:r['cycle_id'] for r in deferred}
            # Page budgets can prevent creating a job at all. The published
            # links remain in the immutable snapshot metadata; recover only
            # never-attempted URLs from each parent's most recent snapshot.
            unqueued = db.execute("""WITH latest_pages AS (
                SELECT j.resource_key,s.metadata,c.cycle_id,c.created_at,
                       ROW_NUMBER() OVER (PARTITION BY j.resource_key
                           ORDER BY s.captured_at DESC,c.created_at DESC,j.rowid DESC) AS rank
                FROM snapshots s JOIN jobs j USING(job_id) JOIN cycles c USING(cycle_id)
                WHERE c.owner=? AND c.source=? AND c.mode=? AND j.kind='listing')
                SELECT link.value AS url,MIN(p.cycle_id) AS cycle_id
                FROM latest_pages p,json_each(p.metadata,'$.next_urls') link
                WHERE p.rank=1 AND link.type='text' AND NOT EXISTS (
                    SELECT 1 FROM jobs tried JOIN cycles tc USING(cycle_id)
                    WHERE tc.owner=? AND tc.source=? AND tc.mode=?
                        AND tried.kind='listing' AND tried.resource_key=link.value)
                GROUP BY link.value ORDER BY MIN(p.created_at),link.value LIMIT ?""",
                (owner,source,policy.mode,owner,source,policy.mode,policy.max_listing_pages+1)).fetchall()
            for item in unqueued:
                continuations.setdefault(item['url'],item['cycle_id'])
            # Carry unfinished work first so repeated small windows can move
            # beyond the seed page. Omitted seeds still make coverage partial.
            planned_urls=list(dict.fromkeys([*continuations,*listing_urls]))
            if len(planned_urls)>policy.max_listing_pages:
                self._reason(db,cycle,"listing_page_limit")
            for url in planned_urls[:policy.max_listing_pages]:
                payload={"url":url}
                if url in continuations:
                    payload['continued_from_cycle']=continuations[url]
                self._job(db,cycle,"listing",url,payload,now)
            if not listing_urls:
                raise ValueError("fonte precisa de pelo menos uma listagem registrada")
            db.execute("UPDATE source_config SET next_due=? WHERE owner=? AND source=?",(now+policy.interval_s,owner,source))
            return cycle

    def recollection(self, owner, parent_run_id, *, db=None):
        if db is None:
            with self._db() as connection:
                return self.recollection(owner, parent_run_id, db=connection)
        row = db.execute("""SELECT j.job_id,j.cycle_id,j.status,j.run_id,j.error FROM jobs j
            JOIN cycles c ON c.cycle_id=j.cycle_id
            WHERE c.owner=? AND j.kind='detail' AND j.resource_key=?""",
            (owner, 'refresh:'+parent_run_id)).fetchone()
        return dict(row) if row else None

    def enqueue_recollection(self, owner, parent_run_id, candidate, mode, *, now=None):
        """One durable request per prior run; never reset a completed job."""
        now = time.time() if now is None else now
        with self._db(write=True) as db:
            existing = self.recollection(owner, parent_run_id, db=db)
            if existing:
                return existing
            config = db.execute('SELECT * FROM source_config WHERE owner=? AND source=?',
                                (owner, candidate.source)).fetchone()
            if not config or not config['enabled'] or config['mode'] != mode:
                raise ValueError('habilite a fonte no mesmo modo da coleta anterior')
            active = db.execute("SELECT * FROM cycles WHERE owner=? AND source=? AND status='active'",
                                (owner, candidate.source)).fetchone()
            policy = SourcePolicy.model_validate_json(active['policy'] if active else config['policy'])
            if policy.mode != mode or (active and active['deadline'] <= now):
                raise ValueError('aguarde a finalização do ciclo anterior')
            if active:
                cycle = active['cycle_id']
                count = db.execute("SELECT COUNT(*) FROM jobs WHERE cycle_id=? AND kind='detail'", (cycle,)).fetchone()[0]
                if count >= policy.max_candidates:
                    raise ValueError('limite de candidatos do ciclo atingido; aguarde o próximo ciclo')
            else:
                cycle = 'tcc-'+uuid.uuid4().hex
                db.execute('INSERT INTO cycles(cycle_id,owner,source,mode,policy,created_at,deadline) VALUES(?,?,?,?,?,?,?)',
                           (cycle, owner, candidate.source, mode, config['policy'], now, now+policy.cycle_timeout_s))
                self._reason(db, cycle, 'targeted_recollection_not_full_source_scan')
            payload = candidate.model_dump(mode='json')
            payload['_refresh_parent_run_id'] = parent_run_id
            self._job(db, cycle, 'detail', 'refresh:'+parent_run_id, payload, now)
            # Initial manual acquisitions may not yet be in the recurrent set.
            if not db.execute('SELECT 1 FROM known_candidates WHERE owner=? AND source=? AND mode=? AND candidate_key=?',
                              (owner,candidate.source,mode,candidate_key(candidate))).fetchone():
                self._remember(db,owner,candidate.source,mode,candidate,now,listing=False)
            return self.recollection(owner, parent_run_id, db=db)

    @staticmethod
    def _finish(db,cycle,now):
        if not db.execute("SELECT 1 FROM jobs WHERE cycle_id=? AND status IN ('queued','retry','running','recover')",(cycle,)).fetchone():
            if db.execute("SELECT deadline FROM cycles WHERE cycle_id=?",(cycle,)).fetchone()[0] <= now:
                ContinuousStore._reason(db,cycle,"cycle_time_limit")
            # Graph exhaustion caused by duplicate links is not end-of-list
            # evidence. Every visited route must reach an explicit terminal
            # within its own pagination family; another tab cannot prove it.
            rows=db.execute("""SELECT s.url,s.metadata FROM snapshots s JOIN jobs j USING(job_id)
                WHERE j.cycle_id=? AND j.kind='listing' AND j.status='succeeded'""",(cycle,)).fetchall()
            pages={r["url"]:json.loads(r["metadata"]) for r in rows}
            def family(url):
                parsed=urlsplit(url)
                query=tuple(sorted((key,value) for key,value in parse_qsl(parsed.query)
                                   if key not in ("page","pagina","p","offset")))
                return parsed.netloc,parsed.path,query
            def reaches_terminal(url,seen):
                if url in seen or url not in pages:
                    return False
                seen.add(url)
                page=pages[url]
                if page.get("terminal_evidence") or page.get("empty_evidence"):
                    return True
                return any(reaches_terminal(target,seen) for target in page.get("next_urls",[])
                           if family(target)==family(url))
            if any(not reaches_terminal(url,set()) for url in pages):
                ContinuousStore._reason(db,cycle,"listing_exhaustiveness_unproven")
            row = db.execute("SELECT reasons FROM cycles WHERE cycle_id=?",(cycle,)).fetchone()
            failed = db.execute("SELECT 1 FROM jobs WHERE cycle_id=? AND status IN ('failed','deferred')",(cycle,)).fetchone()
            db.execute("UPDATE cycles SET status=?,finished_at=? WHERE cycle_id=? AND status='active'",
                       ("partial" if failed or json.loads(row[0]) else "completed",now,cycle))

    def _maintain(self,db,now):
        for cycle in db.execute("SELECT * FROM cycles WHERE status='active'").fetchall():
            policy = SourcePolicy.model_validate_json(cycle["policy"])
            db.execute("""UPDATE jobs SET status='recover',error='worker_lease_expired_finalize_only',updated_at=?
                WHERE cycle_id=? AND status='running' AND lease_until<=? AND (attempts>=? OR ?<=?)""",
                (now,cycle["cycle_id"],now,policy.max_attempts,cycle["deadline"],now))
            if cycle["deadline"] <= now:
                self._reason(db,cycle["cycle_id"],"cycle_time_limit")
                db.execute("""UPDATE jobs SET status='deferred',error='cycle_time_limit',updated_at=?
                    WHERE cycle_id=? AND (status IN ('queued','retry') OR (status='running' AND lease_until<=?))""",
                    (now,cycle["cycle_id"],now))
            self._finish(db,cycle["cycle_id"],now)

    def ready_jobs(self, *, limit=100, now=None):
        now = time.time() if now is None else now
        with self._db(write=True) as db:
            self._maintain(db,now)
            # Compute source service times once, rather than rescanning the
            # entire job history for each queued document in large catalogues.
            rows = db.execute("""WITH last_served AS (
                SELECT sc.owner,sc.source,MAX(served.updated_at) AS served_at
                FROM jobs served JOIN cycles sc USING(cycle_id)
                WHERE served.attempts>0 AND served.error IS NOT 'acquisition_busy'
                GROUP BY sc.owner,sc.source)
                SELECT j.job_id,c.owner,c.source FROM jobs j JOIN cycles c USING(cycle_id)
                JOIN source_config s ON s.owner=c.owner AND s.source=c.source
                LEFT JOIN last_served ls ON ls.owner=c.owner AND ls.source=c.source
                WHERE c.status='active' AND (c.deadline>? OR j.status='recover') AND s.enabled=1 AND s.next_request<=?
                AND ((j.status IN ('queued','retry','recover') AND j.available_at<=?) OR (j.status='running' AND j.lease_until<=?))
                AND NOT EXISTS (SELECT 1 FROM jobs running JOIN cycles rc USING(cycle_id)
                    WHERE rc.owner=c.owner AND rc.source=c.source AND running.status='running' AND running.lease_until>?)
                ORDER BY
                    COALESCE(ls.served_at,0),
                    CASE WHEN j.status='recover' THEN 0 WHEN j.kind='listing' THEN 1
                         WHEN j.resource_key LIKE 'refresh:%' THEN 2 ELSE 3 END,
                    j.available_at,j.job_id""",(now,now,now,now,now)).fetchall()
            seen,found=set(),[]
            for row in rows:
                scope=(row["owner"],row["source"])
                if scope not in seen:
                    found.append(row["job_id"])
                    seen.add(scope)
                if len(found)>=limit:
                    break
            return found

    def claim(self, job_id: str, *, now=None):
        now = time.time() if now is None else now
        with self._db(write=True) as db:
            self._maintain(db,now)
            row=db.execute("""SELECT j.*,c.owner,c.source,c.policy,c.deadline,c.browser_reserved_s,
                s.browser_hold,s.policy AS current_policy FROM jobs j JOIN cycles c USING(cycle_id)
                JOIN source_config s ON s.owner=c.owner AND s.source=c.source
                WHERE j.job_id=? AND c.status='active' AND s.enabled=1 AND s.next_request<=?
                AND ((j.status IN ('queued','retry','recover') AND j.available_at<=?) OR (j.status='running' AND j.lease_until<=?))""",
                (job_id,now,now,now)).fetchone()
            if not row or (row["deadline"]<=now and row["status"]!='recover'):
                return None
            if db.execute("""SELECT 1 FROM jobs j JOIN cycles c USING(cycle_id) WHERE c.owner=? AND c.source=?
                AND j.status='running' AND j.lease_until>?""",(row["owner"],row["source"],now)).fetchone():
                return None
            policy=SourcePolicy.model_validate_json(row["policy"])
            current=SourcePolicy.model_validate_json(row["current_policy"])
            token=uuid.uuid4().hex
            fence=row["fence"]+1
            until=now+policy.job_timeout_s+120
            recovery_only=row["status"]=='recover'
            browser=bool(not recovery_only and policy.allow_browser and current.allow_browser and not row["browser_hold"] and
                         row["browser_reserved_s"]+policy.job_timeout_s<=min(policy.max_browser_seconds,current.max_browser_seconds))
            if browser:
                db.execute("UPDATE cycles SET browser_reserved_s=browser_reserved_s+? WHERE cycle_id=?",(policy.job_timeout_s,row["cycle_id"]))
            attempts=row["attempts"]+(0 if recovery_only else 1)
            db.execute("UPDATE jobs SET status='running',attempts=?,lease_token=?,fence=?,lease_until=?,updated_at=? WHERE job_id=?",
                       (attempts,token,fence,until,now,job_id))
            db.execute("UPDATE source_config SET next_request=? WHERE owner=? AND source=?",(now+policy.min_request_gap_s,row["owner"],row["source"]))
            return JobLease(job_id,row["cycle_id"],row["owner"],row["source"],row["kind"],json.loads(row["payload"]),token,
                            fence,attempts,row["run_id"],policy,browser,until,row["deadline"],recovery_only)

    def owner_for_job(self,job_id):
        with self._db() as db:
            row=db.execute("SELECT c.owner FROM jobs j JOIN cycles c USING(cycle_id) WHERE j.job_id=?",(job_id,)).fetchone()
        return row[0] if row else None

    @staticmethod
    def _check(db,lease,now):
        row=db.execute("SELECT * FROM jobs WHERE job_id=? AND status='running' AND lease_token=? AND fence=? AND lease_until>?",
                       (lease.job_id,lease.token,lease.fence,now)).fetchone()
        if not row:
            raise LeaseLost("lease vencido ou substituído; checkpoint recusado")
        return row

    def check_lease(self,lease,*,now=None):
        with self._db() as db:
            self._check(db,lease,time.time() if now is None else now)

    def renew(self,lease,*,now=None):
        now=time.time() if now is None else now
        with self._db(write=True) as db:
            self._check(db,lease,now)
            # A heartbeat cannot keep a hung job alive beyond its original cap.
            db.execute("UPDATE jobs SET lease_until=? WHERE job_id=?",(min(lease.lease_until,now+lease.policy.job_timeout_s+120),lease.job_id))

    @staticmethod
    def _snapshot(db,lease,url,html,metadata,now):
        content=html.encode("utf-8")
        if len(content)>2*1024*1024:
            raise ValueError("snapshot excede 2 MiB")
        db.execute("""INSERT INTO snapshots(job_id,url,html,sha256,captured_at,metadata) VALUES(?,?,?,?,?,?)
            ON CONFLICT(job_id) DO UPDATE SET url=excluded.url,html=excluded.html,sha256=excluded.sha256,
            captured_at=excluded.captured_at,metadata=excluded.metadata""",
            (lease.job_id,url,html,hashlib.sha256(content).hexdigest(),now,_json(metadata)))

    def complete_listing(self,lease,html,page,*,now=None):
        now=time.time() if now is None else now
        with self._db(write=True) as db:
            self._check(db,lease,now)
            self._snapshot(db,lease,lease.payload["url"],html,{
                "next_urls":page.next_urls,"empty_evidence":page.empty_evidence,"terminal_evidence":page.terminal_evidence,
                "truncated":page.truncated,"diagnostics":page.diagnostics,"candidate_count":len(page.candidates),
                "sessions":getattr(page,"sessions",[])},now)
            if page.truncated:
                self._reason(db,lease.cycle_id,"listing_candidates_truncated")
            for candidate in page.candidates:
                self._remember(db,lease.owner_user_id,lease.source,lease.policy.mode,candidate,now,listing=True)
                key=candidate_key(candidate)
                if db.execute("SELECT 1 FROM jobs WHERE cycle_id=? AND kind='detail' AND resource_key=?",(lease.cycle_id,key)).fetchone():
                    continue
                count=db.execute("SELECT COUNT(*) FROM jobs WHERE cycle_id=? AND kind='detail'",(lease.cycle_id,)).fetchone()[0]
                if count>=lease.policy.max_candidates:
                    self._reason(db,lease.cycle_id,"candidate_limit")
                    continue
                self._job(db,lease.cycle_id,"detail",key,candidate.model_dump(mode="json"),now)
            for url in page.next_urls:
                if db.execute("SELECT 1 FROM jobs WHERE cycle_id=? AND kind='listing' AND resource_key=?",(lease.cycle_id,url)).fetchone():
                    continue
                count=db.execute("SELECT COUNT(*) FROM jobs WHERE cycle_id=? AND kind='listing'",(lease.cycle_id,)).fetchone()[0]
                if count>=lease.policy.max_listing_pages:
                    self._reason(db,lease.cycle_id,"listing_page_limit")
                    continue
                self._job(db,lease.cycle_id,"listing",url,{"url":url},now)
            db.execute("UPDATE jobs SET status='succeeded',error=NULL,updated_at=? WHERE job_id=?",(now,lease.job_id))
            self._finish(db,lease.cycle_id,now)

    def listing_checkpoint(self,lease,html,*,now=None):
        now=time.time() if now is None else now
        with self._db(write=True) as db:
            self._check(db,lease,now)
            self._snapshot(db,lease,lease.payload["url"],html,{"parsed":False},now)

    def detail_checkpoint(self,lease,html,manifest,*,truncated=False,now=None):
        now=time.time() if now is None else now
        with self._db(write=True) as db:
            self._check(db,lease,now)
            self._document_checkpoint(db, lease, manifest, now)
            self._snapshot(db,lease,lease.payload["detail_url_observed"],html,{"documents":manifest,"documents_truncated":truncated},now)
            if truncated:
                self._reason(db,lease.cycle_id,"document_list_truncated")

    @staticmethod
    def _document_identity(doc):
        from app.tenderproof.document_identity import document_identity
        return document_identity(doc)

    def _document_checkpoint(self, db, lease, manifest, now):
        key = candidate_key(DiscoveredCandidate.model_validate(lease.payload))
        identity = (lease.owner_user_id, lease.source, lease.policy.mode, key)
        row = db.execute('SELECT * FROM document_review_state WHERE owner=? AND source=? AND mode=? AND candidate_key=?', identity).fetchone()
        previous = json.loads(row['manifest']) if row else None
        pending = json.loads(row['pending_documents']) if row else []
        if previous is None:
            retained = {self._document_identity(doc) for doc in pending}
            for doc in manifest:
                if doc.get('kind') in ('consolidado', 'retificacao', 'prorrogacao') and self._document_identity(doc) not in retained:
                    pending.append(doc)
                    retained.add(self._document_identity(doc))
        if previous is None:
            # Upgrade existing volumes using their last recorded manifest.
            old = db.execute('SELECT summary FROM observations WHERE owner=? AND source=? AND mode=? AND candidate_key=? ORDER BY last_seen DESC LIMIT 1', identity).fetchone()
            previous = json.loads(old['summary']).get('documents') if old else None
        if previous is not None:
            known = {self._document_identity(doc) for doc in previous}
            retained = {self._document_identity(doc) for doc in pending}
            for doc in manifest:
                doc_key = self._document_identity(doc)
                if doc_key not in known and doc_key not in retained:
                    pending.append(doc)
                    retained.add(doc_key)
        detected = row['detected_at'] if row else None
        if pending and detected is None:
            detected = now
        db.execute('INSERT INTO document_review_state VALUES(?,?,?,?,?,?,?) ON CONFLICT(owner,source,mode,candidate_key) DO UPDATE SET manifest=excluded.manifest,pending_documents=excluded.pending_documents,detected_at=excluded.detected_at',
            (*identity, _json(manifest), _json(pending), detected))

    def document_review(self, owner, source, mode, key, *, db=None):
        if db is None:
            with self._db() as connection:
                return self.document_review(owner, source, mode, key, db=connection)
        row = db.execute('SELECT pending_documents,detected_at FROM document_review_state WHERE owner=? AND source=? AND mode=? AND candidate_key=?', (owner,source,mode,key)).fetchone()
        documents = json.loads(row['pending_documents']) if row else []
        return {'pending': bool(documents), 'documents': documents,
            'reason': 'Documentos novos ou alterados foram observados. Seus efeitos precisam de revisão; os valores do catálogo permanecem preservados.' if documents else '',
            'detected_at': row['detected_at'] if row else None}

    def review_for_run(self, run, *, db=None):
        if db is None:
            with self._db() as connection:
                return self.review_for_run(run, db=connection)
        candidate = next((c for c in run.candidates if c.candidate_id == run.selected_candidate_id), None)
        result = self.document_review(run.owner_user_id, run.source, run.mode, candidate_key(candidate), db=db) if candidate else {'pending':False,'documents':[],'reason':'','detected_at':None}
        if candidate and not result['pending']:
            from app.tenderproof.review_cases import outdated_approval
            outdated = outdated_approval(run, db)
            if outdated:
                return {**result, 'pending':True, 'documents':outdated['revision']['manifest'],
                    'reason':'A interpretação dos campos foi atualizada. Prepare e confira novamente os efeitos dos documentos.'}
        return result

    @staticmethod
    def _selected_document(summary):
        if summary.get('selected_document'):
            return summary['selected_document']
        # Historical summaries stored only the manifest. Infer its association
        # only when exactly one principal exists; never pick among several.
        originals = [d for d in summary.get('documents', []) if d.get('kind') == 'edital']
        return originals[0] if len(originals) == 1 else None

    def _acquired_document_checkpoint(self, db, lease, run_id, summary, now):
        self._acquired_single_document_checkpoint(db, lease, run_id, summary, now)
        for extra in summary.get('supplementary_documents', []):
            self._acquired_single_document_checkpoint(db, lease, run_id,
                {**summary, 'selected_document': extra['document'],
                 'artifact_sha256': extra['artifact_sha256']}, now)

    def _acquired_single_document_checkpoint(self, db, lease, run_id, summary, now):
        document = self._selected_document(summary)
        digest = summary.get('artifact_sha256')
        if not document or not isinstance(digest, str) or len(digest) != 64 or any(c not in '0123456789abcdef' for c in digest):
            return
        identity = (lease.owner_user_id, lease.source, lease.policy.mode, candidate_key(DiscoveredCandidate.model_validate(lease.payload)))
        document_key = _json(self._document_identity(document)[:4])
        old = db.execute('SELECT sha256,run_id FROM acquired_document_state WHERE owner=? AND source=? AND mode=? AND candidate_key=? AND document_key=?', (*identity,document_key)).fetchone()
        if old is None:
            history = db.execute('SELECT summary,run_id FROM observations WHERE owner=? AND source=? AND mode=? AND candidate_key=? ORDER BY first_seen DESC',identity).fetchall()
            for item in history:
                previous = json.loads(item['summary'])
                selected = self._selected_document(previous)
                if selected and previous.get('artifact_sha256') and _json(self._document_identity(selected)[:4]) == document_key:
                    old = {'sha256':previous['artifact_sha256'],'run_id':item['run_id']}
                    break
        if old and old['sha256'] != digest:
            state = db.execute('SELECT pending_documents,detected_at FROM document_review_state WHERE owner=? AND source=? AND mode=? AND candidate_key=?', identity).fetchone()
            pending = json.loads(state['pending_documents']) if state else []
            changed = dict(document, change='bytes_changed', previous_sha256=old['sha256'], sha256=digest,
                           previous_run_id=old['run_id'], run_id=run_id)
            if not any(d.get('change') == 'bytes_changed' and d.get('previous_sha256') == old['sha256'] and d.get('sha256') == digest
                       and _json(self._document_identity(d)[:4]) == document_key for d in pending):
                pending.append(changed)
            detected = state['detected_at'] if state and state['detected_at'] is not None else now
            db.execute('INSERT INTO document_review_state VALUES(?,?,?,?,?,?,?) ON CONFLICT(owner,source,mode,candidate_key) DO UPDATE SET pending_documents=excluded.pending_documents,detected_at=excluded.detected_at',
                       (*identity,_json(summary.get('documents',[])),_json(pending),detected))
        db.execute('INSERT INTO acquired_document_state VALUES(?,?,?,?,?,?,?,?,?) ON CONFLICT(owner,source,mode,candidate_key,document_key) DO UPDATE SET document=excluded.document,sha256=excluded.sha256,run_id=excluded.run_id,updated_at=excluded.updated_at',
                   (*identity,document_key,_json(document),digest,run_id,now))

    def acquired_document_checkpoint(self, lease, run_id, summary, *, now=None):
        """Preserved bytes can change even when subsequent PDF processing fails."""
        now=time.time() if now is None else now
        with self._db(write=True) as db:
            self._check(db,lease,now)
            self._acquired_document_checkpoint(db,lease,run_id,summary,now)

    def set_run_id(self,lease,run_id,*,now=None):
        now=time.time() if now is None else now
        with self._db(write=True) as db:
            self._check(db,lease,now)
            db.execute("UPDATE jobs SET run_id=? WHERE job_id=?",(run_id,lease.job_id))

    def document_signature_history(self,lease,signature,digest):
        """Read candidate-scoped legacy evidence in batches; never rewrite it."""
        identity=(lease.owner_user_id,lease.source,lease.policy.mode,candidate_key(DiscoveredCandidate.model_validate(lease.payload)))
        with self._db() as db:
            if db.execute('SELECT 1 FROM observations WHERE owner=? AND source=? AND mode=? AND candidate_key=? AND signature=?',(*identity,signature)).fetchone():
                return
        offset=0
        while True:
            with self._db() as db:
                rows=db.execute('SELECT observation_id,signature,run_id,summary FROM observations WHERE owner=? AND source=? AND mode=? AND candidate_key=? ORDER BY first_seen,observation_id LIMIT 100 OFFSET ?',(*identity,offset)).fetchall()
            if not rows:
                return
            for row in rows:
                result=dict(row)
                result['summary']=json.loads(result['summary'])
                if result['summary'].get('artifact_sha256')==digest:
                    yield result
            offset+=len(rows)

    def record_document_signature_match(self,lease,previous,normalized_signature,*,now=None):
        """Audit the comparison in this acquisition snapshot, not the old row."""
        now=time.time() if now is None else now
        with self._db(write=True) as db:
            self._check(db,lease,now)
            row=db.execute('SELECT metadata FROM snapshots WHERE job_id=?',(lease.job_id,)).fetchone()
            if row is None:
                raise ValueError('checkpoint documental ausente para auditoria de identidade')
            metadata=json.loads(row['metadata'])
            metadata['document_signature_match']={'rule':'normalized_ephemeral_url_same_sha256',
                'observation_id':previous['observation_id'],'preserved_signature':previous['signature'],
                'normalized_signature':normalized_signature,'previous_run_id':previous['run_id']}
            db.execute('UPDATE snapshots SET metadata=? WHERE job_id=?',(_json(metadata),lease.job_id))

    def complete_detail(self,lease,run_id,signature,summary,*,now=None):
        now=time.time() if now is None else now
        key=candidate_key(DiscoveredCandidate.model_validate(lease.payload))
        identity=f"{lease.owner_user_id}:{lease.source}:{lease.policy.mode}:{key}:{signature}"
        observation="tco-"+hashlib.sha256(identity.encode()).hexdigest()
        with self._db(write=True) as db:
            self._check(db,lease,now)
            self._acquired_document_checkpoint(db, lease, run_id, summary, now)
            summary = dict(summary, document_review=self.document_review(lease.owner_user_id, lease.source, lease.policy.mode, key, db=db))
            db.execute("""INSERT INTO observations(observation_id,owner,source,mode,candidate_key,signature,run_id,first_seen,last_seen,summary)
                VALUES(?,?,?,?,?,?,?,?,?,?) ON CONFLICT(owner,source,mode,candidate_key,signature) DO UPDATE SET last_seen=excluded.last_seen""",
                (observation,lease.owner_user_id,lease.source,lease.policy.mode,key,signature,run_id,now,now,_json(summary)))
            db.execute("""UPDATE known_candidates SET last_checked=?,next_check=?,last_run_id=?,
                last_valid_run_id=CASE WHEN ? THEN ? ELSE last_valid_run_id END
                WHERE owner=? AND source=? AND mode=? AND candidate_key=?""",
                (now,now+lease.policy.interval_s,run_id,summary.get("validation_status")=="valid",run_id,
                 lease.owner_user_id,lease.source,lease.policy.mode,key))
            db.execute("UPDATE jobs SET status='succeeded',run_id=?,error=NULL,updated_at=? WHERE job_id=?",(run_id,now,lease.job_id))
            self._finish(db,lease.cycle_id,now)
        return observation

    def fail(self,lease,error,*,retryable=True,now=None):
        now=time.time() if now is None else now
        with self._db(write=True) as db:
            self._check(db,lease,now)
            retry=retryable and lease.attempts<lease.policy.max_attempts
            delay=min(3600,lease.policy.retry_base_s*2**(lease.attempts-1))
            db.execute("UPDATE jobs SET status=?,error=?,available_at=?,updated_at=? WHERE job_id=?",
                       ("retry" if retry else "failed",error[:500],now+delay,now,lease.job_id))
            if not retry:
                self._reason(db,lease.cycle_id,f"{lease.kind}_failed:{error[:120]}")
                if lease.kind=="detail":
                    key=candidate_key(DiscoveredCandidate.model_validate(lease.payload))
                    snapshot=db.execute("SELECT metadata FROM snapshots WHERE job_id=?",(lease.job_id,)).fetchone()
                    run=db.execute("SELECT run_id FROM jobs WHERE job_id=?",(lease.job_id,)).fetchone()
                    metadata=json.loads(snapshot["metadata"]) if snapshot else {}
                    if metadata.get("documents") and run["run_id"]:
                        # A failed principal-document selection must still expose
                        # the observed manifest for review. It proves links only,
                        # never document bytes or effects on canonical fields.
                        summary={"title":lease.payload.get("title_observed"),
                            "validation_status":"document_review_required",
                            "documents":sorted(metadata["documents"],key=lambda d:(d["url"],d["title"])),
                            "documents_truncated":metadata.get("documents_truncated",False),
                            "is_synthetic_sample":lease.policy.mode=="mock",
                            "review_reason":"Documentos observados; aquisição do edital principal não concluída. Revisar vínculos e conteúdo antes de publicar.",
                            "document_bytes_verified":False}
                        signature=hashlib.sha256(_json(summary).encode()).hexdigest()
                        identity=f"{lease.owner_user_id}:{lease.source}:{lease.policy.mode}:{key}:{signature}"
                        observation="tco-"+hashlib.sha256(identity.encode()).hexdigest()
                        db.execute("""INSERT INTO observations(observation_id,owner,source,mode,candidate_key,signature,run_id,first_seen,last_seen,summary)
                            VALUES(?,?,?,?,?,?,?,?,?,?) ON CONFLICT(owner,source,mode,candidate_key,signature) DO UPDATE SET last_seen=excluded.last_seen""",
                            (observation,lease.owner_user_id,lease.source,lease.policy.mode,key,signature,run["run_id"],now,now,_json(summary)))
                    db.execute("UPDATE known_candidates SET last_checked=?,next_check=? WHERE owner=? AND source=? AND mode=? AND candidate_key=?",
                               (now,now+lease.policy.interval_s,lease.owner_user_id,lease.source,lease.policy.mode,key))
            self._finish(db,lease.cycle_id,now)

    def defer_busy(self,lease,*,now=None):
        """Internal contention is not a failed source attempt or paid launch."""
        now=time.time() if now is None else now
        with self._db(write=True) as db:
            self._check(db,lease,now)
            launched=db.execute("SELECT 1 FROM browser_attempts WHERE job_id=? AND fence=?",(lease.job_id,lease.fence)).fetchone()
            if launched:
                raise ValueError("uma tentativa com intenção de browser não pode devolver sua reserva")
            db.execute("UPDATE jobs SET status='retry',attempts=MAX(0,attempts-1),error='acquisition_busy',available_at=?,updated_at=? WHERE job_id=?",
                       (now+lease.policy.retry_base_s,now,lease.job_id))
            if lease.allow_browser:
                db.execute("UPDATE cycles SET browser_reserved_s=MAX(0,browser_reserved_s-?) WHERE cycle_id=?",(lease.policy.job_timeout_s,lease.cycle_id))

    def finalize_pending(self,lease,*,now=None):
        now=time.time() if now is None else now
        with self._db(write=True) as db:
            self._check(db,lease,now)
            db.execute("UPDATE jobs SET status='recover',error='checkpoint_commit_pending',available_at=?,updated_at=? WHERE job_id=?",
                       (now+lease.policy.retry_base_s,now,lease.job_id))

    def browser_creating(self,lease,*,now=None):
        """Commit intent before calling a paid provider, including no-ID crashes."""
        now=time.time() if now is None else now
        attempt="tcb-"+uuid.uuid4().hex
        with self._db(write=True) as db:
            self._check(db,lease,now)
            config=db.execute("SELECT enabled,policy,browser_hold FROM source_config WHERE owner=? AND source=?",(lease.owner_user_id,lease.source)).fetchone()
            if not lease.allow_browser or not config["enabled"] or not SourcePolicy.model_validate_json(config["policy"]).allow_browser or config["browser_hold"]:
                raise ValueError("nova criação de browser suspensa")
            db.execute("INSERT INTO browser_attempts(attempt_id,job_id,fence,owner,source,created_at,updated_at) VALUES(?,?,?,?,?,?,?)",
                       (attempt,lease.job_id,lease.fence,lease.owner_user_id,lease.source,now,now))
            db.execute("UPDATE source_config SET browser_hold='journal' WHERE owner=? AND source=?",(lease.owner_user_id,lease.source))
        return attempt

    def browser_created(self,attempt,session_id,*,now=None):
        if not isinstance(session_id,str) or not session_id or len(session_id)>256:
            raise ValueError("ID de sessão inválido")
        now=time.time() if now is None else now
        with self._db(write=True) as db:
            # Late provider acknowledgment must remain recordable after lease
            # expiry; it does not grant permission to commit a stale job result.
            changed=db.execute("UPDATE browser_attempts SET session_id=?,state='active',updated_at=? WHERE attempt_id=? AND state='creating'",
                               (session_id,now,attempt)).rowcount
            if changed!=1:
                raise ValueError("intenção de sessão não encontrada")

    def browser_closed(self,attempt,session_id,*,now=None):
        now=time.time() if now is None else now
        with self._db(write=True) as db:
            row=db.execute("SELECT * FROM browser_attempts WHERE attempt_id=? AND session_id=?",(attempt,session_id)).fetchone()
            if not row:
                raise ValueError("encerramento sem sessão correspondente")
            db.execute("UPDATE browser_attempts SET state='closed',updated_at=? WHERE attempt_id=?",(now,attempt))
            pending=db.execute("SELECT 1 FROM browser_attempts WHERE owner=? AND source=? AND state!='closed'",(row["owner"],row["source"])).fetchone()
            if not pending:
                db.execute("UPDATE source_config SET browser_hold=NULL WHERE owner=? AND source=? AND browser_hold='journal'",(row["owner"],row["source"]))

    def open_browser_attempts(self,owner,source):
        with self._db() as db:
            rows=db.execute("""SELECT b.*,j.run_id,j.status AS job_status,j.lease_until FROM browser_attempts b
                JOIN jobs j USING(job_id) WHERE b.owner=? AND b.source=? AND b.state!='closed' ORDER BY b.created_at""",(owner,source)).fetchall()
        return [dict(row) for row in rows]

    def hold_browser(self,owner,source,reason):
        with self._db(write=True) as db:
            pending=db.execute("SELECT 1 FROM browser_attempts WHERE owner=? AND source=? AND state!='closed'",(owner,source)).fetchone()
            db.execute("UPDATE source_config SET browser_hold=? WHERE owner=? AND source=?",("journal" if pending else reason[:500],owner,source))

    def clear_browser_hold(self,owner,source,expected):
        with self._db(write=True) as db:
            db.execute("UPDATE source_config SET browser_hold=NULL WHERE owner=? AND source=? AND browser_hold=?",(owner,source,expected))

    def snapshot(self,job_id,owner):
        with self._db() as db:
            row=db.execute("SELECT s.* FROM snapshots s JOIN jobs j USING(job_id) JOIN cycles c USING(cycle_id) WHERE s.job_id=? AND c.owner=?",
                           (job_id,owner)).fetchone()
        if not row:
            return None
        result=dict(row)
        result["metadata"]=json.loads(result["metadata"])
        return result

    def cycle(self,cycle_id,owner):
        with self._db() as db:
            row=db.execute("SELECT * FROM cycles WHERE cycle_id=? AND owner=?",(cycle_id,owner)).fetchone()
            if not row:
                return None
            result=dict(row)
            result["policy"]=json.loads(result["policy"])
            result["reasons"]=json.loads(result["reasons"])
            result["jobs"]=[dict(j) for j in db.execute("SELECT job_id,kind,status,attempts,available_at,lease_until,fence,run_id,error,updated_at FROM jobs WHERE cycle_id=? ORDER BY rowid",(cycle_id,))]
            return result

    def status(self,owner):
        configs=self.configurations(owner)
        with self._db() as db:
            for config in configs:
                source=config["source"]
                config["known_candidates"]=db.execute("SELECT COUNT(*) FROM known_candidates WHERE owner=? AND source=?",(owner,source)).fetchone()[0]
                config["pending_reviews"]=db.execute("SELECT COUNT(*) FROM observations WHERE owner=? AND source=? AND status='pending_review'",(owner,source)).fetchone()[0]
                rows=db.execute("SELECT cycle_id,status,created_at,finished_at,reasons,browser_reserved_s FROM cycles WHERE owner=? AND source=? ORDER BY created_at DESC LIMIT 10",(owner,source)).fetchall()
                config["cycles"]=[{**dict(r),"reasons":json.loads(r["reasons"])} for r in rows]
        return configs

    def observations(self,owner,*,source=None,limit=100,offset=0):
        with self._db() as db:
            rows=db.execute("SELECT * FROM observations WHERE owner=?"+(" AND source=?" if source else "")+
                " ORDER BY first_seen DESC,observation_id LIMIT ? OFFSET ?",(owner,*([source] if source else []),limit,offset)).fetchall()
        return [{**dict(r),"summary":dict(json.loads(r["summary"]), document_review=self.document_review(
            owner, r['source'], r['mode'], r['candidate_key']))} for r in rows]

    def catalogue_review(self, owner, source, *, external_id=None, link=None, title=None):
        """Read queue review evidence for a catalogue item; never mutates data."""
        with self._db() as db:
            rows = db.execute("SELECT * FROM known_candidates WHERE owner=? AND source=?", (owner, source)).fetchall()
            match = None
            for row in rows:
                candidate = json.loads(row['candidate'])
                if (row['mode'] == 'real' and external_id and link
                        and str(candidate.get('external_id') or '') == str(external_id)
                        and candidate.get('detail_url_observed') == link):
                    match = row
                    break
            if match is None:
                return {'pending': False, 'documents': [], 'reason': '', 'evidence': 'none'}
            review = self.document_review(owner, match['source'], match['mode'], match['candidate_key'], db=db)
            return {**review, 'evidence': 'document_review' if review['pending'] else 'known_candidate',
                    'candidate_key': match['candidate_key'], 'last_run_id': match['last_run_id']}

    def metrics(self, owner, *, now=None):
        """Measured owner-scoped counters; never infer document or source quality."""
        now = time.time() if now is None else now
        with self._db() as db:
            jobs = db.execute("""SELECT j.status, COUNT(*) AS count,
                SUM(MAX(j.attempts-1,0)) AS retries
                FROM jobs j JOIN cycles c USING(cycle_id) WHERE c.owner=? GROUP BY j.status""", (owner,)).fetchall()
            oldest = db.execute("""SELECT MIN(j.available_at) FROM jobs j JOIN cycles c USING(cycle_id)
                WHERE c.owner=? AND j.status IN ('queued','retry') AND j.available_at<=?""", (owner,now)).fetchone()[0]
            durations = db.execute("""SELECT source, COUNT(*) AS cycles,
                AVG(finished_at-created_at) AS mean_seconds, MAX(finished_at-created_at) AS max_seconds
                FROM cycles WHERE owner=? AND finished_at IS NOT NULL GROUP BY source""", (owner,)).fetchall()
            snapshots = db.execute("""SELECT COUNT(*), COALESCE(SUM(LENGTH(CAST(s.html AS BLOB))),0)
                FROM snapshots s JOIN jobs j USING(job_id) JOIN cycles c USING(cycle_id) WHERE c.owner=?""", (owner,)).fetchone()
            pending = db.execute("SELECT COUNT(*) FROM browser_attempts WHERE owner=? AND state!='closed'", (owner,)).fetchone()[0]
        return {"measured_at": now, "jobs_by_status": {r["status"]:r["count"] for r in jobs},
                "retry_attempts": sum(r["retries"] or 0 for r in jobs),
                "oldest_ready_delay_seconds": max(0, now-oldest) if oldest is not None else 0,
                "completed_cycles_by_source": [dict(r) for r in durations],
                "snapshot_pages": snapshots[0], "snapshot_html_bytes": snapshots[1],
                "unconfirmed_browser_attempts": pending,
                "scope": "owner_history; cycle duration includes queue delay; retries are attempts after the first"}


def get_continuous_store():
    # Path-scoped connections; no cached state leaks across workers or tests.
    return ContinuousStore()
