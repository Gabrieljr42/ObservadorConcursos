"""Individually observed contracts; captures do not establish full coverage."""
import re
import hashlib
from urllib.parse import parse_qs, urlsplit, urlunsplit, urljoin
from bs4 import BeautifulSoup

from app.tenderproof.pilot_adapters import PilotHTMLAdapter, folded, visible_soup, document_kind
from app.tenderproof.contracts import DocumentCandidate
from app.tenderproof.validation import title_is_corroborated


class PubliconsultAdapter(PilotHTMLAdapter):
    source = 'publiconsult_open'
    detail_pattern = r'/Concurso/Detail/(\d+)'
    document_identity_pattern = r'/Concurso/Detail/(\d+)'
    candidate_selector = '.panel a[href*="/Concurso/Detail/"]'
    ready_selectors = ('.panel a[href*="/Concurso/Detail/"]',)
    listing_query_keys = ()
    document_hosts = ('gsistbucket.s3.amazonaws.com',)

    def __init__(self):
        super().__init__(self.source, 'https://publiconsult.com.br/Concurso/Index',
                         document_hosts=self.document_hosts)

    def validate_detail_url(self, url):
        parts = self._destination(url)
        query = parse_qs(parts.query, keep_blank_values=True)
        if (parts.hostname != self.portal_host or not re.fullmatch(self.detail_pattern, parts.path)
                or query not in ({}, {'origem': ['H']})):
            raise ValueError('detalhe Publiconsult fora da rota observada')

    def _title(self, anchor):
        panel = anchor.find_parent(class_='panel')
        heading = panel.select_one('.panel-heading p') if panel else None
        return heading.get_text(' ', strip=True) if heading else None

    def parse_listing(self, html, url, limit=200):
        # Official source ships complete tab panels, then explicitly initializes
        # and shows this one container on DOM ready. Other hidden nodes retain
        # the common conservative treatment; no unseen endpoint is synthesized.
        soup = BeautifulSoup(html, 'lxml')
        scripts = '\n'.join(node.get_text() for node in soup.select('script'))
        tabs = soup.select_one('#tabs')
        if (tabs is not None
                and re.search(r'\$\([\'"]#tabs[\'"]\)\.tabs\(\)', scripts)
                and re.search(r'\$\([\'"]#tabs[\'"]\)\.show\(\)', scripts)):
            tabs['style'] = re.sub(r'display\s*:\s*none\s*;?', '', tabs.get('style', ''), flags=re.I)
        return super().parse_listing(str(soup), url, limit)

    def in_scope(self, title, url):
        return super().in_scope(title, url) and bool(re.search(
            r'concurso publico|processo seletivo', folded(title)))

    def document_route(self, parts):
        return parts.path.startswith('/publiconsult/Anexos/')

    def validate_document_url(self, url, candidate):
        self._check_candidate(candidate)
        parts = self._destination(url)
        query = parse_qs(parts.query, keep_blank_values=True)
        # Names observed in official links, values are not recorded in fixtures.
        keys = {'AWSAccessKeyId', 'Expires', 'Signature', 'raw'}
        if (parts.hostname not in self.document_hosts
                or not re.fullmatch(rf'/publiconsult/Anexos/{re.escape(candidate.external_id)}/[^/]+\.pdf', parts.path, re.I)
                or set(query)-keys or any(len(values) != 1 for values in query.values())):
            raise ValueError('documento Publiconsult pertence a outro concurso ou destino')

    def _document_title(self, anchor):
        row = anchor.find_parent('tr')
        return row.get_text(' ', strip=True) if row else ''

    def documents(self, html, candidate):
        documents = super().documents(html, candidate)
        for document in documents:
            parts = urlsplit(document.url_requested)
            stable_url = urlunsplit((parts.scheme, parts.netloc, parts.path, '', ''))
            document.doc_id = f'{self.source}-doc-{hashlib.sha256(stable_url.encode()).hexdigest()[:16]}'
            if document.kind == 'edital' and not re.fullmatch(
                    r'edital de abertura(?: de inscricoes)?', folded(document.title)):
                document.kind = 'outro'
        return documents

    def confirm_identity(self, candidate, html, url):
        soup = self._check_detail(candidate, html, url)
        heading = ' '.join(node.get_text(' ', strip=True) for node in soup.select('h4'))
        if not candidate.title_observed or not title_is_corroborated(candidate.title_observed, heading):
            raise ValueError('título do detalhe Publiconsult incompatível')
        if not self.documents(html, candidate):
            raise ValueError('detalhe Publiconsult sem documentos associados')


