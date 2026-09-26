"""Real ELO captures and controlled cross-tenant/pagination errors."""
import json
from pathlib import Path
import pytest
from bs4 import UnicodeDammit
from app.tenderproof.batch60_elo_adapter import EloAdapter
from app.tenderproof.batch30_own_adapters import ReisAdapter

ROOT=Path(__file__).parent/'fixtures/tenderproof_batch60_own'
def content(kind):return UnicodeDammit((ROOT/f'elo_open-{kind}.html').read_bytes(),is_html=True).unicode_markup

def test_public_api_observed_route_and_separate_tenant():
    a=EloAdapter();page=a.parse_listing(content('api-listing'),a.listing_urls[0])
    assert len(page.candidates)==7 and page.terminal_evidence
    assert page.candidates[0].external_id=='137'
    assert page.candidates[0].detail_url_observed.endswith('/concurso/137')
    assert a.request_headers(a.listing_urls[0])['X-TenantID']=='eloassessoria'
    assert ReisAdapter().request_headers(a.listing_urls[0])['X-TenantID']=='reisauditores'
    c=page.candidates[0];a.confirm_identity(c,content('api-detail0'),c.detail_url_observed)
    chosen=a.choose_document(a.documents(content('api-detail0'),c))
    assert chosen.title=='EDITAL' and '/sgs.eloassessoriaeservicos.com.br/' in chosen.url_requested
    with pytest.raises(ValueError):a.validate_document_url(chosen.url_requested.replace('sgs.eloassessoriaeservicos.com.br','sgs.reisauditores.com.br'),c)

@pytest.mark.parametrize('change',['count','last','duplicate'])
def test_inconsistent_pagination_is_not_empty(change):
    a=EloAdapter();data=json.loads(content('api-listing'))
    if change=='count':data['totalElements']+=1
    if change=='last':data['last']=False
    if change=='duplicate':data['content'][1]['id']=data['content'][0]['id']
    with pytest.raises(ValueError):a.parse_listing(json.dumps(data),a.listing_urls[0])

def test_wrong_detail_title_and_limited_page():
    a=EloAdapter();page=a.parse_listing(content('api-listing'),a.listing_urls[0])
    with pytest.raises(ValueError):a.confirm_identity(page.candidates[1],content('api-detail0'),page.candidates[1].detail_url_observed)
    limited=a.parse_listing(content('api-listing'),a.listing_urls[0],limit=1)
    assert limited.truncated
    with pytest.raises(ValueError):a.parse_listing('<p>Carregando concursos...</p>',a.listing_urls[0])
