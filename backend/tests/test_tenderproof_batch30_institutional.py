"""Real dated sanitized HTML; mutations below are explicitly synthetic."""
import hashlib
import json
from pathlib import Path
import pytest
from app.tenderproof.batch30_institutional_adapters import PubliconsultAdapter
from app.tenderproof.security import DestinationBlocked

ROOT = Path(__file__).parent/'fixtures/tenderproof_batch30_institutional'


def sample():
    adapter = PubliconsultAdapter()
    listing = (ROOT/'publiconsult-listing.html').read_text(encoding='utf-8')
    detail = (ROOT/'publiconsult-detail.html').read_text(encoding='utf-8')
    page = adapter.parse_listing(listing, adapter.listing_urls[0])
    candidate = next(c for c in page.candidates if c.external_id == '681')
    return adapter, listing, page, candidate, detail


def test_publiconsult_official_identity_and_document_labels():
    adapter, _, page, candidate, detail = sample()
    assert len(page.candidates) == 13
    assert '\ufffd' not in candidate.title_observed
    adapter.confirm_identity(candidate, detail, candidate.detail_url_observed)
    documents = adapter.documents(detail, candidate)
    assert len(documents) == 15
    chosen = adapter.choose_document(documents)
    assert chosen.title == 'Edital de Abertura de Inscrições'
    assert all(d.kind != 'edital' for d in documents if d != chosen)
    assert not page.terminal_evidence  # no proved exhaustion of the portal


def test_publiconsult_capture_hashes_and_no_lossy_decoding():
    manifest = json.loads((ROOT/'manifest-publiconsult.json').read_text(encoding='utf-8'))
    for page in manifest['pages']:
        raw = (ROOT/page['file']).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == page['fixture_sha256']
        assert '\ufffd' not in raw.decode('utf-8')
        assert 'Signature=' not in raw.decode('utf-8')


def test_publiconsult_synthetic_limit_blank_and_challenge():
    adapter, listing, _, _, _ = sample()
    limited = adapter.parse_listing(listing, adapter.listing_urls[0], 1)
    assert limited.truncated and len(limited.candidates) == 1
    assert not limited.terminal_evidence
    blank = adapter.parse_listing('<main>Sem resultados</main>', adapter.listing_urls[0])
    assert not blank.empty_evidence and not blank.terminal_evidence
    with pytest.raises(ValueError):
        adapter.parse_listing('<main>Verify you are human</main>', adapter.listing_urls[0])


def test_publiconsult_synthetic_cross_contest_and_wrong_title():
    adapter, _, _, candidate, detail = sample()
    with pytest.raises(ValueError):
        adapter.confirm_identity(candidate.model_copy(update={'external_id': '682'}), detail, candidate.detail_url_observed)
    with pytest.raises(ValueError):
        adapter.confirm_identity(candidate.model_copy(update={'title_observed': 'Concurso Polícia Civil Amazonas'}), detail, candidate.detail_url_observed)
    doc = adapter.choose_document(adapter.documents(detail, candidate))
    for bad in [doc.url_requested.replace('/681/', '/682/'),
                doc.url_requested.replace('/publiconsult/', '/another/'),
                doc.url_requested.replace('gsistbucket.s3.amazonaws.com', '127.0.0.1'),
                doc.url_requested+'?redirect=https://example.test',
                doc.url_requested+'?raw=1&raw=2']:
        with pytest.raises((ValueError, DestinationBlocked)):
            adapter.validate_document_url(bad, candidate)


def test_publiconsult_synthetic_ambiguity_and_other_documents():
    adapter, _, _, candidate, detail = sample()
    docs = adapter.documents(detail, candidate)
    main = adapter.choose_document(docs)
    with pytest.raises(ValueError):
        adapter.choose_document([d for d in docs if d.kind != 'edital'])
    with pytest.raises(ValueError):
        adapter.choose_document([main, main.model_copy(update={'doc_id': 'different', 'url_requested': main.url_requested+'?raw=1'})])


def test_publiconsult_hidden_tabs_require_observed_initialization():
    adapter, listing, _, _, _ = sample()
    disabled = listing.replace("$('#tabs').show();", '')
    assert disabled != listing
    page = adapter.parse_listing(disabled, adapter.listing_urls[0])
    assert not page.candidates and not page.empty_evidence
