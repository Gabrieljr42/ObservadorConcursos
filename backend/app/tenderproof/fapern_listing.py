"""Official service discovery and fixed, read-only public directory requests."""
import base64
import json
import re
from dataclasses import dataclass
from urllib.parse import urlsplit, quote
from bs4 import BeautifulSoup
from app.tenderproof.fapern_drive import ROOT, canonical_path, parse_directory

PORTAL = 'https://www.cidadao.rn.gov.br/wp-json/wp/v2/servicos?per_page=100&order=desc&orderby=date&page='
SHARE = 'https://drive.rn.gov.br/index.php/s/'


def share_token(url):
    match=re.fullmatch(re.escape(SHARE)+r'([A-Za-z0-9]{8,64})',url)
    if not match: raise ValueError('compartilhamento público RN inválido')
    return match[1]


def exact(url):
    def validate(target):
        if target!=url: raise ValueError('redirecionamento altera a origem FAPERN')
    return validate


def discover_share(fetch):
    matches=[];page=1;total=None;ids=set()
    while total is None or page<=total:
        response=fetch(PORTAL+str(page),exact(PORTAL+str(page)),2*1024*1024)
        headers=response.pagination_headers or {}
        count=int(headers.get('x-wp-totalpages','0'))
        if not 1<=count<=50 or total is not None and total!=count:
            raise ValueError('paginação do Portal do Cidadão ausente ou alterada')
        total=count;rows=json.loads(response.content)
        if not isinstance(rows,list) or len(rows)>100: raise ValueError('serviços públicos inválidos')
        for row in rows:
            if type(row.get('id')) is not int or row['id'] in ids: raise ValueError('identidade de serviço duplicada')
            ids.add(row['id']);acf=row.get('acf') or {}
            agencies=acf.get('orgao_serv') or []
            title=BeautifulSoup(row.get('title',{}).get('rendered',''),'html.parser').get_text(' ',strip=True)
            if any(a.get('slug')=='fapern' for a in agencies) and re.match(r'^Editais\b',title,re.I):
                url=acf.get('link_externo','');share_token(url)
                if acf.get('servico_indisponivel'): raise ValueError('serviço oficial de editais indisponível')
                matches.append({'service_id':row['id'],'share_url':url,'title':title})
        page+=1
    if len(matches)!=1: raise ValueError('vínculo oficial FAPERN ausente ou ambíguo')
    return matches[0] | {'service_pages':total,'services_scanned':len(ids)}


@dataclass(frozen=True)
class FapernDirectoryRequest:
    token: str
    path: str

    def transport(self,url,source):
        share_token(SHARE+self.token)
        path=canonical_path(self.path)
        expected='https://drive.rn.gov.br'+quote(path,safe='/')
        if source!='fapern_selection' or not path.endswith('/') or url!=expected:
            raise ValueError('requisição fora do diretório público FAPERN')
        return {'method':'PROPFIND','content_type':'application/xml',
                'body':'<d:propfind xmlns:d="DAV:"><d:allprop/></d:propfind>',
                'headers':{'Depth':'1','Authorization':'Basic '+base64.b64encode((self.token+':').encode('ascii')).decode('ascii')}}


def acquire_directory(fetch,share,path):
    token=share_token(share)
    request=FapernDirectoryRequest(token,path)
    url='https://drive.rn.gov.br'+quote(canonical_path(path),safe='/')
    response=fetch(url,exact(url),4*1024*1024,public_listing_request=request)
    return parse_directory(response.content,path)
