from __future__ import annotations

import hashlib
import json
import logging
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

from app.pdf.extractor import extract_pdf_text_from_url
from app.pdf.parsers.ibfc import parse_ibfc_pdf
from app.connectors.common import extract_pdf_link
from app.publications import parse_publications_from_dom

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class CrawlCandidate:
    title_hint: str | None
    detail_url: str


@dataclass(slots=True)
class TitleParts:
    title: str | None = None
    orgao: str | None = None
    localidade_texto: str | None = None
    modalidade: str | None = None


class IBFCOpenConnector:
    banca = 'IBFC'

    MENU_OR_SECTION_LABELS = {
        'publicações', 'publicacoes', 'editais e publicações oficiais', 'editais e publicacoes oficiais',
        'informações gerais', 'informacoes gerais', 'links', 'arquivos', 'anexos', 'cronograma',
        'isencao', 'isenção', 'resultado', 'comunicados', 'recursos', 'inscrições', 'inscricoes',
    }

    KNOWN_FIELD_LABELS = {
        'situação', 'situacao', 'edital', 'inscrições', 'inscricoes', 'pedidos de isenção',
        'pedidos de isencao', 'publicações', 'publicacoes', 'informações gerais', 'informacoes gerais',
        'arquivos', 'links', 'cronograma', 'resultado', 'recursos', 'anexos',
    }

    def __init__(self, base_url: str = 'https://concursos.ibfc.org.br', list_url: str | None = None):
        self.base_url = base_url.rstrip('/')
        self.list_url = list_url or f'{self.base_url}/index/abertos/'
        self._last_listing_empty = False

    def crawl_with_diagnostics(self) -> Any:
        from app.connectors.base import CrawlResult, CrawlRunData
        candidates = self._fetch_candidates()
        concursos: list[dict[str, Any]] = []
        rejected = 0
        with httpx.Client(timeout=45.0, follow_redirects=True, headers=self._headers()) as client:
            for candidate in candidates:
                try:
                    detail_response = client.get(candidate.detail_url)
                    detail_response.raise_for_status()
                    item = self._parse_detail(candidate, detail_response.text, client=client)
                    if item and self._is_valid_item(item):
                        concursos.append(item)
                    else:
                        rejected += 1
                except Exception as exc:
                    logger.warning('IBFC detail error for %s: %s', candidate.detail_url, exc)
                    rejected += 1

        empty_ev = {
            'kind': 'explicit_text',
            'value': 'Inscrições abertas: nenhum item cadastrado',
            'source': self.list_url,
        } if self._last_listing_empty else None

        return CrawlResult(
            items=concursos,
            run_data=CrawlRunData(
                candidates_found=len(candidates),
                candidates_rejected=rejected,
                status='success' if concursos else ('empty_valid' if self._last_listing_empty else 'degraded'),
                http_status=200,
                browser_used=False,
                diagnostics_payload={'empty_evidence': empty_ev},
            ),
        )

    def crawl(self) -> list[dict[str, Any]]:
        return self.crawl_with_diagnostics().items

    def _fetch_candidates(self) -> list[CrawlCandidate]:
        results: list[CrawlCandidate] = []
        seen: set[str] = set()
        # This connector represents the "open" source.  Mixing the ongoing
        # and homepage catalogs caused closed certames to be emitted when the
        # official open tab was empty.
        targets = [self.list_url]
        
        with httpx.Client(timeout=45.0, follow_redirects=True, headers=self._headers()) as client:
            for target_url in targets:
                try:
                    response = client.get(target_url)
                    status_code = getattr(response, 'status_code', None)
                    if isinstance(status_code, int) and status_code != 200:
                        continue
                    soup = BeautifulSoup(response.text, 'lxml')
                    listing_text = self._clean(soup.get_text(' ', strip=True))
                    if 'inscri' in listing_text.lower() and 'nenhum item cadastrado' in listing_text.lower():
                        self._last_listing_empty = True
                    for anchor in soup.select('a[href]'):
                        href = anchor.get('href', '').strip()
                        if '/informacoes/' not in href:
                            continue

                        detail_url = urljoin(target_url, href)
                        if detail_url in seen:
                            continue
                        seen.add(detail_url)

                        title_hint = self._clean(anchor.get_text(' ', strip=True))
                        results.append(CrawlCandidate(title_hint=title_hint or None, detail_url=detail_url))
                except Exception as exc:
                    logger.warning('IBFC listing error for %s: %s', target_url, exc)

        return results

    def _parse_detail(self, candidate: CrawlCandidate, html: str, *, client: httpx.Client) -> dict[str, Any]:
        soup = BeautifulSoup(html, 'lxml')
        lines = self._text_lines(soup)
        text = '\n'.join(lines)

        title_parts = self._parse_title_hint(candidate.title_hint)
        fallback_headings = self._safe_headings(soup)

        modalidade = title_parts.modalidade or self._infer_modalidade(candidate.title_hint, text, fallback_headings)
        orgao = title_parts.orgao or self._first_non_section(fallback_headings) or self._infer_orgao_from_title(candidate.title_hint)
        localidade_texto = title_parts.localidade_texto
        situacao = self._sanitize_status(self._find_labeled_value(lines, 'Situação') or self._status_from_title_hint(candidate.title_hint))

        edital_numero, edital_data, edital_bruto = self._extract_edital(lines, text)
        inscricoes_raw = self._find_labeled_value(lines, 'Inscrições') or self._inscricoes_from_title_hint(candidate.title_hint)
        inscricao_inicio, inscricao_fim = self._extract_inscricao_interval(inscricoes_raw)

        edital_url, inscricao_url = self._extract_links(soup, candidate.detail_url)
        title = self._build_title(orgao, localidade_texto, candidate.title_hint, modalidade, title_parts.title)
        external_id = self._extract_external_id(candidate.detail_url)

        pdf_payload: dict[str, Any] = {
            'ok': False,
            'url': edital_url,
            'error': None,
            'pages': None,
            'text_hash': None,
        }
        pdf_fields: dict[str, Any] = {
            'cargo': None,
            'area': None,
            'cidade': None,
            'uf': None,
            'vagas': None,
            'salario_min': None,
            'salario_max': None,
            'escolaridade': None,
            'taxa': None,
            'prova_data': None,
            'raw_pdf_fields': {},
        }
        edital_pdf_excerpt = None
        pdf_extracted_at = None

        if edital_url:
            extraction = extract_pdf_text_from_url(edital_url, client=client)
            pdf_payload.update({
                'ok': extraction.ok,
                'error': extraction.error,
                'pages': extraction.pages,
                'text_hash': extraction.text_hash,
            })
            if extraction.ok and extraction.text:
                pdf_extracted_at = datetime.now(UTC)
                edital_pdf_excerpt = extraction.text[:4000]
                parsed_pdf = parse_ibfc_pdf(extraction.text, title=title, orgao=orgao)
                pdf_fields.update(parsed_pdf)

        cidade = pdf_fields.get('cidade') or self._infer_cidade(localidade_texto)
        uf = pdf_fields.get('uf') or self._infer_uf(localidade_texto)

        raw_payload = {
            'title_hint': candidate.title_hint,
            'title_parts': {
                'title': title_parts.title,
                'orgao': title_parts.orgao,
                'localidade_texto': title_parts.localidade_texto,
                'modalidade': title_parts.modalidade,
            },
            'fallback_headings': fallback_headings,
            'modalidade': modalidade,
            'orgao': orgao,
            'localidade_texto': localidade_texto,
            'situacao': situacao,
            'edital_bruto': edital_bruto,
            'inscricoes_bruto': inscricoes_raw,
            'detail_url': candidate.detail_url,
            'edital_url': edital_url,
            'inscricao_url': inscricao_url,
            'pdf': pdf_payload,
            'pdf_fields': pdf_fields.get('raw_pdf_fields') or {},
            'publications': parse_publications_from_dom(soup, candidate.detail_url, source='ibfc'),
        }

        resumo = self._build_summary(
            title,
            modalidade,
            situacao,
            inscricao_inicio,
            inscricao_fim,
            cargo=pdf_fields.get('cargo'),
            area=pdf_fields.get('area'),
            vagas=pdf_fields.get('vagas'),
            salario_min=pdf_fields.get('salario_min'),
            salario_max=pdf_fields.get('salario_max'),
        )

        return {
            'external_id': external_id,
            'banca': self.banca,
            'orgao': orgao,
            'titulo': title,
            'modalidade': modalidade,
            'cidade': cidade,
            'uf': uf,
            'cargo': pdf_fields.get('cargo'),
            'area': pdf_fields.get('area'),
            'status': situacao,
            'vagas': pdf_fields.get('vagas'),
            'salario_min': pdf_fields.get('salario_min'),
            'salario_max': pdf_fields.get('salario_max'),
            'escolaridade': pdf_fields.get('escolaridade'),
            'taxa': pdf_fields.get('taxa'),
            'prova_data': pdf_fields.get('prova_data'),
            'edital_numero': edital_numero,
            'edital_data': edital_data,
            'inscricao_inicio': inscricao_inicio,
            'inscricao_fim': inscricao_fim,
            'link_pagina': candidate.detail_url,
            'link_edital': edital_url,
            'link_inscricao': inscricao_url,
            'resumo': resumo,
            'raw_data': raw_payload,
            'edital_pdf_text_hash': pdf_payload.get('text_hash'),
            'edital_pdf_pages': pdf_payload.get('pages'),
            'edital_pdf_excerpt': edital_pdf_excerpt,
            'pdf_extracted_at': pdf_extracted_at,
            'content_hash': self._build_hash(raw_payload),
            'fetched_at': datetime.now(UTC),
        }

    def _parse_title_hint(self, title_hint: str | None) -> TitleParts:
        if not title_hint:
            return TitleParts()
        value = self._clean(title_hint)
        value = re.sub(r'\s+', ' ', value)

        core = re.split(r'\s+Edital\s+n?[º°o.]?\s*\d{1,4}/\d{4}\b', value, maxsplit=1, flags=re.IGNORECASE)[0]
        core = re.split(r'\s+Inscri[cç][oõ]es\s+de\s+', core, maxsplit=1, flags=re.IGNORECASE)[0]
        core = re.sub(r'\s+Inscri[cç][oõ]es\s+Abertas!?$', '', core, flags=re.IGNORECASE).strip(' -')

        localidade = None
        estado_match = re.search(r'\b(Estado\s+de\s+[A-Za-zÀ-ÿ ]+)$', core, flags=re.IGNORECASE)
        if estado_match:
            localidade = self._clean(estado_match.group(1))
            core_without_location = self._clean(core[:estado_match.start()].strip(' -'))
        else:
            city_match = re.search(r'\b([A-ZÁÉÍÓÚÂÊÔÃÕÇ][A-Za-zÀ-ÿ .\'’\-]{2,80}\s*[-/]\s*[A-Z]{2})$', core)
            if city_match:
                localidade = self._clean(city_match.group(1))
                core_without_location = self._clean(core[:city_match.start()].strip(' -'))
            else:
                core_without_location = core

        title = f'{core_without_location} - {localidade}' if localidade and core_without_location else core
        orgao = None
        if core_without_location:
            parts = [self._clean(part) for part in core_without_location.split(' - ') if self._clean(part)]
            if localidade:
                # When a location was already separated, the remaining string is the organization.
                # Example: "MGS - Minas Gerais Administração e Serviços S/A Estado de Minas Gerais".
                orgao = core_without_location
            elif len(parts) >= 3:
                # When there is no explicit location, IBFC cards commonly use:
                # "ORG - Organization name - Role/Program".
                orgao = ' - '.join(parts[:-1])
            elif len(parts) >= 1:
                orgao = parts[0]
        if not localidade and ' Estado de ' in core:
            before, after = core.split(' Estado de ', 1)
            orgao = self._clean(before.strip(' -')) or orgao
            localidade = f'Estado de {self._clean(after)}'
            title = f'{orgao} - {localidade}' if orgao else core

        modalidade = None
        lowered = value.lower()
        if 'processo seletivo' in lowered or 'jovem aprendiz' in lowered or 'formação para o mundo do trabalho' in lowered:
            modalidade = 'Processo Seletivo'
        elif 'concurso público' in lowered or 'concurso publico' in lowered:
            modalidade = 'Concurso Público'

        return TitleParts(title=title or None, orgao=orgao or None, localidade_texto=localidade, modalidade=modalidade)

    def _safe_headings(self, soup: BeautifulSoup) -> list[str]:
        headings = [self._clean(tag.get_text(' ', strip=True)) for tag in soup.select('h1, h2, h3, h4, h5')]
        return [value for value in headings if value and not self._is_section_label(value) and value.lower() != 'concursos']

    def _first_non_section(self, values: list[str]) -> str | None:
        for value in values:
            if not self._is_section_label(value):
                return value
        return None

    def _is_section_label(self, value: str | None) -> bool:
        if not value:
            return True
        normalized = self._normalize_key(value)
        return normalized in self.MENU_OR_SECTION_LABELS

    def _extract_edital(self, lines: list[str], text: str) -> tuple[str | None, datetime | None, str | None]:
        raw = self._find_labeled_value(lines, 'Edital', lookahead=3)
        if not raw:
            match = re.search(r'Edital\s*n?[º°o.]?\s*(\d{1,4}/\d{4})(?:\s+de\s+(\d{2}/\d{2}/\d{4}))?', text, flags=re.IGNORECASE)
            if not match:
                return None, None, None
            raw = ' '.join(part for part in match.groups() if part)

        number_match = re.search(r'(\d{1,4}/\d{4})', raw)
        date_match = re.search(r'(\d{2}/\d{2}/\d{4})', raw)
        if not date_match:
            for idx, line in enumerate(lines):
                if 'edital' in line.lower():
                    joined = ' '.join(lines[idx: idx + 5])
                    date_match = re.search(r'(\d{2}/\d{2}/\d{4})', joined)
                    break

        edital_numero = number_match.group(1) if number_match else self._clean(raw.replace(' de ', ' ')) or None
        edital_data = self._parse_date(date_match.group(1)) if date_match else None
        edital_bruto = self._clean(raw)
        return edital_numero, edital_data, edital_bruto

    def _extract_inscricao_interval(self, raw: str | None) -> tuple[datetime | None, datetime | None]:
        if not raw:
            return None, None
        interval_match = re.search(
            r'(\d{2}/\d{2}/\d{4}(?:\s+\d{2}:\d{2})?)\s+a\s+(\d{2}/\d{2}/\d{4}(?:\s+\d{2}:\d{2})?)',
            raw,
        )
        if not interval_match:
            return None, None
        return self._parse_datetime(interval_match.group(1)), self._parse_datetime(interval_match.group(2))

    def _extract_links(self, soup: BeautifulSoup, detail_url: str) -> tuple[str | None, str | None]:
        edital_url = extract_pdf_link(soup, detail_url)
        inscricao_url = None
        for anchor in soup.select('a[href]'):
            href = anchor.get('href', '').strip()
            label = self._clean(anchor.get_text(' ', strip=True)).lower()
            absolute = urljoin(detail_url, href)
            normalized_url = absolute.lower().split('?')[0]

            if not inscricao_url and any(token in label for token in ['inscrição online', 'inscricao online', 'área do candidato', 'area do candidato', 'inscrever']):
                inscricao_url = absolute
        return edital_url, inscricao_url

    def _is_valid_item(self, item: dict[str, Any]) -> bool:
        title = (item.get('titulo') or '').strip().lower()
        if not title or title == 'concurso sem título identificado':
            return False
        return bool(item.get('external_id') and item.get('orgao'))

    def _find_labeled_value(self, lines: list[str], label: str, *, lookahead: int = 2) -> str | None:
        label_key = self._normalize_key(label)
        for idx, line in enumerate(lines):
            line_key = self._normalize_key(line.rstrip(':'))
            if line_key == label_key or line_key.startswith(f'{label_key}:'):
                inline = line.split(':', 1)[1].strip() if ':' in line else ''
                candidates = [inline] if inline else []
                for next_line in lines[idx + 1: idx + 1 + lookahead]:
                    if self._looks_like_new_label(next_line) or self._is_section_label(next_line):
                        break
                    candidates.append(next_line)
                value = self._clean(' '.join(candidates))
                return value or None
        return None

    def _looks_like_new_label(self, line: str) -> bool:
        stripped = line.strip()
        if bool(re.match(r'^[A-Za-zÀ-ÿ ]{2,35}:$', stripped)):
            return True
        return self._normalize_key(stripped.rstrip(':')) in self.KNOWN_FIELD_LABELS

    def _sanitize_status(self, value: str | None) -> str | None:
        if not value:
            return None
        lowered = value.lower()
        known = [
            'inscrições abertas', 'inscricoes abertas', 'em andamento', 'finalizado', 'suspenso',
            'cancelado', 'homologado', 'previsto', 'encerrado',
        ]
        for status in known:
            if status in lowered:
                return status.replace('inscricoes', 'inscrições').title() if 'inscri' in status else status.capitalize()
        return self._clean(value)

    def _status_from_title_hint(self, title_hint: str | None) -> str | None:
        if not title_hint:
            return None
        lowered = title_hint.lower()
        if 'inscrições abertas' in lowered or 'inscricoes abertas' in lowered:
            return 'Inscrições abertas'
        if 'em andamento' in lowered:
            return 'Em andamento'
        return None

    def _inscricoes_from_title_hint(self, title_hint: str | None) -> str | None:
        if not title_hint:
            return None
        match = re.search(
            r'Inscri[cç][oõ]es\s+de\s+(\d{2}/\d{2}/\d{4}(?:\s+\d{2}:\d{2})?)\s+a\s+(\d{2}/\d{2}/\d{4}(?:\s+\d{2}:\d{2})?)',
            title_hint,
            flags=re.IGNORECASE,
        )
        if not match:
            return None
        return f'{match.group(1)} a {match.group(2)}'

    def _infer_modalidade(self, title_hint: str | None, text: str, headings: list[str]) -> str | None:
        combined = ' '.join([title_hint or '', text[:1500]]).lower()
        if 'jovem aprendiz' in combined or 'processo seletivo' in combined:
            return 'Processo Seletivo'
        if 'concurso público' in combined or 'concurso publico' in combined:
            return 'Concurso Público'
        for heading in headings:
            if not self._is_section_label(heading):
                return heading
        return None

    def _build_summary(
        self,
        title: str,
        modalidade: str | None,
        situacao: str | None,
        inscricao_inicio: datetime | None,
        inscricao_fim: datetime | None,
        *,
        cargo: str | None = None,
        area: str | None = None,
        vagas: int | None = None,
        salario_min: Any = None,
        salario_max: Any = None,
    ) -> str:
        parts = [title]
        if modalidade:
            parts.append(modalidade)
        if situacao:
            parts.append(f'Situação: {situacao}')
        if inscricao_inicio and inscricao_fim:
            parts.append(
                'Inscrições: '
                f'{inscricao_inicio.strftime("%d/%m/%Y %H:%M")} '
                f'a {inscricao_fim.strftime("%d/%m/%Y %H:%M")}'
            )
        if cargo:
            parts.append(f'Cargo: {cargo}')
        if area:
            parts.append(f'Área: {area}')
        if vagas:
            parts.append(f'Vagas: {vagas}')
        if salario_min and salario_max:
            if salario_min == salario_max:
                parts.append(f'Salário: R$ {salario_min}')
            else:
                parts.append(f'Salário: R$ {salario_min} a R$ {salario_max}')
        return ' | '.join(parts)

    def _infer_uf(self, localidade_texto: str | None) -> str | None:
        if not localidade_texto:
            return None
        normalized = localidade_texto.lower()
        state_map = {
            'acre': 'AC', 'alagoas': 'AL', 'amapá': 'AP', 'amazonas': 'AM', 'bahia': 'BA',
            'ceará': 'CE', 'distrito federal': 'DF', 'espírito santo': 'ES', 'goiás': 'GO',
            'maranhão': 'MA', 'mato grosso': 'MT', 'mato grosso do sul': 'MS', 'minas gerais': 'MG',
            'pará': 'PA', 'paraíba': 'PB', 'paraná': 'PR', 'pernambuco': 'PE', 'piauí': 'PI',
            'rio de janeiro': 'RJ', 'rio grande do norte': 'RN', 'rio grande do sul': 'RS',
            'rondônia': 'RO', 'roraima': 'RR', 'santa catarina': 'SC', 'são paulo': 'SP',
            'sergipe': 'SE', 'tocantins': 'TO',
        }
        for key, uf in state_map.items():
            if key in normalized:
                return uf
        brazil_ufs = set(state_map.values())
        for m in re.finditer(r'\b([A-Z]{2})\b', localidade_texto):
            cand = m.group(1).upper()
            if cand in brazil_ufs:
                return cand
        return None

    def _infer_cidade(self, localidade_texto: str | None) -> str | None:
        if not localidade_texto:
            return None
        cleaned = self._clean(localidade_texto)
        if self._is_section_label(cleaned):
            return None
        if cleaned.lower().startswith('estado de '):
            return None
        match = re.search(r'^(.*?)[-/]\s*[A-Z]{2}$', cleaned)
        if match:
            return self._clean(match.group(1)) or None
        if any(token in cleaned.lower() for token in ['minas gerais', 'brasil', 'editais', 'publicações', 'publicacoes']):
            return None
        return cleaned or None

    def _infer_orgao_from_title(self, title_hint: str | None) -> str | None:
        return self._parse_title_hint(title_hint).orgao

    def _build_title(
        self,
        orgao: str | None,
        localidade_texto: str | None,
        title_hint: str | None,
        modalidade: str | None,
        parsed_title: str | None = None,
    ) -> str:
        if parsed_title:
            return parsed_title
        if orgao and localidade_texto and not self._is_section_label(localidade_texto):
            return f'{orgao} - {localidade_texto}'
        if orgao and not self._is_section_label(orgao):
            return orgao
        if title_hint:
            parsed = self._parse_title_hint(title_hint)
            if parsed.title:
                return parsed.title
            return title_hint
        if modalidade and not self._is_section_label(modalidade):
            return modalidade
        return 'Concurso sem título identificado'

    def _extract_external_id(self, detail_url: str) -> str | None:
        match = re.search(r'/informacoes/(\d+)/?$', detail_url)
        return match.group(1) if match else None

    def _build_hash(self, payload: dict[str, Any]) -> str:
        raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str)
        return hashlib.sha256(raw.encode('utf-8')).hexdigest()

    def _headers(self) -> dict[str, str]:
        return {
            'User-Agent': (
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/146.0.0.0 Safari/537.36'
            )
        }

    def _text_lines(self, soup: BeautifulSoup) -> list[str]:
        for tag in soup.select('script, style, noscript'):
            tag.decompose()
        text = soup.get_text('\n', strip=True).replace('\xa0', ' ')
        return [line for line in (self._clean(line) for line in text.splitlines()) if line]

    def _clean(self, value: str | None) -> str:
        if not value:
            return ''
        return re.sub(r'\s+', ' ', value).strip()

    def _normalize_key(self, value: str | None) -> str:
        if not value:
            return ''
        value = self._clean(value).lower().rstrip(':')
        value = value.replace('ç', 'c').replace('ã', 'a').replace('õ', 'o')
        value = value.replace('á', 'a').replace('à', 'a').replace('â', 'a').replace('é', 'e')
        value = value.replace('ê', 'e').replace('í', 'i').replace('ó', 'o').replace('ô', 'o').replace('ú', 'u')
        return value

    def _parse_datetime(self, value: str) -> datetime | None:
        value = self._clean(value)
        for fmt in ('%d/%m/%Y %H:%M', '%d/%m/%Y'):
            try:
                parsed = datetime.strptime(value, fmt)
                return parsed.replace(tzinfo=UTC)
            except ValueError:
                continue
        return None

    def _parse_date(self, value: str) -> datetime | None:
        value = self._clean(value)
        try:
            return datetime.strptime(value, '%d/%m/%Y').replace(tzinfo=UTC)
        except ValueError:
            return None
