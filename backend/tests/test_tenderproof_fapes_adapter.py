import json
from types import SimpleNamespace
import pytest
from app.tenderproof.fapes_adapter import FapesAdapter
from test_tenderproof_fapes_panels import panel

ROOT = 'https://fapes.es.gov.br/editais'
SECTION = 'https://fapes.es.gov.br/nova-area'
MENU = '<li class="dropdown"><a>Editais</a><ul><li class="dropdown"><a>Abertos</a><ul class="dropdown-menu"><li><a href="/nova-area">Nova área</a></li></ul></li></ul></li>'


def fixture(body):
    calls = []
    def fetch(url, validate, limit):
        calls.append(url)
        validate(url)
        return SimpleNamespace(url_final=url, content=(MENU if url == ROOT else body).encode())
    return fetch, calls


def test_dynamic_discovery_detail_identity_and_original():
    adapter = FapesAdapter()
    fetch, calls = fixture('<ul class="galeriade-arquivos">'+panel(99221, 'Nova chamada')+'</ul>')
    root = adapter.acquire_listing(ROOT, fetch)
    assert adapter.parse_listing(root, ROOT).next_urls == [SECTION]
    listing = adapter.acquire_listing(SECTION, fetch)
    candidate = adapter.parse_listing(listing, SECTION).candidates[0]
    proof = adapter.acquire_detail(candidate.detail_url_observed, candidate, fetch)
    adapter.confirm_identity(candidate, proof, candidate.detail_url_observed)
    docs = adapter.documents(proof, candidate)
    assert adapter.choose_document(docs).url_requested.endswith('/novo.pdf')
    assert calls == [ROOT, ROOT, SECTION, ROOT, SECTION]
    wrong = candidate.model_copy(update={'external_id': '1'})
    with pytest.raises(ValueError): adapter.documents(proof, wrong)


def test_unobserved_section_never_fetched_and_changed_menu_rejected():
    adapter = FapesAdapter()
    adapter.validate_listing_url('https://fapes.es.gov.br/forma%C3%A7%C3%A3o')
    with pytest.raises(ValueError): adapter.validate_listing_url('https://fapes.es.gov.br/%252e%252e/admin')
    fetch, calls = fixture('')
    with pytest.raises(ValueError): adapter.acquire_listing('https://fapes.es.gov.br/admin', fetch)
    assert calls == [ROOT]
    data = {'format': 'fapes-section/1', 'url': SECTION, 'menu': MENU.replace('/nova-area', '/outra'), 'html': ''}
    with pytest.raises(ValueError): adapter.parse_listing(json.dumps(data), SECTION)


def test_annual_archives_are_partial_and_blank_gallery_not_empty():
    adapter = FapesAdapter()
    fetch, _ = fixture('<ul class="galeriade-arquivos">'+panel(12, 'Editais Encerrados 2025')+panel(13, 'Atual')+'</ul>')
    listing = adapter.parse_listing(adapter.acquire_listing(SECTION, fetch), SECTION)
    assert listing.truncated and len(listing.candidates) == 1
    assert listing.candidates[0].external_id == '13'
    assert listing.diagnostics and not listing.empty_evidence
    fetch, _ = fixture('<h1>Em julgamento</h1>')
    with pytest.raises(ValueError): adapter.parse_listing(adapter.acquire_listing(SECTION, fetch), SECTION)


def test_duplicate_rows_do_not_duplicate_document_identity():
    adapter = FapesAdapter()
    body = '<ul class="galeriade-arquivos">'+panel(7, 'Atual')+'</ul>'
    row = body[body.index('<tr>'):body.index('</tr>')+5]
    fetch, _ = fixture(body.replace('</tbody>', row+'</tbody>'))
    proof = adapter.acquire_listing(SECTION, fetch)
    candidate = adapter.parse_listing(proof, SECTION).candidates[0]
    assert len(adapter.documents(proof, candidate)) == 1
    with pytest.raises(ValueError): adapter.validate_document_url('https://fapes.es.gov.br/Media/fapes/%252e%252e/x.pdf', candidate)
