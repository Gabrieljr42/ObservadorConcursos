"""TenderProof — adaptador REAL exercitado com doubles na fronteira do SDK.

Substitui apenas ``solari_browser`` (``_get_solari_class`` /
``_get_solari_error_class``); todo o resto — ciclo de vida, captura de rede,
download, replay polling, timeouts — é o código de produção. Não testa
``FakeSolariDriver`` (coberto nos outros arquivos).
"""

import asyncio
import os
import tempfile

import pytest

import app.tenderproof.solari_adapter as adapter_mod
from app.tenderproof.security import DestinationBlocked, TenderProofSettings
from app.tenderproof.solari_adapter import (
    SolariBrowserAdapter,
    SolariConfig,
    SolariNotConfigured,
)


class FakeSolariError(Exception):
    def __init__(self, message="erro", status=None, code=None):
        super().__init__(message)
        self.status = status
        self.code = code


class FakeResponse:
    def __init__(self, url, status=200, payload=None, unreadable=False):
        self.url = url
        self.status = status
        self._payload = payload
        self._unreadable = unreadable

    async def json(self):
        if self._unreadable:
            raise ValueError("json inválido")
        return self._payload


class FakeRedirectNode:
    def __init__(self, url, parent=None):
        self.url = url
        self.redirected_from = parent


class FakeAPIRequest:
    def __init__(self, url):
        self.url = url
        self.redirected_from = None


class FakeAPIResponse:
    def __init__(self, url, status=200, headers=None, body=b"", chain=()):
        self.url = url
        self.status = status
        self.headers = headers or {}
        self._body = body
        node = None
        for hop in chain:
            node = FakeRedirectNode(hop, node)
        self.request = FakeAPIRequest(url)
        self.request.redirected_from = node

    async def dispose(self):
        self.disposed = True

    async def body(self):
        return self._body


class FakeDownload:
    def __init__(self, content, url, failure=None):
        self._content = content
        self.url = url
        self._failure = failure
        self.suggested_filename = "edital.pdf"
        self.deleted = False

    async def failure(self):  # assíncrono no SDK real — doubles devem refletir
        return self._failure

    async def path(self):
        raise RuntimeError("Path is not available for remote connections")

    async def save_as(self, path):
        from pathlib import Path
        self._tmp = str(path)
        Path(path).write_bytes(self._content)

    async def delete(self):
        self.deleted = True
        try:
            os.unlink(self._tmp)
        except Exception:
            pass


class FakeDownloadInfo:
    def __init__(self, download=None, click_error=None, page=None):
        self._download = download
        self._click_error = click_error
        self._page = page

    @property
    def value(self):
        page = self._page

        async def _get():
            # Resolução tardia: o download só existe após o clique dentro do bloco.
            if page is not None and page._pending_download is not None:
                return page._pending_download
            return self._download

        return _get()


class FakeDownloadCtx:
    def __init__(self, script, page):
        self._script = script
        self._page = page

    async def __aenter__(self):
        mode = self._script.get("click", "ok")
        if mode == "raise_on_enter":
            raise RuntimeError("expect_download falhou")
        return FakeDownloadInfo(self._page._pending_download, page=self._page)

    async def __aexit__(self, *exc):
        return False


class FakeAnchor:
    def __init__(self, page):
        self._page = page

    async def click(self):
        mode = self._page._script.get("click", "ok")
        if mode == "interrupted":
            self._page._pending_download = FakeDownload(b"", self._page._script["doc_url"], failure="net")
        elif mode == "no_path":
            self._page._pending_download = FakeDownload(None, self._page._script["doc_url"])
        else:
            self._page._pending_download = FakeDownload(
                self._page._script["click_bytes"], self._page._script["doc_url"]
            )


class FakeHandle:
    def __init__(self, element):
        self._element = element

    def as_element(self):  # síncrono no patchright real
        return self._element

    async def dispose(self):
        pass


class FakeLocator:
    def __init__(self, page):
        self.first = self
        self._page = page

    async def wait_for(self, timeout=None):
        if self._page._script.get("no_anchors"):
            raise TimeoutError("sem âncora")


class FakeRoute:
    def __init__(self, url):
        self.request = FakeAPIRequest(url)
        self.aborted = False
        self.continued = False

    async def abort(self):
        self.aborted = True

    async def continue_(self):
        self.continued = True


class FakeNavigationRequest(FakeAPIRequest):
    def __init__(self, url, page, *, navigation=True):
        super().__init__(url)
        self.frame = page.main_frame
        self.navigation = navigation

    def is_navigation_request(self):
        return self.navigation


class FakeNavigationRoute:
    def __init__(self, url, page, *, navigation=True):
        self.request = FakeNavigationRequest(url, page, navigation=navigation)
        self._page = page
        self.aborted = False
        self.fulfilled = False
        self.body = b""

    async def fetch(self, *, url, max_redirects, timeout):
        assert max_redirects == 0  # Model one response, never follow internally.
        script = self._page._script
        script.setdefault("navigation_requested_urls", []).append(url)
        response = script.get("navigation_responses", {}).get(url, {})
        return FakeAPIResponse(
            url, status=response.get("status", 200), headers=response.get("headers", {}),
            body=response.get("body", script.get("html", "<html></html>").encode()),
        )

    async def abort(self):
        self.aborted = True

    async def fulfill(self, *, response, body):
        self.fulfilled = True
        self.body = body


