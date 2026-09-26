from types import SimpleNamespace
import pytest
from app.tenderproof.fapema_adapter import FapemaAdapter
from app.tenderproof.fapema_listing import HOST
from test_tenderproof_fapema_detail import fixture,URL


def test_acquisition_binds_dynamic_category_to_fresh_menu():
    adapter=FapemaAdapter();section=HOST+'/category/editais/editais-novos/'
    menu=f'<nav><a href="{section}">Novos</a></nav>'
    listing='<main id="main"><div class="search-results"><div class="search-result-item"><h3><a href="'+URL+'">Novo</a></h3></div></div></main>'
    calls=[]
    def fetch(url,validator,limit):
        calls.append(url);validator(url)
        return SimpleNamespace(url_final=url,content=(menu if url==adapter.listing_urls[0] else listing).encode())
    proof=adapter.acquire_listing(section,fetch)
    assert adapter.parse_listing(proof,section).candidates[0].detail_url_observed==URL
    assert calls==[adapter.listing_urls[0],section]
    calls.clear()
    with pytest.raises(ValueError):adapter.acquire_listing(HOST+'/category/editais/editais-desconhecidos/',fetch)
    assert calls==[adapter.listing_urls[0]]


def test_html_amendment_cannot_be_ignored_by_document_selection():
    adapter=FapemaAdapter();candidate=adapter.candidate_from_url(URL)
    with pytest.raises(ValueError,match='aviso HTML'):adapter.documents(fixture(),candidate)
    html=fixture().replace('<p>COMUNICADO: recursos prorrogados até 15/02.</p>','')
    docs=adapter.documents(html,candidate)
    assert adapter.choose_document(docs).kind=='edital'
