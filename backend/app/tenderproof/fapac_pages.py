"""FAPAC document blocks delimited by published banners, separators and edition headings."""
import re
from urllib.parse import urljoin,urlsplit,unquote,quote
from bs4 import BeautifulSoup
from app.tenderproof.pilot_adapters import folded

LISTING='https://fapac.ac.gov.br/'
EDITAIS=LISTING+'98-2/'

def page_url(url):
    if url not in (LISTING,EDITAIS):raise ValueError('Pagina FAPAC fora do contrato')
    return url

def leaves(html):
    s=BeautifulSoup(html,'html.parser')
    if not any(urljoin(LISTING,a['href'])==EDITAIS and folded(a.get_text(' ',strip=True))=='editais' for a in s.select('a[href]')):raise ValueError('Menu Editais ausente')
    return {EDITAIS:'Editais'}

def document_url(url):
    p=urlsplit(url);path=unquote(p.path)
    if p.scheme!='https' or p.netloc!='fapac.ac.gov.br' or p.query or p.fragment or not path.startswith('/wp-content/uploads/') or not re.search(r'\.(pdf|docx?|xlsx?|zip)$',path,re.I) or any(x in ('.','..') for x in path.split('/')) or '%' in path or '\\' in path or any(ord(c)<32 for c in path):raise ValueError('Documento FAPAC fora do contrato')
    return LISTING.rstrip('/')+quote(path,safe='/()')

def panels(html,url):
    page_url(url);s=BeautifulSoup(html,'html.parser');body=s.select_one('article .czr-wp-the-content')
    if body is None:raise ValueError('Corpo Editais ausente')
    groups=[];docs=[];pending=[];texts=[]
    def flush():
        if docs or pending:
            groups.append({'title':next((d['title'] for d in docs if d['kind']=='edital'),texts[0] if texts else 'Sem titulo'),'documents':list(docs),'pending_links':list(pending),'text':' '.join(texts)})
        docs.clear();pending.clear();texts.clear()
    for node in body.find_all(recursive=False):
        label=node.get_text(' ',strip=True);fold=folded(label)
        if node.select_one('img') is not None or re.fullmatch(r'_+',label) or re.fullmatch(r'editais\s+\d{4}',fold):flush()
        if label:texts.append(label)
        for a in node.select('a[href]'):
            target=urljoin(url,a['href']);title=label or a.get('title','')
            try:target=document_url(target)
            except ValueError:
                pending.append({'url':target,'title':title});continue
            if any(d['url']==target for d in docs):continue
            kind='outro'
            if re.search(r'resultado|comissao|comunicado',fold):pass
            elif 'prorrog' in fold:kind='prorrogacao'
            elif re.search(r'retific|republic|errata|incorrec|aumento de recursos',fold):kind='retificacao'
            elif re.search(r'anexo|formulario|ficha de inscri|projeto para inscri',fold):kind='anexo'
            elif re.search(r'edital|chamamento|processo seletivo',fold):kind='edital'
            docs.append({'url':target,'title':title,'kind':kind,'format':urlsplit(target).path.rsplit('.',1)[-1].lower()})
    flush()
    return groups,[]
