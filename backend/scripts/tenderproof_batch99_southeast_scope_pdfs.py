"""Bounded official FAPESQ PDF scope investigation; no source activation."""
import sys,os,json,hashlib,time
from pathlib import Path
from datetime import datetime,timezone
from urllib.parse import urlsplit
import httpx
from bs4 import BeautifulSoup
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.tenderproof.security import validate_destination
from app.tenderproof.http_driver import _public_dns
from app.tenderproof.processing import extract_pages_isolated
BASE=Path(__file__).resolve().parents[1];F=BASE/'tests/fixtures/tenderproof_batch99_southeast';R=BASE/'.tenderproof/r99scope'
def main():
 R.mkdir(parents=True,exist_ok=True);os.environ['TENDERPROOF_ARTIFACT_DIR']=str(R/'artifacts');os.environ['TENDERPROOF_PROCESSING_DIR']=str(R/'processing');os.environ['TENDERPROOF_PROCESSING_MODE']='local'
 rows=[]
 for key in ('58','57'):
  h=F/('fapesq-'+key+'.html');s=BeautifulSoup(h.read_text(encoding='utf-8'),'lxml');a=next(a for a in s.select('#content a[href]') if a['href'].endswith('.pdf'))
  u=a['href'];row={'source':'fapesq_selection','notice':key+'/2026','url':u,'title':a.get_text(' ',strip=True),'observed_at':datetime.now(timezone.utc).isoformat(),'detail_sha256':hashlib.sha256(h.read_bytes()).hexdigest(),'max_bytes':30*1024*1024,'max_pages':60,'tls_verified':True}
  try:
   validate_destination(u,allowlist=('fapesq.rpp.br',));assert urlsplit(u).scheme=='https';_public_dns(urlsplit(u).hostname);deadline=time.monotonic()+25
   with httpx.Client(timeout=25,trust_env=False,follow_redirects=False,verify=True,headers={'User-Agent':'ObservadorDeConcursos/1.0'}) as client:
    with client.stream('GET',u) as response:
     response.raise_for_status();b=bytearray()
     for chunk in response.iter_bytes():
      b.extend(chunk)
      if len(b)>30*1024*1024 or time.monotonic()>deadline:raise ValueError('scope transfer bounded limit exceeded')
   assert b.startswith(b'%PDF');p=R/('fapesq-'+key+'.pdf');p.write_bytes(b)
   row.update(bytes=len(b),sha256=hashlib.sha256(b).hexdigest(),file=str(p))
   pages,total,*rest=extract_pages_isolated(bytes(b),artifact_id='scope-'+key,owner_id='901',max_pages=60,max_bytes=30*1024*1024)
   text='\n'.join(p.text for p in pages);(R/('fapesq-'+key+'.txt')).write_text(text,encoding='utf-8')
   row.update(total_pages=total,processed_pages=len(pages),text_file=str(R/('fapesq-'+key+'.txt')),scope_review_pending=True)
  except Exception as e:row.update(error=type(e).__name__,reason=str(e))
  rows.append(row)
 (BASE.parent/'docs/tenderproof-batch99-southeast-scope-pdfs.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(rows,ensure_ascii=False))
if __name__=='__main__':main()
