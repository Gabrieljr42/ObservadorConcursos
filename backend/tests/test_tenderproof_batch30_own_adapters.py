"""Contracts against dated raw HTTP captures; negative mutations are synthetic."""
from pathlib import Path
import json
import pytest
from bs4 import UnicodeDammit
from app.tenderproof.batch30_own_adapters import BATCH30_OWN_ADAPTERS
from app.tenderproof.contracts import DocumentCandidate
from app.tenderproof.source_adapters import SourcePageBlocked

ROOT=Path(__file__).parent/'fixtures/tenderproof_batch30_own'
ADAPTERS={a.source:a for a in BATCH30_OWN_ADAPTERS}
FIXTURES={
 'ibfc_open':('ibfc_ongoing','https://concursos.ibfc.org.br/index/1/','496','ibfc_detail'),
 'admtec_open':('admtec_browser_ua','https://admtec.org.br/','MTEz/MTIx','admtec_detail'),
 'institutomais_open':('institutomais_open','https://www.institutomais.org.br/Concursos/ConcursosAbertos','10646','institutomais_detail2'),
 'reisesreis_open':('reis_api',ADAPTERS['reisesreis_open'].listing_urls[0],'70','reis_detail')}


def html(name):
 return UnicodeDammit((ROOT/(name+'-listing.html')).read_bytes(),is_html=True).unicode_markup


def sample(source):
 adapter=ADAPTERS[source];listing,url,external,detail=FIXTURES[source]
 page=adapter.parse_listing(html(listing),url,200)
 candidate=next(c for c in page.candidates if c.external_id==external)
 return adapter,page,candidate,html(detail)


@pytest.mark.parametrize('source',ADAPTERS)
def test_official_discovery_and_detail_identity(source):
 adapter,page,candidate,detail=sample(source)
 assert len(page.candidates)>0
 adapter.confirm_identity(candidate,detail,candidate.detail_url_observed)
 docs=adapter.documents(detail,candidate)
 assert docs
 for doc in docs:adapter.validate_document_url(doc.url_requested,candidate)


@pytest.mark.parametrize('source',ADAPTERS)
def test_conservative_blank_and_challenge(source):
 adapter=ADAPTERS[source];url=FIXTURES[source][1]
 with pytest.raises((ValueError,SourcePageBlocked)):
  adapter.parse_listing('<main>Verify you are human</main>',url,10)
 if source=='reisesreis_open':
  with pytest.raises(ValueError):adapter.parse_listing('{}',url,10)
 else:
  page=adapter.parse_listing('<main>Sem conteúdo renderizado</main>',url,10)
  assert not page.candidates and page.empty_evidence is None and page.terminal_evidence is None


@pytest.mark.parametrize('source',ADAPTERS)
def test_wrong_candidate_detail_and_private_origin(source):
 adapter,_,candidate,detail=sample(source)
 wrong=candidate.model_copy(update={'external_id':'999999'})
 with pytest.raises(ValueError):adapter.confirm_identity(wrong,detail,candidate.detail_url_observed)
 with pytest.raises(Exception):adapter.validate_document_url('https://127.0.0.1/edital.pdf',candidate)
 with pytest.raises(Exception):adapter.validate_detail_url(candidate.detail_url_observed.replace('https://','http://'))


@pytest.mark.parametrize('source',ADAPTERS)
def test_limit_is_explicit_and_main_ambiguity(source):
 adapter=ADAPTERS[source];name,url,_,_=FIXTURES[source]
 page=adapter.parse_listing(html(name),url,1)
 if source!='reisesreis_open':assert page.truncated and len(page.candidates)==1
 else:assert len(page.candidates)==1 and page.terminal_evidence
 docs=[DocumentCandidate(doc_id='a',title='Edital de abertura',kind='edital',url_requested='https://example.test/a.pdf'),
       DocumentCandidate(doc_id='b',title='Edital de abertura',kind='edital',url_requested='https://example.test/b.pdf')]
 with pytest.raises(ValueError):adapter.choose_document(docs)
 with pytest.raises(ValueError):adapter.parse_listing(html(name),url,0)


def test_ibfc_observed_empty_and_tabs():
 adapter=ADAPTERS['ibfc_open'];page=adapter.parse_listing(html('ibfc_open'),adapter.listing_urls[0])
 assert not page.candidates and page.empty_evidence=='Nenhum item cadastrado.'
 assert 'https://concursos.ibfc.org.br/index/1/' in page.next_urls


