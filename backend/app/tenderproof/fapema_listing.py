"""FAPEMA category pages with observed pagination and stable editorial URLs."""
import re
from urllib.parse import urlsplit, urljoin
from bs4 import BeautifulSoup

HOST='https://www.fapema.br'


def listing_url(url):
    p=urlsplit(url)
    match=re.fullmatch(r'/category/editais/(editais-[a-z-]+)/(?:page/([1-9]\d*)/)?',p.path)
    if p.scheme!='https' or p.netloc!='www.fapema.br' or p.query or p.fragment or not match:
        raise ValueError('categoria FAPEMA fora do contrato')
    return match[1], int(match[2] or 1)


def detail_url(url):
    p=urlsplit(url)
    if p.scheme!='https' or p.netloc!='www.fapema.br' or p.query or p.fragment or not re.fullmatch(r'/[a-z0-9_-]+/',p.path):
        raise ValueError('detalhe FAPEMA fora do contrato')
    return p.path.strip('/')


def discover_categories(html):
    soup=BeautifulSoup(html,'html.parser')
    urls=[]
    for a in soup.select('a[href]'):
        url=urljoin(HOST+'/',a['href'])
        if '/category/editais/editais-' not in url:
            continue
        listing_url(url)
        urls.append(url)
    if not urls:
        raise ValueError('menu FAPEMA sem categorias identificadas')
    return sorted(set(urls))


def parse_listing(html,url):
    category,number=listing_url(url)
    soup=BeautifulSoup(html,'html.parser')
    main=soup.select_one('main#main')
    if main is None or main.select_one('.search-results') is None:
        raise ValueError('listagem FAPEMA não identificada')
    rows=[]
    for item in main.select('.search-result-item'):
        links=item.select('h3 a[href]')
        if len(links)!=1:
            raise ValueError('linha editorial não interpretada')
        a=links[0]
        target=urljoin(url,a['href']);detail_url(target)
        title=a.get_text(' ',strip=True)
        if not title:
            raise ValueError('título editorial ausente')
        date=item.select_one('.search-result-date');excerpt=item.select_one('.search-result-excerpt')
        rows.append({'url':target,'title':title,'date_observed':date.get_text(' ',strip=True) if date else None,
            'excerpt':excerpt.get_text(' ',strip=True) if excerpt else None})
    if not rows:
        raise ValueError('categoria vazia sem prova de ausência')
    pager=main.select_one('.pagination');next_urls=[];terminal=False
    if pager is not None and not pager.get_text(strip=True) and not pager.select('a[href]'):
        pager=None
    if pager:
        current=pager.select_one('[aria-current=page]')
        if current is None or current.get_text(strip=True)!=str(number):
            raise ValueError('página corrente diverge da URL')
        indices=[number]
        for a in pager.select('a[href]'):
            target=urljoin(url,a['href']);kind,index=listing_url(target)
            if kind!=category:
                raise ValueError('paginador troca categoria')
            indices.append(index)
            if target!=url:next_urls.append(target)
        terminal=not pager.select_one('a.next[href]') and number==max(indices)
    return {'items':rows,'next_urls':sorted(set(next_urls)),'terminal':terminal,
        'diagnostics':[] if pager else ['Sem paginador explícito; completude não comprovada.']}
