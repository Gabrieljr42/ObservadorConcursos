"""Resume the full observed FAPESQ detail inventory, preserving each attempt."""
import argparse
import hashlib
import json
import os
import time
from pathlib import Path
from datetime import datetime,timezone
import httpx
from app.tenderproof.fapesq_detail import detail_url,parse_detail


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seconds',type=int,default=600)
    args=parser.parse_args()
    if not 30<=args.seconds<=600:parser.error('seconds must be between 30 and 600')
    base=Path('.tenderproof/product-completion/fapesq')
    summary=json.loads((base/'annual-inventory-summary.json').read_text(encoding='utf-8'))
    inventory_path=Path(summary['report']);raw=inventory_path.read_bytes()
    inventory=json.loads(raw);items={x['url']:x for x in inventory['items']}
    fingerprint=hashlib.sha256(raw).hexdigest()
    output=base/('details-'+fingerprint[:16]);output.mkdir(parents=True,exist_ok=True)
    receipts={}
    for url in items:
        path=output/(hashlib.sha256(url.encode()).hexdigest()+'.json')
        if path.exists():
            row=json.loads(path.read_text(encoding='utf-8'))
            if row['url']!=url:raise ValueError('receipt identity mismatch')
            receipts[url]=row
    deadline=time.monotonic()+args.seconds
    def save_summary():
        result={'inventory_sha256':fingerprint,'inventory':str(inventory_path),'output':str(output),
                'updated_at':datetime.now(timezone.utc).isoformat(),'expected':len(items),
                'attempted':len(receipts),'pending':len(items)-len(receipts),
                'parsed':sum(r.get('manifest') is not None for r in receipts.values()),
                'errors':[{'url':r['url'],'error':r['error'],'status':r.get('status')} for r in receipts.values() if r.get('error')],
                'documents':sum(len(r.get('manifest',{}).get('documents',[])) for r in receipts.values()),
                'source_integrated':False,'published':False}
        (base/'detail-inventory-summary.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
        return result
    with httpx.Client(trust_env=False,timeout=25,follow_redirects=False) as client:
        for url,item in items.items():
            if url in receipts:continue
            if time.monotonic()+26>=deadline:break
            key=hashlib.sha256(url.encode()).hexdigest()
            row={'url':url,'observed_title':item['title'],'checked_at':datetime.now(timezone.utc).isoformat()}
            try:
                detail_url(url)
                with client.stream('GET',url) as response:
                    row['status']=response.status_code;row['redirect']=response.headers.get('location')
                    content=b''
                    for chunk in response.iter_bytes():
                        content+=chunk
                        if len(content)>4000000:raise ValueError('response_limit')
                (output/(key+'.html')).write_bytes(content)
                row.update(file=key+'.html',sha256=hashlib.sha256(content).hexdigest())
                response.raise_for_status()
                row['manifest']=parse_detail(content.decode('utf-8'),url)
            except Exception as exc:row['error']=type(exc).__name__+': '+str(exc)
            temporary=output/(key+'.tmp');temporary.write_text(json.dumps(row,ensure_ascii=False,indent=2),encoding='utf-8')
            os.replace(temporary,output/(key+'.json'));receipts[url]=row
            if len(receipts)%20==0:
                status=save_summary();print(json.dumps({k:status[k] for k in ('expected','attempted','pending','parsed','documents')}),flush=True)
            time.sleep(1)
    status=save_summary()
    print(json.dumps({k:status[k] for k in ('expected','attempted','pending','parsed','documents','output')}),flush=True)


if __name__=='__main__':main()
