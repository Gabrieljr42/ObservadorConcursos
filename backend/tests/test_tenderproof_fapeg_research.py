import pytest
from app.tenderproof.fapeg_adapter import FapegAdapter,RESEARCH_LISTINGS
from app.tenderproof.security import DestinationBlocked


def listing(year=2028,extra=''):
    return f'''<article><section class="entry-content"><table class="planilhaview"><thead><tr><th>Nº</th><th>Tipo</th><th>Origem</th><th>Descrição</th><th>Link</th></tr></thead><tbody><tr><td>23/{year}</td><td>Chamada Pública</td><td>Fapeg</td><td>Seleção de bolsistas</td><td><a href="https://goias.gov.br/fapeg/chamada-23-{year}/">ABRIR</a></td>{extra}</tr></tbody></table></section></article>'''


def detail(year=2028):
    return f'''<article><h2 class="entry-title">Chamada Pública 23/{year} FAPEG</h2><section class="entry-content"><a href="/fapeg/wp-content/uploads/sites/5/{year}/09/original.pdf">Edital</a><a href="/fapeg/wp-content/uploads/sites/5/{year}/09/errata.pdf">1ª Retificação</a></section></article>'''


def test_live_table_shape_and_future_year_without_sample_ids():
    a=FapegAdapter();p=a.parse_listing(listing(),RESEARCH_LISTINGS[0]);c=p.candidates[0]
    assert len(a.listing_urls)==4 and len(p.next_urls)==2
    assert c.external_id=='https://goias.gov.br/fapeg/chamada-23-2028/'
    a.confirm_identity(c,detail(),c.external_id)
    assert [d.kind for d in a.documents(detail(),c)]==['edital','retificacao']
    assert a.parse_listing(listing(extra='<td></td><td></td>'),RESEARCH_LISTINGS[2]).candidates


def test_preview_links_and_nonempty_extra_columns_remain_pending():
    a=FapegAdapter()
    for html in (listing().replace('chamada-23-2028/','?p=123&preview=true'),listing(extra='<td>missing annex</td><td></td>')):
        p=a.parse_listing(html,RESEARCH_LISTINGS[0]);assert p.truncated and not p.candidates and p.diagnostics


def test_wrong_detail_year_and_external_document_block_manifest():
    a=FapegAdapter();c=a.parse_listing(listing(),RESEARCH_LISTINGS[0]).candidates[0]
    for html in (detail(2027),detail().replace('/fapeg/wp-content/uploads/sites/5/2028/09/errata.pdf','https://outside.example/errata.pdf')):
        with pytest.raises((ValueError,DestinationBlocked)):a.documents(html,c)


def test_unclassified_complementary_link_is_not_silently_ignored():
    a=FapegAdapter();c=a.parse_listing(listing(),RESEARCH_LISTINGS[0]).candidates[0]
    html=detail().replace('</section>','<a href="https://outside.example/form">Inscrição</a></section>')
    with pytest.raises(ValueError):a.documents(html,c)


def test_original_and_pdf_identity_are_required():
    from types import SimpleNamespace
    a=FapegAdapter();c=a.parse_listing(listing(),RESEARCH_LISTINGS[0]).candidates[0]
    with pytest.raises(ValueError):a.documents(detail().replace('>Edital<','>Resultado<'),c)
    assert a.document_identity_ids(c,[SimpleNamespace(text='FAPEG CHAMADA 23/2028')])=={c.external_id}
    assert a.document_identity_ids(c,[SimpleNamespace(text='FAPEG CHAMADA 22/2028')])!={c.external_id}


@pytest.mark.parametrize('number',['Edital 23/2028','2028/23'])
def test_observed_historical_number_formats(number):
    a=FapegAdapter();html=listing().replace('<td>23/2028</td>',f'<td>{number}</td>')
    assert a.parse_listing(html,RESEARCH_LISTINGS[2]).candidates[0].title_observed.startswith('23/2028 |')


@pytest.mark.parametrize('article_id,year,expected', [('9876',2028,1),('9877',2028,0),('9876',2027,0)])
def test_public_preview_resolution_requires_article_id_and_call_number(article_id,year,expected):
    from types import SimpleNamespace
    adapter=FapegAdapter();requests=[]
    html=listing().replace('https://goias.gov.br/fapeg/chamada-23-2028/','https://goias.gov.br/fapeg/?p=9876&preview=true')
    def fetch(url,validate,max_bytes):
        requests.append(url);validate(url)
        if url==RESEARCH_LISTINGS[0]:return SimpleNamespace(content=html.encode(),url_final=url)
        final='https://goias.gov.br/fapeg/chamada-23-2028/';validate(final)
        body=detail(year).replace('<article>',f'<article id="post-{article_id}">')
        return SimpleNamespace(content=body.encode(),url_final=final)
    acquired=adapter.acquire_listing(RESEARCH_LISTINGS[0],fetch)
    page=adapter.parse_listing(acquired,RESEARCH_LISTINGS[0])
    assert len(page.candidates)==expected
    assert requests==[RESEARCH_LISTINGS[0],'https://goias.gov.br/fapeg/?p=9876']
    assert ('data-observed-preview-url' in acquired)==bool(expected)
    assert page.truncated is (not bool(expected))


def test_public_resolution_rejects_external_redirect_before_fetch():
    from types import SimpleNamespace
    adapter=FapegAdapter()
    html=listing().replace('https://goias.gov.br/fapeg/chamada-23-2028/','https://goias.gov.br/fapeg/?p=9876&preview=true')
    def fetch(url,validate,max_bytes):
        validate(url)
        if url==RESEARCH_LISTINGS[0]:return SimpleNamespace(content=html.encode(),url_final=url)
        with pytest.raises((ValueError,DestinationBlocked)):validate('https://outside.example/private/')
        raise ValueError('external redirect blocked')
    page=adapter.parse_listing(adapter.acquire_listing(RESEARCH_LISTINGS[0],fetch),RESEARCH_LISTINGS[0])
    assert not page.candidates and page.truncated
