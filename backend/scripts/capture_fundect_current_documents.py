"""Fresh FUNDECT listing and documents in the newest observed annual cohort or updated since it."""
import hashlib,json,re,time
from datetime import datetime,timezone
from pathlib import Path
import httpx
from app.tenderproof.fundect_pages import API,parse_api,document_url
LISTING=API
from app.tenderproof.processing import extract_pages_isolated


def main():
    root=Path('.tenderproof/product-completion/fundect')/datetime.now(timezone.utc).strftime('current-documents-%Y%m%dT%H%M%SZ')
    root.mkdir(parents=True)
    report={'listing_url':LISTING,'documents':[],'source_integrated':False,'published':False}
    def save():
        (root/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    with httpx.Client(timeout=25,trust_env=False,follow_redirects=False) as client:
        def acquire(url,limit):
            with client.stream('GET',url) as response:
                response.raise_for_status();raw=bytearray()
                for chunk in response.iter_bytes():
                    raw.extend(chunk)
                    if len(raw)>limit:raise ValueError('acquisition byte limit')
            return bytes(raw)
        raw=acquire(LISTING,4*1024*1024);digest=hashlib.sha256(raw).hexdigest()
        (root/(digest+'.json')).write_bytes(raw)
        calls=parse_api(raw)
        report.update(listing_sha256=digest,calls=calls,selection_rule='Every call returned by the current official API, without fixed year or ID filters.',pending_links=[p for c in calls for p in c['pending_links']])
        save();seen={}
        for call in calls:
            for doc in call['documents']:
                url=document_url(doc['url'])
                if url in seen:
                    seen[url]['groups'].append({'call_url':call['url'],'id':call['id']});continue
                row={**doc,'groups':[{'call_url':call['url'],'id':call['id']}]}
                seen[url]=row;report['documents'].append(row)
                try:
                    content=acquire(url,30*1024*1024);digest=hashlib.sha256(content).hexdigest()
                    (root/(digest+'.'+doc['format'])).write_bytes(content);row.update(sha256=digest,bytes=len(content))
                    if doc['format']=='pdf':
                        pages,total,processed,truncated,errors=extract_pages_isolated(content,artifact_id='fundect-'+digest,owner_id='fundect-source-audit',max_bytes=30*1024*1024,max_pages=200)
                        (root/(digest+'-pages.json')).write_text(json.dumps([p.model_dump(mode='json') for p in pages],ensure_ascii=False),encoding='utf-8')
                        row.update(total_pages=total,processed_pages=processed,truncated=truncated,errors=errors)
                    else:row['reading_pending']=True
                except Exception as exc:row['error']=type(exc).__name__+': '+str(exc)
                save();print(json.dumps({'documents':len(report['documents']),'pages':row.get('processed_pages'),'error':row.get('error')}),flush=True)
                time.sleep(1)
    report['finished_at']=datetime.now(timezone.utc).isoformat();save();print(str(root),flush=True)


if __name__=='__main__':main()