class FakeRequestContext:
    def __init__(self, script, context):
        self._script = script
        self._context = context

    async def get(self, url, timeout=None, max_redirects=None):
        assert max_redirects == 0
        self._script.setdefault("requested_urls", []).append(url)
        spec = self._script.get("request", {})
        if spec.get("raise"):
            raise RuntimeError("request falhou")
        destination = spec.get("final_url", url)
        if destination != url:
            return FakeAPIResponse(url, status=302, headers={"location": destination})
        return FakeAPIResponse(
            url, status=spec.get("status", 200),
            headers=spec.get("headers", {"content-type": "application/pdf"}),
            body=spec.get("body", b""),
        )


class FakeContext:
    def __init__(self, script):
        self.request = FakeRequestContext(script, self)
        self._routes: list = []
        self.unrouted = False

    async def route(self, pattern, handler):
        self._routes.append((pattern, handler))

    async def unroute(self, pattern, handler=None):
        self._routes = [(p, h) for p, h in self._routes if p != pattern or (handler is not None and h != handler)]
        self.unrouted = True


class FakePage:
    def __init__(self, script, browser):
        self._script = script
        self._browser = browser
        self._handlers = []
        self.context = FakeContext(script)
        self._pending_download = None
        self.url = "about:blank"
        self.main_frame = object()
        self._rendered_html = None

    def on(self, event, handler):
        self._handlers.append((event, handler))

    async def goto(self, url, wait_until=None, timeout=None):
        if self._script.get("hang_on") == "goto":
            await asyncio.sleep(30)
        self._script.setdefault("goto_urls", []).append(url)
        if self.context._routes:
            route = FakeNavigationRoute(url, self)
            await self.context._routes[-1][1](route)
            if route.aborted:
                raise RuntimeError("net::ERR_FAILED (navigation aborted)")
            assert route.fulfilled
            self._rendered_html = route.body.decode()
        self.url = self._script.get("page_final_url", url)
        for asset in self._script.get("navigation_assets", []):
            route = FakeNavigationRoute(asset, self, navigation=False)
            await self.context._routes[-1][1](route)
        for entry in self._script.get("rest", []):
            for _event, handler in self._handlers:
                handler(FakeResponse(entry["url"], entry.get("status", 200),
                                     entry.get("payload"), entry.get("unreadable", False)))

    def locator(self, selector):
        return FakeLocator(self)

    async def wait_for_response(self, predicate, timeout=None):
        return None

    async def content(self):
        return self._rendered_html if self._rendered_html is not None else self._script.get("html", "<html></html>")

    async def evaluate_handle(self, js, url):
        if self._script.get("no_anchor_for_download"):
            return FakeHandle(None)
        return FakeHandle(FakeAnchor(self))

    def expect_download(self, timeout=None):
        return FakeDownloadCtx(self._script, self)


class FakeBrowser:
    instances = []

    def __init__(self, script, session_id):
        self._script = script
        self.id = session_id
        self.page = FakePage(script, self)
        self.close_calls = 0
        FakeBrowser.instances.append(self)

    async def new_page(self):
        return self.page

    async def close(self):
        self.close_calls += 1
        if self._script.get("close_raises"):
            raise RuntimeError("close falhou")


class FakeSessions:
    def __init__(self, script):
        self._script = script
        self.replay_calls = 0

    async def get(self, session_id):
        return {"status": self._script.get("provider_status", "released")}

    async def get_replay_url(self, session_id):
        self.replay_calls += 1
        plan = self._script.get("replay_plan", [("ok", "https://replay.example/s")])
        outcome = plan[min(self.replay_calls - 1, len(plan) - 1)]
        if outcome[0] == "404":
            raise FakeSolariError("replay not found", status=404)
        if outcome[0] == "error":
            raise FakeSolariError(outcome[2], status=outcome[1])
        return {"url": outcome[1]}


class FakeSolari:
    instances = []

    def __init__(self, api_key=None, region=None, base_url=None, *,
                 max_attempts=2, backoff_ms=500, timeout_ms=90_000):
        self.api_key = api_key
        self._max_attempts = max_attempts
        self._backoff_ms = backoff_ms
        self._timeout_s = timeout_ms / 1000
        self.sessions = FakeSessions(FakeSolari.script)
        self.exit_calls = 0
        FakeSolari.instances.append(self)

    @classmethod
    def reset(cls, script):
        cls.instances = []
        cls.script = dict(script)
        FakeBrowser.instances = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        self.exit_calls += 1
        return False

    async def launch(self, **kwargs):
        FakeSolari.script["launch_kwargs"] = kwargs
        if FakeSolari.script.get("launch_raises"):
            raise RuntimeError("launch falhou")
        session_id = FakeSolari.script.get("session_id", "sess-real-1")
        return FakeBrowser(FakeSolari.script, session_id)


@pytest.fixture
def doubles(monkeypatch):
    monkeypatch.setattr(adapter_mod, "_get_solari_class", lambda: FakeSolari)
    monkeypatch.setattr(adapter_mod, "_get_solari_error_class", lambda: FakeSolariError)
    return FakeSolari


