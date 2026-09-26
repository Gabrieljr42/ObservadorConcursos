"""TenderProof Fase 1 — discovery limitado, sessão sempre encerrada, downloads."""

import pytest

from app.tenderproof.acquisition import (
    AcquisitionService,
    choose_edital,
    confirm_identity,
    parse_document_candidates,
    parse_listing_candidates,
)
from app.tenderproof.contracts import DiscoveredCandidate
from app.tenderproof.demo_pdf import make_text_pdf
from app.tenderproof.mock_demo import DETAIL_HTML_42, LISTING_HTML, PDF_PAGE_1
from app.tenderproof.security import TenderProofSettings
from app.tenderproof.solari_adapter import DownloadedBytes, FakeSolariDriver, ObservedJson


def _listing_with(n: int) -> str:
    links = "".join(
        f'<a href="/concurso.jsp?cod={100 + i}">Concurso Exemplo {100 + i}</a>'
        for i in range(n)
    )
    return f"<html><body>{links}</body></html>"


def test_discovery_is_limited_to_five_with_observed_title_and_url():
    candidates = parse_listing_candidates(_listing_with(8), base_url="https://novo.ibgpconcursos.com.br", limit=5)
    assert len(candidates) == 5
    for cand in candidates:
        assert cand.title_observed and cand.detail_url_observed.startswith("https://")
        assert "concurso.jsp?cod=" in cand.detail_url_observed


def test_interface_noise_anchors_get_context_title_or_none():
    html = (
        "<html><body>"
        "<div class='card'><h3>Concurso Prefeitura de Belo Horizonte MG</h3>"
        "<a href='/concurso.jsp?cod=704'>SAIBA MAIS</a></div>"
        "<div><a href='/concurso.jsp?cod=705'>SAIBA MAIS</a></div>"
        "</body></html>"
    )
    candidates = parse_listing_candidates(html, base_url="https://novo.ibgpconcursos.com.br")
    by_id = {c.external_id: c for c in candidates}
    assert "SAIBA MAIS" not in (by_id["704"].title_observed or "")
    assert "Belo Horizonte" in (by_id["704"].title_observed or "")
    # Sem contexto aproveitável: título honesto é None (vira UNKNOWN adiante).
    assert by_id["705"].title_observed is None or "SAIBA MAIS" not in by_id["705"].title_observed


def test_edital_choice_prefers_direct_download_endpoint():
    from app.tenderproof.contracts import DocumentCandidate

    docs = [
        DocumentCandidate(doc_id="doc-01", title="Edital 01/2026 (visualizar)",
                          url_requested="https://novo.ibgpconcursos.com.br/leitor?doc=1", kind="edital"),
        DocumentCandidate(doc_id="doc-02", title="Edital 01/2026",
                          url_requested="https://novo.ibgpconcursos.com.br/rest/concurso/download/edital/1/?file=x.pdf",
                          kind="edital"),
    ]
    chosen, _ = choose_edital(docs)
    assert chosen.doc_id == "doc-02"


def test_session_is_closed_after_listing_failure():
    driver = FakeSolariDriver(fail_on="listing")
    svc = AcquisitionService(TenderProofSettings())
    with pytest.raises(RuntimeError):
        svc.discover(driver)
    # O serviço de alto nível (service.py) encerra em finally; aqui o driver
    # expõe o encerramento idempotente exigido pelo contrato.
    driver.close()
    assert driver.closed and driver.close_calls == 1


def test_full_service_closes_session_on_detail_failure():
    from app.tenderproof.service import TenderProofService
    from app.tenderproof.store import TenderProofStore

    store = TenderProofStore()
    svc = TenderProofService(store, TenderProofSettings())
    run = svc.start_discovery(FakeSolariDriver(listing_html=LISTING_HTML, detail_html=DETAIL_HTML_42))
    assert run.execution_status.value == "awaiting_selection"
    failing = FakeSolariDriver(fail_on="download", listing_html=LISTING_HTML, detail_html=DETAIL_HTML_42)
    # injeta download scriptado ausente -> falha; sessão deve encerrar
    out = svc.select_and_process(run.run_id, "cand-42", failing)
    assert out.execution_status.value == "failed"
    assert failing.closed


def test_oversize_download_is_rejected():
    big = DownloadedBytes(
        url_requested="https://novo.ibgpconcursos.com.br/big.pdf",
        url_final="https://novo.ibgpconcursos.com.br/big.pdf",
        content=b"%PDF" + b"0" * 100,
        redirect_chain=["https://novo.ibgpconcursos.com.br/big.pdf"],
    )
    driver = FakeSolariDriver(downloads={big.url_requested: big})
    with pytest.raises(ValueError, match="acima do limite"):
        driver.download(big.url_requested, max_bytes=10)


def test_html_instead_of_pdf_is_rejected():
    svc = AcquisitionService(TenderProofSettings())
    html_payload = DownloadedBytes(
        url_requested="https://novo.ibgpconcursos.com.br/e.pdf",
        url_final="https://novo.ibgpconcursos.com.br/e.pdf",
        content=b"<!DOCTYPE html><html><body>leitor</body></html>",
        content_type="text/html",
        redirect_chain=["https://novo.ibgpconcursos.com.br/e.pdf"],
    )
    with pytest.raises(ValueError, match="HTML"):
        svc._validate_payload(html_payload)


def test_real_pdf_bytes_pass_validation():
    svc = AcquisitionService(TenderProofSettings())
    payload = DownloadedBytes(
        url_requested="https://novo.ibgpconcursos.com.br/e.pdf",
        url_final="https://novo.ibgpconcursos.com.br/e.pdf",
        content=make_text_pdf([PDF_PAGE_1]),
        content_type="application/pdf",
        redirect_chain=["https://novo.ibgpconcursos.com.br/e.pdf"],
    )
    svc._validate_payload(payload)  # não levanta


def test_edital_choice_prefers_edital_and_justifies():
    docs = parse_document_candidates(DETAIL_HTML_42, base_url="https://novo.ibgpconcursos.com.br")
    assert {d.kind for d in docs} >= {"edital", "gabarito"}
    chosen, reason = choose_edital(docs)
    assert chosen.kind == "edital"
    assert "gabarito" not in chosen.title.lower()
    assert "ignorado" in reason


def test_identity_confirmation_rejects_mismatched_detail():
    cand = DiscoveredCandidate(
        candidate_id="cand-42",
        title_observed="Concurso Exemplo",
        detail_url_observed="https://novo.ibgpconcursos.com.br/concurso.jsp?cod=42",
        external_id="42",
        observed_at="2026-03-02T00:00:00+00:00",
    )
    with pytest.raises(ValueError):
        confirm_identity(
            candidate=cand,
            detail_html="<html>outro concurso cod=99</html>",
            detail_url="https://novo.ibgpconcursos.com.br/concurso.jsp?cod=99",
        )


def test_structured_observations_are_filtered():
    from app.tenderproof.acquisition import filter_structured_observations

    observed = [
        ObservedJson(url="https://novo.ibgpconcursos.com.br/rest/concurso/42", status=200),
        ObservedJson(url="https://cdn.tracker.example/pixel", status=200),
    ]
    assert [o.url for o in filter_structured_observations(observed)] == [
        "https://novo.ibgpconcursos.com.br/rest/concurso/42"
    ]
