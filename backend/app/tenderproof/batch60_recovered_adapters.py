"""EPL/APTA/SHDIAS contracts from preserved 2026-09-08 public pages."""
from __future__ import annotations

import base64
import hashlib
import re
from urllib.parse import parse_qs, quote, unquote, urlsplit

from bs4 import BeautifulSoup

from app.tenderproof.contracts import DocumentCandidate
from app.tenderproof.pilot_adapters import PilotHTMLAdapter, document_kind, folded, visible_soup
from app.tenderproof.source_adapter_base import SourcePageBlocked
from app.tenderproof.validation import title_is_corroborated

BROWSER_UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'


def normalized_html(html):
    # SHDIAS contains prematurely closed html/body in an embedded description.
    # html.parser preserves the following publication nodes; unwrap only the
    # document scaffolding, then apply the shared visibility rules unchanged.
    soup = BeautifulSoup(html, 'html.parser')
    for node in list(soup.select('script, style, template, noscript')):
        if node.parent is not None:
            node.decompose()
    for node in list(soup.select('html, head, body')):
        node.unwrap()
    return str(soup)


class RecoveredAdapter(PilotHTMLAdapter):
    detail_pattern = r'/concursos/publicacoes/[^/]+/(\d+)/?'
    document_identity_pattern = r'/concursos/publicacoes/[^/]+/(\d+)/?'
    candidate_selector = 'a[href*="/concursos/publicacoes/"]'
    ready_selectors = ('a[href*="/concursos/publicacoes/"]',)
    listing_query_keys = ()
    document_hosts = ('cdn-arquivo.concursos.srv.br', 'www.dropbox.com')
    identity_selector = 'h1, h2'

    def request_headers(self, url):
        return {'User-Agent': BROWSER_UA} if urlsplit(url).hostname == self.portal_host else {}

    def parse_listing(self, html, url, limit=200):
        if len(html.encode('utf8')) > 2 * 1024 * 1024:
            raise ValueError('listagem excede 2 MiB')
        normalized = normalized_html(html)
        if 'navegador incompativel' in folded(visible_soup(normalized).get_text(' ', strip=True)):
            raise SourcePageBlocked('portal exige navegador compatível; não é vazio')
        return super().parse_listing(normalized, url, limit)

    def confirm_identity(self, candidate, html, url):
        soup = self._check_detail(candidate, normalized_html(html), url)
        heading = ' '.join(n.get_text(' ', strip=True) for n in soup.select(self.identity_selector))
        if not candidate.title_observed or not title_is_corroborated(candidate.title_observed, heading):
            raise ValueError('título do concurso incompatível com detalhe')
        # A process-scoped CDN document is required even where additional
        # externally hosted publications are linked on the same official page.
        if not any(urlsplit(d.url_requested).hostname == self.document_hosts[0] for d in self.documents(html, candidate)):
            raise ValueError('detalhe sem documento vinculado ao processo')

    def process_id(self, candidate):
        return candidate.external_id.zfill(5)

    def document_route(self, parts):
        return parts.path.startswith('/' + self.tenant + '/') or (parts.hostname == 'www.dropbox.com' and parts.path.startswith('/scl/fi/'))

    def validate_document_url(self, url, candidate):
        self._check_candidate(candidate)
        p = self._destination(url)
        if p.hostname == 'www.dropbox.com':
            q = parse_qs(p.query, keep_blank_values=True)
            if not re.fullmatch(r'/scl/fi/[A-Za-z0-9]+/[^/]+\.pdf', p.path, re.I) or set(q) != {'rlkey', 'dl', 'raw'} or any(len(v) != 1 for v in q.values()) or q['dl'] != ['0'] or q['raw'] != ['1'] or not re.fullmatch(r'[A-Za-z0-9]+', q['rlkey'][0]):
                raise ValueError('link externo fora do contrato observado')
            return
        expected = '/' + self.tenant + '/' + self.process_id(candidate) + '/' + self.document_directory + '/'
        if p.hostname != self.document_hosts[0] or p.query or not unquote(p.path).startswith(expected) or not re.fullmatch(re.escape(expected) + r'[^/]+\.pdf', unquote(p.path), re.I):
            raise ValueError('documento de outro processo ou tenant')

    def documents(self, html, candidate):
        return super().documents(normalized_html(html), candidate)

    def choose_document(self, docs):
        # Dropbox file IDs do not encode process identity; only process-bound
        # CDN originals can be automatically selected for extraction.
        chosen = super().choose_document(docs)
        if urlsplit(chosen.url_requested).hostname != self.document_hosts[0]:
            raise ValueError('documento externo exige revisão de identidade')
        return chosen


