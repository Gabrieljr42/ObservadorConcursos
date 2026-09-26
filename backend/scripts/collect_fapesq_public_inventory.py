"""Bounded public annual/collection discovery; no login or document publication."""
import hashlib
import json
import time
from datetime import datetime,timezone
from pathlib import Path
import httpx
from app.tenderproof.fapesq_listing import annual_url,parse_annual,parse_collection,collection_url


def main():
    base=Path('.tenderproof/product-completion/fapesq')
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    output=base/('inventory-'+stamp);output.mkdir(parents=True)
    report={'started_at':stamp,'annuals':[],'collections':[],'items':[],'errors':[],
            'complete':False,'source_integrated':False}
    deadline=time.monotonic()+300;requests=0
    with httpx.Client(trust_env=False,timeout=25,follow_redirects=False) as client:
        def fetch(url):
            nonlocal requests
            if requests>=100 or time.monotonic()>=deadline:raise ValueError('inventory limit')
            requests+=1
            with client.stream('GET',url) as response:
                content=b''
                for chunk in response.iter_bytes():
                    content+=chunk
                    if len(content)>4000000:raise ValueError('response limit')
            name=hashlib.sha256(url.encode()).hexdigest()+'.html';(output/name).write_bytes(content)
            receipt={'url':url,'status':response.status_code,'file':name,'sha256':hashlib.sha256(content).hexdigest()}
            time.sleep(1)
            return response,content,receipt
        response,_,receipt=fetch('https://fapesq.rpp.br/editais-1')
        report['entry']=receipt
        if response.status_code not in (301,302,307,308):raise ValueError('public menu redirect changed')
        start=response.headers['location'];annual_url(start)
        pending=[start];seen=set();collections=[]
        while pending:
            url=pending.pop(0)
            if url in seen:continue
            seen.add(url)
            try:
                response,content,receipt=fetch(url);response.raise_for_status()
                parsed=parse_annual(content.decode('utf-8'),url)
                report['annuals'].append({**receipt,**parsed});collections.append(parsed['collection']);pending.extend(parsed['annuals'])
            except Exception as exc:report['errors'].append({'url':url,'error':str(exc)})
            (output/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
        for start in dict.fromkeys(collections):
            url=start;visited=set()
            while url:
                try:
                    collection_url(url)
                    if url in visited:raise ValueError('pagination cycle')
                    visited.add(url)
                    response,content,receipt=fetch(url);response.raise_for_status()
                    parsed=parse_collection(content.decode('utf-8'),url)
                    report['collections'].append({**receipt,'count':len(parsed['items']),'terminal':parsed['terminal']})
                    report['items'].extend(parsed['items']);url=parsed['next_url']
                except Exception as exc:
                    report['errors'].append({'url':url,'error':str(exc)});break
                (output/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    report['finished_at']=datetime.now(timezone.utc).isoformat()
    report['unresolved_menu_links']=sorted({u for a in report['annuals'] for u in a['unresolved_links']})
    report['canonical_graph_complete']=not report['errors']
    report['complete']=not report['errors'] and not report['unresolved_menu_links']
    (output/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    summary={'report':str(output/'report.json'),'annuals':len(report['annuals']),
             'collection_pages':len(report['collections']),'unique_items':len({x['url'] for x in report['items']}),
             'errors':report['errors'],'unresolved_menu_links':report['unresolved_menu_links'],
             'complete':report['complete'],'canonical_graph_complete':report['canonical_graph_complete'],'source_integrated':False}
    (base/'annual-inventory-summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(summary,ensure_ascii=False))


if __name__=='__main__':main()
