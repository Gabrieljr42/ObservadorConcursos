"""Inspect the anonymous viewer's published download address; no authentication."""
import hashlib,json,re
from pathlib import Path
from urllib.parse import urlsplit
import httpx


def acquire(client):
    root=Path('.tenderproof/product-completion/fapeg/sharepoint-20260909T185055Z')
    observed=json.loads((root/'report.json').read_text(encoding='utf-8'))[0]['url']
    for _ in range(4):
        p=urlsplit(observed)
        if p.scheme!='https' or p.hostname!='goiasgovbr-my.sharepoint.com':raise ValueError('Viewer redirect outside public host')
        with client.stream('GET',observed) as response:
            if response.status_code>=400:raise ValueError('Viewer HTTP '+str(response.status_code))
            body=bytearray()
            for chunk in response.iter_bytes():
                body.extend(chunk)
                if len(body)>8*1024*1024:raise ValueError('Viewer byte limit')
            if response.is_redirect:
                observed=response.headers['location'];continue
            text=bytes(body).decode('utf-8');break
    else:raise ValueError('Viewer redirect limit')
    def value(key):
        matches=re.findall(r'"'+re.escape(key)+r'"\s*:\s*("(?:[^"\\]|\\.)*"|true|false|null)',text)
        if len(matches)!=1:raise ValueError('Ambiguous viewer field: '+key)
        return json.loads(matches[0])
    url=value('FileGetUrl');name=value('FileName');view_only=value('ViewOnly')
    p=urlsplit(url)
    report={'file_name':name,'view_only':view_only,'download_host':p.hostname,'download_path':p.path}
    print(json.dumps(report,ensure_ascii=True),flush=True)
    if view_only is not False:raise ValueError('Viewer does not permit download')
    if p.scheme!='https' or p.hostname!='goiasgovbr-my.sharepoint.com' or not p.path.endswith('/_layouts/15/download.aspx'):
        raise ValueError('Published download endpoint requires review')
    with client.stream('GET',url) as response:
        if response.status_code!=200:
            report['download_status']=response.status_code
            (root/'download-pending.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
            raise ValueError('Public download returned HTTP '+str(response.status_code))
        raw=bytearray()
        for chunk in response.iter_bytes():
            raw.extend(chunk)
            if len(raw)>8*1024*1024:raise ValueError('Download byte limit')
        if not raw.startswith(b'PK'):raise ValueError('Response is not a workbook package')
        digest=hashlib.sha256(raw).hexdigest();(root/(digest+'.xlsx')).write_bytes(raw)
        report.update(sha256=digest,bytes=len(raw),content_type=response.headers.get('content-type'),status=response.status_code)
    (root/'download-receipt.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report,ensure_ascii=True))


if __name__=='__main__':
    with httpx.Client(timeout=30,follow_redirects=False,trust_env=False) as client:acquire(client)