LISTING_HTML = (
    "<html><body>"
    "<a href='/concurso.jsp?cod=42'>Concurso Exemplo cod 42</a>"
    "</body></html>"
)
DETAIL_HTML = (
    "<html><body><h1>Concurso Exemplo cod 42</h1>"
    "<a href='https://novo.ibgpconcursos.com.br/f/edital.pdf'>Edital 01/2026</a>"
    "</body></html>"
)
DOC_URL = "https://novo.ibgpconcursos.com.br/f/edital.pdf"
PDF = b"%PDF-1.4 fake-bytes"


def _settings(**over):
    limits = {
        "total_timeout_s": 30.0,
        "replay_deadline_s": 0.05,
        "replay_poll_interval_s": 0.01,
    }
    limits.update(over)
    settings = TenderProofSettings.from_env()
    for key, value in limits.items():
        setattr(settings.limits, key, value)
    return settings


def _config():
    return SolariConfig(api_key="test-key", recording=True)


def test_missing_credentials_raise_without_sdk_touch(doubles):
    adapter = SolariBrowserAdapter(SolariConfig(api_key=None), _settings())
    with pytest.raises(SolariNotConfigured):
        adapter.open_listing("https://novo.ibgpconcursos.com.br/x")
    assert FakeSolari.instances == []


def test_missing_sdk_raises(monkeypatch):
    def _boom():
        raise ImportError("sem pacote")

    monkeypatch.setattr(adapter_mod, "_get_solari_class", _boom)
    adapter = SolariBrowserAdapter(_config(), _settings())
    with pytest.raises(SolariNotConfigured):
        adapter.open_listing("https://novo.ibgpconcursos.com.br/x")


def test_listing_session_lifecycle_and_replay(doubles):
    FakeSolari.reset({"html": LISTING_HTML, "session_id": "sess-list-1"})
    adapter = SolariBrowserAdapter(_config(), _settings())
    html = adapter.open_listing("https://novo.ibgpconcursos.com.br/inscricoes_abertas.jsp")
    assert "cod=42" in html
    assert adapter.session_id == "sess-list-1"
    assert adapter.replay_available
    assert adapter.replay_url() == "https://replay.example/s"
    records = adapter.session_records()
    assert len(records) == 1 and records[0].phase == "discovery"
    assert records[0].closed and records[0].replay_status == "available"
    assert FakeBrowser.instances[0].close_calls == 1  # encerrada, sem vazar sessão
    adapter.close()
    adapter.close()  # idempotente


def test_detail_and_download_share_one_session(doubles):
    FakeSolari.reset({
        "html": DETAIL_HTML, "session_id": "sess-detail-1",
        "doc_url": DOC_URL, "click_bytes": PDF,
    })
    adapter = SolariBrowserAdapter(_config(), _settings())
    html = adapter.open_detail("https://novo.ibgpconcursos.com.br/concurso.jsp?cod=42")
    assert "cod 42" in html
    browser_before = FakeBrowser.instances[-1]
    downloaded = adapter.download(DOC_URL, max_bytes=10_000)
    assert FakeBrowser.instances[-1] is browser_before  # mesma sessão/contexto
    assert downloaded.content == PDF and downloaded.mechanism == "click"
    assert downloaded.sha256 and downloaded.url_final == DOC_URL
    adapter.close()
    assert browser_before.close_calls == 1
    records = adapter.session_records()
    assert [r.phase for r in records] == ["detail"]
    assert records[0].closed


def test_json_captured_after_navigation_and_noise_ignored(doubles):
    FakeSolari.reset({
        "html": LISTING_HTML,
        "rest": [
            {"url": "https://novo.ibgpconcursos.com.br/rest/concurso/42", "status": 200,
             "payload": {"meta": {"nome": "X"}}},
            {"url": "https://tracker.example/pixel", "status": 200, "payload": {}},
            {"url": "https://novo.ibgpconcursos.com.br/rest/concurso/erro", "status": 200,
             "unreadable": True},
        ],
    })
    adapter = SolariBrowserAdapter(_config(), _settings())
    adapter.open_listing("https://novo.ibgpconcursos.com.br/inscricoes_abertas.jsp")
    observed = adapter.observed_json()
    assert [o.url for o in observed] == ["https://novo.ibgpconcursos.com.br/rest/concurso/42"]
    assert observed[0].payload == {"meta": {"nome": "X"}}
    assert any("ilegível" in note for note in adapter.diagnostics())  # falha visível
    adapter.close()


def test_download_falls_back_to_request_when_click_fails(doubles):
    FakeSolari.reset({
        "html": DETAIL_HTML, "doc_url": DOC_URL, "click": "interrupted",
        "request": {"body": PDF, "final_url": DOC_URL},
    })
    adapter = SolariBrowserAdapter(_config(), _settings())
    adapter.open_detail("https://novo.ibgpconcursos.com.br/concurso.jsp?cod=42")
    downloaded = adapter.download(DOC_URL, max_bytes=10_000)
    assert downloaded.content == PDF and downloaded.mechanism == "request"
    assert any("via request" in note for note in adapter.diagnostics())
    adapter.close()


