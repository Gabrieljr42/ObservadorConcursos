from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from urllib.parse import urlparse

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

import httpx
from bs4 import BeautifulSoup

from app.publications import parse_publications_from_lines
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


@dataclass(slots=True)
class GenericCandidate:
    title_hint: str | None
    detail_url: str
    status_hint: str | None = None


class GenericBancaConnector:
    """Defensive connector for relatively simple official banca portals.

    The connector deliberately prefers *not* saving anything over saving noisy
    navigation text. It is used for the first MVP pass of new bancas; once a
    banca proves valuable, it can receive a dedicated parser.
    """

    banca = 'GENERICA'
    mode = 'open'
    candidate_keywords = ('concurso', 'processo seletivo', 'seleção pública', 'selecao publica', 'edital')
    blocked_keywords = (
        'notícia', 'noticias', 'política de privacidade', 'cookies', 'fale conosco',
        'contato', 'login', 'área do candidato', 'area do candidato', 'segunda via',
        'certificado', 'resultado de busca', 'blog', 'apostila', 'instagram', 'facebook',
    )
    excluded_terms = (
        'vestibular', 'medicina', 'residência médica', 'residencia medica', 'processo seletivo - 2º semestre',
    )
    detail_url_patterns = (
        r'/informacoes/\d+',
        r'/concurso',
        r'/concursos/',
        r'/edital',
        r'codigoconcurso=',
        r'id=',
    )
    max_candidates = 20
    use_browser_fallback = True
    browser_fallback_statuses = {401, 403, 406, 408, 409, 429, 500, 502, 503, 520, 521, 522, 523, 524}

    def __init__(self, base_url: str, list_url: str | None = None):
        self.base_url = base_url.rstrip('/')
        self.list_url = list_url or self.base_url

    def crawl(self) -> list[dict[str, Any]]:
        candidates = self._fetch_candidates()
        concursos: list[dict[str, Any]] = []
        with self._http_client() as client:
            for candidate in candidates:
                try:
                    html = self._fetch_html(candidate.detail_url)
                    parsed = self._parse_detail(candidate, html, client=client)
                    if parsed:
                        concursos.append(parsed)
                except Exception:
                    # Keep source robust; one broken card must not break the whole crawl.
                    continue
        return concursos

    def _fetch_candidates(self) -> list[GenericCandidate]:
        html = self._fetch_html(self.list_url)
        soup = BeautifulSoup(html, 'lxml')
        candidates: list[GenericCandidate] = []
        seen: set[str] = set()

        for anchor in soup.select('a[href]'):
            url = normalize_url(self.list_url, anchor.get('href'))
            if not url:
                continue
            if not self._same_domain_or_allowed(url):
                continue
            if url in seen:
                continue

            own_text = clean(anchor.get_text(' ', strip=True)) or ''
            nearby = self._nearby_text(anchor) or own_text
            haystack = f'{own_text} {nearby} {url}'.lower()
            if self._is_blocked(haystack):
                continue
            if not self._looks_like_candidate_url(url, haystack):
                continue

            status_hint = self._infer_status(nearby)
            if self.mode == 'open' and status_hint in {'Finalizado', 'Homologado'}:
                continue
            if self.mode == 'open' and any(term in haystack for term in self.excluded_terms):
                continue

            seen.add(url)
            candidates.append(GenericCandidate(title_hint=nearby[:700] if nearby else own_text[:700], detail_url=url, status_hint=status_hint))
            if len(candidates) >= self.max_candidates:
                break
        return candidates

    def _http_client(self, *, verify: bool = True) -> httpx.Client:
        return httpx.Client(
            timeout=60.0,
            follow_redirects=True,
            headers=HEADERS,
            verify=verify,
        )

    def _fetch_html(self, url: str) -> str:
        """Fetch an HTML page, retrying with Chromium for bot/403-like blocks.

        The crawler should never fail a whole source just because a site rejects
        a simple HTTP request. The normal path is fast `httpx`; if the server
        returns 403/429/etc. or has a broken certificate, we try a browser-like
        fetch with Playwright/Chromium. If Chromium also fails, the exception is
        propagated to the service, which will report the source as failed instead
        of crashing the whole `/crawl-all/sync` run.
        """
        try:
            with self._http_client() as client:
                response = client.get(url)
                if response.status_code in self.browser_fallback_statuses:
                    return self._fetch_html_with_browser(url, reason=f'HTTP {response.status_code}')
                response.raise_for_status()
                return response.text
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code if exc.response is not None else None
            if status in self.browser_fallback_statuses:
                return self._fetch_html_with_browser(url, reason=f'HTTP {status}')
            raise
        except httpx.ConnectError as exc:
            message = str(exc).lower()
            if 'certificate_verify_failed' in message or 'certificate verify failed' in message:
                try:
                    # Some older public banca portals have incomplete certificate
                    # chains. Retrying without verification is acceptable here
                    # because this is only used for public scraping, not auth.
                    with self._http_client(verify=False) as client:
                        response = client.get(url)
                        if response.status_code in self.browser_fallback_statuses:
                            return self._fetch_html_with_browser(url, reason=f'HTTP {response.status_code} after SSL retry')
                        response.raise_for_status()
                        return response.text
                except Exception:
                    return self._fetch_html_with_browser(url, reason='SSL verification failed')
            raise
        except httpx.TransportError as exc:
            message = str(exc).lower()
            if 'ssl' in message or 'tls' in message or 'forbidden' in message or '403' in message:
                return self._fetch_html_with_browser(url, reason=message[:120])
            raise

    def _fetch_html_with_browser(self, url: str, *, reason: str | None = None) -> str:
        if not self.use_browser_fallback:
            raise RuntimeError(f'Browser fallback disabled for {url}. Reason: {reason or "unknown"}')

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                headless=True,
                args=['--disable-dev-shm-usage', '--no-sandbox'],
            )
            try:
                context = browser.new_context(
                    user_agent=HEADERS.get('User-Agent'),
                    locale='pt-BR',
                    timezone_id='America/Sao_Paulo',
                    ignore_https_errors=True,
                    extra_http_headers={
                        'Accept-Language': HEADERS.get('Accept-Language', 'pt-BR,pt;q=0.9'),
                        'Accept': HEADERS.get('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'),
                    },
                )
                page = context.new_page()
                try:
                    page.goto(url, wait_until='networkidle', timeout=45000)
                except PlaywrightTimeoutError:
                    # Some sites keep analytics/chat requests open forever. DOM
                    # content is usually enough for our parser.
                    try:
                        page.wait_for_load_state('domcontentloaded', timeout=10000)
                    except PlaywrightTimeoutError:
                        pass
                html = page.content()
                context.close()
                return html
            finally:
                browser.close()

    def _same_domain_or_allowed(self, url: str) -> bool:
        base_host = urlparse(self.base_url).netloc.replace('www.', '')
        host = urlparse(url).netloc.replace('www.', '')
        return not host or host == base_host or host.endswith(base_host)

    def _looks_like_candidate_url(self, url: str, haystack: str) -> bool:
        if any(re.search(pattern, url, flags=re.IGNORECASE) for pattern in self.detail_url_patterns):
            if any(keyword in haystack for keyword in self.candidate_keywords) or any(x in haystack for x in ('mais informações', 'mais informacoes', 'acessar', 'saiba mais', 'inscrição', 'inscricao')):
                return True
        # Some WordPress-like portals use semantic slugs without a predictable path.
        if any(keyword in haystack for keyword in self.candidate_keywords) and any(x in haystack for x in ('inscrições abertas', 'inscricoes abertas', 'em andamento', 'edital nº', 'edital n')):
            return True
        return False

    def _nearby_text(self, anchor) -> str | None:
        parents = []
        node = anchor
        for _ in range(5):
            node = node.parent if node else None
            if node:
                parents.append(node)
        for parent in parents:
            value = clean(parent.get_text(' ', strip=True))
            if value and len(value) > 10:
                return value
        return clean(anchor.get_text(' ', strip=True))

    def _infer_status(self, text: str | None) -> str | None:
        lowered = (text or '').lower()
        if 'homologado' in lowered or 'finalizado' in lowered or 'encerrado' in lowered:
            return 'Finalizado'
        if 'inscrições abertas' in lowered or 'inscricoes abertas' in lowered or 'inscrição aberta' in lowered or 'inscricao aberta' in lowered:
            return 'Inscrições abertas'
        if 'em andamento' in lowered:
            return 'Em andamento'
        if 'novo concurso' in lowered or 'próximo concurso' in lowered or 'proximo concurso' in lowered:
            return 'Previsto'
        return None

    def _parse_detail(self, candidate: GenericCandidate, html: str, *, client: httpx.Client) -> dict[str, Any] | None:
        soup = BeautifulSoup(html, 'lxml')
        lines = text_lines(soup)
        text = '\n'.join(lines)
        if self._is_blocked(text[:3000].lower()) or any(term in text[:4000].lower() for term in self.excluded_terms):
            return None

        title = self._extract_title(lines, candidate.title_hint)
        orgao = self._extract_orgao(title, lines, candidate.title_hint)
        cidade, uf = self._extract_city_uf(title, orgao, lines, text)
        modalidade = self._infer_modalidade(title, text)
        inicio, fim = parse_date_interval(text)
        status = status_from_dates(inicio, fim, fallback=candidate.status_hint or self._infer_status(text[:2000]) or 'Em andamento')
        edital_url = extract_pdf_link(soup, candidate.detail_url)
        inscricao_url = self._extract_inscricao_link(soup, candidate.detail_url)
        cargo_candidates = self._extract_cargo_candidates(lines)
        area = classify_area_from_many(cargo_candidates, title, orgao, text[:1500])
        cargo = 'Vários cargos' if len(cargo_candidates) >= 2 else (cargo_candidates[0] if cargo_candidates else None)
        vagas = self._extract_vagas(text, lines)
        salario_min, salario_max = self._extract_salarios(text)
        taxa = self._extract_taxa(text)
        external_id = self._extract_external_id(candidate.detail_url)

        pdf_payload, pdf_fields, excerpt, pdf_at = extract_pdf_fields_if_possible(edital_url, title=title, orgao=orgao, client=client)
        if pdf_fields:
            cargo = cargo or pdf_fields.get('cargo')
            area = area or pdf_fields.get('area')
            vagas = vagas or pdf_fields.get('vagas')
            salario_min = salario_min or pdf_fields.get('salario_min')
            salario_max = salario_max or pdf_fields.get('salario_max')
            taxa = taxa if taxa is not None else pdf_fields.get('taxa')

        # Defensive persistence gate: avoid saving navigation/informational pages.
        if not self._is_valid_certame(title, orgao, cidade, uf, inicio, fim, edital_url, cargo_candidates, text):
            return None

        publications = parse_publications_from_lines(lines, source=self.banca.lower())
        raw_payload = {
            'title_hint': candidate.title_hint,
            'detail_url': candidate.detail_url,
            'lines_sample': lines[:140],
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

    def _extract_title(self, lines: list[str], hint: str | None) -> str:
        bad = {
            'home', 'início', 'inicio', 'concursos', 'editais', 'inscrições abertas', 'inscricoes abertas',
            'em andamento', 'resultados disponíveis', 'resultados disponiveis', 'área do candidato', 'area do candidato',
            self.banca.lower(), 'login', 'contato', 'notícias', 'noticias', 'menu'
        }
        candidates = []
        if hint:
            candidates.extend(re.split(r'\s{2,}|\s\|\s|\s+»\s+', hint))
        candidates.extend(lines[:120])
        for raw in candidates:
            line = clean(raw)
            if not line:
                continue
            lowered = line.lower().strip()
            if lowered in bad or len(line) < 12 or len(line) > 220:
                continue
            if re.search(r'\b(?:concurso|processo seletivo|seleção pública|selecao publica|edital|prefeitura|c[âa]mara|secretaria|minist[eé]rio|defensoria|tribunal|pol[ií]cia|corpo de bombeiros)\b', line, flags=re.IGNORECASE):
                return line
        return f'Concurso {self.banca}'

    def _extract_orgao(self, title: str, lines: list[str], hint: str | None) -> str | None:
        for value in [title, hint] + lines[:160]:
            if not value:
                continue
            match = re.search(r'((?:PREFEITURA|C[ÂA]MARA|SECRETARIA|MINIST[ÉE]RIO|TRIBUNAL|DEFENSORIA|POL[ÍI]CIA|CORPO DE BOMBEIROS|UNIVERSIDADE|FUNDA[CÇ][AÃ]O|CONSELHO)[^\n]{3,160})', value, flags=re.IGNORECASE)
            if match:
                orgao = clean(match.group(1))
                if orgao:
                    orgao = re.sub(r'\s*[-–]\s*(?:EDITAL|CONCURSO|PROCESSO SELETIVO).*$','', orgao, flags=re.IGNORECASE).strip()
                    return orgao
        return None

    def _extract_city_uf(self, title: str, orgao: str | None, lines: list[str], text: str):
        for value in [title, orgao] + lines[:120] + [text[:2500]]:
            cidade, uf = extract_city_uf(value)
            if cidade or uf:
                return cidade, uf
        return None, None

    def _infer_modalidade(self, title: str | None, text: str | None) -> str | None:
        haystack = f'{title or ""} {(text or "")[:1000]}'.lower()
        if 'processo seletivo simplificado' in haystack:
            return 'Processo Seletivo Simplificado'
        if 'processo seletivo' in haystack or 'seleção pública' in haystack or 'selecao publica' in haystack:
            return 'Processo Seletivo'
        if 'concurso público' in haystack or 'concurso publico' in haystack:
            return 'Concurso Público'
        return 'Concurso'

    def _extract_inscricao_link(self, soup: BeautifulSoup, base: str) -> str | None:
        for anchor in soup.select('a[href]'):
            text = clean(anchor.get_text(' ', strip=True)) or ''
            href = anchor.get('href')
            haystack = f'{text} {href or ""}'.lower()
            if any(term in haystack for term in ['inscrição', 'inscricao', 'candidato', 'cadastro', 'realizar inscrição', 'realizar inscricao']):
                return normalize_url(base, href)
        return None

    def _extract_cargo_candidates(self, lines: list[str]) -> list[str]:
        cargos: list[str] = []
        collecting = False
        for line in lines:
            norm = (clean(line) or '').strip()
            if not norm:
                continue
            lower = norm.lower()
            if lower in {'vagas', 'cargo', 'cargos', 'quadro de vagas'}:
                collecting = True
                continue
            if lower in {'publicações', 'publicacoes', 'resultado', 'gabarito', 'contato', 'sobre', 'notícias', 'noticias'}:
                if collecting:
                    break
            if collecting or re.match(r'^\d{1,4}\s*[.\-–]\s*\S', norm):
                if self._looks_like_cargo_line(norm):
                    cargo = re.sub(r'^\d{1,4}\s*[.\-–]\s*', '', norm).strip()
                    if cargo not in cargos:
                        cargos.append(cargo)
            if len(cargos) >= 80:
                break
        return cargos

    def _looks_like_cargo_line(self, value: str) -> bool:
        lowered = value.lower()
        if len(value) < 4 or len(value) > 180:
            return False
        if any(term in lowered for term in ['download', 'recurso', 'homologação', 'homologacao', 'resultado', 'gabarito', 'formulário', 'formulario', 'laudo médico', 'laudo medico']):
            return False
        if re.fullmatch(r'\d{1,2}/\d{1,2}/\d{2,4}', value):
            return False
        return bool(re.search(r'(assistente|agente|analista|auxiliar|técnico|tecnico|professor|médico|medico|enfermeiro|fiscal|contador|advogado|guarda|motorista|operador|engenheiro|farmac|psic[oó]logo|administrativo|social|sa[uú]de|pedagogo)', value, flags=re.IGNORECASE))

    def _extract_vagas(self, text: str, lines: list[str]) -> int | None:
        # Only trust explicit total lines or clearly tabular counts. Avoid a lone 1.
        for pattern in [r'(?:total\s+de\s+vagas|quantidade\s+de\s+vagas|vagas\s+ofertadas)\D{0,30}(\d{2,5})', r'(\d{2,5})\s+vagas']:
            match = re.search(pattern, text, flags=re.IGNORECASE)
            if match:
                return int(match.group(1))
        return None

    def _extract_salarios(self, text: str) -> tuple[Decimal | None, Decimal | None]:
        values: list[Decimal] = []
        for match in re.finditer(r'R\$\s*\d{1,3}(?:\.\d{3})*,\d{2}|\d{1,3}(?:\.\d{3})*,\d{2}', text):
            context = text[max(0, match.start() - 80):match.end() + 80].lower()
            if not any(term in context for term in ['remuneração', 'remuneracao', 'vencimento', 'salário', 'salario', 'subsídio', 'subsidio']):
                continue
            parsed = parse_money(match.group(0))
            if parsed and parsed >= Decimal('1000'):
                values.append(parsed)
        if values:
            return min(values), max(values)
        return None, None

    def _extract_taxa(self, text: str) -> Decimal | None:
        match = re.search(r'(?:taxa|inscrição|inscricao).{0,80}(R\$\s*\d{1,3}(?:\.\d{3})*,\d{2})', text, flags=re.IGNORECASE | re.DOTALL)
        if match:
            return parse_money(match.group(1))
        if re.search(r'taxa\s+de\s+inscri[cç][aã]o\s+gratuita|inscri[cç][aã]o\s+gratuita', text, flags=re.IGNORECASE):
            return Decimal('0.00')
        return None

    def _extract_prova_data(self, text: str):
        match = re.search(r'(?:data\s+da\s+prova|provas?\s+objetivas?).{0,120}(\d{1,2}/\d{1,2}/\d{2,4})', text, flags=re.IGNORECASE | re.DOTALL)
        if match:
            from app.connectors.common import first_date
            return first_date(match.group(1))
        return None

    def _extract_edital_numero(self, title: str | None, text: str | None) -> str | None:
        for value in [title, text[:2500] if text else None]:
            if not value:
                continue
            match = re.search(r'Edital\s+n?[º°o.]?\s*(\d{1,4}/\d{4})', value, flags=re.IGNORECASE)
            if match:
                return match.group(1)
        return None

    def _extract_edital_data(self, text: str | None):
        if not text:
            return None
        match = re.search(r'Edital\s+n?[º°o.]?\s*\d{1,4}/\d{4}.{0,30}(\d{1,2}/\d{1,2}/\d{2,4})', text, flags=re.IGNORECASE | re.DOTALL)
        if match:
            from app.connectors.common import first_date
            return first_date(match.group(1))
        return None

    def _extract_external_id(self, url: str) -> str | None:
        return extract_external_id(url, [r'/informacoes/(\d+)', r'CodigoConcurso=(\d+)', r'cod=(\d+)', r'id=(\d+)', r'/concursos?/([^/?#]+)'])

    def _is_blocked(self, haystack: str) -> bool:
        return any(term in haystack for term in self.blocked_keywords)

    def _is_valid_certame(self, title: str | None, orgao: str | None, cidade: str | None, uf: str | None, inicio, fim, edital_url: str | None, cargo_candidates: list[str], text: str) -> bool:
        lowered_title = (title or '').lower()
        if not title or lowered_title in {'concurso', 'concursos', 'ibgp concursos', 'instituto aocp', 'idecan', 'consulplan'}:
            return False
        if any(term in lowered_title for term in ['para saber mais informações', 'legislações de concursos', 'legislacoes de concursos', 'área do candidato', 'area do candidato']):
            return False
        has_identity = bool(orgao or cidade or uf)
        has_dates_or_doc = bool((inicio and fim) or edital_url or cargo_candidates)
        return has_identity and has_dates_or_doc


class AOCPConnector(GenericBancaConnector):
    banca = 'Instituto AOCP'
    candidate_keywords = GenericBancaConnector.candidate_keywords + ('mpgo', 'ebserh', 'prefeitura')


class IDECANConnector(GenericBancaConnector):
    banca = 'IDECAN'
    # IDECAN has two public portals. Keep same parser for both.


class ConsulplanConnector(GenericBancaConnector):
    banca = 'CONSULPLAN'
    candidate_keywords = GenericBancaConnector.candidate_keywords + ('prefeitura', 'conselho', 'guarda civil')


class FumarcConnector(GenericBancaConnector):
    banca = 'FUMARC'
    # FUMARC website varies a lot; this connector is intentionally defensive.
    max_candidates = 10
