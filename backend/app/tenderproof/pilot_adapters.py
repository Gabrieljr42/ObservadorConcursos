"""Observed pilot families (2026-09-07), with conservative identity and coverage.

Configuration identifies eight implemented adapters, not eight homologations.
Raw official captures and limitations live in tests/fixtures/tenderproof_pilot.
"""
from __future__ import annotations

import hashlib
import re
import unicodedata
from datetime import datetime, timezone
from urllib.parse import parse_qs, unquote, urljoin, urlsplit, urlunsplit

from bs4 import BeautifulSoup

from app.tenderproof.contracts import DiscoveredCandidate, DocumentCandidate
from app.tenderproof.security import validate_destination, DestinationBlocked
from app.tenderproof.source_adapter_base import HTMLSourceAdapter, SourcePageBlocked
from app.tenderproof.validation import title_is_corroborated


def folded(value):
    return unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode().casefold()


def visible_soup(html):
    soup = BeautifulSoup(html, 'lxml')
    for node in list(soup.select('script, style, template, noscript, [hidden], [aria-hidden=true], .hidden, .d-none')):
        if node.parent is not None:
            node.decompose()
    for node in list(soup.select('[style]')):
        if node.attrs and re.search(r'display\s*:\s*none|visibility\s*:\s*hidden', node['style'], re.I):
            node.decompose()
    text = folded(soup.get_text(' ', strip=True))
    if any(marker in text for marker in ('verify you are human', 'just a moment', 'checking your browser', 'access denied', 'enable javascript and cookies', 'verifique que voce e humano')):
        raise SourcePageBlocked('página bloqueada por challenge; não é vazio legítimo')
    return soup


def document_kind(title, url):
    from app.tenderproof.document_labels import publication_label, individual_administrative_act
    # URL may corroborate exclusion, never promote an unlabeled file to edital.
    text = folded(title)
    combined = text + ' ' + folded(unquote(url))
    # Explicit publication labels enter the document-effects review gate.
    # A filename alone cannot establish the nature of an update.
    # The source may put a numbered publication prefix before its actual type.
    # Only consume this prefix; words in the middle of an opening title do not
    # establish an update or an individual administrative act.
    update_label = publication_label(title)
    if re.match(r'^(?:retificacao|errata)\b', update_label):
        return 'retificacao'
    if re.match(r'^prorrogacao\b', update_label):
        return 'prorrogacao'
    if re.match(r'^(?:ampliacao|reducao)\s+(?:do numero\s+)?de vagas\b', update_label):
        return 'retificacao'
    if individual_administrative_act(title):
        return 'outro'
    if 'gabarito' in combined:
        return 'gabarito'
    if 'resultado' in combined:
        return 'resultado'
    if re.search(r'\banexo\s+[ivx\d]', text):
        return 'anexo'
    excluded = ('retific', 'errata', 'convoca', 'homologa', 'recurso', 'impugna', 'cronograma', 'manual', 'privacidade', 'politica', 'cookie', 'termos', 'historico', 'isen', 'comunicado', 'julgamento', 'bolsa', 'bolsista', 'vestibular', 'classific', 'preliminar', 'definitiv', 'decisao', 'cumprimento', 'deferid', 'indeferid', 'suspens', 'cancel', 'adiamento')
    if any(term in combined for term in excluded):
        return 'outro'
    if re.match(r'^edital\b', text):
        return 'edital'
    return 'outro'