def test_invalid_html_and_oversize_downloads_rejected(doubles):
    FakeSolari.reset({
        "html": DETAIL_HTML, "doc_url": DOC_URL, "click_bytes": b"<html>bloqueio</html>",
    })
    adapter = SolariBrowserAdapter(_config(), _settings())
    adapter.open_detail("https://novo.ibgpconcursos.com.br/concurso.jsp?cod=42")
    with pytest.raises(ValueError, match="HTML"):
        adapter.download(DOC_URL, max_bytes=10_000)
    adapter.close()

    FakeSolari.reset({
        "html": DETAIL_HTML, "doc_url": DOC_URL, "click_bytes": PDF,
        "request": {"body": PDF, "final_url": DOC_URL,
                    "headers": {"content-type": "application/pdf", "content-length": "99999"}},
    })
    adapter = SolariBrowserAdapter(_config(), _settings())
    adapter.open_detail("https://novo.ibgpconcursos.com.br/concurso.jsp?cod=42")
    with pytest.raises(ValueError, match="acima do limite"):
        adapter.download(DOC_URL, max_bytes=10)  # clique: pós-checagem; request: pré-checagem
    adapter.close()


def test_forbidden_redirect_is_blocked(doubles):
    script = {
        "html": DETAIL_HTML, "doc_url": DOC_URL, "no_anchor_for_download": True,
        "request": {"body": PDF, "final_url": "https://evil.example.com/f.pdf",
                    "chain": ("https://novo.ibgpconcursos.com.br/f/edital.pdf",)},
    }
    FakeSolari.reset(script)
    adapter = SolariBrowserAdapter(_config(), _settings())
    adapter.open_detail("https://novo.ibgpconcursos.com.br/concurso.jsp?cod=42")
    with pytest.raises(Exception, match="(?i)allowlist|bloquead"):
        adapter.download(DOC_URL, max_bytes=10_000)
    # Nenhum corpo tocado após o bloqueio + guarda removida após o download.
    assert FakeSolari.script["requested_urls"] == [DOC_URL]
    adapter.close()


def test_click_download_success_uses_click_path(doubles):
    # Sem await em failure(), a corrotina seria truthy e este teste falharia
    # (todo clique pareceria "interrompido" e cairia no fallback).
    FakeSolari.reset({
        "html": DETAIL_HTML, "doc_url": DOC_URL, "click_bytes": PDF,
    })
    adapter = SolariBrowserAdapter(_config(), _settings())
    adapter.open_detail("https://novo.ibgpconcursos.com.br/concurso.jsp?cod=42")
    downloaded = adapter.download(DOC_URL, max_bytes=10_000)
    assert downloaded.mechanism == "click"
    assert downloaded.content == PDF
    assert downloaded.sha256
    adapter.close()


def test_missing_anchor_is_legitimate_fallback_and_temp_cleaned(doubles):
    FakeSolari.reset({
        "html": DETAIL_HTML, "doc_url": DOC_URL, "no_anchor_for_download": True,
        "request": {"body": PDF, "final_url": DOC_URL},
    })
    adapter = SolariBrowserAdapter(_config(), _settings())
    adapter.open_detail("https://novo.ibgpconcursos.com.br/concurso.jsp?cod=42")
    downloaded = adapter.download(DOC_URL, max_bytes=10_000)
    assert downloaded.mechanism == "request"
    assert any("sem âncora" in note for note in adapter.diagnostics())
    adapter.close()


def test_temp_file_removed_when_content_invalid(doubles):
    FakeSolari.reset({
        "html": DETAIL_HTML, "doc_url": DOC_URL, "click_bytes": b"<html>bloqueio</html>",
    })
    adapter = SolariBrowserAdapter(_config(), _settings())
    adapter.open_detail("https://novo.ibgpconcursos.com.br/concurso.jsp?cod=42")
    with pytest.raises(ValueError, match="HTML"):
        adapter.download(DOC_URL, max_bytes=10_000)
    browser = FakeBrowser.instances[-1]
    assert browser.page._pending_download.deleted is True
    adapter.close()


def test_replay_available_after_retries(doubles):
    FakeSolari.reset({
        "html": LISTING_HTML,
        "replay_plan": [("404",), ("404",), ("ok", "https://replay.example/late")],
    })
    settings = _settings(replay_deadline_s=5.0, replay_poll_interval_s=0.01)
    adapter = SolariBrowserAdapter(_config(), settings)
    adapter.open_listing("https://novo.ibgpconcursos.com.br/inscricoes_abertas.jsp")
    assert adapter.replay_url() == "https://replay.example/late"
    assert "tentativa(s)" in (adapter.session_records()[0].replay_note or "")
    adapter.close()


def test_replay_definitive_failure_is_recorded_not_silent(doubles):
    FakeSolari.reset({
        "html": LISTING_HTML,
        "replay_plan": [("error", 500, "pool indisponível")],
    })
    adapter = SolariBrowserAdapter(_config(), _settings())
    adapter.open_listing("https://novo.ibgpconcursos.com.br/inscricoes_abertas.jsp")
    record = adapter.session_records()[0]
    assert record.replay_status == "failed"
    assert "pool indisponível" in (record.replay_note or "")
    assert not adapter.replay_available
    assert any("replay" in note for note in adapter.diagnostics())
    adapter.close()


def test_close_failure_records_unclosed_session_without_raising(doubles):
    FakeSolari.reset({"html": DETAIL_HTML, "doc_url": DOC_URL, "click_bytes": b"%PDF-1.4 x",
                      "close_raises": True})
    adapter = SolariBrowserAdapter(_config(), _settings())
    adapter.open_detail("https://novo.ibgpconcursos.com.br/concurso.jsp?cod=42")
    adapter.close()  # nunca levanta
    adapter.close()  # idempotente
    records = adapter.session_records()
    assert len(records) == 1 and records[0].phase == "detail"
    assert records[0].closed is False
    assert any("close falhou" in note or "expira no servidor" in note for note in adapter.diagnostics())


