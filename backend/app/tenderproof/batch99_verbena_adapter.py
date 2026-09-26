"""One verified personnel subportal, linked by the official homepage banner.

The banner has no useful text. Its title is reviewed detail evidence, not text
extracted from that banner. Other personnel banners remain outside this scope.
"""
import re
from datetime import datetime, timezone
from urllib.parse import urlsplit, unquote
from app.tenderproof.contracts import DiscoveredCandidate
from app.tenderproof.pilot_adapters import PilotHTMLAdapter, folded, visible_soup
from app.tenderproof.source_adapter_base import ListingPage

class VerbenaAdapter(PilotHTMLAdapter):
    source='verbena_selection'
    base='/2026/concurso-camara-pires-do-rio/'
    reviewed_title='IV - Concurso Público da Câmara Municipal de Pires do Rio - GO'
    document_hosts=('sistemas.institutoverbena.ufg.br',)
    document_identity_pattern=r'/2026/(concurso-camara-pires-do-rio)/'
    def __init__(self):
        super().__init__(self.source,'https://institutoverbena.ufg.br/',document_hosts=self.document_hosts)
    def validate_detail_url(self,url):
        p=self._destination(url)
        if p.hostname!=self.document_hosts[0] or p.path!=self.base or p.query:raise ValueError('subportal Verbena fora do escopo verificado')
    def candidate_from_url(self,url,title=None):
        self.validate_detail_url(url)
        return DiscoveredCandidate(candidate_id=self.source+'-2026-pires',source=self.source,external_id='concurso-camara-pires-do-rio',
            detail_url_observed=url,title_observed=title,observed_at=datetime.now(timezone.utc))
    def parse_listing(self,html,url,limit=200):
        self.validate_listing_url(url)
        if not 1<=limit<=10000:raise ValueError('limite inválido')
        soup=visible_soup(html)
        target='https://'+self.document_hosts[0]+self.base
        matches=[a for a in soup.select('a[data-banner-id][href]') if a['href']==target]
        return ListingPage(candidates=[self.candidate_from_url(target,self.reviewed_title)] if matches else [],
            truncated=True,diagnostics=['Somente banner Pires do Rio2026; título verificado no detalhe preservado, não no banner. Outras seleções e arquivo ainda fora da cobertura.'])
    def confirm_identity(self,c,html,url):
        soup=self._check_detail(c,html,url);title=soup.select_one('title')
        if not title or folded(title.get_text(' ',strip=True))!=folded(self.reviewed_title):raise ValueError('órgão/título Verbena divergente')
        if c.title_observed and folded(c.title_observed)!=folded(self.reviewed_title):raise ValueError('candidato Verbena divergente')
        if not any(folded(d.title)=='edital de abertura n 01/2026' or re.fullmatch(r'edital de abertura n[oa°º]?\s*01/2026',folded(d.title)) for d in self.documents(html,c)):
            raise ValueError('edital de abertura01/2026 ausente')
    def document_route(self,p):return '/sistema/arquivos/editais/' in p.path
    def validate_document_url(self,url,c):
        self._check_candidate(c);p=self._destination(url)
        if p.hostname!=self.document_hosts[0] or p.query or not unquote(p.path).startswith(self.base+'sistema/arquivos/editais/') or not p.path.lower().endswith('.pdf'):
            raise ValueError('PDF Verbena fora do concurso associado')

BATCH99_VERBENA_ADAPTERS=(VerbenaAdapter(),)
