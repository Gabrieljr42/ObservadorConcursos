"""Captured HTML integration, synthetic fixture, no driver/network activity."""
from pathlib import Path

from app.tenderproof.recovery import Strategy
from app.tenderproof.recovery_integration import inspect_listing, recover_listing_candidates
from app.tenderproof.recovery_store import RecoveryStore
from app.tenderproof.recovery_validation import POLICY, load_snapshot
from app.tenderproof.security import TenderProofSettings

HTML = (Path(__file__).parent / "tenderproof_fixtures/recovery/ibgp_navigation_changed.html").read_text(encoding="utf-8")
URL = "https://novo.ibgpconcursos.com.br/inscricoes_abertas.jsp"


def strategy():
    return Strategy(cards=(".old-card", ".new-card"), details=(".detail",), documents=(".notice",))


def test_changed_layout_recovered_without_html_identity_marker():
    assert "data-identity" not in HTML
    settings = TenderProofSettings()
    old = strategy().model_copy(update={"cards": (".old-card",)})
    assert inspect_listing(old, html=HTML, listing_url=URL, settings=settings)[1]["diagnosis"] == "false_empty"
    candidates, report = inspect_listing(strategy(), html=HTML, listing_url=URL, settings=settings)
    assert report["diagnosis"] == "navigation_recovered"
    assert report["evidence_state"] == "pending_document_validation"
    assert candidates[0].external_id == "704"
    assert candidates[0].title_observed == "ITABIRAPREV - Concurso Público 001/2026"


def test_acquisition_hook_requires_owner_active_reviewed_strategy(tmp_path):
    store = RecoveryStore(tmp_path / "recovery.db")
    args = dict(source="ibgp_open", html=HTML, listing_url=URL, settings=TenderProofSettings())
    assert recover_listing_candidates(store, owner_user_id=1, **args) == ([], None)
    proposal = store.propose(1, strategy())["id"]
    store.validate(1, proposal)
    store.observe(1, proposal, load_snapshot("09_recovered_navigation"), POLICY)
    assert recover_listing_candidates(store, owner_user_id=1, **args) == ([], None)
    store.review(1, proposal, True, "Reviewed synthetic results")
    store.activate(1, proposal)
    assert len(recover_listing_candidates(store, owner_user_id=1, **args)[0]) == 1
    assert recover_listing_candidates(store, owner_user_id=2, **args) == ([], None)
    store.rollback(1, proposal, "Return to original")
    assert recover_listing_candidates(store, owner_user_id=1, **args) == ([], None)


def test_invalid_identity_or_unsafe_url_never_becomes_candidate():
    for url in ("https://evil.example/concurso.jsp?cod=704", "/other.jsp?cod=704",
                "/concurso.jsp?cod=704&cod=999", "https://user:pw@novo.ibgpconcursos.com.br/concurso.jsp?cod=704"):
        html = HTML.replace("/concurso.jsp?cod=704", url)
        candidates, report = inspect_listing(strategy(), html=html, listing_url=URL, settings=TenderProofSettings())
        assert not candidates
        assert report["diagnosis"] in ("identity_inconsistent", "destination_blocked")


def test_runtime_corpus_is_packaged_outside_tests():
    from app.tenderproof.recovery_validation import FIXTURES, validate_strategy
    assert "tests" not in FIXTURES.parts
    assert validate_strategy(strategy())["passed"]
