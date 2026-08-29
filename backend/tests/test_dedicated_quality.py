import pytest
from bs4 import BeautifulSoup

from app.connectors.base import CandidateItem
from app.connectors.dedicated.apis import UniselvaAPIConnector
from app.connectors.dedicated.national import GenericDedicatedBancaConnector, IESESConnector
from app.connectors.dedicated.regional import (
    ABCPConnector,
    AccessConnector,
    AvancaSPConnector,
    AvaliaConnector,
    COTECConnector,
    FUNCERNConnector,
    LegatusConnector,
    ObjetivaConnector,
    UFUConnector,
    FUNVAPIConnector,
)


def test_generic_dedicated_rejects_navigation_and_documents(monkeypatch):
    connector = GenericDedicatedBancaConnector(
        base_url='https://banca.example', list_url='https://banca.example/concursos'
    )
    html = '''
    <div class="card"><a href="/concursos">Concursos disponíveis</a></div>
    <div class="card"><a href="/concursos/123">Prefeitura de Exemplo - Concurso Público</a></div>
    <div class="card"><a href="/categoria/concursos">Prefeitura - Editais</a></div>
    <div class="card"><a href="/edital/123.pdf">Edital Prefeitura</a></div>
    <a href="/concursos/456">Saiba mais</a>
    <a href="/concursos/789">Câmara Municipal - Processo Seletivo</a>
    '''
    monkeypatch.setattr(connector, '_fetch_html', lambda url: html)

    candidates = connector._fetch_candidates()

    assert [item.detail_url for item in candidates] == [
        'https://banca.example/concursos/123',
        'https://banca.example/concursos/789',
    ]
    assert all(item.status_hint is None for item in candidates)


def test_generic_dedicated_does_not_turn_link_presence_into_open_status():
    connector = GenericDedicatedBancaConnector(
        base_url='https://banca.example', list_url='https://banca.example/lista'
    )
    html = '<a href="/concursos/123">Prefeitura de Exemplo - Concurso Público</a>'
    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr(connector, '_fetch_html', lambda url: html)
    try:
        candidates = connector._fetch_candidates()
    finally:
        monkeypatch.undo()
    assert len(candidates) == 1
    assert candidates[0].status_hint is None


@pytest.mark.parametrize(
    ('connector', 'base', 'listing'),
    [
        (COTECConnector(list_url='https://www.cotec.fadenor.com.br/index/abertos/'), 'www.cotec.fadenor.com.br', '/index/abertos/'),
        (UFUConnector(), 'www.portalselecao.ufu.br', '/servicos/Edital/listar/concursos'),
        (AvaliaConnector(), 'www2.avalia.org.br', '/concursos.jsp'),
        (AccessConnector(), 'access.selecao.net.br', 'https://access.selecao.net.br'),
        (ABCPConnector(), 'abcp.selecao.net.br', '/index/abertos/'),
        (IESESConnector(), 'ieses.org', '/projetos'),
        (UniselvaAPIConnector(), 'inscricao.fundacaouniselva.org.br', '/selecoes'),
        (ObjetivaConnector(), 'concursos.objetivas.com.br', 'https://concursos.objetivas.com.br'),
        (LegatusConnector(), 'www.legatus.org.br', 'https://www.legatus.org.br'),
    ],
)
def test_audited_connectors_use_canonical_hosts(connector, base, listing):
    assert base in connector.base_url
    assert base in connector.list_url
    if listing.startswith('/'):
        assert connector.list_url.endswith(listing)


def test_detail_url_requires_specific_identity_pattern():
    connector = GenericDedicatedBancaConnector('https://banca.example', 'https://banca.example/')
    assert not connector._is_detail_url('https://banca.example/concursos')
    assert not connector._is_detail_url('https://banca.example/concursos/abertos')
    assert not connector._is_detail_url('https://banca.example/edital/1.pdf')
    assert connector._is_detail_url('https://banca.example/concursos/123')


def test_candidate_context_does_not_leak_status_from_broad_container(monkeypatch):
    connector = FUNCERNConnector()
    html = '''
    <article>
      <section><h2>Inscrições abertas</h2>
        <article><div><span>Inscrições abertas</span><h3>Concurso Público Cidade/RN</h3>
          <a href="/concursos/cidade-2026/">Saiba mais</a></div></article>
      </section>
      <section><h2>Outros processos</h2>
        <article><div><span>Finalizado</span><h3>Seleção para estágio FUNCERN</h3>
          <a href="/concursos/estagio-finalizado/">Saiba mais</a></div></article>
      </section>
    </article>'''
    monkeypatch.setattr(connector, '_fetch_html', lambda url: html)

    candidates = connector._fetch_candidates()

    assert [item.detail_url for item in candidates] == ['https://funcern.br/concursos/cidade-2026/']
    assert candidates[0].status_hint == 'Inscrições abertas'


