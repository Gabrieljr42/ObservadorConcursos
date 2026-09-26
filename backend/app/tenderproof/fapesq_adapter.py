"""Public FAPESQ annual graph and document manifests, with explicit review gaps."""
import hashlib
import json
import re
import httpx
from datetime import datetime, timezone
from urllib.parse import urlsplit, unquote

from app.tenderproof.contracts import DiscoveredCandidate, DocumentCandidate
from app.tenderproof.fapesq_listing import HOST, annual_url, collection_url, parse_annual, parse_collection
from app.tenderproof.fapesq_detail import detail_url, parse_detail, parse_file_view
from app.tenderproof.source_adapter_base import HTMLSourceAdapter, ListingPage


def exact(expected):
    def validate(target):
        if target != expected:
            raise ValueError('redirecionamento altera identidade FAPESQ')
    return validate


class FapesqAdapter(HTMLSourceAdapter):
    source = 'fapesq_selection'
    listing_urls = (HOST + '/editais-1',)
    allowed_hosts = ('fapesq.rpp.br',)
    ready_selectors = ('#content',)
    observed_url_paths = ()
    document_identity_pattern = r'(?!)'
    implementation_state = 'partial'
    implementation_scope = 'Menu anual dinâmico e documentos públicos; classificação, links defeituosos, campos e publicação pendentes.'

    def validate_listing_url(self, url):
        if url == self.listing_urls[0]:
            return
        try:
            annual_url(url)
        except ValueError:
            collection_url(url)

    def acquire_listing(self, url, fetch):
        self.validate_listing_url(url)
        def validate(target):
            if url == self.listing_urls[0]:
                if target != url:
                    annual_url(target)
            else:
                exact(url)(target)
        response = fetch(url, validate, 2 * 1024 * 1024)
        validate(response.url_final)
        if url == self.listing_urls[0]:
            annual_url(response.url_final)
        return json.dumps({'format': 'fapesq-listing/1', 'requested': url,
            'final': response.url_final, 'html': response.content.decode('utf-8-sig')}, ensure_ascii=False)

    def parse_listing(self, html, url, limit=200):
        self.validate_listing_url(url)
        if type(limit) is not int or not 1 <= limit <= 10000:
            raise ValueError('limite de candidatos inválido')
        data = json.loads(html)
        if data.get('format') != 'fapesq-listing/1' or data.get('requested') != url:
            raise ValueError('listagem adquirida não corresponde à URL')
        final = data['final']
        if url == self.listing_urls[0]:
            annual_url(final)
        else:
            exact(url)(final)
        try:
            annual_url(final)
        except ValueError:
            parsed = parse_collection(data['html'], final)
            truncated = len(parsed['items']) > limit
            return ListingPage(
                candidates=[self.candidate_from_url(r['url'], r['title']) for r in parsed['items'][:limit]],
                next_urls=[parsed['next_url']] if parsed['next_url'] else [], truncated=truncated,
                terminal_evidence='Página atual final confirmada pelo paginador.' if parsed['terminal'] and not truncated else None,
                diagnostics=['Compatibilidade de cada seleção exige análise documental.'])
        parsed = parse_annual(data['html'], final)
        return ListingPage(next_urls=list(dict.fromkeys([parsed['collection'], *parsed['annuals']])),
            truncated=bool(parsed['unresolved_links']),
            diagnostics=['Atalho anual não resolvido: ' + u for u in parsed['unresolved_links']])

    def validate_detail_url(self, url):
        detail_url(url)

    def candidate_from_url(self, url, title=None):
        identity = detail_url(url)
        return DiscoveredCandidate(candidate_id='fapesq-' + hashlib.sha256(identity.encode()).hexdigest()[:24],
            source=self.source, external_id=identity, detail_url_observed=url,
            title_observed=title, observed_at=datetime.now(timezone.utc))

    def _candidate(self, candidate, url):
        if (candidate.source != self.source or candidate.external_id != detail_url(url)
                or candidate.detail_url_observed != url):
            raise ValueError('identidade do candidato FAPESQ divergente')

    def acquire_detail(self, url, candidate, fetch):
        self._candidate(candidate, url)
        response = fetch(url, exact(url), 2 * 1024 * 1024)
        body = response.content.decode('utf-8-sig')
        manifest = parse_detail(body, url)
        if not manifest['manifest_complete']:
            raise ValueError('manifesto FAPESQ contém endereço malformado pendente')
        pages = {}
        failures = {}
        for document in manifest['documents']:
            if document['requires_file_page']:
                target = document['url']
                try:
                    response = fetch(target, exact(target), 2 * 1024 * 1024)
                except httpx.HTTPStatusError as exc:
                    if not 400 <= exc.response.status_code < 500:
                        raise
                    failures[target] = {'status': exc.response.status_code,
                        'error': 'Página documental oficial indisponível; arquivo não adquirido.'}
                    continue
                page = response.content.decode('utf-8-sig')
                parse_file_view(page, target)
                pages[target] = page
        return json.dumps({'format': 'fapesq-detail/1', 'url': url, 'html': body,
            'file_pages': pages, 'file_page_errors': failures}, ensure_ascii=False)

    def _parsed(self, html, candidate):
        self._candidate(candidate, candidate.detail_url_observed)
        data = json.loads(html)
        if data.get('format') != 'fapesq-detail/1' or data.get('url') != candidate.detail_url_observed:
            raise ValueError('detalhe composto FAPESQ divergente')
        manifest = parse_detail(data['html'], candidate.detail_url_observed)
        if not manifest['manifest_complete']:
            raise ValueError('manifesto documental incompleto')
        required = {d['url'] for d in manifest['documents'] if d['requires_file_page']}
        failures = data.get('file_page_errors', {})
        if (set(data['file_pages']) & set(failures)
                or set(data['file_pages']) | set(failures) != required
                or any(type(r.get('status')) is not int or not 400 <= r['status'] < 500 for r in failures.values())):
            raise ValueError('páginas de arquivo não correspondem ao manifesto')
        for document in manifest['documents']:
            if document['requires_file_page']:
                if document['url'] in failures:
                    document['acquisition_error'] = failures[document['url']]
                else:
                    document['url'] = parse_file_view(data['file_pages'][document['url']], document['url'])
        return manifest

    def confirm_identity(self, candidate, html, url):
        self._candidate(candidate, url)
        self._parsed(html, candidate)

    def documents(self, html, candidate):
        return [DocumentCandidate(doc_id='fapesq-doc-' + hashlib.sha256(
            (candidate.external_id + ':' + row['href_observed']).encode()).hexdigest()[:24],
            title=row['title'] or 'Arquivo documental', kind=row['kind'], url_requested=row['url'],
            reason_chosen='Link observado no detalhe canônico; modalidade e efeito exigem conferência.'
                + (' PENDENTE: página de arquivo retornou HTTP '+str(row['acquisition_error']['status'])+'.' if row.get('acquisition_error') else ''))
            for row in self._parsed(html, candidate)['documents']]

    def validate_document_url(self, url, candidate):
        self._candidate(candidate, candidate.detail_url_observed)
        p = urlsplit(url)
        path = unquote(p.path)
        if (p.scheme != 'https' or p.netloc != 'fapesq.rpp.br' or p.query or p.fragment
                or not path.startswith('/editais/') or any(s in ('.', '..') for s in path.split('/'))
                or '\\' in path or not re.search(r'\.(?:pdf|docx?|xlsx?|zip)$', path, re.I)):
            raise ValueError('download fora do contrato documental FAPESQ')

    def choose_document(self, docs):
        originals = [d for d in docs if d.kind == 'edital']
        if len(originals) != 1:
            raise ValueError('edital original ausente ou ambíguo FAPESQ')
        return originals[0]
