"""Pinned offline preflight for one preserved UFU selection (source 40).

The UFU fixture is an official detail page, not a downloaded edital PDF.  This
module therefore promotes only literals present on that page and deliberately
does not invent fee, vacancies, salary, or other document-only fields.
"""
from __future__ import annotations

import hashlib
import re
from typing import Any

from bs4 import BeautifulSoup

SOURCE = "ufu_selection"
SOURCE_ID = 40
EXTERNAL_ID = "1843"
DETAIL_URL = "https://www.portalselecao.ufu.br/servicos/Edital/cronograma/1843"
# The reviewed artifact is the linked administrative HTML document, not the
# candidate's detail-page URL.  Both URLs are part of the pin and have
# separate responsibilities in the dispatcher/revalidation contract.
DOCUMENT_URL = "https://www.portalselecao.ufu.br/servicos/ArquivoAdministrativo/download/ed123099e7f76388ae6c3a83ba7c6b80"
FIXTURE_NAME = "ufu_selection-cycle1-detail-9088337b8d.html"
ARTIFACT_ID = "ufu-selection-1843-detail-2026-r10"
EXPECTED_SHA256 = "72d8f9c6c18c734e8227a14c036ca32b8b9f705b2db507c8cd0169f939dc0daf"
EXPECTED_BYTES = 26619

TITLE = "Edital 144/2026 - Processo Seletivo Simplificado para Docentes"
ORG = "Universidade Federal de Uberlândia"
EDITAL = "144/2026"
REGISTRATION = "19/08/2026 15:00 03/09/2026 14:59 Inscrições"


def _text(content: bytes) -> str:
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError("UFU artifact is not UTF-8 HTML") from exc
    if "\ufffd" in text:
        raise ValueError("extraction contains U+FFFD replacement character")
    if len(text) < 1000 or "</html>" not in text.lower():
        raise ValueError("UFU artifact is truncated HTML")
    if re.search(r"(?:traceback|fatal error|internal server error)", text, re.I):
        raise ValueError("UFU artifact contains an error page")
    return text


def preflight(content: bytes, *, source: str = SOURCE, external_id: str = EXTERNAL_ID) -> dict[str, Any]:
    if source != SOURCE or external_id != EXTERNAL_ID:
        raise ValueError("UFU identity drift")
    digest = hashlib.sha256(content).hexdigest()
    if len(content) != EXPECTED_BYTES or digest != EXPECTED_SHA256:
        raise ValueError("artifact drift: byte length or SHA-256 mismatch")
    text = _text(content)
    soup = BeautifulSoup(text, "html.parser")
    if not soup.select_one('.fb-share-button[data-href="%s"]' % DETAIL_URL):
        raise ValueError("UFU detail identity marker missing")
    if TITLE not in soup.get_text(" ", strip=True) or ORG not in soup.get_text(" ", strip=True):
        raise ValueError("UFU detail required markers missing")
    return {"artifact_id": ARTIFACT_ID, "sha256": digest, "byte_len": len(content),
            "pages": 1, "source": SOURCE, "source_id": SOURCE_ID,
            "external_id": EXTERNAL_ID, "detail_url": DETAIL_URL, "network": False}


def _evidence(eid: str, snippet: str, path: str) -> dict[str, Any]:
    if not snippet or "\ufffd" in snippet:
        raise ValueError("invalid evidence snippet")
    return {"evidence_id": eid, "artifact_id": ARTIFACT_ID,
            "document_sha256": EXPECTED_SHA256, "source_url": DOCUMENT_URL,
            "page_number": 1, "snippet": snippet, "json_path": path,
            "method": "offline-html-text", "method_version": "ufu-selection-r1"}


def parse(content: bytes, **identity: str) -> dict[str, Any]:
    preflight(content, **identity)
    text = BeautifulSoup(_text(content), "html.parser").get_text(" ", strip=True)
    for marker in (TITLE, ORG, REGISTRATION):
        if marker not in text:
            raise ValueError(f"drift: required literal not found: {marker}")
    docs = sorted(set(re.findall(
        r"https://www\.portalselecao\.ufu\.br/servicos/ArquivoAdministrativo/download/[a-f0-9]{32}",
        _text(content))))
    evidence = {
        "titulo": _evidence("ufu-1843-titulo", TITLE, "identity.title"),
        "orgao": _evidence("ufu-1843-orgao", ORG, "identity.orgao"),
        "edital_numero": _evidence("ufu-1843-edital", EDITAL, "identity.edital_numero"),
        "inscricao": _evidence("ufu-1843-inscricao", REGISTRATION, "inscricao"),
    }
    return {"identity": {"source": SOURCE, "source_id": SOURCE_ID,
                          "external_id": EXTERNAL_ID, "title": TITLE,
                          "orgao": ORG, "edital_numero": EDITAL,
                          "detail_url": DETAIL_URL},
            "inscricao_inicio": "2026-08-19T15:00:00",
            "inscricao_fim": "2026-09-03T14:59:00",
            "document_urls": docs, "evidence": evidence,
            "reference_only": True, "pending_fields": ["taxa", "cargos", "remuneracao"]}


def derive(content: bytes, **identity: str) -> dict[str, Any]:
    parsed = parse(content, **identity)
    return parsed
