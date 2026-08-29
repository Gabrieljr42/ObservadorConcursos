"""Regression and opt-in live tests for Exame and ADM&TEC.

The live tests are opt-in because the two portals use bot/browser guards in
some environments.  They document the URLs and the audited invariants while
the fixture tests run deterministically in CI.
"""

from __future__ import annotations

import os
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from app.connectors.dedicated.regional import ADMTECConnector, ExameConnector
from app.connectors.dedicated import ExameConsultoresConnector
from app.connectors.dedicated.platforms import EloOpenConnector, RBOOpenConnector
from app.connectors.registry import DEDICATED_CLASSES, DEFINITIONS_BY_SOURCE_TYPE, get_connector


EXAME_LIST_URL = 'https://concursos.exameconsultores.com.br/index/1/'
EXAME_DETAIL_URL = 'https://www.exameconsultores.com.br/informacoes/544/'
ADMTEC_HOME_URL = 'https://admtec.org.br/'


def test_registry_uses_regional_classes_and_preserves_elo_rbo_mappings():
    assert DEDICATED_CLASSES['exame_open'] is ExameConsultoresConnector
    assert DEDICATED_CLASSES['admtec_open'] is ADMTECConnector
    assert DEDICATED_CLASSES['elo_open'] is EloOpenConnector
    assert DEDICATED_CLASSES['rbo_open'] is RBOOpenConnector

    exame_def = DEFINITIONS_BY_SOURCE_TYPE['exame_open']
    admtec_def = DEFINITIONS_BY_SOURCE_TYPE['admtec_open']
    assert exame_def.base_url == 'https://concursos.exameconsultores.com.br'
    assert exame_def.list_urls == [EXAME_LIST_URL]
    assert admtec_def.base_url == 'https://admtec.org.br'
    assert admtec_def.list_urls == [ADMTEC_HOME_URL]

    assert isinstance(get_connector('exame_open'), ExameConsultoresConnector)
    assert isinstance(get_connector('admtec_open'), ADMTECConnector)
    assert isinstance(get_connector('elo_open'), EloOpenConnector)
    assert isinstance(get_connector('rbo_open'), RBOOpenConnector)


def test_exame_discovers_isolated_li_item_cards_before_semantic_filtering():
    connector = ExameConnector()
    connector._fetch_html = lambda _url: '''
      <main>
        <ul class="lista">
        <li class="item"><h3>P.M. de Santana de Pirapama - Concurso Público</h3>
          <p>Edital nº 01/2026 Inscrições de 12/10/2026 a 10/11/2026</p>
          <a href="/informacoes/544/">Mais Informações</a></li>
        <li class="item"><h3>P.M. de Córrego Fundo - Concurso Público</h3>
          <p>Edital nº 02/2026 Inscrições Abertas</p>
          <a href="/informacoes/536/">Quantidade de Vagas</a></li>
        <li class="item"><h3>P.M. de Maria da Fé - Processo Seletivo Interno - Diretores</h3>
          <a href="/informacoes/545/">Mais Informações</a></li>
        <li class="item"><h3>P.M. de Lagoa da Prata - Processo de Certificação Ocupacional</h3>
          <a href="/informacoes/525/">Mais Informações</a></li>
        <li class="item"><h3>C.M. de Lagoa Dourada - Concurso Público</h3>
          <p>Edital nº 01/2026 Inscrições encerradas</p>
          <a href="/informacoes/543/">Mais Informações</a></li>
        <li class="item"><h3>C.M. de Montalvânia - Concurso Público</h3>
          <p>Edital nº 01/2026 Inscrições encerradas</p>
          <a href="/informacoes/535/">Mais Informações</a></li>
        </ul>
      </main>'''

    candidates = connector._fetch_candidates()

    assert [item.external_id for item in candidates] == ['544', '536', '545', '525', '543', '535']
    assert all('/informacoes/' in item.detail_url for item in candidates)
    assert candidates[0].status_hint == 'Em andamento'


def test_exame_semantic_filter_rejects_internal_and_certification_details():
    from app.connectors.base import CandidateItem

    connector = ExameConnector()
    for title in (
        'P.M. de Maria da Fé - Processo Seletivo Interno - Diretores',
        'P.M. de Lagoa da Prata - Processo de Certificação Ocupacional',
    ):
        candidate = CandidateItem(title_hint=title, detail_url='https://concursos.exameconsultores.com.br/informacoes/1/')
        assert connector._parse_detail(candidate, f'<h1>{title}</h1>', client=MagicMock()) is None


