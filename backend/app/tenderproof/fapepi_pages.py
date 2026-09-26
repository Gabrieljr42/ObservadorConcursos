"""Observed FAPEPI WordPress listing and editorial document contracts."""
import re
from urllib.parse import urlsplit, urljoin, unquote
from bs4 import BeautifulSoup
from app.tenderproof.pilot_adapters import folded

ROOT = 'https://www.fapepi.pi.gov.br'
LISTING = ROOT + '/editais-fapepi/'


def detail_url(url):
    p = urlsplit(url)
    if (p.scheme != 'https' or p.netloc != 'www.fapepi.pi.gov.br' or p.query or p.fragment
            or not re.fullmatch(r'/edital/[a-z0-9_-]+/', p.path)):
        raise ValueError('endereço de edital FAPEPI inválido')
    return p.path.split('/')[2]


def parse_listing(html):
    soup = BeautifulSoup(html, 'html.parser')
    lists = soup.select('ul.display-posts-listing')
    if not lists:
        raise ValueError('listas editoriais FAPEPI ausentes')
    items = {}
    for listing in lists:
        panel = listing.find_parent(class_='eael-tab-content-item')
        section = None
        if panel and panel.get('id'):
            tabs = soup.find_all(attrs={'role': 'tab', 'aria-controls': panel['id']})
            if len(tabs) != 1:
                raise ValueError('seção FAPEPI sem rótulo único')
            section = tabs[0].get_text(' ', strip=True)
        for row in listing.find_all('li', recursive=False):
            links = row.select('a.title[href]')
            if len(links) != 1:
                raise ValueError('linha de listagem FAPEPI não interpretada')
            a = links[0]
            url = urljoin(LISTING, a['href'])
            detail_url(url)
            title = a.get_text(' ', strip=True)
            if not title:
                raise ValueError('título de edital ausente')
            item = items.setdefault(url, {'url': url, 'titles': [], 'sections': []})
            item['titles'].append(title)
            if section and section not in item['sections']:
                item['sections'].append(section)
    if not items:
        raise ValueError('vazio sem declaração de ausência')
    navigation = [{'url': urljoin(LISTING, a['href']), 'text': a.get_text(' ', strip=True)}
        for a in soup.select('.pagination a[href], .nav-links a[href], a[rel=next]')]
    return {'items': list(items.values()), 'navigation': navigation,
        'coverage_complete': False, 'coverage_reason': 'Listas publicadas sem contador total; completude histórica exige conferência.'}


def document_url(url):
    p = urlsplit(url)
    path = unquote(p.path)
    if (p.scheme != 'https' or p.netloc != 'www.fapepi.pi.gov.br' or p.query or p.fragment
            or not path.startswith('/wp-content/uploads/') or not re.search(r'\.(pdf|docx?|xlsx?|zip|odt)$', path, re.I)
            or any(s in ('.', '..') for s in path.split('/')) or '\\' in path or '%' in path):
        raise ValueError('arquivo fora do contrato documental FAPEPI')


def parse_detail(html, url):
    detail_url(url)
    soup = BeautifulSoup(html, 'html.parser')
    canonical = soup.select_one('link[rel=canonical][href]')
    if canonical is None or canonical['href'] != url:
        raise ValueError('identidade canônica divergente FAPEPI')
    main = soup.select_one('main.type-edital')
    heading = main.select_one('h1.entry-title') if main else None
    content = main.select_one('.page-content') if main else None
    if heading is None or content is None:
        raise ValueError('corpo de edital FAPEPI não identificado')
    documents, pending = [], []
    for a in content.select('a[href]'):
        target = urljoin(url, a['href'])
        label = a.get_text(' ', strip=True)
        try:
            document_url(target)
        except ValueError:
            pending.append({'url': target, 'title': label, 'reason': 'Link complementar exige contrato e inspeção próprios.'})
            continue
        text = folded(label)
        if re.search(r'resultado|homologacao|classificacao|convocacao|recurso', text):
            kind = 'outro'
        elif re.search(r'prorrog|reabertura', text):
            kind = 'prorrogacao'
        elif re.search(r'retificad|consolidad', text):
            kind = 'consolidado'
        elif re.search(r'retifica|errata|alteracao', text):
            kind = 'retificacao'
        elif re.match(r'anexo', text):
            kind = 'anexo'
        elif re.match(r'(edital|chamada)\b', text):
            kind = 'edital'
        else:
            kind = 'outro'
        documents.append({'title': label, 'url': target, 'kind': kind})
    return {'title': heading.get_text(' ', strip=True), 'url': url,
        'published_text': (main.select_one('.page-meta').get_text(' ', strip=True) if main.select_one('.page-meta') else None),
        'body_text': content.get_text(' ', strip=True), 'documents': documents, 'pending_links': pending,
        'scope_review_required': True, 'manifest_complete': bool(documents) and not pending}