def test_timeout_and_cancel_close_session(doubles):
    FakeSolari.reset({"html": DETAIL_HTML, "hang_on": "goto"})
    settings = _settings(total_timeout_s=0.3)
    adapter = SolariBrowserAdapter(_config(), settings)
    with pytest.raises(TimeoutError):
        adapter.open_detail("https://novo.ibgpconcursos.com.br/concurso.jsp?cod=42")
    adapter.close()  # nunca levanta
    assert FakeBrowser.instances[0].close_calls >= 1


def test_real_adapter_offline_flow_writes_no_canonical_tables(doubles):
    from sqlalchemy import create_engine, func, select
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import StaticPool

    from app.database import Base
    from app.models import Concurso, ConcursoVersion, Notification
    from app.tenderproof.service import TenderProofService
    from app.tenderproof.store import TenderProofStore

    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False},
                           poolclass=StaticPool)
    Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine)()

    from app.tenderproof.demo_pdf import make_text_pdf

    pdf = make_text_pdf([
        "PREFEITURA MUNICIPAL DE EXEMPLO\nConcurso Exemplo cod 42\n"
        "Edital n. 01/2026\ninscricoes de 10/03/2026 a 20/04/2026\n"
        "Cargo de Agente com vencimento de R$ 3.500,00"
    ])
    FakeSolari.reset({
        "html": ("<html><body><a href='/concurso.jsp?cod=42'>Concurso Exemplo cod 42</a></body></html>"),
        "doc_url": DOC_URL, "click_bytes": pdf,
    })
    service = TenderProofService(TenderProofStore(), _settings())
    adapter = SolariBrowserAdapter(_config(), _settings())
    run = service.start_discovery(adapter)
    assert run.execution_status.value == "awaiting_selection"

    FakeSolari.reset({
        "html": ("<html><body>concurso.jsp?cod=42 Concurso Exemplo cod 42 "
                 f"<a href='{DOC_URL}'>Edital n. 01/2026</a></body></html>"),
        "doc_url": DOC_URL, "click_bytes": pdf,
    })
    adapter2 = SolariBrowserAdapter(_config(), _settings())
    out = service.select_and_process(run.run_id, "cand-42", adapter2)
    assert out.execution_status.value == "completed"
    assert out.sessions and out.sessions[0].phase == "discovery"
    # O registro da etapa detail nasce no close(): presente após o término.
    assert [s.phase for s in out.sessions] == ["discovery", "detail"]
    assert all(s.closed for s in out.sessions)
    assert db.execute(select(func.count()).select_from(Concurso)).scalar() == 0
    assert db.execute(select(func.count()).select_from(ConcursoVersion)).scalar() == 0
    assert db.execute(select(func.count()).select_from(Notification)).scalar() == 0
    db.close()


def test_anchor_programming_error_does_not_trigger_request(doubles, monkeypatch):
    FakeSolari.reset({"html": DETAIL_HTML, "doc_url": DOC_URL, "click_bytes": PDF})
    adapter = SolariBrowserAdapter(_config(), _settings())
    async def broken_anchor(*args):
        raise TypeError("invalid SDK invocation")
    monkeypatch.setattr(adapter, "_find_anchor", broken_anchor)
    adapter.open_detail("https://novo.ibgpconcursos.com.br/concurso.jsp?cod=42")
    try:
        with pytest.raises(TypeError):
            adapter.download(DOC_URL, max_bytes=10_000)
        assert not FakeSolari.script.get("requested_urls")
    finally:
        adapter.close()


def test_allowed_redirect_is_followed_explicitly(doubles):
    destination = "https://novo.ibgpconcursos.com.br/f/edital-final.pdf"
    FakeSolari.reset({
        "html": DETAIL_HTML, "doc_url": DOC_URL, "no_anchor_for_download": True,
        "request": {"body": PDF, "final_url": destination},
    })
    adapter = SolariBrowserAdapter(_config(), _settings())
    adapter.open_detail("https://novo.ibgpconcursos.com.br/concurso.jsp?cod=42")
    try:
        downloaded = adapter.download(DOC_URL, max_bytes=10_000)
        assert downloaded.redirect_chain == [DOC_URL, destination]
        assert FakeSolari.script["requested_urls"] == [DOC_URL, destination]
    finally:
        adapter.close()


@pytest.mark.parametrize("status", [200, 302])
def test_click_route_never_follows_redirect_automatically(status):
    class Route:
        request = FakeAPIRequest(DOC_URL)
        aborted = False
        fulfilled = False
        response = FakeAPIResponse(DOC_URL, status=status, body=PDF)
        async def fetch(self, *, max_redirects, timeout):
            assert max_redirects == 0
            return self.response
        async def abort(self):
            self.aborted = True
        async def fulfill(self, **kwargs):
            self.fulfilled = True
    context = FakeContext({})
    adapter = SolariBrowserAdapter(_config(), _settings())
    route = Route()
    async def check():
        async with adapter._route_guard(context):
            await context._routes[0][1](route)
    asyncio.run(check())
    assert route.aborted is (status == 302)
    assert route.fulfilled is (status == 200)
    assert route.response.disposed


