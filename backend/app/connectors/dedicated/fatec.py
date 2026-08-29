from __future__ import annotations

import re
from datetime import UTC, datetime
from typing import Any

import httpx
from bs4 import BeautifulSoup

from app.connectors.base import BaseConnector, CrawlResult, CrawlRunData
from app.connectors.common import (
    build_hash,
    build_summary,
    classify_area,
    clean,
    extract_pdf_link,
    parse_date_interval,
)
from app.connectors.institutional import InstitutionalSelectionConnector
from app.publications import parse_publications_from_dom


class FATECSelectionConnector(BaseConnector):
    """Parse the FATEC personnel table, whose rows have documents but no detail URL."""

    banca = 'FATEC'
    category = 'institutional_selection'
    mode = 'all'

    def __init__(
        self,
        base_url: str = 'https://www.fatecsm.org.br',
        list_url: str | None = None,
    ):
        super().__init__(base_url, list_url or f'{base_url.rstrip("/")}/processos-seletivos/')

    def _fetch_candidates(self):  # pragma: no cover - crawl is table-oriented
        raise NotImplementedError

    def _parse_detail(self, candidate, html: str, *, client: httpx.Client):  # pragma: no cover
        raise NotImplementedError

    def crawl_with_diagnostics(self) -> CrawlResult:
        try:
            html = self._fetch_html(self.list_url)
            soup = BeautifulSoup(html, 'lxml')
            rows = soup.select('table tr')
            items: list[dict[str, Any]] = []
            rejected = 0
            candidates = 0

            for row in rows:
                cells = row.select('td')
                if len(cells) < 5:
                    continue
                row_text = clean(row.get_text(' ', strip=True)) or ''
                portal_status = (clean(cells[0].get_text(' ', strip=True)) or '').lower()
                if 'em andamento' not in portal_status and 'aberto' not in portal_status:
                    continue
                candidates += 1
                item = self._parse_row(row)
                if item:
                    items.append(item)
                else:
                    rejected += 1

            self.run_data.candidates_found = candidates
            self.run_data.candidates_rejected = rejected
            self.run_data.status = 'success' if items else 'degraded'
            if not items:
                self.run_data.error_type = 'UnconfirmedEmpty'
                self.run_data.error_message = 'No eligible active FATEC personnel rows were parsed'
            return CrawlResult(items, self.run_data)
        except Exception as exc:
            self.run_data.status = 'failed'
            self.run_data.error_type = exc.__class__.__name__
            self.run_data.error_message = str(exc)
            return CrawlResult([], self.run_data)

    def _parse_row(self, row) -> dict[str, Any] | None:
        cells = row.select('td')
        number = clean(cells[1].get_text(' ', strip=True))
        period = clean(cells[2].get_text(' ', strip=True))
        description = clean(cells[3].get_text(' ', strip=True))
        row_text = clean(row.get_text(' ', strip=True)) or ''
        if not number or not description:
            return None
        if not InstitutionalSelectionConnector.has_personnel_evidence(description, row_text):
            return None

        inicio, fim = parse_date_interval(period)
        status = 'Em andamento' if 'em andamento' in row_text.lower() else 'Inscrições abertas'
        edital_url = extract_pdf_link(row, self.list_url)
        publications = parse_publications_from_dom(row, self.list_url, source='fatec')
        cargo = self._cargo_from_description(description)
        area = classify_area(cargo, description)
        external_id = re.sub(r'[^0-9A-Za-z]+', '-', number).strip('-').lower()
        page_url = f'{self.list_url.rstrip("/")}/#processo-{external_id}'
        raw_payload = {
            'number': number,
            'period': period,
            'description': description,
            'row_text': row_text,
            'publications': publications,
            'source_list_url': self.list_url,
        }

        return {
            'external_id': external_id,
            'banca': self.banca,
            'orgao': 'Fundação de Apoio à Tecnologia e Ciência - FATEC',
            'titulo': f'Processo Seletivo {number} - {description}',
            'modalidade': 'Processo Seletivo',
            'cargo': cargo,
            'area': area,
            'cidade': 'Santa Maria',
            'uf': 'RS',
            'status': status,
            'vagas': self._extract_vagas(row_text),
            'salario_min': None,
            'salario_max': None,
            'escolaridade': None,
            'taxa': None,
            'prova_data': None,
            'edital_numero': number,
            'edital_data': None,
            'inscricao_inicio': inicio,
            'inscricao_fim': fim,
            'link_pagina': page_url,
            'link_edital': edital_url,
            'link_inscricao': None,
            'resumo': build_summary(
                description,
                'Processo Seletivo',
                status,
                inicio,
                fim,
                cargo=cargo,
                area=area,
            ),
            'raw_data': raw_payload,
            'content_hash': build_hash(raw_payload),
            'fetched_at': datetime.now(UTC),
        }

    @staticmethod
    def _cargo_from_description(description: str) -> str:
        value = re.sub(
            r'^(?:PROCESSO\s+SELETIVO\s+PARA\s+CONTRATAÇÃO\s+DE|CONTRATAÇÃO\s+CLT:|SELEÇÃO\s+DE)\s*',
            '',
            description,
            flags=re.IGNORECASE,
        )
        return clean(value) or description

    @staticmethod
    def _extract_vagas(text: str) -> int | None:
        for pattern in (
            r'n[uú]mero\s+total\s+de\s+vagas\s*[:\-]?\s*(\d{1,4})',
            r'total\s+de\s+vagas\s*[:\-]?\s*(\d{1,4})',
            r'\b(\d{1,4})\s+vagas\b',
        ):
            match = re.search(pattern, text, re.I)
            if match:
                return int(match.group(1))
        return None
