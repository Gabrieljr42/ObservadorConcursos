"""FAPERR publication graph and central.to.gov.br documentary acquisition."""
import hashlib
from datetime import datetime,timezone
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from app.tenderproof.contracts import DiscoveredCandidate,DocumentCandidate
from app.tenderproof.source_adapter_base import HTMLSourceAdapter,ListingPage
from app.tenderproof.faperr_pages import LISTING,detail_url,document_url,discover,parse

class FaperrAdapter(HTMLSourceAdapter):
    source='faperr_selection';listing_urls=(LISTING,);allowed_hosts=('faperr.rr.gov.br',)
    ready_selectors=('article .entry-content',);observed_url_paths=();document_identity_pattern=r'(?!)'
    implementation_state='partial'
    implementation_scope='Grafo publico de editais e documentos locais; modalidade, efeitos, referencias externas e publicacao pendentes.'

    def validate_listing_url(self,url):
        if url!=LISTING:detail_url(url)

    def acquire_listing(self,url,fetch):
        self.validate_listing_url(url)
        def exact(final):
            if final!=url:raise ValueError('Redirecionamento FAPERR inesperado')
        r=fetch(url,exact,4*1024*1024);exact(r.url_final);return r.content.decode('utf-8-sig')

    def parse_listing(self,html,url,limit=200):
        if url!=LISTING:raise ValueError('Listagem FAPERR fora do contrato')
        if type(limit)is not int or not 1<=limit<=10000:raise ValueError('Limite invalido')
        items=discover(html)
        return ListingPage(candidates=[self.candidate_from_url(u,d['title']) for u,d in list(items.items())[:limit]],truncated=len(items)>limit)

    def validate_detail_url(self,url):
        self.validate_listing_url(url)
        if url==LISTING:raise ValueError('Pagina inicial nao e edital')

    def candidate_from_url(self,url,title=None):
        self.validate_detail_url(url)
        return DiscoveredCandidate(candidate_id='faperr-'+hashlib.sha256(url.encode()).hexdigest()[:24],source=self.source,external_id=url,detail_url_observed=url,title_observed=title,observed_at=datetime.now(timezone.utc))

    def _candidate(self,candidate,url):
        self.validate_detail_url(url)
        if candidate.source!=self.source or candidate.external_id!=url or candidate.detail_url_observed!=url:raise ValueError('Identidade FAPERR divergente')

    def acquire_detail(self,url,candidate,fetch):
        self._candidate(candidate,url)
        menu=self.acquire_listing(LISTING,fetch)
        if url not in discover(menu):raise ValueError('Detalhe ausente do menu atual')
        return self.acquire_listing(url,fetch)

    def confirm_identity(self,candidate,html,url):
        self._candidate(candidate,url);p=parse(html,url)
        if not p['documents']:raise ValueError('Detalhe FAPERR sem documentos')
        if candidate.title_observed and candidate.title_observed!=p['title']:raise ValueError('Titulo FAPERR alterado; redescobrir antes de adquirir')

    def documents(self,html,candidate):
        self.confirm_identity(candidate,html,candidate.detail_url_observed);p=parse(html,candidate.detail_url_observed)
        if p['pending_links']:raise ValueError('Manifesto FAPERR com links complementares pendentes')
        grouped={}
        for d in p['documents']:
            if not d['title']:raise ValueError('Documento sem rotulo')
            grouped.setdefault(d['url'],[]).append(d)
        result=[]
        for url,ds in grouped.items():
            kinds={d['kind'] for d in ds}
            if len(kinds)!=1:raise ValueError('Papel documental conflitante')
            result.append(DocumentCandidate(doc_id='faperr-'+hashlib.sha256((candidate.external_id+url).encode()).hexdigest()[:24],title=' / '.join(dict.fromkeys(d['title'] for d in ds)),kind=kinds.pop(),url_requested=url,reason_chosen='Repositorio oficial vinculado ao detalhe da FAPERR; identidade documental e modalidade exigem conferencia.'))
        return result

    def validate_document_url(self,url,candidate):self._candidate(candidate,candidate.detail_url_observed);document_url(url)

    def choose_document(self,docs):
        originals=[d for d in docs if d.kind=='edital']
        if len(originals)!=1:raise ValueError('Original FAPERR ausente ou ambiguo')
        return originals[0]
