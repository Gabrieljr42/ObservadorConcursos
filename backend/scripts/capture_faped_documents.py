"""Acquire the documents discovered in the public personnel section."""
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.tenderproof.faped_parser import parse_personnel, validate_document
from app.tenderproof.processing import extract_pages_isolated


def main():
    root = Path(__file__).resolve().parents[1] / '.tenderproof/product-completion/faped'
    rows = parse_personnel((root / 'celetista.html').read_text(encoding='iso-8859-1'))
    output = root / datetime.now(timezone.utc).strftime('documents-%Y%m%dT%H%M%SZ')
    output.mkdir()
    records = []
    with httpx.Client(timeout=25, follow_redirects=False) as client:
        for call in rows:
            for document in call['documents']:
                record = {'identity': call['identity'], **document}
                try:
                    validate_document(document['url'])
                    with client.stream('GET', document['url']) as response:
                        response.raise_for_status()
                        body = bytearray()
                        for chunk in response.iter_bytes():
                            body.extend(chunk)
                            if len(body) > 15_000_000:
                                raise ValueError('document limit exceeded')
                    digest = hashlib.sha256(body).hexdigest()
                    (output / (digest + '.pdf')).write_bytes(body)
                    record.update(sha256=digest, byte_len=len(body))
                    pages, total, processed, truncated, errors = extract_pages_isolated(bytes(body),
                        artifact_id='faped-' + digest, owner_id='faped-scope-audit',
                        max_bytes=15_000_000, max_pages=150)
                    (output / (digest + '-pages.json')).write_text(json.dumps(
                        [p.model_dump(mode='json') for p in pages], ensure_ascii=False), encoding='utf-8')
                    record.update(total_pages=total, processed_pages=processed, truncated=truncated, errors=errors)
                except Exception as exc:
                    record['error'] = type(exc).__name__ + ': ' + str(exc)[:180]
                records.append(record)
                (output / 'verification.json').write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding='utf-8')
                print(json.dumps(record, ensure_ascii=True), flush=True)
    print(str(output), flush=True)


if __name__ == '__main__':
    main()
