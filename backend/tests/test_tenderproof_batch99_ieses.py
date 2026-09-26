import json
from pathlib import Path
import pytest
from app.tenderproof.batch99_ieses_adapter import IESESAdapter

FIX=Path(__file__).parent/'fixtures/tenderproof_batch99_own'
def fixture(name):return (FIX/('ieses_open-'+name+'.html')).read_text(encoding='utf-8')

def test_observed_partial_discovery_and_original():
    a=IESESAdapter();p=a.parse_listing(fixture('api0'),a.listing_urls[0])
    assert len(p.candidates)==2 and p.truncated and not p.terminal_evidence
    assert p.next_urls==['https://ieses.org/projetos/api?offset=12&limit=12']
    c=p.candidates[0];detail=fixture('redirect-detail0')
    a.confirm_identity(c,detail,'https://scgas2026.ieses.org/')
    docs=a.documents(detail,c)
    assert len(docs)==5
    assert a.choose_document(docs).url_requested.endswith('/edital_20260810_101748.pdf')
    assert len([d for d in docs if d.kind=='edital'])==1
    with pytest.raises(ValueError):a.choose_document([d for d in docs if d.kind!='edital'])

@pytest.mark.parametrize('mutation',['duplicate','reuse','wrong_folder','shell'])
def test_fail_closed_json_contract(mutation):
    a=IESESAdapter();data=json.loads(fixture('api0'))
    if mutation=='duplicate':data['projetos'][1]['projectTokenKey']='0026'
    if mutation=='reuse':data['projetos'][0]['projectTokenKey']='9999'
    if mutation=='wrong_folder':data['projetos'][0]['pasta']='other'
    if mutation=='shell':data={}
    with pytest.raises(ValueError):a.parse_listing(json.dumps(data),a.listing_urls[0])

def test_empty_and_limit_are_explicit():
    a=IESESAdapter();p=a.parse_listing('{"projetos":[]}',a.listing_urls[0])
    assert p.empty_evidence and p.terminal_evidence and not p.candidates
    assert a.parse_listing(fixture('api0'),a.listing_urls[0],limit=1).truncated

def test_detail_year_and_document_association():
    a=IESESAdapter();c=a.parse_listing(fixture('api0'),a.listing_urls[0]).candidates[0]
    detail=fixture('redirect-detail0')
    with pytest.raises(ValueError):a.confirm_identity(c,detail,'https://crmvsc.ieses.org/')
    with pytest.raises(ValueError):a.confirm_identity(c,detail.replace('001/2026','999/2099'),c.detail_url_observed)
    with pytest.raises(ValueError):a.validate_document_url('https://'+a.cdn+'/2026/crmvsc/documentos/edital.pdf',c)
    with pytest.raises(ValueError):a.validate_listing_url(a.listing_urls[0]+'&offset=12')
