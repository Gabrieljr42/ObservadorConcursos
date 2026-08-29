from __future__ import annotations

import logging
import re
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
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
from app.publications import parse_publications_from_dom, parse_publications_from_lines

logger = logging.getLogger(__name__)


class AOCPConnector(BaseConnector):
    """Dedicated connector for Instituto AOCP."""

    banca = 'Instituto AOCP'
    use_browser_fallback = True
    browser_strategy = 'fallback'

    DETAIL_URL_PATTERNS = (
        r'/concurso\.jsp\?id=\d+',
        r'/concurso/\d+',
        r'/concursos/\d+',
        r'id=\d+',
    )

    def __init__(self, base_url: str = 'https://www.institutoaocp.org.br', list_url: str | None = None):
        super().__init__(
            base_url=base_url,
            list_url=list_url or 'https://www.institutoaocp.org.br',
        )

    def _fetch_candidates(self) -> list[CandidateItem]:
        candidates: list[CandidateItem] = []
        seen: set[str] = set()

        urls_to_scan = [
            self.list_url,
            'https://www.institutoaocp.org.br/concursos.jsp',
            'https://www.institutoaocp.org.br/inscricoesAbertas.jsp',
        ]

        fetch_success = False
        last_fetch_exc = None
        for scan_url in urls_to_scan:
            try:
                html = self._fetch_html(scan_url)
                fetch_success = True
            except Exception as exc:
                last_fetch_exc = exc
                logger.warning('AOCP: error fetching %s: %s', scan_url, exc)
                continue

            soup = BeautifulSoup(html, 'lxml')

            for card in soup.select('.concurso, .item-concurso, .card, tr, .box-concurso'):
                anchors = card.select('a[href]')
                card_text = clean(card.get_text(' ', strip=True)) or ''
                for a in anchors:
                    href = a.get('href')
                    url = normalize_url(scan_url, href)
                    if not url or url in seen or not self._same_domain(url):
                        continue
                    if any(bad in url.lower() for bad in ['login', 'contato', 'institucional', 'privacidade']):
                        continue

                    if any(re.search(pat, url, flags=re.IGNORECASE) for pat in self.DETAIL_URL_PATTERNS) or 'id=' in url:
                        seen.add(url)
                        candidates.append(CandidateItem(
                            title_hint=card_text[:500] or clean(a.get_text(' ', strip=True)),
                            detail_url=url,
                            status_hint=self._infer_status(card_text),
                            external_id=extract_external_id(url, [r'id=(\d+)']),
                        ))
                        if len(candidates) >= self.max_candidates:
                            return candidates

            for a in soup.select('a[href]'):
                href = a.get('href')
                url = normalize_url(scan_url, href)
                if not url or url in seen or not self._same_domain(url):
                    continue
                if any(re.search(pat, url, flags=re.IGNORECASE) for pat in self.DETAIL_URL_PATTERNS):
                    seen.add(url)
                    t_text = clean(a.get_text(' ', strip=True))
                    candidates.append(CandidateItem(
                        title_hint=t_text,
                        detail_url=url,
                        status_hint='Inscrições abertas' if 'abertas' in scan_url.lower() else None,
                        external_id=extract_external_id(url, [r'id=(\d+)']),
                    ))
                    if len(candidates) >= self.max_candidates:
                        break

        if not candidates and not fetch_success and last_fetch_exc:
            raise last_fetch_exc

        if not candidates and fetch_success:
            self.mark_empty_evidence('selector_empty', 'Scanned AOCP pages returned zero open contest cards', self.list_url)

        return candidates

    def _same_domain(self, url: str) -> bool:
        host = urlparse(url).netloc.replace('www.', '')
        return not host or 'institutoaocp.org.br' in host or 'aocp.org.br' in host

    def _infer_status(self, text: str | None) -> str | None:
        lowered = (text or '').lower()
        if 'inscrições abertas' in lowered or 'inscricoes abertas' in lowered:
            return 'Inscrições abertas'
        if 'em andamento' in lowered or 'andamento' in lowered:
            return 'Em andamento'
        if 'encerrado' in lowered or 'finalizado' in lowered:
            return 'Finalizado'
        return None

    def _parse_detail(self, candidate: CandidateItem, html: str, *, client: httpx.Client) -> dict[str, Any] | None:
        soup = BeautifulSoup(html, 'lxml')
        lines = text_lines(soup)
        text = '\n'.join(lines)

        title = self._extract_title(lines, candidate.title_hint)
        orgao = self._extract_orgao(title, lines, candidate.title_hint)
        cidade, uf = extract_city_uf(f'{title} {orgao} {text[:2000]}')
        modalidade = 'Concurso Público' if 'concurso' in title.lower() else 'Processo Seletivo'
        inicio, fim = parse_date_interval(text)
        status = status_from_dates(inicio, fim, fallback=candidate.status_hint or self._infer_status(text[:2000]))

        edital_url = extract_pdf_link(soup, candidate.detail_url)
        inscricao_url = self._extract_inscricao_link(soup, candidate.detail_url)
        cargo_candidates = self._extract_cargo_candidates(lines)
        area = classify_area_from_many(cargo_candidates, title, orgao, text[:1500])
        cargo = 'Vários cargos' if len(cargo_candidates) >= 2 else (cargo_candidates[0] if cargo_candidates else None)
        vagas = self._extract_vagas(text)
        salario_min, salario_max = self._extract_salarios(text)
        taxa = self._extract_taxa(text)
        external_id = candidate.external_id or extract_external_id(candidate.detail_url, [r'id=(\d+)'])

        pdf_payload, pdf_fields, excerpt, pdf_at = extract_pdf_fields_if_possible(edital_url, title=title, orgao=orgao, client=client)
        if pdf_fields:
            cargo = cargo or pdf_fields.get('cargo')
            area = area or pdf_fields.get('area')
            vagas = vagas or pdf_fields.get('vagas')
            salario_min = salario_min or pdf_fields.get('salario_min')
            salario_max = salario_max or pdf_fields.get('salario_max')
            taxa = taxa if taxa is not None else pdf_fields.get('taxa')

        if not self._is_valid_certame(title, orgao, cidade, uf, inicio, fim, edital_url, cargo_candidates, text):
            return None

        publications = parse_publications_from_dom(soup, candidate.detail_url, source='aocp')
        if not publications:
            publications = parse_publications_from_lines(lines, source='aocp')
        raw_payload = {
            'title_hint': candidate.title_hint,
            'detail_url': candidate.detail_url,
            'lines_sample': lines[:120],
            'cargo_candidates': cargo_candidates[:60],
            'publications': publications,
            'pdf': pdf_payload,
            'pdf_fields': pdf_fields.get('raw_pdf_fields') if isinstance(pdf_fields, dict) else {},
            'source_list_url': self.list_url,
        }
        resumo = build_summary(title, modalidade, status, inicio, fim, cargo=cargo, area=area, vagas=vagas, salario_min=salario_min, salario_max=salario_max)

        return {
            'external_id': external_id,
            'banca': self.banca,
            'orgao': orgao,
            'titulo': title,
            'modalidade': modalidade,
            'cargo': cargo,
            'area': area,
            'cidade': cidade or (pdf_fields or {}).get('cidade'),
            'uf': uf or (pdf_fields or {}).get('uf'),
            'status': status,
            'vagas': vagas,
            'salario_min': salario_min,
            'salario_max': salario_max,
            'escolaridade': (pdf_fields or {}).get('escolaridade'),
            'taxa': taxa,
            'prova_data': (pdf_fields or {}).get('prova_data'),
            'edital_numero': None,
            'edital_data': None,
            'inscricao_inicio': inicio,
            'inscricao_fim': fim,
            'link_pagina': candidate.detail_url,
            'link_edital': edital_url,
            'link_inscricao': inscricao_url,
            'resumo': resumo,
            'raw_data': raw_payload,
            'edital_pdf_text_hash': pdf_payload.get('text_hash'),
            'edital_pdf_pages': pdf_payload.get('pages'),
            'edital_pdf_excerpt': excerpt,
            'pdf_extracted_at': pdf_at,
            'content_hash': build_hash(raw_payload),
            'fetched_at': datetime.now(UTC),
        }

    def _extract_title(self, lines: list[str], hint: str | None) -> str:
        candidates = [hint] if hint else []
        candidates.extend(lines[:80])
        for raw in candidates:
            line = clean(raw)
            if not line or len(line) < 10 or len(line) > 220:
                continue
            if re.search(r'\b(?:concurso|processo seletivo|edital|prefeitura|tribunal|ebserh|pol[íi]cia|secretaria|hospital|uf)\b', line, flags=re.IGNORECASE):
                return line
        return 'Concurso Instituto AOCP'

    def _extract_orgao(self, title: str, lines: list[str], hint: str | None) -> str | None:
        for val in [title, hint] + lines[:100]:
            if not val:
                continue
            m = re.search(r'((?:PREFEITURA|C[ÂA]MARA|SECRETARIA|MINIST[ÉE]RIO|TRIBUNAL|DEFENSORIA|POL[ÍI]CIA|EBSERH|CORPO DE BOMBEIROS|UNIVERSIDADE|HOSPITAL)[^\n]{3,150})', val, flags=re.IGNORECASE)
            if m:
                return clean(m.group(1))
        return None

    def _extract_inscricao_link(self, soup: BeautifulSoup, base: str) -> str | None:
        for a in soup.select('a[href]'):
            t = clean(a.get_text(' ', strip=True)) or ''
            href = a.get('href')
            if any(k in f'{t} {href}'.lower() for k in ['inscrição', 'inscricao', 'inscreva-se', 'área do candidato']):
                return normalize_url(base, href)
        return None

    def _extract_cargo_candidates(self, lines: list[str]) -> list[str]:
        cargos = []
        for line in lines[:120]:
            norm = (clean(line) or '').strip()
            if not norm or len(norm) < 4 or len(norm) > 120:
                continue
            if re.search(r'\b(assistente|agente|analista|auxiliar|técnico|tecnico|professor|médico|medico|enfermeiro|fiscal|contador|advogado|guarda|motorista|engenheiro)\b', norm, flags=re.IGNORECASE):
                cargos.append(norm)
            if len(cargos) >= 40:
                break
        return cargos

    def _extract_vagas(self, text: str) -> int | None:
        for pat in [
            r'(?:total\s+de\s+vagas|quantidade\s+de\s+vagas|vagas\s+ofertadas)\D{0,30}(\d{1,5})',
            r'\b(\d{1,5})\s+vagas\b',
        ]:
            m = re.search(pat, text, flags=re.IGNORECASE)
            if m:
                val = int(m.group(1))
                if 1 <= val <= 50000:
                    return val
        return None

    def _extract_salarios(self, text: str):
        vals = []
        for match in re.finditer(r'R\$\s*\d{1,3}(?:\.\d{3})*,\d{2}', text):
            parsed = parse_money(match.group(0))
            if parsed and parsed >= Decimal('1000'):
                vals.append(parsed)
        if vals:
            return min(vals), max(vals)
        return None, None

    def _extract_taxa(self, text: str):
        for pat in [
            r'(?:taxa\s+de\s+inscri[cç][aã]o|taxa)\s*[:\-–]?\s*(R\$\s*\d{1,3}(?:\.\d{3})*,\d{2})',
            r'(?:taxa|inscri[cç][aã]o).{0,30}(R\$\s*\d{1,3}(?:\.\d{3})*,\d{2})',
        ]:
            m = re.search(pat, text, flags=re.IGNORECASE)
            if m:
                val = parse_money(m.group(1))
                if val is not None and val <= Decimal('1000.00'):
                    return val
        if re.search(r'taxa\s+de\s+inscri[cç][aã]o\s+gratuita|inscri[cç][aã]o\s+gratuita|isento\s+de\s+taxa', text, flags=re.IGNORECASE):
            return Decimal('0.00')
        return None
