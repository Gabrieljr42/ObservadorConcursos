"""Bounded public HTTP captures for four explicitly selected batch30 sources."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import socket
import ipaddress
import httpx
import sys
ROOT=Path(__file__).resolve().parents[1]
FIXTURES=ROOT/'tests/fixtures/tenderproof_batch30_own'
URLS={'ibfc_open':'https://concursos.ibfc.org.br/index/abertos/','reisesreis_open':'https://novo.reisauditores.com.br/concursos-em-andamento','admtec_open':'https://admtec.org.br/','institutomais_open':'https://www.institutomais.org.br/Concursos/ConcursosAbertos'}
def fetch(pair):
 from urllib.parse import urlsplit
 source,url=pair
 result={'source':source,'url':url,'observed_at':datetime.now(timezone.utc).isoformat()}
 try:
  if any(not ipaddress.ip_address(x[4][0]).is_global for x in socket.getaddrinfo(urlsplit(url).hostname,443,type=socket.SOCK_STREAM)):
   raise ValueError('private_dns')
  with httpx.Client(timeout=25,follow_redirects=False,trust_env=False,headers={'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36', **({'X-TenantID':'reisauditores'} if source.startswith('reis_api') else {})}) as client:
   with client.stream('GET',url) as response:
    chunks=[];size=0
    for chunk in response.iter_bytes():
     size+=len(chunk)
     if size>2*1024*1024:raise ValueError('above2MiB')
     chunks.append(chunk)
    raw=b''.join(chunks)
    path=FIXTURES/(source+'-listing.html');path.write_bytes(raw)
    result.update(status=response.status_code,location=response.headers.get('location'),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),file=path.name)
 except Exception as exc:result.update(error=type(exc).__name__+':'+str(exc))
 return result
if __name__=='__main__':
 FIXTURES.mkdir(parents=True,exist_ok=True)
 phase=sys.argv[1] if len(sys.argv)>1 else 'initial'
 targets=URLS if phase=='initial' else {'ibfc_ongoing':'https://concursos.ibfc.org.br/index/1/','institutomais_detail':'https://www.institutomais.org.br/Concursos/Detalhe/10645','reis_component':'https://novo.reisauditores.com.br/_astro/ConcursosPagination.DxmG8JD1.js','admtec_browser_ua':'https://admtec.org.br/'}
 if phase=='advanced':
  targets={'ibfc_detail':'https://concursos.ibfc.org.br/informacoes/496/','institutomais_detail2':'https://www.institutomais.org.br/Concursos/Detalhe/10646','admtec_detail':'https://admtec.org.br/concursos/publicacoes/MTEz/MTIx','reis_grid':'https://novo.reisauditores.com.br/_astro/ConcursosGrid.D92mt0L9.js','reis_api':'https://api.gestaoselecoes.com.br/api/editais?page=0&size=9&situacao=PUBLICADO,INSCRICAO_ABERTA,ANDAMENTO&order=DESC'}
 if phase=='more':
  targets={'reis_detail':'https://novo.reisauditores.com.br/editais/70','ibfc_detail2':'https://concursos.ibfc.org.br/informacoes/485/','admtec_detail2':'https://admtec.org.br/concursos/publicacoes/MTA4/MTE2','institutomais_detail3':'https://www.institutomais.org.br/Concursos/Detalhe/10648'}
 rows=list(ThreadPoolExecutor(4).map(fetch,targets.items()))
 (FIXTURES/(phase+'-probe.json')).write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps(rows,ensure_ascii=False))
