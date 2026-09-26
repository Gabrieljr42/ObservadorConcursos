"""FAPEMA editorial documents, including PDF.js links and HTML notices."""
import re
from urllib.parse import urlsplit,urljoin,parse_qs,unquote,quote
from bs4 import BeautifulSoup
from app.tenderproof.fapema_listing import HOST,detail_url
from app.tenderproof.pilot_adapters import folded


def document_url(url):
    p=urlsplit(url);path=unquote(p.path)
    if (p.scheme!='https' or p.netloc!='www.fapema.br' or p.query or p.fragment
            or not path.startswith('/wp-content/uploads/') or not re.search(r'\.(pdf|docx?|xlsx?|odt|zip)$',path,re.I)
            or any(x in ('.','..') for x in path.split('/')) or '\\' in path or '%' in path
            or any(ord(c)<32 for c in path)):
        raise ValueError('documento fora do contrato FAPEMA')
    return HOST+quote(path,safe='/')


def viewer_document(url):
    p=urlsplit(url)
    if (p.scheme!='https' or p.netloc!='www.fapema.br'
            or p.path!='/wp-content/plugins/pdfjs-viewer-shortcode/pdfjs/web/viewer.php'):
        raise ValueError('visualizador PDF.js fora do contrato')
    params=parse_qs(p.query,keep_blank_values=True)
    if len(params.get('file',[]))!=1:
        raise ValueError('visualizador sem arquivo único')
    return document_url(params['file'][0])


def role(label):
    text=folded(label)
    text=re.sub(r'^\d{1,2}/\d{1,2}(?:/\d{2,4})?\s*[-–—:]?\s*','',text)
    if re.search(r'resultado|excedente|convoca|homologa|recurso|classifica',text):return 'outro'
    if re.search(r'prorrog|reabertura',text):return 'prorrogacao'
    if re.search(r'retificad|consolidad',text):return 'consolidado'
    if re.search(r'retifica|errata|altera',text):return 'retificacao'
    if re.match(r'anexo',text):return 'anexo'
    if re.match(r'edital\b',text):return 'edital'
    return 'outro'


def parse_detail(html,url):
    detail_url(url);soup=BeautifulSoup(html,'html.parser')
    canonical=soup.select_one('link[rel=canonical][href]')
    if canonical is None or canonical['href']!=url:raise ValueError('identidade canônica FAPEMA divergente')
    article=soup.select_one('article#main')
    title=article.select_one('h1.h-entry__p-name') if article else None
    content=article.select_one('.h-entry__e-content') if article else None
    if title is None or content is None:raise ValueError('corpo editorial FAPEMA ausente')
    documents=[];pending=[];grouped={};current_label=None
    # The source closes accordion wrappers early. Associate viewer pairs with
    # preceding editorial anchors in DOM order, never with a stale wrapper.
    for node in content.select('a[href],iframe[src],embed[src],object[data]'):
        raw=node.get('src') or node.get('href') or node.get('data')
        label=node.get_text(' ',strip=True) or node.get('title') or ''
        if raw=='#':
            current_label=label or None
            continue
        if raw.startswith('#'):continue
        target=urljoin(url,raw)
        viewer='/pdfjs/web/viewer.php?' in target
        if viewer:
            label=current_label
            if not label:
                pending.append({'url':target,'reason':'Visualizador sem rótulo editorial anterior'})
                continue
        try:
            resolved=viewer_document(target) if viewer else document_url(target)
            if not label:
                pending.append({'url':target,'reason':'Documento sem rótulo'})
                continue
            key=(label,resolved)
            if key not in grouped:
                grouped[key]={'title':label,'url':resolved,'kind':role(label),'observed_links':[]}
                documents.append(grouped[key])
            grouped[key]['observed_links'].append(target)
        except ValueError as exc:pending.append({'url':target,'title':label,'reason':str(exc)})
    notices=[]
    for node in content.select('p,h2,h3,h4'):
        text=node.get_text(' ',strip=True)
        if re.search(r'comunicado|prorrog|retific|errata',folded(text)) and text not in notices:
            notices.append(text)
    return {'url':url,'title':title.get_text(' ',strip=True),'documents':documents,'pending_links':pending,
        'html_notices':notices,'body_text':content.get_text(' ',strip=True),'scope_review_required':True,
        'manifest_complete':bool(documents) and not pending,'html_effect_review_required':bool(notices)}
