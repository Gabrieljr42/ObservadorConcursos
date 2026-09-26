"""FAPDF menu and Liferay panels; unstable DOM ids are never contest identities."""
import re
from urllib.parse import urljoin,urlsplit,unquote
from bs4 import BeautifulSoup
from app.tenderproof.pilot_adapters import folded

HOST='https://fap.df.gov.br'
LISTING=HOST+'/'

def page_url(url):
    p=urlsplit(url)
    if p.scheme!='https' or p.netloc!='fap.df.gov.br' or p.query or p.fragment or not re.fullmatch(r'/(?:[a-z0-9_-]+/)*[a-z0-9_-]*',p.path):raise ValueError('Pagina FAPDF fora do contrato')
    return url

def document_url(url):
    p=urlsplit(url);path=unquote(p.path)
    if p.scheme!='https' or p.netloc!='fap.df.gov.br' or p.query or p.fragment or not path.startswith('/documents/') or any(x in ('.','..') for x in path.split('/')) or '%' in path or '\\' in path or any(ord(c)<32 for c in path):raise ValueError('Documento FAPDF fora do contrato')
    return url

def leaves(html):
    s=BeautifulSoup(html,'html.parser')
    menus=[a.parent for a in s.select('a[href]') if urljoin(LISTING,a['href'])==HOST+'/category/editais']
    if not menus:raise ValueError('Menu de editais ausente')
    result={}
    for menu in menus:
        for a in menu.select('li a[href]'):
            if not a.parent.find('ul',recursive=False):result[page_url(urljoin(LISTING,a['href']))]=a.get_text(' ',strip=True)
    if not result:raise ValueError('Menu de editais vazio')
    return result

def panels(html,url):
    page_url(url);s=BeautifulSoup(html,'html.parser');groups=[];owned=set()
    for b in s.select('.journal-content-article button[aria-controls]'):
        panel=s.find(id=b['aria-controls'])
        if panel is None:raise ValueError('Painel ausente')
        if panel.select('button[aria-controls]'):continue
        docs=[];pending=[];registrations=[]
        for a in panel.select('a[href]'):
            owned.add(id(a));target=urljoin(url,a['href']);title=a.get_text(' ',strip=True);p=a.find_parent(['p','li']);context=p.get_text(' ',strip=True) if p else title
            if a['href'].startswith(('#','mailto:','tel:')):continue
            try:document_url(target)
            except ValueError:
                (registrations if 'formulario de inscricao' in folded(title) else pending).append({'url':target,'title':title});continue
            text=folded(title);ctx=folded(context);kind='outro'
            if re.search('resultado|homolog|convoc|comissao|extrato|outorga',text):pass
            elif 'prorrog' in ctx:kind='prorrogacao'
            elif 'retific' in ctx or 'republica' in ctx:kind='consolidado' if re.search('edital|chamada',text) else 'retificacao'
            elif re.search('anexo|declaracao|formulario|termo de',text):kind='anexo'
            elif re.match(r'(edital|chamada)',text):kind='edital'
            docs.append({'url':target,'title':title,'kind':kind,'context':context})
        groups.append({'title':b.get_text(' ',strip=True),'documents':docs,'pending_links':pending,'registration_links':registrations,'text':panel.get_text(' ',strip=True)})
    unassigned=[{'url':urljoin(url,a['href']),'title':a.get_text(' ',strip=True)} for a in s.select('.journal-content-article a[href]') if id(a) not in owned]
    return groups,unassigned
