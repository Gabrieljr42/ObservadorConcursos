"""FAPEAP program pages acquired by ordinary browser navigation."""
import re,hashlib
from datetime import datetime,timezone
from urllib.parse import urlsplit,urljoin,unquote,quote
from bs4 import BeautifulSoup
from app.tenderproof.contracts import DiscoveredCandidate,DocumentCandidate
from app.tenderproof.pilot_adapters import folded
from app.tenderproof.source_adapter_base import HTMLSourceAdapter,ListingPage

ROOT='https://fapeap.portal.ap.gov.br/'

def program_url(url):
    p=urlsplit(url)
    if p.scheme!='https' or p.netloc!='fapeap.portal.ap.gov.br' or p.query or p.fragment or not re.fullmatch('/pagina/programas/[a-z0-9-]+',p.path):raise ValueError('Programa FAPEAP fora do contrato')
    return url

def document_url(url):
    p=urlsplit(url);path=unquote(p.path)
    if p.scheme!='https' or p.netloc!='matrix.amapa.gov.br' or p.query or p.fragment or not re.match(r'^//storage/(submenus/66/files|publications/66)/[^/]+$',path) or '%' in path or '\\' in path or any(ord(c)<32 for c in path):raise ValueError('Arquivo FAPEAP fora do contrato')
    return 'https://matrix.amapa.gov.br'+quote(path,safe='/()')

class FapeapAdapter(HTMLSourceAdapter):
    source='fapeap_selection';listing_urls=(ROOT,);allowed_hosts=('fapeap.portal.ap.gov.br','matrix.amapa.gov.br')
    ready_selectors=('h1',);observed_url_paths=();document_identity_pattern=r'(?!)'
    implementation_state='partial'
    implementation_scope='Programas publicados no menu via navegador; publicacoes paginadas e documentos quebrados exigem conciliacao; sem homologacao integral.'

    def validate_listing_url(self,url):
        if url!=ROOT:raise ValueError('Listagem FAPEAP fora do contrato')

    def parse_listing(self,html,url,limit=200):
        self.validate_listing_url(url)
        if type(limit)is not int or not 1<=limit<=10000:raise ValueError('Limite invalido')
        s=BeautifulSoup(html,'html.parser');items={}
        for a in s.select('a[href]'):
            target=urljoin(url,a['href'])
            try:program_url(target)
            except ValueError:continue
            items[target]=a.get_text(' ',strip=True)
        if not items:raise ValueError('Menu de programas ausente')
        return ListingPage(candidates=[self.candidate_from_url(u,t) for u,t in list(items.items())[:limit]],truncated=True,diagnostics=['Programas nao equivalem necessariamente a um unico edital. Conciliacao com publicacoes paginadas pendente.'])

    def validate_detail_url(self,url):program_url(url)

    def candidate_from_url(self,url,title=None):
        program_url(url)
        return DiscoveredCandidate(candidate_id='fapeap-'+hashlib.sha256(url.encode()).hexdigest()[:24],source=self.source,external_id=url,detail_url_observed=url,title_observed=title,observed_at=datetime.now(timezone.utc))

    def confirm_identity(self,candidate,html,url):
        program_url(url)
        if candidate.source!=self.source or candidate.external_id!=url or candidate.detail_url_observed!=url:raise ValueError('Candidato FAPEAP divergente')
        s=BeautifulSoup(html,'html.parser')
        if len(s.select('h1'))!=1 or not s.select('table tr'):raise ValueError('Programa ou arquivos ausentes')

    def documents(self,html,candidate):
        self.confirm_identity(candidate,html,candidate.detail_url_observed);s=BeautifulSoup(html,'html.parser');result=[];seen=set()
        for tr in s.select('table tr'):
            cells=tr.select('td')
            if len(cells)<2:continue
            title=cells[0].get_text(' ',strip=True)
            for a in cells[-1].select('a[href]'):
                url=document_url(urljoin(candidate.detail_url_observed,a['href']))
                if url in seen:continue
                seen.add(url);text=folded(title);kind='outro'
                if re.search('resultado|homolog|enquadramento|convoc|perguntas',text):pass
                elif 'prorrog' in text:kind='prorrogacao'
                elif 'retific' in text:kind='retificacao'
                elif text.startswith('anexo'):kind='anexo'
                elif re.match('(edital|chamada)',text):kind='edital'
                result.append(DocumentCandidate(doc_id='fapeap-'+hashlib.sha256((candidate.external_id+url).encode()).hexdigest()[:24],title=title,kind=kind,url_requested=url,reason_chosen='Arquivo da tabela do programa; identidade documental e conciliacao com publicacoes exigem conferencia.'))
        return result

    def validate_document_url(self,url,candidate):program_url(candidate.detail_url_observed);document_url(url)

    def choose_document(self,docs):
        originals=[d for d in docs if d.kind=='edital']
        if len(originals)!=1:raise ValueError('Original FAPEAP ausente ou ambiguo')
        return originals[0]
