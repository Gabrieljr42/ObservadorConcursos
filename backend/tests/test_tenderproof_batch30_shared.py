"""Official batch30 HTML and clearly controlled adverse perturbations."""
import hashlib,json
from pathlib import Path
import pytest
from bs4 import UnicodeDammit
from app.tenderproof.source_adapters import get_source_adapter,SourcePageBlocked
from app.tenderproof.batch30_shared_adapters import BATCH30_SHARED_ADAPTERS
ROOT=Path(__file__).parent/'fixtures'/'tenderproof_batch30_shared'
MANIFEST=json.loads((ROOT/'manifest.json').read_text(encoding='utf-8'))
IDS=[a.source for a in BATCH30_SHARED_ADAPTERS]

def capture(source,kind):
 r=next(x for x in MANIFEST['pages'] if x['source']==source and x['kind']==kind);b=(ROOT/r['file']).read_bytes();assert hashlib.sha256(b).hexdigest()==r['sha256']
 return r,UnicodeDammit(b,is_html=True).unicode_markup

def sample(source):
 a=get_source_adapter(source);r,html=capture(source,'own-listing' if source=='consulpam_open' else 'listing');p=a.parse_listing(html,r['url'],1000)
 d,detail=capture(source,'own-detail' if source=='consulpam_open' else 'detail-alt1' if source=='idcap_open' else 'detail')
 c=next(c for c in p.candidates if c.detail_url_observed==d['url'])
 return a,r,html,p,c,d,detail

@pytest.mark.parametrize('source',IDS)
def test_official_discovery_and_document_identity(source):
 a,r,html,p,c,d,detail=sample(source)
 assert p.candidates and len({x.external_id for x in p.candidates})==len(p.candidates)
 assert not p.terminal_evidence and not p.empty_evidence
 a.confirm_identity(c,detail,d['url']);docs=a.documents(detail,c)
 assert docs
 assert all('privacidade' not in x.title.casefold() for x in docs)
 for doc in docs:a.validate_document_url(doc.url_requested,c)

@pytest.mark.parametrize('source',IDS)
def test_conservative_empty_and_visible_challenge(source):
 a=get_source_adapter(source)
 p=a.parse_listing('<main><p>Nenhum item encontrado.</p></main>',a.listing_urls[0])
 assert not p.candidates and not p.empty_evidence and not p.terminal_evidence
 with pytest.raises(SourcePageBlocked):a.parse_listing('<h1>Just a moment</h1>',a.listing_urls[0])

@pytest.mark.parametrize('source',IDS)
def test_source_id_title_and_destination_guards(source):
 a,r,html,p,c,d,detail=sample(source)
 with pytest.raises(ValueError):a.confirm_identity(c.model_copy(update={'external_id':'99999999'}),detail,d['url'])
 with pytest.raises(ValueError):a.confirm_identity(c.model_copy(update={'title_observed':'Municipio Incompatibilissimo'}),detail,d['url'])
 for url in ('https://127.0.0.1/a.pdf','https://evil.test/a.pdf'):
  with pytest.raises(Exception):a.validate_document_url(url,c)

@pytest.mark.parametrize('source',IDS)
def test_controlled_limit_document_ambiguity_and_adverse_labels(source):
 a,r,html,p,c,d,detail=sample(source)
 limited=a.parse_listing(html,r['url'],1)
 assert not limited.terminal_evidence
 if len(p.candidates)>1:assert limited.truncated
 doc=a.documents(detail,c)[0].model_copy(update={'title':'Edital de abertura','kind':'edital'})
 with pytest.raises(ValueError,match='ambíguos'):a.choose_document([doc,doc.model_copy(update={'url_requested':doc.url_requested+'?other=1'})])
 # Actual document URL paired with controlled malicious labels must not promote.
 from html import escape
 for title in ('EDITAL DAS INSCRIÇÕES DEFERIDAS/INDEFERIDAS','EDITAL DA AVALIAÇÃO DE TÍTULOS','Edital de classificação provisória'):
  changed=a.documents(f'<a href="{escape(doc.url_requested,quote=True)}">{title}</a>',c)
  assert all(x.kind!='edital' for x in changed)

@pytest.mark.parametrize('source',[s for s in IDS if s!='consulpam_open'])
def test_shared_cdn_requires_tenant_and_contest_id(source):
 a,r,html,p,c,d,detail=sample(source);url=a.documents(detail,c)[0].url_requested
 for wrong in (url.replace('/uploads/'+a.tenant+'/', '/uploads/999999/'),url.replace('/concursos/'+c.external_id+'/', '/concursos/999999/')):
  with pytest.raises(ValueError):a.validate_document_url(wrong,c)


def test_w2_observed_complex_pagination_preserved():
 a=get_source_adapter('w2_open');r,html=capture(a.source,'listing');p=a.parse_listing(html,r['url']);r2,h2=capture(a.source,'page2')
 assert r2['url'] in p.next_urls
 assert a.parse_listing(h2,r2['url']).candidates
 for bad in (r2['url'].replace('pp=10','pp=100000'),r2['url']+'&pg=3',r2['url'].replace('q=','q=private')):
  with pytest.raises(ValueError):a.validate_listing_url(bad)


def test_consulpam_aliases_are_not_silently_merged():
 a=get_source_adapter('consulpam_open')
 with pytest.raises(Exception):a.candidate_from_url('https://consulpam.selecao.net.br/informacoes/41/')
 own=a.candidate_from_url('https://www.consulpam.com.br/index.php?menu=concursos&acao=ver&id=41')
 assert own.external_id=='41'
 r,html=capture(a.source,'listing');assert 'Nenhum item cadastrado' in html
 assert a.listing_urls[0]!='https://consulpam.selecao.net.br/index/abertos/'


def test_idcap_encoding_repair_and_announced_contest_without_documents():
 a,r,html,p,c,d,detail=sample('idcap_open');assert 'Itajaí' in c.title_observed
 r0,h0=capture(a.source,'detail');announced=next(x for x in p.candidates if x.detail_url_observed==r0['url'])
 with pytest.raises(ValueError,match='documento'):a.confirm_identity(announced,h0,r0['url'])
