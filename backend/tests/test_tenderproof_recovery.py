"""Synthetic adversarial recovery + real local SQLite/JWT dependency boundary."""
from dataclasses import replace

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.auth import get_current_user
from app.models import User
from app.tenderproof.recovery import Strategy, run_strategy, safe_excerpt
from app.tenderproof.recovery_router import get_recovery_store, router
from app.tenderproof.recovery_store import RecoveryConflict, RecoveryStore
from app.tenderproof.recovery_validation import POLICY, load_snapshot, validate_strategy


def good():
    return Strategy(cards=(".old-card", ".new-card"), details=(".detail",), documents=(".notice",))


@pytest.mark.parametrize("name,expected", [
    ("01_old_layout", "recovered"), ("02_changed_layout", "recovered"),
    ("03_legitimate_empty", "legitimate_empty"), ("04_false_empty", "false_empty"),
    ("05_wrong_contest", "wrong_document"), ("06_annex", "wrong_document_kind"),
    ("07_malicious_content", "recovered"), ("08_semantic_error", "identity_inconsistent"),
    ("09_recovered_navigation", "recovered"), ("10_regression", "recovered"),
])
def test_adversarial_fixtures(name, expected):
    result = run_strategy(good(), load_snapshot(name), POLICY)
    assert result["diagnosis"] == expected
    assert result["is_synthetic"] and result["publication"] == "disabled"
    assert "do-not-retain" not in result["excerpt"]


def test_independent_validator_rejects_semantically_wrong_and_regression():
    assert validate_strategy(good())["passed"]
    for change in ({"documents": (".annex",)}, {"cards": (".new-card",)}, {"cards": (".broken",)}):
        assert not validate_strategy(good().model_copy(update=change))["passed"]


@pytest.mark.parametrize("change", [
    {"python": "print('bad')"}, {"javascript": "fetch('bad')"}, {"shell": "rm"},
    {"max_steps": 999999}, {"hosts": ["evil.example"]}, {"identity_required": False},
    {"cards": ["a[href]"]}, {"cards": ["x" * 65]}, {"operations": ["evaluate"]},
])
def test_proposal_cannot_change_policy_or_execute_code(change):
    with pytest.raises(ValidationError):
        Strategy.model_validate({**good().model_dump(), **change})


def test_diagnosis_limits_network_redirect_evidence():
    snapshot = load_snapshot("09_recovered_navigation")
    assert run_strategy(good(), replace(snapshot, network_error=True), POLICY)["diagnosis"] == "network_failure"
    assert run_strategy(good(), replace(snapshot, blocked=True), POLICY)["diagnosis"] == "blocked"
    for policy in (replace(POLICY, max_bytes=1), replace(POLICY, max_steps=1), replace(POLICY, max_seconds=0)):
        assert run_strategy(good(), snapshot, policy)["diagnosis"] == "limit_exceeded"
    bad = replace(snapshot, redirects=("https://evil.example/redirect",))
    assert run_strategy(good(), bad, POLICY)["diagnosis"] == "destination_blocked"
    docs = {k: replace(v, quote="fabricated evidence") for k, v in snapshot.documents.items()}
    assert run_strategy(good(), replace(snapshot, documents=docs), POLICY)["diagnosis"] == "insufficient_evidence"
    assert run_strategy(good(), replace(snapshot, pages={}), POLICY)["diagnosis"] == "layout_changed"
    old = good().model_copy(update={"cards": (".old-card",)})
    assert run_strategy(old, snapshot, POLICY)["diagnosis"] == "false_empty"


def observed(store, owner=1):
    proposal = store.propose(owner, good())["id"]
    assert store.validate(owner, proposal)["state"] == "tested"
    assert store.observe(owner, proposal, load_snapshot("09_recovered_navigation"), POLICY)["state"] == "observed"
    return proposal


def approved(store, owner=1):
    proposal = observed(store, owner)
    store.review(owner, proposal, True, "Human checked identity and evidence")
    return proposal


def test_persisted_lifecycle_human_review_rollback_isolation(tmp_path):
    path = tmp_path / "recovery.sqlite3"
    store = RecoveryStore(path)
    proposal = observed(store)
    assert store.active_strategy(1, "ibgp") is None
    with pytest.raises(RecoveryConflict):
        store.activate(1, proposal)
    with pytest.raises(KeyError):
        store.get(2, proposal)
    store.review(1, proposal, True, "Human reviewed")
    store.activate(1, proposal)
    store = RecoveryStore(path)
    assert store.active_strategy(1, "ibgp").digest == good().digest
    assert store.active_strategy(2, "ibgp") is None
    second = approved(store)
    store.activate(1, second)
    with pytest.raises(RecoveryConflict):
        store.rollback(1, proposal, "would overwrite later")
    rolled = store.rollback(1, second, "Regression noticed by reviewer")
    assert rolled["state"] == "rolled_back"
    assert store.get(1, proposal)["state"] == "active"
    assert store.active_strategy(1, "ibgp").digest == good().digest
    store.rollback(1, proposal, "Restore original connector")
    assert store.active_strategy(1, "ibgp") is None
    assert store.get(1, second)["audit"][-1]["action"] == "rolled_back"


