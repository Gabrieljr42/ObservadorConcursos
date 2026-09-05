from __future__ import annotations

import json
import re
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.connectors.base import BaseConnector, CandidateItem, CrawlResult, CrawlRunData
from app.connectors.configurable import ConfigurableHTMLConnector, SourceDefinition
from app.connectors.institutional import InstitutionalSelectionConnector
from app.connectors.registry import MASTER_SOURCES, get_connector
from app.audit_validation import build_field_audit
from app.database import Base
from app.models import Concurso, Source
from app.services import CrawlService


def test_master_sources_exact_count_99():
    """Verify that MASTER_SOURCES has exactly 99 unique sources."""
    assert len(MASTER_SOURCES) == 99
    source_types = [s.source_type for s in MASTER_SOURCES]
    assert len(set(source_types)) == 99


def test_unconfirmed_empty_yields_degraded():
    """A connector finding zero candidates without explicit empty evidence MUST yield degraded."""
    class DummyConnector(BaseConnector):
        banca = 'Dummy'
        def _fetch_candidates(self) -> list[CandidateItem]:
            return []

    conn = DummyConnector('https://dummy.example.com')
    res = conn.crawl_with_diagnostics()
    assert res.run_data.status == 'degraded'
    assert res.run_data.error_type == 'UnconfirmedEmpty'
    assert res.run_data.diagnostics_payload.get('empty_evidence') is None


def test_rejection_reason_codes_keep_quality_gate_candidate_trace():
    class DummyRejectedConnector(BaseConnector):
        banca = 'Dummy'

        def _fetch_candidates(self) -> list[CandidateItem]:
            return [CandidateItem(title_hint='Concurso de teste', detail_url='https://dummy.example.com/1')]

        def _fetch_html(self, url: str, *, reason: str | None = None) -> str:
            return '<html></html>'

        def _parse_detail(self, candidate, html: str, *, client):
            return None

    result = DummyRejectedConnector('https://dummy.example.com').crawl_with_diagnostics()

    assert result.run_data.candidates_rejected == 1
    assert result.run_data.diagnostics_payload['rejection_counts']['quality_gate'] == 1
    assert result.run_data.diagnostics_payload['rejections'][0]['reason'] == 'quality_gate'


def test_blocked_discovery_is_not_relabelled_as_ambiguous_empty():
    class DummyBlockedConnector(BaseConnector):
        banca = 'Dummy'

        def _fetch_candidates(self) -> list[CandidateItem]:
            self.run_data.status = 'blocked'
            self.run_data.error_type = 'CloudflareChallenge'
            self.run_data.error_message = 'challenge'
            return []

    result = DummyBlockedConnector('https://dummy.example.com').crawl_with_diagnostics()

    assert result.run_data.status == 'blocked'
    assert result.run_data.error_type == 'CloudflareChallenge'
    assert result.run_data.error_message == 'challenge'


def test_explicitly_closed_detail_keeps_closed_rejection_reason():
    class DummyClosedConnector(BaseConnector):
        banca = 'Dummy'

        def _fetch_candidates(self) -> list[CandidateItem]:
            return [CandidateItem(title_hint='Concurso encerrado', detail_url='https://dummy.example.com/1')]

        def _fetch_html(self, url: str, *, reason: str | None = None) -> str:
            return '<html></html>'

        def _parse_detail(self, candidate, html: str, *, client):
            self.mark_empty_evidence('evaluated_closed', 'registration window ended', candidate.detail_url)
            return None

    result = DummyClosedConnector('https://dummy.example.com').crawl_with_diagnostics()

    assert result.run_data.diagnostics_payload['rejection_counts']['evaluated_closed'] == 1
    assert result.run_data.diagnostics_payload['rejections'][0]['reason'] == 'evaluated_closed'