@pytest.mark.parametrize("method", ["open_listing", "open_detail"])
def test_navigation_invalid_initial_host_is_rejected_before_paid_session(doubles, method):
    FakeSolari.reset({})
    adapter = SolariBrowserAdapter(_config(), _settings())
    try:
        with pytest.raises(DestinationBlocked):
            getattr(adapter, method)("https://unregistered.example/concurso.jsp?cod=42")
        assert not FakeBrowser.instances
        assert not FakeSolari.instances
    finally:
        adapter.close()


@pytest.mark.parametrize("destination", [
    "https://portal.imeso.com.br/edital/ver/43",
    "https://unregistered.example/edital/ver/42",
    "http://127.0.0.1/edital/ver/42",
])
def test_detail_redirect_different_contest_or_host_never_reaches_destination(doubles, destination):
    requested = "https://portal.imeso.com.br/edital/ver/42"
    FakeSolari.reset({"html": "<p>Concurso 42</p>", "navigation_responses": {
        requested: {"status": 302, "headers": {"location": destination}},
    }})
    adapter = SolariBrowserAdapter(_config(), _settings(), source="imeso_open")
    try:
        with pytest.raises((ValueError, DestinationBlocked)):
            adapter.open_detail(requested)
        assert FakeSolari.script["navigation_requested_urls"] == [requested]
        assert FakeSolari.script["goto_urls"] == [requested]
        assert FakeBrowser.instances[0].close_calls >= 1
        assert adapter.session_records()[0].closed
    finally:
        adapter.close()


def test_browser_detail_follows_allowed_same_contest_redirect_as_new_guarded_navigation(doubles):
    requested = "https://portal.imeso.com.br/edital/ver/42"
    destination = requested + "/"
    FakeSolari.reset({"html": "<p>Concurso 42</p>", "navigation_responses": {
        requested: {"status": 301, "headers": {"location": destination}},
    }})
    adapter = SolariBrowserAdapter(_config(), _settings(), source="imeso_open")
    try:
        assert adapter.open_detail(requested) == "<p>Concurso 42</p>"
        assert FakeSolari.script["navigation_requested_urls"] == [requested, destination]
        assert FakeSolari.script["goto_urls"] == [requested, destination]
        assert adapter._live["page"].url == destination
    finally:
        adapter.close()
    assert FakeBrowser.instances[0].close_calls == 1
    assert adapter.session_records()[0].closed


def test_browser_final_url_is_revalidated_even_when_html_matches_requested_contest(doubles):
    requested = "https://novo.ibgpconcursos.com.br/concurso.jsp?cod=42"
    FakeSolari.reset({"html": DETAIL_HTML,
                      "page_final_url": "https://novo.ibgpconcursos.com.br/concurso.jsp?cod=43"})
    adapter = SolariBrowserAdapter(_config(), _settings())
    try:
        with pytest.raises(ValueError, match="identidade"):
            adapter.open_detail(requested)
        assert FakeBrowser.instances[0].close_calls >= 1
        assert adapter.session_records()[0].closed
    finally:
        adapter.close()


def test_listing_redirect_cannot_attach_another_tab_to_the_requested_url(doubles):
    requested = "https://novo.ibgpconcursos.com.br/inscricoes_abertas.jsp"
    FakeSolari.reset({"html": LISTING_HTML, "navigation_responses": {
        requested: {"status": 302, "headers": {"location": "https://novo.ibgpconcursos.com.br/index.jsp"}},
    }})
    adapter = SolariBrowserAdapter(_config(), _settings())
    try:
        with pytest.raises(ValueError, match="listagem"):
            adapter.open_listing(requested)
        assert FakeSolari.script["navigation_requested_urls"] == [requested]
        assert FakeBrowser.instances[0].close_calls >= 1
        assert adapter.session_records()[0].closed
    finally:
        adapter.close()


def test_asset_redirect_hops_are_checked_without_automatic_following(doubles):
    requested = "https://novo.ibgpconcursos.com.br/inscricoes_abertas.jsp"
    asset = "https://novo.ibgpconcursos.com.br/app.js"
    trusted = "https://cdn.imeso.com.br/shared.js"
    blocked = "http://127.0.0.1/internal.js"
    FakeSolari.reset({"html": LISTING_HTML, "navigation_assets": [asset], "navigation_responses": {
        asset: {"status": 302, "headers": {"location": trusted}},
        trusted: {"status": 302, "headers": {"location": blocked}},
    }})
    adapter = SolariBrowserAdapter(_config(), _settings())
    try:
        assert adapter.open_listing(requested) == LISTING_HTML
        assert FakeSolari.script["navigation_requested_urls"] == [requested, asset, trusted]
        assert any("requisição bloqueada" in note for note in adapter.diagnostics())
    finally:
        adapter.close()


def test_detail_navigation_guard_remains_until_download_and_close(doubles):
    requested = "https://novo.ibgpconcursos.com.br/concurso.jsp?cod=42"
    FakeSolari.reset({"html": DETAIL_HTML, "doc_url": DOC_URL, "click_bytes": PDF})
    adapter = SolariBrowserAdapter(_config(), _settings())
    try:
        adapter.open_detail(requested)
        page = adapter._live["page"]
        assert page.context._routes
        page.url = "https://novo.ibgpconcursos.com.br/concurso.jsp?cod=43"
        with pytest.raises(ValueError, match="identidade"):
            adapter.download(DOC_URL, max_bytes=10_000)
        assert not FakeSolari.script.get("requested_urls")
    finally:
        adapter.close()
    assert not page.context._routes