class PilotHTMLAdapter(HTMLSourceAdapter):
    """Only observed links are navigated; no inferred pagination endpoints."""
    empty_patterns = ()  # No reliable empty markers observed in these captures.
    observed_url_paths = ()
    listing_query_keys = ('page',)

    def __init__(self, source, listing_url, *, listing_paths=None, document_hosts=()):
        self.source = source
        self.listing_urls = (listing_url,)
        self.portal_host = urlsplit(listing_url).hostname
        self.allowed_hosts = (self.portal_host, *document_hosts)
        self.listing_paths = listing_paths or (urlsplit(listing_url).path,)

    def _host_in_contract(self, host):
        return host in self.allowed_hosts

    def _destination(self, url):
        validate_destination(url, allowlist=self.allowed_hosts)
        p = urlsplit(url)
        decoded = unquote(p.path)
        if p.scheme != 'https' or p.port not in (None,443) or not self._host_in_contract(p.hostname) or p.fragment or re.search(r'%2f|%5c|%25', p.path, re.I) or '\\' in decoded or any(s in ('.', '..') for s in decoded.split('/')):
            raise ValueError('destino fora do contrato da fonte')
        return p

    def validate_listing_url(self, url):
        p = self._destination(url)
        query = parse_qs(p.query, keep_blank_values=True)
        if p.hostname != self.portal_host or p.path not in self.listing_paths or any(k not in self.listing_query_keys for k in query) or any(len(v) != 1 or not re.fullmatch(r'\d{1,5}', v[0]) for v in query.values()):
            raise ValueError('URL fora das listagens observadas da fonte')

    def validate_detail_url(self, url):
        p = self._destination(url)
        if p.hostname != self.portal_host or p.query or not re.fullmatch(self.detail_pattern, p.path):
            raise ValueError('identidade de URL de detalhe inválida')

    def candidate_from_url(self, url, title=None):
        self.validate_detail_url(url)
        external = re.fullmatch(self.detail_pattern, urlsplit(url).path)[1]
        return DiscoveredCandidate(candidate_id=f'{self.source}-{external}', external_id=external,
            source=self.source, title_observed=title, detail_url_observed=url, observed_at=datetime.now(timezone.utc))

    def _candidates(self, html, url, limit):
        soup = visible_soup(html)
        result, seen = [], set()
        for a in soup.select(self.candidate_selector):
            p = urlsplit(urljoin(url, a['href']))
            target = urlunsplit((p.scheme, p.netloc, p.path, p.query, ''))
            try:
                candidate = self.candidate_from_url(target, self._title(a))
            except (ValueError, DestinationBlocked):
                continue
            if candidate.external_id in seen or not self.in_scope(self._scope_title(a) or '', target):
                continue
            seen.add(candidate.external_id)
            result.append(candidate)
            if len(result) >= limit:
                break
        return result

    def parse_listing(self, html, url, limit=200):
        # The shared engine checks bytes, truncation, pagination and empty state.
        visible_soup(html)
        return super().parse_listing(html, url, limit)

    def _scope_title(self, anchor):
        return self._title(anchor)

    def choose_document(self, docs):
        chosen = super().choose_document(docs)
        if 'consolidad' in folded(chosen.title):
            raise ValueError('edital consolidado exige revisão dos efeitos das alterações')
        return chosen

    def in_scope(self, title, url):
        return not any(t in folded(title) for t in ('vestibular', 'bolsista', 'bolsa de', 'exame de qualificacao', 'residencia medica'))

    def _check_candidate(self, candidate):
        expected = self.candidate_from_url(candidate.detail_url_observed)
        if candidate.source != self.source or candidate.external_id != expected.external_id:
            raise ValueError('fonte ou identidade do candidato incompatível')

    def _check_detail(self, candidate, html, url):
        self._check_candidate(candidate)
        self.validate_detail_url(url)
        if self.candidate_from_url(url).external_id != candidate.external_id:
            raise ValueError('identidade do detalhe incompatível com candidato')
        return visible_soup(html)

    def documents(self, html, candidate):
        self._check_candidate(candidate)
        soup = visible_soup(html)
        docs, seen = [], set()
        for a in soup.select('a[href]'):
            url = urljoin(candidate.detail_url_observed, a['href'])
            p = urlsplit(url)
            if p.hostname not in self.document_hosts or not ('.pdf' in p.path.casefold() or '.pdf' in p.query.casefold()):
                continue
            # Only document directories are included; generic privacy PDFs are excluded.
            if not self.document_route(p):
                continue
            self.validate_document_url(url, candidate)
            if url in seen:
                continue
            seen.add(url)
            title = self._document_title(a)
            docs.append(DocumentCandidate(doc_id=f'{self.source}-doc-{hashlib.sha256(url.encode()).hexdigest()[:16]}',
                title=title[:300], url_requested=url, kind=document_kind(title, url)))
        return docs

    def _document_title(self, anchor):
        return ' '.join(anchor.get_text(' ', strip=True).split())


class SelecaoNetAdapter(PilotHTMLAdapter):
    detail_pattern = r'/informacoes/(\d+)/?'
    document_identity_pattern = r'/informacoes/(\d+)/?'
    candidate_selector = 'h3 a[href]'
    ready_selectors = ('h3 a[href*="/informacoes/"]',)
    listing_query_keys = ()
    document_hosts = ('anexos-r2.selecao.net.br', 'anexos.cdn.selecao.net.br')

    def __init__(self, source, host, tenant, tabs):
        super().__init__(source, f'https://{host}/index/abertos/', listing_paths=tuple(f'/index/{s}/' for s in tabs), document_hosts=self.document_hosts)
        self.tenant = tenant

    def _title(self, anchor):
        return anchor.get_text(' ', strip=True)

    def document_route(self, p):
        return p.path.startswith('/uploads/')

    def validate_document_url(self, url, candidate):
        self._check_candidate(candidate)
        p = self._destination(url)
        if p.hostname not in self.document_hosts or p.query or not re.fullmatch(rf'/uploads/{self.tenant}/concursos/{re.escape(candidate.external_id)}/anexos/[A-Za-z0-9_.-]+\.pdf', p.path):
            raise ValueError('documento pertence a outro concurso ou tenant da plataforma')

    def confirm_identity(self, candidate, html, url):
        soup = self._check_detail(candidate, html, url)
        if not self.documents(html, candidate):
            raise ValueError('identidade sem documento vinculado ao ID e tenant')
        if candidate.title_observed and not title_is_corroborated(candidate.title_observed, ' '.join(h.get_text(' ',strip=True) for h in soup.select('.dados h2, h1'))):
            raise ValueError('título do detalhe incompatível com candidato')


