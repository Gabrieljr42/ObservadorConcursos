"""Read-only bounded capture of source pages whose URLs have been observed."""
import asyncio, hashlib, json, sys, re
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit, urljoin, parse_qs
from datetime import datetime, timezone
import httpx
from bs4 import BeautifulSoup, UnicodeDammit
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.tenderproof.inventory import public_dns
from app.tenderproof.security import validate_destination
OUT=Path(__file__).resolve().parents[1]/'tests/fixtures/tenderproof_batch30_institutional'
TARGETS={
'publiconsult-listing':'https://publiconsult.com.br/Concurso/Index',
'publiconsult-detail':'https://publiconsult.com.br/Concurso/Detail/681?origem=H',
'ufu-listing':'https://www.portalselecao.ufu.br/servicos/Edital/listar/concursos',
'ufu-detail':'https://www.portalselecao.ufu.br/servicos/Edital/cronograma/1828',
'uniselva-listing':'https://web.fundacaouniselva.org.br/frmSelecoes.aspx',
'uniselva-detail':'https://web.fundacaouniselva.org.br/frmSelecao.aspx?_id=1261'}
async def main():
 OUT.mkdir(parents=True,exist_ok=True)
 records=[]
 async with httpx.AsyncClient(timeout=20,follow_redirects=False,trust_env=False,verify=True) as client:
  for name,url in TARGETS.items():
   record={'name':name,'url':url,'observed_at':datetime.now(timezone.utc).isoformat()}
   try:
    host=urlsplit(url).hostname;validate_destination(url,allowlist=(host,));await public_dns(host)
    async with client.stream('GET',url) as response:
     record['status']=response.status_code;raw=bytearray()
     async for chunk in response.aiter_bytes():
      raw.extend(chunk)
      if len(raw)>2*1024*1024:raise ValueError('Response exceeds2MiB')
    decoded=UnicodeDammit(bytes(raw),is_html=True)
    if decoded.contains_replacement_characters:
     raise ValueError('HTML decoding lost characters; do not preserve a corrupted fixture')
    record['decoded_encoding']=decoded.original_encoding
    soup=BeautifulSoup(decoded.unicode_markup,'lxml')
    # Never preserve ephemeral public signed keys or CSRF values in fixtures.
    redacted=0; signed_query_keys=set()
    for a in soup.find_all(True):
     for attribute in ['href','src','action','data-src']:
      if not isinstance(a.get(attribute),str): continue
      p=urlsplit(a[attribute])
      if re.search(r'X-Amz-|AWSAccessKeyId|Signature=',p.query,re.I):
       signed_query_keys.update(parse_qs(p.query,keep_blank_values=True))
       a[attribute]=urlunsplit((p.scheme,p.netloc,p.path,'',''));redacted+=1
    for i in soup.select('input[type=hidden]'):i.attrs.pop('value',None)
    data=str(soup).encode('utf-8');(OUT/f'{name}.html').write_bytes(data)
    record.update(bytes=len(raw),original_sha256=hashlib.sha256(raw).hexdigest(),fixture_sha256=hashlib.sha256(data).hexdigest(),redacted_signed_links=redacted,file=f'{name}.html')
    record['signed_query_keys']=sorted(signed_query_keys)
    print(name,len(raw),'status',response.status_code)
   except Exception as e:record['error']=type(e).__name__+': '+str(e);print(name,record['error'])
   records.append(record)
 (OUT/('manifest-'+sys.argv[1]+'.json' if len(sys.argv)>1 else 'manifest.json')).write_text(json.dumps({'provenance':'live public HTTP capture; sanitized hidden values and public signed URL queries; no browsers or credential use;2MiB/page20s','pages':records},ensure_ascii=False,indent=2),encoding='utf-8')
if len(sys.argv)>1 and sys.argv[1]=='followup':
 TARGETS={'uniselva-modern-listing':'https://inscricao.fundacaouniselva.org.br/selecoes','uniselva-modern-detail':'https://inscricao.fundacaouniselva.org.br/selecoes/1261','ufu-ta-listing':'https://www.portalselecao.ufu.br/servicos/Edital/listar/concurso_ta','ufu-ta-detail':'https://www.portalselecao.ufu.br/servicos/Edital/cronograma/1781'}
if len(sys.argv)>1 and sys.argv[1]=='assets':
 TARGETS={'uniselva-main-js':'https://inscricao.fundacaouniselva.org.br/main-CUVRP5XO.js'}
if len(sys.argv)>1 and sys.argv[1]=='publiconsult':
 TARGETS={name:url for name,url in TARGETS.items() if name.startswith('publiconsult-')}
asyncio.run(main())
