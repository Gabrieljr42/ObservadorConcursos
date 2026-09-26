"""Traverse published annual links and preserve current editorial document manifests."""
import hashlib,json,time
from pathlib import Path
from datetime import datetime,timezone
import httpx
from app.tenderproof.fapeal_pages import LISTING,discover_categories,parse_listing,parse_detail

def main():
    root=Path('.tenderproof/product-completion/fapeal')/datetime.now(timezone.utc).strftime('inventory-%Y%m%dT%H%M%SZ');root.mkdir()
    report={'pages':[],'details':[],'errors':[],'source_integrated':False}
    def save():(root/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    with httpx.Client(timeout=25,trust_env=False,follow_redirects=False) as client:
        def get(url):
            with client.stream('GET',url)as r:
                r.raise_for_status();body=bytearray()
                for chunk in r.iter_bytes():
                    body.extend(chunk)
                    if len(body)>4*1024*1024:raise ValueError('HTML limit')
            raw=bytes(body);sha=hashlib.sha256(raw).hexdigest();(root/(sha+'.html')).write_bytes(raw)
            return raw,sha
        raw,sha=get(LISTING);report['listing_sha256']=sha;categories=discover_categories(raw);report['categories']=categories
        pending=list(categories);seen=set();current={};latest=max(categories.values())
        while pending:
            url=pending.pop(0)
            if url in seen:continue
            if len(seen)>=500:raise ValueError('archive page limit')
            seen.add(url)
            try:
                raw,sha=get(url);parsed=parse_listing(raw,url);report['pages'].append({'url':url,'sha256':sha,**parsed});pending.extend(parsed['next_urls'])
                if categories.get(url.split('/page/')[0].rstrip('/')+'/')==latest:
                    for item in parsed['items']:current[item['url']]=item
            except Exception as exc:report['errors'].append({'url':url,'error':type(exc).__name__+': '+str(exc)})
            save();time.sleep(1)
        report['current_cohort_year']=latest
        for url in current:
            try:
                raw,sha=get(url);parsed=parse_detail(raw,url);report['details'].append({'sha256':sha,**parsed})
            except Exception as exc:report['errors'].append({'url':url,'error':type(exc).__name__+': '+str(exc)})
            save();print(json.dumps({'pages':len(report['pages']),'details':len(report['details']),'errors':len(report['errors'])}),flush=True);time.sleep(1)
    report['finished_at']=datetime.now(timezone.utc).isoformat();save();print(str(root),flush=True)

if __name__=='__main__':main()
