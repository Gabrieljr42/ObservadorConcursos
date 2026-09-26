import pytest
from app.tenderproof.fapesq_listing import collection_url,parse_collection
from app.tenderproof.fapesq_listing import parse_annual

BASE='https://fapesq.rpp.br/editais/2034/colecao-de-editais-2034'


def page(pager):
    return '<div id="content"><h2 class="tileHeadline"><a href="https://fapesq.rpp.br/editais/2034/selecao-tecnica">Seleção técnica</a></h2><ul class="listingBar">'+pager+'</ul></div>'


def test_public_pagination_uses_observed_next_and_explicit_last_page():
    result=parse_collection(page('<li><span>1</span></li><li><a class="proximo" href="?b_start:int=25">Próximo</a></li>'),BASE)
    assert result['next_url']==BASE+'?b_start:int=25' and not result['terminal']
    assert parse_collection(page('<li><a href="'+BASE+'">1</a></li><li><span>2</span></li>'),BASE+'?b_start:int=25')['terminal']


@pytest.mark.parametrize('url',[BASE+'?b_start:int=-1',BASE.replace('2034/colecao','2033/colecao'),BASE.replace('fapesq.rpp.br','evil.invalid'),BASE+'?came_from=login'])
def test_only_public_collection_navigation(url):
    with pytest.raises(ValueError):collection_url(url)


def test_missing_pager_and_regressive_navigation_are_not_exhaustion():
    with pytest.raises(ValueError):parse_collection(page(''),BASE)
    with pytest.raises(ValueError):parse_collection(page('<li><a class="proximo" href="?b_start:int=0">Próximo</a></li>'),BASE+'?b_start:int=25')


def test_annual_navigation_retains_broken_links_without_guessing_paths():
    url=BASE.replace('colecao-de-editais','editais')
    html='<div id="content"><a href="'+BASE+'">Mais</a><a href="/editais/2032/editais-2032">Editais de 2032</a><a href="https://fapesq.rpp.br/../editais-2031">Editais de 2031</a></div>'
    result=parse_annual(html,url)
    assert result['collection']==BASE
    assert result['annuals']==['https://fapesq.rpp.br/editais/2032/editais-2032']
    assert result['unresolved_links']==['https://fapesq.rpp.br/../editais-2031']
    with pytest.raises(ValueError):parse_annual(html.replace('colecao-de-editais-2034','colecao-de-editais-2033'),url)
