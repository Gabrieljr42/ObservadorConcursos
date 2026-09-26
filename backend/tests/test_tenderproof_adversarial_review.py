"""Independent adversarial review: synthetic inputs, expected fail-closed behavior."""
from datetime import datetime, timezone

import pytest

from app.tenderproof.acquisition import AcquisitionService, confirm_identity, parse_document_candidates, choose_edital
from app.tenderproof.contracts import DiscoveredCandidate, PageText, ValidationStatus, FieldState
from app.tenderproof.fields import extract_fields
from app.tenderproof.security import DestinationBlocked, validate_destination
from app.tenderproof.sources import IMESO_LISTING, build_imeso_mock_driver, imeso_candidates
from app.tenderproof.validation import validate_identity
from test_tenderproof_evidence import _artifact


def candidate(source="ibgp_open", title="PREFEITURA MUNICIPAL DE ALFA"):
    return DiscoveredCandidate(candidate_id="candidate-42", external_id="42", source=source,
        title_observed=title, observed_at=datetime.now(timezone.utc),
        detail_url_observed="https://portal.imeso.com.br/edital/ver/42" if source == "imeso_open"
        else "https://novo.ibgpconcursos.com.br/concurso.jsp?cod=42")


@pytest.mark.parametrize("text", [
    "Recurso contra indeferimento de inscrição de 10/03/2026 a 12/03/2026.",
    "Pedido de isenção da taxa de inscrição de 10/03/2026 a 12/03/2026.",
    "Pagamento da inscrição até 10/03/2026. Resultado das inscrições em 12/03/2026.",
])
def test_other_event_dates_not_supported_registration(text):
    fields = extract_fields(candidate=candidate(), artifact=_artifact(),
                            pages=[PageText(artifact_id="a", page_number=1, text=text)])
    for field in fields:
        if field.field_name in ("inscricao_inicio", "inscricao_fim"):
            assert field.state != FieldState.SUPPORTED


def test_imeso_pdf_explicit_other_contest_is_rejected():
    result = validate_identity(candidate=candidate("imeso_open"),
        pages=[PageText(artifact_id="a", page_number=1,
            text="PREFEITURA MUNICIPAL DE ALFA. EDITAL DE ABERTURA 01/2026. https://portal.imeso.com.br/edital/ver/999")],
        document_title="Edital de abertura", document_url="https://cdn.imeso.com.br/edital/1/42/edital.pdf")
    assert result.status == ValidationStatus.WRONG_CONTEST


@pytest.mark.parametrize("text", [
    "ANEXO I DO EDITAL 01/2026. PREFEITURA MUNICIPAL DE ALFA. Conteúdo programático cod=42",
    "GABARITO OFICIAL DO EDITAL 01/2026. PREFEITURA MUNICIPAL DE ALFA. cod=42",
])
def test_pdf_body_attachment_not_accepted_as_main_notice(text):
    result = validate_identity(candidate=candidate(), pages=[PageText(artifact_id="a", page_number=1,text=text)],
                               document_title="Edital", document_url="https://novo.ibgpconcursos.com.br/edital.pdf")
    assert result.status == ValidationStatus.NON_EDITAL


def test_ibgp_candidate_id_substring_is_not_identity():
    with pytest.raises(ValueError):
        confirm_identity(candidate=candidate(), detail_html="PREFEITURA MUNICIPAL DE ALFA cod=142",
                         detail_url="https://novo.ibgpconcursos.com.br/concurso.jsp?cod=142")


def test_s3_virtual_bucket_does_not_bypass_imeso_bucket_scope():
    with pytest.raises(DestinationBlocked):
        validate_destination("https://attacker-bucket.s3.us-east-1.amazonaws.com/edital.pdf")


@pytest.mark.parametrize("final_url", [
    "https://evil.example/document.pdf",
    "https://cdn.imeso.com.br/edital/1/999/edital.pdf",
])
def test_imeso_final_download_url_checked_even_if_chain_omits_it(final_url):
    driver = build_imeso_mock_driver()
    chosen = imeso_candidates(driver.open_listing(IMESO_LISTING), IMESO_LISTING)[0]
    download = next(iter(driver._downloads.values()))
    download.url_final = final_url
    with pytest.raises((ValueError, DestinationBlocked)):
        AcquisitionService().select_and_fetch(driver, candidate=chosen)


def test_generic_municipality_words_do_not_prove_contest_identity_or_title():
    pages = [PageText(artifact_id="a", page_number=1,
        text="PREFEITURA MUNICIPAL DE BETA. EDITAL DE ABERTURA 01/2026.")]
    result = validate_identity(candidate=candidate(), pages=pages,
        document_title="Edital de abertura", document_url="https://novo.ibgpconcursos.com.br/edital.pdf")
    assert result.status != ValidationStatus.VALID
    fields = extract_fields(candidate=candidate(), artifact=_artifact(), pages=pages)
    assert next(f for f in fields if f.field_name == "titulo").state != FieldState.SUPPORTED


def test_ibgp_main_notice_in_anexos_directory_is_not_attachment():
    html = '<table id="editais"><tr><td>23/06/2026</td><td>EDITAL Nº 01-2026</td><td><a href="rest/concurso/download/edital/23011/?file=site/anexos/704/00 - EDITAL.pdf"><img src="pdf.png" /></a></td></tr><tr><td>23/06/2026</td><td>ANEXO I - CARGOS</td><td><a href="rest/concurso/download/edital/23012/?file=site/anexos/704/01 - ANEXO I.pdf"><img src="pdf.png" /></a></td></tr></table>'
    docs = parse_document_candidates(html, base_url="https://novo.ibgpconcursos.com.br/concurso.jsp?cod=704")
    chosen, _ = choose_edital(docs)
    assert "/23011/" in chosen.url_requested
    assert docs[1].kind == "anexo"


def test_table_fee_and_salary_proximity_must_not_publish_fee_as_salary():
    text = "TAXA DE INSCRIÇÃO VAGAS VENCIMENTO (R$) CARGA HORÁRIA\n" + "x " * 110 + "R$ 120,00 1+CR 0 R$ 3.242,00 40h"
    fields = extract_fields(candidate=candidate(), artifact=_artifact(), pages=[PageText(artifact_id="a",page_number=22,text=text)])
    field = next(f for f in fields if f.field_name == "remuneracao")
    assert field.state != FieldState.SUPPORTED or "120.00" not in field.value["valores_observados"]
