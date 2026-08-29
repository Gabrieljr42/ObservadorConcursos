from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
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
    extract_external_id,
    extract_pdf_fields_if_possible,
    normalize_url,
    parse_date_interval,
    parse_money,
    status_from_dates,
    text_lines,
)

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class IBGPCandidate:
    cod: str
    title_hint: str | None = None
    detail_url: str = ''


class IBGPConnector(BaseConnector):
    banca = 'IBGP'
    browser_strategy = 'fallback'

    def __init__(self, base_url: str = 'https://novo.ibgpconcursos.com.br', list_url: str | None = None):
        super().__init__(base_url=base_url)
        self.list_url = list_url or f'{self.base_url}/index.jsp'

    def crawl_with_diagnostics(self) -> CrawlResult:
        candidates = self._fetch_candidates()
        concursos: list[dict[str, Any]] = []
        rejected = 0

        with httpx.Client(timeout=30.0, follow_redirects=True, headers=HEADERS, verify=False) as client:
            for candidate in candidates:
                try:
                    item = self._fetch_and_parse_json(candidate, client=client)
                    if item and self._is_valid_item(item):
                        concursos.append(item)
                    else:
                        rejected += 1
                except Exception as exc:
                    logger.warning('IBGP parse error for cod=%s: %s', candidate.cod, exc)
                    rejected += 1

        return CrawlResult(
            items=concursos,
            run_data=CrawlRunData(
                candidates_found=len(candidates),
                candidates_rejected=rejected,
                status='success' if concursos else 'degraded',
                http_status=200,
                browser_used=self.run_data.browser_used,
            ),
        )

    def crawl(self) -> list[dict[str, Any]]:
        return self.crawl_with_diagnostics().items

    def _fetch_candidates(self) -> list[IBGPCandidate]:
        """Discover active IBGP contest IDs from HTML/browser carousel."""
        seen_cods: set[str] = set()
        candidates: list[IBGPCandidate] = []

        targets = [self.list_url]

        for target in targets:
            try:
                html = self._fetch_html(target)
                soup = BeautifulSoup(html, 'lxml')
                found = self._extract_cods_from_soup(soup, seen_cods, candidates)
                if found == 0 and not seen_cods:
                    b_html = self._fetch_html_with_browser(target, reason='IBGP JS Carousel')
                    b_soup = BeautifulSoup(b_html, 'lxml')
                    self._extract_cods_from_soup(b_soup, seen_cods, candidates)
            except Exception as exc:
                logger.warning('IBGP listing fetch error for %s: %s', target, exc)

        return candidates

    def _extract_cods_from_soup(self, soup: BeautifulSoup, seen: set[str], candidates: list[IBGPCandidate]) -> int:
        count = 0
        for anchor in soup.select('a[href]'):
            href = anchor.get('href', '')
            m = re.search(r'concurso\.jsp\?cod=(\d+)', href, re.I)
            if m:
                cod = m.group(1)
                if cod not in seen:
                    seen.add(cod)
                    detail_url = f'{self.base_url}/concurso.jsp?cod={cod}'
                    title_hint = clean(anchor.get_text(' ', strip=True))
                    candidates.append(IBGPCandidate(cod=cod, title_hint=title_hint or None, detail_url=detail_url))
                    count += 1
        return count

    def _fetch_and_parse_json(self, candidate: IBGPCandidate, *, client: httpx.Client) -> dict[str, Any] | None:
        cod = candidate.cod
        meta_url = f'{self.base_url}/rest/concurso/{cod}'
        r_meta = client.get(meta_url)
        if r_meta.status_code != 200:
            return None
        meta = r_meta.json()
        if not isinstance(meta, dict) or not meta.get('id'):
            return None

        # Title and Organ
        nome = clean(meta.get('nome')) or f'Concurso IBGP {cod}'
        empresa = meta.get('empresa') or {}
        orgao = clean(empresa.get('nome')) if isinstance(empresa, dict) else None

        # Dates & Status
        inicio_str = meta.get('inicioInscricaoFormatado')
        fim_str = meta.get('fimInscricaoFormatado')
        inicio = self._parse_ibgp_datetime(inicio_str)
        fim = self._parse_ibgp_datetime(fim_str)

        is_open = bool(meta.get('statusInscricao'))
        if is_open:
            status = 'Inscrições abertas'
        else:
            status = status_from_dates(inicio, fim)

        # Location
        cidade, uf = extract_city_uf(f'{nome} {orgao}')

        # Modality & Edital number
        modalidade = 'Processo Seletivo' if 'processo seletivo' in nome.lower() else 'Concurso Público'
        m_ed = re.search(r'Edital\s*n?[º°o.]?\s*(\d{1,4}/\d{4})', nome, re.I)
        edital_numero = m_ed.group(1) if m_ed else None

        # Fetch cargos for vacancies & fees
        vagas = 0
        salarios: list[Decimal] = []
        cargo_names: list[str] = []
        taxa = None
        prova_data = None

        try:
            r_cargos = client.get(f'{self.base_url}/rest/concurso/cargos/{cod}')
            if r_cargos.status_code == 200:
                cargos_data = r_cargos.json()
                if isinstance(cargos_data, dict):
                    cargos_list = cargos_data.get('cargos') or []
                    for c_item in cargos_list:
                        if isinstance(c_item, dict):
                            c_name = clean(c_item.get('nome'))
                            if c_name:
                                cargo_names.append(c_name)
                            v_ampla = c_item.get('vagas') or 0
                            v_pcd = c_item.get('vagasPcd') or 0
                            if isinstance(v_ampla, int):
                                vagas += v_ampla
                            if isinstance(v_pcd, int):
                                vagas += v_pcd
                            sal = c_item.get('vencimento') or c_item.get('salario')
                            if sal:
                                p_sal = parse_money(str(sal))
                                if p_sal and p_sal >= Decimal('1000'):
                                    salarios.append(p_sal)

                    valores = cargos_data.get('valoresInscricao') or []
                    if valores and isinstance(valores, list):
                        for val in valores:
                            if isinstance(val, (int, float, str)):
                                p_taxa = parse_money(str(val))
                                if p_taxa:
                                    taxa = p_taxa
                                    break
        except Exception:
            pass

        cargo = 'Vários cargos' if len(cargo_names) >= 2 else (cargo_names[0] if cargo_names else None)
        area = classify_area(nome, orgao, cargo, ' '.join(cargo_names[:30]))
        salario_min = min(salarios) if salarios else None
        salario_max = max(salarios) if salarios else None

        # Fetch editais & publications
        publications: list[dict[str, Any]] = []
        link_edital = None

        try:
            r_editais = client.get(f'{self.base_url}/rest/concurso/editais/{cod}')
            if r_editais.status_code == 200:
                editais_list = r_editais.json()
                if isinstance(editais_list, list):
                    for ed in editais_list:
                        if isinstance(ed, dict):
                            ed_name = clean(ed.get('nome')) or clean(ed.get('nomeReal')) or 'Edital'
                            ed_id = ed.get('id')
                            nome_real = ed.get('nomeReal')
                            if ed_id and nome_real:
                                download_url = f'{self.base_url}/rest/concurso/download/edital/{ed_id}/?file=site/anexos/{cod}/{nome_real}'
                                if not link_edital and ('edital' in ed_name.lower() or 'edital' in nome_real.lower()):
                                    link_edital = download_url
                                publications.append({
                                    'title': ed_name,
                                    'link': download_url,
                                    'publication_type': 'edital' if 'edital' in ed_name.lower() else 'anexo',
                                    'content_hash': build_hash({'url': download_url, 'title': ed_name}),
                                })
        except Exception:
            pass

        link_pagina = f'{self.base_url}/concurso.jsp?cod={cod}'
        link_inscricao = f'{self.base_url}/candidato/index.jsp?cod={cod}' if is_open else None

        raw_payload = {
            'cod': cod,
            'meta': meta,
            'cargos_count': len(cargo_names),
            'publications': publications,
            'source_list_url': self.list_url,
        }

        resumo = build_summary(
            nome, modalidade, status, inicio, fim,
            cargo=cargo, area=area, vagas=vagas if vagas > 0 else None,
            salario_min=salario_min, salario_max=salario_max,
        )

        return {
            'external_id': str(cod),
            'banca': self.banca,
            'orgao': orgao,
            'titulo': nome,
            'modalidade': modalidade,
            'cargo': cargo,
            'area': area,
            'cidade': cidade,
            'uf': uf,
            'status': status,
            'vagas': vagas if vagas > 0 else None,
            'salario_min': salario_min,
            'salario_max': salario_max,
            'escolaridade': None,
            'taxa': taxa,
            'prova_data': prova_data,
            'edital_numero': edital_numero,
            'edital_data': None,
            'inscricao_inicio': inicio,
            'inscricao_fim': fim,
            'link_pagina': link_pagina,
            'link_edital': link_edital,
            'link_inscricao': link_inscricao,
            'resumo': resumo,
            'raw_data': raw_payload,
            'content_hash': build_hash(raw_payload),
            'fetched_at': datetime.now(UTC),
        }

    def _is_valid_item(self, item: dict[str, Any]) -> bool:
        title = (item.get('titulo') or '').lower().strip()
        if not title or len(title) < 5:
            return False
        return bool(item.get('orgao') or item.get('uf') or item.get('inscricao_inicio'))

    def _parse_ibgp_datetime(self, date_str: str | None) -> datetime | None:
        if not date_str:
            return None
        # Format: "31/08/26 09:00" or "31/08/2026 09:00"
        m = re.search(r'(\d{2})/(\d{2})/(\d{2,4})(?:\s+(\d{2}):(\d{2}))?', date_str)
        if not m:
            return None
        day, month, year = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if year < 100:
            year += 2000
        hour = int(m.group(4)) if m.group(4) else 0
        minute = int(m.group(5)) if m.group(5) else 0
        try:
            return datetime(year, month, day, hour, minute, tzinfo=UTC)
        except ValueError:
            return None
