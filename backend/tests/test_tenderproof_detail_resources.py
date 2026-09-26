"""Controlled transport proofs for bounded public detail resource composition."""
import json
from types import SimpleNamespace
import httpx
import pytest
from app.tenderproof import http_driver as module
from app.tenderproof.security import DestinationBlocked,TenderProofSettings,TenderProofLimits,validate_destination

URL='https://example.org/detail/42'
RESOURCES=['https://example.org/api/identity?id=42','https://example.org/api/documents?id=42']

class Adapter:
    source='controlled'
    def candidate_from_url(self,url):
        self.validate_detail_url(url)
        return SimpleNamespace(source=self.source,external_id='42',detail_url_observed=url)
    def validate_detail_url(self,url):
        if url!=URL:raise ValueError('different detail')
    def detail_resource_urls(self,html,url):return RESOURCES
    def validate_detail_resource_url(self,url,candidate):
        validate_destination(url,allowlist=('example.org',))
        if url not in RESOURCES or candidate.external_id!='42':raise ValueError('different resource identity')
    def compose_detail(self,html,url,resources):return json.dumps({'url':url,'html':html,'resources':resources})

@pytest.fixture
def setup(monkeypatch):
    adapter=Adapter();calls=[]
    monkeypatch.setattr(module,'get_source_adapter',lambda source:adapter)
    monkeypatch.setattr(module,'_public_dns',lambda host:None)
    def build(handler=None,max_requests=3):
        def transport(request):
            calls.append(str(request.url))
            return handler(request) if handler else httpx.Response(200,text='observed '+str(request.url))
        client=httpx.Client(transport=httpx.MockTransport(transport))
        return module.BoundedHTTPDriver('controlled',TenderProofSettings(limits=TenderProofLimits(max_navigations=max_requests)),client=client)
    return adapter,calls,build

def test_composed_snapshot_preserves_response_urls_and_bodies(setup):
    _,calls,build=setup;driver=build()
    try:
        result=json.loads(driver.open_detail(URL))
        assert calls==[URL,*RESOURCES] and driver.requests==3
        assert result['resources']==[{'url':u,'body':'observed '+u} for u in RESOURCES]
    finally:driver.close()

@pytest.mark.parametrize('urls',[[RESOURCES[0]]*2,RESOURCES*2,[RESOURCES[0],'http://127.0.0.1/secret'],['https://example.org/api/identity?id=99']])
def test_reject_entire_invalid_plan_before_any_supplementary_request(setup,urls):
    adapter,calls,build=setup;adapter.detail_resource_urls=lambda html,url:urls;driver=build()
    try:
        with pytest.raises((ValueError,DestinationBlocked)):driver.open_detail(URL)
        assert calls==[URL]
    finally:driver.close()

def test_redirect_does_not_fetch_other_resource_or_private_destination(setup):
    _,calls,build=setup
    driver=build(lambda request:httpx.Response(200,text='detail') if str(request.url)==URL else httpx.Response(302,headers={'location':'http://127.0.0.1/secret'}))
    try:
        with pytest.raises(DestinationBlocked):driver.open_detail(URL)
        assert calls==[URL,RESOURCES[0]]
    finally:driver.close()

def test_navigation_budget_is_shared_with_detail(setup):
    _,calls,build=setup;driver=build(max_requests=2)
    try:
        with pytest.raises(ValueError,match='requisições'):driver.open_detail(URL)
        assert calls==[URL,RESOURCES[0]]
    finally:driver.close()

def test_composed_snapshot_size_is_bounded(setup):
    adapter,_,build=setup;adapter.compose_detail=lambda *args:'x'*(2*1024*1024+1);driver=build()
    try:
        with pytest.raises(ValueError,match='tamanho'):driver.open_detail(URL)
    finally:driver.close()

def test_partial_resources_never_return_completed_snapshot(setup):
    _,calls,build=setup
    driver=build(lambda request:httpx.Response(503) if str(request.url)==RESOURCES[1] else httpx.Response(200,text='observed'))
    try:
        with pytest.raises(httpx.HTTPStatusError):driver.open_detail(URL)
        assert calls==[URL,*RESOURCES]
    finally:driver.close()
