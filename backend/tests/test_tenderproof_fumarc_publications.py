import json
from datetime import datetime, timezone
from urllib.parse import urlencode

import pytest

from app.tenderproof.fumarc_publications import (
    publication_url, parse_publications, downloadable_pdf,
)


def row(identity=1, contest=88):
    return {'Id': identity, 'ConcursoId': contest, 'Title': 'Edital',
            'TipoPublicacao': 'Arquivo', 'PermitirDownload': True,
            'Arquivo': {'Url': 'https://www.fumarc.com.br/Documentos%20Compartilhados/Novo/edital.pdf'}}


def body(rows, following=None):
    envelope = {'results': rows}
    if following is not None:
        envelope['__next'] = following
    return json.dumps({'d': envelope})


def cursor(url, identity):
    return url + '&' + urlencode({'$skiptoken': f'Paged=TRUE&p_DataInicioPublicacao=20260101%2000%3A00%3A00&p_ID={identity}'})


def test_pages_are_bound_to_dynamic_contest_and_observed_cursor():
    url = publication_url(88)
    following = cursor(url, 2)
    parsed = parse_publications(body([row(1), row(2)], following), url, 88)
    assert parsed.next_url == following
    assert len(parsed.rows) == 2
    assert parse_publications(body([]), following, 88).next_url is None
    assert downloadable_pdf(parsed.rows[0]).endswith('/Novo/edital.pdf')


@pytest.mark.parametrize('rows', [[row(contest=89)], [row(), row()], [dict(row(), ID=2)]])
def test_mixed_or_duplicate_identity_is_rejected(rows):
    with pytest.raises(ValueError):
        parse_publications(body(rows), publication_url(88), 88)


def test_next_cannot_change_contest_window_or_cursor_identity():
    url = publication_url(88, datetime(2026, 1, 1, tzinfo=timezone.utc))
    for following in (cursor(publication_url(89), 1), cursor(url, 2), cursor(url.replace('2026-01-01', '2026-02-01'), 1)):
        with pytest.raises(ValueError):
            parse_publications(body([row()], following), url, 88)
    following = cursor(url, 1)
    with pytest.raises(ValueError):
        parse_publications(body([row()], following), following, 88)


@pytest.mark.parametrize('permission', [False, None, 1, 'true'])
def test_download_requires_explicit_permission(permission):
    assert downloadable_pdf(dict(row(), PermitirDownload=permission)) is None


@pytest.mark.parametrize('url', [
    'https://www.fumarc.com.br/other/edital.pdf',
    'https://www.fumarc.com.br/Documentos%20Compartilhados/../edital.pdf',
    'https://www.fumarc.com.br/Documentos%20Compartilhados/edital.pdf?download=1',
    'http://www.fumarc.com.br/Documentos%20Compartilhados/edital.pdf',
])
def test_pdf_destination_cannot_leave_observed_library(url):
    with pytest.raises(ValueError):
        downloadable_pdf(dict(row(), Arquivo={'Url': url}))