def test_source_specific_academic_filters(monkeypatch):
    avancasp = AvancaSPConnector()
    monkeypatch.setattr(avancasp, '_fetch_html', lambda url: '''
      <div><a href="/informacoes/1/">Processo Seletivo Vestibular - Instituto Superior</a></div>
      <div><a href="/informacoes/2/">Concurso Público - Prefeitura de Exemplo</a></div>''')
    assert [c.detail_url for c in avancasp._fetch_candidates()] == [
        'https://avancasp.selecao.net.br/informacoes/2/'
    ]

    cotec = COTECConnector()
    monkeypatch.setattr(cotec, '_fetch_html', lambda url: '''
      <div><a href="/informacoes/1/">Proficiência em Línguas Estrangeiras - Edital 1/2026</a></div>
      <div><a href="/informacoes/2/">Concurso Público - Câmara Municipal</a></div>''')
    assert [c.detail_url for c in cotec._fetch_candidates()] == [
        'https://www.cotec.fadenor.com.br/informacoes/2/'
    ]


def test_structured_vaga_table_extracts_real_totals_and_fields():
    connector = AvancaSPConnector()
    soup = BeautifulSoup('''
      <table><tr><th>Vaga</th><th>Escolaridade</th><th>Salário</th><th>Qtde.</th><th>Taxa</th></tr>
      <tr><td>Analista</td><td>Superior</td><td>R$ 9.940,00</td><td>2 + CR</td><td>R$ 69,80</td></tr>
      <tr><td>Assistente</td><td>Médio</td><td>R$ 3.920,00</td><td>13 + CR</td><td>R$ 53,50</td></tr></table>
    ''', 'html.parser')

    fields = connector._extract_structured_vaga_fields(soup)

    assert fields['cargos'] == ['Analista', 'Assistente']
    assert fields['vagas'] == 15
    assert str(fields['salario_min']) == '3920.00'
    assert str(fields['salario_max']) == '9940.00'
    assert str(fields['taxa']) == '53.50'
    assert fields['escolaridade'] == 'Múltiplas'


def test_structured_vaga_table_adds_numeric_reserve_but_not_bare_cr():
    connector = AccessConnector()
    soup = BeautifulSoup('''
      <table><tr><th>Emprego</th><th>Quantidade</th><th>Salário</th></tr>
      <tr><td>Professor</td><td>86 + 279 Cadastro de Reserva</td><td>R$ 4.000,00</td></tr>
      <tr><td>Analista</td><td>9 + 21 CR</td><td>R$ 5.000,00</td></tr>
      <tr><td>Técnico</td><td>2 + CR</td><td>R$ 3.000,00</td></tr></table>
    ''', 'html.parser')

    fields = connector._extract_structured_vaga_fields(soup)

    assert fields['vagas'] == 397


def test_uniselva_semantic_gate_rejects_consulting_and_accepts_personnel():
    assert not UniselvaAPIConnector._is_eligible_api_item({
        'titulo': 'Contratação de consultor individual',
        'descricao': 'Consultoria por Pessoa Jurídica (CNPJ)',
        'funcaoConsultoria': 'Consultor especialista',
    })
    assert UniselvaAPIConnector._is_eligible_api_item({
        'titulo': 'Edital 062/2026 contratação de estagiário de graduação',
        'descricao': 'Seleção simplificada destinada à contratação de estagiário.',
    })
    assert UniselvaAPIConnector._is_eligible_api_item({
        'titulo': 'Formação de banco de currículos para vaga de Analista Administrativo',
        'descricao': 'Seleção de profissionais para oportunidades na vaga.',
    })


def test_ieses_publications_keep_documents_results_and_gabaritos_only_once():
    soup = BeautifulSoup('''
      <section id="passo03"><a href="/edital.pdf"><time datetime="10/08/2026">10/08/2026</time> - Edital 001/2026</a></section>
      <section id="passo01"><a href="/edital.pdf"><time datetime="10/08/2026">10/08/2026</time> - Edital 001/2026</a></section>
      <section id="passo04"><a href="/prova.pdf">Prova Analista</a><a href="/gabarito.pdf">Gabarito Definitivo</a></section>
      <section id="passo06"><a href="/resultado.pdf">Resultado Final</a></section>
    ''', 'html.parser')

    pubs = IESESConnector._ieses_publications(soup, 'https://concurso.ieses.org/')

    assert [pub['title'] for pub in pubs] == ['Edital 001/2026', 'Gabarito Definitivo', 'Resultado Final']


def test_ieses_extracts_inscription_interval_from_pdf_excerpt():
    start, end = IESESConnector._pdf_inscription_interval(
        'preencher a ficha no período de segunda-feira, 10 de agosto de 2026, '
        'a sexta-feira, 11 de setembro de 2026.'
    )

    assert start.isoformat().startswith('2026-08-10')
    assert end.isoformat().startswith('2026-09-11')


