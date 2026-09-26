"""Use reviewed recovery selectors on HTML already captured by acquisition.

No driver calls, extra sessions, writes or document approval. A discovered link
is still a candidate, subject to all existing detail/PDF evidence validation.
"""
from __future__ import annotations

import re
import time
from datetime import datetime, timezone
from urllib.parse import parse_qs, urljoin, urlsplit

from bs4 import BeautifulSoup

from app.tenderproof.contracts import DiscoveredCandidate
from app.tenderproof.recovery import Strategy, safe_excerpt
from app.tenderproof.recovery_store import RecoveryStore
from app.tenderproof.security import TenderProofSettings, validate_destination


def recover_listing_candidates(
    store: RecoveryStore, *, owner_user_id: int, source: str,
    html: str, listing_url: str, settings: TenderProofSettings,
) -> tuple[list[DiscoveredCandidate], dict | None]:
    """Acquisition hook after open_listing; known IBGP URL identity, no HTML marker.

Only invoke as an alternative to an empty traditional parse. The report must be
retained as diagnosis; an empty result never means deleting catalog entries.
"""
    normalized_source = {"ibgp_open": "ibgp", "imeso": "imeso", "imeso_open": "imeso"}.get(source)
    if normalized_source != "ibgp":
        return [], None
    strategy = store.active_strategy(owner_user_id, normalized_source)
    if strategy is None:
        return [], None
    return inspect_listing(strategy, html=html, listing_url=listing_url, settings=settings)


def inspect_listing(strategy: Strategy, *, html: str, listing_url: str, settings: TenderProofSettings):
    """Bounded candidate-only parser; no document evidence is invented here."""
    started = time.monotonic()
    steps = 0
    candidates = []
    report = {"strategy_hash": strategy.digest, "publication": "disabled",
              "stage": "listing", "evidence_state": "pending_document_validation",
              "excerpt": safe_excerpt(html), "cards": 0}

    def finish(diagnosis):
        report.update(diagnosis=diagnosis, candidates=len(candidates), steps=steps,
                      elapsed_s=time.monotonic() - started)
        return candidates, report

    def select(root, selectors):
        nonlocal steps
        for selector in selectors:
            steps += 1
            if steps > 20 or time.monotonic() - started >= min(2.0, settings.limits.total_timeout_s):
                raise ValueError("limit_exceeded")
            nodes = root.select(selector)
            if nodes:
                return nodes
        return []

    try:
        if len(html.encode()) > min(131072, settings.limits.max_json_bytes):
            return finish("limit_exceeded")
        validate_destination(listing_url, allowlist=settings.allowlist_hosts)
        soup = BeautifulSoup(html, "html.parser")
        cards = select(soup, strategy.cards)
        report["cards"] = len(cards)
        if len(cards) > min(5, settings.limits.max_candidates):
            return finish("limit_exceeded")
        if not cards:
            return finish("false_empty")
        seen = set()
        for card in cards:
            links = select(card, strategy.details)
            if len(links) != 1:
                candidates.clear()
                return finish("layout_changed")
            link = links[0]
            url = urljoin(listing_url, link.get("href", ""))
            validate_destination(url, allowlist=settings.allowlist_hosts)
            parsed = urlsplit(url)
            query = parse_qs(parsed.query)
            ids = query.get("cod", [])
            # Source identity is the exact known portal route and numeric ID;
            # title similarity and page-generated identity markers are irrelevant.
            if (parsed.hostname != "novo.ibgpconcursos.com.br" or parsed.path != "/concurso.jsp"
                    or parsed.username or parsed.password or parsed.port not in (None, 443)
                    or parsed.scheme != "https" or len(ids) != 1 or not re.fullmatch(r"[0-9]{1,12}", ids[0])):
                candidates.clear()
                return finish("identity_inconsistent")
            cod = ids[0]
            if cod in seen:
                continue
            seen.add(cod)
            heading = card.find(["h1", "h2", "h3", "h4"])
            title = heading.get_text(" ", strip=True)[:300] if heading else None
            candidates.append(DiscoveredCandidate(candidate_id=f"cand-{cod}", external_id=cod,
                detail_url_observed=f"https://novo.ibgpconcursos.com.br/concurso.jsp?cod={cod}",
                title_observed=title, observed_at=datetime.now(timezone.utc), source="ibgp_open"))
        return finish("navigation_recovered")
    except Exception as exc:
        candidates.clear()
        return finish("limit_exceeded" if str(exc) == "limit_exceeded" else "destination_blocked")
