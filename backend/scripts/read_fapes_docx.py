"""Read already acquired Word attachments; run in an offline disposable container."""
import argparse
import hashlib
import json
from pathlib import Path
from app.tenderproof.docx_text import extract_docx


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    rows = json.loads((args.input / 'verification.json').read_text(encoding='utf-8'))
    results = []
    for row in rows:
        record = {'panel_id': row['panel_id'], 'url': row['url'], 'sha256': row['sha256']}
        try:
            if row['format'] != 'docx':
                raise ValueError('legacy Word reader pending')
            if row['file'] != row['sha256'] + '.docx':
                raise ValueError('receipt file identity mismatch')
            raw = (args.input / row['file']).read_bytes()
            if hashlib.sha256(raw).hexdigest() != row['sha256']:
                raise ValueError('acquired bytes hash mismatch')
            data = extract_docx(raw)
            (args.output / (row['sha256'] + '.json')).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
            record.update(paragraphs=len(data['paragraphs']), pending_features=data['pending_features'], review_required=True)
        except Exception as exc:
            record['error'] = type(exc).__name__ + ': ' + str(exc)
        results.append(record)
    (args.output / 'verification.json').write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'attempted': len(results), 'read': sum('paragraphs' in r for r in results),
        'paragraphs': sum(r.get('paragraphs', 0) for r in results), 'errors': [r for r in results if r.get('error')]}))


if __name__ == '__main__': main()
