from __future__ import annotations

from contextlib import contextmanager
from datetime import UTC, datetime
from decimal import Decimal

from app.connectors.dedicated.platforms import EloOpenConnector, RBOOpenConnector


class FakeResponse:
    def __init__(self, payload, status_code: int = 200):
        self.payload = payload
        self.status_code = status_code
        self.content = payload.encode('utf-8') if isinstance(payload, str) else b''
        self.encoding = 'utf-8'

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f'HTTP {self.status_code}')

    def json(self):
        if isinstance(self.payload, str):
            raise ValueError('not JSON')
        return self.payload


class FakeClient:
    def __init__(self, responses):
        self.responses = responses
        self.headers = {}
        self.calls = []

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def get(self, url, **kwargs):
        self.calls.append((url, kwargs))
        return self.responses.get(url, FakeResponse({}, 404))


def test_elo_api_list_detail_documents_and_tenant(monkeypatch):
    list_url = 'https://api.gestaoselecoes.com.br/api/editais'
    detail_url = f'{list_url}/42'
    docs_url = f'{detail_url}/documentos'
    client = FakeClient({
        list_url: FakeResponse({'totalElements': 1, 'content': [{
            'id': 42, 'titulo': 'Concurso Público - Prefeitura Municipal de Teste/MG',
            'situacao': 'INSCRICAO_ABERTA',
        }]}),
        detail_url: FakeResponse({'id': 42, 'titulo': 'Concurso Público - Prefeitura Municipal de Teste/MG',
                                  'orgao': 'Prefeitura Municipal de Teste',
                                  'cidade': 'Teste', 'uf': 'MG',
                                  'inicioInscricao': '2026-08-01T00:00:00Z',
                                  'fimInscricao': '2026-09-01T00:00:00Z',
                                  'cargos': [{'nome': 'Professor', 'quantidade': 3}],
                                  'taxaInscricao': 'R$ 80,00'}),
        docs_url: FakeResponse({'documentos': [{'descricao': 'Edital de Abertura',
                                                'arquivo': 'https://cdn.example/edital.pdf',
                                                'dataPublicacao': '2026-07-25'}]}),
    })
    connector = EloOpenConnector()
    monkeypatch.setattr(connector, '_http_client', lambda **_kwargs: client)
    monkeypatch.setattr(
        'app.connectors.dedicated.platforms.extract_pdf_fields_if_possible',
        lambda *args, **kwargs: ({'ok': True, 'url': args[0], 'pages': 1, 'text_hash': 'hash'},
                                  {'raw_pdf_fields': {}}, 'official pdf', datetime.now(UTC)),
    )

    result = connector.crawl_with_diagnostics()
    assert result.run_data.candidates_found == 1
    assert result.run_data.candidates_rejected == 0
    assert len(result.items) == 1
    item = result.items[0]
    assert item['external_id'] == '42'
    assert item['vagas'] == 3
    assert item['taxa'] == Decimal('80.00')
    assert item['link_edital'] == 'https://cdn.example/edital.pdf'
    assert len(item['raw_data']['publications']) == 1
    list_call = next(call for call in client.calls if call[0] == list_url)
    assert list_call[1]['headers']['X-TenantID'] == 'eloassessoria'
    assert list_call[1]['params']['situacao'] == 'PUBLICADO,INSCRICAO_ABERTA,ANDAMENTO'


