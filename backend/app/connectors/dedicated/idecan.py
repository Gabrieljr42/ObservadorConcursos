from __future__ import annotations

import logging
import re
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
    extract_pdf_link,
    normalize_url,
    parse_date_interval,
    parse_money,
    status_from_dates,
    text_lines,
)

logger = logging.getLogger(__name__)


class IDECANConnector(BaseConnector):
    banca = 'IDECAN'

    def __init__(self, base_url: str = 'https://idecan.selecao.net.br', list_url: str | None = None):
        super().__init__(base_url=base_url)
        self.list_url = list_url or f'{self.base_url}/'
        self._last_listing_empty = False

    def crawl_with_diagnostics(self) -> CrawlResult:
        candidates = self._fetch_candidates()
        concursos: list[dict[str, Any]] = []
        rejected = 0

        with httpx.Client(timeout=40.0, follow_redirects=True, headers=HEADERS, verify=False) as client:
            for candidate in candidates[:30]:
                try:
                    response = client.get(candidate.detail_url)
                    if response.status_code != 200:
                        rejected += 1
                        continue
                    parsed = self._parse_detail(candidate, response.text, client=client)
                    if parsed and self._is_valid_item(parsed):
                        concursos.append(parsed)
                    else:
                        rejected += 1
                except Exception as exc:
                    logger.warning('IDECAN detail error for %s: %s', candidate.detail_url, exc)
                    rejected += 1

        return CrawlResult(
            items=concursos,
            run_data=CrawlRunData(
                candidates_found=len(candidates),
                candidates_rejected=rejected,
                status='success' if concursos else ('empty_valid' if self._last_listing_empty else 'degraded'),
                http_status=200,
                browser_used=False,
                diagnostics_payload={'empty_evidence': self._last_listing_empty},
            ),
        )

    def crawl(self) -> list[dict[str, Any]]:
        return self.crawl_with_diagnostics().items

    def _fetch_candidates(self) -> list[CandidateItem]:
        candidates: list[CandidateItem] = []
        seen: set[str] = set()

        # Use the shared fetch pipeline so browser fallback and offline fixture
        # injection work consistently.
        try:
            html = self._fetch_html(self.list_url)
            soup = BeautifulSoup(html, 'lxml')
            normalized_listing = clean(soup.get_text(' ', strip=True)) or ''
            self._last_listing_empty = bool(re.search(
                r'(?:EM\s+INSCRI[CÇ][AÃ]O|INSCRI[CÇ][OÕ]ES\s+ABERTAS).{0,180}'
                r'(?:NENHUM\s+CONCURSO|NENHUM\s+ITEM\s+CADASTRADO)',
                normalized_listing,
                flags=re.IGNORECASE,
            ))
            for anchor in soup.select('a[href]'):
                href = anchor.get('href', '').strip()
                is_new_portal_detail = bool(re.search(r'/edital/ver/\d+', href, re.I))
                if '/informacoes/' not in href and '/concursos/' not in href and not is_new_portal_detail:
                    continue
                if is_new_portal_detail:
                    heading = anchor.find_previous(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
                    heading_text = clean(heading.get_text(' ', strip=True)) if heading else None
                    if not heading_text or 'EM INSCRIÇÃO' not in heading_text.upper():
                        continue
                url = normalize_url(self.list_url, href)
                if not url or url in seen:
                    continue
                seen.add(url)
                title_hint = clean(anchor.get_text(' ', strip=True))
                external_id = extract_external_id(url, [
                    r'/edital/ver/(\d+)', r'/informacoes/(\d+)', r'/concursos/([^/?#]+)',
                ])
                candidates.append(CandidateItem(
                    title_hint=title_hint or None,
                    detail_url=url,
                    external_id=external_id,
                ))
        except Exception as exc:
            logger.warning('IDECAN selecao portal error: %s', exc)

        if candidates or self._last_listing_empty:
            return candidates

        with httpx.Client(timeout=30.0, follow_redirects=True, headers=HEADERS, verify=False) as client:
            # Supplementary: WordPress API posts
            try:
                r_wp = client.get('https://idecan.org.br/wp-json/wp/v2/posts?per_page=20')
                if r_wp.status_code == 200:
                    for p in r_wp.json():
                        raw_title = p.get('title', {}).get('rendered', '')
                        title_hint = BeautifulSoup(raw_title, 'lxml').get_text(' ', strip=True)
                        content_html = p.get('content', {}).get('rendered', '')
                        soup_p = BeautifulSoup(content_html, 'lxml')
                        for a in soup_p.select('a[href]'):
                            href = a.get('href', '')
                            if 'selecao.net.br/informacoes/' in href:
                                if href not in seen:
                                    seen.add(href)
                                    ext_id = extract_external_id(href, [r'/informacoes/(\d+)'])
                                    candidates.append(CandidateItem(
                                        title_hint=title_hint or None,
                                        detail_url=href,
                                        external_id=ext_id,
                                    ))
            except Exception as exc:
                logger.warning('IDECAN WP API error: %s', exc)

        return candidates

    def _parse_detail(self, candidate: CandidateItem, html: str, *, client: httpx.Client) -> dict[str, Any] | None:
        soup = BeautifulSoup(html, 'lxml')
        lines = text_lines(soup)
        text = '\n'.join(lines)

        title, orgao = self._extract_title_and_orgao(soup, lines, candidate.title_hint)
        cidade, uf = extract_city_uf(f'{title} {orgao} {text[:2000]}')
        modalidade = 'Processo Seletivo' if 'processo seletivo' in title.lower() else 'Concurso Público'
        m_ed = re.search(r'Edital\s*n?[º°o.]?\s*(\d{1,4}/\d{4})', f'{title} {text[:1500]}', re.I)
        edital_numero = m_ed.group(1) if m_ed else None

        inicio, fim = parse_date_interval(text)
        status = status_from_dates(inicio, fim)

        vagas = self._extract_vagas(text)
        edital_url = extract_pdf_link(soup, candidate.detail_url)
        inscricao_url = self._extract_inscricao_link(soup, candidate.detail_url)

        pdf_payload, pdf_fields, excerpt, pdf_at = extract_pdf_fields_if_possible(edital_url, title=title, orgao=orgao, client=client)
        cargo = pdf_fields.get('cargo') if pdf_fields else None
        area = pdf_fields.get('area') if pdf_fields else classify_area(title, orgao, cargo, text[:1200])
        if pdf_fields:
            vagas = vagas or pdf_fields.get('vagas')
            if pdf_fields.get('cidade'):
                cidade = pdf_fields.get('cidade')
            if pdf_fields.get('uf'):
                uf = pdf_fields.get('uf')

        taxa = (pdf_fields or {}).get('taxa') or self._extract_taxa(text)
        salario_min, salario_max = self._extract_salarios(text)
        salario_min = (pdf_fields or {}).get('salario_min') or salario_min
        salario_max = (pdf_fields or {}).get('salario_max') or salario_max
        prova_data = pdf_fields.get('prova_data') if pdf_fields else None
        external_id = candidate.external_id or extract_external_id(candidate.detail_url, [r'/edital/ver/(\d+)', r'/informacoes/(\d+)'])

        publications = self._extract_publications(soup, candidate.detail_url)
        raw_payload = {
            'title_hint': candidate.title_hint,
            'detail_url': candidate.detail_url,
            'lines_sample': lines[:80],
            'publications': publications,
            'pdf': pdf_payload,
            'pdf_fields': pdf_fields.get('raw_pdf_fields') if isinstance(pdf_fields, dict) else {},
            'source_list_url': self.list_url,
        }
        resumo = build_summary(title, modalidade, status, inicio, fim, cargo=cargo, area=area, vagas=vagas)

        return {
            'external_id': external_id,
            'banca': self.banca,
            'orgao': orgao,
            'titulo': title,
            'modalidade': modalidade,
            'cargo': cargo,
            'area': area,
            'cidade': cidade,
            'uf': uf,
            'status': status,
            'vagas': vagas,
            'salario_min': salario_min,
            'salario_max': salario_max,
            'escolaridade': pdf_fields.get('escolaridade') if pdf_fields else None,
            'taxa': taxa,
            'prova_data': prova_data,
            'edital_numero': edital_numero,
            'edital_data': None,
            'inscricao_inicio': inicio,
            'inscricao_fim': fim,
            'link_pagina': candidate.detail_url,
            'link_edital': edital_url,
            'link_inscricao': inscricao_url,
            'resumo': resumo,
            'raw_data': raw_payload,
            'content_hash': build_hash(raw_payload),
            'fetched_at': datetime.now(UTC),
        }

    def _is_valid_item(self, item: dict[str, Any]) -> bool:
        title = (item.get('titulo') or '').lower().strip()
        if not title or len(title) < 5 or title == 'idecan':
            return False
        return bool(item.get('orgao') or item.get('uf') or item.get('link_edital'))

    def _extract_title_and_orgao(self, soup: BeautifulSoup, lines: list[str], title_hint: str | None) -> tuple[str, str | None]:
        headers = [clean(h.get_text(' ', strip=True)) for h in soup.select('h1, h2, h3, h4, .titulo-concurso, .subtitulo') if clean(h.get_text(' ', strip=True))]
        title = None
        orgao = None

        bad = {'idecan', 'menu', 'busca', 'acessar área do candidato', 'concursos / vestibulares', 'informações gerais', 'publicações', 'vagas'}
        clean_headers = [h for h in headers if h.lower() not in bad]

        if clean_headers:
            for h in clean_headers:
                if any(k in h.lower() for k in ['prefeitura', 'câmara', 'camara', 'bombeiros', 'polícia', 'policia', 'conselho', 'secretaria', 'tribunal', 'governo', 'instituto']):
                    orgao = h
                    title = h
                    break
            if not title:
                title = clean_headers[0]

        if not title:
            title = clean(title_hint) or 'Concurso IDECAN'
        if not orgao:
            orgao = title

        return title, orgao

    def _extract_vagas(self, text: str) -> int | None:
        m = re.search(
            r'(?:quantidade\s+de\s+vagas|total\s+de\s+vagas|vagas(?:\s+ofertadas)?)\s*[:\-–]?\s*(\d{1,5})',
            text,
            flags=re.IGNORECASE,
        )
        return int(m.group(1)) if m else None

    def _extract_salarios(self, text: str) -> tuple[Decimal | None, Decimal | None]:
        values = [parse_money(match.group(0)) for match in re.finditer(r'R\$\s*\d{1,3}(?:\.\d{3})*,\d{2}', text)]
        salaries = [value for value in values if value is not None and value >= Decimal('500')]
        return (min(salaries), max(salaries)) if salaries else (None, None)

    def _extract_taxa(self, text: str) -> Decimal | None:
        m = re.search(
            r'taxa(?:\s+de\s+inscri[cç][aã]o)?\s*[:\-–]?\s*(R\$\s*\d{1,3}(?:\.\d{3})*,\d{2})',
            text,
            flags=re.IGNORECASE,
        )
        return parse_money(m.group(1)) if m else None

    def _extract_inscricao_link(self, soup: BeautifulSoup, base_url: str) -> str | None:
        for anchor in soup.select('a[href]'):
            text = clean(anchor.get_text(' ', strip=True)) or ''
            href = anchor.get('href', '')
            if 'inscricao' in href.lower() or 'inscrição' in text.lower() or 'candidato' in text.lower():
                return normalize_url(base_url, href)
        return None

    def _extract_publications(self, soup: BeautifulSoup, base_url: str) -> list[dict[str, Any]]:
        pubs: list[dict[str, Any]] = []
        seen: set[str] = set()
        for anchor in soup.select('a[href]'):
            href = anchor.get('href', '').strip()
            text = clean(anchor.get_text(' ', strip=True)) or ''
            if not href or href.startswith('#') or href.startswith('javascript:'):
                continue
            if '.pdf' in href.lower() or any(k in text.lower() for k in ['edital', 'anexo', 'resultado', 'gabarito', 'comunicado', 'errata']):
                full_url = normalize_url(base_url, href)
                if full_url and full_url not in seen:
                    seen.add(full_url)
                    pubs.append({
                        'title': text[:200] if text else href.split('/')[-1][:200],
                        'link': full_url,
                        'publication_type': 'edital' if 'edital' in text.lower() else 'anexo',
                        'content_hash': build_hash({'url': full_url, 'title': text}),
                    })
        return pubs