def test_admtec_discovers_two_segment_publication_links_only():
    connector = ADMTECConnector()
    connector._fetch_html = lambda _url: '''
      <main>
        <article><h3>PREFEITURA MUNICIPAL DE PIRANHAS(AL)</h3>
          <p>Concurso público para provimento de vagas em cargos efetivos.</p>
          <a href="/concursos/publicacoes/MTEz/MTIx">Saiba Mais</a></article>
        <article><h3>PREFEITURA MUNICIPAL DE JOÃO ALFREDO(PE)</h3>
          <p>Concurso público para provimento de vagas em cargos efetivos.</p>
          <a href="/concursos/publicacoes/MTA4/MTE2">Saiba Mais</a></article>
        <article><h3>Formação ADM&amp;TEC</h3>
          <a href="/formacao">Saiba Mais</a></article>
      </main>'''

    candidates = connector._fetch_candidates()

    assert len(candidates) == 2
    assert [item.external_id for item in candidates] == ['MTEz/MTIx', 'MTA4/MTE2']
    assert all('/concursos/publicacoes/' in item.detail_url for item in candidates)


def test_exame_detail_extracts_official_fields_and_publications():
    connector = ExameConnector()
    from app.connectors.base import CandidateItem

    candidate = CandidateItem(
        title_hint='P.M. de Santana de Pirapama - Concurso Público Edital nº 01/2026',
        detail_url=EXAME_DETAIL_URL,
        status_hint='Em andamento',
        external_id='544',
    )
    html = '''
      <h1>Exame Auditores &amp; Consultores</h1>
      <h2>P.M. de Santana de Pirapama - Concurso Público</h2>
      <p>Inscrições de 12/10/2026 a 10/11/2026</p>
      <p>Situação: Em andamento</p>
      <a href="https://anexos-r2.selecao.net.br/edital-01.pdf">EDITAL 10/08/2026</a>
      <a href="https://anexos-r2.selecao.net.br/errata.pdf">RERRATIFICAÇÃO Nº 01 11/08/2026</a>
        <table><tr><th>Vaga</th><th>Qtde.</th></tr>
            <tr><td>AGENTE ADMINISTRATIVO I</td><td>3</td></tr>
            <tr><td>PROFESSOR</td><td>10</td></tr>
            <tr><td>OUTROS CARGOS</td><td>66</td></tr></table>'''
    pdf_fields = {
        'vagas': 79, 'salario_min': Decimal('1518.00'),
        'salario_max': Decimal('5120.00'), 'taxa': Decimal('80.00'),
        'cidade': 'Santana de Pirapama', 'uf': 'MG', 'cargo': None,
        'area': None, 'escolaridade': 'Múltiplas', 'prova_data': None,
        'raw_pdf_fields': {},
    }
    with patch('app.connectors.dedicated.national.extract_pdf_fields_if_possible',
               return_value=({'ok': True, 'text_hash': 'fixture', 'pages': 46}, pdf_fields, 'EDITAL', None)):
        parsed = connector._parse_detail(candidate, html, client=MagicMock())

    assert parsed is not None
    assert parsed['titulo'].startswith('P.M. de Santana de Pirapama')
    assert parsed['cidade'] == 'Santana de Pirapama'
    assert parsed['uf'] == 'MG'
    assert parsed['status'] == 'Em andamento'
    assert parsed['vagas'] == 79
    assert parsed['salario_min'] == Decimal('1518.00')
    assert parsed['taxa'] == Decimal('80.00')
    assert len(parsed['raw_data']['publications']) == 2


