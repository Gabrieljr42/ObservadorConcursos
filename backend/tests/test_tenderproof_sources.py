"""Synthetic controlled second-source and contextual evidence regression."""
import pytest
from app.tenderproof.sources import *
from app.tenderproof.acquisition import choose_edital, parse_document_candidates
from app.tenderproof.contracts import PageText
from app.tenderproof.fields import extract_fields
from app.tenderproof.service import TenderProofService
from app.tenderproof.store import TenderProofStore
from app.tenderproof.security import validate_destination, DestinationBlocked
from test_tenderproof_evidence import _candidate, _artifact


def test_imeso_same_contract_end_to_end():
    service = TenderProofService(TenderProofStore())
    run = service.start_discovery(build_imeso_mock_driver(), source=IMESO_SOURCE,
        listing_url=IMESO_LISTING, mode="mock", is_synthetic=True, owner_user_id=1)
    assert len(run.candidates) == 1
    run = service.select_and_process(run.run_id, "imeso-42", build_imeso_mock_driver())
    assert run.execution_status == "completed", run.error
    assert run.validation_status == "valid"
    assert len(run.fields) == 6
    assert run.field_map()["remuneracao"].state == "unknown"
    assert run.artifact.sha256 and run.is_synthetic_sample


def test_imeso_foreign_links_not_candidates():
    assert not imeso_candidates('<a href="https://evil.test/edital/ver/42">X</a>', IMESO_LISTING)


def test_imeso_wrong_document_refused():
    candidate = imeso_candidates('<div class="row"><p>Exemplo</p><a href="/edital/ver/42">Mais</a></div>', IMESO_LISTING)[0]
    with pytest.raises(ValueError, match="outro concurso"):
        imeso_documents('<a href="https://cdn.imeso.com.br/edital/1/43/edital.pdf">Edital</a>', candidate)


def test_imeso_judgment_referring_to_edital_is_not_edital():
    candidate = imeso_candidates('<div class="row"><p>Exemplo</p><a href="/edital/ver/42">Mais</a></div>', IMESO_LISTING)[0]
    docs = imeso_documents('<div class="row"><p>JULGAMENTO DAS IMPUGNAÇÕES AO EDITAL</p><a href="https://cdn.imeso.com.br/edital/1/42/a.pdf">DOWNLOAD</a></div>', candidate)
    assert docs[0].kind == 'outro'
    with pytest.raises(ValueError): choose_edital(docs)


@pytest.mark.parametrize("url", [
    "https://s3.us-east-1.amazonaws.com/another-bucket/edital/a.pdf",
    "https://s3.us-east-1.amazonaws.com/cdn.imeso.com.br/edital/%2e%2e/a.pdf",
    "https://user:password@cdn.imeso.com.br/edital/a.pdf",
])
def test_document_destination_scope(url):
    with pytest.raises(DestinationBlocked): validate_destination(url)


@pytest.mark.parametrize("label", ["Anexo I do Edital", "Edital retificado", "Errata do Edital", "Gabarito"])
def test_attachment_not_principal(label):
    docs = parse_document_candidates(f'<a href="/edital.pdf">{label}</a>', base_url="https://novo.ibgpconcursos.com.br")
    with pytest.raises(ValueError): choose_edital(docs)


def test_ambiguous_edital_requires_selection():
    docs = parse_document_candidates('<a href="/a.pdf">Edital 01/2026</a><a href="/b.pdf">Edital 02/2026</a>', base_url="https://novo.ibgpconcursos.com.br")
    with pytest.raises(ValueError, match="ambíguos"): choose_edital(docs)


def test_ibgp_accordion_is_not_document():
    base = 'https://novo.ibgpconcursos.com.br/concurso.jsp?cod=704'
    docs = parse_document_candidates(f'<a href="#collapseTwo">Editais</a><a href="{base}#collapseTwo">Editais</a>', base_url=base)
    assert docs == []


def test_ibgp_image_download_uses_table_label_not_anexos_directory():
    html = '<tr><td>23/06/2026</td><td>EDITAL Nº 01-2026</td><td><a href="rest/concurso/download/edital/23011/?file=site/anexos/704/main.pdf"><img src="pdf.png"></a></td></tr>'
    docs = parse_document_candidates(html, base_url='https://novo.ibgpconcursos.com.br/concurso.jsp?cod=704')
    assert docs[0].title == 'EDITAL Nº 01-2026' and docs[0].kind == 'edital'
    assert choose_edital(docs)[0].doc_id == docs[0].doc_id


def test_flattened_fee_salary_table_does_not_publish_fee_as_pay():
    text = 'TAXA DE INSCRIÇÃO\n' + 'outros cabeçalhos ' * 35 + '\nCARGO VENCIMENTO (R$) VAGAS R$ 120,00 1+CR 0 R$ 3.242,00 40h'
    fields = extract_fields(candidate=_candidate(), artifact=_artifact(), pages=[PageText(artifact_id='a',page_number=22,text=text)])
    assert next(f for f in fields if f.field_name=='remuneracao').state == 'unknown'


def test_registration_clause_ignores_payment_and_appeal():
    text = ('EDITAL Nº 01/2026\nAs inscrições deverão ser realizadas, exclusivamente, via internet, '
        'pelo endereço eletrônico www.ibgpconcursos.com.br, no período das 09h do dia '
        '24/08/2026 às 16h do dia 22/09/2026.\nPagamento da taxa de inscrição até 23/09/2026. '
        'Inscrições deferidas em 02/10/2026. Recurso em 05/10/2026.')
    fields = {f.field_name:f for f in extract_fields(candidate=_candidate(), artifact=_artifact(),
        pages=[PageText(artifact_id="a", page_number=6, text=text)])}
    assert fields['inscricao_inicio'].value == '2026-08-24'
    assert fields['inscricao_fim'].value == '2026-09-22'
    assert fields['inscricao_fim'].evidence[0].snippet in text


def test_conflicting_direct_periods_still_conflict():
    text = 'As inscricoes estarao abertas de 01/03/2026 a 02/03/2026. As inscricoes estarao abertas de 04/03/2026 a 05/03/2026.'
    fields = extract_fields(candidate=_candidate(), artifact=_artifact(), pages=[PageText(artifact_id="a",page_number=1,text=text)])
    assert next(f for f in fields if f.field_name=='inscricao_inicio').state == 'conflict'


def test_principal_edital_precedes_incidental_reference():
    fields = extract_fields(candidate=_candidate(), artifact=_artifact(), pages=[
        PageText(artifact_id="a",page_number=1,text='EDITAL Nº 01/2026\nConcurso Publico'),
        PageText(artifact_id="a",page_number=2,text='Conforme regras anteriores do Edital 05/2020.')])
    f = next(f for f in fields if f.field_name=='edital_numero')
    assert f.value == '01/2026' and f.evidence[0].page_number == 1
