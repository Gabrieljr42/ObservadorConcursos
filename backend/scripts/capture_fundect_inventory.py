"""Fresh current API and every previous-call link published by FUNDECT."""
import hashlib,json,time
from datetime import datetime,timezone
from pathlib import Path
import httpx
from app.tenderproof.fundect_pages import LISTING,API,HISTORY,history_items,parse_api,parse_detail

def main():
    root=Path('.tenderproof/product-completion/fundect')/datetime.now(timezone.utc).strftime('inventory-%Y%m%dT%H%M%SZ');root.mkdir()
    report={'acquisitions':[],'details':[],'errors':[],'source_integrated':False}
    def save():(root/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    with httpx.Client(timeout=25,trust_env=False,follow_redirects=False)as c:
        def get(url,ext='html'):
            with c.stream('GET',url)as r:
                r.raise_for_status();raw=bytearray()
                for chunk in r.iter_bytes():
                    raw.extend(chunk)
                    if len(raw)>4*1024*1024:raise ValueError('HTML/JSON byte limit')
            raw=bytes(raw);sha=hashlib.sha256(raw).hexdigest();(root/(sha+'.'+ext)).write_bytes(raw)
            report['acquisitions'].append({'url':url,'sha256':sha,'format':ext});return raw,sha
        get(LISTING);raw,sha=get(API,'json');report['current']=parse_api(raw);raw,sha=get(HISTORY);items=history_items(raw);report['history_items']=items;save()
        for url in items:
            try:
                raw,sha=get(url);report['details'].append({'sha256':sha,**parse_detail(raw,url)})
            except Exception as e:report['errors'].append({'url':url,'error':type(e).__name__+': '+str(e)})
            save();print(json.dumps({'details':len(report['details']),'errors':len(report['errors'])}),flush=True);time.sleep(1)
    report['finished_at']=datetime.now(timezone.utc).isoformat();save();print(str(root),flush=True)

if __name__=='__main__':main()
