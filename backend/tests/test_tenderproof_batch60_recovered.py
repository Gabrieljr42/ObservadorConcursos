import hashlib
import json
from pathlib import Path

import pytest

from app.tenderproof.batch60_recovered_adapters import BATCH60_RECOVERED_ADAPTERS
from app.tenderproof.source_adapter_base import SourcePageBlocked

FIXTURES = Path(__file__).parent / 'fixtures/tenderproof_batch60_blockers'
ROOT = Path(__file__).resolve().parents[2]


def preserved(source):
    rows = json.loads((ROOT / 'docs/tenderproof-batch60-blockers.json').read_text(encoding='utf8'))['pages']
    for file in ('followup-manifest.json', 'detail-manifest.json'):
        rows += json.loads((FIXTURES / file).read_text(encoding='utf8'))['pages']
    adapter = BATCH60_RECOVERED_ADAPTERS[source]
    listing = next(r for r in rows if r['url'] == adapter.listing_urls[0])
    detail = next(r for r in rows if r['source'] == source and '/publicacoes/' in r['url'])
    def read(row):
        raw = (FIXTURES / row['file']).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == row['sha256']
        assert row['status'] == 200
        return raw.decode('utf8')
    html = read(listing)
    page = adapter.parse_listing(html, listing['url'])
    candidate = next(c for c in page.candidates if c.detail_url_observed == detail['url'])
    return adapter, html, candidate, read(detail)


@pytest.mark.parametrize('source', BATCH60_RECOVERED_ADAPTERS)
def test_real_contract(source):
    adapter, html, candidate, detail = preserved(source)
    adapter.confirm_identity(candidate, detail, candidate.detail_url_observed)
    documents = adapter.documents(detail, candidate)
    chosen = adapter.choose_document(documents)
    assert chosen.kind == 'edital'
    assert '/PUBLICA' in chosen.url_requested
    assert len(documents) >= 4
    page = adapter.parse_listing(html, adapter.listing_urls[0], limit=1)
    assert len(page.candidates) == 1 and page.truncated
    assert page.terminal_evidence is None


@pytest.mark.parametrize('source', BATCH60_RECOVERED_ADAPTERS)
def test_identity_and_process_mismatch_rejected(source):
    adapter, _, candidate, detail = preserved(source)
    wrong_title = candidate.model_copy(update={'title_observed': 'Universidade Federal do Amazonas Engenharia Nuclear'})
    with pytest.raises(ValueError, match='título'):
        adapter.confirm_identity(wrong_title, detail, candidate.detail_url_observed)
    chosen = adapter.choose_document(adapter.documents(detail, candidate))
    wrong = chosen.url_requested.replace('/' + adapter.process_id(candidate) + '/', '/99999/')
    with pytest.raises(ValueError, match='processo'):
        adapter.validate_document_url(wrong, candidate)
    with pytest.raises(ValueError):
        adapter.confirm_identity(candidate, detail, candidate.detail_url_observed + '?id=2')


@pytest.mark.parametrize('source', BATCH60_RECOVERED_ADAPTERS)
def test_ambiguity_retification_and_unknown_preserved(source):
    adapter, _, candidate, detail = preserved(source)
    docs = adapter.documents(detail, candidate)
    chosen = adapter.choose_document(docs)
    second = chosen.model_copy(update={'doc_id': 'second-original', 'url_requested': chosen.url_requested.replace('.pdf', '-2.pdf')})
    with pytest.raises(ValueError):
        adapter.choose_document([*docs, second])
    with pytest.raises(ValueError):
        adapter.choose_document([d for d in docs if d.kind != 'edital'])


@pytest.mark.parametrize('source', BATCH60_RECOVERED_ADAPTERS)
def test_empty_challenge_limit_and_headers(source):
    adapter = BATCH60_RECOVERED_ADAPTERS[source]
    page = adapter.parse_listing('<main><p>Nenhum resultado</p></main>', adapter.listing_urls[0])
    assert not page.candidates and not page.empty_evidence and not page.terminal_evidence
    for message in ('Just a moment...', 'Navegador incompatível com o sistema'):
        with pytest.raises(SourcePageBlocked):
            adapter.parse_listing('<h1>' + message + '</h1>', adapter.listing_urls[0])
    with pytest.raises(ValueError):
        adapter.parse_listing('x' * (2 * 1024 * 1024 + 1), adapter.listing_urls[0])
    assert set(adapter.request_headers(adapter.listing_urls[0])) == {'User-Agent'}
    assert adapter.request_headers('https://example.test/') == {}


def test_shdias_observed_listing_only_and_invalid_base64():
    adapter = BATCH60_RECOVERED_ADAPTERS['shdias_open']
    for url in ('https://www.shdias.com.br/concursos/', 'https://www.shdias.com.br/concursos/index/?status=andamento&busca=x', 'https://www.shdias.com.br/concursos/index/?status=andamento&busca=&status=andamento'):
        with pytest.raises(ValueError):
            adapter.validate_listing_url(url)
    with pytest.raises(ValueError):
        adapter.candidate_from_url('https://www.shdias.com.br/concursos/publicacoes/ABC/XYZ')


def test_epl_literal_onclick_only():
    adapter, _, candidate, detail = preserved('epl_open')
    assert len(adapter.documents(detail.replace('nova_pagina(', 'evil('), candidate)) == 0


@pytest.mark.parametrize('source', ('apta_open', 'shdias_open'))
def test_external_publications_recorded_but_not_principal(source):
    adapter, _, candidate, detail = preserved(source)
    external = next(d for d in adapter.documents(detail, candidate) if 'dropbox.com' in d.url_requested)
    with pytest.raises(ValueError, match='externo'):
        adapter.choose_document([external.model_copy(update={'title': 'Edital de abertura', 'kind': 'edital'})])
    with pytest.raises(ValueError):
        adapter.validate_document_url(external.url_requested + '&redirect=https://example.test', candidate)
