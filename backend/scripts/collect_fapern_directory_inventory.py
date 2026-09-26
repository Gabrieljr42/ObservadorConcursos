"""Read-only inventory of the share linked by the official state service."""
import hashlib
import json
import time
from collections import deque
from datetime import datetime, timezone
from pathlib import Path

import httpx
from bs4 import BeautifulSoup
from app.tenderproof.fapern_drive import ROOT, parse_directory


def main():
    base=Path('.tenderproof/product-completion/fapern')
    service=json.loads((base/'service-discovery.json').read_text(encoding='utf-8'))
    matches=[s for s in service['fapern_matches'] if s['title']['rendered'].startswith('Editais')]
    assert len(matches)==1
    share=matches[0]['acf']['link_externo']
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    output=base/('inventory-'+stamp);output.mkdir()
    report={'share_url':share,'started_at':stamp,'directories':[],'files':[],'errors':[],
            'pending':[],'complete':False,'source_integrated':False}
    started=time.monotonic()
    with httpx.Client(trust_env=False,timeout=35,follow_redirects=False) as client:
        response=client.get(share);assert response.status_code==200
        soup=BeautifulSoup(response.text,'html.parser')
        token=soup.select_one('#sharingToken')['value']
        assert share=='https://drive.rn.gov.br/index.php/s/'+token
        assert soup.select_one('#mimetype')['value']=='httpd/unix-directory'
        queue=deque([{'path':ROOT,'url':'https://drive.rn.gov.br'+ROOT}]);seen=set()
        while queue and len(seen)<1000 and time.monotonic()-started<900:
            current=queue.popleft()
            if current['path'] in seen: continue
            seen.add(current['path'])
            try:
                with client.stream('PROPFIND',current['url'],auth=(token,''),
                    headers={'Depth':'1','Content-Type':'application/xml'},
                    content='<d:propfind xmlns:d="DAV:"><d:allprop/></d:propfind>') as response:
                    if response.status_code!=207: raise ValueError('http_'+str(response.status_code))
                    raw=bytearray()
                    for chunk in response.iter_bytes():
                        raw.extend(chunk)
                        if len(raw)>4*1024*1024: raise ValueError('response_size_limit')
                content=bytes(raw);children=parse_directory(content,current['path'])
                name=hashlib.sha256(current['path'].encode()).hexdigest()+'.xml'
                (output/name).write_bytes(content)
                report['directories'].append({'path':current['path'],'response_file':name,
                    'sha256':hashlib.sha256(content).hexdigest(),'child_count':len(children)})
                for child in children:
                    if child['is_directory']: queue.append(child)
                    else: report['files'].append(child)
            except (ValueError,httpx.HTTPError) as exc:
                report['errors'].append({'path':current['path'],'error_type':type(exc).__name__})
            report['pending']=[r['path'] for r in queue]
            (output/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
            if len(seen)%20==0:
                print(json.dumps({'directories':len(seen),'files':len(report['files']),'pending':len(queue),'errors':len(report['errors'])}),flush=True)
        report['complete']=not queue and not report['errors']
        report['finished_at']=datetime.now(timezone.utc).isoformat()
        (output/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
        print(json.dumps({'report':str(output/'report.json'),'directories':len(seen),'files':len(report['files']),
                          'complete_directory_inventory':report['complete'],'source_integrated':False}),flush=True)


if __name__=='__main__': main()
