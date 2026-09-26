"""FAPERR live navigation groups and editorial document manifests."""
import re
from urllib.parse import urlsplit,urljoin,unquote,quote
from bs4 import BeautifulSoup
from app.tenderproof.pilot_adapters import folded
LISTING='https://faperr.rr.gov.br/'

def detail_url(url):
    p=urlsplit(url)
    if p.scheme!='https' or p.netloc!='faperr.rr.gov.br' or p.query or p.fragment or not re.fullmatch('/[a-z0-9-]+/',p.path):raise ValueError('Detalhe FAPERR fora do contrato')
    return url

def document_url(url):
    p=urlsplit(url);path=unquote(p.path)
    if p.scheme!='https' or p.netloc!='faperr.rr.gov.br' or p.query or p.fragment or not path.startswith('/wp-content/uploads/') or not re.search(r'\.(pdf|docx?|xlsx?|zip|odt)$',path,re.I) or any(x in ('.','..') for x in path.split('/')) or '%' in path or '\\' in path or any(ord(c)<32 for c in path):raise ValueError('Documento FAPERR fora do contrato')
    return LISTING.rstrip('/')+quote(path,safe='/()')

def discover(html):
    s=BeautifulSoup(html,'html.parser');items={};groups=set()
    for a in s.select('nav a[href]'):
        category=folded(a.get_text(' ',strip=True))
        if category not in ('abertos','em andamento','encerrados'):continue
        groups.add(category)
        for child in a.parent.select('ul a[href]'):
            if child['href'].startswith('#'):continue
            url=detail_url(urljoin(LISTING,child['href']));items[url]={'title':child.get_text(' ',strip=True),'category':category}
    if groups!={'abertos','em andamento','encerrados'} or not items:raise ValueError('Menu FAPERR incompleto')
    return items

def parse(html,url):
    detail_url(url);s=BeautifulSoup(html,'html.parser');body=s.select_one('article .entry-content');h=s.select_one('article h1.entry-title')
    if body is None or h is None:raise ValueError('Conteudo FAPERR ausente')
    docs=[];pending=[]
    for a in body.select('a[href]'):
        target=urljoin(url,a['href']);title=a.get_text(' ',strip=True)
        if a['href'].startswith(('#','mailto:','tel:')):continue
        try:target=document_url(target)
        except ValueError:pending.append({'url':target,'title':title});continue
        text=folded(title);kind='outro'
        if re.search('resultado|homolog|convoc|classific|enquadramento|publicacao',text):pass
        elif 'prorrog' in text:kind='prorrogacao'
        elif 'retific' in text:kind='retificacao'
        elif re.search('anexo|formulario|modelo|declaracao|termo',text):kind='anexo'
        elif re.match('(edital|chamada|chamamento)',text):kind='edital'
        docs.append({'url':target,'title':title,'kind':kind,'format':urlsplit(target).path.rsplit('.',1)[-1].lower()})
    return {'url':url,'title':h.get_text(' ',strip=True),'documents':docs,'pending_links':pending,'text':body.get_text(' ',strip=True)}
