"""Official captures; explicitly controlled mutations exercise failure paths."""
from pathlib import Path
import pytest
from app.tenderproof.batch60_shared_adapters import BATCH60_SHARED_ADAPTERS
from app.tenderproof.security import DestinationBlocked

ROOT = Path(__file__).parent / 'fixtures/tenderproof_batch60_shared'


@pytest.fixture(params=BATCH60_SHARED_ADAPTERS, ids=lambda a:a.source)
def sample(request):
    a = request.param
    name = a.source.split('_')[0]
    listing = (ROOT / (name+'-listing.html')).read_text(encoding='utf-8')
    detail = (ROOT / (name+'-detail.html')).read_text(encoding='utf-8')
    page = a.parse_listing(listing,a.listing_urls[0])
    c = next(c for c in page.candidates if c.external_id=={'fundep':'72','facet':'44','educapb':'7'}[name])
    return a,listing,detail,c


def test_real_capture_identity_and_principal(sample):
    a,listing,detail,c = sample
    a.confirm_identity(c,detail,c.detail_url_observed)
    docs = a.documents(detail,c)
    selected = a.choose_document(docs)
    assert selected.kind == 'edital'
    a.validate_document_url(selected.url_requested,c)
    assert selected.doc_id == a.choose_document(a.documents(detail,c)).doc_id
    assert len(a.parse_listing(listing,a.listing_urls[0]).candidates) == {'fundep_open':3,'facet_open':7,'educapb_open':5}[a.source]


def test_limits_unknown_empty_and_challenge(sample):
    a,listing,_,_ = sample
    page = a.parse_listing(listing,a.listing_urls[0],limit=1)
    assert page.truncated and not page.terminal_evidence
    empty = a.parse_listing('<main>Site em manutenção</main>',a.listing_urls[0])
    assert not empty.empty_evidence and not empty.terminal_evidence
    with pytest.raises(ValueError):
        a.parse_listing('<main>Just a moment</main>',a.listing_urls[0])


def test_mismatched_identity_and_foreign_tenant(sample):
    a,_,detail,c = sample
    wrong = c.model_copy(update={'title_observed':'Prefeitura Municipal de Município Inexistente ZZ'})
    with pytest.raises(ValueError):
        a.confirm_identity(wrong,detail,c.detail_url_observed)
    with pytest.raises(ValueError):
        a.confirm_identity(c,detail,c.detail_url_observed.replace('/'+c.external_id+'/', '/999999/'))
    selected = a.choose_document(a.documents(detail,c))
    with pytest.raises(ValueError):
        a.validate_document_url(selected.url_requested.replace('/uploads/'+a.tenant+'/', '/uploads/999999/'),c)
    with pytest.raises((ValueError,DestinationBlocked)):
        a.validate_document_url(selected.url_requested.replace('anexos-r2.selecao.net.br','example.org'),c)


def test_ambiguity_and_wrong_document_require_review(sample):
    a,_,detail,c = sample
    selected = a.choose_document(a.documents(detail,c))
    other = selected.model_copy(update={'doc_id':'synthetic-other','url_requested':selected.url_requested.replace('.pdf','-other.pdf')})
    with pytest.raises(ValueError):
        a.choose_document([selected,other])
    with pytest.raises(ValueError):
        a.choose_document([selected.model_copy(update={'kind':'resultado'})])


def test_fundep_personnel_scope():
    assert not BATCH60_SHARED_ADAPTERS[0].in_scope('Título para Especialistas em Pneumologia e Tisiologia - 2026','')


def test_facet_document_title_does_not_rescue_wrong_header():
    from bs4 import BeautifulSoup
    a=BATCH60_SHARED_ADAPTERS[1]
    listing=(ROOT/'facet-listing.html').read_text(encoding='utf-8')
    c=next(c for c in a.parse_listing(listing,a.listing_urls[0]).candidates if c.external_id=='44')
    soup=BeautifulSoup((ROOT/'facet-detail.html').read_text(encoding='utf-8'),'lxml')
    header=soup.select_one('.dados')
    header.clear()
    wrong=soup.new_tag('h2');wrong.string='Prefeitura Municipal de Município Incompatível ZZ';header.append(wrong)
    assert a.choose_document(a.documents(str(soup),c)).kind=='edital'
    with pytest.raises(ValueError):
        a.confirm_identity(c,str(soup),c.detail_url_observed)


def test_reversible_observed_encoding_and_preserved_unicode():
    from app.tenderproof.batch60_shared_adapters import observed_text
    title='Processo Seletivo - PREFEITURA MUNICIPAL DE SUMÉ-PB'
    assert observed_text(title.encode('utf-8').decode('latin1'))==title
    assert observed_text(title)==title
    assert observed_text('Concurso Público - FUMEP de Sete Lagoas/MG'.encode('utf-8').decode('latin1'))=='Concurso Público - FUMEP de Sete Lagoas/MG'
