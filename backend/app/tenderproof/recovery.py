"""TenderProof: bounded declarative snapshot execution, never publication.

Snapshots must be assembled by application adapters; document identity/evidence
must come from their independent document validation, never from page labels.
This executor does not fetch URLs or execute code from proposals or content.
"""
from __future__ import annotations

from app.tenderproof.pdf_header import has_pdf_header

import hashlib
import re
import time
from dataclasses import dataclass
from typing import Literal
from urllib.parse import urljoin, urlsplit, urlunsplit

from bs4 import BeautifulSoup
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.tenderproof.security import validate_destination


class Strategy(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    schema_version: Literal[1] = 1
    source: Literal["ibgp", "imeso"] = "ibgp"
    operations: tuple[Literal["locate_cards", "navigate_details", "identify_documents"], ...] = (
        "locate_cards", "navigate_details", "identify_documents",
    )
    cards: tuple[str, ...] = Field(min_length=1, max_length=3)
    details: tuple[str, ...] = Field(min_length=1, max_length=3)
    documents: tuple[str, ...] = Field(min_length=1, max_length=3)

    @field_validator("operations")
    @classmethod
    def fixed_operations(cls, value):
        if value != ("locate_cards", "navigate_details", "identify_documents"):
            raise ValueError("operation order is fixed")
        return value

    @field_validator("cards", "details", "documents")
    @classmethod
    def simple_selectors(cls, values):
        if any(not re.fullmatch(r"[.#]?[a-zA-Z][a-zA-Z0-9_-]{0,63}", s) for s in values):
            raise ValueError("only bounded simple tag, class or id selectors")
        return values

    @property
    def digest(self):
        return hashlib.sha256(self.model_dump_json().encode()).hexdigest()


@dataclass(frozen=True)
class RecoveryPolicy:
    """Trusted application policy; deliberately absent from proposal schema."""
    hosts: tuple[str, ...]
    expected_identity: str
    max_bytes: int = 131072
    max_steps: int = 20
    max_seconds: float = 2.0
    max_cards: int = 5


@dataclass(frozen=True)
class VerifiedDocument:
    identity: str
    kind: str
    content: bytes
    sha256: str
    page_text: str
    quote: str
    physical_page: int = 1


@dataclass(frozen=True)
class Snapshot:
    url: str
    html: str
    pages: dict[str, str]
    documents: dict[str, VerifiedDocument]
    expected_count: int | None = None
    legitimate_empty: bool = False  # trusted source check, not proposal assertion
    network_error: bool = False
    blocked: bool = False
    is_synthetic: bool = True
    redirects: tuple[str, ...] = ()


def safe_excerpt(value: str) -> str:
    value = value[:8192]
    value = re.sub(r"(?i)(bearer\s+)\S+", r"\1[REDACTED]", value)
    value = re.sub(r"(?i)(api[_-]?key|token|password|secret|authorization)\s*[:=]\s*[^\s<>&]+", r"\1=[REDACTED]", value)
    value = re.sub(r"(?i)(https?://)[^/\s]+@", r"\1[REDACTED]@", value)
    value = re.sub(r"(https?://[^\s?<>]+)\?[^\s<>]+", r"\1?[REDACTED]", value)
    return value[:2000]


def run_strategy(strategy: Strategy, snapshot: Snapshot, policy: RecoveryPolicy) -> dict:
    """Read-only result and bounded diagnostic. No network or catalog dependency."""
    started = time.monotonic()
    steps = 0
    found = []
    card_count = 0
    stage = "listing"

    def tick():
        nonlocal steps
        steps += 1
        if steps > policy.max_steps or time.monotonic() - started >= policy.max_seconds:
            raise ValueError("limit_exceeded")

    def destination(url):
        tick()
        parsed = urlsplit(url)
        if parsed.username or parsed.password or parsed.port not in (None, 80, 443):
            raise ValueError("destination_blocked")
        validate_destination(url, allowlist=policy.hosts)
        # Recovery is stricter: no unreviewed subdomain expansion.
        if parsed.hostname not in policy.hosts:
            raise ValueError("destination_blocked")

    def select(root, alternatives):
        for selector in alternatives:
            tick()
            nodes = root.select(selector)
            if nodes:
                return nodes
        return []

    def result(code):
        parsed = urlsplit(snapshot.url)
        return {
            "diagnosis": code, "strategy_hash": strategy.digest,
            "schema_version": strategy.schema_version, "stage": stage,
            "url": urlunsplit((parsed.scheme, parsed.hostname or "", parsed.path, "", "")),
            "excerpt": safe_excerpt(snapshot.html), "expected_identity": policy.expected_identity,
            "counts": {"cards": card_count, "documents": len(found), "expected": snapshot.expected_count},
            "documents": found, "steps": steps, "elapsed_s": time.monotonic() - started,
            "is_synthetic": snapshot.is_synthetic, "publication": "disabled",
            "limits": {"steps": policy.max_steps, "bytes": policy.max_bytes, "seconds": policy.max_seconds},
        }

    try:
        if snapshot.network_error:
            return result("network_failure")
        if snapshot.blocked:
            return result("blocked")
        destination(snapshot.url)
        for redirect in snapshot.redirects:
            destination(redirect)
        size = len(snapshot.html.encode()) + sum(len(p.encode()) for p in snapshot.pages.values())
        size += sum(len(d.content) + len(d.page_text.encode()) for d in snapshot.documents.values())
        if size > policy.max_bytes:
            return result("limit_exceeded")
        soup = BeautifulSoup(snapshot.html, "html.parser")
        cards = select(soup, strategy.cards)
        card_count = len(cards)
        if card_count > policy.max_cards:
            return result("limit_exceeded")
        if not cards:
            return result("legitimate_empty" if snapshot.legitimate_empty and snapshot.expected_count == 0 else "false_empty")
        for card in cards:
            if card.get("data-identity") != policy.expected_identity:
                return result("identity_inconsistent")
            stage = "details"
            links = select(card, strategy.details)
            if len(links) != 1:
                return result("layout_changed")
            detail_url = urljoin(snapshot.url, links[0].get("href", ""))
            destination(detail_url)
            if detail_url not in snapshot.pages:
                return result("layout_changed")
            detail = BeautifulSoup(snapshot.pages[detail_url], "html.parser")
            stage = "documents"
            links = select(detail, strategy.documents)
            if not links:
                return result("partial_extraction")
            for link in links:
                document_url = urljoin(detail_url, link.get("href", ""))
                destination(document_url)
                document = snapshot.documents.get(document_url)
                if document is None:
                    return result("insufficient_evidence")
                if document.identity != policy.expected_identity:
                    return result("wrong_document")
                if document.kind != "edital_principal":
                    return result("wrong_document_kind")
                if (not has_pdf_header(document.content) or
                    hashlib.sha256(document.content).hexdigest() != document.sha256 or
                    document.physical_page < 1 or not document.quote.strip() or
                    document.quote not in document.page_text):
                    return result("insufficient_evidence")
                found.append({"url": urlunsplit((*urlsplit(document_url)[:3], "", "")),
                              "identity": document.identity, "sha256": document.sha256,
                              "physical_page": document.physical_page, "quote": safe_excerpt(document.quote)})
        if snapshot.expected_count is not None and card_count != snapshot.expected_count:
            return result("partial_extraction")
        tick()
        return result("recovered")
    except Exception as exc:
        # Never preserve raw provider exceptions or URLs carrying secrets.
        return result("limit_exceeded" if str(exc) == "limit_exceeded" else "destination_blocked")
