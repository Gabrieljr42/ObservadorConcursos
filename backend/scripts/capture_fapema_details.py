"""Acquire every editorial detail from an observed FAPEMA category inventory."""
import argparse,hashlib,json,time
from datetime import datetime,timezone
from pathlib import Path
import httpx
from app.tenderproof.fapema_listing import detail_url
from app.tenderproof.fapema_detail import parse_detail


def main():
    parser=argparse.ArgumentParser();parser.add_argument('inventory',type=Path);args=parser.parse_args()
    inventory=json.loads(args.inventory.read_text(encoding='utf-8'))
    root=args.inventory.parent.parent/datetime.now(timezone.utc).strftime('details-%Y%m%dT%H%M%SZ');root.mkdir()
    report={'inventory':str(args.inventory),'details':[],'errors':[],'source_integrated':False,'published':False}
    with httpx.Client(timeout=25,trust_env=False,follow_redirects=False) as client:
        for row in inventory['unique_calls']:
            url=row['url'];record={'url':url}
            try:
                detail_url(url)
                with client.stream('GET',url) as response:
                    record['status']=response.status_code;response.raise_for_status();body=bytearray()
                    for chunk in response.iter_bytes():
                        body.extend(chunk)
                        if len(body)>4000000:raise ValueError('HTML limite de 4 MB')
                sha=hashlib.sha256(body).hexdigest();(root/(sha+'.html')).write_bytes(body);record['sha256']=sha
                record.update(parse_detail(body.decode('utf-8-sig'),url));report['details'].append(record)
            except Exception as exc:
                record['error']=type(exc).__name__+': '+str(exc);report['errors'].append(record)
            (root/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
            print(json.dumps({'details':len(report['details']),'errors':len(report['errors']),'total':len(inventory['unique_calls'])}),flush=True)
            time.sleep(1)
    report['finished_at']=datetime.now(timezone.utc).isoformat()
    (root/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print(str(root),flush=True)


if __name__=='__main__':main()
