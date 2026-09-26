import hashlib
import json
from pathlib import Path
from datetime import datetime, timezone

from bs4 import UnicodeDammit
import pytest

from app.tenderproof.batch99_foundation_adapters import BATCH99_FOUNDATION_ADAPTERS, BATCH99_FOUNDATION_SECTION_ADAPTERS
from app.tenderproof.contracts import Artifact, DiscoveredCandidate, PageText
from app.tenderproof.fields import _extract_inscricoes, _extract_orgao
from test_tenderproof_publication import env

FIX = Path(__file__).parent/'fixtures/tenderproof_batch99_foundations'

def fixture(source, name):
    return UnicodeDammit((FIX/f'{source}-{name}.html').read_bytes()).unicode_markup

def sample(source):
    adapter = BATCH99_FOUNDATION_ADAPTERS[source]
    page = adapter.parse_listing(fixture(source, 'listing0'), adapter.listing_urls[0])
    if source == 'funpec_selection':
        candidate, name = page.candidates[1], 'detail1'
    elif source == 'fade_selection':
        candidate = next(c for c in page.candidates if 'servicos-gerais-' in c.detail_url_observed)
        name = 'detail0'
    else:
        candidate, name = page.candidates[0], 'listing0'
    return adapter, candidate, fixture(source, name)

@pytest.mark.parametrize('source', list(BATCH99_FOUNDATION_ADAPTERS))
def test_observed_contract_principal_identity_and_partial_coverage(source):
    adapter, candidate, html = sample(source)
    adapter.confirm_identity(candidate, html, candidate.detail_url_observed)
    doc = adapter.choose_document(adapter.documents(html, candidate))
    assert doc.kind == 'edital'
    adapter.validate_document_url(doc.url_requested, candidate)
    page = adapter.parse_listing(fixture(source, 'listing0'), adapter.listing_urls[0], limit=1)
    assert not page.empty_evidence and not page.terminal_evidence
    assert page.truncated == (source != 'fapergs_selection')
    if source == 'funpec_selection':
        assert 'https://funpec.br/processos-seletivos/?pagina=2' in page.next_urls

def test_funpec_real_contradiction_remains_impediment():
    adapter = BATCH99_FOUNDATION_ADAPTERS['funpec_selection']
    candidate = adapter.parse_listing(fixture(adapter.source, 'listing0'), adapter.listing_urls[0]).candidates[0]
    with pytest.raises(ValueError, match='diverge'):
        adapter.documents(fixture(adapter.source, 'detail0'), candidate)

@pytest.mark.parametrize('source', ['funpec_selection', 'fade_selection'])
def test_wrong_header_number_canonical_and_unrelated_text_rejected(source):
    adapter, candidate, html = sample(source)
    number = '10/2026' if source == 'funpec_selection' else '090/2026'
    changed = html.replace(number, '999/2099') + '<p>' + candidate.title_observed + '</p>'
    with pytest.raises(ValueError):
        adapter.confirm_identity(candidate, changed, candidate.detail_url_observed)
    with pytest.raises(ValueError):
        adapter.confirm_identity(candidate, html.replace('rel="canonical"', 'rel="not-canonical"'), candidate.detail_url_observed)

@pytest.mark.parametrize('source', list(BATCH99_FOUNDATION_ADAPTERS))
def test_cross_source_identity_destinations_and_ambiguous_principal(source):
    adapter, candidate, html = sample(source)
    with pytest.raises(ValueError):
        adapter.confirm_identity(candidate.model_copy(update={'source': 'other'}), html, candidate.detail_url_observed)
    doc = adapter.choose_document(adapter.documents(html, candidate))
    for url in [doc.url_requested.replace('https://', 'http://'), doc.url_requested+'?token=1',
                doc.url_requested.replace('/upload', '/../upload'), 'https://127.0.0.1/private.pdf']:
        with pytest.raises(Exception):
            adapter.validate_document_url(url, candidate)
    with pytest.raises(ValueError):
        adapter.choose_document([doc, doc.model_copy(update={'doc_id': 'different', 'url_requested': doc.url_requested.replace('.pdf', '-different.pdf')})])

