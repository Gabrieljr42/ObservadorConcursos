import json
import pytest
from app.tenderproof.batch99_fepese_adapter import FepeseAdapter
from app.tenderproof.solari_adapter import DownloadedBytes
from app.tenderproof.security import DestinationBlocked


def record(number):
    url=f'https://2026cpmunicipio{number}.fepese.org.br'
    return {'id':number,'title':{'rendered':f'Município {number}'},
            'content':{'rendered':f'<a href="{url}">Concurso Público – Edital 01/2026</a>'},
            'acf':{'link_hotsite':url}}


def acquisition(records, *, bad_total=False):
    adapter=FepeseAdapter();calls=[]
    def fetch(url,validate,max_bytes):
        validate(url);calls.append(url)
        headers={}
        if '/concursos/' in url:body='<div id="listaconcursos"></div>'
        elif '/tax_concurso_status?' in url:body=json.dumps([{'id':777,'slug':'encerrados'}])
        else:
            from urllib.parse import parse_qs,urlsplit
            query=parse_qs(urlsplit(url).query)
            assert query['tax_concurso_status_exclude']==['777']
            page=int(query['page'][0]);body=json.dumps(records[(page-1)*100:page*100])
            headers={'x-wp-total':str(len(records)+(1 if bad_total else 0)),
                     'x-wp-totalpages':str((len(records)+99)//100)}
        return DownloadedBytes(url_requested=url,url_final=url,content=body.encode(),pagination_headers=headers)
    raw=adapter.acquire_listing(adapter.listing_urls[0],fetch)
    return adapter,raw,calls


def test_catalog_fetches_all_pages_and_resolves_taxonomy_without_fixed_id():
    adapter,raw,calls=acquisition([record(n) for n in range(1,102)])
    result=adapter.parse_listing(raw,adapter.listing_urls[0])
    assert len(result.candidates)==101 and result.terminal_evidence
    assert not result.truncated and len(calls)==4
    assert 'page=2' in calls[-1]


def test_candidate_limit_keeps_catalog_partial():
    adapter,raw,_=acquisition([record(1),record(2)])
    result=adapter.parse_listing(raw,adapter.listing_urls[0],limit=1)
    assert len(result.candidates)==1 and result.truncated and not result.terminal_evidence


def test_missing_record_never_proves_end():
    with pytest.raises(ValueError,match='incompleta'):
        acquisition([record(1)],bad_total=True)


def test_duplicate_record_never_proves_end():
    adapter,raw,_=acquisition([record(1),record(1)])
    with pytest.raises(ValueError,match='repetido'):
        adapter.parse_listing(raw,adapter.listing_urls[0])


def test_uncorroborated_hotsite_remains_pending():
    item=record(1);item['acf']['link_hotsite']='https://2026wrong.fepese.org.br'
    adapter,raw,_=acquisition([item])
    result=adapter.parse_listing(raw,adapter.listing_urls[0])
    assert result.truncated and not result.candidates and not result.terminal_evidence


def test_multiple_edital_links_keep_separate_identities_and_tabs():
    item=record(1);base=item['acf']['link_hotsite']
    item['content']['rendered']=''.join(f'<a href="{base}/?go=home&amp;edital={n}">Concurso Público Edital {n}/2026</a>' for n in (1,2,3))
    adapter,raw,_=acquisition([item])
    page=adapter.parse_listing(raw,adapter.listing_urls[0])
    assert len({c.external_id for c in page.candidates})==3
    assert not page.truncated
    resource=base+'/?go=edital&mn='+'a'*32+'&edital=1'
    adapter.validate_detail_resource_url(resource,page.candidates[0])
    with pytest.raises(ValueError,match='outro edital'):
        adapter.validate_detail_resource_url(resource,page.candidates[1])


@pytest.mark.parametrize('url',[
    'https://evil.example/wp-json/wp/v2/concurso?per_page=100&page=1&tax_concurso_status_exclude=777',
    'https://fepese.org.br/wp-json/wp/v2/users?per_page=100',
    'https://fepese.org.br/wp-json/wp/v2/concurso?per_page=100&page=1&page=2&tax_concurso_status_exclude=777',
])
def test_catalog_urls_are_bounded(url):
    with pytest.raises((ValueError,DestinationBlocked)):FepeseAdapter().validate_catalog_url(url)


def test_http_catalog_guards_every_request_and_preserves_pagination_headers(monkeypatch):
    import httpx
    from app.tenderproof import http_driver
    monkeypatch.setattr(http_driver,'_public_dns',lambda host:None)
    checks=[]
    def handler(request):
        if request.url.path=='/concursos/':return httpx.Response(200,text='<div id="listaconcursos"></div>')
        if request.url.path.endswith('tax_concurso_status'):return httpx.Response(200,json=[{'id':777,'slug':'encerrados'}])
        return httpx.Response(200,json=[record(1)],headers={'x-wp-total':'1','x-wp-totalpages':'1'})
    driver=http_driver.BoundedHTTPDriver('fepese_open',client=httpx.Client(transport=httpx.MockTransport(handler)))
    driver.request_guard=lambda:checks.append(True)
    try:
        raw=driver.open_listing('https://fepese.org.br/concursos/')
        page=driver.adapter.parse_listing(raw,'https://fepese.org.br/concursos/')
        assert len(checks)==3 and len(page.candidates)==1 and page.terminal_evidence
    finally:driver.close()
