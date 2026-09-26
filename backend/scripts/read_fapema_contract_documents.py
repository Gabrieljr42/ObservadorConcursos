"""Read all documents in the preserved detail-contract inspection, not source-wide acceptance."""
import hashlib,json,time
from datetime import datetime,timezone
from pathlib import Path
import httpx
from app.tenderproof.fapema_detail import parse_detail,document_url
from app.tenderproof.processing import extract_pages_isolated


def main():
    source=Path('.tenderproof/product-completion/fapema/detail-contract-inspection')
    root=source.parent/datetime.now(timezone.utc).strftime('contract-documents-%Y%m%dT%H%M%SZ');root.mkdir()
    report={'calls':[],'documents':[],'source_integrated':False,'published':False}
    with httpx.Client(timeout=25,trust_env=False,follow_redirects=False) as client:
        for row in json.loads((source/'verification.json').read_text(encoding='utf-8')):
            raw=(source/(row['sha256']+'.html')).read_bytes()
            if hashlib.sha256(raw).hexdigest()!=row['sha256']:raise ValueError('HTML hash mismatch')
            call=parse_detail(raw.decode('utf-8-sig'),row['url']);report['calls'].append(call)
            for doc in call['documents']:
                record={'call_url':row['url'],**doc};report['documents'].append(record)
                try:
                    url=document_url(doc['url'])
                    with client.stream('GET',url) as response:
                        response.raise_for_status();content=bytearray()
                        for chunk in response.iter_bytes():
                            content.extend(chunk)
                            if len(content)>30*1024*1024:raise ValueError('document byte limit')
                    digest=hashlib.sha256(content).hexdigest();(root/(digest+'.pdf')).write_bytes(content)
                    record.update(sha256=digest,bytes=len(content))
                    pages,total,processed,truncated,errors=extract_pages_isolated(bytes(content),
                        artifact_id='fapema-'+digest,owner_id='fapema-scope-audit',max_bytes=30*1024*1024,max_pages=200)
                    (root/(digest+'-pages.json')).write_text(json.dumps([p.model_dump(mode='json') for p in pages],ensure_ascii=False),encoding='utf-8')
                    record.update(total_pages=total,processed_pages=processed,truncated=truncated,errors=errors)
                except Exception as exc:record['error']=type(exc).__name__+': '+str(exc)
                (root/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
                print(json.dumps({'documents':len(report['documents']),'pages':record.get('processed_pages'),'error':record.get('error')}),flush=True)
                time.sleep(1)
    report['finished_at']=datetime.now(timezone.utc).isoformat()
    (root/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print(str(root),flush=True)


if __name__=='__main__':main()
