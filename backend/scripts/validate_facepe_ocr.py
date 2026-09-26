"""OCR the already-acquired FACEPE documents with missing native page text."""
import json
from pathlib import Path

from app.tenderproof.processing import ProcessingService, ProcessingLimits


def main():
    evidence = Path('/evidence/documents-20260909T081333940148')
    output = Path('/output')
    items = json.loads((evidence/'reprocessing-after-windows-path-fix.json').read_text())['items']
    large = json.loads((evidence/'large-results-processing.json').read_text())['items']
    rows = {x['observed']['file_id']: x for x in items}
    rows.update({x['observed']['file_id']: x for x in large})
    selected = [x for x in rows.values() if x.get('total_pages', 0) > x.get('pages_with_text', 0)]
    service = ProcessingService(output/'batch-jobs')
    report = {'network': 'disabled by container invocation', 'items': [], 'approved': False, 'published': False}
    for item in selected:
        row = {'name': item['observed']['name'], 'input_sha256': item['document']['sha256']}
        report['items'].append(row)
        job = service.enqueue('facepe-ocr-batch', (evidence/item['document']['file']).read_bytes(),
            operation='ocr_pdf', limits=ProcessingLimits(max_pages=450, max_bytes=30*1024*1024,
                total_seconds=120, operation_seconds=110, max_output_bytes=8*1024*1024))
        job = service.execute(job['id'], 'facepe-ocr-batch')
        row.update(job_id=job['id'], state=job['state'], error=job.get('error'))
        if job['state'] == 'succeeded':
            result = service.result(job['id'], 'facepe-ocr-batch')
            name = row['input_sha256']+'-ocr.json'
            (output/name).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
            row.update(result_file=name, total_pages=result['total_pages'],
                ocr_pages=sum(p['method']=='ocr_tesseract' for p in result['pages']),
                empty_pages=sum(not p['text'].strip() for p in result['pages']))
        (output/'batch-report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
        print(json.dumps(row, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
