"""Observed regional personnel selection contracts; no funding-only placeholders."""
from datetime import datetime, timezone
import re
import hashlib
from urllib.parse import parse_qs, urlsplit, unquote
from app.tenderproof.contracts import DiscoveredCandidate, DocumentCandidate
from app.tenderproof.pilot_adapters import PilotHTMLAdapter, visible_soup, folded, document_kind
from app.tenderproof.validation import title_is_corroborated


class FapescSelectionAdapter(PilotHTMLAdapter):
    """Official delegated 2022 archive, explicitly narrower than all FAPESC calls."""
    candidate_selector = 'a[href*="go=edital"]'
    ready_selectors = (candidate_selector,)
    listing_query_keys = ()
    document_hosts = ('fapesc.fepese.org.br',)
    document_identity_pattern = r'fapesc\.fepese\.org\.br/\?go=edital[^\s]*[&]edital=(\d+)'

    def __init__(self):
        super().__init__('fapesc_selection', 'https://fapesc.fepese.org.br/')

    def validate_detail_url(self, url):
        p = self._destination(url)
        q = parse_qs(p.query, keep_blank_values=True)
        if p.path != '/' or set(q) != {'go', 'mn', 'edital'} or q['go'] != ['edital'] or q['edital'] != ['1'] or q['mn'] != ['1151b3eab3b069d5112ccae1943307c4']:
            raise ValueError('detalhe fora do concurso FAPESC observado')

    def candidate_from_url(self, url, title=None):
        self.validate_detail_url(url)
        return DiscoveredCandidate(candidate_id=self.source+'-1', source=self.source, external_id='1', title_observed=title, detail_url_observed=url, observed_at=datetime.now(timezone.utc))

    def _title(self, anchor):
        root = anchor
        while root.parent is not None:
            root = root.parent
        title = root.select_one('title')
        return title.get_text(' ', strip=True) if title else None

    def _candidates(self, html, url, limit):
        soup = visible_soup(html)
        text = folded(soup.get_text(' ', strip=True))
        if not all(t in text for t in ('fapesc', 'concurso publico', 'cargos efetivos')):
            return []
        return super()._candidates(html, url, limit)

    def document_route(self, p):
        return p.path == '/' and parse_qs(p.query).get('go') == ['download']

    def validate_document_url(self, url, candidate):
        self._check_candidate(candidate)
        p = self._destination(url)
        q = parse_qs(p.query, keep_blank_values=True)
        if p.path != '/' or set(q) != {'go', 'arquivo', 'inline'} or q['go'] != ['download'] or q['inline'] != ['1'] or len(q['arquivo']) != 1 or not re.fullmatch(r'(?:2022_001_CP_FAPESC|TA_0[12]_FAPESC_Ed_001)\.pdf', q['arquivo'][0]):
            raise ValueError('documento fora do arquivo FAPESC001/2022 observado')

    def confirm_identity(self, candidate, html, url):
        soup = self._check_detail(candidate, html, url)
        title = soup.select_one('title')
        if title is None or folded(title.get_text(' ', strip=True)) != '2022 - fapesc':
            raise ValueError('cabeçalho FAPESC incompatível')
        if candidate.title_observed and not title_is_corroborated(candidate.title_observed, title.get_text(' ', strip=True)):
            raise ValueError('título FAPESC incompatível')
        docs = self.documents(html, candidate)
        if not any(folded(d.title) == 'edital 001/2022' for d in docs):
            raise ValueError('edital FAPESC001/2022 ausente ou divergente')


BATCH99_REGIONS_ADAPTERS = {'fapesc_selection': FapescSelectionAdapter()}


