"""Traverse the current FAPEMA menu and every observed category page."""
import hashlib,json,time
from datetime import datetime,timezone
from pathlib import Path
import httpx
from app.tenderproof.fapema_listing import HOST,discover_categories,parse_listing,listing_url


def main():
    root=Path('.tenderproof/product-completion/fapema')/datetime.now(timezone.utc).strftime('categories-%Y%m%dT%H%M%SZ');root.mkdir(parents=True)
    report={'pages':[],'errors':[],'source_integrated':False,'published':False}
    def save():
        (root/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    with httpx.Client(timeout=25,trust_env=False,follow_redirects=False) as client:
        def fetch(url):
            with client.stream('GET',url) as response:
                response.raise_for_status();body=bytearray()
                for chunk in response.iter_bytes():
                    body.extend(chunk)
                    if len(body)>4000000:raise ValueError('HTML limite 4 MB')
            sha=hashlib.sha256(body).hexdigest();(root/(sha+'.html')).write_bytes(body)
            return body.decode('utf-8-sig'),sha
        menu,sha=fetch(HOST+'/inicio/');report['menu_sha256']=sha
        pending=discover_categories(menu);report['categories']=list(pending);seen=set();calls={}
        while pending:
            url=pending.pop(0)
            if url in seen:continue
            seen.add(url)
            if len(seen)>500:raise ValueError('limite operacional de páginas')
            try:
                listing_url(url);html,sha=fetch(url);parsed=parse_listing(html,url)
                report['pages'].append({'url':url,'sha256':sha,**parsed});pending.extend(parsed['next_urls'])
                for row in parsed['items']:calls[row['url']]=row
            except Exception as exc:report['errors'].append({'url':url,'error':type(exc).__name__+': '+str(exc)})
            report['unique_calls']=list(calls.values());save()
            print(json.dumps({'pages':len(report['pages']),'calls':len(calls),'errors':len(report['errors'])}),flush=True)
            time.sleep(1)
    report['finished_at']=datetime.now(timezone.utc).isoformat();save()
    print(str(root),flush=True)


if __name__=='__main__':main()
