"""Bounded anonymous acquisition of workbooks linked by FAPEG articles.

Uses the caller's public HTTP fetcher/session; never accepts credentials or
executes viewer JavaScript. The primary edital PDF pipeline stays separate.
"""
import json
import re
from urllib.parse import parse_qs,urlsplit
from bs4 import UnicodeDammit
from app.tenderproof.solari_adapter import DownloadedBytes

HOST='goiasgovbr-my.sharepoint.com'


def validate_workbook_result(url,result,max_bytes):
    folder=share_folder(url)
    if result.url_requested!=url:raise ValueError('Workbook request identity differs')
    final=urlsplit(result.url_final);q=parse_qs(final.query)
    if final.scheme!='https' or final.netloc!=HOST or final.fragment or final.path!=folder+'_layouts/15/download.aspx' or len(q.get('UniqueId',[]))!=1:
        raise ValueError('Workbook final identity differs')
    document_id=q['UniqueId'][0].lower()
    if not re.fullmatch(r'[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}',document_id):raise ValueError('Workbook GUID invalid')
    viewer_found=False
    for hop in result.redirect_chain or []:
        if hop in (url,result.url_final):continue
        p=urlsplit(hop);query=parse_qs(p.query)
        if p.scheme!='https' or p.netloc!=HOST or p.fragment or p.path!=folder+'_layouts/15/Doc.aspx' or query.get('sourcedoc')!=['{'+document_id+'}']:
            raise ValueError('Workbook chain identity differs')
        viewer_found=True
    if not viewer_found:raise ValueError('Workbook viewer evidence missing')
    if len(result.content)>max_bytes or not result.content.startswith(b'PK\x03\x04') or (result.content_type or '').split(';')[0].strip().lower()!='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet':
        raise ValueError('Workbook payload differs from declared format')


def share_folder(url):
    p=urlsplit(url)
    if p.scheme!='https' or p.netloc!=HOST or p.fragment:
        raise ValueError('Workbook share outside FAPEG public tenant')
    match=re.fullmatch(r'/:x:/g/personal/([a-z0-9_]+)/([A-Za-z0-9_-]{20,160})',p.path)
    if not match or not re.fullmatch(r'e=[A-Za-z0-9]{1,32}',p.query):
        raise ValueError('Unrecognized public workbook share')
    return '/personal/'+match[1]+'/'


def _field(text,key):
    matches=re.findall(r'"'+re.escape(key)+r'"\s*:\s*("(?:[^"\\]|\\.)*"|true|false|null)',text)
    if len(matches)!=1:raise ValueError('Missing or ambiguous viewer field: '+key)
    return json.loads(matches[0])


def acquire_public_workbook(url,fetch,*,max_bytes):
    folder=share_folder(url)
    if type(max_bytes) is not int or not 1<=max_bytes<=30*1024*1024:raise ValueError('Invalid workbook byte limit')
    def viewer_destination(target):
        if target==url:return
        p=urlsplit(target)
        if p.scheme!='https' or p.netloc!=HOST or p.fragment or p.path!=folder+'_layouts/15/Doc.aspx':
            raise ValueError('Workbook viewer redirect outside observed personal folder')
        query=parse_qs(p.query)
        if len(query.get('sourcedoc',[]))!=1 or not re.fullmatch(r'\{[0-9a-fA-F-]{36}\}',query['sourcedoc'][0]):
            raise ValueError('Workbook viewer lacks unique document identity')
    viewer=fetch(url,viewer_destination,min(max_bytes,2*1024*1024))
    viewer_destination(viewer.url_final)
    if viewer.url_final==url:raise ValueError('Public workbook viewer not resolved')
    doc_id=parse_qs(urlsplit(viewer.url_final).query)['sourcedoc'][0].strip('{}').lower()
    text=UnicodeDammit(viewer.content,is_html=True).unicode_markup or ''
    if _field(text,'ViewOnly') is not False:raise ValueError('Public viewer disallows download')
    name=_field(text,'FileName');download=_field(text,'FileGetUrl')
    if not isinstance(name,str) or not name.lower().endswith('.xlsx'):raise ValueError('Viewer file is not XLSX')
    p=urlsplit(download);query=parse_qs(p.query)
    if (p.scheme!='https' or p.netloc!=HOST or p.fragment or p.path!=folder+'_layouts/15/download.aspx'
            or query.get('UniqueId')!=[doc_id] or set(query)-{'UniqueId','Translate'}):
        raise ValueError('Download differs from public workbook identity')
    def download_destination(target):
        if target!=download:raise ValueError('Workbook download redirect not authorized')
    result=fetch(download,download_destination,max_bytes)
    if len(result.content)>max_bytes or not result.content.startswith(b'PK\x03\x04'):
        raise ValueError('Workbook bytes are not a bounded ZIP package')
    if (result.content_type or '').split(';')[0].strip().lower()!='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet':
        raise ValueError('Workbook response media type differs')
    # Caller preserves raw ZIP and validates its structure in isolated reading.
    return DownloadedBytes(url_requested=url,url_final=result.url_final,content=result.content,
        content_type=result.content_type,redirect_chain=[*(viewer.redirect_chain or [url]),viewer.url_final,result.url_final],
        mechanism='http'),{'file_name':name,'document_id':doc_id,'viewer_url':viewer.url_final}
