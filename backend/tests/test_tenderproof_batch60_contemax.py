from pathlib import Path
import json,hashlib
import pytest
from app.tenderproof.batch60_contemax_adapter import ContemaxAdapter

F=Path(__file__).parent/'fixtures/tenderproof_batch60_contemax'
A=ContemaxAdapter()
URL=A.listing_urls[0]
DETAIL='https://www.contemaxconsultoria.com.br/site/concursos-em-andamento/prefeitura-municipal-de-cubati-pb'
def fixture(n):return (F/(n+'.html')).read_text(encoding='utf-8')
def candidate():return A.candidate_from_url(DETAIL,'PREFEITURA MUNICIPAL DE CUBATI-PB')

def test_observed_listing_partial_scope():
 p=A.parse_listing(fixture('listing'),URL)
 assert any(c.detail_url_observed==DETAIL for c in p.candidates)
 assert not any('curso-de-formacao' in c.detail_url_observed or 'planos' in (c.title_observed or '').lower() for c in p.candidates)
 assert not p.terminal_evidence

def test_document_selection_legacy_links_upgraded_without_tls_bypass():
 docs=A.documents(fixture('cubati'),candidate());d=A.choose_document(docs)
 assert d.title=='EDITAL REGULAMENTADOR'
 assert d.url_requested=='https://www.contemaxconsultoria.com.br/site/wp-content/uploads/2024/09/Edital-CUBATI.pdf'
 assert len(docs)>10 and sum(x.kind=='edital' for x in docs)==1
 assert all(x.url_requested.startswith('https://') for x in docs)

def test_wrong_title_rejected():
 with pytest.raises(ValueError):A.documents(fixture('cubati').replace('PREFEITURA MUNICIPAL DE CUBATI-PB','PREFEITURA MUNICIPAL DE OUTRA CIDADE'),candidate())

def test_wrong_detail_rejected():
 with pytest.raises(ValueError):A.confirm_identity(candidate(),fixture('cubati'),DETAIL.replace('cubati','outra'))

@pytest.mark.parametrize('url',['http://www.contemaxconsultoria.com.br/site/concursos','https://www.contemaxconsultoria.com.br/site/concursos?page=2','https://sub.www.contemaxconsultoria.com.br/site/concursos'])
def test_listing_destinations(url):
 with pytest.raises(Exception):A.validate_listing_url(url)

@pytest.mark.parametrize('url',['http://www.contemaxconsultoria.com.br/site/wp-content/uploads/2024/09/Edital-CUBATI.pdf','https://www.contemaxconsultoria.com.br/site/wp-content/uploads/2024/09/../x.pdf','https://www.contemaxconsultoria.com.br/site/wp-content/uploads/2024/09/x.pdf?foo=1','https://127.0.0.1/x.pdf'])
def test_document_guards(url):
 with pytest.raises(Exception):A.validate_document_url(url,candidate())

def test_ambiguous_original_rejected():
 docs=A.documents(fixture('cubati'),candidate());d=A.choose_document(docs)
 with pytest.raises(ValueError):A.choose_document([d,d.model_copy(update={'url_requested':d.url_requested.replace('CUBATI','SECOND'),'doc_id':'second'})])

def test_limits_challenge():
 with pytest.raises(ValueError):A.parse_listing('x'*(2*1024*1024+1),URL)
 with pytest.raises(ValueError):A.documents('x'*(2*1024*1024+1),candidate())
 with pytest.raises(ValueError):A.parse_listing('<p>Verify you are human</p>',URL)

def test_fixture_hashes():
 for r in json.loads((F/'manifest-https.json').read_text(encoding='utf-8')):
  assert r['status']==200
  assert hashlib.sha256((F/r['file']).read_bytes()).hexdigest()==r['fixture_sha256']
