"""Public document probes, preserving exact method/body and verified PDF evidence."""
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import httpx
from pypdf import PdfReader
from io import BytesIO

ROOT=Path('tests/fixtures/tenderproof_batch99_regions')

def probe(row):
    out={**row,'observed_at':datetime.now(timezone.utc).isoformat(),'tls_verified':True}
    try:
        with httpx.Client(timeout=25,trust_env=False,follow_redirects=False) as client:
            with client.stream(row.get('method','GET'),row['url'],content=row.get('body','').encode('ascii'),headers=row.get('headers',{})) as response:
                chunks=[];size=0
                for chunk in response.iter_bytes():
                    size+=len(chunk)
                    if size>30*1024*1024:raise ValueError('PDF exceeds30MiB')
                    chunks.append(chunk)
                raw=b''.join(chunks)
                sha=hashlib.sha256(raw).hexdigest()
                file=row['source']+'-'+sha[:16]+('.pdf' if raw.startswith(b'%PDF-') else '.response')
                (ROOT/file).write_bytes(raw)
                out.update(status=response.status_code,content_type=response.headers.get('content-type'),location=response.headers.get('location'),bytes=len(raw),sha256=sha,file=file)
                if response.status_code==200 and raw.startswith(b'%PDF-'):
                    pdf=PdfReader(BytesIO(raw))
                    out['pages']=len(pdf.pages)
                    if len(pdf.pages)>60:raise ValueError('PDF exceeds60pages')
                    text='\n'.join(page.extract_text() or '' for page in pdf.pages)
                    textfile=file+'.txt';(ROOT/textfile).write_text(text,encoding='utf-8')
                    out.update(text_file=textfile,text_sha256=hashlib.sha256(text.encode()).hexdigest(),first_page_excerpt=text[:3500])
                else:out['error']='response not successful PDF'
        out['client_closed']=client.is_closed
    except Exception as exc:out.update(error_type=type(exc).__name__,error=str(exc)[:450])
    return out

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--targets',type=Path,required=True);p.add_argument('--output',type=Path,required=True);args=p.parse_args()
    rows=[probe(row) for row in json.loads(args.targets.read_text(encoding='utf-8'))]
    args.output.write_text(json.dumps({'scope':'Public documents only, exact observed requests, TLS verified, no production','documents':rows},ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps([{k:r.get(k) for k in ('source','status','pages','bytes','sha256','error')} for r in rows]))