class EditalVerAdapter(PilotHTMLAdapter):
    detail_pattern = r'/edital/ver/(\d+)/?'
    document_identity_pattern = r'/edital/ver/(\d+)/?'
    candidate_selector = 'a.detalhes-edital[href]'
    ready_selectors = ('a.detalhes-edital[href*="/edital/ver/"]',)
    listing_query_keys = ()

    def __init__(self, source, host, doc_host, *, bucket='', arquivo=False):
        self.document_hosts = (doc_host, 's3.sa-east-1.amazonaws.com') if arquivo else (doc_host,)
        self.bucket, self.arquivo = bucket, arquivo
        super().__init__(source, f'https://{host}/edital', document_hosts=self.document_hosts)

    def _title(self, anchor):
        row = anchor.find_parent(class_='row')
        paragraphs = row.select('p') if row else []
        return paragraphs[1].get_text(' ', strip=True) if len(paragraphs)>1 else None

    def _scope_title(self, anchor):
        row = anchor.find_parent(class_='row')
        return row.get_text(' ', strip=True) if row else ''

    def document_route(self, p):
        return p.path == '/arquivo.php' if self.arquivo else p.path.startswith(f'{self.bucket}/edital/')

    def validate_document_url(self, url, candidate):
        self._check_candidate(candidate)
        p = self._destination(url)
        path = p.path
        if self.arquivo and p.hostname == 's3.sa-east-1.amazonaws.com':
            query = parse_qs(p.query, keep_blank_values=True)
            keys = {'X-Amz-Content-Sha256','X-Amz-Algorithm','X-Amz-Credential','X-Amz-Date','X-Amz-SignedHeaders','X-Amz-Expires','X-Amz-Signature'}
            if set(query) - keys or any(len(v) != 1 for v in query.values()) or not re.fullmatch(rf'/cdn-ibade\.selecao\.site/edital/\d+/{re.escape(candidate.external_id)}/[A-Za-z0-9_.-]+\.pdf', path):
                raise ValueError('documento pertence a outro concurso ou bucket')
            return
        if self.arquivo:
            query = parse_qs(p.query, keep_blank_values=True)
            if p.path != '/arquivo.php' or set(query) != {'file'} or len(query['file']) != 1:
                raise ValueError('rota documental inválida')
            path = '/' + query['file'][0]
        elif p.query:
            raise ValueError('query documental não observada')
        if p.hostname not in self.document_hosts or not re.fullmatch(rf'{re.escape(self.bucket)}/edital/\d+/{re.escape(candidate.external_id)}/[A-Za-z0-9_.-]+\.pdf', path):
            raise ValueError('documento pertence a outro concurso ou bucket')

    def _document_title(self, anchor):
        row = anchor.find_parent(class_='row')
        label = row.select_one('p') if row else None
        return label.get_text(' ', strip=True) if label else super()._document_title(anchor)

    def confirm_identity(self, candidate, html, url):
        soup = self._check_detail(candidate, html, url)
        if not self.documents(html, candidate):
            raise ValueError('identidade sem vínculo documental verificável')
        title = ' '.join(p.get_text(' ',strip=True) for p in soup.select('p.text-16'))
        if candidate.title_observed and not title_is_corroborated(candidate.title_observed, title):
            raise ValueError('título do detalhe incompatível com candidato')


class FGVAdapter(PilotHTMLAdapter):
    source = 'fgv_open'
    detail_pattern = r'/concursos/([a-z0-9][a-z0-9.-]+)/?'
    document_identity_pattern = r'conhecimento\.fgv\.br/concursos/([a-z0-9][a-z0-9.-]+)'
    candidate_selector = '.views-field-title a[href]'
    ready_selectors = ('.views-field-title a[href]',)
    document_hosts = ('conhecimento.fgv.br',)

    def __init__(self):
        super().__init__(self.source, 'https://conhecimento.fgv.br/concursos')

    def _title(self, anchor):
        return anchor.get_text(' ', strip=True)

    def in_scope(self, title, url):
        return super().in_scope(title, url) and bool(re.search(r'concurso publico|processo seletivo simplificado', folded(title)))

    def document_route(self, p):
        return p.path.startswith('/sites/default/files/concursos/')

    def validate_document_url(self, url, candidate):
        self._check_candidate(candidate)
        p = self._destination(url)
        if p.hostname not in self.document_hosts or p.query or not self.document_route(p) or not p.path.casefold().endswith('.pdf'):
            raise ValueError('destino documental fora do diretório oficial')

    def confirm_identity(self, candidate, html, url):
        soup = self._check_detail(candidate, html, url)
        canonical = soup.select_one('link[rel=canonical]')
        if canonical is not None and canonical.get('href') != url:
            raise ValueError('identidade canônica do detalhe incompatível')
        headings = ' '.join(h.get_text(' ',strip=True) for h in soup.select('h1'))
        if not candidate.title_observed or not title_is_corroborated(candidate.title_observed, headings):
            raise ValueError('identidade exige título do candidato corroborado no detalhe')


