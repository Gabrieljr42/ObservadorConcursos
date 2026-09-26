from pathlib import Path
import json,hashlib
import pytest
from app.tenderproof.batch99_southeast_adapters import *
F=Path(__file__).parent/'fixtures/tenderproof_batch99_southeast'
def h(name):return (F/(name+'.html')).read_text(encoding='utf-8')
A=FapespPersonnelAdapter();B=FaperjPersonnelAdapter()
URL='https://faperj.br/?id=812.7.4'
TITLE='FAPERJ anuncia edital de chamamento público para o cargo de Diretor de Tecnologia'
def fapesp_candidate():return A.parse_listing(h('fapesp-processo'),A.listing_urls[0]).candidates[0]
def faperj_candidate():return B.candidate_from_url(URL,TITLE)

def test_fapesp_current_notice_and_base_href():
 c=fapesp_candidate();ds=A.documents(h('fapesp-processo'),c);d=A.choose_document(ds)
 assert c.external_id=='4470' and d.url_requested.endswith('/4470/concurso0126.pdf')
 assert sum(d.kind=='edital' for d in ds)==1
 assert any(d.url_requested=='https://fapesp.br/files/upload/4470/resultado-heteroidentificacao.pdf' for d in ds)
 assert not A.parse_listing(h('fapesp-processo'),A.listing_urls[0]).terminal_evidence

def test_fapesp_bolsas_not_candidates():
 assert not A.parse_listing(h('fapesp_selection'),A.listing_urls[0]).candidates

def test_fapesp_ambiguous_notice_requires_review():
 html=h('fapesp-processo').replace('concurso0126.pdf','concurso0126.pdf')
 s=visible_soup(html);s.select_one('.page-body').append(visible_soup('<a href="https://fapesp.br/files/upload/4470/outro.pdf">Concurso Público no 02/2026</a>').select_one('a'))
 with pytest.raises(ValueError):A.parse_listing(str(s),A.listing_urls[0])

def test_fapesp_base_crosshost_rejected():
 with pytest.raises(ValueError):A.documents(h('fapesp-processo').replace('<base href="https://fapesp.br/"','<base href="https://example.org/"'),fapesp_candidate())

def test_faperj_official_detail_original_and_literal_position():
 c=faperj_candidate();assert c.title_observed=='Diretor de Tecnologia'
 d=B.choose_document(B.documents(h('faperj-diretor'),c));assert d.kind=='edital' and '20_2025' in d.url_requested

def test_faperj_current_archive_partial_not_empty_confirmation():
 p=B.parse_listing(h('faperj-archive-final'),B.listing_urls[0]);assert not p.candidates and not p.empty_evidence and not p.terminal_evidence
 assert 'https://faperj.br/arquivo_noticias.phtml?pg=2' in p.next_urls

def test_faperj_personnel_filter_rejects_funding():
 for title in ('Auxílio ao Pesquisador Recém-Contratado','Programa de Bolsa de Treinamento e Capacitação Técnica','Edital de Eliminação de Documentos','Resultado preliminar do Programa de Apoio às Academias','EDITAL DE SELEÇÃO PÚBLICA Subvenção Econômica à Pesquisa','Intercâmbio de Pessoal MSCA SE'):
  assert not B.in_scope(title,URL)
 assert B.in_scope(TITLE,URL)

def test_faperj_wrong_identity_title_rejected():
 with pytest.raises(ValueError):B.confirm_identity(faperj_candidate(),h('faperj-diretor'),URL.replace('812','813'))
 with pytest.raises(ValueError):B.documents(h('faperj-diretor').replace('Diretor de Tecnologia','Diretor Administrativo'),faperj_candidate())

@pytest.mark.parametrize('url',['http://faperj.br/?id=812.7.4','https://faperj.br/?id=812.7.4&x=1','https://faperj.br/?id=812.7.4&id=813.7.4','https://faperj.br/?id=415.6.5','https://127.0.0.1/?id=812.7.4'])
def test_faperj_destinations(url):
 with pytest.raises(Exception):B.validate_detail_url(url)

