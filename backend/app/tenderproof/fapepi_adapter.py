"""Current FAPEPI editorial listings and original-linked document manifests."""
import hashlib
from datetime import datetime, timezone
from app.tenderproof.contracts import DiscoveredCandidate, DocumentCandidate
from app.tenderproof.fapepi_pages import LISTING, detail_url, document_url, parse_listing, parse_detail
from app.tenderproof.source_adapter_base import HTMLSourceAdapter, ListingPage


class FapepiAdapter(HTMLSourceAdapter):
    source = 'fapepi_selection'
    listing_urls = (LISTING,)
    allowed_hosts = ('www.fapepi.pi.gov.br',)
    ready_selectors = ('ul.display-posts-listing', 'main.type-edital')
    observed_url_paths = ()
    document_identity_pattern = r'(?!)'
    implementation_state = 'partial'
    implementation_scope = 'Listas editoriais e documentos locais; links complementares, cobertura histórica e publicação pendentes.'

    def validate_listing_url(self, url):
        if url != LISTING:
            raise ValueError('listagem FAPEPI fora do contrato observado')

    def parse_listing(self, html, url, limit=200):
        self.validate_listing_url(url)
        if type(limit) is not int or not 1 <= limit <= 10000:
            raise ValueError('limite de candidatos inválido')
        parsed = parse_listing(html)
        return ListingPage(candidates=[self.candidate_from_url(x['url'], x['titles'][0]) for x in parsed['items'][:limit]],
            truncated=len(parsed['items']) > limit or bool(parsed['navigation']),
            diagnostics=[parsed['coverage_reason']] + ['Navegação pendente: ' + x['url'] for x in parsed['navigation']])

    def validate_detail_url(self, url):
        detail_url(url)

    def candidate_from_url(self, url, title=None):
        identity = detail_url(url)
        return DiscoveredCandidate(candidate_id='fapepi-' + hashlib.sha256(identity.encode()).hexdigest()[:24],
            source=self.source, external_id=identity, detail_url_observed=url,
            title_observed=title, observed_at=datetime.now(timezone.utc))

    def _candidate(self, candidate, url):
        if (candidate.source != self.source or candidate.external_id != detail_url(url)
                or candidate.detail_url_observed != url):
            raise ValueError('identidade do candidato FAPEPI divergente')

    def confirm_identity(self, candidate, html, url):
        self._candidate(candidate, url)
        parse_detail(html, url)

    def documents(self, html, candidate):
        self._candidate(candidate, candidate.detail_url_observed)
        parsed = parse_detail(html, candidate.detail_url_observed)
        if parsed['pending_links']:
            raise ValueError('manifesto FAPEPI com links complementares pendentes de inspeção')
        grouped = {}
        for row in parsed['documents']:
            if not row['title']:
                raise ValueError('documento FAPEPI sem rótulo')
            grouped.setdefault(row['url'], []).append(row)
        result = []
        for url, rows in grouped.items():
            if len({r['kind'] for r in rows}) != 1:
                raise ValueError('papel documental FAPEPI conflitante')
            result.append(DocumentCandidate(doc_id='fapepi-' + hashlib.sha256((candidate.external_id + ':' + url).encode()).hexdigest()[:24],
                title=' / '.join(dict.fromkeys(r['title'] for r in rows)), kind=rows[0]['kind'], url_requested=url,
                reason_chosen='Link no corpo do edital canônico; modalidade, identidade documental e efeito exigem conferência.'))
        return result

    def validate_document_url(self, url, candidate):
        self._candidate(candidate, candidate.detail_url_observed)
        document_url(url)

    def choose_document(self, docs):
        originals = [d for d in docs if d.kind == 'edital']
        if len(originals) != 1:
            raise ValueError('edital original ausente ou ambíguo FAPEPI')
        return originals[0]
