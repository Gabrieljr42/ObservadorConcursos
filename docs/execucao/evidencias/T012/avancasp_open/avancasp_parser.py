"""Pinned, offline Avança SP parser for selection 272 only.

This module is deliberately source-specific and inert: it is not imported by
the shared extractor or production routes.  Its only purpose is the T012
strong-binding preflight over the preserved official PDF.
"""
from __future__ import annotations

import hashlib
import re
from typing import Any

from app.tenderproof.contracts import Artifact, DiscoveredCandidate, ExtractedField, FieldState, PageText
from app.tenderproof.fields import _evidence, extract_fields as generic_extract_fields

SOURCE = "avancasp_open"
EXTERNAL_ID = "272"
EXPECTED_SHA256 = "b0ba7e154786ce20c7bbe5fd454933c552558c4dfcfc588b60a71eab6a4ca06a"
EXPECTED_BYTES = 742298
EXPECTED_EDITAL = "01/2026"
IDENTITY_SNIPPET = "CONCURSO PÚBLICO 01/2026"
DETAIL_URL = "https://avancasp.selecao.net.br/informacoes/272/"
DOCUMENT_URL = "https://anexos-r2.selecao.net.br/uploads/301/concursos/272/anexos/aa3e927b-faeb-414e-ae6c-28800427a051.pdf"
EXPECTED_PAGES = 48


def preflight(content: bytes) -> dict[str, Any]:
    """Reject any bytes other than the pinned official PDF."""
    digest = hashlib.sha256(content).hexdigest()
    if len(content) != EXPECTED_BYTES or digest != EXPECTED_SHA256:
        raise ValueError("avancasp 272 artifact drift: SHA/byte_len mismatch")
    if not content.startswith(b"%PDF-"):
        raise ValueError("avancasp 272 artifact is not a PDF")
    return {"source": SOURCE, "external_id": EXTERNAL_ID, "sha256": digest, "byte_len": len(content)}


def _page_one(pages: list[PageText]) -> PageText:
    if len(pages) != EXPECTED_PAGES or [item.page_number for item in pages] != list(range(1, EXPECTED_PAGES + 1)):
        raise ValueError("avancasp 272 page count/order drift")
    if any(item.error or item.truncated or not item.text.strip() or "\ufffd" in item.text for item in pages):
        raise ValueError("avancasp 272 page text/error drift")
    page = next((item for item in pages if item.page_number == 1), None)
    if page is None or page.error or page.truncated or not page.text.strip():
        raise ValueError("avancasp 272 page 1 is unavailable")
    return page


def document_identity_ids(candidate: DiscoveredCandidate, pages: list[PageText]) -> set[str]:
    """Bind PDF identity to the source and the exact external ID."""
    if candidate.source != SOURCE or candidate.external_id != EXTERNAL_ID:
        raise ValueError("avancasp source/external identity mismatch")
    page = _page_one(pages)
    if IDENTITY_SNIPPET not in page.text:
        raise ValueError("avancasp 272 notice identity heading missing")
    if "PREFEITURA MUNICIPAL DE CABRE" not in page.text:
        raise ValueError("avancasp 272 municipality identity missing")
    return {EXTERNAL_ID}


