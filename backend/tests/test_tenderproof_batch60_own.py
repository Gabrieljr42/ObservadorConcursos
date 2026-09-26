"""Official captures plus explicitly controlled identity/document mutations."""
from pathlib import Path
from bs4 import UnicodeDammit
import pytest
from app.tenderproof.batch60_own_adapters import BATCH60_OWN
from app.tenderproof.source_adapter_base import SourcePageBlocked
from app.tenderproof.security import DestinationBlocked

ROOT=Path(__file__).parent/'fixtures/tenderproof_batch60_own'
def html(source,kind):return UnicodeDammit((ROOT/f'{source}-{kind}.html').read_bytes(),is_html=True).unicode_markup

@pytest.fixture(params=list(BATCH60_OWN))
def sample(request):
    a=BATCH60_OWN[request.param]
    listing=html(a.source,'listing0');detail=html(a.source,'detail0')
    candidate=a.parse_listing(listing,a.listing_urls[0]).candidates[0]
    return a,listing,detail,candidate

def test_official_identity_principal_and_scope(sample):
    a,listing,detail,c=sample
    a.confirm_identity(c,detail,c.detail_url_observed)
    docs=a.documents(detail,c);chosen=a.choose_document(docs)
    assert chosen.kind=='edital'
    assert not a.in_scope('Vestibular e bolsa de pesquisa',c.detail_url_observed)
    assert a.parse_listing(listing,a.listing_urls[0],limit=1).truncated

def test_mismatch_cannot_reuse_detail(sample):
    a,listing,detail,c=sample
    other=a.parse_listing(listing,a.listing_urls[0]).candidates[1]
    with pytest.raises(ValueError):a.confirm_identity(other,detail,other.detail_url_observed)
    with pytest.raises(ValueError):a.confirm_identity(c,detail,other.detail_url_observed)

def test_empty_and_challenge_conservative(sample):
    a,*_=sample
    page=a.parse_listing('<main><p>Sem conteúdo</p></main>',a.listing_urls[0])
    assert not page.empty_evidence and not page.terminal_evidence
    with pytest.raises(SourcePageBlocked):a.parse_listing('<h1>Just a moment...</h1>',a.listing_urls[0])

def test_wrong_document_and_ambiguous_original(sample):
    a,_,detail,c=sample
    docs=a.documents(detail,c);chosen=a.choose_document(docs)
    with pytest.raises(DestinationBlocked):a.validate_document_url('https://example.test/edital.pdf',c)
    with pytest.raises(ValueError):a.validate_document_url(a.listing_urls[0].rstrip('/')+'/politica.pdf',c)
    with pytest.raises(ValueError):a.choose_document([d for d in docs if d.kind!='edital'])
    with pytest.raises(ValueError):a.choose_document([chosen,chosen.model_copy(update={'doc_id':'controlled-second-original','url_requested':chosen.url_requested+'?second=1'})])

def test_repeat_is_stable_and_foreign_source_refused(sample):
    a,listing,detail,c=sample
    assert [x.external_id for x in a.parse_listing(listing,a.listing_urls[0]).candidates]==[x.external_id for x in a.parse_listing(listing,a.listing_urls[0]).candidates]
    assert [d.doc_id for d in a.documents(detail,c)]==[d.doc_id for d in a.documents(detail,c)]
    with pytest.raises(ValueError):a.documents(detail,c.model_copy(update={'source':'controlled_other_source'}))

def test_ms_requires_observed_base_and_document_labels():
    a=BATCH60_OWN['msconcursos_open'];listing=html(a.source,'listing0');detail=html(a.source,'detail0')
    c=a.parse_listing(listing,a.listing_urls[0]).candidates[0]
    with pytest.raises(ValueError):a.documents(detail.replace('<base href="https://msconcursos.com.br/"','<base href="https://example.test/"'),c)
    assert a.choose_document(a.documents(detail,c)).title.startswith('EDITAL DE ABERTURA')

def test_funvapi_canonical_and_outside_original_guard():
    a=BATCH60_OWN['funvapi_open'];c=a.parse_listing(html(a.source,'listing0'),a.listing_urls[0]).candidates[0]
    detail=html(a.source,'detail0')
    with pytest.raises(ValueError):a.confirm_identity(c,detail.replace('rel="canonical"','rel="controlled-removed"'),c.detail_url_observed)

def test_consep_only_exact_observed_original_label_promoted():
    a=BATCH60_OWN['consep_open'];c=a.parse_listing(html(a.source,'listing0'),a.listing_urls[0]).candidates[0]
    detail=html(a.source,'detail0')
    assert sum(d.kind=='edital' for d in a.documents(detail,c))==1
    altered=detail.replace('BAIXA GRANDE DO RIBEIRO - EDITAL - TESTE SELETIVO 2026','BAIXA GRANDE DO RIBEIRO - EDITAL DE RETIFICAÇÃO - TESTE SELETIVO 2026')
    with pytest.raises(ValueError):a.choose_document(a.documents(altered,c))