class FapespaSelectionArchiveAdapter(PilotHTMLAdapter):
    """Reviewed PSS001/2025 archive. Original is explicit reviewed evidence,
    NOT asserted to have been discovered in today's calls HTML.
    """
    ready_selectors = ('strong',)
    document_hosts = ('www.fapespa.pa.gov.br',)
    listing_query_keys = ()
    document_identity_pattern = r'edital\s+n[º°o]?[.\s]*(\d{3}/\d{4})\s+pss/fapespa'
    reviewed_original_url = 'https://www.fapespa.pa.gov.br/wp-content/uploads/2025/07/EDITAL-001-2025-VIGENTE.pdf'
    reviewed_original_sha256 = 'b7c6e61108b99fee196e62f08ad752e34bd7b139c09991986f7bd75e82b8cd21'
    reviewed_evidence = 'tests/fixtures/tenderproof_batch99_regions/pdf-manifest.json'

    def __init__(self):
        super().__init__('fapespa_selection', 'https://www.fapespa.pa.gov.br/chamadas/')

    def validate_detail_url(self, url):
        self.validate_listing_url(url)

    def candidate_from_url(self, url, title=None):
        self.validate_detail_url(url)
        return DiscoveredCandidate(candidate_id=self.source+'-001-2025', source=self.source, external_id='001/2025', title_observed=title, detail_url_observed=url, observed_at=datetime.now(timezone.utc))

    def _section(self, html):
        soup=visible_soup(html)
        matches=[n for n in soup.select('p strong') if re.match(r'^edital n.*001/2025 pss/fapespa', folded(n.get_text(' ',strip=True)))]
        if len(matches)!=1:
            raise ValueError('seção inequívoca PSS/FAPESPA001/2025 ausente')
        header=matches[0]
        if 'contratacao temporaria' not in folded(header.get_text(' ',strip=True)):
            raise ValueError('seção não comprova contratação de pessoas')
        siblings=[]
        for n in header.parent.next_siblings:
            if getattr(n,'name',None) and n.select_one('strong'):
                break
            siblings.append(str(n))
        return header, visible_soup(''.join(siblings))

    def _candidates(self, html, url, limit):
        try: header,_=self._section(html)
        except ValueError: return []
        return [self.candidate_from_url(url,header.get_text(' ',strip=True))]

    def parse_listing(self, html, url, limit=200):
        page=super().parse_listing(html,url,limit)
        page.diagnostics.append('arquivo revisado PSS001/2025; edital original de evidência oficial externa, não descoberto na listagem atual')
        return page

    def validate_document_url(self, url, candidate):
        self._check_candidate(candidate)
        p=self._destination(url)
        if p.query or not re.fullmatch(r'/wp-content/uploads/2025/07/(?:EDITAL-001-2025-VIGENTE|6\.-RESULTADO-PRELIMINAR-APOS-ANALISE-CURRICULAR|7\.-CRONOGRAMA-ALTERADO|9\.-RESULTADO-FINAL-APOS-ANALISE-CURRICULAR|10\.-CONVOCACAO-PARA-ENTREVISTA|11\.-RESULTADO-FINAL-PSS-001\.2025-FAPESPA-1)\.pdf',p.path):
            raise ValueError('documento fora do arquivo revisado PSS001/2025')

    def documents(self, html, candidate):
        self._check_candidate(candidate)
        _,section=self._section(html)
        docs=[]
        for a in section.select('a[href]'):
            if not a['href'].endswith('.pdf'):continue
            self.validate_document_url(a['href'],candidate)
            title=a.get_text(' ',strip=True)
            docs.append(DocumentCandidate(doc_id=self.source+'-'+hashlib.sha256(a['href'].encode()).hexdigest()[:16],title=title,url_requested=a['href'],kind=document_kind(title,a['href'])))
        if not docs:
            raise ValueError('seção sem publicações que corroborem arquivo revisado')
        docs.append(DocumentCandidate(doc_id=self.source+'-reviewed-original-001-2025',title='Edital 001/2025 PSS/FAPESPA',url_requested=self.reviewed_original_url,kind='edital'))
        return docs

    def confirm_identity(self,candidate,html,url):
        self._check_detail(candidate,html,url)
        heading,_=self._section(html)
        if candidate.title_observed and not title_is_corroborated(candidate.title_observed,heading.get_text(' ',strip=True)):
            raise ValueError('título PSS/FAPESPA incompatível')
        self.documents(html,candidate)

BATCH99_REGIONS_ADAPTERS['fapespa_selection'] = FapespaSelectionArchiveAdapter()


