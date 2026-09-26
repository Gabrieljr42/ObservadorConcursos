"""Pinned offline parser for the preserved Instituto Águia process 43 PDF."""
from __future__ import annotations

import hashlib
import io
from typing import Any

from pypdf import PdfReader

SOURCE = "aguia_open"
SOURCE_ID = 27
EXTERNAL_ID = "43"
DETAIL_URL = "https://portal.institutoaguia.org.br/edital/ver/43"
DOCUMENT_URL = "https://cdn.institutoaguia.org.br/edital/1/43/c382a2aac7251c1a31c0b734cd3540df.pdf"
ARTIFACT_ID = "aguia-open-43-pdf-r2"
EXPECTED_SHA256 = "f039e9961f625c23f3a0ec9f60d51ce87534d2a7d96cdfdaab029efba7aa47c7"
EXPECTED_BYTES = 501543
EXPECTED_PAGES = 18

TITLE = "EDITAL DE ABERTURA - PROCESSO SELETIVO  \nNº 01/2025"
ORG = "PREFEITURA MUNICIPAL DE BÁLSAMO"
FEE = "VALOR DA INSCRIÇÃO R$ 65,00"
REGISTRATION = "às 00h do dia 05 de dezembro de 2025 e encerrando-se às 23h59 do dia 16 de dezembro de 2025"
EXAM = "As Provas Objetivas realizadas na data provável de 25/01/2026"


def _pages(content: bytes) -> list[str]:
    try:
        reader = PdfReader(io.BytesIO(content))
    except Exception as exc:
        raise ValueError("artifact is not a readable PDF") from exc
    if len(reader.pages) != EXPECTED_PAGES:
        raise ValueError(f"drift: expected {EXPECTED_PAGES} pages, got {len(reader.pages)}")
    pages = [(page.extract_text() or "") for page in reader.pages]
    if any("\ufffd" in page for page in pages):
        raise ValueError("extraction contains U+FFFD replacement character")
    if any(not page.strip() for page in pages):
        raise ValueError("extraction contains an empty page")
    return pages


def preflight(content: bytes, *, source: str = SOURCE, external_id: str = EXTERNAL_ID) -> dict[str, Any]:
    if source != SOURCE or external_id != EXTERNAL_ID:
        raise ValueError("Águia identity drift")
    digest = hashlib.sha256(content).hexdigest()
    if len(content) != EXPECTED_BYTES or digest != EXPECTED_SHA256:
        raise ValueError("artifact drift: byte length or SHA-256 mismatch")
    pages = _pages(content)
    return {"artifact_id": ARTIFACT_ID, "sha256": digest, "byte_len": len(content), "pages": len(pages),
            "source": SOURCE, "source_id": SOURCE_ID, "external_id": EXTERNAL_ID,
            "detail_url": DETAIL_URL, "document_url": DOCUMENT_URL, "network": False}


def _evidence(eid: str, page: int, snippet: str, path: str) -> dict[str, Any]:
    if not snippet or "\ufffd" in snippet:
        raise ValueError("invalid evidence snippet")
    return {"evidence_id": eid, "artifact_id": ARTIFACT_ID, "document_sha256": EXPECTED_SHA256,
            "source_url": DOCUMENT_URL, "page_number": page, "snippet": snippet,
            "json_path": path, "method": "offline-pdf-text", "method_version": "aguia-balsamo-r1"}


def _require(text: str, snippet: str) -> str:
    if snippet not in text:
        raise ValueError(f"drift: required literal not found: {snippet}")
    return snippet


def parse(content: bytes, **identity: str) -> dict[str, Any]:
    preflight(content, **identity)
    pages = _pages(content)
    title = _require(pages[0], TITLE)
    org = _require(pages[0], ORG)
    fee = _require(pages[0], FEE)
    registration = _require(pages[1], REGISTRATION)
    exam = _require(pages[5], EXAM)
    cargo_markers = [
        _require(pages[0], "300 Educação Infantil"),
        _require(pages[0], "301"),
        _require(pages[1], "302"),
        _require(pages[1], "303"),
    ]
    pay = _require(pages[0], "30h 3.445,71")
    cargos = [
        {"codigo": "300", "nome": "Educação Infantil - PEB I", "remuneracao": "3445.71", "jornada": "30h"},
        {"codigo": "301", "nome": "Ensino Fundamental - Anos Iniciais - PEB I", "remuneracao": "3445.71", "jornada": "30h"},
        {"codigo": "302", "nome": "Artes - Anos Iniciais - PEB II", "remuneracao": "3445.71", "jornada": "30h"},
        {"codigo": "303", "nome": "Educação Física - Anos Iniciais - PEB II", "remuneracao": "3445.71", "jornada": "30h"},
    ]
    evidence = {
        "orgao": _evidence("aguia-43-orgao", 1, org, "orgao"),
        "edital_numero": _evidence("aguia-43-edital", 1, title, "edital_numero"),
        "taxa_inscricao": _evidence("aguia-43-taxa", 1, fee, "taxa_inscricao"),
        "inscricao": _evidence("aguia-43-inscricao", 2, registration, "inscricao"),
        "prova_data": _evidence("aguia-43-prova", 6, exam, "prova_data"),
        "remuneracao": _evidence("aguia-43-remuneracao", 1, pay, "cargos[*].remuneracao"),
    }
    for index, marker in enumerate(cargo_markers):
        evidence[f"cargo_{index}"] = _evidence(f"aguia-43-cargo-{index}", 1 if index < 2 else 2, marker, f"cargos[{index}]")
    return {"identity": {"source": SOURCE, "source_id": SOURCE_ID, "external_id": EXTERNAL_ID,
                          "title": "Prefeitura Municipal de Bálsamo - Processo Seletivo 01/2025",
                          "orgao": "Prefeitura Municipal de Bálsamo", "edital_numero": "01/2025",
                          "detail_url": DETAIL_URL},
            "taxa_inscricao": "65.00", "inscricao_inicio": "2025-12-05T00:00:00",
            "inscricao_fim": "2025-12-16T23:59:00", "prova_data": "2026-01-25",
            "cargos": cargos, "evidence": evidence, "reference_only": True, "pending_fields": []}


def derive(content: bytes, **identity: str) -> dict[str, Any]:
    parsed = parse(content, **identity)
    return {key: parsed[key] for key in ("identity", "taxa_inscricao", "inscricao_inicio", "inscricao_fim", "prova_data", "cargos")}
