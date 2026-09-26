"""Validate review extraction against an already preserved PDF, without network."""
import hashlib
import argparse
import json
from pathlib import Path

from app.tenderproof.processing import extract_pages_isolated


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input')
    parser.add_argument('output')
    parser.add_argument('--max-bytes', type=int, default=30_000_000)
    parser.add_argument('--ocr-timeout', type=float, default=120)
    parser.add_argument('--reuse-completed', action='store_true')
    args = parser.parse_args()
    if not 1024 <= args.max_bytes <= 64*1024*1024:
        parser.error('--max-bytes must be between 1024 and 64 MiB')
    content = Path(args.input).read_bytes()
    pages, total, processed, truncated, errors = extract_pages_isolated(
        content, artifact_id='preserved-ocr-validation', owner_id='ocr-validation',
        max_pages=200, max_bytes=args.max_bytes, operation='ocr_pdf', ocr_timeout_s=args.ocr_timeout,
        reuse_completed=args.reuse_completed)
    assert not errors and not truncated and total == processed
    recognized = [p for p in pages if p.extraction_method == 'ocr_tesseract']
    assert recognized
    assert all(p.ocr['review_required'] and p.ocr['words'] and p.processing_job_id for p in recognized)
    report = {'input_sha256':hashlib.sha256(content).hexdigest(),
              'total_pages':total, 'pages':[p.model_dump(mode='json') for p in pages],
              'approved':False, 'published':False}
    Path(args.output).write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'pages':total,'ocr_pages':len(recognized),'provenance_preserved':True}))


if __name__ == '__main__':
    main()
