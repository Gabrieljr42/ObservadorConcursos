"""Bounded acquisition of a FUMARC contest and every observed publication page."""
import json
import re
from datetime import datetime, timezone
from urllib.parse import urlencode

from app.tenderproof.fumarc_api import HOST, PATH, SELECT
from app.tenderproof.fumarc_publications import publication_url, parse_publications, validate_publication_url
from app.tenderproof.security import validate_destination

MAX_BYTES = 2 * 1024 * 1024


def detail_api_url(contest_id, now):
    if not re.fullmatch(r'[1-9]\d*', str(contest_id)):
        raise ValueError('identidade FUMARC inválida')
    stamp = now.astimezone(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    query = {'$filter': f"ID eq {contest_id} and DataFimPublicacao ge datetime'{stamp}' and DataInicioPublicacao le datetime'{stamp}'",
             '$select': SELECT, '$expand': 'Realizador'}
    return f'https://{HOST}{PATH}?' + urlencode(query)


def acquire_detail(contest_id, fetch, now=None):
    """fetch is the driver's guarded, TLS/DNS/byte/deadline-limited transport."""
    now = now or datetime.now(timezone.utc)
    detail_url = detail_api_url(contest_id, now)

    def exact_detail(target):
        validate_destination(target, allowlist=(HOST,))
        if target != detail_url:
            raise ValueError('redirect altera recurso de detalhe FUMARC')

    response = fetch(detail_url, exact_detail, MAX_BYTES)
    content = response.content
    if len(content) > MAX_BYTES or response.url_final != detail_url:
        raise ValueError('resposta de detalhe fora do contrato')
    data = json.loads(content.decode('utf-8-sig'))
    envelope = data.get('d') if isinstance(data, dict) else None
    rows = envelope.get('results') if isinstance(envelope, dict) else None
    if (not isinstance(rows, list) or len(rows) != 1 or envelope.get('__next') is not None
            or not isinstance(rows[0], dict) or type(rows[0].get('Id')) is not int
            or rows[0]['Id'] != int(contest_id) or rows[0].get('ID', int(contest_id)) != int(contest_id)
            or not isinstance(rows[0].get('Title'), str) or not rows[0]['Title'].strip()):
        raise ValueError('detalhe não confirma concurso único publicado')
    resources = [{'url': detail_url, 'body': data}]
    size = len(content)
    url = publication_url(contest_id, now)
    visited, identities = set(), set()
    while url:
        if url in visited or len(visited) >= 100:
            raise ValueError('publicações incompletas: limite ou ciclo de paginação')
        visited.add(url)

        def exact_publication(target, expected=url):
            validate_publication_url(target, contest_id)
            if target != expected:
                raise ValueError('redirect altera recurso de publicações')

        response = fetch(url, exact_publication, MAX_BYTES)
        size += len(response.content)
        if size > MAX_BYTES or response.url_final != url:
            raise ValueError('detalhe agregado excede contrato')
        text = response.content.decode('utf-8-sig')
        page = parse_publications(text, url, contest_id)
        for row in page.rows:
            if row['Id'] in identities:
                raise ValueError('publicação duplicada entre páginas')
            identities.add(row['Id'])
        resources.append({'url': url, 'body': json.loads(text)})
        url = page.next_url
    result = json.dumps({'source': 'fumarc_open', 'contest_id': int(contest_id),
                         'resources': resources, 'publications_complete': True}, ensure_ascii=False)
    if len(result.encode('utf-8')) > MAX_BYTES:
        raise ValueError('detalhe composto excede limite')
    return result
