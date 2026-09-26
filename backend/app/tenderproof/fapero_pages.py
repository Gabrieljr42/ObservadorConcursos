"""Traverse observed FAPERO annual links; exclude the state-wide service directory."""
import re
from urllib.parse import urljoin,urlsplit
from bs4 import BeautifulSoup

ROOT='https://rondonia.ro.gov.br/fapero/'

def annual_links(html):
    s=BeautifulSoup(html,'html.parser');links={}
    for a in s.select('a[href]'):
        u=urljoin(ROOT,a['href'])
        if re.fullmatch(r'https://rondonia.ro.gov.br/fapero/publicacoes/\d{4}-\d+/(?:editais/)?',u):links[u]=a.get_text(' ',strip=True)
    if not links:raise ValueError('Annual menu missing')
    return links

def parse(html,url):
    s=BeautifulSoup(html,'html.parser');body=s.select_one('.conteudo-pagina-full .entry, .conteudo-pagina .entry')
    if body is None:raise ValueError('Source article missing')
    groups=[];owned=set()
    for section in body.select('section'):
        heading=section.find(['h2','h3'])
        if heading is None:continue
        links=[]
        for a in section.select('a[href]'):
            owned.add(id(a));links.append({'url':urljoin(url,a['href']),'title':a.get_text(' ',strip=True)})
        groups.append({'title':heading.get_text(' ',strip=True),'links':links,'text':section.get_text(' ',strip=True)})
    unassigned=[{'url':urljoin(url,a['href']),'title':a.get_text(' ',strip=True)} for a in body.select('a[href]') if id(a) not in owned]
    return {'groups':groups,'unassigned_links':unassigned,'text':body.get_text(' ',strip=True)}

LISTING=ROOT
leaves=annual_links

def page_url(url):
    if url!=ROOT and not re.fullmatch(r'https://rondonia.ro.gov.br/fapero/publicacoes/\d{4}-\d+/(?:editais/)?',url):raise ValueError('Pagina FAPERO fora do contrato')
    return url

def document_url(url):
    from urllib.parse import unquote,quote
    p=urlsplit(url);path=unquote(p.path)
    if p.scheme!='https' or p.netloc!='rondonia.ro.gov.br' or p.query or p.fragment or not path.startswith('/wp-content/uploads/') or not re.search(r'\.(pdf|docx?|xlsx?|zip)$',path,re.I) or any(x in ('.','..') for x in path.split('/')) or '%' in path or '\\' in path or any(ord(c)<32 for c in path):raise ValueError('Documento FAPERO fora do contrato')
    return 'https://rondonia.ro.gov.br'+quote(path,safe='/()')

def panels(html,url):
    from app.tenderproof.pilot_adapters import folded
    page_url(url);p=parse(html,url);groups=[]
    for g in p['groups']:
        docs=[];pending=[]
        for link in g['links']:
            try:target=document_url(link['url'])
            except ValueError:pending.append(link);continue
            text=folded(link['title']);kind='outro'
            if re.search('resultado|lista|cancelamento|homolog|convoc',text):pass
            elif 'prorrog' in text:kind='prorrogacao'
            elif 'retific' in text:kind='retificacao'
            elif 'anexo' in text:kind='anexo'
            elif 'edital' in text:kind='edital'
            docs.append({'url':target,'title':link['title'],'kind':kind,'format':urlsplit(target).path.rsplit('.',1)[-1].lower()})
        groups.append({**g,'documents':docs,'pending_links':pending})
    return groups,p['unassigned_links']
