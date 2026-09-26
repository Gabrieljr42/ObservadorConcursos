from datetime import datetime, timezone
from app.tenderproof.contracts import Artifact, PageText
from app.tenderproof.fumarc_adapter import FumarcAdapter
from app.tenderproof.fields import extract_fields


def fields(text, page_number=1, source='fumarc_open'):
    candidate = FumarcAdapter().candidate_from_url('https://www.fumarc.com.br/SitePages/Home.aspx?concurso=88')
    candidate.source = source
    artifact = Artifact(artifact_id='doc', sha256='a'*64, byte_len=123,
        url_requested='https://www.fumarc.com.br/Documentos%20Compartilhados/Novo/edital.pdf',
        url_final='https://www.fumarc.com.br/Documentos%20Compartilhados/Novo/edital.pdf',
        downloaded_at=datetime.now(timezone.utc))
    page = PageText(artifact_id='doc', page_number=page_number, text=text)
    return {f.field_name:f for f in extract_fields(candidate=candidate,artifact=artifact,pages=[page])}


def test_official_council_masthead_is_supported_with_verbatim_evidence():
    text = 'CONSELHO REGIONAL DE ADMINISTRAÇÃO DE ESTADO NOVO – CRA-EN\nAUTARQUIA FEDERAL\nCONCURSO PÚBLICO Nº 02/2027'
    result = fields(text)['orgao']
    assert result.state.value == 'supported'
    assert result.value == text.splitlines()[0]
    assert result.evidence[0].snippet in text
    assert fields(text,page_number=3)['orgao'].state.value != 'supported'
    assert fields(text,source='ibgp_open')['orgao'].state.value != 'supported'


def test_separate_published_job_annex_is_an_extraction_dependency():
    result = fields('Anexo I – Quadro de Cargos, Vagas, Salários base, Escolaridades, Requisitos;')['cargos']
    assert result.state.value == 'failed' and result.value is None
    assert 'anexo separado' in result.reason
    assert 'cargos' not in fields('Anexo II – Composição das Provas;')


def test_registration_effectuated_online_with_written_dates_and_hours():
    text = ('As inscrições deverão ser efetuadas, exclusivamente, via internet, a partir das 09h00min do dia '
            '20 de julho\nde 2026 às 23h59min do dia 18 de agosto de 2026 (horário de Brasília).')
    result = fields(text)
    assert result['inscricao_inicio'].value == '2026-07-20'
    assert result['inscricao_fim'].value == '2026-08-18'
    assert result['inscricao_fim'].original_value == '18 de agosto de 2026'
    assert result['inscricao_inicio'].evidence[0].snippet in text
    assert fields('Pagamento das taxas. ' + text.replace('inscrições', 'inscrições de pagamento'))['inscricao_inicio'].value is None
    conflict = fields(text + '\n' + text.replace('18 de agosto', '19 de agosto'))
    assert conflict['inscricao_fim'].state.value == 'conflict'


def test_fumarc_principal_notice_number_is_read_only_from_first_page_heading():
    text = 'CONCURSO PÚBLICO Nº 02/2027\nNos termos do Edital 99/2000 citado no histórico.'
    result = fields(text)['edital_numero']
    assert result.value == '02/2027'
    assert result.original_value == 'CONCURSO PÚBLICO Nº 02/2027'
    assert fields('CONCURSO PÚBLICO Nº 02/2027',page_number=4)['edital_numero'].value is None
    assert fields('CONCURSO PÚBLICO Nº 02/2027',source='ibgp_open')['edital_numero'].value is None
    assert fields('CONCURSO PÚBLICO Nº 02/2027\nCONCURSO PÚBLICO Nº 03/2027')['edital_numero'].state.value == 'conflict'


def test_fee_schedule_requires_written_and_numeric_agreement():
    text = ('O valor correspondente à Taxa de Inscrição para cada cargo será de:\n'
            'a) Nível Médio/Técnico: R$70,00 (setenta reais);\n'
            'b) Nível Superior: R$100,00 (cem reais).\n2.2.2. Inscrições.')
    result = fields(text)['taxas_inscricao']
    assert result.state.value == 'supported'
    assert result.value == {'medio_tecnico': '70.00', 'superior': '100.00'}
    assert result.evidence[0].snippet in text
    assert fields(text.replace('cem reais', 'cento e vinte reais'))['taxas_inscricao'].state.value == 'conflict'
    assert fields(text.replace('cem reais', 'valor ilegível'))['taxas_inscricao'].state.value == 'failed'
    assert fields(text.replace('R$70,00', 'R$80,00'))['taxas_inscricao'].state.value == 'conflict'
    assert fields(text.replace('2.2.2.', 'sem limite'))['taxas_inscricao'].state.value == 'failed'
    assert 'taxas_inscricao' not in fields(text, source='ibgp_open')

def test_fee_schedule_never_ignores_unparsed_or_duplicate_rows():
    base = ('O valor correspondente à Taxa de Inscrição para cada cargo será de:\n'
            'a) Nível Médio/Técnico: R$80,00 (oitenta reais);\n'
            'b) Nível Superior: R$135,00 (cento e trinta e cinco reais).\n')
    assert fields(base + '2.2.2. Inscrições.')['taxas_inscricao'].value['superior'] == '135.00'
    for extra in ('c) Nível Fundamental: R$30,00 (trinta reais).\n',
                  'c) Nível Superior: R$135,00 (cento e trinta e cinco reais).\n',
                  'exceto os cargos especificados abaixo\n'):
        assert fields(base + extra + '2.2.2. Inscrições.')['taxas_inscricao'].state.value == 'failed'
