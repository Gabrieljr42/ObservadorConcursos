from pathlib import Path
import pytest
from app.tenderproof.batch99_verbena_adapter import VerbenaAdapter

FIX=Path(__file__).parent/'fixtures/tenderproof_batch99_own'
def fixture(name):return (FIX/('verbena_selection-'+name+'.html')).read_text(encoding='utf-8')

def test_observed_personnel_banner_and_original_exclude_vestibular():
    a=VerbenaAdapter();p=a.parse_listing(fixture('listing0'),a.listing_urls[0])
    assert len(p.candidates)==1 and p.truncated and not p.terminal_evidence
    c=p.candidates[0];detail=fixture('detail0')
    a.confirm_identity(c,detail,c.detail_url_observed)
    doc=a.choose_document(a.documents(detail,c))
    assert 'Edital_de_Abertura' in doc.url_requested and '01-2026' in doc.url_requested
    with pytest.raises(ValueError):a.validate_detail_url('https://sistemas.institutoverbena.ufg.br/2026/vestibular-ufg/')

def test_wrong_title_year_or_document_is_rejected():
    a=VerbenaAdapter();c=a.parse_listing(fixture('listing0'),a.listing_urls[0]).candidates[0]
    with pytest.raises(ValueError):a.confirm_identity(c,fixture('detail0').replace('Pires do Rio','Outro Município'),c.detail_url_observed)
    with pytest.raises(ValueError):a.confirm_identity(c,fixture('detail0').replace('01/2026','99/2099'),c.detail_url_observed)
    with pytest.raises(ValueError):a.validate_document_url('https://sistemas.institutoverbena.ufg.br/2026/vestibular-ufg/sistema/arquivos/editais/edital.pdf',c)

def test_absent_banner_is_not_legitimate_empty_and_retification_not_original():
    a=VerbenaAdapter();p=a.parse_listing('<html>Carregando</html>',a.listing_urls[0])
    assert not p.candidates and not p.empty_evidence and not p.terminal_evidence
    c=a.parse_listing(fixture('listing0'),a.listing_urls[0]).candidates[0]
    docs=a.documents(fixture('detail0').replace('Edital de Abertura','Edital Retificado'),c)
    with pytest.raises(ValueError):a.choose_document(docs)
