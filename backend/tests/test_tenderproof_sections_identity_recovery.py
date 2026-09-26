from pathlib import Path

from bs4 import UnicodeDammit
import pytest

from app.tenderproof.batch99_foundation_adapters import FAPPRAdapter
from app.tenderproof.contracts import DiscoveredCandidate


def test_preserved_unicode_title_roundtrip_keeps_section_and_document_identity():
    html = UnicodeDammit((Path(__file__).parent / 'fixtures/tenderproof_batch99_foundations/fappr_selection-listing0.html').read_bytes()).unicode_markup
    adapter = FAPPRAdapter()
    candidates = adapter.parse_listing(html, adapter.listing_urls[0]).candidates
    original = next(c for c in candidates if c.external_id == '03/2026')
    candidate = DiscoveredCandidate.model_validate_json(original.model_dump_json())
    assert candidate.title_observed == 'Fundação Araucária - PS 03/2026: Estágio no Setor de Ciência e Tecnologia'
    assert candidate == original
    assert adapter.section_identity(candidate.title_observed) == '03/2026'
    document = adapter.choose_document(adapter.documents(html, candidate))
    assert document.url_requested.endswith('/ps_032026_editalestagiario_setorsecet_assinado.pdf')
    assert any(c.external_id == '04/2026' and c.detail_url_observed == candidate.detail_url_observed for c in candidates)
    with pytest.raises(ValueError):
        adapter.documents(html, candidate.model_copy(update={'external_id': '04/2026'}))
    with pytest.raises(ValueError):
        adapter.documents(html, adapter.candidate_from_url(candidate.detail_url_observed))
