"""IBFC HTTP captures of 2026-09-08; adversarial mutations explicitly synthetic.

Capture origin and SHA256 are recorded in docs/tenderproof-batch30-own-live.json.
Fixtures are decoded/sanitized HTML; these checks do not verify PDF bytes.
"""
from pathlib import Path

import pytest
from bs4 import BeautifulSoup

from app.tenderproof.batch30_own_adapters import IBFCAdapter


ROOT = Path(__file__).parent / 'fixtures/tenderproof_batch30_own'
DETAILS = {'494': 'a7e1781567', '490': 'e7c27c7e94'}


def observed(external_id):
    adapter = IBFCAdapter()
    listing = (ROOT / 'ibfc_open-cycle1-listing-822e0b4c54.html').read_text(encoding='utf-8')
    candidates = adapter.parse_listing(listing, 'https://concursos.ibfc.org.br/index/1/').candidates
    candidate = next(item for item in candidates if item.external_id == external_id)
    detail = (ROOT / f'ibfc_open-cycle1-detail-{DETAILS[external_id]}.html').read_text(encoding='utf-8')
    return adapter, candidate, detail


@pytest.mark.parametrize('external_id', DETAILS)
def test_empty_h2_and_rich_text_siblings_preserve_observed_identity(external_id):
    adapter, candidate, detail = observed(external_id)
    assert not BeautifulSoup(detail, 'html.parser').select_one('.dados > h2').get_text(strip=True)
    adapter.confirm_identity(candidate, detail, candidate.detail_url_observed)


@pytest.mark.parametrize('external_id', DETAILS)
def test_another_contest_header_cannot_be_corroborated_by_other_page_content(external_id):
    adapter, candidate, detail = observed(external_id)
    other = observed('490' if external_id == '494' else '494')[2]
    soup = BeautifulSoup(detail, 'html.parser')
    header = soup.select_one('.dados > h2').parent
    # Preserve the genuine title elsewhere: a broad page-text fallback would
    # incorrectly accept this cross-contest header despite the original URL.
    extra = soup.new_tag('h1')
    extra.string = candidate.title_observed
    soup.append(extra)
    header.replace_with(BeautifulSoup(other, 'html.parser').select_one('.dados > h2').parent)
    with pytest.raises(ValueError, match='título'):
        adapter.confirm_identity(candidate, str(soup), candidate.detail_url_observed)


@pytest.mark.parametrize('external_id', DETAILS)
def test_correct_title_does_not_override_different_detail_route(external_id):
    adapter, candidate, detail = observed(external_id)
    with pytest.raises(ValueError, match='identidade'):
        adapter.confirm_identity(candidate, detail, 'https://concursos.ibfc.org.br/informacoes/999/')


def test_490_multiple_original_notices_remain_ambiguous():
    adapter, candidate, detail = observed('490')
    documents = adapter.documents(detail, candidate)
    originals = [doc for doc in documents if doc.kind == 'edital']
    assert len(originals) == 3
    assert all(any(number in doc.title for number in ('002/2026', '003/2026', '004/2026')) for doc in originals)
    with pytest.raises(ValueError):
        adapter.choose_document(documents)


def test_494_original_document_is_unique_but_other_contest_document_is_rejected():
    adapter, candidate, detail = observed('494')
    chosen = adapter.choose_document(adapter.documents(detail, candidate))
    assert '28/2026' in chosen.title
    with pytest.raises(ValueError, match='outro concurso'):
        adapter.validate_document_url(chosen.url_requested.replace('/494/', '/490/'), candidate)
