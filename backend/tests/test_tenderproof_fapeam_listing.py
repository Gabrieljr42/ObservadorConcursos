import json
import pytest
from app.tenderproof.fapeam_listing import parse_listing, listing_request, validate_detail_url


def payload():
    return {'editais_formatted':[{'ID':91,'post_title':'Seleção &amp; fomento',
        'permalink':'https://www.fapeam.am.gov.br/editais/chamada-2032/',
        'vigencia':'30/10/2031 até 01/01/1970'}], 'paginacao':''}


def test_preserves_unclassified_items_and_period_without_turning_it_into_deadline():
    result=parse_listing(json.dumps(payload()),tab='fluxo-continuo',page=1)
    item=result['items'][0]
    assert item['title']=='Seleção & fomento'
    assert item['period_observed'].endswith('01/01/1970')
    assert item['scope_status']=='requires_document_review'
    assert result['terminal'] and not result['scope_complete']


def test_request_is_exact_read_protocol_not_arbitrary_post():
    url,request=listing_request('editais-resultados',7)
    assert url.endswith('?action=get-editais-resultados')
    assert request['body']=='tipo=editais-resultados&p=7&paginacao=1'
    for tab,page in [('other',1),('editais-abertos',0),('editais-abertos',True)]:
        with pytest.raises(ValueError):listing_request(tab,page)


def test_published_pagination_is_parsed_without_executing_actions():
    data=payload();data['paginacao']="<nav><span class='current'>2</span><a onclick=\"get_editais('editais-encerrados',1,true);\">1</a><a onclick=\"get_editais('editais-encerrados',3,true);\">3</a></nav>"
    result=parse_listing(json.dumps(data),tab='editais-encerrados',page=2)
    assert result['linked_pages']==[1,3] and not result['terminal']
    for changed in [data['paginacao'].replace('editais-encerrados','editais-resultados'),
        data['paginacao'].replace('true);','true);evil();'),data['paginacao'].replace('>2<','>9<')]:
        with pytest.raises(ValueError):parse_listing(json.dumps({**data,'paginacao':changed}),tab='editais-encerrados',page=2)


@pytest.mark.parametrize('url',[
    'https://evil.test/editais/chamada/', 'http://www.fapeam.am.gov.br/editais/chamada/',
    'https://www.fapeam.am.gov.br:443/editais/chamada/',
    'https://www.fapeam.am.gov.br/editais/a%2fb/',
    'https://www.fapeam.am.gov.br/editais/chamada/?next=1',
    'https://www.fapeam.am.gov.br/editais/chamada/#other',
])
def test_detail_identity_rejects_uncontracted_destinations(url):
    with pytest.raises(ValueError):validate_detail_url(url)


def test_partial_or_duplicate_response_does_not_become_empty_success():
    for data in [{}, {'editais_formatted':[]}, {**payload(),'editais_formatted':[{}]},
        {**payload(),'editais_formatted':payload()['editais_formatted']*2}]:
        with pytest.raises(ValueError):parse_listing(json.dumps(data),tab='editais-abertos',page=1)
    with pytest.raises(ValueError):parse_listing(json.dumps(payload()),tab='editais-abertos',page=2)


def make_driver(monkeypatch, handler, source='fapeam_selection'):
    import httpx
    from types import SimpleNamespace
    from app.tenderproof import http_driver
    monkeypatch.setattr(http_driver, 'get_source_adapter', lambda _: SimpleNamespace(source=source))
    monkeypatch.setattr(http_driver, '_public_dns', lambda _: None)
    return http_driver.BoundedHTTPDriver(source, client=httpx.Client(transport=httpx.MockTransport(handler)))


def test_bounded_http_uses_exact_public_read_protocol(monkeypatch):
    import httpx
    from app.tenderproof.fapeam_listing import acquire_page
    seen=[]
    def handler(request):
        seen.append(request)
        return httpx.Response(200, json=payload())
    driver=make_driver(monkeypatch,handler)
    try:
        response, parsed=acquire_page(driver._fetch,tab='editais-resultados',page=1)
        assert parsed['items'][0]['external_id']=='91'
        assert seen[0].method=='POST'
        assert seen[0].content==b'tipo=editais-resultados&p=1&paginacao=1'
        assert str(seen[0].url).endswith('?action=get-editais-resultados')
        assert response.mechanism=='http' and driver.requests==1
    finally:driver.close()


def test_listing_transport_rejects_redirect_before_second_request(monkeypatch):
    import httpx
    from app.tenderproof.fapeam_listing import acquire_page
    seen=[]
    def handler(request):
        seen.append(request)
        return httpx.Response(302,headers={'location':'https://evil.test/'})
    driver=make_driver(monkeypatch,handler)
    try:
        with pytest.raises(ValueError,match='redirect POST'):
            acquire_page(driver._fetch,tab='editais-abertos',page=1)
        assert len(seen)==1
    finally:driver.close()


def test_listing_transport_rejects_arbitrary_body_destination_and_source_before_network(monkeypatch):
    from app.tenderproof.fapeam_listing import FapeamListingRequest
    def handler(_):raise AssertionError('unexpected network')
    driver=make_driver(monkeypatch,handler)
    request=FapeamListingRequest('editais-abertos',1)
    url,_=listing_request(request.tab,request.page)
    try:
        for target,options in [
            (url,{'public_listing_request':{'method':'POST','body':'delete=1'}}),
            (url,{'public_listing_request':request,'acquisition_request':{'body':'1,0'}}),
            (url+'&delete=1',{'public_listing_request':request}),
        ]:
            with pytest.raises(ValueError):driver._fetch(target,lambda _:None,100,**options)
        driver.adapter.source='another_source'
        with pytest.raises(ValueError):driver._fetch(url,lambda _:None,100,public_listing_request=request)
        assert driver.requests==0
    finally:driver.close()


def test_listing_transport_enforces_response_bound(monkeypatch):
    import httpx
    from app.tenderproof.fapeam_listing import acquire_page
    driver=make_driver(monkeypatch,lambda _:httpx.Response(200,headers={'content-length':str(2*1024*1024+1)}))
    try:
        with pytest.raises(ValueError,match='Content-Length'):
            acquire_page(driver._fetch,tab='editais-abertos',page=1)
    finally:driver.close()