@pytest.mark.parametrize("status", [302, 404])
def test_navigation_redirect_loop_or_http_error_is_not_accepted_as_content(doubles, status):
    requested = "https://novo.ibgpconcursos.com.br/concurso.jsp?cod=42"
    FakeSolari.reset({"html": DETAIL_HTML, "navigation_responses": {
        requested: {"status": status, "headers": {"location": requested}},
    }})
    adapter = SolariBrowserAdapter(_config(), _settings())
    try:
        with pytest.raises(ValueError):
            adapter.open_detail(requested)
        assert FakeSolari.script["navigation_requested_urls"] == [requested]
        assert FakeBrowser.instances[0].close_calls >= 1
    finally:
        adapter.close()


@pytest.mark.parametrize("method,url", [
    ("open_listing", "https://novo.ibgpconcursos.com.br/inscricoes_abertas.jsp"),
    ("open_detail", "https://novo.ibgpconcursos.com.br/concurso.jsp?cod=42"),
])
def test_session_observer_reports_creating_before_launch_and_id_after_cleanup_registration(doubles, method, url):
    FakeSolari.reset({"html": DETAIL_HTML})
    events = []
    def observe(event, session_id):
        events.append((event, session_id))
        if event == "creating":
            assert not FakeBrowser.instances
            assert session_id is None
        elif event == "created":
            assert adapter._cancel_state["browser"].id == session_id
            assert adapter.session_id == session_id
        else:
            assert event == "closed"
            assert any(record.session_id == session_id and record.closed for record in adapter.session_records())
    adapter = SolariBrowserAdapter(_config(), _settings(), session_observer=observe)
    try:
        getattr(adapter, method)(url)
        assert events[:2] == [("creating", None), ("created", "sess-real-1")]
    finally:
        adapter.close()
    assert events == [("creating", None), ("created", "sess-real-1"), ("closed", "sess-real-1")]
    assert FakeBrowser.instances[0].close_calls == 1


@pytest.mark.parametrize("event_to_fail", ["creating", "created"])
@pytest.mark.parametrize("method,url", [
    ("open_listing", "https://novo.ibgpconcursos.com.br/inscricoes_abertas.jsp"),
    ("open_detail", "https://novo.ibgpconcursos.com.br/concurso.jsp?cod=42"),
])
def test_session_observer_failure_prevents_acquisition_and_closes_allocated_resources(doubles, event_to_fail, method, url):
    FakeSolari.reset({"html": DETAIL_HTML})
    def observe(event, session_id):
        if event == event_to_fail:
            raise RuntimeError("journal persistence failed")
    adapter = SolariBrowserAdapter(_config(), _settings(), session_observer=observe)
    try:
        with pytest.raises(RuntimeError, match="journal persistence failed"):
            getattr(adapter, method)(url)
        assert not FakeSolari.script.get("navigation_requested_urls")
        assert FakeSolari.instances[0].exit_calls >= 1
        if event_to_fail == "creating":
            assert not FakeBrowser.instances
        else:
            assert FakeBrowser.instances[0].close_calls >= 1
            assert adapter.session_records()[0].closed
    finally:
        adapter.close()


@pytest.mark.parametrize("method,url", [
    ("open_listing", "https://novo.ibgpconcursos.com.br/inscricoes_abertas.jsp"),
    ("open_detail", "https://novo.ibgpconcursos.com.br/concurso.jsp?cod=42"),
])
def test_closed_event_requires_positive_remote_confirmation(doubles, monkeypatch, method, url):
    FakeSolari.reset({"html": DETAIL_HTML})
    async def unconfirmed(*args, **kwargs):
        return False
    monkeypatch.setattr(adapter_mod, "confirm_browser_released", unconfirmed)
    events = []
    adapter = SolariBrowserAdapter(_config(), _settings(), session_observer=lambda event, sid: events.append((event, sid)))
    try:
        getattr(adapter, method)(url)
    finally:
        adapter.close()
    assert events == [("creating", None), ("created", "sess-real-1")]
    assert adapter.session_records()[0].closed is False


@pytest.mark.parametrize("method,url", [
    ("open_listing", "https://novo.ibgpconcursos.com.br/inscricoes_abertas.jsp"),
    ("open_detail", "https://novo.ibgpconcursos.com.br/concurso.jsp?cod=42"),
])
def test_closed_observer_failure_is_visible_and_cannot_skip_client_cleanup(doubles, method, url):
    FakeSolari.reset({"html": DETAIL_HTML})
    def observe(event, sid):
        if event == "closed":
            raise RuntimeError("journal could not record closure")
    adapter = SolariBrowserAdapter(_config(), _settings(), session_observer=observe)
    try:
        if method == "open_listing":
            with pytest.raises(RuntimeError, match="journal"):
                adapter.open_listing(url)
        else:
            adapter.open_detail(url)
    finally:
        adapter.close()
    assert FakeBrowser.instances[0].close_calls >= 1
    assert FakeSolari.instances[0].exit_calls >= 1
    assert adapter.session_records()[0].closed
    assert any("journal: fechamento remoto confirmado, mas persistência falhou" in note for note in adapter.diagnostics())


