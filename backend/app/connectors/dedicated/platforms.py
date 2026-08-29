"""Dedicated connectors for platforms that do not expose a normal banca page.

The ELO portal is a JSON application (the public page only bootstraps the
frontend), while RBO is an HTML portal.  Keeping both implementations here
prevents the generic HTML connector from silently accepting navigation cards
or losing the document links exposed by these portals.
"""

from __future__ import annotations

import re
from datetime import UTC, datetime, time
from decimal import Decimal
from typing import Any, Iterable
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

from app.connectors.base import BaseConnector, CandidateItem
from app.connectors.common import (
    build_hash,
    build_summary,
    classify_area_from_many,
    clean,
    extract_city_uf,
    extract_external_id,
    extract_pdf_fields_if_possible,
    extract_pdf_link,
    normalize_url,
    parse_date_interval,
    parse_money,
    status_from_dates,
    text_lines,
)
from app.publications import (
    build_publication_hash,
    normalize_publication_type,
    parse_publications_from_dom,
    parse_publications_from_lines,
)


def _first(data: dict[str, Any], *keys: str) -> Any:
    """Read API fields tolerating camelCase/snake_case and case changes."""
    if not isinstance(data, dict):
        return None
    for key in keys:
        if key in data and data[key] not in (None, ''):
            return data[key]
    lowered = {str(key).replace('_', '').lower(): value for key, value in data.items()}
    for key in keys:
        value = lowered.get(key.replace('_', '').lower())
        if value not in (None, ''):
            return value
    return None


def _unwrap(value: Any) -> Any:
    if isinstance(value, dict):
        for key in ('data', 'content', 'result', 'edital', 'item'):
            nested = _first(value, key)
            if isinstance(nested, (dict, list)):
                return nested
    return value


def _as_text(value: Any) -> str | None:
    if isinstance(value, dict):
        return clean(_first(value, 'nome', 'name', 'descricao', 'description', 'titulo', 'title', 'valor', 'value'))
    if isinstance(value, (list, tuple, set)):
        values = [_as_text(item) for item in value]
        return clean(' | '.join(item for item in values if item))
    return clean(str(value)) if value not in (None, '') else None


def _date(value: Any, *, end_of_day: bool = False) -> datetime | None:
    text = _as_text(value)
    if not text:
        return None
    try:
        parsed = datetime.fromisoformat(text.replace('Z', '+00:00'))
    except ValueError:
        parsed = None
    if parsed is None:
        parsed = _date_from_visible(text)
    if parsed is None:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    else:
        parsed = parsed.astimezone(UTC)
    if end_of_day and parsed.time() == time.min:
        parsed = parsed.replace(hour=23, minute=59, second=59)
    return parsed


def _date_from_visible(text: str) -> datetime | None:
    match = re.search(r'(\d{1,2})/(\d{1,2})/(\d{2,4})', text)
    if not match:
        return None
    year = int(match.group(3))
    year += 2000 if year < 100 else 0
    try:
        return datetime(year, int(match.group(2)), int(match.group(1)), tzinfo=UTC)
    except ValueError:
        return None


def _iter_dicts(value: Any) -> Iterable[dict[str, Any]]:
    if isinstance(value, list):
        yield from (item for item in value if isinstance(item, dict))
    elif isinstance(value, dict):
        nested = _unwrap(value)
        if nested is not value:
            yield from _iter_dicts(nested)


def _documents(data: dict[str, Any]) -> list[dict[str, Any]]:
    for key in ('documentos', 'publicacoes', 'publicações', 'arquivos', 'anexos', 'documentosPublicados'):
        value = _first(data, key)
        if isinstance(value, list):
            rows = [item if isinstance(item, dict) else {'url': item} for item in value if isinstance(item, (dict, str))]
        else:
            rows = list(_iter_dicts(value))
        if rows:
            return rows
    return []


def _document_url(document: dict[str, Any]) -> str | None:
    value = _first(document, 'url', 'link', 'arquivo', 'urlArquivo', 'downloadUrl', 'documentoUrl', 'caminho', 'href')
    if isinstance(value, dict):
        value = _first(value, 'url', 'link', 'href')
    return clean(value)


