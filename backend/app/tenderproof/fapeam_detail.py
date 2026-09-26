"""Identity-bound FAPEAM article documents; sidebar banners are not edital acts."""
import re
from urllib.parse import unquote, urljoin, urlsplit

from bs4 import BeautifulSoup

from app.tenderproof.fapeam_listing import validate_detail_url

DOCUMENT_HOSTS = ('www.fapeam.am.gov.br', 'fapeam.am.gov.br')


def validate_document_url(url):
    if not isinstance(url, str):
        raise ValueError('URL documental FAPEAM inválida')
    parts = urlsplit(url)
    path = unquote(parts.path)
    if (parts.scheme != 'https' or parts.netloc not in DOCUMENT_HOSTS
            or parts.query or parts.fragment or '\\' in path
            or any(ord(c) < 32 or ord(c) == 127 for c in path)
            or not re.fullmatch(r'/wp-content/uploads/\d{4}/(?:0[1-9]|1[0-2])/[^/]+\.pdf', path, re.I)):
        raise ValueError('documento fora dos uploads oficiais FAPEAM')


def parse_detail(html, *, url, external_id):
    validate_detail_url(url)
    if not isinstance(external_id, str) or not re.fullmatch(r'[1-9]\d*', external_id):
        raise ValueError('identidade de listagem FAPEAM inválida')
    if not isinstance(html, str) or len(html.encode('utf-8')) > 2*1024*1024:
        raise ValueError('detalhe FAPEAM excede limite')
    soup = BeautifulSoup(html, 'html.parser')
    canonical = soup.select('link[rel=canonical]')
    articles = soup.select('article.post-type-editais')
    if (len(canonical) != 1 or canonical[0].get('href') != url or len(articles) != 1
            or articles[0].get('id') != 'post-' + external_id):
        raise ValueError('identidade de detalhe FAPEAM não corroborada')
    article = articles[0]
    titles = article.select('h1.page-title')
    bodies = article.select('div.article-body')
    if len(titles) != 1 or not titles[0].get_text(strip=True) or len(bodies) != 1:
        raise ValueError('conteúdo principal FAPEAM ausente ou ambíguo')
    body = bodies[0]
    originals = body.select('.download-documento-box a[href]')
    if len(originals) > 1:
        raise ValueError('link principal FAPEAM ambíguo')
    original_url = urljoin(url, originals[0]['href']) if originals else None
    if original_url is not None:
        validate_document_url(original_url)
    docs = {}
    external_references = []
    for anchor in body.select('a[href]'):
        target = urljoin(url, anchor['href'])
        if not urlsplit(target).path.lower().endswith('.pdf'):
            continue
        if urlsplit(target).hostname not in DOCUMENT_HOSTS:
            reference = {'url_observed': target, 'label_observed': anchor.get_text(' ', strip=True),
                         'acquisition_status': 'not_acquired', 'relationship': 'requires_review'}
            if reference not in external_references:
                external_references.append(reference)
            continue
        validate_document_url(target)
        label = anchor.get_text(' ', strip=True) or anchor.get('title', '')
        primary = target == original_url
        row = docs.setdefault(target, {'url': target, 'kind': 'edital' if primary else 'requires_review',
            'labels_observed': [], 'context_observed': [], 'effect_status': 'not_assessed'})
        if label and label not in row['labels_observed']:
            row['labels_observed'].append(label)
        parent = anchor.find_parent(['p', 'li', 'td'])
        if parent is not None and body in parent.parents:
            context = parent.get_text(' ', strip=True)
            if context and context not in row['context_observed']:
                row['context_observed'].append(context)
    if original_url is not None and original_url not in docs:
        raise ValueError('documento principal não confirmado no corpo')
    return {'external_id': external_id, 'url': url, 'title_observed': titles[0].get_text(' ', strip=True),
        'documents': list(docs.values()), 'external_references': external_references,
        'principal_status': 'pdf_link_observed' if original_url else 'no_primary_pdf_link_observed',
        'body_text_observed': body.get_text(' ', strip=True),
        'scope_status': 'requires_document_review',
        'scope_complete': False, 'document_coverage_complete': False}
