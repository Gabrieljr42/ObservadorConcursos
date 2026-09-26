import json
from datetime import datetime, timezone
from urllib.parse import urlencode, parse_qs, urlsplit
import pytest
from app.tenderproof.fumarc_api import listing_url, validate_listing_url, parse_listing
from app.tenderproof.security import DestinationBlocked


def url():
    return listing_url(datetime(2026, 9, 8, tzinfo=timezone.utc))


def cursor_url(base, last_id=123):
    return base + '&' + urlencode({'$skiptoken':
        f'Paged=TRUE&p_Prioridade=1.000&p_DataInicioPublicacao=20260801%2011%3A00%3A00&p_ID={last_id}'})


def body(next_url=None, rows=None):
    data = {'results': rows if rows is not None else [{'Id':123,'ID':123,'Title':'Concurso Público Novo'}]}
    if next_url is not None: data['__next'] = next_url
    return json.dumps({'d':data})


def test_dynamic_date_candidate_and_observed_pagination():
    first = url()
    other = listing_url(datetime(2027, 1, 1, tzinfo=timezone.utc))
    assert first != other
    page = parse_listing(body(cursor_url(first)), first)
    assert page.candidates[0].external_id == '123'
    assert page.candidates[0].detail_url_observed.endswith('?concurso=123')
    assert page.next_urls == [cursor_url(first)] and not page.terminal_evidence
    assert parse_listing(body(), cursor_url(first)).terminal_evidence


@pytest.mark.parametrize('mutation', [
    lambda u: u.replace('www.fumarc.com.br', 'evil.test'),
    lambda u: u.replace('https:', 'http:'),
    lambda u: u + '&%24top=9',
    lambda u: u + '&extra=value',
    lambda u: u.replace('Publicado+ne+0', 'Publicado+eq+0'),
    lambda u: u.replace('2026-09-08', '2026-19-08'),
    lambda u: u + '#ignored',
])
def test_changed_public_contract_is_rejected(mutation):
    with pytest.raises((ValueError, DestinationBlocked)): validate_listing_url(mutation(url()))


def test_continuation_cannot_change_window_repeat_or_skip_last_identity():
    first = url()
    next_url = cursor_url(first)
    for following in (next_url.replace('2026-09-08', '2026-09-09'), cursor_url(first,999)):
        with pytest.raises(ValueError): parse_listing(body(following), first)
    with pytest.raises(ValueError): parse_listing(body(next_url),next_url)


def test_empty_truncation_and_duplicate_identity():
    empty = parse_listing(body(rows=[]),url())
    assert empty.empty_evidence and empty.terminal_evidence
    rows = [{'Id':i,'Title':f'Seleção {i}'} for i in (1,2)]
    limited = parse_listing(body(rows=rows),url(),limit=1)
    assert limited.truncated and not limited.terminal_evidence
    with pytest.raises(ValueError): parse_listing(body(rows=[rows[0],rows[0]]),url())
    with pytest.raises(ValueError): parse_listing(body(rows=[{'Id':1,'ID':2,'Title':'Wrong'}]),url())
    with pytest.raises(ValueError): parse_listing('<html>Login</html>',url())
