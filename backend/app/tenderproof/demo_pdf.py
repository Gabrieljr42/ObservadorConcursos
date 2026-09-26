"""TenderProof — utilitário para gerar PDFs textuais mínimos (demo/tests).

Gera PDFs reais e legíveis via pypdf (sem OCR), usados apenas para o modo
``mock`` claramente sintético e para testes offline. Nunca apresentado como
observação oficial.
"""

from __future__ import annotations

from io import BytesIO


def _escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def make_text_pdf(pages: list[str]) -> bytes:
    from pypdf import PdfWriter
    from pypdf.generic import (
        ArrayObject,
        DecodedStreamObject,
        DictionaryObject,
        NameObject,
    )

    writer = PdfWriter()
    for page_text in pages:
        page = writer.add_blank_page(width=612, height=792)
        lines = [line for line in page_text.splitlines() if line.strip()] or [""]
        ops = ["BT /F1 11 Tf 72 740 Td 15 TL"]
        for i, line in enumerate(lines[:60]):
            ops.append(f"({_escape(line[:160])}) Tj")
            if i < len(lines[:60]) - 1:
                ops.append("T*")
        ops.append("ET")
        stream = DecodedStreamObject()
        stream.set_data(" ".join(ops).encode("cp1252", errors="replace"))
        font = DictionaryObject()
        font[NameObject("/Type")] = NameObject("/Font")
        font[NameObject("/Subtype")] = NameObject("/Type1")
        font[NameObject("/BaseFont")] = NameObject("/Helvetica")
        font[NameObject("/Encoding")] = NameObject("/WinAnsiEncoding")
        resources = DictionaryObject()
        fonts = DictionaryObject()
        fonts[NameObject("/F1")] = font
        resources[NameObject("/Font")] = fonts
        page[NameObject("/Resources")] = resources
        page[NameObject("/Contents")] = stream
        # Garante referência indireta do stream no writer.
        stream.indirect_reference = writer._add_object(stream)  # type: ignore[attr-defined]
        page[NameObject("/Contents")] = ArrayObject([stream.indirect_reference])
    buffer = BytesIO()
    writer.write(buffer)
    return buffer.getvalue()
