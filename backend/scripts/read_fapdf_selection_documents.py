"""Read documents of personnel selections discovered in the live annual archive."""
import hashlib,json,re,time
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import urlsplit
import httpx
from app.tenderproof.processing import extract_pages_isolated
from scripts.capture_fapdf_inventory import parse

def main():
    base=Path('.tenderproof/product-completion/fapdf')
    inventory=max(base.glob('inventory-*/report.json'),key=lambda p:p.stat().st_mtime)
    listing=json.loads(inventory.read_text(encoding='utf-8'))
    pages=[p for p in listing['pages'] if any(re.search('SERVIDORES|PROCESSO SELETIVO SIMPLIFICADO',g['title'],re.I) for g in p['groups'])]
    root=base/datetime.now(timezone.utc).strftime('selection-documents-%Y%m%dT%H%M%SZ');root.mkdir()
    report={'inventory':str(inventory),'calls':[],'documents':[],'errors':[],'source_integrated':False,'published':False}
    def save():(root/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    with httpx.Client(timeout=25,trust_env=False,follow_redirects=False) as client:
        def get(url,limit):
            p=urlsplit(url)
            if p.scheme!='https' or p.netloc!='fap.df.gov.br' or p.query or p.fragment:raise ValueError('Unexpected URL')
            with client.stream('GET',url) as r:
                r.raise_for_status();raw=bytearray()
                for c in r.iter_bytes():
                    raw.extend(c)
                    if len(raw)>limit:raise ValueError('Byte limit')
            return bytes(raw)
        seen=set()
        for page in pages:
            raw=get(page['url'],8*1024*1024);sha=hashlib.sha256(raw).hexdigest();(root/(sha+'.html')).write_bytes(raw)
            for group in parse(raw,page['url'])['groups']:
                if not re.search('SERVIDORES|PROCESSO SELETIVO SIMPLIFICADO',group['title'],re.I):continue
                report['calls'].append({'listing_url':page['url'],'listing_sha256':sha,**group})
                for doc in group['links']:
                    if not doc['url'].startswith('https://fap.df.gov.br/documents/') or doc['url'] in seen:continue
                    seen.add(doc['url']);row={**doc,'call_title':group['title']};report['documents'].append(row)
                    try:
                        content=get(doc['url'],30*1024*1024);digest=hashlib.sha256(content).hexdigest()
                        if not content.startswith(b'%PDF-'):raise ValueError('Expected PDF magic')
                        (root/(digest+'.pdf')).write_bytes(content);row.update(sha256=digest,bytes=len(content))
                        ps,total,processed,truncated,errors=extract_pages_isolated(content,artifact_id='fapdf-'+digest,owner_id='fapdf-source-audit',max_bytes=30*1024*1024,max_pages=200)
                        (root/(digest+'-pages.json')).write_text(json.dumps([p.model_dump(mode='json') for p in ps],ensure_ascii=False),encoding='utf-8')
                        row.update(total_pages=total,processed_pages=processed,truncated=truncated,errors=errors)
                    except Exception as e:row['error']=type(e).__name__+': '+str(e)
                    save();print(json.dumps({'documents':len(report['documents']),'pages':row.get('processed_pages'),'error':row.get('error')}),flush=True);time.sleep(1)
    report['finished_at']=datetime.now(timezone.utc).isoformat();save();print(root,flush=True)

if __name__=='__main__':main()
