"""Independent navigation and identity examples for the common adapter contract."""
import httpx
import pytest
import json

from app.tenderproof.acquisition import AcquisitionService
from app.tenderproof.http_driver import BoundedHTTPDriver, ContinuousDriver
from app.tenderproof.security import DestinationBlocked, TenderProofSettings
from app.tenderproof.solari_adapter import FakeSolariDriver
from app.tenderproof.source_adapters import get_source_adapter, SourcePageBlocked


def test_continuous_acquisition_preserves_observed_candidate_title(monkeypatch):
    monkeypatch.setattr('app.tenderproof.http_driver._public_dns',lambda host:None)
    adapter=get_source_adapter('cebraspe_open')
    candidate=adapter.candidate_from_url(adapter.api+'/XYZ_29','XY Z 29')
    settings=TenderProofSettings(allowlist_hosts=adapter.allowed_hosts)
    driver=ContinuousDriver(candidate.source,settings)
    driver.http.client.close()
    row={'eventoURL':'XYZ_29','eventoTipo':'concursos','eventoNomeAbreviado':'XY Z 29',
         'arquivosEdital':[{'tipoExtensaoArquivo':'_.pdf','isGuid':False,
                           'nomeArquivo':'abertura.pdf','descricaoArquivo':'Edital de abertura'}]}
    driver.http.client=httpx.Client(transport=httpx.MockTransport(lambda req:
        httpx.Response(200,content=b'%PDF-1.7\n' if req.url.path.endswith('.pdf') else json.dumps(row).encode())))
    try:
        selected,_,_=AcquisitionService(settings).select_and_fetch(driver,candidate=candidate)
        assert selected.kind=='edital'
        assert driver.http.candidate.title_observed=='XY Z 29'
        with pytest.raises(ValueError):
            driver.set_candidate(candidate.model_copy(update={'external_id':'XYZ_28'}))
    finally:
        driver.close()


def test_section_driver_rebuilds_identity_from_observed_title_and_rejects_id_swap():
    adapter = get_source_adapter('fapese_selection')
    html = open('tests/fixtures/tenderproof_batch99_foundations/fapese_selection-cycle1-detail-197909cd7ff1.html', encoding='utf-8').read()
    candidate = adapter.parse_listing(html, adapter.listing_urls[0]).candidates[0]
    driver = BoundedHTTPDriver(candidate.source, TenderProofSettings(allowlist_hosts=adapter.allowed_hosts))
    try:
        driver.set_candidate(candidate)
        with pytest.raises(ValueError, match='incompatível'):
            driver.set_candidate(candidate.model_copy(update={'external_id': '008/2026'}))
    finally:
        driver.close()


def ibgp_links(n=7):
    return "".join(f'<a href="/concurso.jsp?cod={i}">Concurso Município Exemplo {i}</a>' for i in range(1, n+1))


def imeso_links(n=7):
    return "".join(f'<div class="row"><p>Prefeitura Exemplo {i}</p><a href="/edital/ver/{i}">Detalhes</a></div>' for i in range(1, n+1))


@pytest.mark.parametrize("source,make_links", [("ibgp_open", ibgp_links), ("imeso_open", imeso_links)])
def test_full_page_contract_exceeds_demo_sample_and_reports_truncation(source, make_links):
    adapter = get_source_adapter(source)
    url = adapter.listing_urls[0]
    page = adapter.parse_listing(make_links(), url, 200)
    assert len(page.candidates) == 7
    assert {c.source for c in page.candidates} == {source}
    assert not page.truncated
    limited = adapter.parse_listing(make_links(), url, 3)
    assert len(limited.candidates) == 3 and limited.truncated
    assert limited.terminal_evidence is None


def test_navigation_retains_observed_pages_tabs_but_never_foreign_or_invented_urls():
    adapter = get_source_adapter("ibgp_open")
    url = adapter.listing_urls[0]
    html = ibgp_links() + '''<nav><a href="?page=2" rel="next">Próxima</a>
        <a href="/index.jsp">Concursos</a>
        <a href="https://evil.test/inscricoes_abertas.jsp?page=3">Próxima</a>
        <a href="?callback=exec">Outro</a></nav>'''
    page = adapter.parse_listing(html, url)
    assert page.next_urls == [url + "?page=2", "https://novo.ibgpconcursos.com.br/index.jsp"]
    assert page.terminal_evidence is None
    assert adapter.parse_listing(ibgp_links(), url).next_urls == []
    # Link absence is explicitly insufficient to assert complete coverage.
    assert adapter.parse_listing(ibgp_links(), url).terminal_evidence is None


def test_foreign_contest_link_is_not_rewritten_into_an_official_candidate():
    adapter = get_source_adapter("ibgp_open")
    page = adapter.parse_listing('<a href="https://evil.test/concurso.jsp?cod=42">Concurso</a>', adapter.listing_urls[0])
    assert page.candidates == []
    assert page.empty_evidence is None


@pytest.mark.parametrize("source,phrase", [("ibgp_open", "Nenhum concurso com inscrições abertas."), ("imeso_open", "Nenhum edital encontrado.")])
def test_empty_requires_source_marker_and_challenge_never_counts_as_empty(source, phrase):
    adapter = get_source_adapter(source)
    url = adapter.listing_urls[0]
    page = adapter.parse_listing(f"<main><p>{phrase}</p></main>", url)
    assert page.empty_evidence == phrase and page.terminal_evidence
    assert not adapter.parse_listing("<main><p>Sem resultados</p></main>", url).empty_evidence
    with pytest.raises(SourcePageBlocked):
        adapter.parse_listing(f"<h1>Just a moment</h1><main><p>{phrase}</p></main>", url)