def _document_title(document: dict[str, Any]) -> str:
    return _as_text(_first(document, 'descricao', 'description', 'titulo', 'title', 'nome', 'name', 'tipo', 'type')) or 'Documento oficial'


def _document_date(document: dict[str, Any]) -> str | None:
    value = _first(document, 'dataPublicacao', 'publicationDate', 'data', 'date', 'createdAt', 'publishedAt')
    parsed = _date(value)
    return parsed.date().isoformat() if parsed else None


def _publication_rows(documents: list[dict[str, Any]], *, source: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for document in documents:
        link = _document_url(document)
        if not link or link in seen:
            continue
        seen.add(link)
        title = _document_title(document)
        pub_type = normalize_publication_type(title)
        date = _document_date(document)
        rows.append({
            'title': title,
            'publication_type': pub_type,
            'publication_date': date,
            'link': link,
            'content_hash': build_publication_hash(title, date, link, pub_type),
            'source': source,
        })
    return rows[:80]


def _record_rejection(connector: BaseConnector, url: str, reason: str) -> None:
    """Record a quality-gate rejection without relying on a subclass method."""
    rows = connector.run_data.diagnostics_payload.setdefault('rejections', [])
    if len(rows) < 20:
        rows.append({'url': url, 'reason': reason})


class EloOpenConnector(BaseConnector):
    """ELO Assessoria public editais API, scoped to the ELO tenant."""

    banca = 'Elo Assessoria'
    mode = 'open'
    max_candidates = 100
    api_url = 'https://api.gestaoselecoes.com.br/api/editais'
    tenant_id = 'eloassessoria'
    frontend_url = 'https://eloassessoriaeservicos.com.br'

    def __init__(self, base_url: str = frontend_url, list_url: str | None = None):
        canonical = (base_url or self.frontend_url).rstrip('/')
        super().__init__(canonical, list_url or f'{canonical}/concursos')

    def _api_headers(self) -> dict[str, str]:
        return {'X-TenantID': self.tenant_id, 'Accept': 'application/json'}

    def _fetch_html(self, url: str, *, reason: str | None = None) -> str:
        """ELO detail pages are rendered by the SPA; detail data is REST JSON.

        BaseConnector still invokes this hook for every candidate.  Returning
        an empty document avoids turning a perfectly healthy API response into
        a rejection when a frontend route is changed, while the API detail and
        document calls below remain authoritative.
        """
        return ''

    @staticmethod
    def _list_items(payload: Any) -> list[dict[str, Any]]:
        if isinstance(payload, list):
            return [item for item in payload if isinstance(item, dict)]
        if not isinstance(payload, dict):
            return []
        for key in ('content', 'items', 'editais', 'results', 'data'):
            value = _first(payload, key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
            if isinstance(value, dict):
                nested = EloOpenConnector._list_items(value)
                if nested:
                    return nested
        return []

    def _fetch_candidates(self) -> list[CandidateItem]:
        params = {
            'page': 0,
            'size': self.max_candidates,
            'situacao': 'PUBLICADO,INSCRICAO_ABERTA,ANDAMENTO',
            'order': 'DESC',
        }
        with self._http_client() as client:
            response = client.get(self.api_url, params=params, headers=self._api_headers())
            self.run_data.http_status = response.status_code
            response.raise_for_status()
            payload = response.json()
        items = self._list_items(payload)
        self.run_data.diagnostics_payload.update({
            'api': self.api_url,
            'tenant': self.tenant_id,
            'api_params': params,
            'api_total': _first(payload, 'totalElements', 'total', 'count') if isinstance(payload, dict) else len(items),
            'api_ids': [str(_first(item, 'id', 'codigo', 'externalId')) for item in items],
        })
        candidates: list[CandidateItem] = []
        for item in items:
            external_id = _first(item, 'id', 'codigo', 'externalId', 'external_id')
            if external_id is None:
                continue
            title = _as_text(_first(item, 'titulo', 'title', 'nome', 'descricao', 'descricaoEdital'))
            status = _as_text(_first(item, 'situacao', 'status', 'estado'))
            candidates.append(CandidateItem(
                title_hint=title,
                detail_url=f'{self.base_url}/concurso/{external_id}',
                external_id=str(external_id),
                status_hint=status,
                extra={'api_list_item': item},
            ))
        return candidates

    def _fetch_api_detail(self, candidate: CandidateItem, client: httpx.Client) -> dict[str, Any]:
        client.headers.update(self._api_headers())
        response = client.get(f'{self.api_url}/{candidate.external_id}', headers=self._api_headers())
        if response.status_code == 404:
            # Some deployments use /detalhes; accept it without hardcoding any
            # certame identifier and retain the list record as a last resort.
            alternate = client.get(f'{self.api_url}/{candidate.external_id}/detalhes', headers=self._api_headers())
            if alternate.status_code < 400:
                response = alternate
        response.raise_for_status()
        value = _unwrap(response.json())
        return value if isinstance(value, dict) else {}

    def _fetch_documents(self, candidate: CandidateItem, client: httpx.Client) -> list[dict[str, Any]]:
        response = client.get(f'{self.api_url}/{candidate.external_id}/documentos', headers=self._api_headers())
        if response.status_code >= 400:
            return []
        payload = response.json()
        rows = _documents(payload) if isinstance(payload, dict) else _documents({'documentos': _unwrap(payload)})
        return rows

    def _fetch_frontend_detail(self, candidate: CandidateItem, client: httpx.Client) -> BeautifulSoup:
        """Fetch the SSR detail page used by the public ELO frontend.

        The documented-looking ``/documentos`` route currently responds 500;
        the server-rendered detail route contains the exact visible document,
        cargo, fee and link values instead.
        """
        response = client.get(
            candidate.detail_url,
            headers={'Accept': 'text/html,application/xhtml+xml', 'X-TenantID': self.tenant_id},
        )
        if response.status_code >= 400:
            return BeautifulSoup('', 'lxml')
        return BeautifulSoup(self._response_text(response), 'lxml')

    @staticmethod
    def _status(raw: str | None, start: datetime | None, end: datetime | None) -> str | None:
        status = status_from_dates(start, end)
        if status:
            return status
        normalized = (raw or '').lower()
        if 'aberta' in normalized or 'inscricao_aberta' in normalized or 'inscrição aberta' in normalized:
            return 'Inscrições abertas'
        if 'andamento' in normalized:
            return 'Em andamento'
        if 'publicado' in normalized or 'breve' in normalized:
            return 'Inscrições em breve'
        return raw

    @staticmethod
    def _field_text(data: dict[str, Any], *keys: str) -> str:
        value = _first(data, *keys)
        return _as_text(value) or ''

    @staticmethod
    def _roles(data: dict[str, Any]) -> list[str]:
        value = _first(data, 'cargos', 'funcoes', 'funções', 'vagas', 'positions')
        if isinstance(value, list):
            roles = []
            for item in value:
                role = _as_text(_first(item, 'cargo', 'nome', 'descricao', 'title') if isinstance(item, dict) else item)
                if role and role not in roles:
                    roles.append(role)
            return roles
        role = _as_text(value)
        return [role] if role else []

    @staticmethod
    def _number(value: Any) -> int | None:
        if isinstance(value, (int, float)):
            return int(value)
        text = _as_text(value)
        if not text:
            return None
        match = re.search(r'\d[\d.]*', text)
        if not match:
            return None
        try:
            return int(match.group(0).replace('.', ''))
        except ValueError:
            return None

    def _parse_detail(self, candidate: CandidateItem, html: str, *, client: httpx.Client) -> dict[str, Any] | None:
        list_item = candidate.extra.get('api_list_item') if isinstance(candidate.extra, dict) else {}
        data = self._fetch_api_detail(candidate, client)
        if not data:
            data = list_item if isinstance(list_item, dict) else {}
        documents = _documents(data)
        frontend_soup = self._fetch_frontend_detail(candidate, client)
        frontend_lines = text_lines(frontend_soup)
        if not documents:
            publications = parse_publications_from_dom(frontend_soup, candidate.detail_url, source='elo_assessoria')
            documents = [
                {'descricao': row['title'], 'arquivo': row['link'], 'dataPublicacao': row.get('publication_date')}
                for row in publications if row.get('link')
            ]
        # Keep the API route as a supplementary source only.  It currently
        # returns 500 in production, so a failure here must never reject the
        # certame or replace the SSR documents already collected above.
        if not documents:
            documents = self._fetch_documents(candidate, client)

        title = self._field_text(data, 'titulo', 'title', 'nome', 'descricaoEdital') or candidate.title_hint
        # The real API calls the public-facing organization description
        # ``descricao``.  Combine it with the API's type/number so the stored
        # title remains a certame title rather than a bare organization name.
        description = self._field_text(data, 'descricao', 'description')
        tipo = self._field_text(data, 'tipo', 'modalidade')
        numero = self._field_text(data, 'numero', 'editalNumero')
        ano = self._field_text(data, 'ano')
        if not title or title == description:
            title = ' - '.join(part for part in (tipo, f'{numero}/{ano}' if numero and ano else numero, description) if part)
        if not title:
            return None
        orgao_value = _first(data, 'orgao', 'entidade', 'contratante', 'prefeitura', 'municipio')
        orgao = _as_text(orgao_value) or self._field_text(data, 'orgaoNome', 'nomeOrgao', 'nomeOrgaoSolicitante', 'entidadeNome')
        location = self._field_text(data, 'local', 'localidade', 'cidade', 'municipio', 'endereco')
        uf = self._field_text(data, 'uf', 'estado', 'siglaUf') or None
        cidade, parsed_uf = extract_city_uf(f'{location} {title} {orgao}')
        if not cidade and orgao:
            m_city = re.search(r'(?:prefeitura|município|câmara|pm|cm)\s+(?:municipal\s+)?(?:de|do|da)?\s*([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ ]{2,50})', orgao, re.I)
            if m_city:
                cidade = clean(m_city.group(1).title())
        cidade = cidade or location or None
        uf = (parsed_uf or uf or 'MG').upper() or 'MG'

        start = _date(_first(data, 'inicioInscricao', 'inscricaoInicio', 'dataInicioInscricao', 'dataInicioInscricoes', 'inicio'))
        end = _date(_first(data, 'fimInscricao', 'inscricaoFim', 'dataFimInscricao', 'dataTerminoInscricoes', 'fim'), end_of_day=True)
        if not start or not end:
            visible_start, visible_end = parse_date_interval(' '.join([title, description, location]))
            start, end = start or visible_start, end or visible_end
        raw_status = self._field_text(data, 'situacao', 'status', 'estado') or candidate.status_hint
        status = self._status(raw_status, start, end)
        roles = self._roles(data)
        if not roles:
            for heading in frontend_soup.select('h4'):
                role = clean(heading.get_text(' ', strip=True))
                if role and role not in roles and len(role) <= 160:
                    roles.append(role)
        cargo = self._field_text(data, 'cargo', 'funcao', 'funcão') or ('Vários cargos' if len(roles) > 1 else (roles[0] if roles else None))
        vagas = self._number(_first(data, 'quantidadeVagas', 'numeroVagas', 'totalVagas', 'vagas'))
        if vagas is None:
            vagas = sum(self._number(_first(data, key)) or 0 for key in (
                'totalVagasAmplaConcorrencia', 'totalVagasPcd', 'totalVagasPpp')) or None
        if vagas is None and isinstance(_first(data, 'vagas'), list):
            vagas = sum(self._number(_first(item, 'quantidade', 'qtde', 'vagas')) or 0 for item in _first(data, 'vagas')) or None
        if vagas is None:
            role_rows = _first(data, 'cargos', 'funcoes', 'funções', 'positions')
            if isinstance(role_rows, list):
                vagas = sum(self._number(_first(item, 'quantidade', 'qtde', 'vagas', 'numeroVagas')) or 0 for item in role_rows if isinstance(item, dict)) or None
        salary_values = []
        for key in ('salario', 'remuneracao', 'remuneração', 'salarioMin', 'salarioMax', 'vencimento'):
            value = _first(data, key)
            parsed = parse_money(_as_text(value))
            if parsed is not None:
                salary_values.append(parsed)
        salary_min = min(salary_values) if salary_values else None
        salary_max = max(salary_values) if salary_values else None
        taxa = parse_money(_as_text(_first(data, 'taxa', 'taxaInscricao', 'valorInscricao')))
        if taxa is None:
            fees = [parse_money(match.group(0)) for match in re.finditer(r'R\$\s*[\d.]+,\d{2}', '\n'.join(frontend_lines))]
            fees = [fee for fee in fees if fee is not None and fee >= 0]
            taxa = min(fees) if fees else None
        frontend_salaries = []
        for match in re.finditer(r'R\$\s*[\d.]+,\d{2}', '\n'.join(frontend_lines)):
            context = '\n'.join(frontend_lines)[max(0, match.start() - 80):match.end() + 80].lower()
            if any(token in context for token in ('salário', 'salario', 'remuneração', 'remuneracao', 'vencimento')):
                value = parse_money(match.group(0))
                if value is not None:
                    frontend_salaries.append(value)
        if frontend_salaries:
            salary_min = min(salary_min, min(frontend_salaries)) if salary_min is not None else min(frontend_salaries)
            salary_max = max(salary_max, max(frontend_salaries)) if salary_max is not None else max(frontend_salaries)

        edital_url = None
        for document in documents:
            link = _document_url(document)
            if link and 'edital' in _document_title(document).lower():
                edital_url = link
                break
        publications = _publication_rows(documents, source='elo_assessoria_api')
        pdf_payload, pdf_fields, excerpt, pdf_at = extract_pdf_fields_if_possible(
            edital_url, title=title, orgao=orgao, client=client,
        )
        cargo = cargo or (pdf_fields or {}).get('cargo')
        vagas = vagas if vagas is not None else (pdf_fields or {}).get('vagas')
        salary_min = salary_min or (pdf_fields or {}).get('salario_min')
        salary_max = salary_max or (pdf_fields or {}).get('salario_max')
        taxa = taxa if taxa is not None else (pdf_fields or {}).get('taxa')
        area = classify_area_from_many(roles, cargo, title, orgao, description)
        if not self._is_valid_certame(title, orgao, cidade, uf, start, end, edital_url, roles, description):
            _record_rejection(self, candidate.detail_url, 'quality_gate')
            return None
        raw_payload = {'api': data, 'api_list_item': list_item, 'publications': publications, 'pdf': pdf_payload, 'source_list_url': self.list_url}
        resumo = build_summary(title, 'Processo Seletivo' if 'processo' in title.lower() else 'Concurso', status, start, end, cargo=cargo, area=area, vagas=vagas, salario_min=salary_min, salario_max=salary_max)
        return {
            'external_id': str(_first(data, 'id', 'codigo', 'externalId') or candidate.external_id),
            'banca': self.banca,
            'orgao': orgao,
            'titulo': title,
            'modalidade': self._field_text(data, 'tipo', 'modalidade') or ('Processo Seletivo' if 'processo' in title.lower() else 'Concurso Público'),
            'cargo': cargo,
            'area': area,
            # Do not promote incidental municipalities mentioned in an edital
            # (for example the banca's office address) to the contest location.
            # ELO's API does not expose a location field for all records.
            'cidade': cidade,
            'uf': uf,
            'status': status,
            'vagas': vagas,
            'salario_min': salary_min,
            'salario_max': salary_max,
            'escolaridade': (pdf_fields or {}).get('escolaridade') or self._field_text(data, 'escolaridade', 'nivelEscolaridade') or None,
            'taxa': taxa,
            'prova_data': (pdf_fields or {}).get('prova_data') or _date(_first(data, 'dataProva', 'provaData')),
            'edital_numero': self._field_text(data, 'editalNumero', 'numeroEdital') or ('/'.join(part for part in (self._field_text(data, 'numero'), self._field_text(data, 'ano')) if part) or None),
            'edital_data': _date(_first(data, 'editalData', 'dataEdital')),
            'inscricao_inicio': start,
            'inscricao_fim': end,
            'link_pagina': candidate.detail_url,
            'link_edital': edital_url,
            'link_inscricao': self._field_text(data, 'linkInscricao', 'inscricaoUrl', 'urlInscricao') or next((normalize_url(candidate.detail_url, anchor.get('href')) for anchor in frontend_soup.select('a[href]') if 'inscri' in (anchor.get_text(' ', strip=True) or '').lower()), None),
            'resumo': resumo,
            'raw_data': raw_payload,
            'edital_pdf_text_hash': pdf_payload.get('text_hash'),
            'edital_pdf_pages': pdf_payload.get('pages'),
            'edital_pdf_excerpt': excerpt,
            'pdf_extracted_at': pdf_at,
            'content_hash': build_hash(raw_payload),
            'fetched_at': datetime.now(UTC),
        }


class RBOOpenConnector(BaseConnector):
    """RBO's canonical public open-contests portal."""

    banca = 'RBO Assessoria'
    mode = 'open'
    max_candidates = 100

    def __init__(self, base_url: str = 'https://rboconcursos.selecao.net.br', list_url: str | None = None):
        super().__init__(base_url.rstrip('/'), list_url or f'{base_url.rstrip("/")}/index/abertos/')

    def _fetch_candidates(self) -> list[CandidateItem]:
        html = self._fetch_html(self.list_url)
        soup = BeautifulSoup(html, 'lxml')
        candidates: list[CandidateItem] = []
        seen: set[str] = set()
        for anchor in soup.select('a[href]'):
            url = normalize_url(self.list_url, anchor.get('href'))
            if not url or not re.search(r'/informacoes/[^/?#]+/?$', url, flags=re.IGNORECASE):
                continue
            if url.rstrip('/') in seen:
                continue
            parent = anchor
            nearby = ''
            for _ in range(4):
                parent = parent.parent if parent else None
                if parent:
                    nearby = clean(parent.get_text(' ', strip=True)) or ''
                    if len(nearby) > len(anchor.get_text(' ', strip=True)) + 20:
                        break
            title = clean(anchor.get_text(' ', strip=True)) or nearby
            if not any(token in f'{title} {nearby}'.lower() for token in ('concurso', 'processo seletivo', 'edital')):
                continue
            seen.add(url.rstrip('/'))
            candidates.append(CandidateItem(title_hint=title, detail_url=url, external_id=extract_external_id(url, [r'/informacoes/(\d+)']), extra={'list_text': nearby}))
            if len(candidates) >= self.max_candidates:
                break
        self.run_data.diagnostics_payload.update({'list_url': self.list_url, 'candidate_urls': [item.detail_url for item in candidates]})
        return candidates

    @staticmethod
    def _title(soup: BeautifulSoup, candidate: CandidateItem) -> str:
        for selector in ('h1', 'h2', '.titulo', '.title', 'main header'):
            node = soup.select_one(selector)
            value = clean(node.get_text(' ', strip=True)) if node else None
            if value and value.lower() not in {'concurso', 'concursos', 'informações gerais', 'informacoes gerais'} and any(word in value.lower() for word in ('concurso', 'processo seletivo', 'edital')) and (len(value) >= 20 or ' - ' in value):
                return value
        lines = text_lines(soup)
        for line in lines:
            if any(word in line.lower() for word in ('concurso', 'processo seletivo')) and len(line) > 12 and (' - ' in line or re.search(r'\b\d{1,4}/\d{4}\b', line)):
                return line
        return candidate.title_hint or 'Concurso RBO'

    @staticmethod
    def _organization(title: str) -> str | None:
        match = re.search(
            r'(?:concurso\s+público|processo\s+seletivo)\s*[-–]\s*[^-–]+\s*[-–]\s*(.+)$',
            title,
            flags=re.IGNORECASE,
        )
        if not match:
            return None
        value = clean(match.group(1))
        # RBO uses "Jahu- SP" for a locality, but acronyms such as
        # "SEBRAE-SP" are part of the organization's official name.
        return clean(re.sub(r'-\s+[A-Z]{2}\s*$', '', value or ''))

    @staticmethod
    def _vagas(soup: BeautifulSoup, text: str) -> tuple[list[str], int | None]:
        roles: list[str] = []
        total = 0
        for row in soup.select('tr'):
            cells = [clean(cell.get_text(' ', strip=True)) for cell in row.select('th,td')]
            cells = [cell for cell in cells if cell]
            if len(cells) < 2 or cells[0].lower() in {'vaga', 'vagas'}:
                continue
            qty = re.search(r'\d+', cells[-1] or '')
            if not qty or not re.search(r'[A-Za-zÀ-ÿ]', cells[0] or ''):
                continue
            roles.append(cells[0])
            total += int(qty.group(0))
        if not roles:
            section = text.split('Vagas', 1)[-1] if 'Vagas' in text else text
            for match in re.finditer(r'([^\n|]{3,100})\s+(\d{1,4})\b', section):
                role = clean(match.group(1))
                if role and role.lower() not in {'vaga', 'qtde.', 'qtde'} and 'informações' not in role.lower():
                    roles.append(role)
                    total += int(match.group(2))
        return roles, total or None

    def _parse_detail(self, candidate: CandidateItem, html: str, *, client: httpx.Client) -> dict[str, Any] | None:
        soup = BeautifulSoup(html, 'lxml')
        lines = text_lines(soup)
        text = '\n'.join(lines)
        title = self._title(soup, candidate)
        orgao = self._organization(title)
        cidade, uf = extract_city_uf(title)
        if cidade:
            cidade = re.sub(r'^(?:Estância|Estancia)\s+Turística\s+de\s+', '', cidade, flags=re.IGNORECASE)
        if not uf:
            match = re.search(r'\b([A-Z]{2})\b', title)
            uf = match.group(1) if match else None
        start, end = parse_date_interval(text)
        explicit_status = next((line for line in lines if line.lower().startswith('situação') or line.lower().startswith('situacao')), None)
        status = status_from_dates(start, end, fallback=clean(explicit_status.split(':', 1)[-1]) if explicit_status and ':' in explicit_status else None)
        roles, vagas = self._vagas(soup, text)
        edital_url = extract_pdf_link(soup, candidate.detail_url)
        publications = parse_publications_from_dom(soup, candidate.detail_url, source='rbo')
        if not publications:
            publications = parse_publications_from_lines(lines, source='rbo')
        if not edital_url:
            for publication in publications:
                if publication.get('publication_type') == 'edital' and publication.get('link'):
                    edital_url = publication['link']
                    break
        if not self._is_valid_certame(title, orgao, cidade, uf, start, end, edital_url, roles, text):
            _record_rejection(self, candidate.detail_url, 'quality_gate')
            return None
        pdf_payload, pdf_fields, excerpt, pdf_at = extract_pdf_fields_if_possible(edital_url, title=title, orgao=orgao, client=client)
        cargo = 'Vários cargos' if len(roles) > 1 else (roles[0] if roles else None)
        cargo = cargo or (pdf_fields or {}).get('cargo')
        area = classify_area_from_many(roles, title, orgao, text[:3000])
        raw_payload = {'detail_url': candidate.detail_url, 'lines': lines[:200], 'publications': publications, 'pdf': pdf_payload, 'source_list_url': self.list_url}
        resumo = build_summary(title, 'Processo Seletivo' if 'processo seletivo' in title.lower() else 'Concurso Público', status, start, end, cargo=cargo, area=area, vagas=vagas)
        return {
            'external_id': candidate.external_id or extract_external_id(candidate.detail_url, [r'/informacoes/(\d+)']),
            'banca': self.banca,
            'orgao': orgao,
            'titulo': title,
            'modalidade': 'Processo Seletivo' if 'processo seletivo' in title.lower() else 'Concurso Público',
            'cargo': cargo,
            'area': area,
            'cidade': cidade,
            'uf': uf,
            'status': status,
            'vagas': vagas,
            'salario_min': (pdf_fields or {}).get('salario_min'),
            'salario_max': (pdf_fields or {}).get('salario_max'),
            'escolaridade': (pdf_fields or {}).get('escolaridade'),
            'taxa': (pdf_fields or {}).get('taxa'),
            'prova_data': (pdf_fields or {}).get('prova_data'),
            'edital_numero': None,
            'edital_data': None,
            'inscricao_inicio': start,
            'inscricao_fim': end,
            'link_pagina': candidate.detail_url,
            'link_edital': edital_url,
            'link_inscricao': next((normalize_url(candidate.detail_url, a.get('href')) for a in soup.select('a[href]') if 'inscri' in (a.get_text(' ', strip=True) or '').lower()), None),
            'resumo': resumo,
            'raw_data': raw_payload,
            'edital_pdf_text_hash': pdf_payload.get('text_hash'),
            'edital_pdf_pages': pdf_payload.get('pages'),
            'edital_pdf_excerpt': excerpt,
            'pdf_extracted_at': pdf_at,
            'content_hash': build_hash(raw_payload),
            'fetched_at': datetime.now(UTC),
        }


# Friendly aliases for callers that use the banca name rather than source type.
ELOConnector = EloOpenConnector
RBOConnector = RBOOpenConnector
