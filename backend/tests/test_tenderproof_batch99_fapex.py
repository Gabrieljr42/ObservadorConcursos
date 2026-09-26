from pathlib import Path
import pytest
from app.tenderproof.batch99_foundation_adapters import FAPEXAdapter

FIX=Path(__file__).parent/'fixtures/tenderproof_batch99_foundations'
def fixture(n):return (FIX/f'fapex_selection-public-{n}.html').read_text(encoding='utf-8')

def test_public_alternative_excludes_academic_professional_degree():
    a=FAPEXAdapter();page=a.parse_listing(fixture(0),a.listing_urls[0])
    assert page.candidates[0].external_id=='nr2O'
    assert 'nr6L' not in {c.external_id for c in page.candidates}
    c=page.candidates[0];a.confirm_identity(c,fixture(2),c.detail_url_observed)
    docs=a.documents(fixture(2),c)
    assert a.choose_document(docs).title=='ABERTURA E INSCRIÇÕES'
    assert a.parse_listing(fixture(0),a.listing_urls[0],limit=1).truncated

def test_other_detail_private_portal_and_missing_original():
    a=FAPEXAdapter();c=a.parse_listing(fixture(0),a.listing_urls[0]).candidates[0]
    with pytest.raises(ValueError):a.confirm_identity(c,fixture(2),c.detail_url_observed.replace('nr2O','nr2M'))
    with pytest.raises(ValueError):a.validate_detail_url('https://fapex.org.br/portalrh/login')
    with pytest.raises(ValueError):a.choose_document(a.documents(fixture(2).replace('ABERTURA E INSCRIÇÕES','Retificação'),c))
    with pytest.raises(ValueError):a.validate_document_url('https://fapex.org.br/privacy.pdf',c)
    p=a.parse_listing('<html>Carregando</html>',a.listing_urls[0])
    assert not p.candidates and not p.empty_evidence


