"""FAPEG public call tables alongside the SEAD personnel selection portal."""
import hashlib
import re
from datetime import datetime,timezone
from urllib.parse import urlsplit,urljoin,unquote
from app.tenderproof.batch99_regions_adapters import FapegSelectionAdapter
from app.tenderproof.contracts import DiscoveredCandidate,DocumentCandidate
from app.tenderproof.pilot_adapters import visible_soup,folded
from app.tenderproof.source_adapter_base import ListingPage
from app.tenderproof.security import DestinationBlocked

RESEARCH_LISTINGS=tuple('https://goias.gov.br/fapeg/editais/'+state+'/' for state in ('inscricoes-abertas','em-andamento','encerrados'))


class FapegAdapter(FapegSelectionAdapter):
    implementation_state='partial'
    implementation_scope='SEAD personnel selections and official FAPEG open/in-progress/closed call tables; publication and ambiguous legacy links pending.'

    def __init__(self):
        super().__init__()
        self.allowed_hosts=(*self.allowed_hosts,'goiasgovbr-my.sharepoint.com')
        self.listing_urls=(*self.listing_urls,*RESEARCH_LISTINGS)
        self.ready_selectors=(*self.ready_selectors,'article table.planilhaview')

    def _research(self,url):return urlsplit(url).hostname=='goias.gov.br' and urlsplit(url).path.startswith('/fapeg/')

    def acquire_listing(self,url,fetch):
        from bs4 import BeautifulSoup,UnicodeDammit
        self.validate_listing_url(url)
        result=fetch(url,self.validate_listing_url,2*1024*1024)
        html=UnicodeDammit(result.content,is_html=True).unicode_markup or ''
        if url not in RESEARCH_LISTINGS:return html
        soup=BeautifulSoup(html,'html.parser');attempts=0
        for anchor in soup.select('article .entry-content table.planilhaview tbody td a[href]'):
            observed=urljoin(url,anchor['href'])
            match=re.fullmatch(r'https://goias\.gov\.br/fapeg/\?p=([1-9][0-9]{0,8})&preview=true',observed)
            if not match:continue
            attempts+=1
            if attempts>20:
                anchor['data-resolution-pending']='Limite de resoluções públicas por listagem';continue
            public='https://goias.gov.br/fapeg/?p='+match[1]
            def validate(target):
                self._destination(target)
                if target!=public:self.validate_detail_url(target)
            try:
                resolved=fetch(public,validate,2*1024*1024)
                self.validate_detail_url(resolved.url_final)
                detail=UnicodeDammit(resolved.content,is_html=True).unicode_markup or ''
                articles=BeautifulSoup(detail,'html.parser').select('article')
                if len(articles)!=1 or articles[0].get('id')!='post-'+match[1]:
                    raise ValueError('Artigo público diverge do identificador da prévia')
                row=anchor.find_parent('tr');cells=row.find_all('td',recursive=False)
                number=cells[0].get_text(' ',strip=True)
                if not re.fullmatch(r'\d{1,3}/20\d{2}',number):raise ValueError('Número da chamada pendente')
                candidate=self.candidate_from_url(resolved.url_final,number+' | '+cells[3].get_text(' ',strip=True))
                self._research_article(candidate,detail,resolved.url_final)
                anchor['data-observed-preview-url']=observed
                anchor['data-public-resolution-url']=public
                anchor['data-public-article-sha256']=hashlib.sha256(resolved.content).hexdigest()
                anchor['href']=resolved.url_final
            except Exception as exc:
                anchor['data-resolution-pending']=type(exc).__name__+': '+str(exc)
        return str(soup)

    def validate_listing_url(self,url):
        if url in RESEARCH_LISTINGS:self._destination(url);return
        return super().validate_listing_url(url)

    def validate_detail_url(self,url):
        if not self._research(url):return super().validate_detail_url(url)
        p=self._destination(url)
        if p.query or not re.fullmatch(r'/fapeg/[a-z0-9][a-z0-9_-]+/',p.path) or url in RESEARCH_LISTINGS:
            raise ValueError('Detalhe de chamada FAPEG inválido')

    def candidate_from_url(self,url,title=None):
        if not self._research(url):return super().candidate_from_url(url,title)
        self.validate_detail_url(url)
        return DiscoveredCandidate(candidate_id='fapeg-call-'+hashlib.sha256(url.encode()).hexdigest()[:24],source=self.source,external_id=url,title_observed=title,detail_url_observed=url,observed_at=datetime.now(timezone.utc))

    def parse_listing(self,html,url,limit=200):
        if url not in RESEARCH_LISTINGS:return super().parse_listing(html,url,limit)
        self.validate_listing_url(url)
        if type(limit)is not int or not 1<=limit<=10000:raise ValueError('Limite inválido')
        soup=visible_soup(html);tables=soup.select('article .entry-content table.planilhaview')
        if len(tables)!=1:raise ValueError('Tabela de chamadas ausente ou ambígua')
        headings=[folded(c.get_text(' ',strip=True)) for c in tables[0].select('thead tr')[0].find_all('th',recursive=False)]
        if headings[:5]!=['no','tipo','origem','descricao','link']:raise ValueError('Colunas de chamadas divergentes')
        candidates={};pending=[]
        for row in tables[0].select('tbody tr'):
            cells=row.find_all('td',recursive=False)
            if not any(c.get_text(' ',strip=True) or c.select('a[href]') for c in cells):continue
            if len(cells) not in (5,7) or any(c.get_text(' ',strip=True) or c.select('a[href]') for c in cells[5:]):
                pending.append('Linha com colunas não reconhecidas');continue
            links=cells[4].select('a[href]');raw_number=cells[0].get_text(' ',strip=True)
            normal=re.fullmatch(r'(?:Edital\s+)?(\d{1,3})/(20\d{2})\*?',raw_number,re.I)
            reverse=re.fullmatch(r'(20\d{2})/(\d{1,3})',raw_number)
            number=normal[1]+'/'+normal[2] if normal else reverse[2]+'/'+reverse[1] if reverse else None
            if len(links)!=1 or number is None:
                pending.append('Identidade ou endereço de chamada pendente: '+raw_number);continue
            target=urljoin(url,links[0]['href'])
            title=number.rstrip('*')+' | '+' — '.join(c.get_text(' ',strip=True) for c in cells[1:4] if c.get_text(' ',strip=True))
            try:
                if not self._research(target):raise ValueError('Endereço externo')
                candidate=self.candidate_from_url(target,title)
            except (ValueError,DestinationBlocked):
                pending.append('Endereço de chamada pendente: '+target);continue
            if target in candidates and candidates[target].title_observed!=title:
                pending.append('Endereço compartilhado por linhas divergentes: '+target);continue
            candidates[target]=candidate
        return ListingPage(candidates=list(candidates.values())[:limit],truncated=bool(pending) or len(candidates)>limit,diagnostics=pending,next_urls=[u for u in RESEARCH_LISTINGS if u!=url])

    def _number(self,candidate):
        match=re.match(r'(\d{1,3})/(20\d{2})\s*\|',candidate.title_observed or '')
        if not match:raise ValueError('Número da chamada não preservado na descoberta')
        return int(match[1]),match[2]

    def _research_article(self,candidate,html,url):
        self.validate_detail_url(url)
        if candidate.source!=self.source or candidate.external_id!=url or candidate.detail_url_observed!=url:raise ValueError('Identidade de chamada divergente')
        number,year=self._number(candidate)
        soup=visible_soup(html);articles=soup.select('article')
        if len(articles)!=1:raise ValueError('Artigo de chamada ausente ou ambíguo')
        title=articles[0].select_one('.entry-title');body=articles[0].select_one('.entry-content')
        if title is None or body is None:raise ValueError('Cabeçalho ou conteúdo da chamada ausente')
        ids={(int(n),y) for n,y in re.findall(r'\b(\d{1,3})\s*[/.-]\s*(20\d{2})\b',title.get_text(' ',strip=True))}
        if (number,year) not in ids:raise ValueError('Número da chamada diverge do cabeçalho')
        return body

    def confirm_identity(self,candidate,html,url):
        if not self._research(url):return super().confirm_identity(candidate,html,url)
        self._research_article(candidate,html,url)
        self.documents(html,candidate)

    def validate_document_url(self,url,candidate):
        if not self._research(candidate.detail_url_observed):return super().validate_document_url(url,candidate)
        self._check_candidate(candidate)
        if urlsplit(url).hostname=='goiasgovbr-my.sharepoint.com':
            from app.tenderproof.fapeg_workbook import share_folder
            share_folder(url);return
        p=self._destination(url);path=unquote(p.path)
        if p.hostname!='goias.gov.br' or p.query or not re.fullmatch(r'/fapeg/wp-content/uploads/(?:sites/\d+/)?\d{4}/\d{2}/[^/]+\.(?:pdf|docx?|xlsx?|odt)',path,re.I):
            raise ValueError('Documento de chamada fora do contrato FAPEG')

    def documents(self,html,candidate):
        if not self._research(candidate.detail_url_observed):return super().documents(html,candidate)
        body=self._research_article(candidate,html,candidate.detail_url_observed);docs={}
        for anchor in body.select('a[href]'):
            url=urljoin(candidate.detail_url_observed,anchor['href']);title=anchor.get_text(' ',strip=True);label=folded(title)
            if urlsplit(url).hostname=='goiasgovbr-my.sharepoint.com':
                self.validate_document_url(url,candidate)
                if not title:raise ValueError('Planilha sem rótulo observado')
                docs[url]=DocumentCandidate(doc_id='fapeg-workbook-'+hashlib.sha256((candidate.external_id+url).encode()).hexdigest()[:24],title=title,url_requested=url,kind='anexo',file_format='xlsx',reason_chosen='Planilha publicamente vinculada ao artigo; leitura e conferência pendentes.')
                continue
            if not re.search(r'\.(pdf|docx?|xlsx?|odt)$',urlsplit(url).path,re.I):
                raise ValueError('Link complementar exige classificação explícita: '+url)
            self.validate_document_url(url,candidate)
            kind='retificacao' if 'retific' in label or 'errata' in label else 'prorrogacao' if 'prorrog' in label else 'edital' if label.startswith(('edital','chamada publica')) else 'anexo' if 'anexo' in label else 'resultado' if 'resultado' in label else 'outro'
            if not title:raise ValueError('Documento sem rótulo')
            doc=DocumentCandidate(doc_id='fapeg-call-'+hashlib.sha256((candidate.external_id+url).encode()).hexdigest()[:24],title=title,url_requested=url,kind=kind,reason_chosen='Link no artigo oficial correspondente ao número da chamada; efeitos sujeitos a conferência.')
            if url in docs and docs[url].kind!=kind:raise ValueError('Papel documental conflitante')
            docs[url]=doc
        self.choose_document(list(docs.values()))
        return list(docs.values())

    def supplementary_documents(self,documents,selected):
        return [doc for doc in documents if doc.file_format=='xlsx' and (selected is None or doc.doc_id!=selected.doc_id)]

    def document_identity_ids(self,candidate,pages):
        if not self._research(candidate.detail_url_observed):return set(re.findall(self.document_identity_pattern,'\n'.join(p.text for p in pages),re.I))
        number,year=self._number(candidate)
        first=pages[0].text if pages else ''
        ids={(int(n),y) for n,y in re.findall(r'\b(\d{1,3})\s*[/.-]\s*(20\d{2})\b',first)}
        return {candidate.external_id} if (number,year) in ids and 'fapeg' in folded(first) else {'unconfirmed-fapeg-call'}
