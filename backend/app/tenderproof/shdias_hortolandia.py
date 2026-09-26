"""Pinned, offline SHDias parser for Hortolândia process 00308.

This module is deliberately independent from the generic field dispatcher.  It
accepts only the preserved official PDF bytes and fails closed on any artifact,
identity, page-count, marker, or extraction drift.
"""
from __future__ import annotations

import hashlib
import io
from typing import Any

from pypdf import PdfReader

SOURCE = "shdias_open"
SOURCE_ID = 51
EXTERNAL_ID = "MTEw/MzA4"
PROCESS_ID = "00308"
DETAIL_URL = "https://www.shdias.com.br/concursos/publicacoes/MTEw/MzA4"
DOCUMENT_URL = (
    "https://cdn-arquivo.concursos.srv.br/SHDIAS/00308/PUBLICACOES/"
    "01_Edital_Completo_2026_07_23_08_20_13.pdf"
)
ARTIFACT_ID = "shdias-open-00308-edital-2026"
EXPECTED_SHA256 = "F7DEAACF2D2C6C02195CD84D3DA9C8AB3527E3FC03062AC8EBB8E321F3A750C7"
EXPECTED_BYTES = 697485
EXPECTED_PAGES = 44

TITLE_SNIPPET = "MUNICÍPIO DE HORTOLÂNDIA \nCONCURSO PÚBLICO CPMH 001/2026 - Guarda"
FEE_SNIPPET = "ENSINO MÉDIO COMPLETO VALOR DA INSCRIÇÃO: R$ 63,25"
EXAM_SNIPPET = (
    "05.01.01. A realização da Prova Objetiva está prevista para o dia "
    "27 de setembro de 2026 (DOMINGO)."
)
CARGO_301_SNIPPET = "301 Guarda Municipal – 4ª Classe (Feminino) 11 01 12"
CARGO_302_SNIPPET = "302 Guarda Municipal – 4ª Classe (Masculino) 25 03 28"
PAY_SNIPPET = "R$ 3.971,37 200h/m"


def _pages(content: bytes) -> list[str]:
    try:
        reader = PdfReader(io.BytesIO(content))
    except Exception as exc:
        raise ValueError("artifact is not a readable PDF") from exc
    if len(reader.pages) != EXPECTED_PAGES:
        raise ValueError(f"drift: expected {EXPECTED_PAGES} pages, got {len(reader.pages)}")
    pages = [(page.extract_text() or "") for page in reader.pages]
    if any("\ufffd" in text for text in pages):
        raise ValueError("extraction contains U+FFFD replacement character")
    if any(not text.strip() for text in pages):
        raise ValueError("extraction contains an empty page")
    return pages


def preflight(
    content: bytes,
    *,
    source: str = SOURCE,
    external_id: str = EXTERNAL_ID,
    process_id: str = PROCESS_ID,
) -> dict[str, Any]:
    """Pin the immutable source identity before any field extraction."""
    if source != SOURCE or external_id != EXTERNAL_ID or process_id != PROCESS_ID:
        raise ValueError("SHDias identity drift")
    digest = hashlib.sha256(content).hexdigest().upper()
    if len(content) != EXPECTED_BYTES or digest != EXPECTED_SHA256:
        raise ValueError("artifact drift: byte length or SHA-256 mismatch")
    pages = _pages(content)
    return {
        "artifact_id": ARTIFACT_ID,
        "sha256": digest,
        "byte_len": len(content),
        "pages": len(pages),
        "source": SOURCE,
        "source_id": SOURCE_ID,
        "external_id": EXTERNAL_ID,
        "process_id": PROCESS_ID,
        "detail_url": DETAIL_URL,
        "document_url": DOCUMENT_URL,
        "network": False,
    }


def _evidence(evidence_id: str, page: int, snippet: str, json_path: str) -> dict[str, Any]:
    if not snippet or "\ufffd" in snippet:
        raise ValueError("invalid evidence snippet")
    return {
        "evidence_id": evidence_id,
        "artifact_id": ARTIFACT_ID,
        "document_sha256": EXPECTED_SHA256.lower(),
        "source_url": DOCUMENT_URL,
        "page_number": page,
        "snippet": snippet,
        "json_path": json_path,
        "method": "offline-pdf-text",
        "method_version": "shdias-hortolandia-r4",
    }


