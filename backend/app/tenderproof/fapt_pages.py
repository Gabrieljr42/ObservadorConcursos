"""Traverse FAPT's published edital graph and preserve document links with their context."""
import re
from urllib.parse import urljoin,urlsplit
from bs4 import BeautifulSoup

HOST='https://www.to.gov.br'
LISTING=HOST+'/fapt/'

def page_url(url):
    p=urlsplit(url)
    if p.scheme not in ('http','https') or p.netloc!='www.to.gov.br' or p.query or p.fragment or not re.fullmatch(r'/fapt/(?:[a-z0-9-]+/[a-z0-9]+)?',p.path):raise ValueError('FAPT page boundary')
    return 'https://'+p.netloc+p.path

def parse(raw,url):
    s=BeautifulSoup(raw,'html.parser');body=s.select_one('.page_main_content');h=s.select_one('.page_headline h1')
    if body is None or h is None:raise ValueError('FAPT content missing')
    children={};docs=[];pending=[]
    for a in body.select('a[href]'):
        title=a.get_text(' ',strip=True)
        for icon in a.select('i'):icon.decompose()
        title=a.get_text(' ',strip=True);target=urljoin(url,a['href'])
        if a['href'].startswith(('#','mailto:','tel:')):continue
        if re.fullmatch(r'https://central.to.gov.br/download/[0-9]+',target):
            docs.append({'title':title,'url':target});continue
        try:children[page_url(target)]=title
        except ValueError:pending.append({'url':target,'title':title})
    return {'title':h.get_text(' ',strip=True),'children':children,'documents':docs,'pending_links':pending,'text':body.get_text(' ',strip=True)}

def document_url(url):
    if not re.fullmatch(r'https://central.to.gov.br/download/[0-9]+',url):raise ValueError('FAPT document boundary')
    return url

def document_kind(title):
    from app.tenderproof.pilot_adapters import folded
    text=folded(title).replace('_',' ')
    if re.search(r'resultado|homolog|convoc|entrevista|cadastro.reserva|suspens|impugna|propostas|enquadrad',text):return 'outro'
    if 'prorrog' in text:return 'prorrogacao'
    if 'retific' in text:return 'retificacao'
    if re.search(r'anexo|formulario|modelo|declaracao|termo',text):return 'anexo'
    if re.match(r'(edital|chamamento|chamada)',text):return 'edital'
    return 'outro'
