"""Pinned KLC/632 amendment parser for the preserved one-page retification."""
from __future__ import annotations

import hashlib

from app.tenderproof.contracts import Artifact, DiscoveredCandidate, Evidence, EvidenceValidation, ExtractedField, FieldState, PageText

SOURCE = "klc_open"
EXTERNAL_ID = "632"
ARTIFACT_ID = "art-klc-ret1-1887b316"
ARTIFACT_SHA256 = "0d16e9bc0f61000846c9828340710ee30845191704bc2c888f0d14734a278d60"
ARTIFACT_BYTE_LEN = 423600
EXPECTED_PAGES = 1
DOCUMENT_URL = "https://www.klcconcursos.com.br/editais/1887b316fec80864152561400d6ea76d.pdf"
DOCUMENT_TITLE = "Retificação 1 - Alteração da Data da Prova"
DOCUMENT_KIND = "retificacao"
DATE_SNIPPET = "ser aplicada no dia 17 de maio de 2026"


def extract_fields(*, candidate: DiscoveredCandidate, artifact: Artifact,
                   pages: list[PageText], content: bytes,
                   document: dict | None = None) -> list[ExtractedField]:
    if candidate.source != SOURCE or str(candidate.external_id) != EXTERNAL_ID:
        raise ValueError("KLC retificação source/external drift")
    if artifact.artifact_id != ARTIFACT_ID or artifact.sha256 != ARTIFACT_SHA256 or artifact.byte_len != ARTIFACT_BYTE_LEN:
        raise ValueError("KLC retificação artifact pin drift")
    if artifact.url_requested != DOCUMENT_URL or artifact.url_final != DOCUMENT_URL:
        raise ValueError("KLC retificação URL drift")
    if document is None or document.get("title") != DOCUMENT_TITLE \
            or document.get("kind") != DOCUMENT_KIND \
            or document.get("url") != DOCUMENT_URL:
        raise ValueError("KLC retificação document identity drift")
    if len(content) != ARTIFACT_BYTE_LEN or hashlib.sha256(content).hexdigest() != ARTIFACT_SHA256:
        raise ValueError("KLC retificação bytes/SHA drift")
    if len(pages) != EXPECTED_PAGES or [page.page_number for page in pages] != [1]:
        raise ValueError("KLC retificação page-count drift")
    page = pages[0]
    if page.error or page.truncated or "\ufffd" in page.text:
        raise ValueError("KLC retificação page flags/U+FFFD drift")
    text = page.text
    if "PROCESSO SELETIVO" not in text or "002/2026" not in text or DATE_SNIPPET not in text:
        raise ValueError("KLC retificação identity/date markers missing")
    evidence = Evidence(
        evidence_id="klc632-retificacao-prova-data",
        artifact_id=artifact.artifact_id,
        document_sha256=artifact.sha256,
        source_url=artifact.url_final,
        page_number=1,
        snippet=DATE_SNIPPET,
        method="klc-retificacao-preserved-parser",
        method_version="klc-retificacao-r22",
        validation=EvidenceValidation(ok=True),
    )
    return [ExtractedField(field_name="prova_data", state=FieldState.SUPPORTED,
                           value="2026-05-17", original_value="2026-05-17",
                           evidence=[evidence])]


def dispatch(*, candidate: DiscoveredCandidate, artifact: Artifact,
             pages: list[PageText], content: bytes,
             document: dict | None = None) -> list[ExtractedField]:
    return extract_fields(candidate=candidate, artifact=artifact, pages=pages,
                          content=content, document=document)
