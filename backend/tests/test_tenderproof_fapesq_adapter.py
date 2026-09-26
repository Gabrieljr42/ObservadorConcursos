import json
from types import SimpleNamespace
import pytest
import httpx
from app.tenderproof.fapesq_adapter import FapesqAdapter

A = FapesqAdapter()
ROOT = A.listing_urls[0]
ANNUAL = 'https://fapesq.rpp.br/editais/2038/editais-2038'
COLLECTION = ANNUAL.replace('/editais-2038', '/colecao-de-editais-2038')
DETAIL = ANNUAL.replace('/editais-2038', '/selecao-tecnica')
FILE = 'https://fapesq.rpp.br/editais/edital.pdf'


def fetcher(mapping):
    def fetch(url, validate, max_bytes):
        validate(url)
        final, body = mapping[url]
        validate(final)
        return SimpleNamespace(url_final=final, content=body.encode())
    return fetch


def test_menu_uses_observed_year_and_rejects_auth_redirect():
    body = '<div id="content"><a href="'+COLLECTION+'">Mais</a></div>'
    page = A.parse_listing(A.acquire_listing(ROOT, fetcher({ROOT: (ANNUAL, body)})), ROOT)
    assert page.next_urls == [COLLECTION]
    assert not page.candidates and not page.empty_evidence
    with pytest.raises(ValueError):
        A.acquire_listing(ROOT, fetcher({ROOT: ('https://fapesq.rpp.br/login', body)}))


def test_collection_truncation_does_not_claim_terminal():
    body = '<div id="content">'+''.join('<h2 class="tileHeadline"><a href="'+DETAIL+suffix+'">Seleção</a></h2>' for suffix in ('-a','-b'))+'<ul class="listingBar"><li><span>1</span></li></ul></div>'
    acquired = A.acquire_listing(COLLECTION, fetcher({COLLECTION: (COLLECTION, body)}))
    page = A.parse_listing(acquired, COLLECTION, limit=1)
    assert page.truncated and page.terminal_evidence is None and len(page.candidates) == 1
    assert len(A.parse_listing(acquired, COLLECTION).candidates) == 2


def detail_body(links):
    return '<link rel="canonical" href="'+DETAIL+'"><div id="content"><h1 class="documentFirstHeading">Seleção</h1><div id="parent-fieldname-text">'+links+'</div></div>'


def test_file_page_is_bound_to_observed_manifest_and_preserves_original():
    candidate = A.candidate_from_url(DETAIL)
    result = 'https://fapesq.rpp.br/editais/resultado.pdf'
    download = result+'/@@download/file/Resultado.pdf'
    body = detail_body('<a href="'+FILE+'">Edital 7/2038</a><a href="'+result+'/view">Resultado</a>')
    view = '<link rel="canonical" href="'+result+'"><div id="content"><a href="'+download+'">PDF</a></div>'
    acquired = A.acquire_detail(DETAIL, candidate, fetcher({DETAIL: (DETAIL, body), result+'/view': (result+'/view', view)}))
    docs = A.documents(acquired, candidate)
    assert [d.url_requested for d in docs] == [FILE, download]
    assert A.choose_document(docs).url_requested == FILE
    for doc in docs:
        A.validate_document_url(doc.url_requested, candidate)
    changed = json.loads(acquired)
    changed['file_pages'] = {}
    with pytest.raises(ValueError): A.documents(json.dumps(changed), candidate)
    with pytest.raises(ValueError): A.confirm_identity(candidate, acquired, DETAIL+'-other')


def test_malformed_links_and_foreign_downloads_fail_explicitly():
    candidate = A.candidate_from_url(DETAIL)
    body = detail_body('<a href="'+FILE+'">Edital</a><a href="http://Edital Nº 32">Inválido</a>')
    with pytest.raises(ValueError, match='malformado'):
        A.acquire_detail(DETAIL, candidate, fetcher({DETAIL: (DETAIL, body)}))
    for url in ('https://evil.invalid/file.pdf', FILE+'?token=x', 'https://fapesq.rpp.br/editais/%2e%2e/file.pdf'):
        with pytest.raises(ValueError): A.validate_document_url(url, candidate)


def test_failed_file_page_remains_a_pending_document():
    candidate = A.candidate_from_url(DETAIL)
    broken = 'https://fapesq.rpp.br/editais/broken.pdf/view'
    body = detail_body('<a href="'+FILE+'">Edital 7/2038</a><a href="'+broken+'">Resultado</a>')
    def fetch(url, validate, max_bytes):
        validate(url)
        if url == broken:
            httpx.Response(404, request=httpx.Request('GET', url)).raise_for_status()
        return SimpleNamespace(url_final=url, content=body.encode())
    acquired = A.acquire_detail(DETAIL, candidate, fetch)
    docs = A.documents(acquired, candidate)
    assert len(docs) == 2 and docs[1].url_requested == broken
    assert 'PENDENTE' in docs[1].reason_chosen and '404' in docs[1].reason_chosen
    assert A.choose_document(docs).url_requested == FILE
    with pytest.raises(ValueError): A.validate_document_url(broken, candidate)
