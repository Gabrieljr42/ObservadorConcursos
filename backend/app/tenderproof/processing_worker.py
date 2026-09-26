"""Fixed PDF operation, usable in a credential-free subprocess or sandbox.

No shell, network calls, document instructions, external commands or dynamic code.
The surrounding executor must enforce wall time and resource isolation.
"""
import hashlib
import json
import sys
from pathlib import Path


def main():
    source, destination, pages_limit, output_limit = sys.argv[1:]
    try:
        from pypdf import PdfReader
        # Match the acquisition contract: some official endpoints prepend a few
        # ASCII newlines. Preserve the raw input and original xref offsets.
        raw = Path(source).read_bytes()
        offset = 0
        while offset < len(raw) and offset < 16 and raw[offset] in b' \t\r\n':
            offset += 1
        if raw[offset:offset + 5] != b'%PDF-':
            raise ValueError('invalid_document')
        reader = PdfReader(source, strict=offset == 0)
        if reader.is_encrypted:
            raise ValueError('invalid_document')
        if len(reader.pages) > int(pages_limit):
            raise ValueError('page_limit')
        pages = []
        consumed = 0
        for index, page in enumerate(reader.pages):
            text = page.extract_text() or ''
            consumed += len(text.encode('utf-8'))
            if consumed > int(output_limit):
                raise ValueError('output_limit')
            pages.append({'page_number': index + 1, 'text': text})
        result = {'extractor_version': 'tenderproof-pdf-v2',
                  'input_sha256': hashlib.sha256(Path(source).read_bytes()).hexdigest(),
                  'pages': pages, 'total_pages': len(reader.pages)}
        data = json.dumps(result, ensure_ascii=False).encode('utf-8')
        if len(data) > int(output_limit):
            raise ValueError('output_limit')
        Path(destination).write_bytes(data)
    except Exception as exc:
        code = ('dependency_unavailable' if isinstance(exc, ImportError) else
                str(exc) if str(exc) in ('page_limit', 'output_limit') else 'invalid_document')
        Path(destination).write_text(json.dumps({'error': code}), encoding='utf-8')
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
