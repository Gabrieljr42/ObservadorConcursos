from __future__ import annotations

import logging
import re
from datetime import UTC, datetime
from typing import Any
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

from app.connectors.base import BaseConnector, CandidateItem, CrawlResult, CrawlRunData, HEADERS
from app.connectors.common import (
    build_hash,
    build_summary,
    classify_area,
    clean,
    extract_city_uf,
    extract_pdf_fields_if_possible,
    status_from_dates,
)

logger = logging.getLogger(__name__)


class FumarcConnector(BaseConnector):
    banca = 'FUMARC'

    _VOLATILE_SHAREPOINT_KEYS = {
        '__metadata',
        'OData__UIVersionString',
    }

    @classmethod
    def _stable_sharepoint_value(cls, value: Any) -> Any:
        """Remove SharePoint transport/version metadata before hashing.

        SharePoint can change ``etag``/``OData__UIVersionString`` between
        reads even when the contest's user-visible fields are unchanged.  The
        complete response remains in ``raw_data``; only the content identity
        used for versioning is normalized.
        """
        if isinstance(value, dict):
            return {
                str(key): cls._stable_sharepoint_value(nested)
                for key, nested in value.items()
                if key not in cls._VOLATILE_SHAREPOINT_KEYS and not str(key).startswith('__')
            }
        if isinstance(value, list):
            return [cls._stable_sharepoint_value(nested) for nested in value]
        return value

    def __init__(self, base_url: str = 'https://www.fumarc.com.br', list_url: str | None = None):
        super().__init__(base_url=base_url)
        self.list_url = list_url or f'{self.base_url}/concursos'

    def crawl_with_diagnostics(self) -> CrawlResult:
        concursos: list[dict[str, Any]] = []
        rejected = 0

        api_headers = {
            'Accept': 'application/json;odata=verbose',
            'User-Agent': HEADERS.get('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'),
        }

        with httpx.Client(timeout=40.0, follow_redirects=True, headers=api_headers, verify=False) as client:
            try:
                # 1. Fetch Realizadores (Organs)
                organs_map: dict[int, str] = {}
                r_org = client.get(f'{self.base_url}/_api/web/lists/getByTitle(\x27ConcursoRealizador\x27)/items?$top=200')
                if r_org.status_code == 200:
                    for item in r_org.json().get('d', {}).get('results', []):
                        oid = item.get('Id')
                        otitle = clean(item.get('Title'))
                        if oid and otitle:
                            organs_map[oid] = otitle

                # 2. Fetch Calendarios (Dates)
                dates_map: dict[int, dict[str, datetime | None]] = {}
                r_cal = client.get(f'{self.base_url}/_api/web/lists/getByTitle(\x27ConcursoCalendario\x27)/items?$top=1000')
                if r_cal.status_code == 200:
                    for item in r_cal.json().get('d', {}).get('results', []):
                        cid = item.get('ConcursoId')
                        if cid:
                            if cid not in dates_map:
                                dates_map[cid] = {'inicio': None, 'fim': None, 'prova': None}
                            d_inicio = self._parse_iso_date(item.get('DataInicio'))
                            d_fim = self._parse_iso_date(item.get('DataFim'))
                            cal_title = (item.get('Title') or '').lower()
                            if 'inscri' in cal_title:
                                dates_map[cid]['inicio'] = d_inicio or dates_map[cid]['inicio']
                                dates_map[cid]['fim'] = d_fim or dates_map[cid]['fim']
                            elif 'prova' in cal_title:
                                dates_map[cid]['prova'] = d_inicio or dates_map[cid]['prova']

                # 3. Fetch Concursos
                r_conc = client.get(f'{self.base_url}/_api/web/lists/getByTitle(\x27Concursos\x27)/items?$top=100&$orderby=Id%20desc')
                if r_conc.status_code != 200:
                    return CrawlResult(
                        items=[],
                        run_data=CrawlRunData(
                            status='degraded',
                            http_status=r_conc.status_code,
                            error_type='UnconfirmedEmpty',
                            error_message='FUMARC listing returned no candidate links without an explicit empty-state marker',
                        ),
                    )

                conc_items = r_conc.json().get('d', {}).get('results', [])

                for item in conc_items:
                    cid = item.get('Id')
                    title = clean(item.get('Title'))
                    if not cid or not title:
                        continue

                    # Filter irrelevant system placeholders
                    if any(bad in title.lower() for bad in ['comunicados e avisos', 'teste', 'modelo']):
                        rejected += 1
                        continue

                    realizador_id = item.get('RealizadorId')
                    orgao = organs_map.get(realizador_id) if realizador_id else None
                    dates_info = dates_map.get(cid, {})
                    inicio = dates_info.get('inicio')
                    fim = dates_info.get('fim')
                    prova_data = dates_info.get('prova')

                    modalidade = 'Processo Seletivo' if 'processo seletivo' in title.lower() else 'Concurso Público'
                    status = status_from_dates(inicio, fim)
                    cidade, uf = extract_city_uf(f'{title} {orgao}')
                    # "CREA" and similar organization acronyms are not city
                    # names.  Keep location empty unless the official API/title
                    # provides a valid city/UF pair.
                    cidade_lower = cidade.casefold() if cidade else ''
                    if cidade and (
                        cidade_lower in {'crea', 'concurso publico', 'concurso'}
                        or 'crea' in cidade_lower
                    ):
                        cidade = None
                    if not uf:
                        uf = 'MG'

                    area = classify_area(title, orgao, None, '')
                    detail_url = f'{self.base_url}/SitePages/Home.aspx?concurso={cid}&secao=-1'

                    # Fetch publications for this contest
                    publications: list[dict[str, Any]] = []
                    link_edital = None

                    try:
                        r_pub = client.get(f'{self.base_url}/_api/web/lists/getByTitle(\x27ConcursoPublicacoes\x27)/items?$filter=ConcursoId%20eq%20{cid}&$top=50&$orderby=Id%20desc')
                        if r_pub.status_code == 200:
                            for pub in r_pub.json().get('d', {}).get('results', []):
                                p_title = clean(pub.get('Title')) or 'Documento'
                                link_obj = pub.get('Link') or pub.get('Arquivo')
                                p_url = None
                                if isinstance(link_obj, dict):
                                    p_url = link_obj.get('Url')
                                elif isinstance(link_obj, str):
                                    p_url = link_obj

                                if p_url:
                                    if not link_edital and ('edital' in p_title.lower() or 'edital' in p_url.lower()):
                                        link_edital = p_url
                                    publications.append({
                                        'title': p_title,
                                        'link': p_url,
                                        'publication_type': 'edital' if 'edital' in p_title.lower() else 'anexo',
                                        'content_hash': build_hash({'url': p_url, 'title': p_title}),
                                    })
                    except Exception:
                        pass

                    raw_payload = {
                        'concurso_id': cid,
                        'sharepoint_item': item,
                        'publications': publications,
                        'source_list_url': self.list_url,
                    }
                    content_payload = {
                        **raw_payload,
                        'sharepoint_item': self._stable_sharepoint_value(item),
                    }

                    resumo = build_summary(title, modalidade, status, inicio, fim, area=area)

                    concursos.append({
                        'external_id': str(cid),
                        'banca': self.banca,
                        'orgao': orgao,
                        'titulo': title,
                        'modalidade': modalidade,
                        'cargo': None,
                        'area': area,
                        'cidade': cidade,
                        'uf': uf,
                        'status': status,
                        'vagas': None,
                        'salario_min': None,
                        'salario_max': None,
                        'escolaridade': None,
                        'taxa': None,
                        'prova_data': prova_data,
                        'edital_numero': None,
                        'edital_data': None,
                        'inscricao_inicio': inicio,
                        'inscricao_fim': fim,
                        'link_pagina': detail_url,
                        'link_edital': link_edital,
                        'link_inscricao': None,
                        'resumo': resumo,
                        'raw_data': raw_payload,
                        'content_hash': build_hash(content_payload),
                        'fetched_at': datetime.now(UTC),
                    })

            except Exception as exc:
                logger.warning('FUMARC SharePoint API error: %s', exc)
                return CrawlResult(items=[], run_data=CrawlRunData(status='failed', error_message=str(exc)))

        return CrawlResult(
            items=concursos,
            run_data=CrawlRunData(
                candidates_found=len(concursos) + rejected,
                candidates_rejected=rejected,
                status='success' if concursos else 'degraded',
                http_status=200,
                browser_used=False,
            ),
        )

    def crawl(self) -> list[dict[str, Any]]:
        return self.crawl_with_diagnostics().items

    def _parse_iso_date(self, date_str: str | None) -> datetime | None:
        if not date_str:
            return None
        try:
            # e.g. "2022-10-23T03:00:00Z"
            clean_str = date_str.replace('Z', '+00:00')
            return datetime.fromisoformat(clean_str)
        except Exception:
            return None