def test_rbo_open_discovers_only_information_cards_and_all_publications(monkeypatch):
    list_html = '''
    <h1>Concursos - Inscrições Abertas</h1>
    <article><a href="/informacoes/203/">Concurso Público - 02/2026 - Prefeitura da Estância Turística de Jahu- SP</a></article>
    <article><a href="/informacoes/208/">Processo Seletivo - 036/2026 - Serviço de Apoio às Micro e Pequenas Empresas do Estado de São Paulo – SEBRAE-SP</a></article>
    <a href="/fale-conosco">Fale Conosco</a>
    '''
    detail_html = '''
    <h1>Concurso Público - 02/2026 - Prefeitura da Estância Turística de Jahu- SP</h1>
    <p>Inscrições de 24/08/2026 a 25/09/2026</p><p>Situação: Em andamento</p>
    <h2>Publicações</h2><a href="https://cdn.example/abertura.pdf">EDITAL DE ABERTURA RETIFICADO 18/08/2026</a>
    <a href="https://cdn.example/retificacao.pdf">RETIFICAÇÃO Nº 01 DO EDITAL DE ABERTURA 25/08/2026</a>
    <h2>Vagas</h2><table><tr><th>Vaga</th><th>Qtde.</th></tr>
    <tr><td>AUXILIAR EM SAÚDE BUCAL</td><td>1</td></tr><tr><td>ORIENTADOR SOCIAL</td><td>1</td></tr></table>
    '''
    connector = RBOOpenConnector()
    monkeypatch.setattr(connector, '_fetch_html', lambda url: list_html if url.endswith('/abertos/') else detail_html)
    monkeypatch.setattr(
        'app.connectors.dedicated.platforms.extract_pdf_fields_if_possible',
        lambda *args, **kwargs: ({'ok': True, 'url': args[0], 'pages': 1, 'text_hash': 'hash'},
                                  {'raw_pdf_fields': {}}, 'official pdf', datetime.now(UTC)),
    )
    candidates = connector._fetch_candidates()
    assert [candidate.external_id for candidate in candidates] == ['203', '208']
    parsed = connector._parse_detail(candidates[0], detail_html, client=FakeClient({}))
    assert parsed is not None
    assert parsed['orgao'] == 'Prefeitura da Estância Turística de Jahu'
    assert parsed['cidade'] == 'Jahu'
    assert parsed['uf'] == 'SP'
    assert parsed['vagas'] == 2
    assert len(parsed['raw_data']['publications']) == 2
    assert parsed['link_edital'] == 'https://cdn.example/abertura.pdf'


def test_elo_real_payload_and_documents_500_use_ssr_without_attribute_error(monkeypatch):
    list_url = 'https://api.gestaoselecoes.com.br/api/editais'
    detail_url = f'{list_url}/137'
    docs_url = f'{detail_url}/documentos'
    frontend_url = 'https://eloassessoriaeservicos.com.br/concurso/137'
    payload = {
        'id': 137,
        'descricao': 'CIMAG - CONSÓRCIO PÚBLICO INTERMUNICIPAL MULTIFINALITÁRIO DA MICRORREGIÃO DO CIRCUITO DAS ÁGUAS',
        'numero': '1', 'ano': '2026', 'tipo': 'Concurso Público',
        'situacaoEdital': 'PUBLICADO', 'situacaoInscricao': 'EM_BREVE',
        'nomeOrgaoSolicitante': 'CIMAG', 'dataInicioInscricoes': '24/10/2026',
        'dataTerminoInscricoes': '23/11/2026', 'totalCargos': 2,
        'totalVagasAmplaConcorrencia': 2, 'totalVagasPcd': 0,
        'totalVagasPpp': 0, 'inscricoesAbertas': False,
    }
    ssr = '''<h2>CIMAG - CONSÓRCIO PÚBLICO INTERMUNICIPAL MULTIFINALITÁRIO</h2>
    <h3>Documentos (1)</h3><a href="https://cdn.example/cimag-edital.pdf">EDITAL</a>
    <h4>MÉDICO VETERINÁRIO JUNIOR</h4><span>Ampla Concorrência 1</span>
    <h4>MÉDICO VETERINÁRIO SÊNIOR</h4><span>Ampla Concorrência 1</span>
    <p>Taxa de Inscrição R$ 120,00</p>'''
    client = FakeClient({
        list_url: FakeResponse({'totalElements': 1, 'content': [payload]}),
        detail_url: FakeResponse(payload),
        docs_url: FakeResponse({'error': 'upstream failure'}, status_code=500),
        frontend_url: FakeResponse(ssr),
    })
    connector = EloOpenConnector()
    monkeypatch.setattr(connector, '_http_client', lambda **_kwargs: client)
    monkeypatch.setattr(
        'app.connectors.dedicated.platforms.extract_pdf_fields_if_possible',
        lambda *args, **kwargs: ({'ok': True, 'url': args[0], 'pages': 1, 'text_hash': 'hash'},
                                  {'raw_pdf_fields': {}}, 'official pdf', datetime.now(UTC)),
    )
    result = connector.crawl_with_diagnostics()
    assert result.run_data.candidates_found == 1
    assert result.run_data.candidates_rejected == 0
    assert len(result.items) == 1
    assert result.items[0]['orgao'] == 'CIMAG'
    assert result.items[0]['vagas'] == 2
    assert result.items[0]['link_edital'] == 'https://cdn.example/cimag-edital.pdf'
    assert len(result.items[0]['raw_data']['publications']) == 1
    # The SSR detail already exposed the visible document; the known-500
    # supplementary endpoint must not be required (or even called).
    assert not any(url == docs_url for url, _kwargs in client.calls)


