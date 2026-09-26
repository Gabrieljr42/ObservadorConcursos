"""FUNDECT current API and previous-call pages; preserve documentary roles and scope."""
import json,re
from urllib.parse import urlsplit,urljoin,unquote,quote
from bs4 import BeautifulSoup
from app.tenderproof.pilot_adapters import folded
HOST='https://www.fundect.ms.gov.br'
LISTING=HOST+'/informativos/consultas/'
API=HOST+'/wp-json/consultas/v1/list'
HISTORY=HOST+'/editais-anteriores/'

def detail_url(url):
    p=urlsplit(url)
    if p.scheme!='https' or p.netloc!='www.fundect.ms.gov.br' or p.query or p.fragment or not re.fullmatch(r'/(?:informativos/consultas/)?[a-z0-9_-]+/',p.path):
        raise ValueError('detalhe FUNDECT fora do contrato')
    return url

def document_url(url):
    p=urlsplit(url);path=unquote(p.path)
    if (p.scheme!='https' or p.netloc!='www.fundect.ms.gov.br' or p.query or p.fragment
        or not path.startswith('/wp-content/uploads/') or not re.search(r'\.(pdf|docx?|xlsx?|odt|zip)$',path,re.I)
        or any(x in ('.','..')for x in path.split('/')) or '\\'in path or '%'in path or any(ord(c)<32 for c in path)):
        raise ValueError('documento FUNDECT fora do contrato')
    return HOST+quote(path,safe='/')

def history_items(html):
    s=BeautifulSoup(html,'html.parser');items={}
    for a in s.select('main .wp-block-latest-posts a.wp-block-latest-posts__post-title[href]'):
        items[detail_url(urljoin(HISTORY,a['href']))]=a.get_text(' ',strip=True)
    if not items:raise ValueError('arquivo de editais anteriores ausente')
    return items

def documents(html,url):
    s=BeautifulSoup(html,'html.parser');docs=[];pending=[];seen=set()
    for a in s.select('a[href],iframe[src],embed[src],object[data]'):
        href=a.get('href')or a.get('src')or a.get('data');target=urljoin(url,href)
        if href.startswith(('#','mailto:','tel:')):continue
        title=a.get_text(' ',strip=True);parent=a.find_parent(['p','li'])
        context=parent.get_text(' ',strip=True)if parent else title
        if (target,title)in seen:continue
        seen.add((target,title))
        try:target=document_url(target)
        except ValueError:pending.append({'title':title,'url':target});continue
        text=re.sub(r'^\d{2}/\d{2}/\d{2,4}\s*[-–]?\s*','',folded(title));kind='outro'
        if re.search(r'resultado|homolog|convoc|classific|cancelamento|nomeacao|enquadramento',text):pass
        elif 'prorrog'in text:kind='prorrogacao'
        elif re.search(r'retificado|consolidado',text):kind='consolidado'
        elif re.search(r'retific|errata|alteracao',text):kind='retificacao'
        elif re.match(r'(chamada|edital)\b',text):kind='edital'
        elif re.search(r'\banexo\b',folded(context)):kind='anexo'
        docs.append({'url':target,'title':title,'context':context,'kind':kind,'format':target.rsplit('.',1)[1].lower()})
    return {'documents':docs,'pending_links':pending,'scope_review_required':True}

def parse_api(raw):
    data=json.loads(raw)
    if not isinstance(data,dict)or not isinstance(data.get('posts'),list):raise ValueError('API FUNDECT divergente')
    out=[];ids=set()
    for post in data['posts']:
        if type(post.get('id'))is not int or post['id']<=0 or post['id']in ids:raise ValueError('ID FUNDECT ausente ou repetido')
        ids.add(post['id']);url=detail_url(post['permalink'])
        if not post.get('projeto')or not isinstance(post.get('observacao_html'),str):raise ValueError('conteudo documental ausente')
        parsed=documents(post['observacao_html'],url)
        # The prominent proposal link often points to an update or result, not the original.
        if post.get('proposta')and post['proposta']not in {d['url']for d in parsed['documents']}:
            parsed['pending_links'].append({'title':post.get('leitura',''),'url':post['proposta'],'reason':'proposta fora das observacoes documentais'})
        out.append({'id':post['id'],'url':url,'title':post['projeto'],'status_observed':post.get('tramitacao'),
            'subject':post.get('assunto'),'body_text':post.get('observacao'),**parsed})
    return out

def parse_detail(html,url):
    detail_url(url);s=BeautifulSoup(html,'html.parser');canonical=s.select_one('link[rel=canonical]')
    if canonical is None or canonical.get('href')!=url:raise ValueError('canonical FUNDECT divergente')
    title=s.select_one('#post-interno h1');body=s.select_one('.post-noticias-conteudo')
    if title is None or body is None:raise ValueError('conteudo editorial FUNDECT ausente')
    for n in body.select('.post-noticias-categoria-footer,script,style'):n.decompose()
    return {'url':url,'title':title.get_text(' ',strip=True),'body_text':body.get_text(' ',strip=True),**documents(str(body),url)}
