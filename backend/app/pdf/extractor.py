from __future__ import annotations

import hashlib
from dataclasses import dataclass
from io import BytesIO

import httpx
from pypdf import PdfReader


@dataclass(slots=True)
class PdfExtractionResult:
    url: str
    ok: bool
    text: str | None = None
    pages: int | None = None
    text_hash: str | None = None
    error: str | None = None


def extract_pdf_text_from_url(
    url: str,
    *,
    client: httpx.Client | None = None,
    max_bytes: int = 30 * 1024 * 1024,
    max_pages: int = 120,
) -> PdfExtractionResult:
    """Download a PDF and extract text.

    This intentionally avoids OCR. It works for text-based edital PDFs and
    gracefully returns an error for scanned/image PDFs or malformed files.
    """
    close_client = client is None
    http_client = client or httpx.Client(timeout=60.0, follow_redirects=True)

    try:
        response = http_client.get(url)
        response.raise_for_status()
        content_type = response.headers.get('content-type', '').lower()
        payload = response.content

        if len(payload) > max_bytes:
            return PdfExtractionResult(url=url, ok=False, error=f'PDF acima do limite de {max_bytes} bytes')
        if 'pdf' not in content_type and not url.lower().split('?')[0].endswith('.pdf'):
            return PdfExtractionResult(url=url, ok=False, error=f'Conteúdo não parece ser PDF: {content_type}')

        reader = PdfReader(BytesIO(payload))
        total_pages = len(reader.pages)
        pages_to_read = min(total_pages, max_pages)
        chunks: list[str] = []

        for page_index in range(pages_to_read):
            try:
                page_text = reader.pages[page_index].extract_text() or ''
            except Exception:
                page_text = ''
            if page_text.strip():
                chunks.append(page_text)

        text = '\n'.join(chunks).strip()
        if not text:
            return PdfExtractionResult(
                url=url,
                ok=False,
                pages=total_pages,
                error='Nenhum texto extraído; possivelmente PDF escaneado ou protegido',
            )

        normalized = _normalize_pdf_text(text)
        text_hash = hashlib.sha256(normalized.encode('utf-8')).hexdigest()
        return PdfExtractionResult(url=url, ok=True, text=normalized, pages=total_pages, text_hash=text_hash)
    except Exception as exc:
        return PdfExtractionResult(url=url, ok=False, error=str(exc))
    finally:
        if close_client:
            http_client.close()


def _normalize_pdf_text(value: str) -> str:
    value = value.replace('\x00', ' ').replace('\xa0', ' ')
    lines = [' '.join(line.split()) for line in value.splitlines()]
    lines = [line for line in lines if line]
    return '\n'.join(lines)
