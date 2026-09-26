"""Shared durable reservations, separate from confirmed provider billing.

Reservations are never released automatically, even after verified closure.
An ambiguous create therefore cannot spend the same allowance twice.
"""
from decimal import Decimal, ROUND_CEILING
from contextlib import contextmanager
import os
from pathlib import Path
import sqlite3
import time
import uuid


class BudgetExceeded(RuntimeError):
    pass


class SolariBudget:
    def __init__(self, path, *, limit_usd, authority):
        self.path = Path(path)
        amount = Decimal(str(limit_usd))
        if not amount.is_finite() or amount <= 0 or not authority.strip():
            raise ValueError('Limite e autorização explícitos obrigatórios')
        self.limit_cents = int(amount * 100)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._db() as db:
            db.execute('CREATE TABLE IF NOT EXISTS budget (id INTEGER PRIMARY KEY CHECK(id=1), cents INTEGER NOT NULL, authority TEXT NOT NULL)')
            db.execute('CREATE TABLE IF NOT EXISTS reservations (id TEXT PRIMARY KEY, kind TEXT NOT NULL, cents INTEGER NOT NULL, seconds REAL NOT NULL, tariff TEXT NOT NULL, created_at REAL NOT NULL, resource TEXT UNIQUE, closed_at REAL)')
            db.execute('INSERT OR IGNORE INTO budget VALUES (1,?,?)', (self.limit_cents, authority))
            if db.execute('SELECT cents,authority FROM budget WHERE id=1').fetchone() != (self.limit_cents, authority):
                raise ValueError('Autorização diverge do registro persistido')

    @contextmanager
    def _db(self):
        db = sqlite3.connect(self.path, timeout=30)
        try:
            with db:
                yield db
        finally:
            db.close()

    def reserve(self, kind, *, maximum_seconds, hourly_usd, tariff):
        seconds, rate = Decimal(str(maximum_seconds)), Decimal(str(hourly_usd))
        if not seconds.is_finite() or not rate.is_finite() or seconds <= 0 or rate <= 0 or not tariff:
            raise ValueError('Duração máxima e tarifa verificadas obrigatórias')
        cents = int((seconds * rate * 100 / 3600).to_integral_value(rounding=ROUND_CEILING))
        identifier = 'sbr-' + uuid.uuid4().hex
        with self._db() as db:
            db.execute('BEGIN IMMEDIATE')
            used = db.execute('SELECT coalesce(sum(cents),0) FROM reservations').fetchone()[0]
            if used + cents > self.limit_cents:
                raise BudgetExceeded('Teto cumulativo Solari atingido; nova sessão recusada')
            db.execute('INSERT INTO reservations VALUES (?,?,?,?,?,?,NULL,NULL)',
                       (identifier, kind, cents, float(seconds), tariff, time.time()))
        return identifier

    def created(self, reservation, resource):
        if not resource:
            raise ValueError('Identificador remoto obrigatório')
        with self._db() as db:
            result = db.execute('UPDATE reservations SET resource=? WHERE id=? AND (resource IS NULL OR resource=?)',
                                (resource, reservation, resource))
            if result.rowcount != 1:
                raise ValueError('Reserva ausente ou já vinculada')

    def closed(self, resource):
        with self._db() as db:
            db.execute('UPDATE reservations SET closed_at=coalesce(closed_at,?) WHERE resource=?', (time.time(), resource))

    def snapshot(self):
        with self._db() as db:
            db.row_factory = sqlite3.Row
            rows = [dict(r) for r in db.execute('SELECT * FROM reservations ORDER BY created_at')]
        return {'authorized_usd': self.limit_cents / 100, 'reserved_usd': sum(r['cents'] for r in rows) / 100,
                'confirmed_billed_usd': None, 'reservations': rows}


def configured_budget():
    path = os.getenv('TENDERPROOF_SOLARI_BUDGET_PATH')
    if not path:
        return None
    return SolariBudget(path, limit_usd=os.environ['TENDERPROOF_SOLARI_BUDGET_USD'],
                        authority=os.environ['TENDERPROOF_SOLARI_BUDGET_AUTHORITY'])
