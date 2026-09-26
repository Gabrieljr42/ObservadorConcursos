"""Offline verification of opt-in live operation; no provider resources created."""
import asyncio
import json
from types import SimpleNamespace

import pytest

from scripts import tenderproof_browser_live_check as live


def test_no_execution_without_specific_authorization(tmp_path, monkeypatch):
    monkeypatch.setattr(live, "configured_adapter", lambda: pytest.fail("must not instantiate provider"))
    with pytest.raises(PermissionError):
        live.execute({}, output=tmp_path)


def test_url_equivalence_preserves_exact_document_identity():
    original = "https://novo.ibgpconcursos.com.br/rest/concurso/download/edital/23011/?file=site/anexos/704/00 - EDITAL.pdf"
    assert live.equivalent_document_url(original.replace(" ", "%20"), original)
    assert not live.equivalent_document_url(original.replace("704", "999"), original)
    assert not live.equivalent_document_url(original.replace("23011", "23012"), original)
    assert not live.equivalent_document_url(original + "&other=1", original)


def test_ineligible_source_blocks_all_spend(tmp_path, monkeypatch):
    monkeypatch.setattr(live, "configured_adapter", lambda: pytest.fail("must not instantiate provider"))
    plan = {"operation": live.OPERATION, "fixed_candidates": live.FIXED_CANDIDATES,
            "sources": [{"source": "ibgp_open", "eligible": True}, {"source": "imeso_open", "eligible": False}]}
    with pytest.raises(ValueError, match="preflight blocked"):
        live.execute(plan, authorized=True, output=tmp_path)


def test_changed_candidate_cannot_expand_authorized_scope(tmp_path):
    plan = {"operation": live.OPERATION, "fixed_candidates": {"ibgp_open": "704", "imeso_open": "999"},
            "sources": [{"eligible": True}, {"eligible": True}]}
    with pytest.raises(ValueError, match="fixed candidates"):
        live.execute(plan, authorized=True, output=tmp_path)


def test_persistent_claim_prevents_repeat_after_restart(tmp_path):
    live.claim_attempt(tmp_path, "ibgp_open")
    with pytest.raises(FileExistsError):
        live.claim_attempt(tmp_path, "ibgp_open")
    with pytest.raises(ValueError):
        live.claim_attempt(tmp_path, "another_source")
    live.claim_attempt(tmp_path, "imeso_open")
    assert len(list(tmp_path.glob("*.attempted"))) == 2


def test_config_ignores_environment_endpoint_and_applies_single_attempt(tmp_path, monkeypatch):
    monkeypatch.setattr(live, "BACKEND", tmp_path)
    (tmp_path / ".env").write_text("SOLARI_API_KEY=test-offline-only\nSOLARI_BASE_URL=https://evil.example", encoding="utf-8")
    monkeypatch.setenv("SOLARI_BASE_URL", "https://evil.example")
    monkeypatch.setenv("SOLARI_API_KEY", "wrong-environment-key")
    monkeypatch.setenv("TENDERPROOF_STEALTH", "true")
    adapter, settings = live.configured_adapter()
    assert adapter.config.api_key == "test-offline-only"
    assert adapter.config.base_url == live.OFFICIAL_API
    assert settings.limits.total_timeout_s == 180 and settings.limits.max_attempts == 1
    assert adapter._launch_kwargs() == {"recording": True, "stealth": False, "retries": 0}
    client = adapter._new_client()  # constructor only, no request/context entry
    assert client.base_url == live.OFFICIAL_API and client._max_attempts == 1
    with pytest.raises(RuntimeError, match="forbidden"):
        adapter.open_listing("https://portal.imeso.com.br/edital/searchEdital")
    adapter.close()


def test_prepare_rejects_judgment_and_retified_140_then_selects_observed139(tmp_path, monkeypatch):
    from app.tenderproof.sources import IMESO_LISTING
    monkeypatch.setattr(live, "BACKEND", tmp_path)
    history = tmp_path / ".tenderproof/review/runs/tpr-c84fdce378eb.json"
    history.parent.mkdir(parents=True)
    history.write_text(json.dumps({"candidates": [{"external_id": "704", "source": "ibgp_open"}],
                                  "document": {"url_requested": "https://novo.ibgpconcursos.com.br/edital.pdf"}}))
    listing = '<div class="row"><p>Paraíso</p><a href="/edital/ver/140">Detalhes</a></div><div class="row"><p>Berizal</p><a href="/edital/ver/139">Detalhes</a></div>'
    pages = {IMESO_LISTING: listing,
        "https://portal.imeso.com.br/edital/ver/140": '<div class="row"><p>JULGAMENTO DAS IMPUGNAÇÕES AO EDITAL</p><a href="https://cdn.imeso.com.br/edital/1/140/j.pdf">DOWNLOAD</a></div>',
        "https://portal.imeso.com.br/edital/ver/139": '<div class="row"><p>EDITAL.</p><a href="https://cdn.imeso.com.br/edital/1/139/e.pdf">DOWNLOAD</a></div>'}
    calls = []
    def read(url):
        calls.append(url)
        return pages[url], {"origin": "offline_double", "url": url}
    monkeypatch.setattr(live, "public_html", read)
    plan = live.prepare(tmp_path / "out")
    assert len(calls) == 3
    assert plan["fixed_candidates"] == live.FIXED_CANDIDATES
    assert not plan["imeso_preflight"][0]["eligible"]
    assert plan["sources"][1]["candidate"]["external_id"] == "139"
    assert not list(tmp_path.rglob("*.attempted"))


def test_provider_get_404_stays_unknown_and_never_releases(monkeypatch):
    import solari_browser
    calls = []
    class NotFound(Exception):
        status = 404
    class Sessions:
        async def get(self, session):
            calls.append(("get", session))
            raise NotFound()
        async def get_replay_url(self, session):
            calls.append(("replay", session))
            return SimpleNamespace(url="https://provider.example/replay")
    class Client:
        def __init__(self, **kwargs):
            assert kwargs["base_url"] == live.OFFICIAL_API and kwargs["max_attempts"] == 1
            self.sessions = Sessions()
        async def request(self, method, path):
            assert method == "GET"
            calls.append((method, path))
            return SimpleNamespace(status_code=200 if path.endswith("replay-url") else 404,
                                   json=lambda: {"url": "https://provider.example/replay"})
        async def __aenter__(self): return self
        async def __aexit__(self, *args): pass
    monkeypatch.setattr(solari_browser, "Solari", Client)
    result = asyncio.run(live.provider_readonly(SimpleNamespace(api_key="offline"), ["session-test"]))
    assert result[0]["session"] == {"http_status": 404, "state": "unknown"}
    assert result[0]["replay"]["available"]
    assert calls == [("GET", "/sessions/session-test"), ("GET", "/sessions/session-test/replay-url")]
