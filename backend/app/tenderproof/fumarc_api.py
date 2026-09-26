"""Observed public SharePoint listing contract; not yet a registered adapter."""
import json
import re
from datetime import datetime, timezone
from urllib.parse import parse_qs, urlencode, urlsplit

from app.tenderproof.contracts import DiscoveredCandidate
from app.tenderproof.security import validate_destination
from app.tenderproof.source_adapter_base import ListingPage

HOST = 'www.fumarc.com.br'
HOME = f'https://{HOST}/SitePages/Home.aspx'
PATH = "/_api/web/lists/getByTitle('Concursos')/items"
SELECT = ('Attachments,DataInicioInscricoes,DataFimInscricoes,DataInicioPublicacao,'
          'DataFimPublicacao,Descricao,Id,NumeroVagas,PermitirDownloadEdital,'
          'RealizadorId,Realizador/Title,Status,Title,Prioridade,Edital,LinkInscricoes,LinkResultado')
FIXED = {'$top': '9', '$orderby': 'Prioridade desc,DataInicioPublicacao desc',
         '$select': SELECT, '$expand': 'Realizador'}
DATE = r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z'


def listing_url(now=None):
    now = now or datetime.now(timezone.utc)
    timestamp = now.astimezone(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    query = {'$filter': f"DataFimPublicacao ge datetime'{timestamp}' and DataInicioPublicacao le datetime'{timestamp}' and Publicado ne 0", **FIXED}
    return f'https://{HOST}{PATH}?' + urlencode(query)


def validate_listing_url(url):
    validate_destination(url, allowlist=(HOST,))
    p = urlsplit(url)
    if p.scheme != 'https' or p.hostname != HOST or p.port not in (None, 443) or p.path != PATH or p.fragment:
        raise ValueError('destino fora da API pública FUMARC')
    query = parse_qs(p.query, keep_blank_values=True)
    required = {'$filter', *FIXED}
    if not required.issubset(query) or set(query) - required - {'$skiptoken'} or any(len(v) != 1 for v in query.values()):
        raise ValueError('parâmetros de listagem FUMARC inválidos')
    if any(query[k] != [v] for k, v in FIXED.items()):
        raise ValueError('consulta difere do contrato público FUMARC')
    match = re.fullmatch(rf"DataFimPublicacao ge datetime'({DATE})' and DataInicioPublicacao le datetime'\1' and Publicado ne 0", query['$filter'][0])
    if not match:
        raise ValueError('janela de publicação FUMARC inválida')
    datetime.strptime(match[1], '%Y-%m-%dT%H:%M:%SZ')
    if '$skiptoken' in query:
        token = parse_qs(query['$skiptoken'][0], keep_blank_values=True)
        if (set(token) != {'Paged', 'p_Prioridade', 'p_DataInicioPublicacao', 'p_ID'}
                or any(len(v) != 1 for v in token.values()) or token['Paged'] != ['TRUE']
                or not re.fullmatch(r'-?\d+(?:\.\d+)?', token['p_Prioridade'][0])
                or not re.fullmatch(r'[1-9]\d*', token['p_ID'][0])):
            raise ValueError('cursor de paginação FUMARC inválido')
        datetime.strptime(token['p_DataInicioPublicacao'][0], '%Y%m%d %H:%M:%S')
    return {k: v[0] for k, v in query.items()}


def parse_listing(body, url, limit=200):
    query = validate_listing_url(url)
    if not 1 <= limit <= 10000 or len(body.encode('utf-8')) > 2 * 1024 * 1024:
        raise ValueError('limite da listagem FUMARC excedido')
    data = json.loads(body)
    envelope = data.get('d') if isinstance(data, dict) else None
    rows = envelope.get('results') if isinstance(envelope, dict) else None
    if not isinstance(rows, list) or len(rows) > 9:
        raise ValueError('resposta não corresponde à listagem FUMARC')
    candidates, seen = [], set()
    for row in rows:
        if (not isinstance(row, dict) or type(row.get('Id')) is not int or row['Id'] <= 0
                or ('ID' in row and row['ID'] != row['Id'])
                or not isinstance(row.get('Title'), str) or not row['Title'].strip()
                or row['Id'] in seen):
            raise ValueError('identidade de candidato FUMARC ausente ou duplicada')
        seen.add(row['Id'])
        candidates.append(DiscoveredCandidate(candidate_id=f"fumarc_open-{row['Id']}",
            external_id=str(row['Id']), source='fumarc_open', title_observed=row['Title'].strip(),
            detail_url_observed=HOME + '?concurso=' + str(row['Id']), observed_at=datetime.now(timezone.utc)))
    next_url = envelope.get('__next')
    next_urls = []
    if next_url is not None:
        if not isinstance(next_url, str):
            raise ValueError('continuação FUMARC inválida')
        following = validate_listing_url(next_url)
        if ('$skiptoken' not in following or following.get('$skiptoken') == query.get('$skiptoken')
                or {k: v for k, v in following.items() if k != '$skiptoken'} !=
                   {k: v for k, v in query.items() if k != '$skiptoken'}):
            raise ValueError('continuação altera a consulta ou repete o cursor')
        cursor = parse_qs(following['$skiptoken'])
        if not rows or cursor['p_ID'] != [str(rows[-1]['Id'])]:
            raise ValueError('cursor não corresponde ao último candidato observado')
        next_urls = [next_url]
    truncated = len(candidates) > limit
    return ListingPage(candidates=candidates[:limit], next_urls=next_urls, truncated=truncated,
        empty_evidence='API FUMARC: results=[] sem continuação na janela publicada' if not rows and not next_urls else None,
        terminal_evidence='API FUMARC: página sem __next na janela publicada' if not next_urls and not truncated else None,
        diagnostics=['limite de candidatos da página atingido; cobertura parcial'] if truncated else [])
