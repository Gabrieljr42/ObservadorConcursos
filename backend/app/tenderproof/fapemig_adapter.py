"""FAPEMIG published API pagination and observed detail payload acquisition."""
import hashlib,json,re
from datetime import datetime,timezone
from urllib.parse import urljoin,urlsplit
from bs4 import BeautifulSoup
from app.tenderproof.contracts import DiscoveredCandidate,DocumentCandidate
from app.tenderproof.source_adapter_base import HTMLSourceAdapter,ListingPage
from app.tenderproof.fapemig_pages import LISTING,DETAIL,listing_page,detail_slug,document_url,parse_api,decode_payload,documents

class FapemigAdapter(HTMLSourceAdapter):
    source='fapemig_selection';listing_urls=(LISTING,)
    allowed_hosts=('fapemig.br','api.site.fapemig.br');ready_selectors=('main',)
    observed_url_paths=();document_identity_pattern=r'(?!)'
    implementation_state='partial'
    implementation_scope='API publica paginada e manifesto Nuxt; leitura historica, semantica e publicacao pendentes.'

    def validate_listing_url(self,url):listing_page(url)

    def parse_listing(self,html,url,limit=200):
        if type(limit)is not int or not 1<=limit<=10000:raise ValueError('Limite invalido')
        calls,p=parse_api(html,url)
        candidates=[self.candidate_from_url(DETAIL+c['slug'],c['titulo']) for c in calls[:limit]]
        next_urls=[LISTING.replace('page=1&','page='+str(p['page']+1)+'&')] if p['page']<p['total_pages'] else []
        return ListingPage(candidates=candidates,next_urls=next_urls,truncated=len(calls)>limit)

    def validate_detail_url(self,url):detail_slug(url)

    def candidate_from_url(self,url,title=None):
        slug=detail_slug(url)
        return DiscoveredCandidate(candidate_id='fapemig-'+hashlib.sha256(slug.encode()).hexdigest()[:24],source=self.source,external_id=slug,detail_url_observed=url,title_observed=title,observed_at=datetime.now(timezone.utc))

    def _identity(self,candidate,url):
        detail_slug(url)
        if candidate.source!=self.source or candidate.detail_url_observed!=url or candidate.external_id!=detail_slug(url):raise ValueError('Identidade FAPEMIG divergente')

    def acquire_detail(self,url,candidate,fetch):
        self._identity(candidate,url)
        def get(target):
            def exact(actual):
                if actual!=target:raise ValueError('Redirecionamento FAPEMIG inesperado')
            r=fetch(target,exact,8*1024*1024);exact(r.url_final);return r.content.decode('utf-8-sig')
        html=get(url);s=BeautifulSoup(html,'html.parser');node=s.select_one('script#__NUXT_DATA__')
        if node is None:raise ValueError('Payload FAPEMIG ausente')
        payload=node.get_text()
        if node.get('data-src'):
            target=urljoin(url,node['data-src']);p=urlsplit(target)
            if p.scheme!='https' or p.netloc!='fapemig.br' or p.path!=urlsplit(url).path+'/_payload.json' or p.fragment or not re.fullmatch('[a-f0-9-]+',p.query):raise ValueError('Payload fora do detalhe')
            payload=get(target)
        proof=json.dumps({'format':'fapemig/1','url':url,'html':html,'payload':payload},ensure_ascii=False)
        self._call(proof,candidate);return proof

    def _call(self,html,candidate):
        self._identity(candidate,candidate.detail_url_observed);p=json.loads(html)
        if p.get('format')!='fapemig/1' or p.get('url')!=candidate.detail_url_observed:raise ValueError('Prova FAPEMIG divergente')
        data=decode_payload(p['payload']);call=data['data']['call-details-'+detail_slug(p['url'])]
        if call['slug']!=candidate.external_id or call['slug']!=detail_slug(p['url']) or call['publicacao_status']!='publish':raise ValueError('Detalhe nao confirma identidade')
        if candidate.title_observed and call['titulo']!=candidate.title_observed:raise ValueError('Titulo mudou; redescobrir')
        return call

    def confirm_identity(self,candidate,html,url):self._identity(candidate,url);self._call(html,candidate)

    def documents(self,html,candidate):
        docs,pending=documents(self._call(html,candidate))
        if pending:raise ValueError('Anexos FAPEMIG fora do contrato')
        result=[];seen={}
        for d in docs:
            if not d['title'].strip():raise ValueError('Anexo sem descricao')
            if d['url'] in seen:
                if seen[d['url']]!=d['kind']:raise ValueError('Papel conflitante')
                continue
            seen[d['url']]=d['kind'];result.append(DocumentCandidate(doc_id='fapemig-'+hashlib.sha256((candidate.external_id+d['url']).encode()).hexdigest()[:24],title=d['title'],kind=d['kind'],url_requested=d['url'],reason_chosen='Anexo da chamada identificada no payload publico; efeitos exigem conferencia documental.'))
        return result

    def validate_document_url(self,url,candidate):self._identity(candidate,candidate.detail_url_observed);document_url(url)

    def choose_document(self,docs):
        originals=[d for d in docs if d.kind=='edital']
        if len(originals)!=1:raise ValueError('Original FAPEMIG ambiguo')
        return originals[0]
