"""Current FAPEAL editorial listings and original-linked document manifests."""
import hashlib
from datetime import datetime, timezone
from app.tenderproof.contracts import DiscoveredCandidate, DocumentCandidate
from app.tenderproof.fapeal_pages import LISTING, detail_url, document_url, category_url, discover_categories, parse_listing, parse_detail
from app.tenderproof.source_adapter_base import HTMLSourceAdapter, ListingPage


class FapealAdapter(HTMLSourceAdapter):
    source = 'fapeal_selection'
    listing_urls = (LISTING,)
    allowed_hosts = ('www.fapeal.br',)
    ready_selectors = ('main#main',)
    observed_url_paths = ()
    document_identity_pattern = r'(?!)'
    implementation_state = 'partial'
    implementation_scope = 'Listas editoriais e documentos locais; links complementares, cobertura histórica e publicação pendentes.'

    def validate_listing_url(self, url):
        if url != LISTING: category_url(url)

    def acquire_listing(self, url, fetch):
        import json
        self.validate_listing_url(url)
        def exact(target):
            if target != LISTING: raise ValueError('menu FAPEAL redirecionado')
        response=fetch(LISTING,exact,4*1024*1024);exact(response.url_final)
        menu=response.content.decode('utf-8-sig');categories=discover_categories(menu);body=menu
        if url != LISTING:
            base=url.split('/page/')[0].rstrip('/')+'/'
            if base not in categories:raise ValueError('categoria nao publicada no menu atual')
            def exact_page(target):
                if target != url:raise ValueError('categoria FAPEAL redirecionada')
            response=fetch(url,exact_page,4*1024*1024);exact_page(response.url_final)
            body=response.content.decode('utf-8-sig')
        return json.dumps({'format':'fapeal-listing/1','url':url,'menu':menu,'html':body},ensure_ascii=False)

    def parse_listing(self, html, url, limit=200):
        import json
        self.validate_listing_url(url)
        if type(limit) is not int or not 1 <= limit <= 10000:raise ValueError('limite invalido')
        data=json.loads(html)
        if data.get('format')!='fapeal-listing/1' or data.get('url')!=url:raise ValueError('prova FAPEAL divergente')
        categories=discover_categories(data['menu'])
        if url==LISTING:return ListingPage(next_urls=list(categories))
        if url.split('/page/')[0].rstrip('/')+'/' not in categories:raise ValueError('categoria nao publicada')
        parsed=parse_listing(data['html'],url)
        return ListingPage(candidates=[self.candidate_from_url(x['url'],x['title']) for x in parsed['items'][:limit]],
            next_urls=parsed['next_urls'],empty_evidence=parsed.get('empty_evidence'),truncated=len(parsed['items'])>limit,diagnostics=[parsed['reason']])

    def validate_detail_url(self, url):
        detail_url(url)

    def candidate_from_url(self, url, title=None):
        identity = detail_url(url)
        return DiscoveredCandidate(candidate_id='fapeal-' + hashlib.sha256(identity.encode()).hexdigest()[:24],
            source=self.source, external_id=identity, detail_url_observed=url,
            title_observed=title, observed_at=datetime.now(timezone.utc))

    def _candidate(self, candidate, url):
        if (candidate.source != self.source or candidate.external_id != detail_url(url)
                or candidate.detail_url_observed != url):
            raise ValueError('identidade do candidato FAPEAL divergente')

    def confirm_identity(self, candidate, html, url):
        self._candidate(candidate, url)
        parse_detail(html, url)

    def documents(self, html, candidate):
        self._candidate(candidate, candidate.detail_url_observed)
        parsed = parse_detail(html, candidate.detail_url_observed)
        if parsed['pending_links']:
            raise ValueError('manifesto FAPEAL com links complementares pendentes de inspeção')
        grouped = {}
        for row in parsed['documents']:
            if not row['title']:
                raise ValueError('documento FAPEAL sem rótulo')
            grouped.setdefault(row['url'], []).append(row)
        result = []
        for url, rows in grouped.items():
            if len({r['kind'] for r in rows}) != 1:
                raise ValueError('papel documental FAPEAL conflitante')
            result.append(DocumentCandidate(doc_id='fapeal-' + hashlib.sha256((candidate.external_id + ':' + url).encode()).hexdigest()[:24],
                title=' / '.join(dict.fromkeys(r['title'] for r in rows)), kind=rows[0]['kind'], url_requested=url,
                reason_chosen='Link no corpo do edital canônico; modalidade, identidade documental e efeito exigem conferência.'))
        return result

    def validate_document_url(self, url, candidate):
        self._candidate(candidate, candidate.detail_url_observed)
        document_url(url)

    def choose_document(self, docs):
        originals = [d for d in docs if d.kind == 'edital']
        if len(originals) != 1:
            raise ValueError('edital original ausente ou ambíguo FAPEAL')
        return originals[0]
