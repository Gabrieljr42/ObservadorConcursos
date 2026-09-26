"""Reconcile preserved acquisition, corrected manifests and completed OCR without overwriting attempts."""
import hashlib
import json
from pathlib import Path


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def main():
    root = Path('.tenderproof/product-completion/fundect')
    source = root / 'current-documents-20260909T150101Z'
    acquisition = read(source / 'report.json')
    if not acquisition.get('finished_at'):
        raise ValueError('Acquisition is not terminal')
    calls = read(source / 'manifests-v2.json')
    expected = {d['url'] for call in calls for d in call['documents']}
    if expected != {d['url'] for d in acquisition['documents']}:
        raise ValueError('Document manifest/acquisition URL mismatch')
    ocr = {d['sha256']: d for d in read(root / 'current-ocr/verification.json')}
    word = {d['sha256']: d for d in read(root / 'word-text-current/verification.json')}
    result = {'documents': [], 'source_integrated': False, 'published': False,
              'historical_documents_pending': True, 'semantic_review_pending': True}
    for doc in acquisition['documents']:
        sha = doc['sha256']
        raw = (source / (sha + '.' + doc['format'])).read_bytes()
        if hashlib.sha256(raw).hexdigest() != sha:
            raise ValueError('Acquired file hash mismatch')
        row = {'url': doc['url'], 'sha256': sha, 'format': doc['format'],
               'bindings': [{'call_url': call['url'], 'kind': d['kind'], 'title': d['title']}
                            for call in calls for d in call['documents'] if d['url'] == doc['url']]}
        if doc['format'] == 'pdf':
            native = source / (sha + '-pages.json')
            receipt = ocr.get(sha)
            if receipt and receipt['state'] == 'succeeded':
                output = root / 'current-ocr' / (sha + '.json')
                data = read(output)
                pages = data['pages']
                if data['total_pages'] != receipt['total_pages'] or len(pages) != data['total_pages']:
                    raise ValueError('OCR page count mismatch')
                row.update(method='ocr', review_required=True, evidence=str(output))
            elif native.exists():
                pages = read(native)
                row.update(method='pdf_text', evidence=str(native))
            else:
                pages = []
            row.update(pages=len(pages), empty_pages=sum(not p['text'].strip() for p in pages),
                       reading_complete=bool(pages) and all(p['text'].strip() for p in pages))
        elif doc['format'] == 'docx' and sha in word and not word[sha].get('error'):
            row.update(method='docx_text', reading_complete=True, paragraphs=word[sha]['paragraphs'],
                       pending_features=word[sha]['pending_features'], layout_review_required=True)
        else:
            row['reading_complete'] = False
        result['documents'].append(row)
    result['counts'] = {
        'files_verified': len(result['documents']),
        'files_text_read': sum(d['reading_complete'] for d in result['documents']),
        'pdf_pages': sum(d.get('pages', 0) for d in result['documents']),
        'reading_pending': [d['url'] for d in result['documents'] if not d['reading_complete']],
    }
    (root / 'current-reading-reconciled.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(result['counts']))


if __name__ == '__main__':
    main()
