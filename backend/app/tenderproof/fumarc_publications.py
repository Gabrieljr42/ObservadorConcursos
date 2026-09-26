"""Public publication pages, strictly bound to the requested FUMARC contest."""
import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from urllib.parse import parse_qs, urlencode, urlsplit, unquote

from app.tenderproof.fumarc_api import HOST, DATE
from app.tenderproof.security import validate_destination

PATH = "/_api/web/lists/getByTitle('ConcursoPublicacoes')/items"
SELECT = ('Attachments,ConcursoId,DataFimPublicacao,DataInicioPublicacao,Descricao,'
          'Link/URL,Link/Description,DestacarAtualizacao,Id,SecaoId,Secao/Title,'
          'Secao/Id,Secao/Ordenacao,TipoPublicacao,Title,Created,PermitirDownload,'
          'Arquivo/URL,Arquivo/Description')
FIXED = {'$top': '10', '$orderby': 'DataInicioPublicacao desc', '$select': SELECT, '$expand': 'Secao'}


def publication_url(contest_id, now=None):
    if not re.fullmatch(r'[1-9]\d*', str(contest_id)):
        raise ValueError('identidade FUMARC inválida')
    stamp = (now or datetime.now(timezone.utc)).astimezone(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    query = {'$filter': f"ConcursoId eq {contest_id} and DataInicioPublicacao le datetime'{stamp}' and (DataFimPublicacao ge datetime'{stamp}' or DataFimPublicacao eq null)", **FIXED}
    return f'https://{HOST}{PATH}?' + urlencode(query)


def validate_publication_url(url, contest_id):
    if not re.fullmatch(r'[1-9]\d*', str(contest_id)):
        raise ValueError('identidade FUMARC inválida')
    validate_destination(url, allowlist=(HOST,))
    parts = urlsplit(url)
    if parts.scheme != 'https' or parts.hostname != HOST or parts.port not in (None, 443) or parts.path != PATH or parts.fragment:
        raise ValueError('destino fora da API de publicações FUMARC')
    query = parse_qs(parts.query, keep_blank_values=True)
    if set(query) - {*FIXED, '$filter', '$skiptoken'} or not {*FIXED, '$filter'}.issubset(query) or any(len(v) != 1 for v in query.values()):
        raise ValueError('parâmetros de publicações inválidos')
    if any(query[k] != [v] for k, v in FIXED.items()):
        raise ValueError('consulta de publicações fora do contrato')
    match = re.fullmatch(rf"ConcursoId eq {contest_id} and DataInicioPublicacao le datetime'({DATE})' and \(DataFimPublicacao ge datetime'\1' or DataFimPublicacao eq null\)", query['$filter'][0])
    if not match:
        raise ValueError('publicações de outro concurso ou janela inválida')
    datetime.strptime(match[1], '%Y-%m-%dT%H:%M:%SZ')
    if '$skiptoken' in query:
        cursor = parse_qs(query['$skiptoken'][0], keep_blank_values=True)
        if (set(cursor) != {'Paged', 'p_DataInicioPublicacao', 'p_ID'}
                or any(len(v) != 1 for v in cursor.values()) or cursor['Paged'] != ['TRUE']
                or not re.fullmatch(r'[1-9]\d*', cursor['p_ID'][0])):
            raise ValueError('cursor de publicações inválido')
        datetime.strptime(cursor['p_DataInicioPublicacao'][0], '%Y%m%d %H:%M:%S')
    return {k: v[0] for k, v in query.items()}


@dataclass
class PublicationPage:
    rows: list[dict]
    next_url: str | None


def parse_publications(body, url, contest_id):
    query = validate_publication_url(url, contest_id)
    if len(body.encode('utf-8')) > 2 * 1024 * 1024:
        raise ValueError('página de publicações excede limite')
    data = json.loads(body)
    envelope = data.get('d') if isinstance(data, dict) else None
    rows = envelope.get('results') if isinstance(envelope, dict) else None
    if not isinstance(rows, list) or len(rows) > 10:
        raise ValueError('resposta não corresponde a publicações FUMARC')
    seen = set()
    for row in rows:
        if (not isinstance(row, dict) or type(row.get('Id')) is not int or row['Id'] <= 0
                or row['Id'] in seen or ('ID' in row and row['ID'] != row['Id'])
                or type(row.get('ConcursoId')) is not int or row['ConcursoId'] != int(contest_id)
                or not isinstance(row.get('Title'), str) or not row['Title'].strip()):
            raise ValueError('publicação sem identidade única associada ao concurso')
        seen.add(row['Id'])
    following = envelope.get('__next')
    if following is not None:
        if not isinstance(following, str):
            raise ValueError('continuação de publicações inválida')
        next_query = validate_publication_url(following, contest_id)
        if (not rows or '$skiptoken' not in next_query
                or next_query.get('$skiptoken') == query.get('$skiptoken')
                or {k:v for k,v in next_query.items() if k != '$skiptoken'} != {k:v for k,v in query.items() if k != '$skiptoken'}
                or parse_qs(next_query['$skiptoken'])['p_ID'] != [str(rows[-1]['Id'])]):
            raise ValueError('continuação altera consulta ou último documento')
    return PublicationPage(rows=rows, next_url=following)


def downloadable_pdf(row):
    """Return only a public PDF explicitly permitted by its associated row."""
    if row.get('TipoPublicacao') != 'Arquivo' or row.get('PermitirDownload') is not True:
        return None
    file = row.get('Arquivo')
    if not isinstance(file, dict) or not isinstance(file.get('Url'), str):
        return None
    url = file['Url']
    validate_destination(url, allowlist=(HOST,))
    parts = urlsplit(url)
    path = unquote(parts.path)
    if (parts.scheme != 'https' or parts.hostname != HOST or parts.port not in (None, 443)
            or parts.query or parts.fragment or not path.startswith('/Documentos Compartilhados/')
            or any(segment in ('.', '..') for segment in path.split('/')) or '\\' in path
            or not path.lower().endswith('.pdf')):
        raise ValueError('arquivo fora da biblioteca pública PDF FUMARC')
    return url