class UFUAdapter(PilotHTMLAdapter):
    source = 'ufu_selection'
    detail_pattern = r'/servicos/Edital/cronograma/(\d+)'
    document_identity_pattern = r'/servicos/Edital/cronograma/(\d+)'
    ready_selectors = ('.edital_op[onclick]',)
    listing_query_keys = ()
    document_hosts = ('www.portalselecao.ufu.br',)

    def __init__(self):
        super().__init__(self.source, 'https://www.portalselecao.ufu.br/servicos/Edital/listar/concursos',
                         listing_paths=('/servicos/Edital/listar/concursos', '/servicos/Edital/listar/concurso_ta'))

    def in_scope(self, title, url):
        return super().in_scope(title, url) and bool(re.search(
            r'concurso (?:publico para docentes|tecnico-administrativo)|processo seletivo simplificado', folded(title)))

    def _candidates(self, html, url, limit):
        candidates, seen = [], set()
        for card in visible_soup(html).select('.edital_op[onclick]'):
            # Extract the literal destination observed on official cards. No JS
            # execution, endpoint synthesis or arbitrary onclick evaluation.
            match = re.fullmatch(r"window\.location\.href\s*=\s*['\"]([^'\"]+)['\"];?", card['onclick'].strip())
            title_node = card.select_one('.edital_op_texto h5')
            if not match or title_node is None:
                continue
            title = title_node.get_text(' ', strip=True)
            if not self.in_scope(title, match[1]):
                continue
            candidate = self.candidate_from_url(urljoin(url, match[1]), title)
            if candidate.external_id not in seen:
                seen.add(candidate.external_id)
                candidates.append(candidate)
            if len(candidates) >= limit:
                break
        return candidates

    def document_route(self, parts):
        return bool(re.fullmatch(r'/servicos/ArquivoAdministrativo/download/[a-f0-9]{32}', parts.path))

    def validate_document_url(self, url, candidate):
        self._check_candidate(candidate)
        parts = self._destination(url)
        # UFU/1843's accepted reference-only artifact is the preserved,
        # strongly pinned official cronograma HTML itself.  Permit only this
        # exact detail URL; linked administrative downloads remain governed by
        # the normal route below.
        if (candidate.external_id == '1843'
                and url.rstrip('/') == candidate.detail_url_observed.rstrip('/')):
            return
        if parts.hostname not in self.document_hosts or parts.query or not self.document_route(parts):
            raise ValueError('documento UFU fora da rota administrativa observada')

    def documents(self, html, candidate):
        self._check_candidate(candidate)
        documents, seen = [], set()
        for anchor in visible_soup(html).select('a.list-group-item[href]'):
            url = urljoin(candidate.detail_url_observed, anchor['href'])
            if not self.document_route(urlsplit(url)):
                continue
            self.validate_document_url(url, candidate)
            if url in seen:
                continue
            seen.add(url)
            for timestamp in anchor.select('.lbl_time'):
                timestamp.decompose()
            title = anchor.get_text(' ', strip=True)
            kind = document_kind(title, url)
            if kind == 'edital' and folded(title) not in ('edital de processo', 'edital de condicoes gerais', 'edital de condicoes especificas'):
                kind = 'outro'
            documents.append(DocumentCandidate(doc_id=f'{self.source}-doc-{url.rsplit("/",1)[1]}',
                title=title, kind=kind, url_requested=url))
        return documents

    def choose_document(self, documents):
        if any(folded(doc.title) in ('edital de condicoes gerais', 'edital de condicoes especificas') for doc in documents):
            raise ValueError('UFU: condições gerais e específicas exigem revisão documental conjunta')
        return super().choose_document(documents)

    def confirm_identity(self, candidate, html, url):
        soup = self._check_detail(candidate, html, url)
        heading = ' '.join(node.get_text(' ', strip=True) for node in soup.select('.well > div > b'))
        if not candidate.title_observed or not title_is_corroborated(candidate.title_observed, heading):
            raise ValueError('título do detalhe UFU incompatível')
        share = soup.select_one('.fb-share-button[data-href]')
        if share is None or self.candidate_from_url(share['data-href']).external_id != candidate.external_id:
            raise ValueError('identidade explícita do detalhe UFU incompatível')
        if not self.documents(html, candidate):
            raise ValueError('detalhe UFU sem documento administrativo observado')


BATCH30_INSTITUTIONAL_ADAPTERS = (PubliconsultAdapter(), UFUAdapter())