def test_ufu_uses_listing_identity_over_generic_dirps_heading():
    connector = UFUConnector()
    title = connector._extract_title(
        ['DIRPS - Portal de Seleção'],
        'Processo Seletivo Simplificado Visitante INFIS - Edital 144/2026 Inscrições até 20/09/2026',
    )
    assert title == 'Processo Seletivo Simplificado Visitante INFIS - Edital 144/2026'


def test_avalia_epagri_normalizes_footer_contamination(monkeypatch):
    connector = AvaliaConnector()
    monkeypatch.setattr(
        GenericDedicatedBancaConnector,
        '_parse_detail',
        lambda self, candidate, html, *, client: {
            'titulo': 'Instituto Avalia - Maringá/PR', 'orgao': 'Instituto Avalia',
            'cidade': 'Maringá', 'uf': 'PR', 'status': 'Em andamento',
            'modalidade': 'Concurso Público', 'inscricao_inicio': None,
            'inscricao_fim': None, 'cargo': None, 'area': None, 'vagas': None,
            'salario_min': None, 'salario_max': None, 'resumo': '',
        },
    )
    parsed = connector._parse_detail(
        CandidateItem(title_hint='EPAGRI - Processo Seletivo 2026', detail_url='https://www2.avalia.org.br/concurso.jsp?id=1'),
        'EPAGRI processo seletivo', client=None,
    )
    assert parsed['orgao'] == 'EPAGRI'
    assert parsed['uf'] == 'SC'
    assert parsed['cidade'] is None
    assert parsed['status'] == 'Inscrições abertas'


def test_avalia_uses_pdf_table_for_personnel_fields(monkeypatch):
    connector = AvaliaConnector()
    monkeypatch.setattr(
        GenericDedicatedBancaConnector, '_parse_detail',
        lambda self, candidate, html, *, client: {
            'titulo': 'EPAGRI - Concurso para Emprego Público', 'orgao': 'EPAGRI',
            'cidade': None, 'uf': 'SC', 'status': 'Em andamento',
            'modalidade': 'Concurso Público', 'link_edital': 'https://example.test/epagri.pdf',
            'vagas': None, 'salario_min': None, 'salario_max': None, 'taxa': None,
            'escolaridade': None, 'inscricao_inicio': None, 'inscricao_fim': None,
            'cargo': None, 'area': None, 'resumo': '',
        },
    )
    monkeypatch.setattr(
        'app.connectors.dedicated.regional.extract_pdf_fields_if_possible',
        lambda *args, **kwargs: ({}, {'vagas': 12, 'salario_min': 4362.02,
                                      'salario_max': 16990.33, 'taxa': 200,
                                      'escolaridade': 'Múltiplas'}, 'Tabela', None),
    )
    parsed = connector._parse_detail(
        CandidateItem(title_hint='EPAGRI - processo seletivo', detail_url='https://example.test/1'),
        'EPAGRI', client=object(),
    )
    assert parsed['vagas'] == 12
    assert parsed['salario_min'] == 4362.02
    assert parsed['salario_max'] == 16990.33
    assert parsed['taxa'] == 200


def test_funvapi_prefers_explicit_pdf_total_location_and_dates(monkeypatch):
    connector = FUNVAPIConnector()
    monkeypatch.setattr(
        GenericDedicatedBancaConnector,
        '_parse_detail',
        lambda self, candidate, html, *, client: {
            'titulo': 'Prefeitura Municipal de Belo Jardim - PE',
            'modalidade': 'Concurso Público', 'status': 'Em andamento',
            'orgao': 'Prefeitura Municipal de Belo Jardim', 'cidade': 'Princesa Isabel', 'uf': 'PB',
            'vagas': 2, 'salario_min': None, 'salario_max': None, 'cargo': None, 'area': None,
            'inscricao_inicio': None, 'inscricao_fim': None, 'edital_pdf_excerpt': (
                'A Prefeitura Municipal de Belo Jardim/PE oferta um total de 150 vagas. '
                'Inscrições de 01 de setembro de 2026 a 04 de outubro de 2026.'
            ), 'resumo': '',
        },
    )
    parsed = connector._parse_detail(
        CandidateItem(title_hint='Prefeitura Municipal de Belo Jardim - PE - Concurso Público', detail_url='https://funvapi.com.br/index.php/2026/08/01/belo-jardim/'),
        '', client=None,
    )
    assert parsed['vagas'] == 150
    assert parsed['cidade'] == 'Belo Jardim'
    assert parsed['uf'] == 'PE'
    assert parsed['inscricao_inicio'].isoformat().startswith('2026-09-01')
    assert parsed['inscricao_fim'].isoformat().startswith('2026-10-04')