@pytest.mark.parametrize('source', list(BATCH99_FOUNDATION_ADAPTERS))
def test_unknown_empty_challenge_and_limits_preserve_evidence(source):
    adapter, candidate, html = sample(source)
    page = adapter.parse_listing('<h1>Nenhuma seleção</h1>', adapter.listing_urls[0])
    assert not page.candidates and not page.empty_evidence and not page.terminal_evidence
    with pytest.raises(ValueError):
        adapter.parse_listing('<p>Verify you are human</p>', adapter.listing_urls[0])
    with pytest.raises(ValueError):
        adapter.parse_listing('x'*(2097152+1), adapter.listing_urls[0])
    with pytest.raises(ValueError):
        adapter.documents('x'*(2097152+1), candidate)

@pytest.mark.parametrize('source', ['funpec_selection', 'fade_selection'])
@pytest.mark.parametrize('title', ['Edital bolsa acadêmica', 'Seleção de bolsista pesquisador', 'Vestibular 2026', 'Edital de fomento'])
def test_personnel_filters(source, title):
    adapter = BATCH99_FOUNDATION_ADAPTERS[source]
    assert not adapter.in_scope(title, adapter.listing_urls[0])

def test_fapergs_specific_year_and_non_original_labels():
    adapter, candidate, html = sample('fapergs_selection')
    with pytest.raises(ValueError):
        adapter.confirm_identity(candidate, html.replace('Processo Seletivo 2025', 'Processo Seletivo 2024'), candidate.detail_url_observed)
    docs = adapter.documents(html, candidate)
    assert sum(d.kind == 'edital' for d in docs) == 1
    assert any('ADITIVO' in d.title and d.kind != 'edital' for d in docs)

def test_original_captures_sha256():
    for path in FIX.glob('*-manifest.json'):
        for row in json.loads(path.read_text(encoding='utf8'))['pages']:
            if row.get('file'):
                assert hashlib.sha256((FIX/row['file']).read_bytes()).hexdigest() == row['sha256']


@pytest.mark.parametrize('source', list(BATCH99_FOUNDATION_SECTION_ADAPTERS))
def test_same_url_sections_have_distinct_ids_and_exclusive_documents(source):
    adapter = BATCH99_FOUNDATION_SECTION_ADAPTERS[source]
    html = fixture(source, 'listing0')
    page = adapter.parse_listing(html, adapter.listing_urls[0], limit=2)
    first, second = page.candidates
    assert page.truncated and not page.terminal_evidence
    assert first.detail_url_observed == second.detail_url_observed
    assert first.external_id != second.external_id and first.candidate_id != second.candidate_id
    assert adapter.candidate_from_url(first.detail_url_observed, first.title_observed).external_id == first.external_id
    first_docs, second_docs = (adapter.documents(html, c) for c in (first, second))
    assert adapter.choose_document(first_docs).url_requested != adapter.choose_document(second_docs).url_requested
    assert not set(d.url_requested for d in first_docs) & set(d.url_requested for d in second_docs)
    with pytest.raises(ValueError):
        adapter.confirm_identity(first.model_copy(update={'external_id': second.external_id}), html, first.detail_url_observed)
    with pytest.raises(ValueError):
        adapter.confirm_identity(first, html.replace(first.external_id, '9999/9999999-99'), first.detail_url_observed) if source == 'fatec_selection' else adapter.confirm_identity(first.model_copy(update={'title_observed': second.title_observed}), html, first.detail_url_observed)


@pytest.mark.parametrize('source', list(BATCH99_FOUNDATION_SECTION_ADAPTERS))
def test_section_transport_context_is_not_candidate_or_canonical_identity(source, env):
    from fastapi import HTTPException
    from app.models import Source
    from app.tenderproof.canonical import context
    db, _, _, _, run, _ = env
    db.add(Source(name=source, base_url=BATCH99_FOUNDATION_SECTION_ADAPTERS[source].listing_urls[0], source_type=source))
    db.commit()
    adapter = BATCH99_FOUNDATION_SECTION_ADAPTERS[source]
    transport = adapter.candidate_from_url(adapter.listing_urls[0])
    assert transport.external_id is None
    with pytest.raises(ValueError):
        adapter.confirm_identity(transport, fixture(source, 'listing0'), transport.detail_url_observed)
    with pytest.raises(ValueError):
        adapter.documents(fixture(source, 'listing0'), transport)
    run = run.model_copy(update={'source': source, 'candidates': [transport], 'selected_candidate_id': transport.candidate_id})
    with pytest.raises(HTTPException) as exc:
        context(db, run)
    assert exc.value.status_code == 422