class EPLAdapter(RecoveredAdapter):
    tenant = 'EPL_CONCURSOS'
    document_directory = 'PUBLICAÇÕES'

    def __init__(self):
        super().__init__('epl_open', 'https://www.eplconcursos.com.br/concursos/andamento', listing_paths=('/concursos/andamento',), document_hosts=self.document_hosts)

    def _title(self, anchor):
        card = anchor.find_parent(class_='thumbnail')
        heading = card.select_one('h3') if card else None
        return re.sub(r'/[A-Z]{2}\s*$', '', heading.get_text(' ', strip=True)).strip() if heading else None

    def documents(self, html, candidate):
        self._check_candidate(candidate)
        soup = visible_soup(normalized_html(html))
        docs, seen = [], set()
        for row in soup.select('tr[onclick]'):
            match = re.fullmatch(r"nova_pagina\('([^']+)'\)\s*;?", row['onclick'])
            cells = row.select('td')
            if not match or not cells:
                continue
            p = urlsplit(match[1])
            if not p.path.lower().endswith('.pdf'):
                continue
            url = p._replace(path=quote(unquote(p.path), safe='/'), fragment='').geturl()
            self.validate_document_url(url, candidate)
            if url in seen:
                continue
            seen.add(url)
            title = cells[0].get_text(' ', strip=True)
            label = re.sub(r'^\d+\s*-\s*', '', title)
            docs.append(DocumentCandidate(doc_id='epl_open-doc-' + hashlib.sha256(url.encode()).hexdigest()[:16], title=title, url_requested=url, kind=document_kind(label, url)))
        return docs


class APTAAdapter(RecoveredAdapter):
    tenant = 'APTA'
    document_directory = 'PUBLICACOES'

    def __init__(self):
        super().__init__('apta_open', 'https://www.aptaconcursos.com.br', document_hosts=self.document_hosts)

    def _title(self, anchor):
        row = anchor.find_parent(class_='schedule-item')
        heading = row.select_one('h4') if row else None
        return re.sub(r'\s*-\s*[A-Z]{2}\s*$', '', heading.get_text(' ', strip=True)).strip() if heading else None

    def _scope_title(self, anchor):
        row = anchor.find_parent(class_='schedule-item')
        return row.get_text(' ', strip=True) if row else ''

    def _document_title(self, anchor):
        row = anchor.find_parent(class_='row')
        heading = row.select_one('h5.mb-2') if row else None
        return heading.get_text(' ', strip=True) if heading else ''


class SHDIASAdapter(RecoveredAdapter):
    tenant = 'SHDIAS'
    document_directory = 'PUBLICACOES'
    detail_pattern = r'/concursos/publicacoes/([A-Za-z0-9=]+/[A-Za-z0-9=]+)/?'
    document_identity_pattern = detail_pattern
    identity_selector = '.concurso-name, .concurso-descricao'

    def __init__(self):
        super().__init__('shdias_open', 'https://www.shdias.com.br/concursos/index/?status=andamento&busca=', document_hosts=self.document_hosts)

    def validate_listing_url(self, url):
        p = self._destination(url)
        if p.hostname != self.portal_host or p.path != '/concursos/index/' or parse_qs(p.query, keep_blank_values=True) != {'status': ['andamento'], 'busca': ['']}:
            raise ValueError('listagem SHDIAS fora do filtro observado')

    def candidate_from_url(self, url, title=None):
        candidate = super().candidate_from_url(url, title)
        self.process_id(candidate)
        return candidate

    def process_id(self, candidate):
        try:
            tokens = [base64.b64decode(t, validate=True).decode('ascii') for t in candidate.external_id.split('/')]
        except (ValueError, UnicodeError):
            raise ValueError('identidade SHDIAS codificada inválida') from None
        if len(tokens) != 2 or any(not re.fullmatch(r'\d{1,8}', t) for t in tokens):
            raise ValueError('identidade SHDIAS inválida')
        return tokens[1].zfill(5)

    def _title(self, anchor):
        card = anchor.find_parent(class_='overlayed-item')
        return ' '.join(n.get_text(' ', strip=True) for n in card.select('.concurso-name, .concurso-descricao')) if card else None

    def _document_title(self, anchor):
        for parent in anchor.parents:
            heading = parent.select_one('h6')
            if heading:
                return re.sub(r'^\d+\s*-\s*', '', heading.get_text(' ', strip=True))
        return ''


BATCH60_RECOVERED_ADAPTERS = {adapter.source: adapter for adapter in (EPLAdapter(), APTAAdapter(), SHDIASAdapter())}
