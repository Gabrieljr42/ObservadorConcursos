"""Persistent per-user recovery review, CAS activation and audited rollback."""
from __future__ import annotations

import json
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from app.tenderproof.recovery import RecoveryPolicy, Snapshot, Strategy, run_strategy
from app.tenderproof.recovery_validation import validate_strategy


class RecoveryConflict(ValueError):
    pass


class RecoveryStore:
    def __init__(self, path: Path):
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        with self.connection() as db:
            db.executescript('''
                CREATE TABLE IF NOT EXISTS recovery_proposals (
                    id TEXT PRIMARY KEY, owner INTEGER NOT NULL, source TEXT NOT NULL,
                    state TEXT NOT NULL, strategy TEXT NOT NULL, previous TEXT,
                    validation TEXT, observation TEXT, reviewer INTEGER, reason TEXT,
                    created TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS recovery_active (
                    owner INTEGER NOT NULL, source TEXT NOT NULL, proposal TEXT,
                    PRIMARY KEY(owner, source));
                CREATE TABLE IF NOT EXISTS recovery_audit (
                    id INTEGER PRIMARY KEY, proposal TEXT NOT NULL, actor INTEGER NOT NULL,
                    action TEXT NOT NULL, reason TEXT NOT NULL, at TEXT NOT NULL);
            ''')

    @contextmanager
    def connection(self):
        db = sqlite3.connect(self.path, timeout=10)
        db.row_factory = sqlite3.Row
        try:
            db.execute("BEGIN IMMEDIATE")
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def _get(self, db, owner, proposal):
        row = db.execute("SELECT * FROM recovery_proposals WHERE id=? AND owner=?", (proposal, owner)).fetchone()
        if row is None:
            raise KeyError("proposal not found")
        return dict(row)

    def _audit(self, db, proposal, owner, action, reason=""):
        db.execute("INSERT INTO recovery_audit(proposal,actor,action,reason,at) VALUES(?,?,?,?,?)",
                   (proposal, owner, action, reason[:1000], datetime.now(timezone.utc).isoformat()))

    def get(self, owner, proposal):
        with self.connection() as db:
            row = self._get(db, owner, proposal)
            for key in ("strategy", "validation", "observation"):
                row[key] = json.loads(row[key]) if row[key] else None
            row["audit"] = [dict(r) for r in db.execute("SELECT actor,action,reason,at FROM recovery_audit WHERE proposal=? ORDER BY id", (proposal,))]
            return row

    def propose(self, owner: int, strategy: Strategy):
        proposal = "tprs-" + uuid.uuid4().hex
        with self.connection() as db:
            active = db.execute("SELECT proposal FROM recovery_active WHERE owner=? AND source=?", (owner, strategy.source)).fetchone()
            db.execute("INSERT INTO recovery_proposals(id,owner,source,state,strategy,previous,created) VALUES(?,?,?,?,?,?,?)",
                       (proposal, owner, strategy.source, "proposed", strategy.model_dump_json(), active[0] if active else None,
                        datetime.now(timezone.utc).isoformat()))
            self._audit(db, proposal, owner, "proposed")
        return self.get(owner, proposal)

    def validate(self, owner, proposal):
        with self.connection() as db:
            row = self._get(db, owner, proposal)
            if row["state"] != "proposed":
                raise RecoveryConflict("validation requires proposed state")
            report = validate_strategy(Strategy.model_validate_json(row["strategy"]))
            db.execute("UPDATE recovery_proposals SET state=?,validation=? WHERE id=?", (
                "tested" if report["passed"] else "validation_failed", json.dumps(report), proposal))
            self._audit(db, proposal, owner, "validated" if report["passed"] else "validation_failed")
        return self.get(owner, proposal)

    def observe(self, owner, proposal, snapshot: Snapshot, policy: RecoveryPolicy):
        """Internal adapter boundary; never accept client supplied attestations."""
        with self.connection() as db:
            row = self._get(db, owner, proposal)
            if row["state"] not in ("tested", "observed"):
                raise RecoveryConflict("observation requires tested state")
            strategy = Strategy.model_validate_json(row["strategy"])
            report = run_strategy(strategy, snapshot, policy)
            previous = None
            if row["previous"]:
                old = self._get(db, owner, row["previous"])
                previous = run_strategy(Strategy.model_validate_json(old["strategy"]), snapshot, policy)
            report["previous_result"] = previous
            report["passed"] = report["diagnosis"] in ("recovered", "legitimate_empty")
            db.execute("UPDATE recovery_proposals SET state=?,observation=? WHERE id=?", (
                "observed" if report["passed"] else "tested", json.dumps(report), proposal))
            self._audit(db, proposal, owner, "observed", "synthetic" if snapshot.is_synthetic else "preserved_snapshot")
        return self.get(owner, proposal)

    def review(self, owner, proposal, approve: bool, reason: str):
        if not reason.strip():
            raise RecoveryConflict("review reason required")
        with self.connection() as db:
            row = self._get(db, owner, proposal)
            if row["state"] in ("active", "rolled_back", "rejected", "approved"):
                raise RecoveryConflict("review state invalid")
            if approve and row["state"] != "observed":
                raise RecoveryConflict("approval requires successful observation")
            db.execute("UPDATE recovery_proposals SET state=?,reviewer=?,reason=? WHERE id=?",
                       ("approved" if approve else "rejected", owner, reason[:1000], proposal))
            self._audit(db, proposal, owner, "approved" if approve else "rejected", reason)
        return self.get(owner, proposal)

    def activate(self, owner, proposal):
        with self.connection() as db:
            row = self._get(db, owner, proposal)
            if row["state"] != "approved" or row["reviewer"] != owner:
                raise RecoveryConflict("human approval required")
            active = db.execute("SELECT proposal FROM recovery_active WHERE owner=? AND source=?", (owner, row["source"])).fetchone()
            if (active[0] if active else None) != row["previous"]:
                raise RecoveryConflict("active baseline changed; create and review a new proposal")
            db.execute("INSERT INTO recovery_active VALUES(?,?,?) ON CONFLICT(owner,source) DO UPDATE SET proposal=excluded.proposal", (owner, row["source"], proposal))
            db.execute("UPDATE recovery_proposals SET state='active' WHERE id=?", (proposal,))
            self._audit(db, proposal, owner, "activated")
        return self.get(owner, proposal)

    def rollback(self, owner, proposal, reason):
        if not reason.strip():
            raise RecoveryConflict("rollback reason required")
        with self.connection() as db:
            row = self._get(db, owner, proposal)
            active = db.execute("SELECT proposal FROM recovery_active WHERE owner=? AND source=?", (owner, row["source"])).fetchone()
            if row["state"] != "active" or not active or active[0] != proposal:
                raise RecoveryConflict("cannot overwrite later strategy")
            db.execute("UPDATE recovery_active SET proposal=? WHERE owner=? AND source=?", (row["previous"], owner, row["source"]))
            db.execute("UPDATE recovery_proposals SET state='rolled_back' WHERE id=?", (proposal,))
            self._audit(db, proposal, owner, "rolled_back", reason)
        return self.get(owner, proposal)

    def active_strategy(self, owner, source) -> Strategy | None:
        with self.connection() as db:
            row = db.execute("SELECT p.strategy FROM recovery_active a JOIN recovery_proposals p ON p.id=a.proposal WHERE a.owner=? AND a.source=?", (owner, source)).fetchone()
            return Strategy.model_validate_json(row[0]) if row else None

    def observe_active(self, owner: int, source: str, snapshot: Snapshot, policy: RecoveryPolicy):
        """Acquisition hook: inspect active strategy without changing catalog."""
        strategy = self.active_strategy(owner, source)
        return run_strategy(strategy, snapshot, policy) if strategy else None
