"""Official JSON captures plus explicitly synthetic negative mutations."""
import json
from pathlib import Path

import pytest

from app.tenderproof.batch30_uniselva_adapter import UniselvaAdapter
from app.tenderproof.security import DestinationBlocked

FIXTURES = Path(__file__).parent / 'fixtures/tenderproof_batch30_institutional'


def setup():
    adapter = UniselvaAdapter()
    listing = (FIXTURES / 'uniselva-api-listing.json').read_text(encoding='utf-8')
    detail = (FIXTURES / 'uniselva-api-detail.json').read_text(encoding='utf-8')
    candidate = next(c for c in adapter.parse_listing(listing, adapter.listing_urls[0]).candidates if c.external_id == '1363')
    return adapter, listing, detail, candidate


def test_observed_listing_pagination_and_correct_document():
    a, listing, detail, c = setup()
    page = a.parse_listing(listing, a.listing_urls[0])
    assert len(page.candidates) == 9
    assert page.next_urls == [a.listing_url(2)]
    assert not page.terminal_evidence
    assert a.parse_listing(listing, a.listing_urls[0], limit=1).truncated
    a.confirm_identity(c, detail, c.detail_url_observed)
    docs = a.documents(detail, c)
    assert len(docs) == 2
    chosen = a.choose_document(docs)
    assert 'CONTRATA' in chosen.title
    assert 'PORTARIA' not in chosen.title
    assert '%20' in chosen.url_requested
    assert a.choose_document(a.documents(detail, c)).doc_id == chosen.doc_id


@pytest.mark.parametrize('key,value', [('page', 2), ('pageSize', 10), ('totalPage', 1), ('total', -1), ('items', [])])
def test_synthetic_inconsistent_pagination_is_failure(key, value):
    a, listing, _, _ = setup()
    data = json.loads(listing)
    data[key] = value
    with pytest.raises(ValueError):
        a.parse_listing(json.dumps(data), a.listing_urls[0])


def test_synthetic_explicit_empty_exclusion_and_challenge():
    a, listing, _, _ = setup()
    data = json.loads(listing)
    data.update(items=[], total=0, totalPage=0)
    assert a.parse_listing(json.dumps(data), a.listing_urls[0]).empty_evidence
    for title in ('EDITAL BOLSA DE PESQUISA', 'SELEÇÃO DE BOLSISTA', 'VESTIBULAR 2026'):
        assert not a.in_scope(title)
    for content in ('<html>app-root</html>', '<html>Just a moment</html>', '{}'):
        with pytest.raises(ValueError):
            a.parse_listing(content, a.listing_urls[0])


@pytest.mark.parametrize('change', ['id', 'title', 'foreign_document', 'external_host', 'traversal'])
def test_synthetic_identity_and_document_guards(change):
    a, _, detail, c = setup()
    data = json.loads(detail)
    if change == 'id':
        data['id'] = 1
    elif change == 'title':
        data['titulo'] = 'CONCURSO POLÍCIA MILITAR PARA SOLDADOS'
    elif change == 'foreign_document':
        data['documentos'][0]['idSelecao'] = 1
    elif change == 'external_host':
        data['documentos'][0]['arquivo'] = 'https://example.org/test.pdf'
    else:
        data['documentos'][0]['arquivo'] = 'https://web.fundacaouniselva.org.br/Editais/1363/../test.pdf'
    with pytest.raises((ValueError, DestinationBlocked)):
        a.documents(json.dumps(data), c)


def test_synthetic_ambiguous_principals_require_review():
    a, _, detail, c = setup()
    data = json.loads(detail)
    duplicate = dict(data['documentos'][1])
    duplicate['arquivo'] = duplicate['arquivo'].replace('.pdf', '-versao.pdf')
    data['documentos'].append(duplicate)
    with pytest.raises(ValueError):
        a.choose_document(a.documents(json.dumps(data), c))
