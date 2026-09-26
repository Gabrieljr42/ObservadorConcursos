"""Fresh FAPEMIG listing and documents in the newest observed annual cohort or updated since it."""
import hashlib,json,re,time
from datetime import datetime,timezone
from pathlib import Path
import httpx
from app.tenderproof.fapemig_pages import LISTING,DETAIL,parse_api,documents,document_url
from app.tenderproof.processing import extract_pages_isolated


def main():
    root=Path('.tenderproof/product-completion/fapemig')/datetime.now(timezone.utc).strftime('current-documents-%Y%m%dT%H%M%SZ')
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
        calls=[];url=LISTING
        while True:
            data,pagination=parse_api(raw,url)
            for c in data:
                if c['status_chamada']!='aberta':continue
                docs,pending=documents(c)
                calls.append({'url':DETAIL+c['slug'],'id':c['id'],'title':c['titulo'],'documents':docs,'pending_links':pending})
            if pagination['page']>=pagination['total_pages']:break
            url=LISTING.replace('page=1&','page='+str(pagination['page']+1)+'&')
            raw=acquire(url,8*1024*1024);sha=hashlib.sha256(raw).hexdigest();(root/(sha+'.json')).write_bytes(raw)
            time.sleep(1)
        report.update(listing_sha256=digest,calls=calls,selection_rule='Every status_chamada aberta call across all published API pages, including continuous flow.',pending_links=[p for c in calls for p in c['pending_links']])
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
                        pages,total,processed,truncated,errors=extract_pages_isolated(content,artifact_id='fapemig-'+digest,owner_id='fapemig-source-audit',max_bytes=30*1024*1024,max_pages=200)
                        (root/(digest+'-pages.json')).write_text(json.dumps([p.model_dump(mode='json') for p in pages],ensure_ascii=False),encoding='utf-8')
                        row.update(total_pages=total,processed_pages=processed,truncated=truncated,errors=errors)
                    else:row['reading_pending']=True
                except Exception as exc:row['error']=type(exc).__name__+': '+str(exc)
                save();print(json.dumps({'documents':len(report['documents']),'pages':row.get('processed_pages'),'error':row.get('error')}),flush=True)
                time.sleep(1)
    report['finished_at']=datetime.now(timezone.utc).isoformat();save();print(str(root),flush=True)


if __name__=='__main__':main()