def _require(page_text: str, snippet: str) -> str:
    if snippet not in page_text:
        raise ValueError(f"drift: required literal not found: {snippet}")
    return snippet


def parse(
    content: bytes,
    *,
    source: str = SOURCE,
    external_id: str = EXTERNAL_ID,
    process_id: str = PROCESS_ID,
) -> dict[str, Any]:
    """Return only fields proven by exact literals in the pinned PDF."""
    preflight(content, source=source, external_id=external_id, process_id=process_id)
    pages = _pages(content)
    cover = pages[0]
    table = pages[1]
    exam = pages[13]
    title_snippet = _require(cover, TITLE_SNIPPET)
    fee_snippet = _require(table, FEE_SNIPPET)
    exam_snippet = _require(exam, EXAM_SNIPPET)
    cargo_301 = _require(table, CARGO_301_SNIPPET)
    cargo_302 = _require(table, CARGO_302_SNIPPET)
    pay = _require(table, PAY_SNIPPET)
    evidence = {
        "titulo": _evidence("shdias-00308-titulo", 1, title_snippet, "titulo"),
        "orgao": _evidence("shdias-00308-orgao", 1, title_snippet, "orgao"),
        "edital_numero": _evidence("shdias-00308-edital", 1, title_snippet, "edital_numero"),
        "taxa_inscricao": _evidence("shdias-00308-taxa", 2, fee_snippet, "taxa_inscricao"),
        "prova_data": _evidence("shdias-00308-prova", 14, exam_snippet, "prova_data"),
        "cargo_301": _evidence("shdias-00308-cargo-301", 2, cargo_301, "cargos[0]"),
        "cargo_302": _evidence("shdias-00308-cargo-302", 2, cargo_302, "cargos[1]"),
        "remuneracao": _evidence("shdias-00308-remuneracao", 2, pay, "cargos[*].remuneracao"),
    }
    # ``taxa`` is the canonical versioned Concurso field.  Keep the source
    # label as ``taxa_inscricao`` in the evidence path, but expose the same
    # proven scalar under the canonical name for the shared publication flow.
    evidence["taxa"] = {**evidence["taxa_inscricao"], "evidence_id": "shdias-00308-taxa-canonical", "json_path": "taxa"}
    cargos = [
        {"codigo": "301", "nome": "Guarda Municipal – 4ª Classe (Feminino)", "vagas": 12, "remuneracao": "3971.37"},
        {"codigo": "302", "nome": "Guarda Municipal – 4ª Classe (Masculino)", "vagas": 28, "remuneracao": "3971.37"},
    ]
    return {
        "identity": {
            "source": SOURCE,
            "source_id": SOURCE_ID,
            "external_id": EXTERNAL_ID,
            "process_id": PROCESS_ID,
            "title": "CONCURSO PÚBLICO CPMH 001/2026 - Guarda",
            "orgao": "Município de Hortolândia",
            "edital_numero": "001/2026",
            "detail_url": DETAIL_URL,
        },
        "taxa_inscricao": "63.25",
        "taxa": "63.25",
        "prova_data": "2026-09-27",
        "cargos": cargos,
        "vagas_total": 40,
        "remuneracao": "3971.37",
        "evidence": evidence,
        "reference_only": True,
        "pending_fields": [],
    }


def derive(content: bytes, **identity: str) -> dict[str, Any]:
    """Stable semantic output used by offline revalidation tests."""
    parsed = parse(content, **identity)
    return {
        "identity": parsed["identity"],
        "taxa_inscricao": parsed["taxa_inscricao"],
        "prova_data": parsed["prova_data"],
        "cargos": parsed["cargos"],
        "vagas_total": parsed["vagas_total"],
        "remuneracao": parsed["remuneracao"],
    }
