"""Batch30: observed Selecao.net variants and CONSULPAM's separate official portal.
No registration implies complete coverage. Evidence: batch30_shared fixtures.
"""
import re
from urllib.parse import urlsplit,parse_qs,urljoin
from bs4 import BeautifulSoup
from app.tenderproof.pilot_adapters import SelecaoNetAdapter,PilotHTMLAdapter,folded
from app.tenderproof.validation import title_is_corroborated

class ObservedNetAdapter(SelecaoNetAdapter):
    def __init__(self,source,listing_url,tenant,tabs,document_hosts):
        self.document_hosts=tuple(document_hosts)
        PilotHTMLAdapter.__init__(self,source,listing_url,listing_paths=tuple(dict.fromkeys([urlsplit(listing_url).path,*tabs])),document_hosts=self.document_hosts)
        self.tenant=tenant

    def documents(self,html,candidate):
        docs=super().documents(html,candidate)
        for d in docs:
            if d.kind=='edital' and any(t in folded(d.title) for t in ('avaliacao','titulos','pontuacao','notas','complementar','sumula','sorteio','reabertura','prorrogacao')):
                d.kind='outro'
        return docs

class CotecAdapter(ObservedNetAdapter):
    candidate_selector='h3 a[href], .dados > a[href]'

class IDCAPAdapter(ObservedNetAdapter):
    candidate_selector='.list__item a[href]'
    ready_selectors=('.list__item a[href*="/informacoes/"]',)
    def _title(self,a):
        n=a.select_one('.content__title')
        if n is None:return None
        title=n.get_text(' ',strip=True)
        # Listing declares ISO-8859-1 while observed content is UTF-8. Repair
        # only this source's reversible mojibake, preserving already-valid text.
        if any(ch in title for ch in ('Ã','Â')):
            try:title=title.encode('latin1').decode('utf-8')
            except (UnicodeEncodeError,UnicodeDecodeError):pass
        return title

class QuadrixAdapter(ObservedNetAdapter):
    def confirm_identity(self,candidate,html,url):
        soup=self._check_detail(candidate,html,url)
        if not self.documents(html,candidate):raise ValueError('identidade sem vínculo documental')
        title=' '.join(h.get_text(' ',strip=True) for h in soup.select('.dados h2,h1'))
        if any(ch in title for ch in ('Ã','Â')):
            try:title=title.encode('latin1').decode('utf-8')
            except (UnicodeEncodeError,UnicodeDecodeError):pass
        if candidate.title_observed and not title_is_corroborated(candidate.title_observed,title):
            raise ValueError('título do detalhe incompatível com candidato')

class W2Adapter(ObservedNetAdapter):
    def validate_listing_url(self,url):
        p=self._destination(url);q=parse_qs(p.query,keep_blank_values=True)
        if not p.query:return super().validate_listing_url(url)
        if p.hostname!=self.portal_host or p.path!='/index/todos/' or set(q)!={'ord','dir','pg','q','pp'} or any(len(v)!=1 for v in q.values()) or q['ord']!=[''] or q['dir']!=[''] or q['q']!=[''] or q['pp']!=['10'] or not re.fullmatch(r'\d{1,5}',q['pg'][0]):
            raise ValueError('paginação W2 fora do contrato observado')