@pytest.mark.parametrize('source', list(BATCH99_FOUNDATION_SECTION_ADAPTERS))
def test_canonical_resolver_and_bind_do_not_merge_same_page_external_ids(source, env, monkeypatch):
    """Resolver/ledger unit proof; PDF revalidation is a separate live gate."""
    from types import SimpleNamespace
    from sqlalchemy import select
    from app.models import Source, Concurso
    from app.tenderproof import canonical, publication
    from app.tenderproof.publication_models import CanonicalIdentity
    db, _, _, _, original, store = env
    adapter = BATCH99_FOUNDATION_SECTION_ADAPTERS[source]
    configured = Source(name=source, base_url=adapter.listing_urls[0], source_type=source)
    db.add(configured)
    db.commit()
    candidates = adapter.parse_listing(fixture(source, 'listing0'), adapter.listing_urls[0], limit=2).candidates
    created = []
    for candidate in candidates:
        values = {'titulo': candidate.title_observed, 'orgao': source, 'edital_numero': candidate.external_id}
        monkeypatch.setattr(publication, '_revalidate', lambda *args, v=values: (v, {}))
        run = original.model_copy(update={'source': source, 'candidates': [candidate], 'selected_candidate_id': candidate.candidate_id})
        target, _, _, _, _, identity = canonical.resolve(db, run, store)
        assert target is None
        contest = Concurso(source_id=configured.id, external_id=candidate.external_id, banca=source, content_hash='a'*64,
                           link_pagina=candidate.detail_url_observed, **values)
        db.add(contest)
        db.flush()
        proposal = SimpleNamespace(id=100+len(created), approved_by=1,
            payload={'run': {'artifact': {'sha256': original.artifact.sha256}}})
        canonical.bind(db, contest, identity, proposal)
        db.commit()
        again, *_ = canonical.resolve(db, run, store)
        assert again.id == contest.id
        created.append(contest)
    assert created[0].id != created[1].id
    keys = db.scalars(select(CanonicalIdentity).where(CanonicalIdentity.concurso_id.in_([c.id for c in created]))).all()
    assert len(keys) == 4


def test_fappr_expands_only_observed_year_accordions_and_excludes_funding():
    adapter = BATCH99_FOUNDATION_SECTION_ADAPTERS['fappr_selection']
    page = adapter.parse_listing(fixture(adapter.source, 'listing0'), adapter.listing_urls[0])
    assert any(c.external_id == '001/25' for c in page.candidates)
    assert not any('bolsista' in (c.title_observed or '').lower() or 'Eleição' in (c.title_observed or '') for c in page.candidates)


