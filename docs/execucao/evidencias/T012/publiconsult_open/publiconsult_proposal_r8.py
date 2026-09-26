"""Offline, source-scoped Publiconsult/681 proposal extractor (R8).

This does not wire shared dispatch. It reproduces only the three identity
fields required by proposal creation from the already approved principal PDF.
The separately approved TAF remains documentary provenance, never a source of
principal contest fields.
"""
from __future__ import annotations

import hashlib
import io
import re
from pypdf import PdfReader

SOURCE = "publiconsult_open"
SOURCE_ID = 56
EXTERNAL_ID = "681"
PRINCIPAL_SHA256 = "7e3bc67ae2d209679dabaa791d7d63fb12369dd53e1da85cda9831721bd9917f"
PRINCIPAL_BYTE_LEN = 720592
PRINCIPAL_PAGES = 25
PRINCIPAL_URL = "https://gsistbucket.s3.amazonaws.com/publiconsult/Anexos/681/PM%20VOTUPORANGA%20-%20PS%201-2026%20-%20Edital%20de%20Abertura%20de%20Inscri%C3%A7%C3%B5es.pdf"
TITLE = "Prefeitura Municipal de Votuporanga - Processo Seletivo - Nº 1/2026"
ORGAO = "Prefeitura Municipal de Votuporanga/SP"
EDITAL_NUMERO = "1/2026"


def _pages(content: bytes, page_records: list[dict] | None = None) -> list[str]:
    try:
        reader = PdfReader(io.BytesIO(content))
        pages = [page.extract_text() or "" for page in reader.pages]
    except Exception as exc:
        raise ValueError("principal PDF processing_error") from exc
    if len(pages) != PRINCIPAL_PAGES or any(not page.strip() for page in pages):
        raise ValueError("principal PDF page count/text drift")
    if any("\ufffd" in page for page in pages):
        raise ValueError("principal PDF contains replacement character")
    records = page_records if page_records is not None else [
        {"page_index": index, "page_number": index + 1, "error": None,
         "truncated": False, "processing_error": False}
        for index in range(len(pages))
    ]
    if len(records) != PRINCIPAL_PAGES:
        raise ValueError("principal PDF page record count drift")
    for index, record in enumerate(records):
        if (record.get("page_index") != index or
                record.get("page_number") != index + 1 or
                record.get("error") or record.get("truncated") or
                record.get("processing_error")):
            raise ValueError("principal PDF page order/index/flag drift")
    return pages


def extract_proposal_fields(*, content: bytes, source: str, external_id: str,
                            url_requested: str, url_final: str,
                            page_records: list[dict] | None = None) -> dict:
    if source != SOURCE or str(external_id) != EXTERNAL_ID:
        raise ValueError("source/external pin mismatch")
    if url_requested != PRINCIPAL_URL or url_final != PRINCIPAL_URL:
        raise ValueError("principal URL pin mismatch")
    if len(content) != PRINCIPAL_BYTE_LEN or hashlib.sha256(content).hexdigest() != PRINCIPAL_SHA256:
        raise ValueError("principal SHA/byte pin mismatch")
    pages = _pages(content, page_records)
    first = pages[0]
    if not re.search(r"Prefeitura Municipal de VOTUPORANGA", first, re.I):
        raise ValueError("orgao literal missing")
    if not re.search(r"Processo Seletivo\s+N.{0,2}1/2026", first, re.I):
        raise ValueError("edital literal missing")
    if not any("EDITAL de ABERTURA de INSCRI" in line for line in first.splitlines()):
        raise ValueError("principal document marker missing")
    lines = [line.strip() for line in first.splitlines() if line.strip()]
    title_snippet = next(line for line in lines if "Processo Seletivo" in line and "1/2026" in line)
    marker_snippet = next(line for line in lines if "EDITAL de ABERTURA de INSCRI" in line)
    orgao_snippet = next(line for line in lines if "Prefeitura Municipal de VOTUPORANGA" in line)
    evidence = {
        "titulo": {"page": 1, "snippet": title_snippet},
        "orgao": {"page": 1, "snippet": orgao_snippet},
        "edital_numero": {"page": 1, "snippet": title_snippet},
    }
    for item in evidence.values():
        if item["snippet"] not in first:
            raise ValueError("non-reproducible evidence")
        item.update({"document_sha256": PRINCIPAL_SHA256, "source_url": PRINCIPAL_URL})
    return {
        "source": SOURCE, "source_id": SOURCE_ID, "external_id": EXTERNAL_ID,
        "artifact": {"sha256": PRINCIPAL_SHA256, "byte_len": PRINCIPAL_BYTE_LEN, "pages": PRINCIPAL_PAGES, "url": PRINCIPAL_URL},
        "fields": [
            {"field_name": "titulo", "value": TITLE, "state": "supported", "evidence": [evidence["titulo"]]},
            {"field_name": "orgao", "value": ORGAO, "state": "supported", "evidence": [evidence["orgao"]]},
            {"field_name": "edital_numero", "value": EDITAL_NUMERO, "state": "supported", "evidence": [evidence["edital_numero"]]},
        ],
        "omitted_fields": ["cargos", "remuneracao", "taxa", "prova_data", "documentos"],
        "reference_only": True,
    }
