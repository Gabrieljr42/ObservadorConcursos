"""Preserve the public FAPESQ detail's complete linked document manifest."""
import re
from urllib.parse import urlsplit,urljoin,unquote
import httpx
from app.tenderproof.pilot_adapters import visible_soup,folded,document_kind


def detail_url(url):
    p=urlsplit(url)
    if (p.scheme!='https' or p.netloc!='fapesq.rpp.br' or p.query or p.fragment
            or not re.fullmatch(r'/editais/\d{4}/[a-z0-9-]+',p.path)
            or re.search(r'/(?:colecao-de-editais|editais)-\d{4}$',p.path)):
        raise ValueError('URL fora do detalhe público FAPESQ')
    return p.path[len('/editais/'):]


def parse_detail(html,url):
    identity=detail_url(url);soup=visible_soup(html)
    canonical=soup.select('link[rel=canonical][href]')
    if len(canonical)!=1 or canonical[0]['href']!=url:
        raise ValueError('identidade canônica do detalhe divergente')
    heading=soup.select_one('#content h1.documentFirstHeading')
    body=soup.select_one('#parent-fieldname-text')
    if heading is None or body is None:raise ValueError('detalhe ou corpo documental ausente')
    documents=[];other=[];unresolved=[];seen=set()
    for a in body.select('a[href]'):
        label=a.get_text(' ',strip=True)
        raw=urljoin(url,a['href'])
        try:
            target=str(httpx.URL(raw));p=urlsplit(target)
        except (ValueError,httpx.InvalidURL) as exc:
            unresolved.append({'title':label,'href_observed':raw,'error':type(exc).__name__})
            continue
        if not re.search(r'\.(?:pdf|docx?|xlsx?|zip)(?:/view)?$',p.path,re.I):
            other.append({'title':label,'url':target});continue
        if p.scheme!='https' or p.netloc!='fapesq.rpp.br' or p.query or p.fragment:
            raise ValueError('arquivo documental fora do host oficial observado')
        if target in seen:continue
        seen.add(target);kind=document_kind(label,target);text=folded(label)
        if re.search(r'retificado',text):kind='consolidado'
        elif re.search(r'homolog|resultado|recurso|classifica',text):kind='outro'
        documents.append({'title':label,'url':target,'href_observed':raw,'kind':kind,
                          'requires_file_page':p.path.endswith('/view'),
                          'normalized_dot_segments':any(part in ('.','..') for part in urlsplit(raw).path.split('/'))})
    if not documents:raise ValueError('manifesto documental vazio não confirmado')
    return {'external_id':identity,'url':url,'title':heading.get_text(' ',strip=True),
            'documents':documents,'other_links':other,'unresolved_links':unresolved,
            'manifest_complete':not unresolved}


def parse_file_view(html,url):
    p=urlsplit(url)
    if (p.scheme!='https' or p.netloc!='fapesq.rpp.br' or p.query or p.fragment
            or not p.path.endswith('.pdf/view')):
        raise ValueError('página de arquivo fora do contrato FAPESQ')
    base=url[:-len('/view')]
    soup=visible_soup(html);canonical=soup.select('link[rel=canonical][href]')
    if len(canonical)!=1 or canonical[0]['href']!=base:
        raise ValueError('página de arquivo identifica outro documento')
    prefix=base+'/@@download/file/'
    links=[]
    for a in soup.select('#content a[href]'):
        target=str(httpx.URL(urljoin(url,a['href'])))
        if not target.startswith(prefix):continue
        name=unquote(target[len(prefix):])
        if not name or '/' in name or '\\' in name or name in ('.','..'):
            raise ValueError('nome de arquivo inválido')
        parts=urlsplit(target)
        if parts.query or parts.fragment:raise ValueError('download com parâmetros inesperados')
        links.append(target)
    links=list(dict.fromkeys(links))
    if len(links)!=1:raise ValueError('download único não encontrado na página de arquivo')
    return links[0]
