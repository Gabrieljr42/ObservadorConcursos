"""Personnel-only FAPED acquisition; document IDs are observed in accordions."""
import hashlib
import re
from datetime import datetime, timezone

from app.tenderproof.contracts import DiscoveredCandidate, DocumentCandidate
from app.tenderproof.faped_parser import LISTING, parse_personnel, validate_document
from app.tenderproof.source_adapter_base import HTMLSourceAdapter, ListingPage
from app.tenderproof.pilot_adapters import document_kind


class FapedAdapter(HTMLSourceAdapter):
    source = 'faped_selection'
    listing_urls = (LISTING,)
    allowed_hosts = ('faped.org.br',)
    ready_selectors = ('.accordion-item',)
    observed_url_paths = ()
    document_identity_pattern = r'#docfor([1-9]\d*)$'
    html_encoding = 'iso-8859-1'
    implementation_scope = 'Seção celetista; documentos vinculados ao contêiner observado. Cobertura total e publicação ainda não comprovadas.'

    def validate_listing_url(self, url):
        if url != LISTING:
            raise ValueError('listagem fora da seção celetista FAPED')

    def validate_detail_url(self, url):
        if not re.fullmatch(re.escape(LISTING) + r'#docfor[1-9]\d*', url):
            raise ValueError('detalhe sem identidade de acordeão FAPED')

    def candidate_from_url(self, url, title=None):
        self.validate_detail_url(url)
        identity = url.rsplit('#docfor', 1)[1]
        return DiscoveredCandidate(candidate_id=f'{self.source}-{identity}', source=self.source,
            external_id=identity, title_observed=title, detail_url_observed=url,
            observed_at=datetime.now(timezone.utc))

    def parse_listing(self, html, url, limit=200):
        self.validate_listing_url(url)
        if not 1 <= limit <= 10000:
            raise ValueError('limite de candidatos inválido')
        calls = parse_personnel(html)
        candidates = []
        for call in calls[:limit]:
            candidate = self.candidate_from_url(LISTING + '#docfor' + call['identity'], call['candidate_title'])
            candidate.selection_label_observed = call['title']
            candidates.append(candidate)
        return ListingPage(candidates=candidates, truncated=len(calls) > limit,
            diagnostics=['Seção celetista observada; ausência de paginação explícita não comprova cobertura total.'])

    def acquire_detail(self, url, candidate, fetch):
        self.validate_detail_url(url)
        # The fragment addresses a real DOM container, not a new server endpoint.
        response = fetch(LISTING, self.validate_listing_url, 2 * 1024 * 1024)
        if response.url_final != LISTING or len(response.content) > 2 * 1024 * 1024:
            raise ValueError('resposta de detalhe FAPED fora do contrato')
        html = response.content.decode(self.html_encoding)
        self.confirm_identity(candidate, html, url)
        return html

    def _call(self, candidate, html, url):
        expected = self.candidate_from_url(url)
        if (candidate.source != self.source or candidate.external_id != expected.external_id
                or candidate.detail_url_observed != url):
            raise ValueError('candidato incompatível com seção FAPED')
        matches = [c for c in parse_personnel(html) if c['identity'] == candidate.external_id]
        if len(matches) != 1:
            raise ValueError('seleção não encontrada no documento preservado')
        return matches[0]

    def confirm_identity(self, candidate, html, url):
        self._call(candidate, html, url)

    def document_title_corroborated(self, candidate, pages):
        from app.tenderproof.faped_fields import _TITLE, _ORG
        from app.tenderproof.validation import title_is_corroborated
        self.validate_detail_url(candidate.detail_url_observed)
        if candidate.source != self.source:
            return False
        observed = set(re.findall(r'\b\d{1,4}/\d{4}\b', candidate.title_observed or ''))
        first = [p for p in pages if p.page_number == 1 and not p.error and not p.truncated]
        if len(first) != 1 or not _ORG.search(first[0].text):
            return False
        titles = list(_TITLE.finditer(first[0].text))
        clean = re.sub(r'\s+(?:Encerrado|Aberto)\s*$', '', candidate.title_observed or '', flags=re.I)
        return (len(titles) == 1 and observed == {titles[0][1]}
                and title_is_corroborated(clean, '\n'.join(p.text for p in pages)))

    def documents(self, html, candidate):
        call = self._call(candidate, html, candidate.detail_url_observed)
        docs = []
        for row in call['documents']:
            title = row['title']
            primary = title.casefold() == 'anexo de abertura'
            kind = 'edital' if primary else document_kind(title, row['url'])
            docs.append(DocumentCandidate(doc_id='faped-' + call['identity'] + '-' + hashlib.sha256(row['url'].encode()).hexdigest()[:20],
                title=call['candidate_title'] if primary else title,
                url_requested=row['url'], kind=kind,
                reason_chosen=f"Rótulo original: {title}. Publicado em {row['published_at_local']} no contêiner docfor{call['identity']}."))
        return docs

    def validate_document_url(self, url, candidate):
        self.validate_detail_url(candidate.detail_url_observed)
        if candidate.source != self.source:
            raise ValueError('documento de outra fonte')
        validate_document(url)

    def choose_document(self, docs):
        originals = [d for d in docs if d.kind == 'edital']
        if len(originals) != 1:
            raise ValueError('edital de abertura não é único')
        return originals[0]
