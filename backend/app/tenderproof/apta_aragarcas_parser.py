"""Pinned offline identity parser for APTA selection 708."""
from __future__ import annotations

from datetime import date
import hashlib
from urllib.parse import unquote

from .contracts import Evidence, ExtractedField, FieldState

SOURCE = "apta_open"
EXTERNAL_ID = "708"
EXPECTED_SHA256 = "db9c6d26a285102ae051761500d893c81616b07b69a086ec5353307d5975d79c"
EXPECTED_BYTE_LEN = 362093
EXPECTED_PAGES = 20
DETAIL_URL = "https://www.aptaconcursos.com.br/concursos/publicacoes/Câmara+Municipal+de+Aragarças+/708"
DETAIL_URL_ENCODED = "https://www.aptaconcursos.com.br/concursos/publicacoes/C%C3%A2mara+Municipal+de+Aragar%C3%A7as+/708"
DOCUMENT_URL = "https://cdn-arquivo.concursos.srv.br/APTA/00708/PUBLICACOES/Edital_Completo_2026_07_31_09_13_43.pdf"
VERSION = "apta-aragarcas-708/2-r7"

# The pending retification is a separate one-page document. It must never be
# routed through the strict 20-page principal-edital parser below.
RETIFICATION_SHA256 = "ee8de6a5031ec0de0f8ed1a6b77d85bbceac44e82b545b04896bc08cf1d48786"
RETIFICATION_BYTE_LEN = 76767
RETIFICATION_PAGES = 1
RETIFICATION_URL = "https://cdn-arquivo.concursos.srv.br/APTA/00708/PUBLICACOES/Edital_Retificacao_2_2026_07_28_17_32_37.pdf"
RETIFICATION_TITLE = "Edital de Retificação I ao Edital de Abertura de Inscrições"


def validate_retification(artifact, pages: list, *, source: str, external_id: str,
                          document: dict) -> None:
    """Validate the pinned amendment without promoting catalog fields."""
    if (source, str(external_id), artifact.sha256, artifact.byte_len) != (
            SOURCE, EXTERNAL_ID, RETIFICATION_SHA256, RETIFICATION_BYTE_LEN):
        raise ValueError("APTA/708 retificação: source/external/SHA/bytes drift")
    if (artifact.url_requested != RETIFICATION_URL or artifact.url_final != RETIFICATION_URL
            or document.get("url") != RETIFICATION_URL
            or document.get("title") != RETIFICATION_TITLE
            or document.get("kind") != "retificacao"):
        raise ValueError("APTA/708 retificação: URL/título/tipo drift")
    if len(pages) != RETIFICATION_PAGES:
        raise ValueError("APTA/708 retificação: page count drift")
    page = pages[0]
    if page.page_number != 1 or page.error or page.truncated or not page.text.strip() or "\ufffd" in page.text:
        raise ValueError("APTA/708 retificação: page/text flags drift")
    text = page.text
    required = ("Retifica", "item 9.9", "Permanecem inalterados", "Aragar")
    if any(marker.casefold() not in text.casefold() for marker in required):
        raise ValueError("APTA/708 retificação: literal identity/effect markers missing")


def _detail_matches(url: str) -> bool:
    return url in {DETAIL_URL, DETAIL_URL_ENCODED} and unquote(url) == unquote(DETAIL_URL)


def _texts(pages: list) -> list[str]:
    if len(pages) != EXPECTED_PAGES:
        raise ValueError("APTA/708: page count drift")
    texts = []
    for index, page in enumerate(pages, 1):
        number = getattr(page, "page_number", index)
        text = page if isinstance(page, str) else page.text
        if number != index or not text.strip() or "\ufffd" in text or (
                not isinstance(page, str) and (page.error or page.truncated)):
            raise ValueError("APTA/708: page order/text drift")
        texts.append(text)
    return texts


