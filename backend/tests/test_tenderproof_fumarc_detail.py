import json
from datetime import datetime, timezone
from types import SimpleNamespace
from urllib.parse import urlencode

import pytest

from app.tenderproof.fumarc_detail import acquire_detail, detail_api_url
from app.tenderproof.fumarc_publications import publication_url

NOW = datetime(2026, 9, 8, tzinfo=timezone.utc)


def transport(*, duplicate=False, wrong_detail=False, fail_last=False):
    first = publication_url(88, NOW)
    second = first + '&' + urlencode({'$skiptoken': 'Paged=TRUE&p_DataInicioPublicacao=20260901%2000%3A00%3A00&p_ID=1'})
    detail = {'d': {'results': [{'Id': 89 if wrong_detail else 88, 'Title': 'Concurso novo'}]}}
    one = {'d': {'results': [{'Id': 1, 'ConcursoId': 88, 'Title': 'Edital'}], '__next': second}}
    two = {'d': {'results': [{'Id': 1 if duplicate else 2, 'ConcursoId': 88, 'Title': 'Errata'}]}}
    mapping = {detail_api_url(88, NOW): detail, first: one, second: two}
    calls = []
    def fetch(url, validator, max_bytes):
        validator(url)
        calls.append(url)
        if fail_last and url == second:
            raise TimeoutError('deadline')
        return SimpleNamespace(content=json.dumps(mapping[url]).encode(), url_final=url)
    return fetch, calls


def test_detail_preserves_all_pages_and_original_query_evidence():
    fetch, calls = transport()
    result = json.loads(acquire_detail(88, fetch, NOW))
    assert result['contest_id'] == 88 and result['publications_complete']
    assert [r['url'] for r in result['resources']] == calls
    assert len(calls) == 3
    assert result['resources'][-1]['body']['d']['results'][0]['Title'] == 'Errata'


@pytest.mark.parametrize('options,error', [
    ({'duplicate': True}, ValueError),
    ({'wrong_detail': True}, ValueError),
    ({'fail_last': True}, TimeoutError),
])
def test_partial_or_mixed_acquisition_never_returns_complete_detail(options, error):
    fetch, calls = transport(**options)
    with pytest.raises(error):
        acquire_detail(88, fetch, NOW)
    if options.get('wrong_detail'):
        assert len(calls) == 1


def test_transport_redirect_is_rejected_before_request():
    def fetch(url, validator, max_bytes):
        validator(url.replace('ID+eq+88', 'ID+eq+89'))
        pytest.fail('changed identity was accepted')
    with pytest.raises(ValueError):
        acquire_detail(88, fetch, NOW)


@pytest.mark.parametrize('oversized', [False, True])
def test_driver_detail_hook_preserves_identity_check_and_size_bound(monkeypatch, oversized):
    from app.tenderproof.http_driver import BoundedHTTPDriver
    from app.tenderproof.contracts import DiscoveredCandidate
    candidate = DiscoveredCandidate(candidate_id='new-88', source='fumarc_open', external_id='88',
        detail_url_observed='https://www.fumarc.com.br/SitePages/Home.aspx?concurso=88', observed_at=NOW)
    checked = []
    def validate(url):
        assert url == candidate.detail_url_observed
    adapter = SimpleNamespace(validate_detail_url=validate, candidate_from_url=lambda url: candidate,
        acquire_detail=lambda url, selected, fetch: 'x' * (2 * 1024 * 1024 + 1) if oversized else 'verified',
        confirm_identity=lambda selected, body, url: checked.append((selected, body, url)))
    monkeypatch.setattr('app.tenderproof.http_driver.get_source_adapter', lambda source: adapter)
    driver = BoundedHTTPDriver('fumarc_open', client=SimpleNamespace())
    if oversized:
        with pytest.raises(ValueError):
            driver.open_detail(candidate.detail_url_observed)
        assert checked == []
    else:
        assert driver.open_detail(candidate.detail_url_observed) == 'verified'
        assert checked == [(candidate, 'verified', candidate.detail_url_observed)]
