"""Capture every call published in the FAPERR navigation groups."""
import hashlib,json,time
from datetime import datetime,timezone
from pathlib import Path
import httpx
from app.tenderproof.faperr_pages import LISTING,discover,parse

def main():
    root=Path('.tenderproof/product-completion/faperr')/datetime.now(timezone.utc).strftime('inventory-%Y%m%dT%H%M%SZ');root.mkdir()
    report={'pages':[],'errors':[],'source_integrated':False}
    def save():(root/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    with httpx.Client(timeout=25,trust_env=False,follow_redirects=False) as c:
        def get(url):
            with c.stream('GET',url) as r:
                r.raise_for_status();raw=bytearray()
                for part in r.iter_bytes():
                    raw.extend(part)
                    if len(raw)>4*1024*1024:raise ValueError('HTML limit')
            raw=bytes(raw);sha=hashlib.sha256(raw).hexdigest();(root/(sha+'.html')).write_bytes(raw);return raw,sha
        raw,sha=get(LISTING);items=discover(raw);report.update(listing_sha256=sha,items=items)
        for url,item in items.items():
            try:
                raw,sha=get(url);report['pages'].append({'sha256':sha,'category':item['category'],**parse(raw,url)})
            except Exception as e:report['errors'].append({'url':url,'error':type(e).__name__+': '+str(e)})
            save();print(json.dumps({'pages':len(report['pages']),'errors':len(report['errors'])}),flush=True);time.sleep(1)
    report['finished_at']=datetime.now(timezone.utc).isoformat();save();print(root,flush=True)

if __name__=='__main__':main()
