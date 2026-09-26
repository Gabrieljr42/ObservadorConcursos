"""Offline R3 pin proposal for the first accepted AvançaSP 272 document.

This is evidence-only and intentionally not imported by production routes.
It records the correction proven by the local staging receipt: the parser's
old aa3e/b0ba pin was stale while the first pending manifest URL is bbc8/c60.
"""
from __future__ import annotations

import hashlib

SOURCE = "avancasp_open"
EXTERNAL_ID = "272"
TITLE = "EDITAL COMPLETO 04/09/2026"
KIND = "edital"
DOCUMENT_URL = (
    "https://anexos-r2.selecao.net.br/uploads/301/concursos/272/anexos/"
    "bbc8f6fc-a0a1-49ef-aa1d-7d5d2403f7ce.pdf"
)
EXPECTED_SHA256 = "c60fcc60f0037c4f28907460cf8a60ec6832b115b28988e81d77ebbb66441637"
EXPECTED_BYTES = 750381
EXPECTED_PAGES = 48


def preflight(content: bytes) -> dict[str, object]:
    digest = hashlib.sha256(content).hexdigest()
    if len(content) != EXPECTED_BYTES or digest != EXPECTED_SHA256:
        raise ValueError("avancasp 272 R3 artifact drift: SHA/byte_len mismatch")
    if not content.startswith(b"%PDF-"):
        raise ValueError("avancasp 272 R3 artifact is not a PDF")
    return {"source": SOURCE, "external_id": EXTERNAL_ID, "sha256": digest, "byte_len": len(content)}


def validate_document_binding(*, title: str, kind: str, url: str) -> None:
    if title != TITLE or kind != KIND or url != DOCUMENT_URL:
        raise ValueError("avancasp 272 R3 document manifest mismatch")
