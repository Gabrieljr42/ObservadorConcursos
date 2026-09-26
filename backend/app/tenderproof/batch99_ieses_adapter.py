"""Observed IESES public JSON index and two verified personnel subportals."""
import json
import re
from datetime import datetime,timezone
from urllib.parse import parse_qs,urlsplit
from app.tenderproof.contracts import DiscoveredCandidate
from app.tenderproof.pilot_adapters import PilotHTMLAdapter,visible_soup,folded
from app.tenderproof.source_adapter_base import ListingPage
from app.tenderproof.validation import title_is_corroborated

class IESESAdapter(PilotHTMLAdapter):
    source='ieses_open'
    verified={'scgas2026':('0026','scgas0012026'),'crmvsc':('0025','crmvsc')}
    cdn='iesesconcursos.nyc3.cdn.digitaloceanspaces.com'
    document_identity_pattern=r'(?:www\.)?([a-z0-9]+)\.ieses\.org'
    def __init__(self):
        hosts=tuple(h for key in self.verified for h in (key+'.ieses.org','www.'+key+'.ieses.org'))
        super().__init__(self.source,'https://ieses.org/projetos/api?offset=0&limit=12',document_hosts=(*hosts,self.cdn))
        self.document_hosts=(self.cdn,)
    def validate_listing_url(self,url):
        p=self._destination(url);q=parse_qs(p.query,keep_blank_values=True)
        if p.hostname!='ieses.org' or p.path!='/projetos/api' or set(q)!={'offset','limit'} or q['limit']!=['12'] or len(q['offset'])!=1 or not re.fullmatch(r'\d{1,6}',q['offset'][0]):
            raise ValueError('paginação IESES fora do contrato observado')
    def validate_detail_url(self,url):
        p=self._destination(url);key=p.hostname.removeprefix('www.').removesuffix('.ieses.org')
        if key not in self.verified or p.path!='/' or p.query:raise ValueError('subportal IESES ainda sem contrato documental verificado')
    def candidate_from_url(self,url,title=None):
        self.validate_detail_url(url);key=urlsplit(url).hostname.removeprefix('www.').removesuffix('.ieses.org')
        # Both exact redirects were captured before selecting their final URLs.
        url='https://'+key+'.ieses.org/'
        return DiscoveredCandidate(candidate_id=f'{self.source}-{key}',source=self.source,external_id=key,title_observed=title,
            detail_url_observed=url,observed_at=datetime.now(timezone.utc))
    def parse_listing(self,html,url,limit=200):
        self.validate_listing_url(url)
        if not 1<=limit<=10000 or len(html.encode('utf-8'))>2097152:raise ValueError('limite JSON IESES excedido')
        data=json.loads(html)
        if not isinstance(data,dict) or not isinstance(data.get('projetos'),list) or len(data['projetos'])>12:raise ValueError('JSON IESES incompleto')
        found=[];seen=set();unverified=0
        for row in data['projetos']:
            if not isinstance(row,dict) or any(not isinstance(row.get(k),str) or not row[k] for k in ('projectTokenKey','entidade','evento','pasta','url')):raise ValueError('identidade IESES incompleta')
            if row['projectTokenKey'] in seen:raise ValueError('ID IESES duplicado')
            seen.add(row['projectTokenKey'])
            p=urlsplit(row['url']);key=(p.hostname or '').removeprefix('www.').removesuffix('.ieses.org')
            if key not in self.verified:
                unverified+=1;continue
            if (row['projectTokenKey'],row['pasta'])!=self.verified[key]:raise ValueError('subportal IESES reutilizado ou diretório divergente')
            title=row['entidade']+' - '+row['evento']
            if self.in_scope(title,row['url']):found.append(self.candidate_from_url(row['url'],title))
        offset=int(parse_qs(urlsplit(url).query)['offset'][0]);size=len(data['projetos'])
        return ListingPage(candidates=found[:limit],truncated=len(found)>limit or bool(unverified),
            next_urls=['https://ieses.org/projetos/api?offset='+str(offset+size)+'&limit=12'] if size==12 else [],
            empty_evidence='API oficial projetos=[]' if size==0 and offset==0 else None,
            terminal_evidence='API abaixo de12 itens conforme componente observado' if size<12 and not unverified else None,
            diagnostics=[f'{unverified} subportais ainda sem contrato documental; escopo verificado SCGAS2026 e CRMVSC2026'])
    def confirm_identity(self,c,html,url):
        soup=self._check_detail(c,html,url)
        h1=soup.select_one('h1');h2=soup.select_one('h2')
        text=' '.join(h.get_text(' ',strip=True) for h in (h1,h2) if h)
        if not c.title_observed or not title_is_corroborated(c.title_observed,text):raise ValueError('cabeçalho IESES incompatível')
        numbers=set(re.findall(r'\b\d{3}/\d{4}\b',c.title_observed))
        if numbers and set(re.findall(r'\b\d{3}/\d{4}\b',text))!=numbers:raise ValueError('número/ano IESES incompatível')
        if not self.documents(html,c):raise ValueError('IESES sem documentos oficiais')
    def document_route(self,p):return '/documentos/' in p.path
    def validate_document_url(self,url,c):
        self._check_candidate(c);p=self._destination(url)
        folder=self.verified[c.external_id][1]
        if p.hostname!=self.cdn or p.query or not re.fullmatch('/2026/'+re.escape(folder)+r'/documentos/[a-zA-Z0-9_.-]+\.pdf',p.path):raise ValueError('PDF IESES de outro processo/diretório')
    def _document_title(self,a):
        for node in a.select('time,span.visually-hidden'):node.decompose()
        return a.get_text(' ',strip=True).lstrip('- ').strip()
    def documents(self,html,c):
        docs=super().documents(html,c)
        for doc in docs:
            if doc.kind=='edital' and not re.fullmatch(r'edital\s+\d{3}/\d{4}',folded(doc.title)):doc.kind='outro'
        return docs

BATCH99_IESES_ADAPTERS=(IESESAdapter(),)