def test_admtec_detail_extracts_identity_fee_pdf_and_publications():
    connector = ADMTECConnector()
    from app.connectors.base import CandidateItem

    candidate = CandidateItem(
        title_hint='PREFEITURA MUNICIPAL DE PIRANHAS(AL) Concurso público',
        detail_url='https://www.admtec.org.br/concursos/publicacoes/MTEz/MTIx',
        status_hint='Em andamento',
        external_id='MTEz/MTIx',
    )
    html = '''
      <h1>PREFEITURA MUNICIPAL DE PIRANHAS - AL</h1>
      <p>Concurso público para o provimento de 40 vagas em cargos efetivos.</p>
      <p>Período de Inscrições: 10/04/2026 - 00:00:00 a 11/05/2026 - 23:59:59</p>
      <a href="https://admtec.s3.sa-east-1.amazonaws.com/edital.pdf">Edital do Concurso</a>
      <div>09/04/2026 <a href="https://admtec.s3.sa-east-1.amazonaws.com/diario.pdf">Diário Oficial - Publicação do edital</a></div>
      <div>Valor da Inscrição <strong>R$ 125,00</strong></div>
      <p>GUARDA MUNICIPAL</p>'''
    pdf_fields = {
        'vagas': 40, 'salario_min': Decimal('1621.00'),
        'salario_max': Decimal('1621.00'), 'taxa': Decimal('125.00'),
        'cidade': 'Piranhas', 'uf': 'AL', 'cargo': 'GUARDA MUNICIPAL',
        'area': 'seguranca_publica', 'escolaridade': 'Ensino Médio',
        'prova_data': None, 'raw_pdf_fields': {},
    }
    with patch('app.connectors.dedicated.national.extract_pdf_fields_if_possible',
               return_value=({'ok': True, 'text_hash': 'fixture', 'pages': 20}, pdf_fields, 'EDITAL', None)):
        parsed = connector._parse_detail(candidate, html, client=MagicMock())

    assert parsed is not None
    assert parsed['orgao'].startswith('PREFEITURA MUNICIPAL DE PIRANHAS')
    assert parsed['cidade'] == 'Piranhas'
    assert parsed['uf'] == 'AL'
    assert parsed['vagas'] == 40
    assert parsed['taxa'] == Decimal('125.00')
    assert parsed['salario_min'] == Decimal('1621.00')
    assert parsed['raw_data']['publications']


def test_admtec_historical_detail_is_not_labelled_open_and_dropbox_is_normalized():
    from app.connectors.base import CandidateItem

    connector = ADMTECConnector()
    candidate = CandidateItem(
        title_hint='PREFEITURA MUNICIPAL DE TESTE(PE) Concurso público',
        detail_url='https://www.admtec.org.br/concursos/publicacoes/a/b',
        external_id='a/b',
    )
    html = '''
      <h1>PREFEITURA MUNICIPAL DE TESTE - PE</h1>
      <p>Concurso público para provimento de 6 vagas.</p>
      <p>Período de Inscrições: 01/01/2025 a 31/01/2025</p>
      <p>AGENTE ADMINISTRATIVO</p>
      <a href="https://www.dropbox.com/s/abc/resultado.pdf?dl=0">Resultado final 20/02/2025</a>'''
    with patch('app.connectors.dedicated.national.extract_pdf_fields_if_possible',
               return_value=({'ok': False, 'error': '404', 'text_hash': None, 'pages': None}, {}, None, None)):
        parsed = connector._parse_detail(candidate, html, client=MagicMock())

    assert parsed is not None
    assert parsed['status'] == 'Encerrado'
    assert parsed['link_edital'] is None
    assert parsed['raw_data']['publications'][0]['link'].endswith('dl=1')


def test_admtec_normalizes_dropbox_download_parameter():
    assert ADMTECConnector._normalize_document_url(
        'https://www.dropbox.com/s/abc/edital.pdf?dl=0'
    ).endswith('?dl=1')


@pytest.mark.live
@pytest.mark.skipif(os.getenv('RUN_LIVE_CONNECTORS') != '1', reason='opt-in live portal audit')
def test_exame_live_audited_listing_and_sample_detail():
    connector = ExameConnector()
    candidates = connector._fetch_candidates()
    assert len(candidates) == 6
    sample = next(item for item in candidates if item.external_id == '544')
    result = connector.crawl_with_diagnostics()
    assert result.run_data.candidates_found == 6
    assert result.run_data.candidates_rejected == 2
    assert sample.detail_url.endswith('/informacoes/544/')
    assert len(result.items) == 4
    assert any(item['external_id'] == '544' and item['vagas'] == 79 for item in result.items)


@pytest.mark.live
@pytest.mark.skipif(os.getenv('RUN_LIVE_CONNECTORS') != '1', reason='opt-in live portal audit')
def test_admtec_live_audited_homepage():
    connector = ADMTECConnector()
    candidates = connector._fetch_candidates()
    assert len(candidates) == 4
    result = connector.crawl_with_diagnostics()
    assert result.run_data.candidates_found == 4
    assert result.run_data.candidates_rejected == 0
