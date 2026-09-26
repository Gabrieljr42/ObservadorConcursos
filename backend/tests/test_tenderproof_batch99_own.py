from pathlib import Path
import json
import pytest
from app.tenderproof.batch99_own_adapters import LegatusAdapter,KLCAdapter,NossoRumoAdapter
from app.tenderproof.security import DestinationBlocked

FIX=Path(__file__).parent/'fixtures/tenderproof_batch99_own'
def html(name):return (FIX/name).read_text(encoding='utf-8')

def test_legatus_official_listing_and_primary_document():
    a=LegatusAdapter();page=a.parse_listing(html('legatus_open-listing0.html'),a.listing_urls[0])
    assert len(page.candidates)==11
    c=page.candidates[0];assert c.external_id=='160' and 'TANQUE' in c.title_observed
    detail=html('legatus_open-detail0.html');a.confirm_identity(c,detail,c.detail_url_observed)
    docs=a.documents(detail,c);chosen=a.choose_document(docs)
    assert len(docs)==8 and chosen.url_requested.endswith('/3181/download/')
    assert all(d.kind!='edital' for d in docs if d.url_requested!=chosen.url_requested)
    limited=a.parse_listing(html('legatus_open-listing0.html'),a.listing_urls[0],limit=1)
    assert limited.truncated and not limited.terminal_evidence

def test_legatus_contradictory_detail_and_ambiguous_originals():
    a=LegatusAdapter();c=a.parse_listing(html('legatus_open-listing0.html'),a.listing_urls[0]).candidates[0]
    detail=html('legatus_open-detail0.html')
    with pytest.raises(ValueError):a.confirm_identity(c,detail,c.detail_url_observed.replace('/160/','/159/'))
    with pytest.raises(ValueError):a.confirm_identity(c,detail.replace('MUNICÍPIO DE TANQUE DO PIAUÍ - PI','OUTRO ÓRGÃO INCOMPATÍVEL'),c.detail_url_observed)
    # Explicit controlled new original; never requested from the portal.
    detail=detail.replace('</body>','<a href="/concursos/9999/download/">EDITAL Nº 02/2026 - ABERTURA DO CONCURSO</a></body>')
    with pytest.raises(ValueError):a.choose_document(a.documents(detail,c))

@pytest.mark.parametrize('url',['https://www.legatus.org.br/concursos/3181/download/','https://www.legatus.org.br/concursos/160/tanque/?id=9','https://127.0.0.1/concursos/160/tanque/'])
def test_legatus_invalid_detail_routes(url):
    with pytest.raises((ValueError,DestinationBlocked)):LegatusAdapter().validate_detail_url(url)

def test_legatus_shell_is_not_confirmed_empty():
    a=LegatusAdapter()
    page=a.parse_listing('<html><body>Carregando concursos...</body></html>',a.listing_urls[0])
    assert not page.candidates and not page.empty_evidence and not page.terminal_evidence

def test_klc_observed_listing_details_empty_tab_and_limit():
    a=KLCAdapter();page=a.parse_listing(html('klc_open-tab1.html'),a.listing_urls[0]);c=page.candidates[0]
    assert len(page.candidates)==199 and c.external_id=='632'
    detail=html('klc_open-detail0.html');a.confirm_identity(c,detail,c.detail_url_observed)
    docs=a.documents(detail,c)
    assert len(docs)==7 and a.choose_document(docs).url_requested.endswith('/4fe007a9a3f5afb03835272439f1812f.pdf')
    assert a.parse_listing(html('klc_open-tab1.html'),a.listing_urls[0],limit=1).truncated
    empty=a.parse_listing(html('klc_open-tab0.html'),a.listing_urls[0].replace('sub=2','sub=1'))
    assert not empty.candidates and empty.empty_evidence and empty.terminal_evidence
    unknown=a.parse_listing('<div id="submenu_result">Carregando</div>',a.listing_urls[0])
    assert not unknown.empty_evidence and not unknown.terminal_evidence

def test_klc_wrong_identity_and_supplementary_only():
    a=KLCAdapter();c=a.parse_listing(html('klc_open-tab1.html'),a.listing_urls[0]).candidates[0];detail=html('klc_open-detail0.html')
    with pytest.raises(ValueError):a.confirm_identity(c,detail,c.detail_url_observed.replace('id=632','id=631'))
    with pytest.raises(ValueError):a.confirm_identity(c,detail.replace('002-2026','999-2099'),c.detail_url_observed)
    with pytest.raises(ValueError):a.choose_document([d for d in a.documents(detail,c) if d.kind!='edital'])
    with pytest.raises(ValueError):a.validate_document_url('https://www.klcconcursos.com.br/privacy.pdf',c)
    with pytest.raises(ValueError):a.validate_detail_url(c.detail_url_observed+'&id=633')

def test_nossorumo_observed_cards_public_api_and_exact_document():
    a=NossoRumoAdapter();page=a.parse_listing(html('nossorumo_open-listing0.html'),a.listing_urls[0])
    assert len(page.candidates)==76 and page.candidates[0].external_id=='608'
    c=page.candidates[0];detail=html('nossorumo_open-api0.html')
    a.confirm_identity(c,detail,c.detail_url_observed)
    assert a.choose_document(a.documents(detail,c)).url_requested.endswith('/608-3788-639238739834481180.pdf')
    assert a.parse_listing(html('nossorumo_open-listing0.html'),a.listing_urls[0],limit=1).truncated

@pytest.mark.parametrize('change',['other_project','other_number','other_file','duplicate_id','html_shell'])
def test_nossorumo_wrong_or_ambiguous_public_payload(change):
    a=NossoRumoAdapter();c=a.parse_listing(html('nossorumo_open-listing0.html'),a.listing_urls[0]).candidates[0]
    data=json.loads(html('nossorumo_open-api0.html'))
    if change=='other_project':data['projeto']='OUTRO ÓRGÃO MUNICIPAL INCOMPATÍVEL'
    if change=='other_number':data['projeto']=data['projeto'].replace('03/2026','99/2099')
    if change=='other_file':data['editais'][0]['arquivo']=data['editais'][0]['arquivo'].replace('608-','607-')
    if change=='duplicate_id':data['editais'].append(dict(data['editais'][0]))
    detail='<html>Carregando</html>' if change=='html_shell' else json.dumps(data)
    with pytest.raises(ValueError):a.documents(detail,c)

def test_nossorumo_no_empty_marker_and_private_route_blocked():
    a=NossoRumoAdapter();page=a.parse_listing('<div>Carregando certames...</div>',a.listing_urls[0])
    assert not page.empty_evidence and not page.terminal_evidence
    with pytest.raises((ValueError,DestinationBlocked)):a.validate_detail_url('https://127.0.0.1/Home/GetPublicacoes?idProjeto=608')
    with pytest.raises(ValueError):a.validate_detail_url('https://nossorumo.org.br/Home/GetPublicacoes?idProjeto=608&idInscricao=1')