class ConsulpamAdapter(PilotHTMLAdapter):
    """Own ID space. The separate net portal is an unmerged alternate scope."""
    source='consulpam_open'
    candidate_selector='a[href*="acao=ver"]'
    ready_selectors=('a[href*="acao=ver"]',)
    document_hosts=('www.consulpam.com.br',)
    document_identity_pattern=r'consulpam\.com\.br/index\.php\?menu=concursos&acao=ver&id=(\d+)'
    def __init__(self):
        super().__init__(self.source,'https://www.consulpam.com.br/index.php?menu=concursos')
    def validate_listing_url(self,url):
        p=self._destination(url)
        if p.hostname!=self.portal_host or p.path!='/index.php' or parse_qs(p.query,keep_blank_values=True)!={'menu':['concursos']}:
            raise ValueError('listagem CONSULPAM não observada')
    def validate_detail_url(self,url):
        p=self._destination(url);q=parse_qs(p.query,keep_blank_values=True)
        if p.hostname!=self.portal_host or p.path!='/index.php' or set(q)!={'menu','acao','id'} or q['menu']!=['concursos'] or q['acao']!=['ver'] or len(q['id'])!=1 or not re.fullmatch(r'\d{1,12}',q['id'][0]):
            raise ValueError('identidade de detalhe CONSULPAM inválida')
    def candidate_from_url(self,url,title=None):
        from app.tenderproof.contracts import DiscoveredCandidate
        from datetime import datetime,timezone
        self.validate_detail_url(url);external=parse_qs(urlsplit(url).query)['id'][0]
        return DiscoveredCandidate(candidate_id=f'{self.source}-{external}',external_id=external,source=self.source,title_observed=title,detail_url_observed=url,observed_at=datetime.now(timezone.utc))
    def _title(self,a):return a.get_text(' ',strip=True)
    def document_route(self,p):return p.path.startswith('/arquivos/')
    def validate_document_url(self,url,candidate):
        self._check_candidate(candidate);p=self._destination(url)
        if p.hostname not in self.document_hosts or p.query or not self.document_route(p) or not p.path.lower().endswith('.pdf'):
            raise ValueError('documento fora do diretório oficial CONSULPAM')
    def _document_title(self,a):
        return re.sub(r'^\d{2}/\d{2}/\d{4}\s*-\s*','',a.get_text(' ',strip=True))
    def confirm_identity(self,candidate,html,url):
        soup=self._check_detail(candidate,html,url)
        if not candidate.title_observed or not title_is_corroborated(candidate.title_observed,soup.get_text(' ',strip=True)):
            raise ValueError('título do detalhe CONSULPAM incompatível')
        if not self.documents(html,candidate):raise ValueError('sem vínculo documental oficial')

def tabs(*values):return tuple(f'/index/{v}/' for v in values)
R2=('anexos-r2.selecao.net.br',)
OLD=('anexos.cdn.selecao.net.br',)
BATCH30_SHARED_ADAPTERS=(
 ObservedNetAdapter('exame_open','https://concursos.exameconsultores.com.br/index/1/','140',tabs('abertos',1,2,3,5,7,4),R2),
 ObservedNetAdapter('objetiva_open','https://concursos.objetivas.com.br','361',('/',*tabs('abertos',1,3)),R2),
 CotecAdapter('cotec_open','https://www.cotec.fadenor.com.br/index/abertos/','846',tabs('abertos',1,3,2,5),R2),
 QuadrixAdapter('quadrix_open','https://quadrix.org.br/index/abertos/','861',tabs('abertos',1,3,4,6),R2),
 ObservedNetAdapter('rbo_open','https://rboconcursos.selecao.net.br/index/abertos/','814',tabs('abertos',1,2,3,4,5),R2),
 ObservedNetAdapter('sigma_open','https://concursos.sigmaassessoria.com.br','57',('/',*tabs('abertos',1,2,3,4,5)),R2),
 ObservedNetAdapter('fafipa_open','https://concursos.fundacaofafipa.org.br/','281',tabs('abertos',1,3),R2),
 ObservedNetAdapter('omni_open','https://portal.omniconcursospublicos.com.br','412',('/',*tabs('abertos',1,2,3,4,5)),OLD),
 W2Adapter('w2_open','https://www.w2consultores.com.br/index/todos/','41',tabs('todos','abertos',1,2,3,4,5),OLD),
 ConsulpamAdapter(),
 IDCAPAdapter('idcap_open','https://www.idcap.org.br','227',('/',*tabs('abertos',1,3,5),'/index/abertos','/index/1','/index/3','/index/5'),R2),
)
