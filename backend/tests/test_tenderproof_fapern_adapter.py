import json
from types import SimpleNamespace
import pytest
import httpx
from app.tenderproof.fapern_adapter import FapernAdapter,folder_url
from app.tenderproof.fapern_listing import PORTAL,SHARE,discover_share,FapernDirectoryRequest
from app.tenderproof.fapern_drive import ROOT
from test_tenderproof_fapern_drive import document,response

TOKEN='PublicFixture123'
BASE=SHARE+TOKEN


def test_large_scanned_pdf_requires_explicit_bounded_source_policy():
    from app.tenderproof.continuous_store import SourcePolicy
    assert SourcePolicy().max_download_bytes==30*1024*1024
    assert SourcePolicy(max_download_bytes=45_000_000).max_download_bytes==45_000_000
    with pytest.raises(ValueError): SourcePolicy(max_download_bytes=64*1024*1024+1)


def service(share=BASE):
    return {'id':987,'title':{'rendered':'Editais — FAPERN'},'acf':{'orgao_serv':[{'slug':'fapern'}], 'link_externo':share}}


def test_discovery_scans_all_pages_and_requires_unique_official_service():
    calls=[]
    def fetch(url,validator,limit):
        validator(url);calls.append(url)
        return SimpleNamespace(content=json.dumps([] if url.endswith('1') else [service()]).encode(),pagination_headers={'x-wp-totalpages':'2'})
    assert discover_share(fetch)['share_url']==BASE and len(calls)==2
    for rows in [[service(),{**service(),'id':988}], [service(SHARE+'bad')], []]:
        with pytest.raises(ValueError):discover_share(lambda *a:SimpleNamespace(content=json.dumps(rows).encode(),pagination_headers={'x-wp-totalpages':'1'}))


def test_folder_discovery_manifest_and_document_confinement():
    adapter=FapernAdapter();path=ROOT+'Editais 2031/Seleção 45/'
    url=folder_url(BASE,path);candidate=adapter.candidate_from_url(url)
    def payload(rows):return json.dumps({'format':'fapern-directory/1','url':url,'path':path,'proof':{'share_url':BASE},'rows':rows})
    rows=[{'path':path+name,'name':name,'is_directory':False} for name in ['Edital de Abertura.pdf','Termo de Retificação pdf']]
    assert adapter.parse_listing(payload(rows),url).candidates[0].external_id==candidate.external_id
    docs=adapter.documents(payload(rows),candidate)
    assert len(docs)==2 and docs[1].kind=='retificacao'
    assert adapter.choose_document(docs)==docs[0]
    for doc in docs: adapter.validate_document_url(doc.url_requested,candidate)
    for bad in [docs[0].url_requested.replace('Sele%C3%A7%C3%A3o+45','Outra'),docs[0].url_requested.replace(TOKEN,'OtherToken123')]:
        with pytest.raises(ValueError):adapter.validate_document_url(bad,candidate)
    with pytest.raises(ValueError):adapter.documents(payload([{**rows[0],'path':ROOT+'elsewhere/file.pdf'}]),candidate)


def test_only_public_propfind_transport_and_no_redirect_credentials(monkeypatch):
    from app.tenderproof import http_driver
    monkeypatch.setattr(http_driver,'_public_dns',lambda host:None)
    request=FapernDirectoryRequest(TOKEN,ROOT)
    url='https://drive.rn.gov.br'+ROOT
    seen=[]
    def handler(req):
        seen.append(req)
        assert req.method=='PROPFIND' and req.headers['Depth']=='1'
        assert req.headers['Authorization']==request.transport(url,'fapern_selection')['headers']['Authorization']
        return httpx.Response(207,content=document(response(ROOT,True)))
    driver=http_driver.BoundedHTTPDriver('fapern_selection',client=httpx.Client(transport=httpx.MockTransport(handler)))
    driver._fetch(url,lambda target:None,10000,public_listing_request=request)
    assert len(seen)==1
    for target,source in [('https://evil.invalid/','fapern_selection'),(url,'fapeam_selection')]:
        with pytest.raises(ValueError):request.transport(target,source)
    driver.client.close()
    driver=http_driver.BoundedHTTPDriver('fapern_selection',client=httpx.Client(transport=httpx.MockTransport(lambda req:httpx.Response(302,headers={'Location':'https://evil.invalid/'}))))
    with pytest.raises(ValueError):driver._fetch(url,lambda target:None,10000,public_listing_request=request)
    driver.close()


@pytest.mark.parametrize('name', ['Edital 42-2033.PDF', 'Edital 42 2033.pdf', 'DOE - Edital 42-2033.pdf'])
def test_numbered_original_without_opening_label(name):
    adapter=FapernAdapter();path=ROOT+'Editais 2033/Edital 42-2033/'
    url=folder_url(BASE,path);candidate=adapter.candidate_from_url(url)
    names=[name,'Resultado Edital 42-2033.pdf','Retificação Edital 42-2033.pdf','Anexo Edital 42-2033.pdf']
    def payload(items):
        return json.dumps({'format':'fapern-directory/1','url':url,'path':path,'proof':{'share_url':BASE},
            'rows':[{'path':path+n,'name':n,'is_directory':False} for n in items]})
    docs=adapter.documents(payload(names),candidate)
    assert adapter.choose_document(docs).title==name
    assert all(d.kind!='edital' for d in docs[1:])
    # A second observed version requires explicit document selection/review.
    with pytest.raises(ValueError,match='ambíguo'):
        adapter.choose_document(adapter.documents(payload(names+['Edital de Abertura.pdf']),candidate))