@pytest.mark.parametrize('source', list(BATCH99_FOUNDATION_SECTION_ADAPTERS))
def test_full_publication_distinct_sections_same_url_revalidates_pdf_and_preserves_rollback_history(source, env, monkeypatch):
    """Synthetic PDF bytes, actual publication path; no revalidation stub."""
    from datetime import datetime, timezone
    import textwrap
    from sqlalchemy import select
    from app.models import Source, Concurso, ConcursoVersion
    from app.tenderproof import publication, source_adapters
    from app.tenderproof.contracts import Artifact, DocumentCandidate, TenderProofRun
    from app.tenderproof.demo_pdf import make_text_pdf
    from app.tenderproof.fields import extract_fields
    from app.tenderproof.mock_demo import PDF_PAGE_1
    from app.tenderproof.pdf_text import extract_pages
    from app.tenderproof.pilot_adapters import folded
    from app.tenderproof.publication_models import CanonicalIdentity
    db, _, user, _, _, store = env
    adapter = BATCH99_FOUNDATION_SECTION_ADAPTERS[source]
    monkeypatch.setitem(source_adapters.SOURCE_ADAPTERS, source, adapter)
    configured = Source(name=source, base_url=adapter.listing_urls[0], source_type=source)
    db.add(configured)
    db.commit()
    html = fixture(source, 'listing0')
    candidates = adapter.parse_listing(html, adapter.listing_urls[0], limit=2).candidates
    applied = []
    for index, candidate in enumerate(candidates, 1):
        chosen = adapter.choose_document(adapter.documents(html, candidate))
        body = PDF_PAGE_1.replace('01/2026', f'{index+20:02d}/2026') + '\n' + '\n'.join(textwrap.wrap(folded(candidate.title_observed), width=70))
        data = make_text_pdf([body])
        artifact = Artifact(artifact_id=f'section-{index}', sha256=hashlib.sha256(data).hexdigest(),
            byte_len=len(data), url_requested=chosen.url_requested, url_final=chosen.url_requested,
            downloaded_at=datetime.now(timezone.utc))
        store.save_artifact_file(artifact, data)
        pages, *_ = extract_pages(data, artifact_id=artifact.artifact_id)
        run = TenderProofRun(run_id=f'section-{source}-{index}', owner_user_id=user.id,
            source=source, mode='mock', is_synthetic_sample=True, execution_status='completed',
            validation_status='valid', candidates=[candidate], selected_candidate_id=candidate.candidate_id,
            document=DocumentCandidate(doc_id=f'doc-{index}', title='Edital de abertura', kind='edital', url_requested=chosen.url_requested),
            artifact=artifact, fields=extract_fields(candidate=candidate, artifact=artifact, pages=pages))
        proposal = publication.create_proposal(db, run=run, user=user, store=store)
        assert proposal['action'] == 'create'
        approved = publication.approve_proposal(db, proposal_id=proposal['id'], proposal_hash=proposal['proposal_hash'],
            fields=proposal['eligible_fields'], user=user, store=store)
        result = publication.apply_proposal(db, proposal_id=approved['id'], proposal_hash=approved['proposal_hash'], user=user, store=store)
        repeat = publication.apply_proposal(db, proposal_id=approved['id'], proposal_hash=approved['proposal_hash'], user=user, store=store)
        assert repeat['version_id'] == result['version_id']
        applied.append(result)
    assert applied[0]['concurso_id'] != applied[1]['concurso_id']
    records = db.scalars(select(Concurso).where(Concurso.source_id == configured.id)).all()
    assert len(records) == 2 and len({c.link_pagina for c in records}) == 1
    identity_before = [(r.key, r.concurso_id) for r in db.scalars(select(CanonicalIdentity))]
    publication.rollback_proposal(db, proposal_id=applied[0]['id'], reason='synthetic isolated rollback proof', user=user)
    assert [(r.key, r.concurso_id) for r in db.scalars(select(CanonicalIdentity))] == identity_before
    assert len(db.scalars(select(Concurso).where(Concurso.source_id == configured.id)).all()) == 2
    assert len(db.scalars(select(ConcursoVersion).where(ConcursoVersion.concurso_id.in_([r['concurso_id'] for r in applied]))).all()) == 3



def fapese_sample():
    from app.tenderproof.batch99_foundation_adapters import FAPESEAdapter
    adapter = FAPESEAdapter()
    html = fixture(adapter.source, 'detail0')
    return adapter, html, adapter.parse_listing(html, adapter.listing_urls[0]).candidates[0]


def test_fapese_observed_personnel_rpa_card_principal_partial():
    adapter, html, candidate = fapese_sample()
    assert candidate.external_id == '007/2026'
    adapter.confirm_identity(candidate, html, candidate.detail_url_observed)
    chosen = adapter.choose_document(adapter.documents(html, candidate))
    assert chosen.kind == 'edital' and 'Edital-007.2026-RPA-PRONERA' in chosen.url_requested
    page = adapter.parse_listing(html, adapter.listing_urls[0])
    assert not page.empty_evidence and not page.terminal_evidence


def test_fapese_issuer_sentence_is_literal_orgao_evidence():
    candidate = DiscoveredCandidate(
        candidate_id='fapese-007', source='fapese_selection', external_id='007/2026',
        title_observed='FAPESE - PRONERA - EDITAL Nº 007/2026',
        detail_url_observed='https://www.fapese.org.br/pronera/',
        observed_at=datetime.now(timezone.utc),
    )
    artifact = Artifact(
        artifact_id='art-fapese-orgao', sha256='a' * 64, byte_len=10,
        url_requested='https://www.fapese.org.br/doc.pdf',
        url_final='https://www.fapese.org.br/doc.pdf',
        downloaded_at=datetime.now(timezone.utc),
    )
    page = PageText(
        artifact_id=artifact.artifact_id, page_number=1,
        text='A FUNDAÇÃO DE APOIO À PESQUISA E EXTENSÃO DE SERGIPE (FAPESE), pessoa jurídica de direito privado.',
    )
    field = _extract_orgao(candidate, artifact, [page])
    assert field.state.value == 'supported'
    assert field.value == 'FUNDAÇÃO DE APOIO À PESQUISA E EXTENSÃO DE SERGIPE (FAPESE)'
    assert field.evidence and 'FUNDAÇÃO DE APOIO' in field.evidence[0].snippet