def test_explicit_text_yields_empty_valid():
    """A connector with explicit empty evidence MUST yield empty_valid."""
    class DummyEmptyConnector(BaseConnector):
        banca = 'Dummy'
        def _fetch_candidates(self) -> list[CandidateItem]:
            self.mark_empty_evidence('explicit_text', 'Nenhum concurso disponível no momento')
            return []

    conn = DummyEmptyConnector('https://dummy.example.com')
    res = conn.crawl_with_diagnostics()
    assert res.run_data.status == 'empty_valid'
    assert res.run_data.diagnostics_payload.get('empty_evidence') is not None
    assert res.run_data.diagnostics_payload['empty_evidence']['kind'] == 'explicit_text'


def test_api_empty_yields_empty_valid():
    """An API connector returning empty collection MUST yield empty_valid with structured evidence."""
    class DummyAPIConnector(BaseConnector):
        banca = 'Dummy'
        def _fetch_candidates(self) -> list[CandidateItem]:
            self.mark_empty_evidence('api_empty', 'Endpoint /api/concursos returned 0 items')
            return []

    conn = DummyAPIConnector('https://dummy.example.com')
    res = conn.crawl_with_diagnostics()
    assert res.run_data.status == 'empty_valid'
    assert res.run_data.diagnostics_payload['empty_evidence']['kind'] == 'api_empty'


def test_crawler_only_populated_field_is_unknown_not_match():
    audit = build_field_audit({}, {'titulo': 'Concurso Público 01/2026', 'vagas': 42})
    assert audit['titulo'] == 'UNKNOWN'
    assert audit['vagas'] == 'UNKNOWN'


def test_independent_expected_difference_is_mismatch():
    audit = build_field_audit(
        {'titulo': 'Concurso Público para Salvador'},
        {'titulo': 'Concurso Público para Recife'},
    )
    assert audit['titulo'] == 'MISMATCH'


def test_money_formatting_matches_independent_value():
    audit = build_field_audit(
        {'salario_min': 'R$ 1.500,00'},
        {'salario_min': 1500.0},
    )
    assert audit['salario_min'] == 'MATCH'


def test_url_comparison_ignores_www_alias():
    audit = build_field_audit(
        {'link_inscricao': 'https://msconcursos.com.br/inscricao'},
        {'link_inscricao': 'https://www.msconcursos.com.br/inscricao'},
    )
    assert audit['link_inscricao'] == 'MATCH'


def test_title_comparison_ignores_state_suffix():
    audit = build_field_audit(
        {'titulo': 'Prefeitura Municipal de Piranhas-Alagoas'},
        {'titulo': 'Prefeitura Municipal de Piranhas'},
    )
    assert audit['titulo'] == 'MATCH'


def test_unknown_independent_count_does_not_become_verified():
    from scripts.run_full_live_audit import _verification_status

    entry = {'crawler_status': 'success', 'processed': 1, 'visible_valid_items': None}
    evidence = {'independent': True, 'expected': {'titulo': 'Official contest'}}
    field_audit = build_field_audit(evidence['expected'], {'titulo': 'Official contest'})
    assert _verification_status(entry, evidence, field_audit, {'status': 'UNKNOWN'}) == 'NOT_AUDITED'


def test_verified_requires_identity_and_two_domain_matches():
    from scripts.run_full_live_audit import _verification_status

    entry = {'crawler_status': 'success', 'processed': 1, 'visible_valid_items': 1}
    evidence = {
        'independent': True,
        'expected': {
            'titulo': 'Concurso Público 01/2026',
            'orgao': 'Prefeitura de Teste',
            'cidade': 'Teste',
            'uf': 'MG',
            'link_edital': 'https://example.org/edital.pdf',
        },
    }
    field_audit = build_field_audit(evidence['expected'], evidence['expected'])
    assert _verification_status(entry, evidence, field_audit, {'status': 'MATCH'}) == 'VERIFIED'


def test_verified_without_identity_is_not_audited():
    from scripts.run_full_live_audit import _verification_status

    entry = {'crawler_status': 'success', 'processed': 1, 'visible_valid_items': 1}
    evidence = {
        'independent': True,
        'expected': {'link_edital': 'https://example.org/edital.pdf', 'uf': 'MG', 'cidade': 'Teste'},
    }
    field_audit = build_field_audit(evidence['expected'], evidence['expected'])
    assert _verification_status(entry, evidence, field_audit, {'status': 'MATCH'}) == 'NOT_AUDITED'


