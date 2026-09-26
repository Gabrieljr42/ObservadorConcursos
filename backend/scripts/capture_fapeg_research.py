"""Inventory official call tables and acquire documents of currently open calls."""
import argparse,hashlib,json,re,time
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import urlsplit,urljoin
import httpx
from bs4 import BeautifulSoup
from app.tenderproof.processing import extract_pages_isolated


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--state',choices=('inscricoes-abertas','em-andamento','encerrados'),default='inscricoes-abertas')
    parser.add_argument('--year',type=int,help='Explicit audit batch year; excluded calls remain pending in the report')
    args=parser.parse_args()
    root=Path('.tenderproof/product-completion/fapeg')/datetime.now(timezone.utc).strftime('research-%Y%m%dT%H%M%SZ');root.mkdir()
    report={'listings':[],'calls':[],'details':[],'documents':[],'source_integrated':False,'acquisition_state':args.state}
    def save():(root/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    with httpx.Client(timeout=30,follow_redirects=False,trust_env=False) as client:
        def fetch(url,limit):
            with client.stream('GET',url) as response:
                response.raise_for_status();raw=bytearray()
                for chunk in response.iter_bytes():
                    raw.extend(chunk)
                    if len(raw)>limit:raise ValueError('Byte limit')
            return bytes(raw)
        for state in ('inscricoes-abertas','em-andamento','encerrados'):
            url='https://goias.gov.br/fapeg/editais/'+state+'/'
            raw=fetch(url,8*1024*1024);sha=hashlib.sha256(raw).hexdigest();(root/(sha+'.html')).write_bytes(raw)
            soup=BeautifulSoup(raw,'html.parser');tables=soup.select('article .entry-content table.planilhaview')
            if len(tables)!=1:raise ValueError('Call table missing or ambiguous')
            count=0
            for tr in tables[0].select('tbody tr'):
                cells=tr.find_all('td',recursive=False)
                if len(cells) not in (5,7) or any(c.get_text(' ',strip=True) or c.select('a[href]') for c in cells[5:]):
                    report.setdefault('pending_rows',[]).append({'listing':url,'row_html':str(tr),'reason':'Unexpected nonempty columns'});save();continue
                if not any(c.get_text(' ',strip=True) or c.select('a[href]') for c in cells):continue
                links=cells[4].select('a[href]')
                if len(links)!=1:
                    report.setdefault('pending_rows',[]).append({'listing':url,'row_html':str(tr),'reason':'Call link missing or ambiguous'});save();continue
                target=urljoin(url,links[0]['href']);p=urlsplit(target)
                pending_destination=p.scheme!='https' or p.netloc!='goias.gov.br' or not p.path.startswith('/fapeg/') or bool(p.query) or bool(p.fragment)
                report['calls'].append({'number':cells[0].get_text(' ',strip=True),'type':cells[1].get_text(' ',strip=True),'origin':cells[2].get_text(' ',strip=True),'title':cells[3].get_text(' ',strip=True),'url':target,'state':state,'listing_sha256':sha,'destination_review_pending':pending_destination});count+=1
            report['listings'].append({'url':url,'sha256':sha,'rows':count});save()
            print(json.dumps({'state':state,'calls':count}),flush=True)
        seen={}
        selected=[c for c in report['calls'] if c['state']==args.state]
        if args.year is not None:
            report['audit_batch_year']=args.year
            report['excluded_calls_pending']=[c for c in selected if not re.search(r'(?<!\d)'+str(args.year)+r'(?!\d)',c['number'])]
            selected=[c for c in selected if re.search(r'(?<!\d)'+str(args.year)+r'(?!\d)',c['number'])]
        report['selected_call_count']=len(selected)
        save()
        for call in selected:
            detail={**call,'links':[]};report['details'].append(detail)
            try:
                if call['destination_review_pending']:raise ValueError('Call destination pending review')
                raw=fetch(call['url'],8*1024*1024);sha=hashlib.sha256(raw).hexdigest();(root/(sha+'.html')).write_bytes(raw);detail['sha256']=sha
                soup=BeautifulSoup(raw,'html.parser');article=soup.select_one('article .entry-content')
                if article is None:raise ValueError('Call article missing')
                detail['headings']=[h.get_text(' ',strip=True) for h in soup.select('article .entry-title')]
                detail['text']=article.get_text(' ',strip=True)
                detail['links']=[{'title':a.get_text(' ',strip=True),'url':urljoin(call['url'],a['href'])} for a in article.select('a[href]')]
                for link in detail['links']:
                    u=link['url'];p=urlsplit(u)
                    if not re.search(r'\.(pdf|docx?|xlsx?|odt)$',p.path,re.I):continue
                    if p.scheme!='https' or p.netloc!='goias.gov.br' or not p.path.startswith('/fapeg/wp-content/uploads/') or p.query or p.fragment:
                        detail.setdefault('pending_documents',[]).append(link);continue
                    if u in seen:seen[u]['calls'].append(call['url']);continue
                    row={**link,'calls':[call['url']]};seen[u]=row;report['documents'].append(row)
                    try:
                        data=fetch(u,30*1024*1024);digest=hashlib.sha256(data).hexdigest();ext=p.path.rsplit('.',1)[1].lower();(root/(digest+'.'+ext)).write_bytes(data);row.update(sha256=digest,bytes=len(data),format=ext)
                        if ext=='pdf':
                            pages,total,processed,truncated,errors=extract_pages_isolated(data,artifact_id='fapeg-research-'+digest,owner_id='fapeg-source-audit',max_bytes=30*1024*1024,max_pages=200)
                            (root/(digest+'-pages.json')).write_text(json.dumps([p.model_dump(mode='json') for p in pages],ensure_ascii=False),encoding='utf-8');row.update(total_pages=total,processed_pages=processed,truncated=truncated,errors=errors)
                        else:row['reading_pending']=True
                    except Exception as exc:row['error']=type(exc).__name__+': '+str(exc)
                    save();print(json.dumps({'documents':len(report['documents']),'pages':row.get('processed_pages'),'error':row.get('error')}),flush=True);time.sleep(1)
            except Exception as exc:detail['error']=type(exc).__name__+': '+str(exc)
            save()
    report['finished_at']=datetime.now(timezone.utc).isoformat();save();print(str(root),flush=True)


if __name__=='__main__':main()
