"""Observed FAPEAL annual archives and document-bearing editorial pages."""
import re
from urllib.parse import urlsplit,urljoin,unquote,quote
from bs4 import BeautifulSoup
from app.tenderproof.pilot_adapters import folded

HOST='https://www.fapeal.br'
LISTING=HOST+'/pesquisador/editais/'

def local(url,pattern):
    p=urlsplit(url)
    if p.scheme!='https' or p.netloc!='www.fapeal.br' or p.query or p.fragment or not re.fullmatch(pattern,p.path):
        raise ValueError('URL FAPEAL fora do contrato')
    return url

def category_url(url):return local(url,r'/category/editais/[0-9]{3,4}/(?:page/[1-9][0-9]*/)?')
def detail_url(url):return local(url,r'/[0-9]{4}/[0-9]{2}/[a-z0-9_-]+/')

def document_url(url):
    p=urlsplit(url);path=unquote(p.path)
    if (p.scheme!='https' or p.netloc!='www.fapeal.br' or p.query or p.fragment
            or not path.startswith('/wp-content/uploads/') or not re.search(r'\.(pdf|docx?|odt|xlsx?|zip)$',path,re.I)
            or any(x in ('.','..') for x in path.split('/')) or '\\' in path or '%' in path
            or any(ord(c)<32 for c in path)):
        raise ValueError('documento FAPEAL fora do contrato')
    return HOST+quote(path,safe='/')

def discover_categories(html):
    s=BeautifulSoup(html,'html.parser');out={}
    for a in s.select('main .widget_nav_menu a[href]'):
        if re.fullmatch(r'\d{4}',a.get_text(strip=True)):
            url=category_url(urljoin(LISTING,a['href']));out[url]=a.get_text(strip=True)
    if not out:raise ValueError('menu anual FAPEAL ausente')
    return out

def parse_listing(html,url):
    category_url(url);s=BeautifulSoup(html,'html.parser');main=s.select_one('main#main')
    if main is None:raise ValueError('arquivo anual FAPEAL ausente')
    items=[]
    for article in main.select('article.type-post'):
        links=article.select('h2.entry-title a[href]')
        if len(links)!=1 or not links[0].get_text(strip=True):raise ValueError('identidade editorial ausente')
        items.append({'url':detail_url(urljoin(url,links[0]['href'])),'title':links[0].get_text(' ',strip=True),
            'categories_observed':article.get('class',[])})
    next_urls=[]
    for a in s.select('.pagination a[href],.nav-links a[href],a[rel=next]'):
        target=urljoin(url,a['href'])
        if '/category/editais/' in target:
            category_url(target)
            if target.split('/page/')[0].rstrip('/')!=url.split('/page/')[0].rstrip('/'):
                raise ValueError('paginacao altera categoria')
            if target!=url and target not in next_urls:next_urls.append(target)
    empty=main.select_one('section.no-results h2.page-title')
    if not items and empty is not None and folded(empty.get_text(' ',strip=True))=='nada encontrado':
        return {'items':[],'next_urls':[],'coverage_complete':False,'empty_evidence':'Nada encontrado',
            'reason':'Categoria observada sem resultados; nao comprova ausencia historica de editais.'}
    if not items:raise ValueError('vazio FAPEAL sem evidencia explicita')
    return {'items':items,'next_urls':next_urls,'coverage_complete':False,
        'reason':'Ausencia de pagina seguinte nao comprova exaustao do arquivo anual.'}

def parse_detail(html,url):
    detail_url(url);s=BeautifulSoup(html,'html.parser');canonical=s.select_one('link[rel=canonical]')
    if canonical is None or canonical.get('href')!=url:raise ValueError('canonical FAPEAL divergente')
    article=s.select_one('main article.type-post');title=article.select_one('h1.entry-title') if article else None
    content=article.select_one('.entry-content') if article else None
    if title is None or content is None:raise ValueError('detalhe editorial FAPEAL ausente')
    for n in content.select('.essb_links,script,style'):n.decompose()
    docs=[];pending=[];seen=set()
    for a in content.select('a[href],iframe[src],embed[src],object[data]'):
        href=a.get('href') or a.get('src') or a.get('data');target=urljoin(url,href);label=a.get_text(' ',strip=True)
        if href.startswith(('#','mailto:','tel:')):continue
        if (target,label) in seen:continue
        seen.add((target,label))
        try:target=document_url(target)
        except ValueError:
            pending.append({'title':label,'url':target});continue
        text=folded(label);kind='outro'
        if re.search(r'resultado|homolog|convoc|classific',text):pass
        elif re.search(r'prorrog',text):kind='prorrogacao'
        elif re.search(r'retificado|consolidado',text):kind='consolidado'
        elif re.search(r'retific|errata|adendo',text):kind='retificacao'
        elif re.search(r'anexo',text):kind='anexo'
        elif re.match(r'(edital|chamada)\b',text):kind='edital'
        docs.append({'url':target,'title':label,'kind':kind,'format':target.rsplit('.',1)[1].lower()})
    return {'url':url,'title':title.get_text(' ',strip=True),'documents':docs,'pending_links':pending,
        'body_text':content.get_text(' ',strip=True),'scope_review_required':True,'source_integrated':False}
