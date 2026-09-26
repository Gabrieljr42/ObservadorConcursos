"""Focused isolation tests for the catalogue review-status boundary."""
import json
from pathlib import Path

from app.tenderproof.continuous_store import ContinuousStore


def _candidate(external_id="abc", link="https://example.test/detail/abc"):
    return {"external_id": external_id, "detail_url_observed": link, "title_observed": "Example"}


def _seed(store, *, owner=7, source="imeso_open", mode="real", key="abc", pending=None):
    with store._db(write=True) as db:
        db.execute(
            "INSERT INTO known_candidates(owner,source,mode,candidate_key,candidate,first_seen,last_seen_listing) VALUES (?,?,?,?,?,?,?)",
            (owner, source, mode, key, json.dumps(_candidate(key)), 1, 1),
        )
        db.execute(
            "INSERT INTO document_review_state(owner,source,mode,candidate_key,manifest,pending_documents) VALUES (?,?,?,?,?,?)",
            (owner, source, mode, key, "[]", json.dumps(pending or [])),
        )


def test_catalogue_review_requires_real_mode_and_exact_external_id_and_url(tmp_path):
    store = ContinuousStore(tmp_path / "continuous.sqlite3")
    _seed(store)
    pending = [{"doc_id": "new-1", "kind": "retificacao", "url_requested": "https://example.test/r.pdf"}]
    with store._db(write=True) as db:
        db.execute("UPDATE document_review_state SET pending_documents=? WHERE owner=7 AND source='imeso_open' AND candidate_key='abc'", (json.dumps(pending),))

    result = store.catalogue_review(7, "imeso_open", external_id="abc", link="https://example.test/detail/abc")
    assert result["pending"] is True
    assert result["documents"] == pending

    assert store.catalogue_review(7, "imeso_open", external_id="abc", link="https://example.test/other")["pending"] is False
    assert store.catalogue_review(7, "imeso_open", external_id="wrong", link="https://example.test/detail/abc")["pending"] is False
    assert store.catalogue_review(7, "imeso_open", external_id="abc", link="https://example.test/detail/abc#fragment")["pending"] is False
    assert store.catalogue_review(8, "imeso_open", external_id="abc", link="https://example.test/detail/abc")["pending"] is False
    assert store.catalogue_review(7, "ibgp_open", external_id="abc", link="https://example.test/detail/abc")["pending"] is False

    with store._db(write=True) as db:
        db.execute("INSERT INTO known_candidates(owner,source,mode,candidate_key,candidate,first_seen,last_seen_listing) VALUES (?,?,?,?,?,?,?)", (7, "imeso_open", "mock", "mock-abc", json.dumps(_candidate("abc", "https://example.test/detail/abc")), 1, 1))
        db.execute("INSERT INTO document_review_state(owner,source,mode,candidate_key,manifest,pending_documents) VALUES (?,?,?,?,?,?)", (7, "imeso_open", "mock", "mock-abc", "[]", json.dumps(pending)))
    assert store.catalogue_review(7, "imeso_open", external_id="mock-only", link="https://example.test/detail/abc")["pending"] is False


def test_clear_review_is_not_pending(tmp_path):
    store = ContinuousStore(tmp_path / "continuous.sqlite3")
    _seed(store, pending=[])
    result = store.catalogue_review(7, "imeso_open", external_id="abc", link="https://example.test/detail/abc")
    assert result["pending"] is False
    assert result["documents"] == []
    assert result["evidence"] == "known_candidate"


def test_regular_endpoint_uses_applied_proposal_owner_and_hides_internal_ids(monkeypatch):
    from app import main

    class Source:
        source_type = "imeso_open"

    class Concurso:
        id = 41
        source_id = 9
        external_id = "abc"
        link_pagina = "https://example.test/detail/abc"

    class ScalarResult:
        def __init__(self, values): self.values = values
        def scalars(self): return self
        def all(self): return self.values

    class DB:
        query = None
        def get(self, model, value):
            return Concurso() if model is main.Concurso else Source()
        def execute(self, query):
            self.query = query
            return ScalarResult([7])

    class Store:
        def catalogue_review(self, owner, source, **kwargs):
            assert owner == 7
            assert source == "imeso_open"
            return {"pending": True, "documents": [{"doc_id": "d1"}], "reason": "review", "evidence": "document_review", "candidate_key": "secret", "last_run_id": "secret-run"}

    monkeypatch.setattr(main, "get_continuous_store", lambda: Store())
    db = DB()
    result = main.get_concurso_review_status(41, db, object())
    compiled = str(db.query)
    assert "tenderproof_publication_proposals.state" in compiled
    assert "tenderproof_publication_proposals.concurso_id" in compiled
    assert db.query.compile().params.get("state_1") == "applied"
    assert result == {"pending": True, "documents": [{"doc_id": "d1"}], "reason": "Há documentos novos aguardando conferência. As datas abaixo são da última versão aprovada e podem ter mudado.", "evidence": "document_review"}
    assert "candidate_key" not in result and "last_run_id" not in result
