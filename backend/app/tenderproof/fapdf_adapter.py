"""FAPDF live menu traversal with unique original-document identities per annual page."""
import hashlib,json
from datetime import datetime,timezone
from collections import Counter
from app.tenderproof.contracts import DiscoveredCandidate,DocumentCandidate
from app.tenderproof.source_adapter_base import HTMLSourceAdapter,ListingPage
from app.tenderproof.fapdf_pages import LISTING,page_url,document_url,leaves,panels

def eligible(html,url):
    groups,unassigned=panels(html,url);counts=Counter(d['url'] for g in groups for d in g['documents']);result={};pending=[]
    for g in groups:
        originals={d['url'] for d in g['documents'] if d['kind']=='edital'}
        if len(originals)!=1 or counts[next(iter(originals))]!=1:pending.append(g['title']);continue
        result[next(iter(originals))]=g
    return result,pending,unassigned

class FapdfAdapter(HTMLSourceAdapter):
    source='fapdf_selection';listing_urls=(LISTING,);allowed_hosts=('fap.df.gov.br',)
    ready_selectors=('.journal-content-article',);observed_url_paths=();document_identity_pattern=r'(?!)'
    implementation_state='partial'
    implementation_scope='Painéis com original unívoco; arquivos históricos fora dos painéis, documentos complementares e publicação pendentes.'

    def __init__(self):
        self._listing_hints={}

    def validate_listing_url(self,url):page_url(url)

    def acquire_listing(self,url,fetch):
        page_url(url)
        def get(target):
            def exact(final):
                if final!=target:raise ValueError('Redirecionamento FAPDF inesperado')
            r=fetch(target,exact,8*1024*1024);exact(r.url_final);return r.content.decode('utf-8-sig')
        menu=get(LISTING)
        if url!=LISTING and url not in leaves(menu):raise ValueError('Pagina ausente do menu atual')
        return json.dumps({'format':'fapdf/1','url':url,'menu':menu,'html':menu if url==LISTING else get(url)},ensure_ascii=False)

    def _proof(self,body,url):
        d=json.loads(body)
        if d.get('format')!='fapdf/1' or d.get('url')!=url:raise ValueError('Prova FAPDF divergente')
        if url!=LISTING and url not in leaves(d['menu']):raise ValueError('Pagina nao vinculada ao menu')
        return d

    def parse_listing(self,html,url,limit=200):
        page_url(url);d=self._proof(html,url)
        if type(limit) is not int or not 1<=limit<=10000:raise ValueError('Limite invalido')
        if url==LISTING:return ListingPage(next_urls=list(leaves(d['menu'])))
        groups,pending,unassigned=eligible(d['html'],url)
        candidates=[]
        for doc,g in list(groups.items())[:limit]:
            self._listing_hints[doc]=url
            candidates.append(self.candidate_from_url(doc,g['title']))
        return ListingPage(candidates=candidates,truncated=bool(pending or unassigned) or len(groups)>limit,diagnostics=['Original nao univoco: '+t for t in pending]+(['Links fora de paineis pendentes: '+str(len(unassigned))] if unassigned else []))

    def validate_detail_url(self,url):document_url(url)

    def candidate_from_url(self,url,title=None):
        document_url(url)
        return DiscoveredCandidate(candidate_id='fapdf-'+hashlib.sha256(url.encode()).hexdigest()[:24],source=self.source,external_id=url,detail_url_observed=url,title_observed=title,observed_at=datetime.now(timezone.utc))

    def _identity(self,candidate,url):
        document_url(url)
        if candidate.source!=self.source or candidate.external_id!=url or candidate.detail_url_observed!=url:raise ValueError('Identidade FAPDF divergente')

    def _group(self,body,candidate):
        self._identity(candidate,candidate.detail_url_observed)
        url=json.loads(body).get('url');page_url(url)
        d=self._proof(body,url);groups,_,_=eligible(d['html'],url)
        if candidate.detail_url_observed not in groups:raise ValueError('Original nao univoco na pagina atual')
        return groups[candidate.detail_url_observed]

    def acquire_detail(self,url,candidate,fetch):
        self._identity(candidate,url)
        menu=self.acquire_listing(LISTING,fetch)
        urls=list(leaves(self._proof(menu,LISTING)['menu']))
        hint=self._listing_hints.get(url)
        if hint in urls:urls.remove(hint);urls.insert(0,hint)
        for listing in urls:
            body=self.acquire_listing(listing,fetch)
            groups,_,_=eligible(self._proof(body,listing)['html'],listing)
            if url in groups:self._group(body,candidate);return body
        raise ValueError('Original nao encontrado no menu atual FAPDF')

    def confirm_identity(self,candidate,html,url):self._identity(candidate,url);self._group(html,candidate)

    def documents(self,html,candidate):
        g=self._group(html,candidate)
        if g['pending_links']:raise ValueError('Documentos complementares pendentes FAPDF')
        result=[];seen={}
        for d in g['documents']:
            if not d['title'].strip('. '):raise ValueError('Documento sem rotulo FAPDF')
            if d['url'] in seen:
                if seen[d['url']]!=d['kind']:raise ValueError('Papel documental conflitante')
                continue
            seen[d['url']]=d['kind']
            result.append(DocumentCandidate(doc_id='fapdf-'+hashlib.sha256((candidate.external_id+d['url']).encode()).hexdigest()[:24],title=d['title'],kind=d['kind'],url_requested=d['url'],reason_chosen='Mesmo painel do original unico; identidade e efeitos exigem conferencia.'))
        return result

    def validate_document_url(self,url,candidate):self._identity(candidate,candidate.detail_url_observed);document_url(url)

    def choose_document(self,docs):
        originals=[d for d in docs if d.kind=='edital']
        if len(originals)!=1:raise ValueError('Original FAPDF ambiguo')
        return originals[0]
