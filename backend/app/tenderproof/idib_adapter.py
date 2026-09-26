"""Public IDIB ASP.NET listing and documents observed in September 2026."""
import re
import hashlib
from urllib.parse import urlsplit,parse_qs,urljoin
from datetime import datetime,timezone
from app.tenderproof.pilot_adapters import PilotHTMLAdapter,visible_soup,document_kind,folded
from app.tenderproof.contracts import DiscoveredCandidate,DocumentCandidate
from app.tenderproof.source_adapter_base import ListingPage
from app.tenderproof.validation import title_is_corroborated


class IdibAdapter(PilotHTMLAdapter):
    html_encoding='utf-8' # Current response bytes contradict the legacy meta charset.
    ready_selectors=('#LBL_ConcursoAberto','#LBL_ConcursoAndamento')
    document_identity_pattern=r'concurso\.idib\.org\.br/Concurso\.aspx\?ID=(\d+)'
    listing_query_keys=()

    def __init__(self):
        super().__init__('idib_open','https://concurso.idib.org.br/SITE/Concursos.aspx')

    def validate_detail_url(self,url):
        p=self._destination(url);q=parse_qs(p.query,keep_blank_values=True)
        if p.path!='/Concurso.aspx' or set(q)!={'ID'} or len(q['ID'])!=1 or not re.fullmatch(r'[1-9]\d{0,8}',q['ID'][0]):
            raise ValueError('detalhe IDIB inválido')

    def candidate_from_url(self,url,title=None):
        self.validate_detail_url(url);key=parse_qs(urlsplit(url).query)['ID'][0]
        return DiscoveredCandidate(candidate_id='idib-'+key,external_id=key,source=self.source,
            title_observed=title,detail_url_observed=url,observed_at=datetime.now(timezone.utc))

    def parse_listing(self,html,url,limit=200):
        self.validate_listing_url(url)
        if not 1<=limit<=10000 or len(html.encode('utf-8'))>2*1024*1024:raise ValueError('limite da listagem')
        soup=visible_soup(html);result=ListingPage();seen=set()
        for selector in self.ready_selectors:
            section=soup.select_one(selector)
            if section is None:raise ValueError('seção pública IDIB ausente')
            for a in section.select('a[href]'):
                if 'Concurso.aspx' not in a['href']:continue
                target=urljoin(url,a['href']);title=a.get_text(' ',strip=True)
                c=self.candidate_from_url(target,title)
                if c.external_id in seen:continue
                if not title:raise ValueError('concurso sem título público')
                seen.add(c.external_id);result.candidates.append(c)
        result.truncated=len(result.candidates)>limit
        result.candidates=result.candidates[:limit]
        result.diagnostics=['Seções públicas de inscrições abertas e em andamento; exaustividade ainda exige comprovação.']
        return result

    def validate_document_url(self,url,candidate):
        self._check_candidate(candidate);p=self._destination(url);q=parse_qs(p.query,keep_blank_values=True)
        if (p.path!='/ConcursoDownloadArquivo.aspx' or set(q)!={'ID','ID2'} or q['ID2']!=['1']
                or len(q['ID'])!=1 or not re.fullmatch(r'[A-Za-zÀ-ÿ0-9_ .()-]{1,220}\.pdf',q['ID'][0],re.I)
                or '..' in q['ID'][0]):raise ValueError('documento IDIB fora do contrato')

    def document_request_headers(self,url,candidate):
        if urlsplit(url).path!='/ConcursoDownloadArquivo.aspx':return {}
        self.validate_document_url(url,candidate)
        return {'Referer':candidate.detail_url_observed}

    def documents(self,html,candidate):
        self._check_candidate(candidate);docs=[];seen=set()
        for a in visible_soup(html).select('a[href]'):
            if 'ConcursoDownloadArquivo.aspx' not in a['href']:continue
            url=urljoin(candidate.detail_url_observed,a['href']);self.validate_document_url(url,candidate)
            if url in seen:continue
            seen.add(url);title=a.get_text(' ',strip=True);kind=document_kind(title,url)
            if re.search(r'retifica|aditivo|errata',folded(title)):kind='retificacao'
            elif 'prorrog' in folded(title):kind='prorrogacao'
            docs.append(DocumentCandidate(doc_id='idib-'+hashlib.sha256(url.encode()).hexdigest()[:16],
                title=title,url_requested=url,kind=kind))
        return docs

    def confirm_identity(self,candidate,html,url):
        soup=self._check_detail(candidate,html,url)
        if not title_is_corroborated(candidate.title_observed or '',soup.get_text(' ',strip=True)):
            raise ValueError('título IDIB não corroborado')
        if not self.documents(html,candidate):raise ValueError('manifesto IDIB ausente')
