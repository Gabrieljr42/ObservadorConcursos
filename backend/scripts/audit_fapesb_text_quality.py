"""Audit acquired REDA text; nonempty text is not proof of correct font decoding."""
import hashlib
import json
from pathlib import Path


def main():
    root = Path('.tenderproof/product-completion/fapesb')
    source = root / 'current-documents-20260909T165904Z'
    manifest = json.loads((source / 'report.json').read_text(encoding='utf-8'))
    recovered = set()
    for folder in ('reda-ocr', 'reda-quality-ocr'):
        verification = root / folder / 'verification.json'
        if not verification.exists():
            continue
        for row in json.loads(verification.read_text(encoding='utf-8')):
            if row['state'] != 'succeeded':
                continue
            data = json.loads((root / folder / (row['sha256'] + '.json')).read_text(encoding='utf-8'))
            if len(data['pages']) == row['pages'] and all(p['text'].strip() for p in data['pages']):
                recovered.add(row['sha256'])
    pending = []
    for doc in manifest['documents']:
        sha = doc['sha256']
        if hashlib.sha256((source / (sha + '.pdf')).read_bytes()).hexdigest() != sha:
            raise ValueError('PDF digest mismatch')
        pages = json.loads((source / (sha + '-pages.json')).read_text(encoding='utf-8'))
        damaged = [{'page': p['page_number'], 'unexpected_control_characters': sum(ord(c) < 32 and c not in '\n\r\t' for c in p['text'])} for p in pages]
        damaged = [p for p in damaged if p['unexpected_control_characters']]
        if damaged and sha not in recovered:
            pending.append({'sha256': sha, 'url': doc['url'], 'title': doc['title'], 'pages': damaged, 'state': 'requires_raster_or_visual_reading'})
    report = {'method': 'Control-character evidence of damaged native PDF text; clean text still requires semantic review.', 'documents_checked': len(manifest['documents']), 'pending': pending, 'pending_pages': sum(len(d['pages']) for d in pending)}
    (root / 'reda-text-quality-audit.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    path = root / 'reda-reading-completion.json'
    completion = json.loads(path.read_text(encoding='utf-8'))
    completion.update(text_quality_review_complete=False, additional_damaged_font_files=len(pending), additional_damaged_font_pages=report['pending_pages'], quality_evidence='reda-text-quality-audit.json', recovered_ocr_files=len(recovered), semantic_review_pending=True)
    path.write_text(json.dumps(completion, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'documents_checked': report['documents_checked'], 'pending_files': len(pending), 'pending_pages': report['pending_pages']}))


if __name__ == '__main__':
    main()