def _identity_fields(artifact, pages: list, *, detail_url: str, document_url: str) -> list[ExtractedField]:
    if artifact.url_requested != DOCUMENT_URL or artifact.url_final != DOCUMENT_URL or document_url != DOCUMENT_URL:
        raise ValueError("APTA/708: document URL drift")
    if not _detail_matches(detail_url):
        raise ValueError("APTA/708: detail URL drift")
    texts = _texts(pages)
    joined = "\n".join(texts)
    if "CONCURSO" not in joined or "01/2026" not in joined or "EDITAL DE ABERTURA COMPLETO" not in joined:
        raise ValueError("APTA/708: identity markers drift")
    if "Municipal de Aragar" not in joined and "MUNICIPAL DE ARAGAR" not in joined:
        raise ValueError("APTA/708: organization marker drift")

    def ev(field: str, page_number: int, snippet: str) -> Evidence:
        return Evidence(evidence_id=f"apta-708-r7-{field}", artifact_id=artifact.artifact_id,
                        document_sha256=artifact.sha256, source_url=artifact.url_final,
                        page_number=page_number, snippet=snippet, method="pypdf-native-text",
                        method_version=VERSION)

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


def extract_identity_r7(artifact, pages: list, *, source: str, external_id: str,
                        detail_url: str, document_url: str) -> list[ExtractedField]:
    if (source, str(external_id), artifact.sha256, artifact.byte_len) != (
            SOURCE, EXTERNAL_ID, EXPECTED_SHA256, EXPECTED_BYTE_LEN):
        raise ValueError("APTA/708: source/external/SHA/byte drift")
    return _identity_fields(artifact, pages, detail_url=detail_url, document_url=document_url)


def document_identity_ids(candidate, pages: list) -> set[str]:
    if candidate.source != SOURCE or str(candidate.external_id) != EXTERNAL_ID:
        raise ValueError("APTA/708: source/external mismatch")
    if len(pages) == RETIFICATION_PAGES:
        text = pages[0] if isinstance(pages[0], str) else pages[0].text
        if "Aragar" in text:
            return {EXTERNAL_ID}
    texts = _texts(pages)
    joined = "\n".join(texts)
    if "CONCURSO" not in joined or "01/2026" not in joined or "Municipal de Aragar" not in joined:
        raise ValueError("APTA/708: identity markers drift")
    return {EXTERNAL_ID}


def extract_identity(artifact, pages: list, *, source: str, external_id: str, as_of: date,
                     detail_url: str = DETAIL_URL, document_url: str = DOCUMENT_URL) -> list[ExtractedField]:
    if not (date(2026, 8, 17) <= as_of <= date(2026, 9, 20)):
        return [ExtractedField(field_name="edital_numero", state=FieldState.FAILED,
                               reason="APTA/708: preserved opportunity is outside its proven inscription window")]
    try:
        return extract_identity_r7(artifact, pages, source=source, external_id=external_id,
                                   detail_url=detail_url, document_url=document_url)
    except ValueError as exc:
        # Shared extraction historically returns FAILED fields so revalidation
        # can report a bounded blocker; the strict R7 entry point still raises.
        return [ExtractedField(field_name="edital_numero", state=FieldState.FAILED,
                               reason=str(exc))]


def preflight(content: bytes, *, as_of: date, pages: list | None = None) -> dict:
    if len(content) != EXPECTED_BYTE_LEN or hashlib.sha256(content).hexdigest() != EXPECTED_SHA256:
        raise ValueError("APTA/708: artifact SHA/byte drift")
    if pages is not None:
        _texts(pages)
    return {"source": SOURCE, "external_id": EXTERNAL_ID, "sha256": EXPECTED_SHA256,
            "byte_len": EXPECTED_BYTE_LEN, "pages": EXPECTED_PAGES,
            "edital_numero": "01/2026", "current_as_of": as_of.isoformat(),
            "current": date(2026, 8, 17) <= as_of <= date(2026, 9, 20), "network": False}
