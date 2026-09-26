import json
from pathlib import Path

import pytest

from app.tenderproof.batch60_extended_adapters import CPCONAdapter, GualimpAdapter

OWN = Path(__file__).parent / 'fixtures/tenderproof_batch60_own'
EXTRA = Path(__file__).parent / 'fixtures/tenderproof_batch60_extended'


def gualimp():
    a = GualimpAdapter()
    page = a.parse_listing((OWN/'gualimp_open-detail0.html').read_text(encoding='utf8'), a.listing_urls[0])
    candidate = next(c for c in page.candidates if c.external_id == '135')
    html = (OWN/'gualimp_open-sample-detail.html').read_text(encoding='utf8')
    rows = json.loads((EXTRA/'ajax-manifest.json').read_text(encoding='utf8'))['pages']
    resources = [{'url': row['url'], 'body': (EXTRA/row['file']).read_text(encoding='utf8')} for row in rows if '.php' in row['url']]
    return a, candidate, html, resources


def test_gualimp_real_json_composition_and_principal():
    a, c, h, resources = gualimp()
    composed = a.compose_detail(h, c.detail_url_observed, resources)
    a.confirm_identity(c, composed, c.detail_url_observed)
    docs = a.documents(composed, c)
    assert len(docs) == 7
    chosen = a.choose_document(docs)
    assert 'ABERTURA' in chosen.title and chosen.kind == 'edital'
    assert '/attachment/docs/' in chosen.url_requested
    with pytest.raises(ValueError):
        a.confirm_identity(c, h, c.detail_url_observed)


@pytest.mark.parametrize('number', ['999/2099', '999/2019', '002/2099', 'não informado'])
def test_gualimp_structured_number_must_match_explicit_listing(number):
    a, c, h, resources = gualimp()
    assert '002/2019' in c.title_observed
    identity = json.loads(resources[0]['body'])
    identity[0]['nr_concurso'] = number
    resources[0]['body'] = json.dumps(identity)
    composed = a.compose_detail(h, c.detail_url_observed, resources)
    # A matching number in unrelated publication text cannot hide the conflict.
    composed = composed.replace('</h1>', ' 002/2019</h1>')
    with pytest.raises(ValueError, match='número/ano Gualimp'):
        a.confirm_identity(c, composed, c.detail_url_observed)


def test_gualimp_number_not_inferred_when_listing_omits_it():
    a, c, h, resources = gualimp()
    c = c.model_copy(update={'title_observed': 'PREFEITURA MUNICIPAL DE PORCIÚNCULA/RJ'})
    composed = a.compose_detail(h, c.detail_url_observed, resources)
    a.confirm_identity(c, composed, c.detail_url_observed)


def test_gualimp_number_check_preserves_original_transport_evidence():
    from bs4 import BeautifulSoup
    from html import unescape
    a, c, h, resources = gualimp()
    composed = a.compose_detail(h, c.detail_url_observed, resources)
    a.confirm_identity(c, composed, c.detail_url_observed)
    evidence = BeautifulSoup(composed, 'html.parser').select_one('#gualimp-transport-evidence')
    assert json.loads(unescape(evidence.get_text())) == resources
    with pytest.raises(ValueError, match='número/ano Gualimp'):
        a.confirm_identity(c, composed[:composed.index('<script')], c.detail_url_observed)


@pytest.mark.parametrize('mutation', ['wrong_id', 'duplicate', 'missing', 'bad_identity', 'empty_publications', 'two_identities'])
def test_gualimp_incomplete_or_cross_identity_rejected(mutation):
    a,c,h,rr = gualimp()
    if mutation == 'wrong_id': rr[1]['url'] = rr[1]['url'].replace('135','134')
    if mutation == 'duplicate': rr[1] = rr[0]
    if mutation == 'missing': rr.pop()
    if mutation == 'bad_identity': rr[0]['body'] = '[{"ds_cliente":"Other"}]'
    if mutation == 'empty_publications': rr[1]['body'] = '[]'
    if mutation == 'two_identities': rr[0]['body'] = json.dumps(json.loads(rr[0]['body'])*2)
    with pytest.raises(ValueError): a.compose_detail(h,c.detail_url_observed,rr)


def test_gualimp_script_drift_and_wrong_function_rejected():
    a,c,h,rr = gualimp()
    with pytest.raises(ValueError): a.detail_resource_urls(h.replace('load_publicacoes','unrecognized'),c.detail_url_observed)
    with pytest.raises(ValueError): a.validate_detail_resource_url(rr[0]['url'].replace('load_ps','save_ps'),c)
    with pytest.raises(ValueError): a.validate_document_url('https://gualimpconsultoria.com.br/attachment/docs/../private.pdf',c)
    composed=a.compose_detail(h,c.detail_url_observed,rr)
    with pytest.raises(ValueError): a.confirm_identity(c.model_copy(update={'title_observed':'Universidade Federal do Acre Engenharia'}),composed,c.detail_url_observed)


def test_cpcon_observed_retifications_not_principal_and_refresh_stable_id():
    a = CPCONAdapter()
    page = a.parse_listing((OWN/'cpcon_open-listing0.html').read_text(encoding='utf8'), a.listing_urls[0])
    c=next(c for c in page.candidates if c.external_id=='uepb-002-2026')
    h=(OWN/'cpcon_open-detail0.html').read_text(encoding='utf8')
    a.confirm_identity(c,h,c.detail_url_observed)
    docs=a.documents(h,c)
    assert docs and not any(d.kind=='edital' for d in docs)
    with pytest.raises(ValueError):a.choose_document(docs)
    import re
    changed=re.sub(r'refresh=[A-Za-z0-9]+','refresh=ChangedRefresh123456',h)
    newer=a.documents(changed,c)
    assert [d.doc_id for d in docs]==[d.doc_id for d in newer]
    assert docs[0].url_requested!=newer[0].url_requested
    with pytest.raises(ValueError):a.validate_document_url(docs[0].url_requested+'&wpdmdl=999',c)
    with pytest.raises(ValueError):a.confirm_identity(c,h,c.detail_url_observed.replace('uepb-002','uepb-001'))


@pytest.mark.parametrize('adapter', [CPCONAdapter(),GualimpAdapter()])
def test_coverage_limits_and_no_fake_empty(adapter):
    file=OWN/('cpcon_open-listing0.html' if adapter.source=='cpcon_open' else 'gualimp_open-detail0.html')
    page=adapter.parse_listing(file.read_text(encoding='utf8'),adapter.listing_urls[0],limit=1)
    assert page.truncated and len(page.candidates)==1 and page.terminal_evidence is None
    empty=adapter.parse_listing('<h1>Nenhum concurso</h1>',adapter.listing_urls[0])
    assert not empty.empty_evidence and not empty.terminal_evidence


def test_cpcon_excludes_non_employment_residency():
    a=CPCONAdapter()
    assert not a.in_scope('Processo seletivo para residência jurídica e multidisciplinar','https://cpcon.uepb.edu.br/residencia/')


def test_cpcon_pdf_identity_pattern_excludes_dates_and_registration_app():
    import re
    a = CPCONAdapter()
    assert not re.findall(a.document_identity_pattern, '11/12/2026 https://cpcon.uepb.edu.br/sigeps-app/ https://uepb.edu.br/progep/')
    assert re.findall(a.document_identity_pattern, 'https://cpcon.uepb.edu.br/processo-seletivo-simplificado-no-002-2026/') == ['processo-seletivo-simplificado-no-002-2026']