def test_verified_with_only_one_domain_match_is_not_audited():
    from scripts.run_full_live_audit import _verification_status

    entry = {'crawler_status': 'success', 'processed': 1, 'visible_valid_items': 1}
    evidence = {
        'independent': True,
        'expected': {'titulo': 'Concurso Público 01/2026', 'orgao': 'Prefeitura de Teste', 'uf': 'MG'},
    }
    actual = {'titulo': 'Concurso Público 01/2026', 'orgao': 'Prefeitura de Teste', 'uf': 'MG'}
    field_audit = build_field_audit(evidence['expected'], actual)
    assert _verification_status(entry, evidence, field_audit, {'status': 'MATCH'}) == 'NOT_AUDITED'


def test_generic_official_heading_is_not_used_as_expected_title():
    from bs4 import BeautifulSoup
    from scripts.run_full_live_audit import _extract_official_expected

    expected, _ = _extract_official_expected(
        BeautifulSoup('<html><head><title>IBAM - Instituto</title></head><body><h1>Informações do concurso</h1></body></html>', 'lxml'),
        'https://example.org/concursos/1',
    )

    assert 'titulo' not in expected


def test_official_text_observer_preserves_words_and_line_boundaries():
    from bs4 import BeautifulSoup
    from scripts.run_full_live_audit import _official_text

    observed = _official_text(
        BeautifulSoup('<main><p>Concurso Público</p><p>Inscrições: 03/08/2026 a 04/09/2026.</p></main>', 'lxml')
    )

    assert observed == 'Concurso Público\nInscrições: 03/08/2026 a 04/09/2026.'


def test_official_observer_decodes_legacy_portal_text():
    import httpx
    from scripts.run_full_live_audit import _decode_official_response

    response = httpx.Response(200, content='Polícia Militar'.encode('cp1252'))

    assert _decode_official_response(response) == 'Polícia Militar'


def test_singular_generic_official_heading_is_not_used_as_expected_title():
    from bs4 import BeautifulSoup
    from scripts.run_full_live_audit import _extract_official_expected

    expected, _ = _extract_official_expected(
        BeautifulSoup('<html><body><h1>Concurso aberto</h1></body></html>', 'lxml'),
        'https://example.org/concursos/1',
    )

    assert 'titulo' not in expected


def test_official_title_fallback_recognizes_police_contest_after_portal_brand():
    from bs4 import BeautifulSoup
    from scripts.run_full_live_audit import _extract_official_expected

    expected, _ = _extract_official_expected(
        BeautifulSoup(
            '<html><head><title>FCC - Polícia Militar do Piauí - PM/PI</title></head>'
            '<body><p>Concurso Público. Período de inscrição: 03/08/2026 a 04/09/2026.</p></body></html>',
            'lxml',
        ),
        'https://example.org/concursos/pompi126/index.html',
    )

    assert expected['titulo'] == 'Polícia Militar do Piauí - PM/PI'
    assert expected['inscricao_inicio'] is not None
    assert expected['inscricao_fim'] is not None


def test_official_observer_rejects_brand_only_heading_and_generic_city_fragment():
    from bs4 import BeautifulSoup
    from scripts.run_full_live_audit import _extract_official_expected

    expected, _ = _extract_official_expected(
        BeautifulSoup(
            '<html><head><title>FUMARC</title></head><body>'
            '<h1>Fundação Mariana Resende Costa</h1>'
            '<p>Professor A - PA</p>'
            '</body></html>',
            'lxml',
        ),
        'https://example.org/concursos/1',
    )

    assert 'titulo' not in expected
    assert 'cidade' not in expected
    assert 'uf' not in expected


def test_official_observer_uses_explicit_municipality_location():
    from bs4 import BeautifulSoup
    from scripts.run_full_live_audit import _extract_official_expected

    expected, _ = _extract_official_expected(
        BeautifulSoup(
            '<html><body><h1>Concurso Prefeitura de Carbonita - MG</h1>'
            '<p>Vagas para: Carbonita / MG</p></body></html>',
            'lxml',
        ),
        'https://example.org/concursos/1',
    )

    assert expected['cidade'] == 'Carbonita'
    assert expected['uf'] == 'MG'


