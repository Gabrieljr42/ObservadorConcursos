"""Contemax WordPress contract observed 2026-09-08; PDF HTTPS currently blocked.

HTML HTTPS was verified on the exact official listing/detail paths. Legacy PDF
links are upgraded only on the official uploads directory; TLS remains mandatory.
No claim of full-source coverage or successful document acquisition is implied.
"""
import re
from urllib.parse import urljoin,urlsplit,urlunsplit
from app.tenderproof.pilot_adapters import PilotHTMLAdapter,visible_soup,folded
from app.tenderproof.batch60_major_adapters import document
from app.tenderproof.validation import title_is_corroborated


class ContemaxAdapter(PilotHTMLAdapter):
    source='contemax_open'
    detail_pattern=r'/site/((?:concursos-em-andamento|concursosrealizados)/[a-z0-9-]+)'
    document_identity_pattern=detail_pattern
    candidate_selector='a[href*="/site/concursos-em-andamento/"], a[href*="/site/concursosrealizados/"]'
    ready_selectors=('h3.tt-concurso',)
    listing_query_keys=()
    def __init__(self):
        super().__init__(self.source,'https://www.contemaxconsultoria.com.br/site/concursos')
    def _title(self,a):return a.get_text(' ',strip=True)
    def in_scope(self,title,url):
        return super().in_scope(title,url) and not any(w in folded(title+' '+url) for w in ('curso-de-formacao','curso de forma','planos de cargos','elaboracao de planos'))
    def confirm_identity(self,c,html,url):
        if len(html.encode('utf-8'))>2*1024*1024:raise ValueError('detalhe excede 2 MiB')
        s=self._check_detail(c,html,url);titles=s.select('h3.tt-detalhe')
        if len(titles)!=1 or not c.title_observed or not title_is_corroborated(c.title_observed,titles[0].get_text(' ',strip=True)):
            raise ValueError('título Contemax incompatível ou ambíguo')
    def validate_document_url(self,url,c):
        self._check_candidate(c);p=self._destination(url)
        if p.hostname!=self.portal_host or p.query or not re.fullmatch(r'/site/wp-content/uploads/\d{4}/\d{2}/[A-Za-z0-9_.%-]+\.pdf',p.path,re.I):
            raise ValueError('PDF Contemax fora do diretório observado')
    def documents(self,html,c):
        self.confirm_identity(c,html,c.detail_url_observed)
        s=visible_soup(html);heading=s.select_one('h3.tt-detalhe');scope=heading.parent
        result=[];seen=set()
        for a in scope.select('a[href]'):
            p=urlsplit(urljoin(c.detail_url_observed,a['href']))
            if not p.path.lower().endswith('.pdf'):continue
            # A literal legacy official URL supplies the entire path, never guessed.
            if p.scheme=='http' and p.hostname==self.portal_host and p.port is None and not p.username and not p.password:
                p=p._replace(scheme='https')
            url=urlunsplit(p);self.validate_document_url(url,c)
            if url in seen:continue
            seen.add(url);d=document(self.source,a.get_text(' ',strip=True),url)
            # Only the observed exact original label is principal. Mojibake in
            # historic labels cannot accidentally promote a supplementary notice.
            d.kind='edital' if folded(d.title)=='edital regulamentador' else 'outro'
            result.append(d)
        return result