def test_fapese_table_registration_period_is_source_contract():
    candidate = DiscoveredCandidate(
        candidate_id='fapese-007', source='fapese_selection', external_id='007/2026',
        title_observed='FAPESE - PRONERA - EDITAL Nº 007/2026',
        detail_url_observed='https://www.fapese.org.br/pronera/',
        observed_at=datetime.now(timezone.utc),
    )
    artifact = Artifact(
        artifact_id='art-fapese-period', sha256='b' * 64, byte_len=10,
        url_requested='https://www.fapese.org.br/doc.pdf',
        url_final='https://www.fapese.org.br/doc.pdf',
        downloaded_at=datetime.now(timezone.utc),
    )
    page = PageText(
        artifact_id=artifact.artifact_id, page_number=10,
        text='9. CRONOGRAMA DO CHAMAMENTO PÚBLICO:\n9.2 Inscrição 07/09/2026 a\n14/09/2026\naté as 23:59',
    )
    inicio, fim = _extract_inscricoes(candidate, artifact, [page])
    assert inicio.state.value == fim.state.value == 'supported'
    assert inicio.value == '2026-09-07' and fim.value == '2026-09-14'
    assert inicio.evidence[0].page_number == fim.evidence[0].page_number == 10


@pytest.mark.parametrize('mutation', ['header', 'number', 'canonical', 'duplicate', 'wrong_pdf', 'source', 'size', 'context'])
def test_fapese_identity_rejects_incompatible_evidence(mutation):
    from bs4 import BeautifulSoup
    adapter, html, candidate = fapese_sample()
    soup = BeautifulSoup(html, 'lxml')
    if mutation == 'header': soup.select_one('h1.page-title').string = 'Outro programa'
    elif mutation == 'number': soup.select_one('main h4.button-card__title').string = '03/09/2026 - '+candidate.title_observed.replace('007/2026', '999/2099')
    elif mutation == 'canonical': soup.select_one('link[rel=canonical]')['href'] = 'https://www.fapese.org.br/outro/'
    elif mutation == 'duplicate': soup.select_one('main').append(BeautifulSoup(str(soup.select_one('main a.button-card')), 'lxml'))
    elif mutation == 'wrong_pdf': soup.select_one('main a.button-card')['href'] = soup.select_one('main a.button-card')['href'].replace('007.2026', '008.2026')
    elif mutation == 'source': candidate = candidate.model_copy(update={'source':'other'})
    elif mutation == 'size': soup.append('x'*2097153)
    elif mutation == 'context': candidate = adapter.candidate_from_url(candidate.detail_url_observed)
    with pytest.raises(ValueError):
        adapter.confirm_identity(candidate, str(soup), candidate.detail_url_observed)
        adapter.documents(str(soup), candidate)


@pytest.mark.parametrize('label', ['RETIFICAÇÃO DO EDITAL Nº 007/2026', 'EDITAL Nº 007/2026 - BOLSISTAS DE PESQUISA', 'RESULTADO FINAL', 'SELEÇÃO DE MESTRADO PROFISSIONAL'])
def test_fapese_non_personnel_or_non_principal_is_not_promoted(label):
    from bs4 import BeautifulSoup
    adapter, html, candidate = fapese_sample()
    soup=BeautifulSoup(html,'lxml')
    soup.select_one('main h4.button-card__title').string = '03/09/2026 - '+label
    page = adapter.parse_listing(str(soup), adapter.listing_urls[0])
    assert not page.candidates and not page.empty_evidence


def test_fapese_wrong_destination_query_traversal_rejected():
    from app.tenderproof.security import DestinationBlocked
    adapter, html, candidate = fapese_sample()
    chosen=adapter.choose_document(adapter.documents(html,candidate))
    for url in [chosen.url_requested+'?download=1',chosen.url_requested.replace('https://','http://'),chosen.url_requested.replace('/wp-content/', '/../wp-content/'), chosen.url_requested.replace('www.fapese.org.br','example.org')]:
        with pytest.raises((ValueError, DestinationBlocked)): adapter.validate_document_url(url,candidate)
