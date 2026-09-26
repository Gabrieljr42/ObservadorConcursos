import json
import httpx
import pytest
from pathlib import Path
from app.tenderproof.fapeam_adapter import FapeamAdapter,LISTING,LIVE_LISTING
from app.tenderproof.http_driver import BoundedHTTPDriver
from app.tenderproof.source_adapters import get_source_adapter

BASE='https://www.fapeam.am.gov.br/editais/uma-selecao/'
PDF='https://www.fapeam.am.gov.br/wp-content/uploads/2032/04/abertura.pdf'


def listing():
    return json.dumps({'editais_formatted':[{'ID':98765,'post_title':'Uma seleção',
        'permalink':BASE,'vigencia':'período observado'}],
        'paginacao':"<span class='current'>1</span><a onclick=\"get_editais('editais-encerrados',2,true);\">2</a>"})


def detail(identity='98765'):
    return f'<link rel="canonical" href="{BASE}"><article class="post-type-editais" id="post-{identity}"><h1 class="page-title">Uma seleção</h1><div class="article-body"><div class="download-documento-box"><a href="{PDF}">Edital</a></div></div></article>'


def test_registered_http_path_listing_to_detail_to_pdf(monkeypatch):
    seen=[]
    def handler(request):
        seen.append(request)
        if request.method=='POST':return httpx.Response(200,text=listing())
        if str(request.url)==BASE:return httpx.Response(200,text=detail())
        assert str(request.url)==PDF
        return httpx.Response(200,content=b'%PDF-1.7\ncontrolled',headers={'content-type':'application/pdf'})
    monkeypatch.setattr('app.tenderproof.http_driver._public_dns',lambda _:None)
    driver=BoundedHTTPDriver('fapeam_selection',client=httpx.Client(transport=httpx.MockTransport(handler)))
    adapter=get_source_adapter('fapeam_selection')
    url=LISTING+'?aba=editais-encerrados&p=1'
    try:
        parsed=adapter.parse_listing(driver.open_listing(url),url)
        assert parsed.next_urls==[LISTING+'?aba=editais-encerrados&p=2']
        assert not parsed.terminal_evidence
        candidate=parsed.candidates[0]
        assert candidate.external_id=='98765'
        driver.set_candidate(candidate)
        html=driver.open_detail(candidate.detail_url_observed)
        docs=adapter.documents(html,candidate)
        downloaded=driver.download(adapter.choose_document(docs).url_requested,max_bytes=1000)
        assert downloaded.content.startswith(b'%PDF') and len(seen)==3
        assert str(seen[1].url)==BASE
    finally:driver.close()


def test_candidate_identity_cannot_be_reassigned():
    adapter=FapeamAdapter();candidate=adapter.candidate_from_url(BASE+'#post-98765')
    with pytest.raises(ValueError):adapter.confirm_identity(candidate,detail('98766'),candidate.detail_url_observed)
    with pytest.raises(ValueError):adapter.documents(detail(),candidate.model_copy(update={'external_id':'98766'}))


def test_current_vigentes_navigation_alias_parses_live_ajax_fixture():
    adapter=FapeamAdapter()
    payload=(Path(__file__).parent/'fixtures/tenderproof_batch99_regions/fapeam_vigentes_live.json').read_text(encoding='utf-8')
    page=adapter.parse_listing(payload,LIVE_LISTING,limit=5)
    assert len(page.candidates)==5
    assert page.candidates[0].external_id=='321428'
    assert page.candidates[0].detail_url_observed.endswith('#post-321428')
    assert page.terminal_evidence=='Resposta de paginação validada sem página posterior.'
    assert adapter.validate_listing_url('https://www.fapeam.am.gov.br/editais/?aba=vigentes') is None


def test_inline_edital_amendment_enters_review_without_becoming_principal():
    adapter=FapeamAdapter();candidate=adapter.candidate_from_url(BASE+'#post-98765')
    html=detail().replace('class="download-documento-box"','class="reference"')
    html=html.replace('>Edital</a>','>Decisão n.º 777/2032 – Solicitação de Retificação de Edital.</a>')
    docs=adapter.documents(html,candidate)
    assert len(docs)==1 and docs[0].kind=='retificacao'
    with pytest.raises(ValueError):adapter.choose_document(docs)


@pytest.mark.parametrize('url',[LISTING,LISTING+'?aba=editais-abertos&p=0',
    LISTING+'?aba=other&p=1',LISTING+'?aba=editais-abertos&p=1&action=delete',
    BASE,BASE+'#post-0',BASE+'#post-1#post-2'])
def test_uncontracted_cursors_or_detail_identities_are_rejected(url):
    adapter=FapeamAdapter()
    with pytest.raises(ValueError):adapter.validate_listing_url(url)
    with pytest.raises(ValueError):adapter.validate_detail_url(url)
