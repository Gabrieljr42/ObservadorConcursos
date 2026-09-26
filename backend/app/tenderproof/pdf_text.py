"""TenderProof Fase 2 — extração de texto preservando a página física do PDF."""

from __future__ import annotations

from io import BytesIO

from app.tenderproof.contracts import PageText


def extract_pages(
    content: bytes,
    *,
    artifact_id: str,
    max_pages: int = 60,
) -> tuple[list[PageText], int, int, bool, list[str]]:
    """Extrai texto por página física.

    Retorna (páginas, total, processadas, truncado, erros_por_página).
    Diferencia total de páginas e páginas efetivamente processadas; informa
    truncamento, falhas por página e ausência de texto. Sem OCR.
    """
    from pypdf import PdfReader

    errors: list[str] = []
    try:
        reader = PdfReader(BytesIO(content))
    except Exception as exc:
        errors.append(f"leitura do PDF falhou: {exc}")
        return [], 0, 0, False, errors

    total = len(reader.pages)
    to_process = min(total, max_pages)
    truncated = total > max_pages
    pages: list[PageText] = []
    for index in range(to_process):
        page_number = index + 1  # física, 1-indexed
        try:
            raw = reader.pages[index].extract_text() or ""
        except Exception as exc:
            errors.append(f"página {page_number}: falha de extração ({exc})")
            pages.append(
                PageText(
                    artifact_id=artifact_id,
                    page_number=page_number,
                    text="",
                    char_count=0,
                    truncated=False,
                    error=str(exc)[:300],
                )
            )
            continue
        normalized = _normalize(raw)
        pages.append(
            PageText(
                artifact_id=artifact_id,
                page_number=page_number,
                text=normalized,
                char_count=len(normalized),
                truncated=False,
                error=None,
            )
        )
    if truncated:
        errors.append(f"truncado: {total} páginas totais, {to_process} processadas (limite {max_pages})")
    if to_process and not any(p.text.strip() for p in pages):
        errors.append("documento sem texto extraível (possível PDF escaneado/protegido)")
    return pages, total, to_process, truncated, errors


def _normalize(value: str) -> str:
    value = value.replace("\x00", " ").replace("\xa0", " ")
    lines = [" ".join(line.split()) for line in value.splitlines()]
    return "\n".join(line for line in lines if line)
