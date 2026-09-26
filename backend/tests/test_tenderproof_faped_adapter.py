from types import SimpleNamespace
import pytest

from app.tenderproof.faped_adapter import FapedAdapter
from app.tenderproof.faped_parser import LISTING
from test_tenderproof_faped_parser import listing, append, link


def test_listing_and_fragment_detail_do_not_mix_other_source_sections():
    adapter = FapedAdapter()
    html = listing() + append(876, link('Resultado da entrevista', 'result.pdf'))
    page = adapter.parse_listing(html, LISTING)
    assert len(page.candidates) == 1 and page.terminal_evidence is None
    candidate = page.candidates[0]
    requests = []
    def fetch(url, validator, maximum):
        validator(url)
        requests.append(url)
        return SimpleNamespace(url_final=url, content=html.encode('iso-8859-1'))
    preserved = adapter.acquire_detail(candidate.detail_url_observed, candidate, fetch)
    assert requests == [LISTING]
    assert candidate.detail_url_observed.endswith('#docfor876')
    assert len(adapter.documents(preserved, candidate)) == 2
    with pytest.raises(ValueError): adapter.parse_listing(html, 'https://faped.org.br/editais&filter=1')


def test_missing_and_wrong_candidate_identity_are_rejected():
    adapter = FapedAdapter()
    candidate = adapter.candidate_from_url(LISTING + '#docfor900')
    with pytest.raises(ValueError): adapter.confirm_identity(candidate, listing(), candidate.detail_url_observed)
    candidate = adapter.candidate_from_url(LISTING + '#docfor876')
    candidate.source = 'other'
    with pytest.raises(ValueError): adapter.documents(listing(), candidate)


def test_principal_document_requires_unique_observed_opening_attachment():
    adapter = FapedAdapter()
    html = listing().replace('<span>Edital</span>', '<span>Anexo de abertura</span>')
    candidate = adapter.parse_listing(html, LISTING).candidates[0]
    docs = adapter.documents(html, candidate)
    assert adapter.choose_document(docs).kind == 'edital'
    assert 'PROCESSO SELETIVO' in docs[0].title
    assert 'Anexo de abertura' not in docs[0].title
    assert 'Anexo de abertura' in docs[0].reason_chosen
    with pytest.raises(ValueError): adapter.choose_document(docs + docs)
    with pytest.raises(ValueError): adapter.choose_document([])


def test_limit_is_reported_and_unknown_detail_routes_are_rejected():
    adapter = FapedAdapter()
    page = adapter.parse_listing(listing(1) + listing(2), LISTING, limit=1)
    assert page.truncated and len(page.candidates) == 1
    for url in (LISTING, LISTING + '#docfor0', LISTING + '#docfor1?other=2',
                'https://other.test/editais&filter=2#docfor1'):
        with pytest.raises(ValueError): adapter.candidate_from_url(url)


def test_website_closed_label_is_preserved_without_becoming_part_of_pdf_title():
    page = FapedAdapter().parse_listing(listing().replace('04/2026</h5>', '04/2026 Encerrado</h5>'), LISTING)
    candidate = page.candidates[0]
    assert candidate.title_observed.endswith('04/2026')
    assert candidate.selection_label_observed.endswith('Encerrado')


def test_legacy_candidate_closed_label_requires_matching_notice_and_foundation():
    from app.tenderproof.contracts import PageText
    adapter = FapedAdapter()
    candidate = adapter.candidate_from_url(LISTING + '#docfor876', 'PROCESSO SELETIVO SIMPLIFICADO 045/2027 Encerrado')
    pages = [PageText(artifact_id='doc',page_number=1,text='Fundação de Apoio à Pesquisa e ao Desenvolvimento - FAPED\nEDITAL DE PROCESSO SELETIVO SIMPLIFICADO Nº. 045/2027')]
    assert adapter.document_title_corroborated(candidate,pages)
    pages[0].text = pages[0].text.replace('045/2027','046/2027')
    assert not adapter.document_title_corroborated(candidate,pages)
