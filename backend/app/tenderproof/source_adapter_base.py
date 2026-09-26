"""Source contracts shared by interactive review and continuous acquisition.

Registration certifies an implemented strategy, not the current completeness of
the portal. Every page carries its own evidence of truncation/empty/end state.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from html import escape
from typing import Protocol
from urllib.parse import parse_qs, urljoin, urlsplit, urlunsplit

from bs4 import BeautifulSoup

from app.tenderproof.contracts import DiscoveredCandidate, DocumentCandidate
from app.tenderproof.security import DEFAULT_ALLOWLIST, validate_destination
from app.tenderproof.source_parsers import (
    parse_listing_candidates, parse_document_candidates, confirm_identity, choose_edital,
)
from app.tenderproof.sources import IMESO_LISTING, imeso_candidates, imeso_documents, confirm_imeso_identity


@dataclass
class ListingPage:
    candidates: list[DiscoveredCandidate] = field(default_factory=list)
    next_urls: list[str] = field(default_factory=list)
    empty_evidence: str | None = None
    terminal_evidence: str | None = None
    truncated: bool = False
    diagnostics: list[str] = field(default_factory=list)


class SourcePageBlocked(ValueError):
    """Recognized challenge; cannot be mistaken for a legitimate empty page."""


class SourceAdapter(Protocol):
    source: str
    listing_urls: tuple[str, ...]
    allowed_hosts: tuple[str, ...]
    ready_selectors: tuple[str, ...]
    observed_url_paths: tuple[str, ...]
    document_identity_pattern: str

    def parse_listing(self, html: str, url: str, limit: int = 200) -> ListingPage: ...
    def validate_listing_url(self, url: str) -> None: ...
    def validate_detail_url(self, url: str) -> None: ...
    def candidate_from_url(self, url: str, title: str | None = None) -> DiscoveredCandidate: ...
    def confirm_identity(self, candidate: DiscoveredCandidate, html: str, url: str) -> None: ...
    def documents(self, html: str, candidate: DiscoveredCandidate) -> list[DocumentCandidate]: ...
    def validate_document_url(self, url: str, candidate: DiscoveredCandidate) -> None: ...
    def choose_document(self, docs: list[DocumentCandidate]) -> DocumentCandidate: ...
    def filter_observations(self, observed: list) -> list: ...


class HTMLSourceAdapter:
    """Reusable navigation/coverage rules; identity and documents are source hooks."""
    source: str
    listing_urls: tuple[str, ...]
    allowed_hosts: tuple[str, ...]
    listing_paths: tuple[str, ...]
    observed_url_paths: tuple[str, ...] = ()
    ready_selectors: tuple[str, ...] = ()
    empty_patterns: tuple[str, ...] = ()

    def validate_listing_url(self, url):
        validate_destination(url, allowlist=self.allowed_hosts)
        parts = urlsplit(url)
        expected = urlsplit(self.listing_urls[0])
        params = parse_qs(parts.query, keep_blank_values=True)
        if (parts.scheme != "https" or parts.hostname != expected.hostname or parts.path not in self.listing_paths
                or any(key not in ("page", "pagina", "p", "offset", "status") for key in params)
                or any(len(values) != 1 or not re.fullmatch(r"[A-Za-z0-9_-]{1,40}", values[0]) for values in params.values())):
            raise ValueError("URL fora das listagens registradas para a fonte")

    def _navigation(self, soup, url):
        links = []
        for anchor in soup.select("a[href]"):
            target = urljoin(url, str(anchor["href"]))
            parts = urlsplit(target)
            target = urlunsplit((parts.scheme, parts.netloc, parts.path, parts.query, ""))
            try:
                self.validate_listing_url(target)
            except ValueError:
                continue
            except Exception:
                continue
            if target != url and target not in links:
                links.append(target)
        return links

    def parse_listing(self, html, url, limit=200):
        self.validate_listing_url(url)
        if not 1 <= limit <= 10000:
            raise ValueError("limite de candidatos inválido")
        if len(html.encode("utf-8")) > 2 * 1024 * 1024:
            raise ValueError("listagem excede 2 MiB")
        soup = BeautifulSoup(html, "lxml")
        for node in list(soup.select("script, style, template, noscript, [hidden], [aria-hidden], [style], .hidden, .d-none")):
            if node.attrs is None:
                continue
            if (node.name in ("script", "style", "template", "noscript") or node.has_attr("hidden")
                    or str(node.get("aria-hidden", "")).lower() == "true"
                    or set(node.get("class", [])) & {"hidden", "d-none"}
                    or re.search(r"(?:display\s*:\s*none|visibility\s*:\s*hidden)", str(node.get("style", "")), re.I)):
                node.decompose()
        text = soup.get_text(" ", strip=True)
        if any(marker in text.casefold() for marker in ("verify you are human", "just a moment", "enable javascript and cookies", "checking your browser")):
            raise SourcePageBlocked("listagem bloqueada por challenge")
        candidates = self._candidates(str(soup), url, limit + 1)
        page = ListingPage(candidates=candidates[:limit], truncated=len(candidates) > limit,
                           next_urls=self._navigation(soup, url))
        for candidate in page.candidates:
            if candidate.source != self.source:
                raise ValueError("parser devolveu candidato de outra fonte")
            self.validate_detail_url(candidate.detail_url_observed)
        scope = soup.select_one("main, [role=main], #concursos, #editais") or soup
        if not candidates:
            for node in scope.select("p, h1, h2, h3, div.alert, td, li"):
                phrase = " ".join(node.get_text(" ", strip=True).split())
                if len(phrase) < 200 and any(re.fullmatch(pattern, phrase, re.I) for pattern in self.empty_patterns):
                    page.empty_evidence = phrase
                    page.terminal_evidence = "marcador explícito de vazio: " + phrase
                    break
        # An exhausted visible pager or explicit range is stronger evidence than
        # absence of links. It still describes this listing, not all source data.
        if not page.truncated and not page.empty_evidence:
            for next_node in scope.select(".pagination .next.disabled, .pagination .next[aria-disabled=true], [rel=next][aria-disabled=true], .pagination [aria-label='Próxima'][aria-disabled=true]"):
                page.terminal_evidence = "controle de próxima página explicitamente desabilitado"
                break
            match = re.search(r"(?:mostrando|exibindo)\s+(\d+)\s*(?:a|até|-)\s*(\d+)\s+de\s+(\d+)", scope.get_text(" ", strip=True), re.I)
            if match and 0 < int(match[1]) <= int(match[2]) == int(match[3]) and len(candidates) == int(match[2]) - int(match[1]) + 1:
                page.terminal_evidence = match[0]
        if page.truncated:
            page.diagnostics.append("limite de candidatos da página atingido; cobertura parcial")
        if not page.candidates and not page.empty_evidence:
            page.diagnostics.append("vazio não confirmado; preservar candidatos conhecidos")
        if not page.terminal_evidence and not page.next_urls:
            page.diagnostics.append("fim da listagem sem evidência explícita; cobertura desconhecida")
        return page

    def choose_document(self, docs):
        return choose_edital(docs)[0]

    def filter_observations(self, observed):
        result = []
        for item in observed:
            parts = urlsplit(item.url)
            if parts.hostname in self.allowed_hosts and any(parts.path.startswith(path) for path in self.observed_url_paths):
                result.append(item)
        return result