def test_empty_valid_with_independent_zero_active_is_empty_verified():
    from scripts.run_full_live_audit import _verification_status

    entry = {
        'crawler_status': 'empty_valid',
        'visible_active_valid_items': 0,
        'empty_evidence': None,
    }
    evidence = {
        'metric_evidence': {
            'active_basis': 'official registration tab explicitly empty',
        },
    }

    assert _verification_status(entry, evidence, None, None) == 'EMPTY_VERIFIED'


def test_empty_official_heading_does_not_crash_observer():
    from bs4 import BeautifulSoup
    from scripts.run_full_live_audit import _extract_official_expected

    expected, _ = _extract_official_expected(
        BeautifulSoup('<html><head><title>IBAM</title></head><body><h1></h1><h2> </h2></body></html>', 'lxml'),
        'https://example.org/concursos/1',
    )

    assert 'titulo' not in expected
def test_publication_noise_is_not_accepted():
    from app.publications import is_valid_publication_title

    assert not is_valid_publication_title('Aviso de Privacidade')
    assert not is_valid_publication_title('Aviso de Cookies')
    assert not is_valid_publication_title('Aceitar')
    assert not is_valid_publication_title('Privacidade')
    assert not is_valid_publication_title('Pular para o conteúdo principal')
    assert is_valid_publication_title('Edital de abertura')


def test_unobserved_publications_are_unknown():
    from scripts.run_full_live_audit import _audit_publications

    result = _audit_publications(
        {'expected_titles': ['Edital de abertura'], 'expected_links': []},
        [],
        actual_observed=False,
    )

    assert result['status'] == 'UNKNOWN'
    assert result['actual_count'] is None


def test_institutional_zero_candidates_without_evidence_is_degraded(monkeypatch):
    definition = SourceDefinition(
        source_type='institutional_empty_test',
        name='Institutional empty test',
        banca='TEST',
        base_url='https://example.org',
        list_urls=['https://example.org/editais'],
        category='institutional_selection',
    )
    connector = InstitutionalSelectionConnector(definition)
    monkeypatch.setattr(connector, '_fetch_html', lambda url: '<html><body><h1>Editais</h1><p>Conteúdo carregado.</p></body></html>')
    result = connector.crawl_with_diagnostics()
    assert result.items == []
    assert result.run_data.status == 'degraded'
    assert result.run_data.diagnostics_payload.get('empty_evidence') is None


def test_source_specific_explicit_empty_state_is_accepted():
    definition = SourceDefinition(
        source_type='explicit_empty_test',
        name='Explicit empty test',
        banca='TEST',
        base_url='https://example.org',
        list_urls=['https://example.org/andamento'],
        empty_state_patterns=[r'nenhum item cadastrado'],
    )
    connector = ConfigurableHTMLConnector(definition)
    monkeypatch = lambda url: '<html><body><p>Nenhum item cadastrado.</p></body></html>'
    # Avoid network while exercising the same source-specific empty matcher.
    connector._fetch_html = monkeypatch
    result = connector.crawl_with_diagnostics()
    assert result.items == []
    assert result.run_data.status == 'empty_valid'
    assert result.run_data.diagnostics_payload['empty_evidence']['kind'] == 'explicit_text'


def test_fgv_candidate_filter_excludes_portfolio_and_fragment_links(monkeypatch):
    from app.connectors.dedicated.national import FGVConnector

    definition = next(source for source in MASTER_SOURCES if source.source_type == 'fgv_open')
    connector = FGVConnector(base_url=definition.base_url, list_url=definition.list_urls[0])
    html = '''
    <html><body>
      <a href="/concursos/pms2026">Prefeitura de Salvador</a>
      <a href="/concursos/pms2026#arquivos">Fragmento</a>
      <a href="/nosso-portfolio#tabs">Nosso Portfólio</a>
      <a href="/concursos/busca">Busca</a>
    </body></html>
    '''
    monkeypatch.setattr(connector, '_fetch_html', lambda url: html)

    candidates = connector._fetch_candidates()

    assert [candidate.detail_url for candidate in candidates] == ['https://conhecimento.fgv.br/concursos/pms2026']


