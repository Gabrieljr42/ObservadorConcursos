"""Preserve FAPED personnel accordions and literal document append statements."""
import json
import re
from datetime import datetime
from urllib.parse import urljoin, urlsplit

from bs4 import BeautifulSoup

LISTING = 'https://faped.org.br/editais&filter=2'
_APPEND = re.compile(r'''\s*app\.id\('docfor(?P<id>[1-9]\d*)'\)\.innerHTML\s*\+=\s*(?P<literal>"(?:[^"\\]|\\.)*")\s*;\s*''', re.S)


def validate_document(url):
    parts = urlsplit(url)
    if (parts.scheme != 'https' or parts.netloc != 'faped.org.br' or parts.query or parts.fragment
            or not re.fullmatch(r'/files/uploads/document/[A-Za-z0-9_-]+\.pdf', parts.path)):
        raise ValueError('documento fora da biblioteca PDF pública FAPED')


def document_rows(container):
    rows = []
    for anchor in container.select('a[href]'):
        blocks = anchor.select('.file-block')
        if len(blocks) != 1:
            raise ValueError('linha documental FAPED não interpretada')
        block = blocks[0]
        title = block.find('span')
        date = re.search(r'Publicado em (\d{2}/\d{2}/\d{4} \d{2}:\d{2})\s*$', block.get_text(' ', strip=True))
        if title is None or not title.get_text(' ', strip=True) or not date:
            raise ValueError('metadados documentais FAPED incompletos')
        url = urljoin(LISTING, anchor['href'])
        validate_document(url)
        rows.append({'title': title.get_text(' ', strip=True), 'url': url,
            'published_at_local': datetime.strptime(date[1], '%d/%m/%Y %H:%M').isoformat()})
    return rows


def parse_personnel(html):
    if len(html.encode('utf-8')) > 2 * 1024 * 1024:
        raise ValueError('listagem FAPED excede limite')
    soup = BeautifulSoup(html, 'html.parser')
    calls = {}
    for item in soup.select('.accordion-item'):
        header = item.select_one('.accordion-header h5.title')
        body = item.select_one('.accordion-body')
        containers = body.select('[id^="docfor"]') if body else []
        if header is None or len(containers) != 1:
            raise ValueError('seleção FAPED sem identidade documental única')
        identity = re.fullmatch(r'docfor([1-9]\d*)', containers[0]['id'])
        if not identity or identity[1] in calls:
            raise ValueError('identidade de seleção ausente ou repetida')
        title = header.get_text(' ', strip=True)
        if not re.search(r'PROCESSO SELETIVO SIMPLIFICADO', title, re.I):
            raise ValueError('item não confirmado como seleção celetista')
        opening = re.search(r'Abertura:\s*(\d{2}/\d{2}/\d{4})', body.get_text(' ', strip=True))
        if not opening:
            raise ValueError('data de abertura não interpretada')
        calls[identity[1]] = {'identity': identity[1], 'title': title,
            'candidate_title': re.sub(r'\s+(?:Encerrado|Aberto)\s*$', '', title, flags=re.I),
            'opening_date': datetime.strptime(opening[1], '%d/%m/%Y').date().isoformat(),
            'description': body.get_text(' ', strip=True), 'documents': document_rows(containers[0])}
    if not calls:
        raise ValueError('ausência de seleções celetistas não confirmada')
    for script in soup.select('script'):
        text = script.get_text()
        ids = re.findall(r'docfor([1-9]\d*)', text)
        if not set(ids).intersection(calls):
            continue
        match = _APPEND.fullmatch(text)
        if not match or match['id'] not in calls:
            raise ValueError('instrução documental FAPED não interpretada integralmente')
        # Decode a string literal only. No JavaScript is evaluated or executed.
        fragment = BeautifulSoup(json.loads(match['literal']), 'html.parser')
        docs = document_rows(fragment)
        if len(docs) != 1:
            raise ValueError('instrução documental sem um único documento')
        calls[match['id']]['documents'].extend(docs)
    for call in calls.values():
        urls = [d['url'] for d in call['documents']]
        if not urls or len(urls) != len(set(urls)):
            raise ValueError('documentos ausentes ou repetidos na seleção')
    return list(calls.values())
