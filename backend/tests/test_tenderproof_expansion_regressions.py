"""Adversarial regressions found while extending the demo to continuous work."""
import httpx
import pytest

from app.tenderproof.contracts import DocumentCandidate, ExecutionStatus, SessionRecord, TenderProofRun
from app.tenderproof.http_driver import BoundedHTTPDriver, ContinuousDriver
from app.tenderproof.mock_demo import build_mock_driver
from app.tenderproof.service import TenderProofService
from app.tenderproof.source_adapters import get_source_adapter
from app.tenderproof.source_parsers import choose_edital
from app.tenderproof.store import TenderProofStore


@pytest.mark.parametrize("container", [
    '<template>{}</template>', '<p hidden>{}</p>', '<p aria-hidden="true">{}</p>',
    '<p style="display: none">{}</p>', '<p class="d-none">{}</p>', '<script>{}</script>',
])
def test_invisible_empty_markers_cannot_certify_empty_listing(container):
    adapter = get_source_adapter("ibgp_open")
    page = adapter.parse_listing("<main>" + container.format("Nenhum concurso disponível.") + "</main>", adapter.listing_urls[0])
    assert page.empty_evidence is None and page.terminal_evidence is None


def test_unrelated_footer_pagination_does_not_certify_contest_coverage():
    adapter = get_source_adapter("ibgp_open")
    html = '<main><a href="/concurso.jsp?cod=42">Concurso Exemplo</a></main>'
    html += '<footer><p>Mostrando 1 a 1 de 1</p><div class="pagination"><a class="next disabled">Próxima notícia</a></div></footer>'
    assert adapter.parse_listing(html, adapter.listing_urls[0]).terminal_evidence is None


def test_titleless_candidate_requires_its_exact_code_in_detail():
    adapter = get_source_adapter("ibgp_open")
    candidate = adapter.candidate_from_url("https://novo.ibgpconcursos.com.br/concurso.jsp?cod=42")
    for html in ("<p>Outro concurso</p>", "<p>cod=420</p>"):
        with pytest.raises(ValueError, match="não confirmada"):
            adapter.confirm_identity(candidate, html, candidate.detail_url_observed)
    adapter.confirm_identity(candidate, "<p>cod=42</p>", candidate.detail_url_observed)


def test_direct_endpoint_cannot_hide_another_principal_edital():
    docs = [DocumentCandidate(doc_id="1", kind="edital", title="Edital 01", url_requested="https://novo.ibgpconcursos.com.br/rest/concurso/download/edital/1/"),
            DocumentCandidate(doc_id="2", kind="edital", title="Edital 02", url_requested="https://novo.ibgpconcursos.com.br/edital02.pdf")]
    with pytest.raises(ValueError, match="ambíguos"):
        choose_edital(docs)


def test_slow_transport_enforces_total_deadline_before_buffer_fills(monkeypatch):
    clock, yielded = [0.0], []
    monkeypatch.setattr("app.tenderproof.http_driver.time.monotonic", lambda: clock[0])
    monkeypatch.setattr("app.tenderproof.http_driver._public_dns", lambda host: None)
    class SlowStream(httpx.SyncByteStream):
        def __iter__(self):
            for index in range(100):
                clock[0] += 0.6
                yielded.append(index)
                yield b"x"
    client = httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(200, stream=SlowStream())))
    driver = BoundedHTTPDriver("ibgp_open", client=client)
    driver.deadline = 1.0
    with pytest.raises(TimeoutError):
        driver.open_listing(driver.adapter.listing_urls[0])
    assert yielded == [0, 1]
    driver.close()


def test_navigation_only_shell_still_uses_authorized_browser(monkeypatch):
    driver = ContinuousDriver("ibgp_open", allow_browser=True)
    shell = '<a href="/inscricoes_encerradas.jsp">Encerrados</a>'
    rendered = '<a href="/concurso.jsp?cod=42">Concurso Exemplo</a>'
    monkeypatch.setattr(driver.http, "open_listing", lambda url: shell)
    class Browser:
        def open_listing(self, url): return rendered
    monkeypatch.setattr(driver, "_fallback", lambda reason: Browser())
    assert driver.open_listing(driver.http.adapter.listing_urls[0]) == rendered
    driver.close()


def test_close_exception_on_consumed_run_does_not_keep_global_lease():
    store = TenderProofStore()
    service = TenderProofService(store)
    run = service.start_discovery(build_mock_driver(), is_synthetic=True)
    run.execution_status = ExecutionStatus.COMPLETED
    store.put_run(run)
    driver = build_mock_driver()
    def broken_close(): raise RuntimeError("close failed")
    driver.close = broken_close
    with pytest.raises(RuntimeError, match="close failed"):
        service.select_and_process(run.run_id, "cand-42", driver)
    token = store.acquire_execution_lease()
    assert token is not None
    store.release_execution_lease(token)


def test_browser_closed_and_artifact_durable_before_pdf_processing(monkeypatch):
    store = TenderProofStore()
    service = TenderProofService(store)
    run = service.start_discovery(build_mock_driver(), is_synthetic=True)
    driver = build_mock_driver()
    reached = []
    def processing(*args, **kwargs):
        persisted = store.get_run(run.run_id)
        assert driver.closed
        assert persisted.artifact and store.load_artifact_bytes(persisted.artifact).startswith(b"%PDF")
        reached.append(True)
        raise RuntimeError("simulated parser failure")
    monkeypatch.setattr("app.tenderproof.service.extract_pages_isolated", processing)
    result = service.select_and_process(run.run_id, "cand-42", driver)
    assert reached == [True] and result.execution_status == ExecutionStatus.FAILED


def test_replay_refresh_cannot_overwrite_concurrently_completed_acquisition(monkeypatch):
    from app.tenderproof.solari_adapter import SolariConfig
    store = TenderProofStore()
    run = TenderProofRun(run_id="replay-race", mode="real", execution_status=ExecutionStatus.PROCESSING,
                        sessions=[SessionRecord(phase="detail", session_id="session-1")])
    store.put_run(run)
    monkeypatch.setattr(SolariConfig, "from_env", lambda: SolariConfig(api_key="test-only"))
    async def poll(*args, **kwargs):
        completed = store.get_run(run.run_id)
        completed.execution_status = ExecutionStatus.COMPLETED
        completed.semantic_hash = "completed-new-result"
        store.put_run(completed)
        return "available", "https://replay.example/session-1", "ready"
    monkeypatch.setattr("app.tenderproof.solari_adapter.poll_replay_url", poll)
    result = TenderProofService(store).refresh_replay(run.run_id)
    assert result.execution_status == ExecutionStatus.COMPLETED
    assert result.semantic_hash == "completed-new-result" and result.replay_available