@pytest.mark.parametrize('url',['https://fapesp.br/files/upload/9999/concurso0126.pdf','http://fapesp.br/files/upload/4470/concurso0126.pdf','https://fapesp.br/files/upload/4470/../x.pdf','https://fapesp.br/files/upload/4470/concurso0126.pdf?q=1'])
def test_fapesp_document_guards(url):
 with pytest.raises(Exception):A.validate_document_url(url,fapesp_candidate())

def test_limits_and_challenges():
 for a in (A,B):
  with pytest.raises(ValueError):a.parse_listing('x'*(2*1024*1024+1),a.listing_urls[0])
  with pytest.raises(ValueError):a.parse_listing('<p>Verify you are human</p>',a.listing_urls[0])

def test_fapes_declaration_is_not_edital_for_people():
 s=visible_soup(h('fapes-concursos'));text=folded(s.get_text(' ',strip=True))
 assert 'declaracao de nao realizacao de concurso publico de 2023 ate 2026' in text
 assert not B.in_scope('Declaração de não realização de concurso público de 2023 até 2026','')

def test_captured_hashes():
 for p in F.glob('manifest-*.json'):
  for r in json.loads(p.read_text(encoding='utf-8')):
   if r.get('file'):assert hashlib.sha256((F/r['file']).read_bytes()).hexdigest()==r['fixture_sha256']


@pytest.mark.parametrize('old,new', [('01/2026','02/2027'),('01/2026','02/2026'),('01/2026','01/2027'),('concurso0126.pdf','concurso0227.pdf')])
def test_fapesp_reused_page_cannot_transform_contest(old,new):
 html=h('fapesp-processo').replace(old,new)
 with pytest.raises(ValueError):A.parse_listing(html,A.listing_urls[0])
 with pytest.raises(ValueError):A.documents(html,fapesp_candidate())

def test_fapesp_candidate_edition_checked_explicitly():
 c=fapesp_candidate().model_copy(update={'title_observed':'FAPESP Concurso Público 02/2027'})
 with pytest.raises(ValueError):A.documents(h('fapesp-processo'),c)


C=FapesbPersonnelAdapter()
def reda_candidate():return C.parse_listing(h('fapesb-reda'),C.listing_urls[0]).candidates[0]
def test_fapesb_personnel_tab_only_and_original():
 c=reda_candidate();ds=C.documents(h('fapesb-reda'),c)
 assert c.external_id=='01-2026' and c.detail_url_observed.endswith('#reda-tab-2026')
 assert C.choose_document(ds).url_requested==C.original
 assert len(ds)>20 and sum(d.kind=='edital' for d in ds)==1
 assert not any('2023' in d.title for d in ds)

@pytest.mark.parametrize('old,new',[('01/2026','02/2026'),('01/2026','01/2027'),('EDITAL_DEFINITIVO_REDA_2026.pdf','other.pdf'),('id="reda-tab-2026"','id="reda-tab-2027"')])
def test_fapesb_edition_and_original_identity(old,new):
 with pytest.raises(ValueError):C.documents(h('fapesb-reda').replace(old,new),reda_candidate())

def test_fapesb_foreign_year_candidate_rejected():
 with pytest.raises(ValueError):C.candidate_from_url(C.listing_urls[0]+'#reda-tab-2023')
 with pytest.raises(ValueError):C.validate_document_url('https://www.fapesb.ba.gov.br/wp-content/uploads/2026/08/other.pdf',reda_candidate())

def test_fapesb_duplicate_tab_rejected():
 s=visible_soup(h('fapesb-reda'));section=s.select_one('#reda-tab-2026')
 section.parent.append(visible_soup(str(section)).select_one('#reda-tab-2026'))
 with pytest.raises(ValueError):C.documents(str(s),reda_candidate())

def test_fapesq_personnel_sounding_scholarships_not_promoted():
 assert not B.in_scope('EDITAL Nº58/2026 PROCESSO SELETIVO PARA CONTRATAÇÃO DE COORDENADORES AUDIOVISUAIS E EQUIPE TÉCNICA','')
 assert not B.in_scope('EDITAL Nº57/2026 SELEÇÃO DE OFICINEIROS/AVALIADORES PARA FESTIVAL DE ARTE','')
