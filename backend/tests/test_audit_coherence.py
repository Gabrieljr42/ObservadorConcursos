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
from app.connectors.registry import MASTER_SOURCES, get_connector
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
