import json
from pathlib import Path
import pytest
from app.tenderproof.batch99_regions_adapters import FapescSelectionAdapter
from app.tenderproof.contracts import DocumentCandidate
from app.tenderproof.security import DestinationBlocked

FIX = Path(__file__).parent/'fixtures/tenderproof_batch99_regions'

def capture(manifest, source='fapesc_selection'):
    row = next(r for r in json.loads((FIX/manifest).read_text(encoding='utf-8'))['pages'] if r['source']==source)
    return row['url'], (FIX/row['file']).read_text(encoding=row['encoding'])

def test_fapesc_observed_contract():
    a = FapescSelectionAdapter()
    url, html = capture('alternate-manifest.json')
    listing = a.parse_listing(html, url, 1)
    assert len(listing.candidates)==1 and not listing.truncated
    assert listing.terminal_evidence is None
    candidate = listing.candidates[0]
    detail, body = capture('contest-manifest.json')
    a.confirm_identity(candidate, body, detail)
    docs = a.documents(body, candidate)
    assert len(docs)==3
    assert sum(d.kind=='edital' for d in docs)==1
    assert a.choose_document(docs).title=='Edital 001/2022'

@pytest.mark.parametrize('url', ['https://fapesc.fepese.org.br/?go=edital&mn=1151b3eab3b069d5112ccae1943307c4&edital=2', 'https://fapesc.fepese.org.br/?go=edital&mn=1151b3eab3b069d5112ccae1943307c4&edital=1&edital=2','https://evil.test/?go=edital&mn=1151b3eab3b069d5112ccae1943307c4&edital=1'])
def test_wrong_detail(url):
    with pytest.raises((ValueError, DestinationBlocked)): FapescSelectionAdapter().candidate_from_url(url)

def test_wrong_document_and_title():
    a=FapescSelectionAdapter()
    url,body=capture('contest-manifest.json')
    c=a.candidate_from_url(url, '2022 - FAPESC')
    with pytest.raises(ValueError): a.validate_document_url('https://fapesc.fepese.org.br/?go=download&arquivo=other.pdf&inline=1',c)
    with pytest.raises(ValueError): a.confirm_identity(c,body.replace('2022 - FAPESC','2023 - FAPESC'),url)
    with pytest.raises(ValueError): a.confirm_identity(c,body.replace('Edital 001/2022','Edital 002/2022'),url)

def test_no_fake_empty_or_scope():
    a=FapescSelectionAdapter()
    p=a.parse_listing('<html><body>Bolsas de pesquisa</body></html>',a.listing_urls[0])
    assert not p.candidates and not p.empty_evidence and not p.terminal_evidence
    with pytest.raises(ValueError): a.parse_listing('x'*(2*1024*1024+1),a.listing_urls[0])
    with pytest.raises(ValueError): a.parse_listing('',a.listing_urls[0],0)

def test_ambiguous_and_amendment_only():
    a=FapescSelectionAdapter()
    u,b=capture('contest-manifest.json')
    docs=a.documents(b,a.candidate_from_url(u))
    with pytest.raises(ValueError): a.choose_document([d for d in docs if d.kind!='edital'])
    original=a.choose_document(docs)
    with pytest.raises(ValueError): a.choose_document(docs+[DocumentCandidate(doc_id='other',title=original.title,url_requested='https://fapesc.fepese.org.br/other.pdf',kind='edital')])


def test_fapespa_reviewed_archive_explicit():
    from app.tenderproof.batch99_regions_adapters import FapespaSelectionArchiveAdapter
    a=FapespaSelectionArchiveAdapter()
    url,html=capture('selection-manifest.json','fapespa_selection')
    page=a.parse_listing(html,url,1)
    assert len(page.candidates)==1 and not page.empty_evidence
    assert any('arquivo revisado' in d for d in page.diagnostics)
    c=page.candidates[0]
    a.confirm_identity(c,html,url)
    docs=a.documents(html,c)
    assert len(docs)==6
    assert a.choose_document(docs).url_requested==a.reviewed_original_url
    assert a.reviewed_original_url not in html
    with pytest.raises(ValueError):a.confirm_identity(c,html.replace('001/2025 PSS/FAPESPA','002/2025 PSS/FAPESPA'),url)
    with pytest.raises(ValueError):a.validate_document_url('https://www.fapespa.pa.gov.br/wp-content/uploads/2025/07/other.pdf',c)
    assert not a.parse_listing('<p>Bolsas de pesquisa</p>',url).empty_evidence


def test_fapeg_original_and_retifications_preserve_post_identity():
    from app.tenderproof.batch99_regions_adapters import FapegSelectionAdapter
    from app.tenderproof.document_identity import document_identity,document_manifest
    a=FapegSelectionAdapter()
    url,html=capture('categories-manifest.json','fapeg_selection')
    page=a.parse_listing(html,url,1)
    assert len(page.candidates)==1
    c=page.candidates[0]
    _,body=capture('selection-manifest.json','fapeg_selection')
    a.confirm_identity(c,body,c.detail_url_observed)
    docs=a.documents(body,c)
    assert len(docs)==25
    original=a.choose_document(docs)
    assert original.acquisition_request.body=='177,0'
    identities={document_identity(document_manifest(d)) for d in docs}
    assert len(identities)==25
    assert {'177,0','181,0','195,0','59,59','59,58','186836,0'} <= {d.acquisition_request.body for d in docs}
    bad=original.model_copy(deep=True)
    bad.acquisition_request.body='181,0'
    with pytest.raises(ValueError):a.validate_document_request(bad,c)
    with pytest.raises(ValueError):a.choose_document([d for d in docs if d is not original])
