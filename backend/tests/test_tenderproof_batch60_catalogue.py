"""Official portal fixtures; controlled negative mutations are synthetic."""
from pathlib import Path
import pytest
from bs4 import BeautifulSoup
from app.tenderproof.batch60_catalogue_adapters import BATCH60_CATALOGUE_ADAPTERS
from app.tenderproof.security import DestinationBlocked

ROOT=Path(__file__).parent/'fixtures/tenderproof_batch60_own'


@pytest.fixture(params=BATCH60_CATALOGUE_ADAPTERS,ids=lambda a:a.source)
def sample(request):
    a=request.param
    prefix='zambini_open' if a.source=='zambini_open' else 'consulplan_open'
    url='https://www.zambini.org.br/portal/concursos/encerrados' if prefix=='zambini_open' else a.listing_urls[0]
    listing=(ROOT/(prefix+'-detail0.html')).read_text(encoding='utf-8')
    detail=(ROOT/(prefix+'-sample-detail.html')).read_text(encoding='utf-8')
    page=a.parse_listing(listing,url)
    c=next(c for c in page.candidates if c.external_id==('1966' if prefix=='zambini_open' else 'unai2026'))
    return a,url,listing,detail,c


def test_observed_discovery_principal_identity(sample):
    a,url,listing,detail,c=sample
    a.confirm_identity(c,detail,c.detail_url_observed)
    chosen=a.choose_document(a.documents(detail,c))
    assert chosen.kind=='edital'
    assert a.choose_document(a.documents(detail,c)).doc_id==chosen.doc_id
    a.validate_document_url(chosen.url_requested,c)
    page=a.parse_listing(listing,url,limit=1)
    assert page.truncated and not page.terminal_evidence


def test_wrong_header_even_with_original_document_and_notice_titles(sample):
    a,_,_,detail,c=sample
    soup=BeautifulSoup(detail,'lxml')
    for h in soup.select(a.identity_selector):
        h.string='Prefeitura Municipal de Município Incompatível ZZ'
    assert a.choose_document(a.documents(str(soup),c)).kind=='edital'
    with pytest.raises(ValueError):
        a.confirm_identity(c,str(soup),c.detail_url_observed)


def test_ambiguous_document_foreign_host_and_unconfirmed_empty(sample):
    a,url,_,detail,c=sample
    chosen=a.choose_document(a.documents(detail,c))
    other=chosen.model_copy(update={'doc_id':'synthetic-other','url_requested':chosen.url_requested.replace('.pdf','-other.pdf')})
    with pytest.raises(ValueError):a.choose_document([chosen,other])
    with pytest.raises((ValueError,DestinationBlocked)):a.validate_document_url('https://example.org/other.pdf',c)
    page=a.parse_listing('<main>Site em manutenção</main>',url)
    assert not page.empty_evidence and not page.terminal_evidence
    with pytest.raises(ValueError):a.parse_listing('<main>Just a moment</main>',url)


def test_consulplan_aliases_keep_separate_source_identity():
    first,second=BATCH60_CATALOGUE_ADAPTERS[:2]
    url='https://institutoconsulplan.org.br/unai2026'
    a,b=first.candidate_from_url(url,'Câmara Municipal de Unaí/MG'),second.candidate_from_url(url,'Câmara Municipal de Unaí/MG')
    assert a.external_id==b.external_id=='unai2026' and a.candidate_id!=b.candidate_id
    detail=(ROOT/'consulplan_open-sample-detail.html').read_text(encoding='utf-8')
    with pytest.raises(ValueError):first.confirm_identity(b,detail,url)
    assert first.in_scope('Concurso Público para Médico de Medicina do Trabalho','')
    assert first.in_scope('Concurso para Ingresso na Carreira de Auditor','')
    assert not first.in_scope('Vestibular de Medicina 1.2027','')
    assert not first.in_scope('UFV PASES - Triênio 2026-2028','')


def test_consulplan_canonical_and_single_foreign_directory_refused():
    a=BATCH60_CATALOGUE_ADAPTERS[0]
    url='https://institutoconsulplan.org.br/unai2026'
    c=a.candidate_from_url(url,'Câmara Municipal de Unaí/MG')
    detail=(ROOT/'consulplan_open-sample-detail.html').read_text(encoding='utf-8')
    with pytest.raises(ValueError):a.confirm_identity(c,detail.replace('href="'+url+'"','href="https://institutoconsulplan.org.br/outro2026"'),url)
    with pytest.raises(ValueError):a.confirm_identity(c,detail.replace('/concursos/1333/','/concursos/9999/'),url)
    with pytest.raises(ValueError):a.confirm_identity(c,detail.replace('logo_1333_','logo_9999_'),url)


def test_zambini_real_default_empty_has_explicit_evidence():
    a=BATCH60_CATALOGUE_ADAPTERS[-1]
    page=a.parse_listing((ROOT/'zambini_open-listing0.html').read_text(encoding='utf-8'),a.listing_urls[0])
    assert not page.candidates and page.empty_evidence=='No momento não temos nenhum concurso em andamento.'
    assert page.terminal_evidence
