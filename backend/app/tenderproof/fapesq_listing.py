"""Observed public Plone collection pagination for FAPESQ."""
import re
from urllib.parse import parse_qs, urljoin, urlsplit
from app.tenderproof.pilot_adapters import visible_soup

HOST='https://fapesq.rpp.br'


def annual_url(url):
    p=urlsplit(url)
    match=re.fullmatch(r'/editais/(\d{4})/editais-\1',p.path.rstrip('/'))
    if p.scheme!='https' or p.netloc!='fapesq.rpp.br' or p.query or p.fragment or not match:
        raise ValueError('URL fora do índice anual público FAPESQ')
    return match[1]


def parse_annual(html,url):
    year=annual_url(url)
    content=visible_soup(html).select_one('#content')
    if content is None:raise ValueError('índice anual público ausente')
    collections=[];annuals=[];unresolved=[]
    for anchor in content.select('a[href]'):
        target=urljoin(url,anchor['href'])
        try:
            other_year,offset=collection_url(target)
            if other_year!=year or offset:raise ValueError('coleção inicial de outro ano')
            collections.append(target)
            continue
        except ValueError:
            pass
        try:
            annual_url(target)
            if target!=url:annuals.append(target)
        except ValueError:
            if re.search(r'editais.*\d{4}',anchor.get_text(' ',strip=True),re.I):
                unresolved.append(target)
    collections=list(dict.fromkeys(collections))
    if len(collections)!=1:raise ValueError('coleção anual única não comprovada')
    return {'year':year,'collection':collections[0],'annuals':list(dict.fromkeys(annuals)),
            'unresolved_links':list(dict.fromkeys(unresolved))}


def collection_url(url):
    p=urlsplit(url)
    match=re.fullmatch(r'/editais/(\d{4})/colecao-de-editais-\1',p.path.rstrip('/'))
    params=parse_qs(p.query,keep_blank_values=True)
    if (p.scheme!='https' or p.netloc!='fapesq.rpp.br' or p.fragment or not match
            or set(params)-{'b_start:int'} or any(len(v)!=1 or not re.fullmatch(r'\d{1,6}',v[0]) for v in params.values())):
        raise ValueError('URL fora da coleção pública FAPESQ')
    return match[1],int(params.get('b_start:int',['0'])[0])


def parse_collection(html,url):
    year,offset=collection_url(url)
    soup=visible_soup(html);content=soup.select_one('#content')
    if content is None:raise ValueError('conteúdo público da coleção ausente')
    items=[];seen=set()
    for anchor in content.select('.tileHeadline a[href]'):
        target=urljoin(url,anchor['href']);p=urlsplit(target)
        if (p.scheme!='https' or p.netloc!='fapesq.rpp.br' or p.query or p.fragment
                or not re.fullmatch(r'/editais/'+year+r'/[a-z0-9-]+',p.path)):
            raise ValueError('detalhe fora do contrato público da coleção')
        if target in seen:raise ValueError('detalhe duplicado na coleção')
        seen.add(target);items.append({'url':target,'title':anchor.get_text(' ',strip=True)})
    if not items:raise ValueError('coleção vazia sem declaração de ausência')
    pager=content.select_one('.listingBar')
    if pager is None:raise ValueError('paginação da coleção não declarada')
    following=pager.select('a.proximo[href]')
    if len(following)>1:raise ValueError('próxima página ambígua')
    next_url=None
    if following:
        next_url=urljoin(url,following[0]['href']);next_year,next_offset=collection_url(next_url)
        if next_year!=year or next_offset<=offset:raise ValueError('paginação regressiva ou de outro ano')
    else:
        current=[int(x.get_text(strip=True)) for x in pager.select('li > span') if x.get_text(strip=True).isdigit()]
        linked=[int(x.get_text(strip=True)) for x in pager.select('a') if x.get_text(strip=True).isdigit()]
        if len(current)!=1 or any(n>current[0] for n in linked):raise ValueError('fim da coleção não comprovado')
    return {'items':items,'next_url':next_url,'terminal':next_url is None,'year':year,'offset':offset}
