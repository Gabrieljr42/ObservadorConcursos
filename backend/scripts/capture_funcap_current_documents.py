"""Fresh FUNCAP listing and documents in the newest observed annual cohort or updated since it."""
import hashlib,json,re,time
from datetime import datetime,timezone
from pathlib import Path
import httpx
from app.tenderproof.funcap_panels import LISTING,parse_panels,document_url
from app.tenderproof.processing import extract_pages_isolated


def main():
    root=Path('.tenderproof/product-completion/funcap')/datetime.now(timezone.utc).strftime('current-documents-%Y%m%dT%H%M%SZ')
    root.mkdir(parents=True)
    report={'listing_url':LISTING,'documents':[],'source_integrated':False,'published':False}
    def save():
        (root/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    with httpx.Client(timeout=25,trust_env=False,follow_redirects=False) as client:
        def acquire(url,limit):
            with client.stream('GET',url) as response:
                response.raise_for_status();raw=bytearray()
                for chunk in response.iter_bytes():
                    raw.extend(chunk)
                    if len(raw)>limit:raise ValueError('acquisition byte limit')
            return bytes(raw)
        raw=acquire(LISTING,4*1024*1024);digest=hashlib.sha256(raw).hexdigest()
        (root/(digest+'.html')).write_bytes(raw)
        parsed=parse_panels(raw)
        (root/'panels.json').write_text(json.dumps(parsed,ensure_ascii=False,indent=2),encoding='utf-8')
        years=[int(p['year_group'].rsplit('-',1)[1]) for p in parsed['panels'] if re.fullmatch(r'bloco-ano-\d{4}',p['year_group'] or '')]
        newest=max(years)
        calls=[p for p in parsed['panels'] if p['year_group']==f'bloco-ano-{newest}' or any(int(d['published_at'][:4])>=newest for d in p['documents']) or 'abertos' in p['status_observed'].lower()]
        report.update(listing_sha256=digest,observed_year=newest,selection_rule='Newest observed annual group, any group with documents updated since that year, and all observed open groups; older untouched groups remain pending.',calls=calls)
        save();seen={}
        for call in calls:
            for doc in call['documents']:
                url=document_url(doc['url'])
                if url in seen:
                    seen[url]['groups'].append({'year_group':call['year_group'],'solicitation_id':call['solicitation_id']});continue
                row={**doc,'groups':[{'year_group':call['year_group'],'solicitation_id':call['solicitation_id']}]}
                seen[url]=row;report['documents'].append(row)
                try:
                    content=acquire(url,30*1024*1024);digest=hashlib.sha256(content).hexdigest()
                    (root/(digest+'.'+doc['format'])).write_bytes(content);row.update(sha256=digest,bytes=len(content))
                    if doc['format']=='pdf':
                        pages,total,processed,truncated,errors=extract_pages_isolated(content,artifact_id='funcap-'+digest,owner_id='funcap-source-audit',max_bytes=30*1024*1024,max_pages=200)
                        (root/(digest+'-pages.json')).write_text(json.dumps([p.model_dump(mode='json') for p in pages],ensure_ascii=False),encoding='utf-8')
                        row.update(total_pages=total,processed_pages=processed,truncated=truncated,errors=errors)
                    else:row['reading_pending']=True
                except Exception as exc:row['error']=type(exc).__name__+': '+str(exc)
                save();print(json.dumps({'documents':len(report['documents']),'pages':row.get('processed_pages'),'error':row.get('error')}),flush=True)
                time.sleep(1)
    report['finished_at']=datetime.now(timezone.utc).isoformat();save();print(str(root),flush=True)


if __name__=='__main__':main()