class FapegSelectionAdapter(PilotHTMLAdapter):
    export_contract = {
        'exportEditalPdf': ('exportarEditalPdf', False),
        'exportarRetificacaoPdf': ('exportarRetificacaoPdf', False),
        'exportArquivoFaseDinamica': ('downloadArquivoFaseDinamica', False),
        'exportEditalEntrevista': ('exportarEditalEntrevista', False),
        'exportResultadoPdf': ('exportarResultadoCertamePdf', True),
        'exportAtaPdf': ('exportarAtaCertamePdf', True),
    }
    candidate_selector = 'a[href*="selecao.go.gov.br/edital/"]'
    ready_selectors = (candidate_selector,)
    listing_query_keys = ()
    document_hosts = ('selecao.go.gov.br',)
    document_identity_pattern = r'edital n[ºo°]?[.\s]*(\d{1,6}/20\d{2})[^\n]{0,15}sead/fapeg'
    detail_pattern = r'/edital/edital-n-(\d{1,6})(20\d{2})[–-]seadfapeg_processo-seletivo-simplificado_fapeg\|([1-9][0-9]{0,8})'

    def __init__(self):
        super().__init__('fapeg_selection','https://goias.gov.br/administracao/processos-seletivos-simplificados/',document_hosts=self.document_hosts)
        self._observed_exports = {}

    def _title(self, anchor):
        return anchor.get_text(' ',strip=True)

    def in_scope(self,title,url):
        return 'fapeg' in folded(title) and 'processo seletivo' in folded(title)

    def validate_detail_url(self,url):
        p=self._destination(url)
        if p.hostname!='selecao.go.gov.br' or p.query or not re.fullmatch(self.detail_pattern,unquote(p.path)):
            raise ValueError('detalhe fora do contrato de seleção SEAD/FAPEG')

    def candidate_from_url(self,url,title=None):
        self.validate_detail_url(url)
        number,year,identifier=re.fullmatch(self.detail_pattern,unquote(urlsplit(url).path)).groups()
        return DiscoveredCandidate(candidate_id=self.source+'-'+identifier,source=self.source,external_id=number+'/'+year,title_observed=title,detail_url_observed=url,observed_at=datetime.now(timezone.utc))

    def validate_document_url(self,url,candidate):
        self._check_candidate(candidate)
        p=self._destination(url)
        if p.hostname!='selecao.go.gov.br' or p.path not in {'/'+v[0] for v in self.export_contract.values()} or p.query:
            raise ValueError('endpoint fora do contrato documental FAPEG')

    def validate_document_request(self,document,candidate):
        self.validate_document_url(document.url_requested,candidate)
        request=document.acquisition_request
        if request is None or request.method!='POST' or request.content_type!='application/x-www-form-urlencoded':
            raise ValueError('exportação FAPEG exige POST público observado')
        signature=(document.doc_id,document.url_requested,request.body,document.kind,document.title)
        if signature not in self._observed_exports.get(candidate.detail_url_observed,set()):
            raise ValueError('corpo POST não corresponde à identidade documental observada')

    def documents(self,html,candidate):
        from app.tenderproof.contracts import DocumentAcquisitionRequest
        self._check_candidate(candidate)
        soup=visible_soup(html)
        headings=' '.join(n.get_text(' ',strip=True) for n in soup.select('h1,h2,h3'))
        identity=re.search(r'edital\s+n[ºo°]?[.\s]*(\d{1,6}/20\d{2})\s*[–-]?\s*sead/fapeg',folded(headings))
        if not identity or identity[1]!=candidate.external_id:
            raise ValueError('cabeçalho FAPEG incompatível')
        fields=soup.select('input#idEditalCertameFixo')
        expected_id=re.fullmatch(self.detail_pattern,unquote(urlsplit(candidate.detail_url_observed).path))[3]
        if len(fields)!=1 or fields[0].get('value')!=expected_id:
            raise ValueError('identificador do certame FAPEG divergente')
        contest_id=fields[0]['value']
        docs=[]
        for button in soup.select('tr button[data-id]'):
            row=button.find_parent('tr')
            cells=row.find_all('td',recursive=False)
            if len(cells)!=3:raise ValueError('linha documental FAPEG mudou')
            description=cells[1].get_text(' ',strip=True)
            identifier=button['data-id']
            classes=[c for c in button.get('class',[]) if c.startswith('export')]
            if len(classes)!=1 or classes[0] not in self.export_contract or not re.fullmatch(r'[1-9][0-9]{0,8}',identifier):
                raise ValueError('botão documental FAPEG não reconhecido')
            function,phase=self.export_contract[classes[0]]
            original=folded(description)=='publicacao edital' and function=='exportarEditalPdf'
            title='Edital '+candidate.external_id+' SEAD/FAPEG' if original else description
            kind='edital' if original else 'consolidado' if function=='exportarEditalPdf' else 'retificacao' if function=='exportarRetificacaoPdf' else 'resultado' if classes[0]=='exportResultadoPdf' or 'homologacao' in folded(description) else 'outro'
            body=contest_id+','+identifier if phase else identifier+',0'
            doc=DocumentCandidate(doc_id=f'fapeg-{function}-{identifier}',title=title,url_requested='https://selecao.go.gov.br/'+function,kind=kind,acquisition_request=DocumentAcquisitionRequest(body=body))
            docs.append(doc)
        if sum(d.kind=='edital' for d in docs)!=1 or len({d.doc_id for d in docs})!=len(docs):
            raise ValueError('manifesto FAPEG duplicado ou sem original único')
        key=candidate.detail_url_observed
        self._observed_exports.pop(key,None)
        self._observed_exports[key]={(d.doc_id,d.url_requested,d.acquisition_request.body,d.kind,d.title) for d in docs}
        while len(self._observed_exports)>128:self._observed_exports.pop(next(iter(self._observed_exports)))
        for doc in docs:self.validate_document_request(doc,candidate)
        return docs

    def choose_document(self,docs):
        originals=[d for d in docs if d.kind=='edital']
        if len(originals)!=1:raise ValueError('original FAPEG ausente ou ambíguo')
        return originals[0]

    def confirm_identity(self,candidate,html,url):
        soup=self._check_detail(candidate,html,url)
        headings=' '.join(n.get_text(' ',strip=True) for n in soup.select('h1,h2,h3'))
        normalized_heading=headings.replace('–',' ').replace('—',' ')
        if candidate.external_id not in headings or 'sead/fapeg' not in folded(headings) or not title_is_corroborated(candidate.title_observed or 'FAPEG',normalized_heading):
            raise ValueError('cabeçalho FAPEG incompatível')
        if not self.documents(html,candidate):raise ValueError('detalhe sem manifesto edital FAPEG')

BATCH99_REGIONS_ADAPTERS['fapeg_selection']=FapegSelectionAdapter()
