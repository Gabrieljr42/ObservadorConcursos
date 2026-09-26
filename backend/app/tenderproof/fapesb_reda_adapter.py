"""REDA selection tabs discovered from the current FAPESB page, without fixed years or files."""
import re
from urllib.parse import urlsplit,urljoin
from bs4 import BeautifulSoup
from app.tenderproof.source_adapter_base import HTMLSourceAdapter,ListingPage
from app.tenderproof.pilot_adapters import folded
from app.tenderproof.contracts import DiscoveredCandidate,DocumentCandidate
from datetime import datetime,timezone
import hashlib

LISTING='https://www.fapesb.ba.gov.br/reda/'

def document_context(anchor, tab):
    """Read the published heading immediately before this list, within its tab."""
    block=anchor.find_parent(['ul','ol'])
    if block is None or tab not in block.parents:return ''
    for sibling in block.previous_siblings:
        if not getattr(sibling,'name',None):continue
        if sibling.name in ('p','strong','h5','h6') and not sibling.select('a[href]'):
            return sibling.get_text(' ',strip=True)
        # A separator or another list ends the scope: never borrow its heading.
        return ''
    return ''

def document_url(url):
    from urllib.parse import unquote
    p=urlsplit(url);path=unquote(p.path)
    if p.scheme!='https' or p.netloc!='www.fapesb.ba.gov.br' or p.query or p.fragment or not re.fullmatch(r'/wp-content/uploads/\d{4}/\d{2}/[^/]+\.pdf',path,re.I) or any(x in ('.','..') for x in path.split('/')) or '\\' in path or '%' in path or any(ord(c)<32 for c in path):raise ValueError('PDF REDA fora do contrato')
    return url

def groups(html):
    s=BeautifulSoup(html,'html.parser');tabs=s.select('[id^="reda-tab-"]');result={};pending=[]
    if not tabs or len({t['id'] for t in tabs})!=len(tabs):raise ValueError('Abas REDA ausentes ou duplicadas')
    for t in tabs:
        year=re.fullmatch(r'reda-tab-(\d{4})',t['id']);heads=t.select('h4')
        if not year or len(heads)!=1:raise ValueError('Identidade de aba REDA ambigua')
        title=heads[0].get_text(' ',strip=True);number=re.search(r'edital\s+n[ºo°]?\s*(\d+)/(\d{4})',title,re.I)
        if not number or number[2]!=year[1] or 'fapesb' not in folded(title):raise ValueError('Cabecalho REDA divergente')
        docs=[];originals=[]
        for a in t.select('a[href]'):
            u=urljoin(LISTING,a['href']);label=a.get_text(' ',strip=True);text=folded(label)
            if u=='http://selecao.ba.gov.br/':continue
            try:document_url(u)
            except ValueError:pending.append({'url':u,'title':label,'tab':t['id']});continue
            kind='edital' if text=='edital de abertura' else 'prorrogacao' if 'prorrog' in text else 'retificacao' if 'errata' in text or 'retific' in text else 'anexo' if 'anexo' in text else 'outro'
            if kind=='edital':originals.append(u)
            context=document_context(a,t)
            display=label if kind=='edital' or not context else context+' — '+label
            docs.append({'url':u,'title':display,'kind':kind,'link_label':label,'section_title':context})
        if len(set(originals))!=1:raise ValueError('Original REDA ausente ou ambiguo')
        original=originals[0]
        if original in result:raise ValueError('Original compartilhado entre edicoes')
        result[original]={'title':title,'documents':docs,'tab':t['id'],'pending_links':[]}
    return result,pending

class FapesbRedaAdapter(HTMLSourceAdapter):
    source='fapesb_selection';listing_urls=(LISTING,);allowed_hosts=('www.fapesb.ba.gov.br',)
    ready_selectors=('[id^="reda-tab-"]',)
    observed_url_paths=();document_identity_pattern=r'(?!)';implementation_state='partial'
    implementation_scope='Abas REDA publicadas sem ano/arquivo fixo; outros programas FAPESB e publicacao pendentes.'
    def validate_listing_url(self,url):
        if url!=LISTING:raise ValueError('Listagem REDA invalida')
    def acquire_listing(self,url,fetch):
        self.validate_listing_url(url)
        def exact(actual):
            if actual!=url:raise ValueError('Redirecionamento REDA inesperado')
        r=fetch(url,exact,4*1024*1024);exact(r.url_final);return r.content.decode('utf-8-sig')
    def parse_listing(self,html,url,limit=200):
        self.validate_listing_url(url)
        if type(limit)is not int or not 1<=limit<=10000:raise ValueError('Limite invalido')
        g,p=groups(html)
        return ListingPage(candidates=[self.candidate_from_url(u,v['title']) for u,v in list(g.items())[:limit]],truncated=bool(p) or len(g)>limit,diagnostics=['Links complementares pendentes'] if p else [])
    def candidate_from_url(self,url,title=None):
        document_url(url)
        return DiscoveredCandidate(candidate_id='fapesb-'+hashlib.sha256(url.encode()).hexdigest()[:24],source=self.source,external_id=url,detail_url_observed=url,title_observed=title,observed_at=datetime.now(timezone.utc))
    def validate_detail_url(self,url):document_url(url)
    def _identity(self,c,url):
        document_url(url)
        if c.source!=self.source or c.external_id!=url or c.detail_url_observed!=url:raise ValueError('Identidade REDA divergente; redescoberta necessaria')
    def _group(self,html,c):
        self._identity(c,c.detail_url_observed);g,p=groups(html)
        if c.external_id not in g:raise ValueError('Original ausente da pagina atual')
        if c.title_observed and c.title_observed!=g[c.external_id]['title']:raise ValueError('Identidade editorial mudou')
        if any(x['tab']==g[c.external_id]['tab'] for x in p):raise ValueError('Anexos da aba pendentes')
        return g[c.external_id]
    def acquire_detail(self,url,candidate,fetch):
        self._identity(candidate,url);html=self.acquire_listing(LISTING,fetch);self._group(html,candidate);return html
    def validate_document_url(self,url,candidate):self._identity(candidate,candidate.detail_url_observed);document_url(url)
    def confirm_identity(self,candidate,html,url):self._identity(candidate,url);self._group(html,candidate)
    def documents(self,html,candidate):
        g=self._group(html,candidate);result=[];seen={}
        for d in g['documents']:
            if not d['title'].strip():raise ValueError('Documento REDA sem rotulo')
            if d['url'] in seen:
                if seen[d['url']]!=d['kind']:raise ValueError('Papel REDA conflitante')
                continue
            seen[d['url']]=d['kind'];result.append(DocumentCandidate(doc_id='fapesb-'+hashlib.sha256((candidate.external_id+d['url']).encode()).hexdigest()[:24],title=d['title'],kind=d['kind'],url_requested=d['url'],reason_chosen='Link na mesma aba REDA do edital original; efeitos dependem de conferencia.'))
        return result
    def choose_document(self,docs):
        originals=[d for d in docs if d.kind=='edital']
        if len(originals)!=1:raise ValueError('Original REDA ambiguo')
        return originals[0]
