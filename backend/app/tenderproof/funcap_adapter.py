"""FUNCAP acquisition keyed by unique observed original documents, never reused consultation IDs."""
import hashlib
from datetime import datetime,timezone
from collections import Counter
from app.tenderproof.contracts import DiscoveredCandidate,DocumentCandidate
from app.tenderproof.funcap_panels import LISTING,parse_panels,document_url
from app.tenderproof.source_adapter_base import HTMLSourceAdapter,ListingPage


def eligible_groups(html):
    parsed=parse_panels(html);counts=Counter(d['url'] for p in parsed['panels'] for d in p['documents'])
    eligible={};pending=[]
    for panel in parsed['panels']:
        originals=[d for d in panel['documents'] if d['kind']=='edital' and d['format']=='pdf']
        if len(originals)!=1 or counts[originals[0]['url']]!=1:
            pending.append(panel['title']);continue
        eligible[originals[0]['url']]=panel
    return parsed,eligible,pending


class FuncapAdapter(HTMLSourceAdapter):
    source='fapece_selection'
    listing_urls=(LISTING,)
    allowed_hosts=('montenegro.funcap.ce.gov.br',)
    ready_selectors=('.editais-conteudo',)
    observed_url_paths=()
    document_identity_pattern=r'(?!)'
    implementation_state='partial'
    implementation_scope='Grupos com original PDF unívoco; identidade documental, grupos ambíguos, modalidade e publicação pendentes.'

    def validate_listing_url(self,url):
        if url!=LISTING:raise ValueError('listagem FUNCAP fora do contrato')

    def acquire_listing(self,url,fetch):
        self.validate_listing_url(url)
        def exact(target):self.validate_listing_url(target)
        response=fetch(url,exact,4*1024*1024);exact(response.url_final)
        return response.content.decode('utf-8-sig')

    def parse_listing(self,html,url,limit=200):
        self.validate_listing_url(url)
        if type(limit) is not int or not 1<=limit<=10000:raise ValueError('limite inválido')
        parsed,groups,pending=eligible_groups(html)
        return ListingPage(candidates=[self.candidate_from_url(u,p['title']) for u,p in list(groups.items())[:limit]],
            truncated=bool(pending) or len(groups)>limit,
            diagnostics=[parsed['reason']]+['Original não unívoco: '+title for title in pending])

    def validate_detail_url(self,url):
        if document_url(url)!=url or not url.lower().endswith('.pdf') or '/resultados/' in url:
            raise ValueError('referência de original FUNCAP inválida')

    def candidate_from_url(self,url,title=None):
        self.validate_detail_url(url)
        return DiscoveredCandidate(candidate_id='funcap-'+hashlib.sha256(url.encode()).hexdigest()[:24],
            source=self.source,external_id=url,detail_url_observed=url,title_observed=title,observed_at=datetime.now(timezone.utc))

    def _candidate(self,candidate,url):
        self.validate_detail_url(url)
        if candidate.source!=self.source or candidate.external_id!=url or candidate.detail_url_observed!=url:
            raise ValueError('candidato FUNCAP divergente')

    def _group(self,html,candidate):
        self._candidate(candidate,candidate.detail_url_observed)
        _,groups,_=eligible_groups(html)
        if candidate.external_id not in groups:raise ValueError('original não vinculado univocamente à listagem atual FUNCAP')
        return groups[candidate.external_id]

    def acquire_detail(self,url,candidate,fetch):
        self._candidate(candidate,url)
        html=self.acquire_listing(LISTING,fetch);self._group(html,candidate)
        return html

    def confirm_identity(self,candidate,html,url):
        self._candidate(candidate,url);self._group(html,candidate)

    def documents(self,html,candidate):
        return [DocumentCandidate(doc_id='funcap-'+hashlib.sha256((candidate.external_id+':'+d['url']).encode()).hexdigest()[:24],
            title=d['title'],kind=d['kind'],url_requested=d['url'],
            reason_chosen='Arquivo observado no mesmo grupo do original unívoco; identidade documental e modalidade exigem conferência. Data publicada: '+d['published_at'])
            for d in self._group(html,candidate)['documents']]

    def validate_document_url(self,url,candidate):
        self._candidate(candidate,candidate.detail_url_observed);document_url(url)

    def choose_document(self,docs):
        originals=[d for d in docs if d.kind=='edital']
        if len(originals)!=1:raise ValueError('original FUNCAP ausente ou ambíguo')
        return originals[0]
