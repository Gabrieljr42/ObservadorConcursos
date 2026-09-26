"""Preserve documents from observed FAPES panels, with isolated PDF reading."""
import sys,json,hashlib,time,argparse
from pathlib import Path
from datetime import datetime,timezone
import httpx
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.tenderproof.processing import extract_pages_isolated

def main():
 root=Path(__file__).resolve().parents[1]/'.tenderproof/product-completion/fapes'
 parser=argparse.ArgumentParser()
 parser.add_argument('--panels-file',type=Path,default=root/'carreira-abertos-panels.json')
 parser.add_argument('--max-pages',type=int,default=100)
 args=parser.parse_args()
 if not 1 <= args.max_pages <= 250:parser.error('max-pages must be between 1 and 250')
 rows=json.loads(args.panels_file.read_text(encoding='utf-8'))
 output=root/datetime.now(timezone.utc).strftime('documents-%Y%m%dT%H%M%SZ');output.mkdir()
 results=[]
 with httpx.Client(timeout=25,follow_redirects=False) as client:
  for call in rows:
   for doc in call['documents']:
    record={'panel_id':call['panel_id'],**doc}
    try:
     if doc.get('format','pdf') != 'pdf':
      raise ValueError('non-PDF attachment preserved in discovery; document reader pending')
     with client.stream('GET',doc['url']) as response:
      response.raise_for_status();content=b''
      for chunk in response.iter_bytes():
       content+=chunk
       if len(content)>15000000:raise ValueError('document limit')
     digest=hashlib.sha256(content).hexdigest()
     record.update(sha256=digest,byte_len=len(content))
     (output/(digest+'.pdf')).write_bytes(content)
     pages,total,processed,truncated,errors=extract_pages_isolated(content,artifact_id='fapes-'+digest,
        owner_id='fapes-scope-audit',max_bytes=15000000,max_pages=args.max_pages)
     (output/(digest+'-pages.json')).write_text(json.dumps([p.model_dump(mode='json') for p in pages],ensure_ascii=False),encoding='utf-8')
     record.update(total_pages=total,processed_pages=processed,truncated=truncated,errors=errors)
    except Exception as exc:record['error']=type(exc).__name__+': '+str(exc)[:140]
    results.append(record)
    (output/'verification.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'panel_id':call['panel_id'],'title':doc['title'],'pages':record.get('processed_pages'),'error':record.get('error')},ensure_ascii=True),flush=True)
    time.sleep(1)
 print(output,flush=True)
if __name__=='__main__':main()
