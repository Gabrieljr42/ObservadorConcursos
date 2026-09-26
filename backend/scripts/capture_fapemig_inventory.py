"""Read the public /api/calls contract observed in FAPEMIG's current website bundle."""
import hashlib,json,time
from pathlib import Path
from datetime import datetime,timezone
import httpx

def main():
    root=Path('.tenderproof/product-completion/fapemig')/datetime.now(timezone.utc).strftime('inventory-%Y%m%dT%H%M%SZ');root.mkdir()
    report={'pages':[],'calls':[],'errors':[],'source_integrated':False}
    def save():(root/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    with httpx.Client(timeout=30,trust_env=False,follow_redirects=False) as c:
        page=1;seen=set();expected=None
        while page<=500:
            url=f'https://fapemig.br/api/calls?page={page}&per_page=12&publicacao_status=publish'
            try:
                with c.stream('GET',url) as q:
                    q.raise_for_status();raw=bytearray()
                    for chunk in q.iter_bytes():
                        raw.extend(chunk)
                        if len(raw)>8*1024*1024:raise ValueError('JSON byte limit')
                sha=hashlib.sha256(raw).hexdigest();(root/(sha+'.json')).write_bytes(raw);data=json.loads(raw)
                if expected is None:expected=data['total']
                if data['total']!=expected or data['page']!=page:raise ValueError('Pagination changed')
                for call in data['data']:
                    if call['id'] in seen:raise ValueError('Repeated call')
                    seen.add(call['id']);report['calls'].append(call)
                report['pages'].append({'url':url,'sha256':sha,'pagination':data['pagination']});save();print(json.dumps({'page':page,'calls':len(seen)}),flush=True)
                if page>=data['pagination']['total_pages']:
                    if len(seen)!=expected:raise ValueError('Total mismatch')
                    break
                page+=1;time.sleep(1)
            except Exception as e:report['errors'].append({'url':url,'error':type(e).__name__+': '+str(e)});break
    report['finished_at']=datetime.now(timezone.utc).isoformat();save();print(root,flush=True)

if __name__=='__main__':main()
