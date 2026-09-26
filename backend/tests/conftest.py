"""Keep TenderProof test artifacts separate from real review runs."""

import pytest


@pytest.fixture
def legacy_crawler_enabled(monkeypatch):
    """Legacy compatibility suites explicitly exercise an opted-in installation."""
    from app.config import get_settings
    monkeypatch.setattr(get_settings(), 'legacy_crawler_enabled', True)


@pytest.fixture(autouse=True)
def isolated_tenderproof_store(tmp_path, monkeypatch, request):
    if "tenderproof" not in request.node.nodeid:
        return
    import app.tenderproof.store as store

    monkeypatch.setenv("TENDERPROOF_ARTIFACT_DIR", str(tmp_path / "artifacts"))
    monkeypatch.setattr(store, "_store", None)
