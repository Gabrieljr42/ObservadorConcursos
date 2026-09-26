"""Pinned, offline EPL identity parser for T012 strong-binding recovery.

This module is deliberately source-local.  It does not alter the shared field
extractor or publication flow; the integrator may use its output when wiring a
future EPL-specific adapter revision.
"""
from __future__ import annotations

import hashlib
import re
from datetime import datetime
from io import BytesIO

from pypdf import PdfReader
from app.tenderproof.contracts import Artifact, Evidence, ExtractedField, FieldState, PageText, ValidationResult, ValidationStatus


SOURCE = "epl_open"
EXTERNAL_ID = "52"
SHA256 = "b040f8c3ff74845185dfdfec2096b70da84a7ee10c54d228afe7b82ed205805f"
BYTE_LEN = 784614
DETAIL_URL = "https://www.eplconcursos.com.br/concursos/publicacoes/FUNDA%C3%87%C3%83O+HOSPITALAR+SANTA+TEREZINHA+DE+ERECHIM/52"
DOCUMENT_URL = "https://cdn-arquivo.concursos.srv.br/EPL_CONCURSOS/00052/PUBLICA%C3%87%C3%95ES/01%20-%20EDITAL%20DE%20ABERTURA%20-%20VERSAO%20FINAL_1701470854.pdf"


class EPLParserError(ValueError):
    pass


EXPECTED_PAGES = 43


def _text(content: bytes) -> list[str]:
    """Extract every page, rejecting incomplete/error/replacement output."""
    try:
        pages = PdfReader(BytesIO(content)).pages
        if len(pages) != EXPECTED_PAGES:
            raise EPLParserError(f"EPL PDF page count diverged: {len(pages)}")
        texts = []
        for number, page in enumerate(pages, 1):
            text = page.extract_text() or ""
            if not text.strip() or "\ufffd" in text:
                raise EPLParserError(f"EPL page {number} is empty, truncated, or contains U+FFFD")
            if not re.search(r"P.gina\s+%d\s+de\s+43" % number, text):
                raise EPLParserError(f"EPL page {number} footer/page marker is missing")
            texts.append(text)
        return texts
    except EPLParserError:
        raise
    except Exception as exc:
        raise EPLParserError("EPL PDF extraction failed") from exc


def _contract(content: bytes, *, source: str, external_id: str, detail_url: str, document_url: str) -> tuple[list[str], str, str]:
    if source != SOURCE or external_id != EXTERNAL_ID:
        raise EPLParserError("EPL parser is pinned to source=epl_open external_id=52")
    if detail_url != DETAIL_URL or document_url != DOCUMENT_URL:
        raise EPLParserError("EPL detail/document URL binding diverged")
    if len(content) != BYTE_LEN or hashlib.sha256(content).hexdigest() != SHA256:
        raise EPLParserError("EPL artifact bytes diverged from pinned SHA/byte_len")
    pages = _text(content)
    text = "\n".join(pages)
    orgao_snippet = "A Funda\u00e7\u00e3o Hospitalar Santa Terezinha de Erechim \u2013 FHSTE"
    edital_snippet = "CONCURSO P\u00daBLICO N\u00b0 01/2023"
    if orgao_snippet not in text:
        raise EPLParserError("EPL órgão not reproduced from PDF")
    if edital_snippet not in text:
        raise EPLParserError("EPL edital number not reproduced from PDF")
    return pages, orgao_snippet, edital_snippet


def _artifact() -> Artifact:
    return Artifact(artifact_id="art-8c5dbef058", sha256=SHA256, byte_len=BYTE_LEN,
                    url_requested=DOCUMENT_URL, url_final=DOCUMENT_URL,
                    content_type="application/pdf", downloaded_at=datetime(2026, 9, 8, 14, 13, 22))


def extract_identity(artifact: Artifact, pages: list[PageText | str], *, source: str,
                     external_id: str) -> list[ExtractedField]:
    """Return typed fresh fields consumable by the normal validation gate."""
    def failed(reason: str) -> list[ExtractedField]:
        return [ExtractedField(field_name="edital_numero", state=FieldState.FAILED, reason=reason)]

    if (source, external_id, artifact.sha256, artifact.byte_len) != (SOURCE, EXTERNAL_ID, SHA256, BYTE_LEN):
        return failed("EPL/52: source, external ID, SHA or byte length drift")
    if artifact.url_requested != DOCUMENT_URL or artifact.url_final != DOCUMENT_URL:
        return failed("EPL/52: artifact URL is not the pinned official document")
    if len(pages) != EXPECTED_PAGES:
        return failed("EPL/52: page count drift")
    texts = []
    for number, page in enumerate(pages, 1):
        if isinstance(page, str):
            text = page
        else:
            if (page.artifact_id != artifact.artifact_id or page.page_number != number
                    or page.error or page.truncated):
                return failed("EPL/52: page order/number/error/truncated metadata drift")
            text = page.text
        if (not text.strip() or "\ufffd" in text
                or not re.search(r"P.gina\s+%d\s+de\s+43" % number, text)):
            return failed("EPL/52: incomplete page text")
        texts.append(text)
    joined = "\n".join(texts)
    orgao_snippet = "A Funda\u00e7\u00e3o Hospitalar Santa Terezinha de Erechim \u2013 FHSTE"
    edital_snippet = "CONCURSO P\u00daBLICO N\u00b0 01/2023"
    if orgao_snippet not in joined or edital_snippet not in joined:
        return [ExtractedField(field_name="edital_numero", state=FieldState.FAILED,
                               reason="EPL/52: identity structure drift")]
    def evidence(field: str, snippet: str, suffix: str) -> Evidence:
        if snippet not in texts[0] or "\ufffd" in snippet:
            raise EPLParserError("EPL/52: evidence snippet is not verbatim")
        return Evidence(evidence_id=f"epl-52-{suffix}", artifact_id=artifact.artifact_id,
                        document_sha256=artifact.sha256, source_url=artifact.url_final,
                        page_number=1, snippet=snippet, method="pypdf-native-text",
                        method_version="epl-52-r5")
    return [
        ExtractedField(field_name="orgao", state=FieldState.SUPPORTED,
                       value="Fundação Hospitalar Santa Terezinha de Erechim (FHSTE)",
                       original_value=orgao_snippet, evidence=[evidence("orgao", orgao_snippet, "orgao")]),
        ExtractedField(field_name="edital_numero", state=FieldState.SUPPORTED,
                       value="01/2023", original_value=edital_snippet,
                       evidence=[evidence("edital_numero", edital_snippet, "edital")]),
    ]


def revalidate(content: bytes, *, source: str = SOURCE, external_id: str = EXTERNAL_ID,
               detail_url: str = DETAIL_URL, document_url: str = DOCUMENT_URL) -> list[ExtractedField]:
    """Validate the pinned selection and return typed fresh identity fields."""
    _contract(content, source=source, external_id=external_id, detail_url=detail_url, document_url=document_url)
    artifact = _artifact()
    pages = [PageText(artifact_id=artifact.artifact_id, page_number=i + 1, text=text)
             for i, text in enumerate(_text(content))]
    return extract_identity(artifact, pages, source=source, external_id=external_id)


def validation_result(content: bytes) -> ValidationResult:
    try:
        revalidate(content)
    except EPLParserError as exc:
        return ValidationResult(status=ValidationStatus.UNREADABLE, errors=[str(exc)])
    return ValidationResult(status=ValidationStatus.VALID)


