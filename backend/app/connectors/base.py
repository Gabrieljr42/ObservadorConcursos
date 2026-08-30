from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

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
from app.publications import parse_publications_from_lines

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class CandidateItem:
    title_hint: str | None
    detail_url: str
    status_hint: str | None = None
    external_id: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class CrawlRunData:
    candidates_found: int = 0
    candidates_rejected: int = 0
    http_status: int | None = None
    browser_used: bool = False
    status: str = 'success'  # success | empty_valid | degraded | blocked | failed
    error_type: str | None = None
    error_message: str | None = None
    diagnostics_payload: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class CrawlResult:
    items: list[dict[str, Any]]
    run_data: CrawlRunData


class BaseConnector:
    """Base class for all portal crawlers in Observador de Concursos.

    Provides a robust 3-stage fetch pipeline:
    1. Fast standard HTTP (httpx)
    2. Resilient HTTP retry (custom headers, cookies, or permissive SSL for legacy sites)
    3. Headless Playwright Chromium fallback for bot guards (403, 429, Cloudflare, JS-rendered DOM)
    """

    banca: str = 'BASE'
    category: str = 'banca'  # 'banca' | 'institutional_selection'
    mode: str = 'open'       # 'open' | 'ongoing' | 'all'
    use_browser_fallback: bool = True
    browser_strategy: str = 'fallback'  # 'never' | 'fallback' | 'always'
    verify_ssl: bool = True
    max_candidates: int = 30
    timeout: float = 45.0
    # Empty is an assertion about the remote portal, not merely the absence of
    # parsed rows.  Connectors may opt in only after matching an explicit,
    # source-specific empty-state marker.
    confirmed_empty: bool = False
    empty_evidence: dict[str, Any] | None = None

    browser_fallback_statuses: set[int] = {
        401, 403, 406, 408, 409, 429, 500, 502, 503, 520, 521, 522, 523, 524,
    }

    blocked_keywords: tuple[str, ...] = (
        'notícia', 'noticias', 'política de privacidade', 'politica de privacidade',
        'cookies', 'fale conosco', 'contato', 'login', 'área do candidato',
        'area do candidato', 'segunda via', 'certificado', 'resultado de busca',
        'blog', 'apostila', 'instagram', 'facebook', 'twitter', 'youtube',
        'ouvidoria', 'transparência', 'transparencia', 'perguntas frequentes', 'faq',
    )

    excluded_terms: tuple[str, ...] = (
        'vestibular', 'vestibulares', 'residência médica', 'residencia medica',
        'processo seletivo - 2º semestre', 'transferência facultativa',
        'transferencia facultativa', 'reopção de curso', 'reopcao de curso',
    )

    def __init__(self, base_url: str, list_url: str | None = None):
        self.base_url = base_url.rstrip('/')
        self.list_url = list_url or self.base_url
        self.run_data = CrawlRunData()
        self.confirmed_empty = False
        self.empty_evidence = None

    def mark_empty_evidence(self, kind: str, value: str, source: str | None = None) -> None:
        """Explicitly record verified evidence that a portal is genuinely empty."""
        self.confirmed_empty = True
        self.empty_evidence = {
            'kind': kind,
            'value': str(value)[:500],
            'source': source or self.list_url,
        }
        self.run_data.diagnostics_payload['empty_evidence'] = self.empty_evidence

    def _http_client(self, *, verify: bool | None = None) -> httpx.Client:
        should_verify = self.verify_ssl if verify is None else verify
        return httpx.Client(
            timeout=self.timeout,
            follow_redirects=True,
            headers=dict(HEADERS),
            verify=should_verify,
        )

    @staticmethod
    def _response_text(response: httpx.Response) -> str:
        """Decode legacy Brazilian portals without silently keeping mojibake."""
        raw = response.content
        candidates: list[str] = []
        for encoding in ('utf-8', response.encoding, 'cp1252', 'latin-1'):
            if not encoding:
                continue
            try:
                value = raw.decode(encoding)
            except (LookupError, UnicodeDecodeError):
                continue
            if value not in candidates:
                candidates.append(value)
        if not candidates:
            return response.text

        def penalty(value: str) -> int:
            return (
                value.count('\ufffd') * 100
                + value.count('Ã') * 8
                + value.count('Â') * 5
                + value.count('�') * 100
            )

        return min(candidates, key=penalty)

    def _fetch_html(self, url: str, *, reason: str | None = None) -> str:
        """Fetch an HTML page using the 3-stage resilient pipeline."""
        if self.browser_strategy == 'always':
            self.run_data.browser_used = True
            return self._fetch_html_with_browser(url, reason=reason or 'browser_strategy=always')

        # Stage 1 & 2: HTTPX with defensive retries
        try:
            with self._http_client() as client:
                response = client.get(url)
                self.run_data.http_status = response.status_code
                if response.status_code in self.browser_fallback_statuses:
                    if self.browser_strategy != 'never' and self.use_browser_fallback:
                        self.run_data.browser_used = True
                        return self._fetch_html_with_browser(url, reason=f'HTTP {response.status_code}')
                response.raise_for_status()
                return self._response_text(response)
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code if exc.response is not None else None
            self.run_data.http_status = status
            if status in self.browser_fallback_statuses and self.browser_strategy != 'never' and self.use_browser_fallback:
                self.run_data.browser_used = True
                return self._fetch_html_with_browser(url, reason=f'HTTP {status}')
            raise
        except httpx.ConnectError as exc:
            message = str(exc).lower()
            if 'certificate_verify_failed' in message or 'certificate verify failed' in message:
                try:
                    with self._http_client(verify=False) as client:
                        response = client.get(url)
                        self.run_data.http_status = response.status_code
                        if response.status_code in self.browser_fallback_statuses and self.browser_strategy != 'never':
                            self.run_data.browser_used = True
                            return self._fetch_html_with_browser(url, reason=f'HTTP {response.status_code} after SSL retry')
                        response.raise_for_status()
                        return self._response_text(response)
                except Exception:
                    if self.browser_strategy != 'never' and self.use_browser_fallback:
                        self.run_data.browser_used = True
                        return self._fetch_html_with_browser(url, reason='SSL verification failed')
            if self.browser_strategy != 'never' and self.use_browser_fallback:
                self.run_data.browser_used = True
                return self._fetch_html_with_browser(url, reason=f'ConnectError: {message[:80]}')
            raise
        except httpx.TransportError as exc:
            message = str(exc).lower()
            if ('ssl' in message or 'tls' in message or 'forbidden' in message or '403' in message or 'timeout' in message) and self.browser_strategy != 'never' and self.use_browser_fallback:
                self.run_data.browser_used = True
                return self._fetch_html_with_browser(url, reason=message[:120])
            raise

    def _fetch_html_with_browser(self, url: str, *, reason: str | None = None) -> str:
        """Stage 3: Headless Chromium via Playwright."""
        if not self.use_browser_fallback and self.browser_strategy != 'always':
            raise RuntimeError(f'Browser fallback disabled for {url}. Reason: {reason or "unknown"}')

        self.run_data.browser_used = True
        logger.info('Launching browser fallback for %s (reason: %s)', url, reason)
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(
                headless=True,
                args=['--disable-dev-shm-usage', '--no-sandbox', '--disable-gpu'],
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
                    page.goto(url, wait_until='domcontentloaded', timeout=int(self.timeout * 1000))
                    page.wait_for_timeout(2500)
                except PlaywrightTimeoutError:
                    try:
                        page.wait_for_load_state('domcontentloaded', timeout=10000)
                    except PlaywrightTimeoutError:
                        pass
                html = page.content()
                context.close()
                if '<title>Just a moment...' in html or 'Attention Required! | Cloudflare' in html or 'challenge-platform' in html:
                    self.run_data.status = 'blocked'
                    self.run_data.error_type = 'CloudflareChallenge'
                    self.run_data.error_message = 'Site protected by Cloudflare challenge / WAF'
                    raise RuntimeError('Site protected by Cloudflare challenge / WAF')
                return html
            finally:
                browser.close()

    def _fetch_candidates(self) -> list[CandidateItem]:
        """Override in subclasses to discover certame candidate URLs."""
        raise NotImplementedError

    def _parse_detail(self, candidate: CandidateItem, html: str, *, client: httpx.Client) -> dict[str, Any] | None:
        """Override in subclasses to parse detail page HTML into a standardized concurso dict."""
        raise NotImplementedError

    def _is_valid_certame(
        self,
        title: str | None,
        orgao: str | None,
        cidade: str | None,
        uf: str | None,
        inicio: datetime | None,
        fim: datetime | None,
        edital_url: str | None,
        cargo_candidates: list[str],
        text: str,
    ) -> bool:
        """Quality Gate: ensure the item represents a real certame and not navigation/informational junk."""
        if not title:
            return False
        clean_title = (title or '').lower().strip()
        if len(clean_title) < 5 or clean_title in {
            'concurso', 'concursos', 'inscrições abertas', 'em andamento', 'home', 'início',
            'processo seletivo / concurso', 'concurso sem título identificado',
        }:
            return False
        if any(term in clean_title for term in [
            'para saber mais informações', 'legislações de concursos', 'área do candidato',
            'política de privacidade', 'fale conosco', 'resultados anteriores',
            'instruções para', 'clique aqui', 'arquivos disponíveis', 'termos de uso',
        ]):
            return False

        title_has_identity = bool(re.search(
            r'\b(?:prefeitura|c[âa]mara|secretaria|tribunal|conselho|universidade|instituto|funda[cç][aã]o|cons[oó]rcio|estado|munic[ií]pio)\b',
            clean_title,
        ))
        has_identity = bool(orgao or cidade or uf or title_has_identity)
        text_start = text[:5000].lower()
        has_evidence = bool(
            (inicio and fim)
            or edital_url
            or cargo_candidates
            or re.search(r'\bedital\s+(?:n[º°o.]?\s*)?\d{1,4}(?:/\d{4})?', text_start)
        )
        return bool(has_identity and has_evidence)

    def crawl_with_diagnostics(self) -> CrawlResult:
        """Execute full crawl workflow and collect diagnostic metadata."""
        items: list[dict[str, Any]] = []
        try:
            candidates = self._fetch_candidates()
            self.run_data.candidates_found = len(candidates)

            with self._http_client() as client:
                for candidate in candidates:
                    try:
                        html = self._fetch_html(candidate.detail_url)
                        parsed = self._parse_detail(candidate, html, client=client)
                        if parsed:
                            items.append(parsed)
                        else:
                            self.run_data.candidates_rejected += 1
                    except Exception as item_exc:
                        logger.warning('Failed to parse candidate %s: %s', candidate.detail_url, item_exc)
                        self.run_data.candidates_rejected += 1
                        continue

            if not items:
                if self.confirmed_empty and self.empty_evidence:
                    self.run_data.status = 'empty_valid'
                    self.run_data.diagnostics_payload['empty_evidence'] = self.empty_evidence
                else:
                    # Zero candidates can mean a changed selector, a JS-only
                    # page, a redirect, or a genuinely empty portal.  Without
                    # explicit evidence it must never be reported as valid.
                    self.run_data.status = 'degraded'
                    self.run_data.diagnostics_payload['empty_evidence'] = None
                    if self.run_data.candidates_found == 0:
                        self.run_data.error_type = 'UnconfirmedEmpty'
                        self.run_data.error_message = (
                            'No candidates found and no explicit empty-state evidence was recorded'
                        )
                    elif self.run_data.candidates_rejected:
                        self.run_data.error_type = 'AllCandidatesRejected'
                        self.run_data.error_message = (
                            f'All {self.run_data.candidates_found} candidates were rejected by the quality gate'
                        )
            else:
                self.run_data.status = 'success'

        except httpx.HTTPStatusError as exc:
            status_code = exc.response.status_code if exc.response is not None else 0
            if status_code in (401, 403, 429):
                self.run_data.status = 'blocked'
            else:
                self.run_data.status = 'failed'
            self.run_data.error_type = exc.__class__.__name__
            self.run_data.error_message = str(exc)
        except Exception as exc:
            if self.run_data.status != 'blocked':
                self.run_data.status = 'failed'
                self.run_data.error_type = exc.__class__.__name__
            self.run_data.error_message = str(exc)

        return CrawlResult(items=items, run_data=self.run_data)

    def crawl(self) -> list[dict[str, Any]]:
        """Legacy entrypoint conforming to original CrawlService contract."""
        result = self.crawl_with_diagnostics()
        if result.run_data.status == 'failed' and result.run_data.error_message:
            raise RuntimeError(f'{result.run_data.error_type}: {result.run_data.error_message}')
        return result.items