def test_consulplan_cross_source_deduplication():
    """Verify that cross-source deduplication prevents duplicate contests from alias sources."""
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    # Create Source 7 and Source 38
    src1 = Source(id=7, source_type='consulplan_open', name='CONSULPLAN', base_url='https://www.consulplan.net', active=True)
    src2 = Source(id=38, source_type='institutoconsulplan_open', name='Instituto Consulplan', base_url='https://institutoconsulplan.org.br', active=True)
    db.add_all([src1, src2])
    db.commit()

    service = CrawlService(db)

    # Ingest contest from Source 7
    item1 = {
        'external_id': '800',
        'banca': 'Instituto Consulplan',
        'orgao': 'Prefeitura Municipal de Teste',
        'titulo': 'Concurso Público 01/2026',
        'modalidade': 'Concurso Público',
        'cargo': 'Auditor',
        'status': 'Inscrições abertas',
        'link_pagina': 'https://institutoconsulplan.org.br/concurso.aspx?codigo=800',
        'link_edital': 'https://institutoconsulplan.org.br/edital.pdf',
        'vagas': 10,
        'content_hash': 'hash_800_v1',
    }

    # Match when none exists -> creates
    existing1 = service._find_existing_concurso(7, item1)
    assert existing1 is None

    c1 = Concurso(source_id=7, **item1)
    db.add(c1)
    db.commit()

    # Now ingest the same contest from Source 38 (different source_id, same link_pagina / banca+external_id)
    item2 = {
        'external_id': '800',
        'banca': 'Instituto Consulplan',
        'orgao': 'Prefeitura Municipal de Teste',
        'titulo': 'Concurso Público 01/2026 - Atualizado',
        'modalidade': 'Concurso Público',
        'cargo': 'Auditor',
        'status': 'Inscrições abertas',
        'link_pagina': 'https://institutoconsulplan.org.br/concurso.aspx?codigo=800',
        'vagas': 15,
        'content_hash': 'hash_800_v2',
    }

    existing2 = service._find_existing_concurso(38, item2)
    assert existing2 is not None
    assert existing2.id == c1.id
    assert existing2.external_id == '800'
    db.close()


def test_generated_docs_match_master_sources(tmp_path):
    """Test that docs generated from audit_live_99.json have exactly 99 valid rows without control characters."""
    from scripts.generate_live_audit_docs import generate_live_sources_audit_md, generate_live_audit_issues_md

    # Mock audit data with 99 sources
    sources = []
    for idx, s in enumerate(MASTER_SOURCES, 1):
        sources.append({
            'index': idx,
            'source_type': s.source_type,
            'name': s.name,
            'canonical_name': s.banca,
            'category': s.category,
            'url': s.list_urls[0] if s.list_urls else s.base_url,
            'status': 'empty_valid',
            'http_status': 200,
            'browser_used': False,
            'processed': 0,
            'empty_evidence': {'kind': 'evaluated_closed', 'value': 'test evidence'},
        })

    mock_audit = {
        'generated_at': '2026-08-29T18:00:00Z',
        'summary': {
            'total_sources': 99,
            'success': 0,
            'empty_valid': 99,
            'blocked': 0,
            'failed': 0,
            'degraded': 0,
            'total_items': 0,
            'duration_seconds': 10.0,
        },
        'sources': sources,
    }

    doc_path = tmp_path / 'LIVE_SOURCES_AUDIT.md'
    generate_live_sources_audit_md(mock_audit, doc_path)

    content = doc_path.read_text(encoding='utf-8')
    # Check no control characters escaped incorrectly
    for bad_char in ['\x00', '\x07', '\x08', '\x0c']:
        assert bad_char not in content

    # Find table rows with | 01 | ... | 99 |
    table_rows = re.findall(r'^\|\s*(\d{2})\s*\|', content, re.MULTILINE)
    assert len(table_rows) == 99
    assert table_rows[0] == '01'
    assert table_rows[-1] == '99'
