from datetime import datetime, timezone
import pytest

from app.tenderproof.contracts import Artifact, PageText
from app.tenderproof.faped_adapter import FapedAdapter
from app.tenderproof.faped_parser import LISTING
from app.tenderproof.fields import extract_fields

HEADER = 'Fundação de Apoio à Pesquisa e ao Desenvolvimento - FAPED\nEDITAL DE PROCESSO SELETIVO SIMPLIFICADO Nº. 045/2027\n'
PERIOD = 'A inscrição será realizada de 06/02/2027 à 18/02/2027 até 23h59min,'


def fields(text, title='PROCESSO SELETIVO SIMPLIFICADO 045/2027', **page_options):
    candidate = FapedAdapter().candidate_from_url(LISTING + '#docfor876', title)
    artifact = Artifact(artifact_id='doc', sha256='a' * 64, byte_len=123,
        url_requested='https://faped.org.br/files/uploads/document/new.pdf',
        url_final='https://faped.org.br/files/uploads/document/new.pdf', downloaded_at=datetime.now(timezone.utc))
    return {f.field_name: f for f in extract_fields(candidate=candidate, artifact=artifact,
        pages=[PageText(artifact_id='doc', page_number=1, text=text, **page_options)])}


def test_header_and_direct_dates_have_literal_independent_evidence():
    text = HEADER + PERIOD
    result = fields(text)
    assert result['titulo'].value == HEADER.splitlines()[1]
    assert result['orgao'].value == HEADER.splitlines()[0]
    assert result['inscricao_inicio'].value == '2027-02-06'
    assert result['inscricao_fim'].value == '2027-02-18'
    assert result['inscricao_fim'].original_value == '18/02/2027'
    for name in ('titulo', 'orgao', 'inscricao_inicio', 'inscricao_fim'):
        assert result[name].state.value == 'supported'
        assert all(e.snippet in text and e.document_sha256 == 'a' * 64 for e in result[name].evidence)


@pytest.mark.parametrize('period', [PERIOD.replace('06/02/2027','31/02/2027'),
    PERIOD.replace('06/02/2027','19/02/2027'), PERIOD.replace('23h59min','25h59min'),
    PERIOD.replace('inscrição','pagamento')])
def test_invalid_or_unrelated_period_is_implementation_pending(period):
    result = fields(HEADER + period)
    for name in ('inscricao_inicio','inscricao_fim'):
        assert result[name].value is None and result[name].state.value == 'failed'


def test_competing_registration_dates_require_conference():
    result = fields(HEADER + PERIOD + '\n' + PERIOD.replace('18/02/2027','20/02/2027'))
    assert result['inscricao_fim'].state.value == 'conflict'
    incomplete = fields(HEADER + PERIOD + '\nA inscrição será realizada de data a definir.')
    assert incomplete['inscricao_inicio'].state.value == 'failed'


@pytest.mark.parametrize('options', [{'truncated':True}, {'error':'unreadable'}])
def test_damaged_page_cannot_support_identity_or_dates(options):
    result = fields(HEADER + PERIOD, **options)
    assert all(result[name].state.value == 'failed' for name in ('titulo','orgao','inscricao_inicio','inscricao_fim'))


def test_notice_identity_must_agree_with_observed_selection():
    assert fields(HEADER, title='PROCESSO SELETIVO SIMPLIFICADO 099/2027')['titulo'].state.value == 'failed'


def test_published_unparsed_job_table_is_not_absent():
    result = fields(HEADER + 'Cargo N.º de Vagas Carga-horária Salário Base (bruto)\nCargo novo 01 8 horas diárias R$ 8.000,00')
    assert result['cargos'].state.value == 'failed' and result['cargos'].evidence