def test_rbo_real_shaped_details_crawl_two_of_two_without_quality_gate_error(monkeypatch):
    list_html = '''<h1>Concursos - Inscrições Abertas</h1>
    <a href="/informacoes/203/">Concurso Público - 02/2026 - Prefeitura da Estância Turística de Jahu- SP</a>
    <a href="/informacoes/208/">Processo Seletivo - 036/2026 - Serviço de Apoio às Micro e Pequenas Empresas do Estado de São Paulo – SEBRAE-SP</a>'''
    jahu = '''<h2>Concurso Público - 02/2026 - Prefeitura da Estância Turística de Jahu- SP</h2>
    <p>Inscrições de 24/08/2026 a 25/09/2026</p><p>Situação: Em andamento</p>
    <a href="https://cdn.example/jahu-edital.pdf">EDITAL DE ABERTURA RETIFICADO 18/08/2026</a>
    <a href="https://cdn.example/jahu-ret.pdf">RETIFICAÇÃO Nº 01 DO EDITAL DE ABERTURA 25/08/2026</a>
    <table><tr><th>Vaga</th><th>Qtde.</th></tr><tr><td>AUXILIAR EM SAÚDE BUCAL</td><td>1</td></tr>
    <tr><td>ORIENTADOR SOCIAL</td><td>1</td></tr><tr><td>TÉCNICO EM RADIOLOGIA I</td><td>1</td></tr>
    <tr><td>ADVOGADO - SUAS</td><td>1</td></tr><tr><td>DENTISTA I</td><td>1</td></tr>
    <tr><td>ENFERMEIRO DO PSF I</td><td>1</td></tr><tr><td>FISIOTERAPEUTA I</td><td>1</td></tr>
    <tr><td>FONOAUDIÓLOGO I</td><td>1</td></tr><tr><td>TÉCNICO EM ATENDIMENTO SOCIOEDUCATIVO</td><td>1</td></tr>
    <tr><td>TERAPEUTA OCUPACIONAL I</td><td>1</td></tr></table>'''
    sebrae = '''<h2>Processo Seletivo - 036/2026 - Serviço de Apoio às Micro e Pequenas Empresas do Estado de São Paulo – SEBRAE-SP</h2>
    <p>Inscrições de 28/08/2026 a 03/09/2026</p><p>Situação: Em andamento</p>
    <a href="https://sebrae.com.br/comunicado.pdf">COMUNICADO E DIVULGAÇÕES 28/08/2026</a>
    <table><tr><th>Vaga</th><th>Qtde.</th></tr><tr><td>SECRETÁRIO ACADÊMICO SÊNIOR</td><td>1</td></tr></table>'''
    connector = RBOOpenConnector()
    monkeypatch.setattr(connector, '_fetch_html', lambda url: list_html if url.endswith('/abertos/') else (jahu if '/203/' in url else sebrae))
    monkeypatch.setattr(
        'app.connectors.dedicated.platforms.extract_pdf_fields_if_possible',
        lambda *args, **kwargs: ({'ok': False, 'url': args[0], 'pages': None, 'text_hash': None},
                                  {'raw_pdf_fields': {}}, None, None),
    )
    result = connector.crawl_with_diagnostics()
    assert result.run_data.candidates_found == 2
    assert result.run_data.candidates_rejected == 0
    assert len(result.items) == 2
    assert {item['vagas'] for item in result.items} == {10, 1}
    assert sum(len(item['raw_data']['publications']) for item in result.items) == 3