def test_paid_client_uses_one_attempt_bounded_timeout_and_no_launch_retries(doubles):
    FakeSolari.reset({"html": DETAIL_HTML})
    adapter = SolariBrowserAdapter(_config(), _settings())
    try:
        adapter.open_detail("https://novo.ibgpconcursos.com.br/concurso.jsp?cod=42")
        allocation_client = FakeSolari.instances[0]
        assert allocation_client._max_attempts == 1
        assert allocation_client._timeout_s == 30
        assert FakeSolari.script["launch_kwargs"]["retries"] == 0
    finally:
        adapter.close()


def test_real_sdk_does_not_repeat_session_post_after_an_uncertain_response(monkeypatch):
    import httpx
    from solari_browser.client import Solari
    from solari_browser.errors import SolariError
    monkeypatch.setattr(adapter_mod, "_get_solari_class", lambda: Solari)
    attempts = []
    async def allocated_but_response_lost(request):
        attempts.append((request.method, request.url.path))
        raise httpx.ReadTimeout("fixture: allocation happened but response was lost")
    async def check():
        adapter = SolariBrowserAdapter(_config(), _settings())
        client = adapter._new_client()
        client._http = httpx.AsyncClient(transport=httpx.MockTransport(allocated_but_response_lost))
        try:
            with pytest.raises(SolariError, match="exhausted 1 attempts"):
                await client.sessions.create()
            assert attempts == [("POST", "/sessions")]
            assert client._timeout_s == 30
        finally:
            await client.close()
            adapter.close()
    asyncio.run(check())


@pytest.mark.parametrize("kind", ["navigation", "download"])
@pytest.mark.parametrize("error_kind", ["closed", "cancelled"])
def test_late_response_disposal_after_handler_shutdown_has_no_listener_error(kind, error_kind):
    from patchright._impl._errors import TargetClosedError
    requested = "https://novo.ibgpconcursos.com.br/concurso.jsp?cod=42"
    adapter = SolariBrowserAdapter(_config(), _settings())
    async def check():
        entered_dispose = asyncio.Event()
        release_dispose = asyncio.Event()
        page = FakePage({}, None)
        class Response(FakeAPIResponse):
            async def dispose(self):
                entered_dispose.set()
                await release_dispose.wait()
                if error_kind == "closed":
                    raise TargetClosedError()
                raise asyncio.CancelledError()
        class Route(FakeNavigationRoute):
            async def fetch(self, *, url=None, max_redirects, timeout):
                assert max_redirects == 0
                return Response(requested, body=PDF)
        route = Route(requested, page)
        guard = adapter._navigation_guard(page, requested, phase="detail") if kind == "navigation" else adapter._route_guard(page.context)
        async with guard:
            task = asyncio.create_task(page.context._routes[-1][1](route))
            await asyncio.wait_for(entered_dispose.wait(), timeout=1)
        # The callback is confirmed live at response.dispose while its handler
        # is removed; this models the delayed callback seen after browser close.
        assert not task.done()
        release_dispose.set()
        await asyncio.wait_for(task, timeout=1)
        assert task.exception() is None
        assert route.fulfilled
        assert not adapter.diagnostics()
    try:
        asyncio.run(check())
    finally:
        adapter.close()


@pytest.mark.parametrize("stopping,error_kind", [(False, "closed"), (False, "cancelled"), (True, "unexpected")])
def test_cleanup_only_swallows_expected_shutdown_exceptions(stopping, error_kind):
    from patchright._impl._errors import TargetClosedError
    adapter = SolariBrowserAdapter(_config(), _settings())
    error = {"closed": TargetClosedError, "cancelled": asyncio.CancelledError, "unexpected": RuntimeError}[error_kind]
    async def broken_cleanup():
        raise error("fixture cleanup problem")
    async def check():
        with pytest.raises(error):
            await adapter._cleanup_browser_call(broken_cleanup, stopping=stopping)
    try:
        asyncio.run(check())
    finally:
        adapter.close()


def test_expected_abort_cleanup_does_not_hide_real_navigation_rejection():
    from patchright._impl._errors import TargetClosedError
    requested = "https://novo.ibgpconcursos.com.br/concurso.jsp?cod=42"
    adapter = SolariBrowserAdapter(_config(), _settings())
    async def check():
        page = FakePage({}, None)
        guard = adapter._navigation_guard(page, requested, phase="detail")
        class Route(FakeNavigationRoute):
            async def abort(self):
                raise TargetClosedError()
            async def fetch(self, **kwargs):
                pytest.fail("blocked destination must never be fetched")
        async with guard:
            handler = page.context._routes[-1][1]
        await handler(Route("http://127.0.0.1/private", page))
        with pytest.raises(DestinationBlocked):
            guard.check()
    try:
        asyncio.run(check())
    finally:
        adapter.close()


def test_unexpected_unroute_error_remains_visible_and_client_is_still_closed(doubles, monkeypatch):
    FakeSolari.reset({"html": DETAIL_HTML})
    adapter = SolariBrowserAdapter(_config(), _settings())
    adapter.open_detail("https://novo.ibgpconcursos.com.br/concurso.jsp?cod=42")
    context = adapter._live["page"].context
    async def broken_unroute(*args, **kwargs):
        raise RuntimeError("fixture unexpected unroute failure")
    monkeypatch.setattr(context, "unroute", broken_unroute)
    adapter.close()
    assert FakeSolari.instances[0].exit_calls >= 1
    assert any("unexpected unroute failure" in note for note in adapter.diagnostics())
