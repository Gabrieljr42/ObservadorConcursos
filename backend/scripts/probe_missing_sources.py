"""Read-only bounded current probes; no access challenge handling."""
import httpx,json,concurrent.futures
from pathlib import Path
from datetime import datetime,timezone
from bs4 import BeautifulSoup

def main():
 root=Path(__file__).resolve().parents[1]/'.tenderproof/product-completion/new-sources'/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
 root.mkdir(parents=True)
 targets={'iuds':'https://www.iuds.org.br','oppus':'https://www.oppusconcursos.com.br','idgran':'https://idgran.com.br','leandroferreira':'https://www.leandroferreira.com.br'}
 def fetch(item):
  name,url=item
  try:
   with httpx.Client(timeout=15,follow_redirects=True) as c:
    with c.stream('GET',url) as r:
     body=b''
     for chunk in r.iter_bytes():
      body+=chunk
      if len(body)>2000000:raise ValueError('response limit')
     (root/(name+'.html')).write_bytes(body)
     soup=BeautifulSoup(body,'html.parser')
     return {'source':name,'url':str(r.url),'status':r.status_code,'bytes':len(body),'title':soup.title.get_text() if soup.title else None}
  except Exception as e:return {'source':name,'error':type(e).__name__,'detail':str(e)[:180]}
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:results=list(pool.map(fetch,targets.items()))
 (root/'verification.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
 print(root)
 print(json.dumps(results,ensure_ascii=True))
if __name__=='__main__':main()
