import pytest
from app.tenderproof.fapema_listing import HOST,parse_listing


def body(pager):
    return '<main id="main"><div class="search-results"><div class="search-result-item"><h3><a href="'+HOST+'/nova-chamada/">Nova chamada</a></h3></div></div><div class="pagination">'+pager+'</div></main>'


def test_empty_pager_preserves_items_without_certifying_terminal():
    r=parse_listing(body(''),HOST+'/category/editais/editais-em-julgamento/')
    assert len(r['items'])==1 and not r['terminal'] and r['diagnostics']


def test_observed_pagination_and_last_page_identity():
    url=HOST+'/category/editais/editais-encerrados/'
    r=parse_listing(body('<span aria-current="page">1</span><a class="next" href="'+url+'page/2/">Next</a>'),url)
    assert r['next_urls']==[url+'page/2/'] and not r['terminal']
    html=body('<a href="'+url+'">1</a><span aria-current="page">2</span>')
    assert parse_listing(html,url+'page/2/')['terminal']
    with pytest.raises(ValueError):parse_listing(html,url)
    with pytest.raises(ValueError):parse_listing(html.replace('href="'+url+'"','href="https://evil.test/"'),url+'page/2/')