def extract_fields(*, candidate: DiscoveredCandidate, artifact: Artifact, pages: list[PageText]) -> list[ExtractedField]:
    """Reuse generic field extraction only after pinned identity checks.

    The shared extractor does not recognize this notice's heading as an
    ``edital_numero``.  We add that one source-specific, verbatim-supported
    field and retain all generic fields/evidence for the real revalidation.
    """
    if candidate.source != SOURCE or candidate.external_id != EXTERNAL_ID:
        raise ValueError("avancasp source/external identity mismatch")
    if artifact.sha256 != EXPECTED_SHA256 or artifact.byte_len != EXPECTED_BYTES:
        raise ValueError("avancasp 272 artifact is not pinned")
    if artifact.url_requested != DOCUMENT_URL or artifact.url_final != DOCUMENT_URL:
        raise ValueError("avancasp 272 document URL is not pinned")
    if candidate.detail_url_observed != DETAIL_URL:
        raise ValueError("avancasp 272 detail URL is not pinned")
    page = _page_one(pages)
    document_identity_ids(candidate, pages)
    fields = [field for field in generic_extract_fields(candidate=candidate, artifact=artifact, pages=pages,
                                                        _skip_source_dispatch=True)
              if field.field_name not in {"edital_numero", "cargos"}]
    fields.append(ExtractedField(
        field_name="edital_numero", state=FieldState.SUPPORTED, value=EXPECTED_EDITAL,
        evidence=[_evidence(artifact=artifact, page=page, snippet=IDENTITY_SNIPPET)],
    ))
    def page(number: int) -> PageText:
        return next(item for item in pages if item.page_number == number)

    # The preserved PDF's three employment tables are stable under this
    # pinned SHA. Keep the literal table evidence while publishing only the
    # canonical values needed by the proposal path.
    rows = [
        ("Auxiliar de Serviços", 1, "1 + CR", "2204.14", "40h", "Fundamental Completo", "55.00", 1, "Auxiliar de Serviços"),
        ("Motorista", 1, "1 + CR", "2711.76", "40h", "Fundamental Completo", "55.00", 1, "Motorista"),
        ("Operador de Máquinas", 1, "1 + CR", "3473.20", "40h", "Fundamental Incompleto", "55.00", 2, "Operador de Máquinas"),
        ("Servente de Limpeza", 0, "CR", "2204.14", "40h", "Fundamental Completo", "55.00", 2, "Servente de Limpeza"),
        ("Agente de Fiscalização Ambiental", 1, "1 + CR", "3473.20", "40h", "Médio + Técnico", "74.00", 2, "Agente de Fiscalização"),
        ("Agente de Trânsito", 0, "CR", "2473.98", "40h", "Médio", "74.00", 2, "Agente de Trânsito"),
        ("Agente Fiscal de Obras", 1, "1 + CR", "3473.20", "40h", "Médio + Técnico", "74.00", 2, "Agente Fiscal de Obras"),
        ("Agrimensor", 1, "1 + CR", "3713.64", "40h", "Técnico", "74.00", 2, "Agrimensor"),
        ("Técnico em Edificações", 1, "1 + CR", "3713.64", "40h", "Médio + Técnico", "74.00", 2, "Técnico em Edificações"),
        ("Arquiteto - A", 1, "1 + CR", "11735.45", "40h", "Superior", "92.00", 3, "Arquiteto"),
        ("Biólogo", 1, "1 + CR", "4889.21", "30h", "Superior", "92.00", 3, "Biólogo"),
        ("Engenheiro Civil - A", 0, "CR", "11735.45", "40h", "Superior", "92.00", 3, "Engenheiro Civil"),
        ("Professor de Educação Básica II - PEB II - Artes", 0, "CR", "4942.63", "36h", "Superior", "92.00", 3, "Professor de Educação Básica"),
        ("Psicólogo - A", 0, "CR", "8202.12", "40h", "Superior", "92.00", 3, "Psicólogo"),
    ]
    cargos = []
    evidences = []
    for nome, vagas, vagas_observadas, remuneracao, jornada, requisitos, taxa, page_number, snippet in rows:
        text_page = page(page_number)
        match = next((line.strip() for line in text_page.text.splitlines() if snippet in line), None)
        if not match:
            raise ValueError(f"avancasp 272 cargo row missing: {nome}")
        cargos.append({"nome": nome, "vagas_imediatas": vagas, "cadastro_reserva": True,
                       "vagas_observadas": vagas_observadas, "remuneracao": remuneracao,
                       "moeda": "BRL", "jornada": jornada, "requisitos": requisitos,
                       "taxa_inscricao": taxa})
        evidences.append(_evidence(artifact=artifact, page=text_page, snippet=match))
    fields.append(ExtractedField(field_name="cargos", state=FieldState.SUPPORTED,
                                  value=cargos, evidence=evidences))
    return fields
