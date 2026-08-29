import os
from decimal import Decimal
from unittest.mock import MagicMock, patch
import pytest
import httpx

from app.connectors.base import CandidateItem
from app.connectors.dedicated.idecan import IDECANConnector
from app.connectors.dedicated.consulplan import ConsulplanConnector
from app.connectors.dedicated.aocp import AOCPConnector

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), 'fixtures')


def _read_fixture(banca: str, filename: str) -> str:
    path = os.path.join(FIXTURES_DIR, banca, filename)
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()


def test_idecan_parser_with_fixtures():
    connector = IDECANConnector(base_url='https://idecan.org.br')
    listing_html = _read_fixture('idecan', 'listing.html')
    detail_html = _read_fixture('idecan', 'detail.html')

    # 1. Candidate discovery
    connector._fetch_html = MagicMock(return_value=listing_html)
    candidates = connector._fetch_candidates()
    assert len(candidates) >= 1
    cand = candidates[0]
    assert 'campina-grande' in cand.detail_url

    # 2. Detail extraction
    mock_client = MagicMock(spec=httpx.Client)
    item = connector._parse_detail(cand, detail_html, client=mock_client)
    assert item is not None
    assert 'Campina Grande' in item['titulo']
    assert item['banca'] == 'IDECAN'
    assert item['cidade'] == 'Campina Grande'
    assert item['uf'] == 'PB'
    assert item['vagas'] == 150
    assert item['taxa'] == Decimal('95.00')
    assert item['salario_min'] == Decimal('3500.00')
    assert item['salario_max'] == Decimal('8200.00')
    assert item['link_edital'] == 'https://idecan.org.br/editais/edital_abertura_01_2026.pdf'


def test_consulplan_parser_with_fixtures():
    connector = ConsulplanConnector(base_url='https://institutoconsulplan.org.br')
    listing_html = _read_fixture('consulplan', 'listing.html')
    detail_html = _read_fixture('consulplan', 'detail.html')

    connector._fetch_html = MagicMock(return_value=listing_html)
    candidates = connector._fetch_candidates()
    assert len(candidates) >= 1
    cand = candidates[0]
    assert 'codigo=1055' in cand.detail_url

    mock_client = MagicMock(spec=httpx.Client)
    item = connector._parse_detail(cand, detail_html, client=mock_client)
    assert item is not None
    assert 'juiz de fora' in item['titulo'].lower()
    assert item['banca'] == 'Instituto Consulplan'
    assert item['uf'] == 'MG'
    assert item['vagas'] == 45
    assert item['taxa'] == Decimal('80.00')
    assert item['salario_min'] == Decimal('4200.00')
    assert item['salario_max'] == Decimal('9800.00')
    assert item['link_edital'] == 'https://institutoconsulplan.org.br/editais/edital_abertura.pdf'


def test_aocp_parser_with_fixtures():
    connector = AOCPConnector(base_url='https://www.institutoaocp.org.br')
    listing_html = _read_fixture('aocp', 'listing.html')
    detail_html = _read_fixture('aocp', 'detail.html')

    connector._fetch_html = MagicMock(return_value=listing_html)
    candidates = connector._fetch_candidates()
    assert len(candidates) >= 1
    cand = candidates[0]
    assert 'id=990' in cand.detail_url

    mock_client = MagicMock(spec=httpx.Client)
    item = connector._parse_detail(cand, detail_html, client=mock_client)
    assert item is not None
    assert 'Paraná' in item['titulo'] or 'PR' in item['titulo']
    assert item['banca'] == 'Instituto AOCP'
    assert item['uf'] == 'PR'
    assert item['vagas'] == 60
    assert item['taxa'] == Decimal('120.00')
    assert item['salario_min'] == Decimal('6800.00')
    assert item['salario_max'] == Decimal('12500.00')
    assert item['link_edital'] == 'https://www.institutoaocp.org.br/editais/edital_tjpr.pdf'


def test_ibfc_regression_with_fixtures():
    from app.connectors.ibfc import IBFCOpenConnector
    connector = IBFCOpenConnector(base_url='https://concursos.ibfc.org.br')
    listing_html = _read_fixture('ibfc', 'listing.html')
    detail_html = _read_fixture('ibfc', 'detail.html')

    with patch.object(httpx.Client, 'get') as mock_get:
        mock_resp = MagicMock()
        mock_resp.text = listing_html
        mock_resp.raise_for_status.return_value = None
        mock_get.return_value = mock_resp
        candidates = connector._fetch_candidates()
        assert len(candidates) >= 1
        cand = candidates[0]
        assert '500' in cand.detail_url

    mock_client = MagicMock(spec=httpx.Client)
    item = connector._parse_detail(cand, detail_html, client=mock_client)
    assert item is not None
    assert 'SECRETARIA DE ESTADO' in item['titulo']
    assert item['banca'] == 'IBFC'
    assert item['uf'] == 'PR'
    assert item['status'].lower() == 'inscrições abertas'


def test_imeso_regression_with_fixtures():
    from app.connectors.imeso import IMESOOpenConnector
    connector = IMESOOpenConnector(base_url='https://portal.imeso.com.br')
    listing_html = _read_fixture('imeso', 'listing.html')
    detail_html = _read_fixture('imeso', 'detail.html')

    with patch.object(httpx.Client, 'get') as mock_get:
        mock_resp = MagicMock()
        mock_resp.text = listing_html
        mock_resp.raise_for_status.return_value = None
        mock_get.return_value = mock_resp
        candidates = connector._fetch_candidates()
        assert len(candidates) >= 1
        cand = candidates[0]
        assert '250' in cand.detail_url

    mock_client = MagicMock(spec=httpx.Client)
    item = connector._parse_detail(cand, detail_html, client=mock_client)
    assert item is not None
    assert 'VESPASIANO' in item['titulo'].upper()
    assert item['banca'] == 'IMESO'
    assert item['uf'] == 'MG'
    assert item['vagas'] == 80


def test_fundep_regression_with_fixtures():
    from app.connectors.fundep import FundepOpenConnector
    connector = FundepOpenConnector(base_url='https://www.gestaodeconcursos.com.br')
    listing_html = _read_fixture('fundep', 'listing.html')
    detail_html = _read_fixture('fundep', 'detail.html')

    with patch.object(httpx.Client, 'get') as mock_get:
        mock_resp = MagicMock()
        mock_resp.text = listing_html
        mock_resp.raise_for_status.return_value = None
        mock_get.return_value = mock_resp
        candidates = connector._fetch_candidates()
        assert len(candidates) >= 1
        cand = candidates[0]
        assert '1120' in cand.detail_url

    mock_client = MagicMock(spec=httpx.Client)
    item = connector._parse_detail(cand, detail_html, client=mock_client)
    assert item is not None
    assert 'MGS' in item['titulo']
    assert item['banca'] == 'FUNDEP'
    assert item['uf'] == 'MG'
    assert item['vagas'] == 200

