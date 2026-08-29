from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

from app.connectors.base import BaseConnector, CandidateItem
from app.connectors.common import (
    HEADERS,
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


@dataclass(slots=True)
class SourceDefinition:
    source_type: str
    name: str
    banca: str
    base_url: str
    list_urls: list[str]
    category: str = 'banca'  # 'banca' | 'institutional_selection'
    mode: str = 'open'       # 'open' | 'ongoing' | 'all'
    card_selectors: list[str] = field(default_factory=list)
    link_selectors: list[str] = field(default_factory=list)
    detail_url_patterns: list[str] = field(default_factory=list)
    status_selectors: list[str] = field(default_factory=list)
    blocked_terms: list[str] = field(default_factory=list)
    excluded_terms: list[str] = field(default_factory=list)
    browser_strategy: str = 'fallback'  # 'never' | 'fallback' | 'always'
    verify_ssl: bool = True
    max_candidates: int = 25
    frequency_minutes: int = 360
    default_uf: str | None = None
    default_cidade: str | None = None
    default_orgao: str | None = None


class ConfigurableHTMLConnector(BaseConnector):
    """Declarative, configurable HTML connector for standard banca portals."""

    def __init__(self, definition: SourceDefinition, base_url: str | None = None, list_url: str | None = None):
        self.definition = definition
        self._explicit_list_url = list_url is not None
        super().__init__(
            base_url=base_url or definition.base_url,
            list_url=list_url or (definition.list_urls[0] if definition.list_urls else definition.base_url),
        )
        self.banca = definition.banca
        self.category = definition.category
        self.mode = definition.mode
        self.browser_strategy = definition.browser_strategy
        self.verify_ssl = definition.verify_ssl
        self.max_candidates = definition.max_candidates

        # Extend blocked & excluded terms
        if definition.blocked_terms:
            self.blocked_keywords = self.blocked_keywords + tuple(definition.blocked_terms)
        if definition.excluded_terms:
            self.excluded_terms = self.excluded_terms + tuple(definition.excluded_terms)

    def _fetch_candidates(self) -> list[CandidateItem]:
        candidates: list[CandidateItem] = []
        seen: set[str] = set()

        urls_to_scan = [self.list_url] if self._explicit_list_url else (
            self.definition.list_urls if self.definition.list_urls else [self.list_url]
        )
        fetch_success = False
        last_fetch_exc = None
        total_evaluated_cards = 0
        total_closed_cards = 0
        explicit_empty_match = None

        for scan_url in urls_to_scan:
            try:
                html = self._fetch_html(scan_url)
                fetch_success = True
            except Exception as exc:
                last_fetch_exc = exc
                logger.warning('Failed to fetch list URL %s for %s: %s', scan_url, self.banca, exc)
                continue

            soup = BeautifulSoup(html, 'lxml')
            page_text = clean(soup.get_text(' ', strip=True)) or ''

            # Check for explicit empty state phrases on the page
            empty_patterns = [
                r'nenhum\s+(?:concurso|processo\s+seletivo|edital|registro|resultado|evento)\b',
                r'n[ãa]o\s+h[áa]\s+(?:concursos?|inscri[cç][oõ]es?|processos?\s+seletivos?|editais?|certames?|eventos?)\b',
                r'n[ãa]o\s+existem?\s+(?:concursos?|inscri[cç][oõ]es?|processos?\s+seletivos?|editais?|certames?)\b',
                r'sem\s+(?:concursos?|inscri[cç][oõ]es?|processos?\s+seletivos?|editais?|eventos?)\b',
                r'inscri[cç][oõ]es?\s+encerradas?\s+para\s+todos',
                r'nenhuma\s+inscri[cç][ãa]o\s+aberta',
                r'nenhum\s+evento\s+com\s+inscri[cç][oõ]es\s+abertas',
            ]
            for ep in empty_patterns:
                m = re.search(ep, page_text, flags=re.IGNORECASE)
                if m:
                    explicit_empty_match = (m.group(0), scan_url)
                    break

            # 1. First, check configured card selectors
            if self.definition.card_selectors:
                for card_sel in self.definition.card_selectors:
                    for card in soup.select(card_sel):
                        total_evaluated_cards += 1
                        card_text = clean(card.get_text(' ', strip=True)) or ''
                        if self._is_blocked(card_text.lower()):
                            continue
                        for anchor in card.select('a[href]'):
                            url = normalize_url(scan_url, anchor.get('href'))
                            if not url or url in seen or not self._same_domain_or_allowed(url):
                                continue
                            anchor_text = clean(anchor.get_text(' ', strip=True)) or ''
                            haystack = f'{anchor_text} {card_text} {url}'.lower()
                            if not self._looks_like_candidate(url, haystack):
                                continue
                            status_hint = self._infer_status(card_text)
                            if self.mode == 'open' and status_hint == 'Finalizado':
                                total_closed_cards += 1
                                continue
                            seen.add(url)
                            candidates.append(CandidateItem(
                                title_hint=card_text[:500],
                                detail_url=url,
                                status_hint=status_hint,
                            ))
                            if len(candidates) >= self.max_candidates:
                                return candidates

            # 2. General anchor discovery with pattern matching
            for anchor in soup.select('a[href]'):
                href = anchor.get('href')
                url = normalize_url(scan_url, href)
                if not url or url in seen or not self._same_domain_or_allowed(url):
                    continue

                own_text = clean(anchor.get_text(' ', strip=True)) or ''
                nearby = self._nearby_text(anchor) or own_text
                haystack = f'{own_text} {nearby} {url}'.lower()

                if self._is_blocked(haystack):
                    continue
                if self._looks_like_candidate(url, haystack):
                    total_evaluated_cards += 1
                    status_hint = self._infer_status(nearby)
                    if self.mode == 'open' and status_hint == 'Finalizado':
                        total_closed_cards += 1
                        continue
                    seen.add(url)
                    candidates.append(CandidateItem(
                        title_hint=nearby[:500] if nearby else own_text[:500],
                        detail_url=url,
                        status_hint=status_hint,
                    ))
                    if len(candidates) >= self.max_candidates:
                        break

        if not fetch_success and last_fetch_exc:
            raise last_fetch_exc

        if not candidates:
            if explicit_empty_match:
                self.mark_empty_evidence(
                    kind='explicit_text',
                    value=explicit_empty_match[0],
                    source=explicit_empty_match[1],
                )
            elif total_closed_cards > 0:
                self.mark_empty_evidence(
                    kind='evaluated_closed',
                    value=f'{total_closed_cards} certames evaluated; all registration windows closed',
                    source=self.list_url,
                )

        return candidates

    def _same_domain_or_allowed(self, url: str) -> bool:
        base_host = urlparse(self.base_url).netloc.replace('www.', '')
        host = urlparse(url).netloc.replace('www.', '')
        return not host or host == base_host or host.endswith(base_host)

    def _looks_like_candidate(self, url: str, haystack: str) -> bool:
        parsed = urlparse(url)
        path = parsed.path.rstrip('/').lower()
        normalized = url.rstrip('/').lower()
        list_urls = {value.rstrip('/').lower() for value in self.definition.list_urls}
        list_urls.add(self.list_url.rstrip('/').lower())
        list_urls.add(self.base_url.rstrip('/').lower())

        # A list/category page, section anchor or PDF is not a detail page.
        if normalized in list_urls or not path or parsed.fragment:
            return False
        if path.endswith('.pdf') or any(token in path for token in (
            '/category/', '/categoria/', '/tag/', '/noticias', '/noticia/',
            '/login', '/contato', '/institucional', '/politica-', '/termos',
        )):
            return False

        if self.definition.detail_url_patterns:
            if any(re.search(pat, url, flags=re.IGNORECASE) for pat in self.definition.detail_url_patterns):
                return True

        general_patterns = [
            r'/concursos?/[^/?#]{2,}', r'/processos?-seletivos?/[^/?#]{2,}',
            r'/edital/(?:ver/)?\d+', r'/informacoes/\d+', r'/detalhe/\d+',
            r'id=\d+', r'codigo=\d+', r'cod=\d+', r'codigoconcurso=\d+',
        ]
        if any(re.search(pat, url, flags=re.IGNORECASE) for pat in general_patterns):
            if any(kw in haystack for kw in ['concurso', 'processo seletivo', 'edital', 'seleção', 'selecao', 'inscrições', 'inscricoes', 'saiba mais', 'acessar']):
                return True

        return False

    def _nearby_text(self, anchor) -> str | None:
        node = anchor
        for _ in range(4):
            node = node.parent if node else None
            if node:
                val = clean(node.get_text(' ', strip=True))
                if val and len(val) > 15:
                    return val
        return clean(anchor.get_text(' ', strip=True))

    def _infer_status(self, text: str | None) -> str | None:
        lowered = (text or '').lower()
        if any(term in lowered for term in [
            'homologado', 'finalizado', 'encerrado', 'encerrada', 'encerradas',
            'concluído', 'concluido', 'resultado final', 'classificação final',
            'gabarito definitivo', 'concursos anteriores', 'concursos encerrados'
        ]):
            return 'Finalizado'
        if any(term in lowered for term in ['inscrições abertas', 'inscricoes abertas', 'inscrição aberta', 'inscricao aberta', 'aberto', 'abertos']):
            return 'Inscrições abertas'
        if any(term in lowered for term in ['em andamento', 'andamento']):
            return 'Em andamento'
        if any(term in lowered for term in ['em breve', 'previsto', 'novo concurso', 'próximo concurso']):
            return 'Inscrições em breve'
        return None

    def _is_blocked(self, haystack: str) -> bool:
        return any(kw in haystack for kw in self.blocked_keywords)

    def _parse_detail(self, candidate: CandidateItem, html: str, *, client: httpx.Client) -> dict[str, Any] | None:
        soup = BeautifulSoup(html, 'lxml')
        content_root = soup.select_one(
            'main, article, [role="main"], #content, #conteudo, .entry-content'
        )
        if content_root and len(text_lines(BeautifulSoup(str(content_root), 'lxml'))) < 10:
            content_root = None
        content_soup = BeautifulSoup(str(content_root or soup), 'lxml')
        lines = text_lines(content_soup)
        text = '\n'.join(lines)

        title = self._extract_title(lines, candidate.title_hint)
        # Apply exclusions to the contest content, not global navigation/footer.
        content_haystack = f'{title} {text[:5000]}'.lower()
        matched_exclusion = next((term for term in self.excluded_terms if term in content_haystack), None)
        if matched_exclusion:
            self._record_rejection(candidate.detail_url, f'excluded_term:{matched_exclusion}')
            return None
        orgao = self._extract_orgao(title, lines, candidate.title_hint) or self.definition.default_orgao
        cidade, uf = self._extract_city_uf(title, orgao, lines, text)
        if not cidade and self.definition.default_cidade:
            cidade = self.definition.default_cidade
        if not uf and self.definition.default_uf:
            uf = self.definition.default_uf

        modalidade = self._infer_modalidade(title, text)
        inicio, fim = parse_date_interval(text)
        status = status_from_dates(inicio, fim, fallback=candidate.status_hint)
        edital_url = extract_pdf_link(soup, candidate.detail_url)
        inscricao_url = self._extract_inscricao_link(soup, candidate.detail_url)
        cargo_candidates = self._extract_cargo_candidates(lines)
        area = classify_area_from_many(cargo_candidates, title, orgao, text[:1500])
        cargo = 'Vários cargos' if len(cargo_candidates) >= 2 else (cargo_candidates[0] if cargo_candidates else None)
        vagas = self._extract_vagas(text)
        salario_min, salario_max = self._extract_salarios(text)
        taxa = self._extract_taxa(text)
        external_id = self._extract_external_id(candidate.detail_url) or candidate.external_id

        pdf_payload, pdf_fields, excerpt, pdf_at = extract_pdf_fields_if_possible(edital_url, title=title, orgao=orgao, client=client)
        if pdf_fields:
            cargo = cargo or pdf_fields.get('cargo')
            area = area or pdf_fields.get('area')
            vagas = vagas or pdf_fields.get('vagas')
            salario_min = salario_min or pdf_fields.get('salario_min')
            salario_max = salario_max or pdf_fields.get('salario_max')
            taxa = taxa if taxa is not None else pdf_fields.get('taxa')

        if not self._is_valid_certame(title, orgao, cidade, uf, inicio, fim, edital_url, cargo_candidates, text):
            self._record_rejection(candidate.detail_url, 'quality_gate')
            return None

        if self.mode == 'open' and status in {'Finalizado', 'Encerrado'}:
            self.mark_empty_evidence('evaluated_closed', f'Status {status} on detail {candidate.detail_url}', candidate.detail_url)
            return None

        publications = parse_publications_from_dom(soup, candidate.detail_url, source=self.banca.lower())
        if not publications:
            publications = parse_publications_from_lines(lines, source=self.banca.lower())
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
            'prova_data': (pdf_fields or {}).get('prova_data') or self._extract_prova_data(text),
            'edital_numero': self._extract_edital_numero(title, text),
            'edital_data': self._extract_edital_data(text),
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

    def _record_rejection(self, url: str, reason: str) -> None:
        rejections = self.run_data.diagnostics_payload.setdefault('rejections', [])
        if len(rejections) < 10:
            rejections.append({'url': url, 'reason': reason})

    def _extract_title(self, lines: list[str], hint: str | None) -> str:
        bad = {
            'home', 'início', 'inicio', 'concursos', 'editais', 'inscrições abertas', 'inscricoes abertas',
            'em andamento', 'área do candidato', 'login', 'contato', 'notícias', 'noticias', 'menu',
            self.banca.lower(),
        }
        candidates = []
        if hint:
            candidates.extend(re.split(r'\s{2,}|\s\|\s|\s+»\s+', hint))
        candidates.extend(lines[:100])
        for raw in candidates:
            line = clean(raw)
            if not line:
                continue
            lowered = line.lower().strip()
            if lowered in bad or len(line) < 10 or len(line) > 220:
                continue
            if re.search(r'\b(?:concurso|processo seletivo|seleção pública|selecao publica|edital|prefeitura|c[âa]mara|secretaria|minist[eé]rio|defensoria|tribunal|pol[ií]cia|fundação|funda[cç][aã]o|conselho|guarda|hospital)\b', line, flags=re.IGNORECASE):
                return line
        return f'Processo Seletivo / Concurso {self.banca}'

    def _extract_orgao(self, title: str, lines: list[str], hint: str | None) -> str | None:
        for val in [title, hint] + lines[:150]:
            if not val:
                continue
            match = re.search(r'((?:PREFEITURA|C[ÂA]MARA|SECRETARIA|MINIST[ÉE]RIO|TRIBUNAL|DEFENSORIA|POL[ÍI]CIA|CORPO DE BOMBEIROS|UNIVERSIDADE|FUNDA[CÇ][AÃ]O|CONSELHO|HOSPITAL|INSTITUTO)[^\n]{3,150})', val, flags=re.IGNORECASE)
            if match:
                orgao = clean(match.group(1))
                if orgao:
                    return re.sub(r'\s*[-–]\s*(?:EDITAL|CONCURSO|PROCESSO SELETIVO).*$', '', orgao, flags=re.IGNORECASE).strip()
        return None

    def _extract_city_uf(self, title: str, orgao: str | None, lines: list[str], text: str):
        for val in [title, orgao] + lines[:100] + [text[:2500]]:
            cidade, uf = extract_city_uf(val)
            if cidade or uf:
                return cidade, uf
        return None, None

    def _infer_modalidade(self, title: str | None, text: str | None) -> str | None:
        haystack = f'{title or ""} {(text or "")[:1000]}'.lower()
        if 'processo seletivo simplificado' in haystack or 'pss' in haystack:
            return 'Processo Seletivo Simplificado'
        if 'processo seletivo' in haystack or 'seleção pública' in haystack or 'selecao publica' in haystack:
            return 'Processo Seletivo'
        if 'concurso público' in haystack or 'concurso publico' in haystack:
            return 'Concurso Público'
        return 'Concurso'

    def _extract_inscricao_link(self, soup: BeautifulSoup, base: str) -> str | None:
        for a in soup.select('a[href]'):
            t = clean(a.get_text(' ', strip=True)) or ''
            href = a.get('href')
            h = f'{t} {href or ""}'.lower()
            if any(k in h for k in ['inscrição', 'inscricao', 'inscreva-se', 'formulario de inscricao', 'faça sua inscrição']):
                return normalize_url(base, href)
        return None

    def _extract_cargo_candidates(self, lines: list[str]) -> list[str]:
        cargos: list[str] = []
        for line in lines[:150]:
            norm = (clean(line) or '').strip()
            if not norm or len(norm) < 4 or len(norm) > 150:
                continue
            if re.search(r'\b(assistente|agente|analista|auxiliar|técnico|tecnico|professor|médico|medico|enfermeiro|fiscal|contador|advogado|guarda|motorista|operador|engenheiro|farmac|psic[oó]logo|pedagogo|pesquisador|bolsista)\b', norm, flags=re.IGNORECASE):
                cargo = re.sub(r'^\d{1,4}\s*[.\-–]\s*', '', norm).strip()
                if cargo not in cargos and not any(bad in cargo.lower() for bad in ['download', 'resultado', 'gabarito', 'edital', 'recurso']):
                    cargos.append(cargo)
            if len(cargos) >= 50:
                break
        return cargos

    def _extract_vagas(self, text: str) -> int | None:
        for pat in [r'(?:total\s+de\s+vagas|quantidade\s+de\s+vagas|vagas\s+ofertadas)\D{0,30}(\d{1,5})', r'(\d{1,5})\s+vagas']:
            for m in re.finditer(pat, text, flags=re.IGNORECASE):
                val = int(m.group(1))
                context = text[max(0, m.start() - 80):m.end() + 30].lower()
                if 2000 <= val <= 2100 and any(term in context for term in ('edital', 'concurso', 'processo')):
                    continue
                if 1 <= val <= 50000:
                    return val
        return None

    def _extract_salarios(self, text: str) -> tuple[Decimal | None, Decimal | None]:
        vals: list[Decimal] = []
        for match in re.finditer(r'R\$\s*\d{1,3}(?:\.\d{3})*,\d{2}', text):
            ctx = text[max(0, match.start() - 60):match.end() + 60].lower()
            if any(k in ctx for k in ['remuneração', 'remuneracao', 'vencimento', 'salário', 'salario', 'subsídio', 'bolsa']):
                parsed = parse_money(match.group(0))
                if parsed and parsed >= Decimal('500'):
                    vals.append(parsed)
        if vals:
            return min(vals), max(vals)
        return None, None

    def _extract_taxa(self, text: str) -> Decimal | None:
        m = re.search(r'(?:taxa|inscrição|inscricao).{0,60}(R\$\s*\d{1,3}(?:\.\d{3})*,\d{2})', text, flags=re.IGNORECASE | re.DOTALL)
        if m:
            return parse_money(m.group(1))
        if re.search(r'taxa\s+de\s+inscri[cç][aã]o\s+gratuita|inscri[cç][aã]o\s+gratuita|isento\s+de\s+taxa', text, flags=re.IGNORECASE):
            return Decimal('0.00')
        return None

    def _extract_prova_data(self, text: str):
        m = re.search(r'(?:data\s+da\s+prova|provas?\s+objetivas?).{0,100}(\d{1,2}/\d{1,2}/\d{2,4})', text, flags=re.IGNORECASE | re.DOTALL)
        if m:
            from app.connectors.common import first_date
            return first_date(m.group(1))
        return None

    def _extract_edital_numero(self, title: str | None, text: str | None) -> str | None:
        for val in [title, text[:2500] if text else None]:
            if not val:
                continue
            m = re.search(r'Edital\s+n?[º°o.]?\s*(\d{1,4}/\d{4})', val, flags=re.IGNORECASE)
            if m:
                return m.group(1)
        return None

    def _extract_edital_data(self, text: str | None):
        if not text:
            return None
        m = re.search(r'Edital\s+n?[º°o.]?\s*\d{1,4}/\d{4}.{0,30}(\d{1,2}/\d{1,2}/\d{2,4})', text, flags=re.IGNORECASE | re.DOTALL)
        if m:
            from app.connectors.common import first_date
            return first_date(m.group(1))
        return None

    def _extract_external_id(self, url: str) -> str | None:
        return extract_external_id(url, [
            r'/informacoes/(\d+)', r'CodigoConcurso=(\d+)', r'cod=(\d+)',
            r'id=(\d+)', r'/concursos?/([^/?#]+)', r'/edital/(\d+)',
        ])