class FuncernAdapter(FGVAdapter):
    source = 'funcern_selection'
    detail_pattern = r'/concursos/([a-z0-9][a-z0-9-]+)/'
    document_identity_pattern = r'funcern\.br/concursos/([a-z0-9][a-z0-9-]+)'
    candidate_selector = 'article a[href]'
    ready_selectors = ('article a[href*="/concursos/"]',)
    document_hosts = ('funcern.br', 'nyc3.digitaloceanspaces.com')

    def __init__(self):
        PilotHTMLAdapter.__init__(self, self.source, 'https://funcern.br/concursos/', document_hosts=('nyc3.digitaloceanspaces.com',))

    def _title(self, anchor):
        article = anchor.find_parent('article')
        heading = article.select_one('h3') if article else None
        return heading.get_text(' ',strip=True) if heading else None

    def in_scope(self, title, url):
        text = folded(title + ' ' + url)
        # Institutional inventory includes admissions/scholarships. Only clearly
        # personnel recruitment is admitted; unknown modalities stay outside.
        return super().in_scope(title, url) and not any(t in text for t in ('bolsa', 'bolsista', 'proitec', 'integrado', 'vestibular', 'ingresso', 'fomento'))

    def confirm_identity(self, candidate, html, url):
        soup = self._check_detail(candidate, html, url)
        canonical = soup.select_one('link[rel=canonical]')
        if canonical is not None:
            cp = urlsplit(canonical.get('href', ''))
            # Actual 2026-09-07 page advertises localhost. Never navigate it.
            # Tolerate only this observed template defect with exactly the same
            # path; official response URL + h1 + PDF text remain mandatory.
            if canonical.get('href') != url and not (cp.scheme == 'http' and cp.netloc == 'localhost' and cp.path == urlsplit(url).path and not cp.query and not cp.fragment):
                raise ValueError('identidade canônica do detalhe incompatível')
        title = ' '.join(h.get_text(' ',strip=True) for h in soup.select('h1'))
        if not candidate.title_observed or not title_is_corroborated(candidate.title_observed, title):
            raise ValueError('identidade exige título do candidato corroborado no detalhe')

    def validate_document_url(self, url, candidate):
        p = self._destination(url)
        if p.hostname == 'nyc3.digitaloceanspaces.com':
            self._check_candidate(candidate)
            # Observed official redirect, exact tenant namespace, no generic
            # Spaces access. Corroborate distinctive slug tokens in the file.
            words = [w for w in candidate.external_id.split('-') if len(w)>3 and w not in ('concurso','publico','seletivo','processo') and not w.isdigit()]
            filename = folded(unquote(p.path.rsplit('/',1)[-1]))
            if p.query or not p.path.startswith('/repo/funcern.br/media/documents/') or not p.path.endswith('.pdf') or not words or not all(w in filename for w in words):
                raise ValueError('documento pertence a outro concurso ou tenant FUNCERN')
            return
        return super().validate_document_url(url, candidate)

    def document_route(self, p):
        return bool(re.match(r'/documents/\d+/', p.path))


PILOT_ADAPTERS = (
    SelecaoNetAdapter('access_open', 'access.selecao.net.br', '422', ('abertos','1','3','7')),
    SelecaoNetAdapter('abcp_open', 'abcp.selecao.net.br', '567', ('abertos','1','2','3','4','5')),
    SelecaoNetAdapter('avancasp_open', 'avancasp.selecao.net.br', '301', ('abertos','1','2','3','4','5')),
    EditalVerAdapter('ibade_open', 'portal.ibade.selecao.site', 'ibade.selecao.site', arquivo=True),
    EditalVerAdapter('fenix_open', 'portal.fenix.selecao.site', 'cdn-fenix.selecao.site'),
    EditalVerAdapter('legalle_open', 'portal.editais.legalleconcursos.com.br', 's3.sa-east-1.amazonaws.com', bucket='/cdn.legalle.com.br'),
    FGVAdapter(), FuncernAdapter(),
)
