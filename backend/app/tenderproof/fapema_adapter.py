"""FAPEMA continuous discovery and document acquisition with explicit review gaps."""
import hashlib,json
from datetime import datetime,timezone
from app.tenderproof.contracts import DiscoveredCandidate,DocumentCandidate
from app.tenderproof.fapema_listing import HOST,listing_url,detail_url,discover_categories,parse_listing
from app.tenderproof.fapema_detail import parse_detail,document_url
from app.tenderproof.source_adapter_base import HTMLSourceAdapter,ListingPage


def exact(expected):
    def validate(target):
        if target!=expected:raise ValueError('redirecionamento altera identidade FAPEMA')
    return validate


class FapemaAdapter(HTMLSourceAdapter):
    source='fapema_selection'
    listing_urls=(HOST+'/inicio/',)
    allowed_hosts=('www.fapema.br',)
    ready_selectors=('.search-results','article#main')
    observed_url_paths=()
    document_identity_pattern=r'(?!)'
    implementation_state='partial'
    implementation_scope='Menu, categorias paginadas e documentos PDF.js; links indisponíveis, avisos HTML e publicação pendentes.'

    def validate_listing_url(self,url):
        if url!=self.listing_urls[0]:listing_url(url)

    def acquire_listing(self,url,fetch):
        self.validate_listing_url(url);root=self.listing_urls[0]
        response=fetch(root,exact(root),2*1024*1024);exact(root)(response.url_final)
        menu=response.content.decode('utf-8-sig');categories=discover_categories(menu);body=menu
        if url!=root:
            category,_=listing_url(url)
            if HOST+'/category/editais/'+category+'/' not in categories:
                raise ValueError('categoria ausente do menu atual FAPEMA')
            response=fetch(url,exact(url),2*1024*1024);exact(url)(response.url_final)
            body=response.content.decode('utf-8-sig')
        return json.dumps({'format':'fapema-listing/1','url':url,'menu':menu,'html':body},ensure_ascii=False)

    def parse_listing(self,html,url,limit=200):
        self.validate_listing_url(url)
        if type(limit) is not int or not 1<=limit<=10000:raise ValueError('limite inválido')
        data=json.loads(html)
        if data.get('format')!='fapema-listing/1' or data.get('url')!=url:raise ValueError('prova de listagem divergente')
        categories=discover_categories(data['menu'])
        if url==self.listing_urls[0]:return ListingPage(next_urls=categories)
        category,_=listing_url(url)
        if HOST+'/category/editais/'+category+'/' not in categories:raise ValueError('categoria sem vínculo com menu')
        parsed=parse_listing(data['html'],url);truncated=len(parsed['items'])>limit
        return ListingPage(candidates=[self.candidate_from_url(x['url'],x['title']) for x in parsed['items'][:limit]],
            next_urls=parsed['next_urls'],truncated=truncated,diagnostics=parsed['diagnostics'],
            terminal_evidence='Página corrente final confirmada pelo paginador.' if parsed['terminal'] and not truncated else None)

    def validate_detail_url(self,url):detail_url(url)

    def candidate_from_url(self,url,title=None):
        identity=detail_url(url)
        return DiscoveredCandidate(candidate_id='fapema-'+hashlib.sha256(identity.encode()).hexdigest()[:24],source=self.source,
            external_id=identity,detail_url_observed=url,title_observed=title,observed_at=datetime.now(timezone.utc))

    def _candidate(self,candidate,url):
        if candidate.source!=self.source or candidate.external_id!=detail_url(url) or candidate.detail_url_observed!=url:
            raise ValueError('candidato FAPEMA divergente')

    def confirm_identity(self,candidate,html,url):
        self._candidate(candidate,url);parse_detail(html,url)

    def documents(self,html,candidate):
        self._candidate(candidate,candidate.detail_url_observed)
        parsed=parse_detail(html,candidate.detail_url_observed)
        if parsed['pending_links']:raise ValueError('manifesto FAPEMA com links complementares pendentes')
        if parsed['html_effect_review_required']:raise ValueError('aviso HTML FAPEMA exige revisão de efeito antes da seleção documental')
        grouped={}
        for row in parsed['documents']:grouped.setdefault(row['url'],[]).append(row)
        result=[]
        for url,rows in grouped.items():
            if len({r['kind'] for r in rows})!=1:raise ValueError('papéis documentais conflitantes')
            result.append(DocumentCandidate(doc_id='fapema-'+hashlib.sha256((candidate.external_id+':'+url).encode()).hexdigest()[:24],
                title=' / '.join(dict.fromkeys(r['title'] for r in rows)),kind=rows[0]['kind'],url_requested=url,
                reason_chosen='Arquivo observado no corpo canônico; modalidade e efeito documental exigem conferência.'))
        return result

    def validate_document_url(self,url,candidate):
        self._candidate(candidate,candidate.detail_url_observed);document_url(url)

    def choose_document(self,docs):
        originals=[d for d in docs if d.kind=='edital']
        if len(originals)!=1:raise ValueError('original FAPEMA ausente ou ambíguo')
        return originals[0]
