"""OCR only acquired director-selection documents with missing native page text."""
import json,hashlib
from pathlib import Path
from app.tenderproof.processing import ProcessingService,ProcessingLimits

def main():
    source=Path('/evidence/current-documents-20260909T160517Z');out=Path('/evidence/current-ocr');out.mkdir(exist_ok=True)
    service=ProcessingService(out/'jobs');report=[]
    for d in json.loads((source/'report.json').read_text())['documents']:
        if d['format']!='pdf' or not d.get('sha256'):continue
        native=source/(d['sha256']+'-pages.json')
        pages=json.loads(native.read_text()) if native.exists() else []
        if pages and all(p['text'].strip()for p in pages):continue
        raw=(source/(d['sha256']+'.pdf')).read_bytes()
        if hashlib.sha256(raw).hexdigest()!=d['sha256']:raise ValueError('OCR input hash mismatch')
        row={'url':d['url'],'sha256':d['sha256']};report.append(row)
        job=service.enqueue('faperr-current-ocr',raw,operation='ocr_pdf',limits=ProcessingLimits(max_pages=200,max_bytes=30*1024*1024,total_seconds=600,operation_seconds=590,max_output_bytes=8*1024*1024))
        job=service.execute(job['id'],'faperr-current-ocr');row.update(job_id=job['id'],state=job['state'],error=job.get('error'))
        if job['state']=='succeeded':
            result=service.result(job['id'],'faperr-current-ocr');(out/(d['sha256']+'.json')).write_text(json.dumps(result,ensure_ascii=False),encoding='utf-8')
            row.update(total_pages=result['total_pages'],empty_pages=sum(not p['text'].strip()for p in result['pages']))
        (out/'verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(row),flush=True)

if __name__=='__main__':main()