def test_admtec_user_agent_response_not_empty():
    adapter=ADAPTERS['admtec_open']
    with pytest.raises(SourcePageBlocked):adapter.parse_listing(html('admtec_open'),adapter.listing_urls[0])
    assert 'Chrome' in adapter.request_headers(adapter.listing_urls[0])['User-Agent']
    assert adapter.request_headers('https://cdn-arquivo.concursos.srv.br/x.pdf')=={}


def test_admtec_current_wordpress_route_and_media_document():
    adapter=ADAPTERS['admtec_open']
    listing=(ROOT/'admtec_current-listing.html').read_text(encoding='utf-8')
    detail=(ROOT/'admtec_current-detail.html').read_text(encoding='utf-8')
    page=adapter.parse_listing(listing,adapter.listing_urls[0])
    assert len(page.candidates)==1
    candidate=page.candidates[0]
    assert candidate.external_id=='prefeitura-municipal-de-piranhas-al'
    assert candidate.detail_url_observed.endswith('/concurso/prefeitura-municipal-de-piranhas-al/')
    adapter.confirm_identity(candidate,detail,candidate.detail_url_observed)
    docs=adapter.documents(detail,candidate)
    assert len(docs)==1
    assert docs[0].kind=='outro'
    adapter.validate_document_url(docs[0].url_requested,candidate)


@pytest.mark.parametrize('source',('ibfc_open','admtec_open'))
def test_observed_retified_main_is_not_auto_published(source):
 adapter,_,candidate,detail=sample(source)
 docs=adapter.documents(detail,candidate)
 assert not [d for d in docs if d.kind=='edital']
 with pytest.raises(ValueError):adapter.choose_document(docs)


def test_institutomais_chooses_label_not_click_here_or_filename():
 adapter,_,candidate,detail=sample('institutomais_open')
 doc=adapter.choose_document(adapter.documents(detail,candidate))
 assert 'EDITAL DO CONCURSO PÚBLICO' in doc.title
 assert 'FUNDACI_Edital' in doc.url_requested
 assert all('Residência Médica' not in (c.title_observed or '') for c in sample('institutomais_open')[1].candidates)


def test_reis_api_pagination_and_empty_are_structural():
 adapter=ADAPTERS['reisesreis_open'];url=adapter.listing_urls[0]
 data=json.loads(html('reis_api'))
 data.update(content=[],last=True,totalPages=0,totalElements=0,numberOfElements=0,empty=True)
 assert adapter.parse_listing(json.dumps(data),url).empty_evidence
 data.update(totalPages=2,totalElements=10,last=False)
 with pytest.raises(ValueError):adapter.parse_listing(json.dumps(data),url)
 data=json.loads(html('reis_api'));data.update(totalPages=2,totalElements=10,last=False,content=[dict(data['content'][0],id=70+i) for i in range(9)],numberOfElements=9)
 page=adapter.parse_listing(json.dumps(data),url)
 assert len(page.next_urls)==1 and 'page=1' in page.next_urls[0]
 assert adapter.request_headers(url)['X-TenantID']=='reisauditores'
 assert adapter.request_headers('https://s3.amazonaws.com/a')=={}


def test_reis_rejects_missing_final_items_and_duplicate_identities():
 adapter=ADAPTERS['reisesreis_open'];url=adapter.listing_urls[0]
 data=json.loads(html('reis_api'));data.update(totalPages=1,totalElements=2,last=True)
 with pytest.raises(ValueError,match='quantidade'):adapter.parse_listing(json.dumps(data),url)
 data.update(content=data['content']*2,numberOfElements=2)
 with pytest.raises(ValueError,match='duplicada'):adapter.parse_listing(json.dumps(data),url)


def test_reis_wrong_astro_id_is_rejected():
 adapter,_,candidate,detail=sample('reisesreis_open')
 detail=detail.replace('&quot;id&quot;:[0,70]','&quot;id&quot;:[0,71]')
 with pytest.raises(ValueError):adapter.confirm_identity(candidate,detail,candidate.detail_url_observed)


@pytest.mark.parametrize('source',ADAPTERS)
def test_official_host_does_not_authorize_other_bucket_or_path(source):
 adapter,_,candidate,detail=sample(source)
 doc=adapter.documents(detail,candidate)[0]
 if source=='ibfc_open':bad=doc.url_requested.replace('/arquivos-publicos/','/private/')
 elif source=='admtec_open':bad=doc.url_requested.replace('/00121/','/00999/')
 elif source=='institutomais_open':bad=doc.url_requested.replace('/ckfinder/userfiles/files/','/private/')
 else:bad=doc.url_requested.replace('/sgs.reisauditores.com.br/','/other-tenant/')
 with pytest.raises(ValueError):adapter.validate_document_url(bad,candidate)
