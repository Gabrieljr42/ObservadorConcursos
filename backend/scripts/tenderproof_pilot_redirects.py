import json
from pathlib import Path
import httpx
from app.tenderproof.source_adapters import get_source_adapter
from app.tenderproof.http_driver import _public_dns
from urllib.parse import urlsplit,urlunsplit,parse_qsl,urlencode
r=json.loads(Path('../docs/tenderproof-pilot-live.json').read_text(encoding='utf-8'))
rows=[]
for source,external in [('ibade_open','127'),('funcern_selection','concurso-lagoa-de-pedras-2026')]:
 rec=next(c for c in r['cycles'] if c['cycle']==1 and c['source']==source)
 sample=next(c for c in rec['attempts'] if c['candidate']['external_id']==external)
 a=get_source_adapter(source);c=a.candidate_from_url(sample['candidate']['detail_url_observed'],sample['candidate']['title_observed'])
 cap=sample['captures'][0];html=(Path('tests/fixtures/tenderproof_pilot')/cap['file']).read_text(encoding='utf-8')
 d=a.choose_document(a.documents(html,c));a.validate_document_url(d.url_requested,c);_public_dns(urlsplit(d.url_requested).hostname)
 with httpx.Client(follow_redirects=False,trust_env=False,verify=True,timeout=20) as client:
  with client.stream('GET',d.url_requested) as response:
   location=urlsplit(response.headers.get('location',''));safe=urlunsplit((location.scheme,location.netloc,location.path,urlencode([(k,'REDACTED') for k,v in parse_qsl(location.query)]),''))
   row={'source':source,'url':d.url_requested,'status':response.status_code,'location':safe};rows.append(row);print(row)
Path('../docs/tenderproof-pilot-redirects.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')

