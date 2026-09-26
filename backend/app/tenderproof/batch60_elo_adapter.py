"""Observed ELO tenant of the same public API used by Reis; separate documents."""
import re
from app.tenderproof.batch30_own_adapters import ReisAdapter,HeadingAdapter
from app.tenderproof.pilot_adapters import visible_soup,PilotHTMLAdapter


class EloAdapter(ReisAdapter):
    source='elo_open'
    frontend='https://novo.eloassessoriaeservicos.com.br'
    tenant_id='eloassessoria'
    frontend_listing_path='/concursos'
    detail_prefix='/concurso/'
    detail_pattern=r'/concurso/(\d+)'
    document_identity_pattern=r'eloassessoriaeservicos\.com\.br/concurso/(\d+)'
    identity_selector='h2'
    def confirm_identity(self,candidate,html,url):
        HeadingAdapter.confirm_identity(self,candidate,html,url)
    def document_route(self,p):
        return p.path.startswith('/sgs.eloassessoriaeservicos.com.br/') and '/anexos/' in p.path
    def validate_document_url(self,url,candidate):
        self._check_candidate(candidate);p=self._destination(url)
        if p.hostname!='s3.amazonaws.com' or p.query or not re.fullmatch(r'/sgs\.eloassessoriaeservicos\.com\.br/[a-z0-9-]+/\d+/\d+-\d{4}/anexos/[^/]+\.pdf',p.path,re.I):
            raise ValueError('documento ELO fora do tenant observado')
    def documents(self,html,candidate):
        soup=visible_soup(html)
        # Duplicate action links precede the publication table and lack labels.
        # Classify only the observed labelled rows, never the download button.
        for a in soup.select('a[href]'):
            if not a.find_parent('tr'):a.attrs.pop('href',None)
        return PilotHTMLAdapter.documents(self,str(soup),candidate)
    def _document_title(self,a):
        row=a.find_parent('tr');cells=row.select('td') if row else []
        return cells[0].get_text(' ',strip=True) if cells else ''


BATCH60_ELO_ADAPTERS=(EloAdapter(),)
