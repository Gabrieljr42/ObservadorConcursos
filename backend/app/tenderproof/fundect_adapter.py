"""Current FUNDECT editorial listings and original-linked document manifests."""
import hashlib
from datetime import datetime, timezone
from app.tenderproof.contracts import DiscoveredCandidate, DocumentCandidate
from app.tenderproof.fundect_pages import LISTING, API, HISTORY, detail_url, document_url, history_items, parse_api, parse_detail
from app.tenderproof.source_adapter_base import HTMLSourceAdapter, ListingPage


class FundectAdapter(HTMLSourceAdapter):
    source = 'fundect_selection'
    listing_urls = (LISTING,)
    allowed_hosts = ('www.fundect.ms.gov.br',)
    ready_selectors = ('main',)
    observed_url_paths = ()
    document_identity_pattern = r'(?!)'
    implementation_state = 'partial'
    implementation_scope = 'Listas editoriais e documentos locais; links complementares, cobertura histórica e publicação pendentes.'

    def validate_listing_url(self, url):
        if url != LISTING:raise ValueError('listagem FUNDECT fora do contrato')

    def acquire_listing(self, url, fetch):
        import json
        self.validate_listing_url(url)
        proof={'format':'fundect-listing/1'}
        for key,target in [('menu',LISTING),('api',API),('history',HISTORY)]:
            def exact(actual,expected=target):
                if actual != expected:raise ValueError('redirecionamento FUNDECT divergente')
            response=fetch(target,exact,4*1024*1024);exact(response.url_final)
            proof[key]=response.content.decode('utf-8-sig')
        self._proof(proof)
        return json.dumps(proof,ensure_ascii=False)

    def _proof(self, data):
        if data.get('format')!='fundect-listing/1':raise ValueError('prova FUNDECT divergente')
        if API not in data['menu'].replace('\\/','/') or HISTORY not in data['menu']:
            raise ValueError('API ou historico sem vinculo no portal')
        current=parse_api(data['api']);historical=history_items(data['history'])
        return current,historical

    def parse_listing(self, html, url, limit=200):
        import json
        self.validate_listing_url(url)
        if type(limit)is not int or not 1<=limit<=10000:raise ValueError('limite invalido')
        current,historical=self._proof(json.loads(html));items={x['url']:x['title']for x in current};items.update(historical)
        return ListingPage(candidates=[self.candidate_from_url(u,t)for u,t in list(items.items())[:limit]],
            truncated=len(items)>limit,diagnostics=['API atual e arquivo anterior descobertos; completude historica e modalidade pendentes.'])

    def acquire_detail(self,url,candidate,fetch):
        import json
        self._candidate(candidate,url)
        proof=json.loads(self.acquire_listing(LISTING,fetch));current,historical=self._proof(proof)
        if url not in {x['url']for x in current} and url not in historical:raise ValueError('chamada ausente dos indices atuais')
        if url in historical:
            def exact(actual):
                if actual != url:raise ValueError('detalhe FUNDECT redirecionado')
            response=fetch(url,exact,4*1024*1024);exact(response.url_final)
            proof['detail']=response.content.decode('utf-8-sig');proof['detail_url']=url
        return json.dumps(proof,ensure_ascii=False)

    def _parsed(self,html,url):
        import json
        data=json.loads(html);current,historical=self._proof(data)
        if url in historical:
            if data.get('detail_url')!=url:raise ValueError('detalhe FUNDECT ausente')
            return parse_detail(data['detail'],url)
        found=[x for x in current if x['url']==url]
        if len(found)!=1:raise ValueError('chamada API nao univoca')
        return found[0]

    def validate_detail_url(self, url):
        detail_url(url)

    def candidate_from_url(self, url, title=None):
        identity = detail_url(url)
        return DiscoveredCandidate(candidate_id='fundect-' + hashlib.sha256(identity.encode()).hexdigest()[:24],
            source=self.source, external_id=identity, detail_url_observed=url,
            title_observed=title, observed_at=datetime.now(timezone.utc))

    def _candidate(self, candidate, url):
        if (candidate.source != self.source or candidate.external_id != detail_url(url)
                or candidate.detail_url_observed != url):
            raise ValueError('identidade do candidato FUNDECT divergente')

    def confirm_identity(self, candidate, html, url):
        self._candidate(candidate, url)
        self._parsed(html, url)

    def documents(self, html, candidate):
        self._candidate(candidate, candidate.detail_url_observed)
        parsed = self._parsed(html, candidate.detail_url_observed)
        if parsed['pending_links']:
            raise ValueError('manifesto FUNDECT com links complementares pendentes de inspeção')
        grouped = {}
        for row in parsed['documents']:
            if not row['title']:
                raise ValueError('documento FUNDECT sem rótulo')
            grouped.setdefault(row['url'], []).append(row)
        result = []
        for url, rows in grouped.items():
            if len({r['kind'] for r in rows}) != 1:
                raise ValueError('papel documental FUNDECT conflitante')
            result.append(DocumentCandidate(doc_id='fundect-' + hashlib.sha256((candidate.external_id + ':' + url).encode()).hexdigest()[:24],
                title=' / '.join(dict.fromkeys(r['title'] for r in rows)), kind=rows[0]['kind'], url_requested=url,
                reason_chosen='Link no corpo do edital canônico; modalidade, identidade documental e efeito exigem conferência.'))
        return result

    def validate_document_url(self, url, candidate):
        self._candidate(candidate, candidate.detail_url_observed)
        document_url(url)

    def choose_document(self, docs):
        originals = [d for d in docs if d.kind == 'edital']
        if len(originals) != 1:
            raise ValueError('edital original ausente ou ambíguo FUNDECT')
        return originals[0]