def test_explicit_range_corroborates_observed_count_and_limit_wins():
    adapter = get_source_adapter("ibgp_open")
    url = adapter.listing_urls[0]
    html = ibgp_links(3) + "<p>Mostrando 8 a 10 de 10</p>"
    assert adapter.parse_listing(html, url).terminal_evidence
    assert not adapter.parse_listing(html, url, 2).terminal_evidence
    assert not adapter.parse_listing(ibgp_links(1) + "<p>Mostrando 8 a 10 de 10</p>", url).terminal_evidence


def test_unregistered_source_and_cross_source_identity_are_rejected():
    with pytest.raises(ValueError, match="não suportada"):
        get_source_adapter("unregistered_test_source")
    ibgp, imeso = get_source_adapter("ibgp_open"), get_source_adapter("imeso_open")
    candidate = imeso.candidate_from_url("https://portal.imeso.com.br/edital/ver/42")
    with pytest.raises((ValueError, DestinationBlocked)):
        ibgp.confirm_identity(candidate, "cod=42", candidate.detail_url_observed)


def test_document_limit_does_not_hide_a_second_main_edital():
    adapter = get_source_adapter("ibgp_open")
    candidate = adapter.candidate_from_url("https://novo.ibgpconcursos.com.br/concurso.jsp?cod=42")
    html = "<p>cod=42</p>" + "".join(f'<a href="/e{i}.pdf">Edital {i}</a>' for i in range(11))
    driver = FakeSolariDriver(detail_html=html)
    with pytest.raises(ValueError, match="excedem o limite"):
        AcquisitionService().select_and_fetch(driver, candidate=candidate)


def http_driver(monkeypatch, source, handler):
    monkeypatch.setattr("app.tenderproof.http_driver._public_dns", lambda host: None)
    return BoundedHTTPDriver(source, client=httpx.Client(transport=httpx.MockTransport(handler)))


def test_http_redirect_is_rejected_before_request_to_unregistered_destination(monkeypatch):
    visited = []
    def handler(request):
        visited.append(str(request.url))
        return httpx.Response(302, headers={"location": "http://127.0.0.1/secrets"})
    driver = http_driver(monkeypatch, "ibgp_open", handler)
    with pytest.raises((DestinationBlocked, ValueError)):
        driver.open_listing(driver.adapter.listing_urls[0])
    assert visited == [driver.adapter.listing_urls[0]]
    driver.close()


def test_http_document_redirect_cannot_change_imeso_contest(monkeypatch):
    visited = []
    def handler(request):
        visited.append(str(request.url))
        if "/edital/ver/42" in str(request.url):
            return httpx.Response(200, text="<p>Concurso 42</p>")
        return httpx.Response(302, headers={"location": "https://cdn.imeso.com.br/edital/1/43/edital.pdf"})
    driver = http_driver(monkeypatch, "imeso_open", handler)
    driver.open_detail("https://portal.imeso.com.br/edital/ver/42")
    with pytest.raises(ValueError, match="outro concurso"):
        driver.download("https://cdn.imeso.com.br/edital/1/42/edital.pdf", max_bytes=1000)
    assert len(visited) == 2 and "/43/" not in " ".join(visited)
    driver.close()


def test_http_limits_bytes_and_deadline(monkeypatch):
    driver = http_driver(monkeypatch, "ibgp_open", lambda request: httpx.Response(200, content=b"%PDF" + b"x" * 50))
    driver.candidate = driver.adapter.candidate_from_url("https://novo.ibgpconcursos.com.br/concurso.jsp?cod=42")
    with pytest.raises(ValueError, match="limite"):
        driver.download("https://novo.ibgpconcursos.com.br/e.pdf", max_bytes=10)
    driver.deadline = 0
    with pytest.raises(TimeoutError):
        driver.open_listing(driver.adapter.listing_urls[0])
    driver.close()


def test_continuous_driver_does_not_open_paid_browser_without_both_opt_ins(monkeypatch):
    created = []
    monkeypatch.setattr("app.tenderproof.http_driver.SolariBrowserAdapter", lambda *a, **k: created.append(True))
    monkeypatch.setenv("TENDERPROOF_BROWSER_LIVE_ENABLED", "false")
    driver = ContinuousDriver("ibgp_open", allow_browser=True)
    monkeypatch.setattr(driver.http, "open_listing", lambda url: "<main>Carregando...</main>")
    with pytest.raises(ValueError, match="não habilitado"):
        driver.open_listing(driver.http.adapter.listing_urls[0])
    driver.close()
    assert created == []


def test_http_success_never_creates_browser_even_when_authorized(monkeypatch):
    created = []
    monkeypatch.setattr("app.tenderproof.http_driver.SolariBrowserAdapter", lambda *a, **k: created.append(True))
    monkeypatch.setenv("TENDERPROOF_BROWSER_LIVE_ENABLED", "true")
    driver = ContinuousDriver("imeso_open", allow_browser=True)
    monkeypatch.setattr(driver.http, "open_listing", lambda url: imeso_links())
    assert imeso_links() == driver.open_listing(driver.http.adapter.listing_urls[0])
    assert driver.session_records() == []
    driver.close()
    assert created == []

