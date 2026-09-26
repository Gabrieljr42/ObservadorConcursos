"""Proposed source-specific APTA/708 fix; evidence-only, not wired."""
from __future__ import annotations

import hashlib
from urllib.parse import unquote

from app.tenderproof.contracts import Evidence, ExtractedField, FieldState

SOURCE = "apta_open"
EXTERNAL_ID = "708"
EXPECTED_SHA256 = "db9c6d26a285102ae051761500d893c81616b07b69a086ec5353307d5975d79c"
EXPECTED_BYTE_LEN = 362093
EXPECTED_PAGES = 20
DETAIL_URL = "https://www.aptaconcursos.com.br/concursos/publicacoes/Câmara+Municipal+de+Aragarças+/708"
DOCUMENT_URL = "https://cdn-arquivo.concursos.srv.br/APTA/00708/PUBLICACOES/Edital_Completo_2026_07_31_09_13_43.pdf"
VERSION = "apta-aragarcas-708/2-r7"


def _texts(pages: list) -> list[str]:
    if len(pages) != EXPECTED_PAGES:
        raise ValueError("APTA/708 R7: page count drift")
    texts = []
    for index, page in enumerate(pages, 1):
        number = getattr(page, "page_number", index)
        text = page if isinstance(page, str) else page.text
        if number != index or not text.strip() or "\ufffd" in text or (
            not isinstance(page, str) and (page.error or page.truncated)
        ):
            raise ValueError("APTA/708 R7: page order/text drift")
        texts.append(text)
    return texts


def _detail_matches(url: str) -> bool:
    return (url in {DETAIL_URL, "https://www.aptaconcursos.com.br/concursos/publicacoes/C%C3%A2mara+Municipal+de+Aragar%C3%A7as+/708"}
            and unquote(url) == unquote(DETAIL_URL))


def extract_identity_r7(artifact, pages: list, *, source: str, external_id: str,
                        detail_url: str, document_url: str) -> list[ExtractedField]:
    if (source, str(external_id)) != (SOURCE, EXTERNAL_ID):
        raise ValueError("APTA/708 R7: source/external mismatch")
    if (artifact.sha256, artifact.byte_len) != (EXPECTED_SHA256, EXPECTED_BYTE_LEN):
        raise ValueError("APTA/708 R7: SHA/byte drift")
    if artifact.url_requested != DOCUMENT_URL or artifact.url_final != DOCUMENT_URL:
        raise ValueError("APTA/708 R7: document URL drift")
    if not _detail_matches(detail_url):
        raise ValueError("APTA/708 R7: detail URL drift")
    texts = _texts(pages)
    joined = "\n".join(texts)
    if "CONCURSO" not in joined or "01/2026" not in joined or "EDITAL DE ABERTURA COMPLETO" not in joined:
        raise ValueError("APTA/708 R7: identity markers drift")
    if "Municipal de Aragar" not in joined and "MUNICIPAL DE ARAGAR" not in joined:
        raise ValueError("APTA/708 R7: organization marker drift")
    def ev(field: str, page_number: int, snippet: str) -> Evidence:
        return Evidence(evidence_id=f"apta-708-r7-{field}", artifact_id=artifact.artifact_id,
                        document_sha256=artifact.sha256, source_url=artifact.url_final,
                        page_number=page_number, snippet=snippet, method="pypdf-native-text", method_version=VERSION)
    title_snippet = next(x.strip() for x in texts[0].splitlines() if "Municipal de Aragar" in x)
    orgao_snippet = next(x.strip() for x in texts[13].splitlines() if "MUNICIPAL DE ARAGAR" in x)
    edital_snippet = next(x.strip() for x in texts[0].splitlines() if "01/2026" in x and "CONCURSO" in x)
    return [
        ExtractedField(field_name="titulo", state=FieldState.SUPPORTED, value="Câmara Municipal de Aragarças",
                       original_value="Câmara Municipal de Aragarças", evidence=[ev("titulo", 1, title_snippet)]),
        ExtractedField(field_name="orgao", state=FieldState.SUPPORTED, value="Câmara Municipal De Aragarças",
                       original_value="Câmara Municipal de Aragarças", evidence=[ev("orgao", 14, orgao_snippet)]),
        ExtractedField(field_name="edital_numero", state=FieldState.SUPPORTED, value="01/2026",
                       original_value="01/2026", evidence=[ev("edital", 1, edital_snippet)]),
    ]