def test_stale_strategy_baseline_and_rejection(tmp_path):
    store = RecoveryStore(tmp_path / "r.db")
    first, stale = approved(store), approved(store)
    store.activate(1, first)
    with pytest.raises(RecoveryConflict):
        store.activate(1, stale)
    proposal = store.propose(1, good())["id"]
    with pytest.raises(RecoveryConflict):
        store.review(1, proposal, True, "too early")
    assert store.review(1, proposal, False, "insufficient evidence")["state"] == "rejected"


def test_active_observation_preserved_snapshot_honesty(tmp_path):
    store = RecoveryStore(tmp_path / "r.db")
    proposal = approved(store)
    store.activate(1, proposal)
    snapshot = replace(load_snapshot("09_recovered_navigation"), is_synthetic=False)
    report = store.observe_active(1, "ibgp", snapshot, POLICY)
    assert report["publication"] == "disabled" and not report["is_synthetic"]
    assert store.observe_active(2, "ibgp", snapshot, POLICY) is None


def test_auth_api_cannot_supply_validation_or_observation_attestations(tmp_path):
    app = FastAPI()
    app.include_router(router)
    store = RecoveryStore(tmp_path / "r.db")
    app.dependency_overrides[get_recovery_store] = lambda: store
    client = TestClient(app)
    assert client.post("/tenderproof/recovery/proposals", json=good().model_dump()).status_code in (401, 403)
    user = User(id=1, name="Reviewer", email="reviewer@example.com", password_hash="unused")
    app.dependency_overrides[get_current_user] = lambda: user
    response = client.post("/tenderproof/recovery/proposals", json=good().model_dump())
    assert response.status_code == 201
    base = "/tenderproof/recovery/proposals/" + response.json()["id"]
    assert client.post(base + "/activate").status_code == 409
    assert client.post(base + "/validate").json()["state"] == "tested"
    assert client.post(base + "/observe-offline").json()["observation"]["is_synthetic"]
    assert client.post(base + "/review", json={"approve": True, "reason": "Manual approval"}).status_code == 200
    assert client.post(base + "/activate").json()["state"] == "active"
    assert client.post(base + "/rollback", json={"reason": "restore"}).json()["state"] == "rolled_back"
    user.id = 2
    assert client.get(base).status_code == 404
    assert client.post(base + "/validate").status_code == 404


def test_excerpt_redaction():
    text = safe_excerpt("Bearer abc123 api_key=SECRET https://site.test/path?token=OTHER password=PW")
    assert all(secret not in text for secret in ("abc123", "SECRET", "OTHER", "PW"))
    assert len(safe_excerpt("x" * 99999)) == 2000


def test_concurrent_activation_has_one_winner(tmp_path):
    from concurrent.futures import ThreadPoolExecutor

    path = tmp_path / "recovery.db"
    store = RecoveryStore(path)
    proposals = [approved(store), approved(store)]

    def activate(proposal):
        try:
            RecoveryStore(path).activate(1, proposal)
            return "active"
        except RecoveryConflict:
            return "stale"

    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(activate, proposals)) == ["active", "stale"]


def test_corrupt_document_hash_and_non_pdf_rejected():
    snapshot = load_snapshot("09_recovered_navigation")
    for changes in ({"sha256": "0" * 64}, {"content": b"not a PDF"}, {"physical_page": 0}):
        docs = {key: replace(doc, **changes) for key, doc in snapshot.documents.items()}
        result = run_strategy(good(), replace(snapshot, documents=docs), POLICY)
        assert result["diagnosis"] == "insufficient_evidence"


def test_observation_failure_prevents_approval(tmp_path):
    store = RecoveryStore(tmp_path / "recovery.db")
    proposal = store.propose(1, good())["id"]
    store.validate(1, proposal)
    assert store.observe(1, proposal, load_snapshot("05_wrong_contest"), POLICY)["state"] == "tested"
    with pytest.raises(RecoveryConflict):
        store.review(1, proposal, True, "Generic approval cannot override evidence")
