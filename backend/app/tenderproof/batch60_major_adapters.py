"""Five major portals, based on official HTML/JS/API captures of 2026-09-08."""
from datetime import datetime,timezone
import hashlib
import json
import re
from urllib.parse import parse_qs,urljoin,urlsplit,urldefrag
from app.tenderproof.contracts import DiscoveredCandidate,DocumentCandidate
from app.tenderproof.pilot_adapters import PilotHTMLAdapter,visible_soup,folded,document_kind
from app.tenderproof.source_adapter_base import ListingPage
from app.tenderproof.validation import title_is_corroborated


def candidate(source,url,key,title):
    return DiscoveredCandidate(candidate_id=f'{source}-{key}',external_id=key,source=source,
        detail_url_observed=url,title_observed=title,observed_at=datetime.now(timezone.utc))


def document(source,title,url):
    kind=document_kind(title,url)
    if any(word in folded(title) for word in ('reabert','prorrog','retific')):kind='outro'
    return DocumentCandidate(doc_id=source+'-'+hashlib.sha256(url.encode()).hexdigest()[:18],title=title,kind=kind,url_requested=url)


class FCCAdapter(PilotHTMLAdapter):
    source='fcc_open'
    detail_pattern=r'/concursos/([a-z0-9]+)/index\.html'
    document_identity_pattern=r'/concursos/([a-z0-9]+)/'
    candidate_selector='.textoInstituicao2 a[href]'
    ready_selectors=('.textoInstituicao2 a[href]',)
    def __init__(self):super().__init__(self.source,'https://www.concursosfcc.com.br/concursoAndamento.html')
    def _title(self,a):return a.get_text(' ',strip=True)
    def _scope_title(self,a):return a.parent.parent.get_text(' ',strip=True)
    def document_route(self,p):return p.path.startswith('/concursos/')
    def validate_document_url(self,url,c):
        self._check_candidate(c);p=self._destination(url)
        if p.hostname!=self.portal_host or p.query or not re.fullmatch('/concursos/'+re.escape(c.external_id)+r'/[^/]+\.pdf',p.path,re.I):raise ValueError('PDF FCC fora do concurso')
    def confirm_identity(self,c,html,url):
        s=self._check_detail(c,html,url)
        if not c.title_observed or not title_is_corroborated(c.title_observed,' '.join(n.get_text(' ',strip=True) for n in s.select('.textoInstituicao'))):raise ValueError('título FCC incompatível')
    def documents(self,html,c):
        s=self._check_detail(c,html,c.detail_url_observed);result=[];seen=set()
        for a in s.select('a[href]'):
            url=urljoin(c.detail_url_observed,a['href']);p=urlsplit(url)
            if p.hostname==self.portal_host and p.path=='/rybena/web/index.html':
                q=parse_qs(p.query,keep_blank_values=True)
                if set(q)!={'file'} or len(q['file'])!=1:raise ValueError('wrapper documental FCC ambíguo')
                url=q['file'][0]
            if '.pdf' not in urlsplit(url).path.lower():continue
            self.validate_document_url(url,c)
            if url not in seen:result.append(document(self.source,a.get_text(' ',strip=True),url));seen.add(url)
        return result


class AvaliaAdapter(PilotHTMLAdapter):
    source='avalia_open'
    candidate_selector='h4 a[href*="concurso.jsp?id="]'
    ready_selectors=('h4 a[href*="concurso.jsp?id="]',)
    document_identity_pattern=r'concurso\.jsp\?id=(\d+)'
    document_hosts=('arquivos-site.avalia.org.br',)
    def __init__(self):super().__init__(self.source,'https://www2.avalia.org.br/concursos.jsp',document_hosts=('arquivos-site.avalia.org.br',))
    def _title(self,a):return a.get_text(' ',strip=True)
    def validate_detail_url(self,url):
        p=self._destination(url);q=parse_qs(p.query,keep_blank_values=True)
        if p.hostname!=self.portal_host or p.path!='/concurso.jsp' or set(q)!={'id'} or len(q['id'])!=1 or not re.fullmatch(r'\d+',q['id'][0]):raise ValueError('identidade Avalia inválida')
    def candidate_from_url(self,url,title=None):
        self.validate_detail_url(url);return candidate(self.source,url,parse_qs(urlsplit(url).query)['id'][0],title)
    def _scope_title(self,a):return a.get_text(' ',strip=True)
    def in_scope(self,title,url):
        return super().in_scope(title,url) and not any(x in folded(title) for x in ('termo de fomento','ganhe o mundo'))
    def confirm_identity(self,c,html,url):
        s=self._check_detail(c,html,url)
        if not c.title_observed or not title_is_corroborated(c.title_observed,' '.join(n.get_text(' ',strip=True) for n in s.select('h5.card-title'))):raise ValueError('título Avalia incompatível')
    def document_route(self,p):return p.path.startswith('/publicacoes/')
    def validate_document_url(self,url,c):
        self._check_candidate(c);p=self._destination(url)
        if p.hostname!='arquivos-site.avalia.org.br' or p.query or not re.fullmatch(r'/publicacoes/[a-f0-9-]{36}\.pdf',p.path,re.I):raise ValueError('diretório documental Avalia inválido')
    def _document_title(self,a):return re.sub(r'^\d{2}/\d{2}/\d{4}\s*-\s*','',a.get_text(' ',strip=True))


class IBAMAdapter(PilotHTMLAdapter):
    source='ibam_open'
    document_identity_pattern=r'inscricao\.asp\?[^\s]*cod=(\d+)'
    ready_selectors=('.card h4',)
    def __init__(self):super().__init__(self.source,'https://www.ibam-concursos.org.br',listing_paths=('','/','/default.asp'))
    def validate_detail_url(self,url):
        base,fragment=urldefrag(url);self.validate_listing_url(base)
        if not re.fullmatch(r'docs-\d+',fragment):raise ValueError('IBAM requer âncora documental observada')
    def candidate_from_url(self,url,title=None):
        self.validate_detail_url(url);return candidate(self.source,url,urlsplit(url).fragment.removeprefix('docs-'),title)
    def parse_listing(self,html,url,limit=200):
        self.validate_listing_url(url)
        if not 1<=limit<=10000:raise ValueError('limite inválido')
        if len(html.encode('utf-8'))>2*1024*1024:raise ValueError('HTML IBAM excede limite')
        s=visible_soup(html);found=[]
        for card in s.select('.card'):
            h=card.select_one('h4');anchor=card.select_one('[data-bs-target^="#docs-"]')
            if not h or not anchor:continue
            target=anchor['data-bs-target']
            if not re.fullmatch(r'#docs-\d+',target) or not card.select_one(target):continue
            title=h.get_text(' ',strip=True)
            if self.in_scope(title,url):found.append(self.candidate_from_url(urldefrag(url)[0]+target,title))
        repeated={c.external_id for c in found if sum(x.external_id==c.external_id for x in found)>1}
        found=[c for c in found if c.external_id not in repeated]
        return ListingPage(candidates=found[:limit],truncated=len(found)>limit or bool(repeated),
            diagnostics=['Seções IBAM duplicadas excluídas: '+', '.join(sorted(repeated))] if repeated else [])
    def _section(self,html,c):
        self._check_candidate(c);s=visible_soup(html)
        nodes=s.select('#docs-'+c.external_id)
        if len(nodes)!=1:raise ValueError('seção IBAM ausente ou duplicada')
        card=nodes[0].find_parent(class_='card');h=card.select_one('h4') if card else None
        if not h or not c.title_observed or not title_is_corroborated(c.title_observed,h.get_text(' ',strip=True)):raise ValueError('título da seção IBAM incompatível')
        if not card.select_one('[data-bs-target="#docs-'+c.external_id+'"]'):raise ValueError('âncora IBAM não corroborada')
        return nodes[0]
    def confirm_identity(self,c,html,url):
        self.validate_detail_url(url)
        if self.candidate_from_url(url).external_id!=c.external_id:raise ValueError('seção IBAM de outro concurso')
        self._section(html,c)
    def validate_document_url(self,url,c):
        self._check_candidate(c);p=self._destination(url)
        if p.hostname!=self.portal_host or p.query or not re.fullmatch(r'/documento/[^/]+\.pdf',p.path,re.I):raise ValueError('PDF IBAM fora do diretório oficial')
    def documents(self,html,c):
        result=[]
        for a in self._section(html,c).select('a[href]'):
            url=urljoin(c.detail_url_observed,a['href'])
            if not urlsplit(url).path.lower().endswith('.pdf'):continue
            self.validate_document_url(url,c);result.append(document(self.source,a.get_text(' ',strip=True),url))
        return result


class CebraspeAdapter(PilotHTMLAdapter):
    source='cebraspe_open'
    detail_pattern=r'/cebraspe/eventos/([A-Za-z0-9_]+)'
    document_identity_pattern=r'/concursos/([A-Za-z0-9_]+)/'
    api='https://apis.cebraspe.org.br/cebraspe/eventos'
    def document_identity_ids(self,c,pages):
        from app.tenderproof.cebraspe_identity import PDF_EVENT_URL
        ids=set(re.findall(PDF_EVENT_URL,'\n'.join(p.text for p in pages),re.I))
        return {c.external_id if v.casefold()==c.external_id.casefold() else v for v in ids}

    def document_title_corroborated(self,c,pages):
        from app.tenderproof.cebraspe_identity import masthead
        return masthead(c,pages) is not None

    def __init__(self):super().__init__(self.source,self.api+'/tipo/concursos/',document_hosts=('cdn.cebraspe.org.br',))
    @staticmethod
    def _json(html):
        if len(html.encode())>2*1024*1024:raise ValueError('JSON Cebraspe excede limite')
        try:return json.loads(html.lstrip('\ufeff'))
        except ValueError:visible_soup(html);raise ValueError('Cebraspe requer JSON da API observada') from None
    def parse_listing(self,html,url,limit=200):
        self.validate_listing_url(url)
        if not 1<=limit<=10000:raise ValueError('limite inválido')
        data=self._json(html)
        if not isinstance(data,list):raise ValueError('grupos Cebraspe inválidos')
        found=[];seen=set();ambiguous=set()
        for group in data:
            if not isinstance(group,dict) or not isinstance(group.get('eventos'),list) or not isinstance(group.get('faseEvento'),str):raise ValueError('grupo Cebraspe incompleto')
            for row in group['eventos']:
                if not isinstance(row,dict) or row.get('eventoTipo')!='concursos' or not isinstance(row.get('eventoURL'),str) or not isinstance(row.get('eventoNomeAbreviado'),str):raise ValueError('identidade Cebraspe inválida')
                c=self.candidate_from_url(self.api+'/'+row['eventoURL'],row['eventoNomeAbreviado'])
                if c.external_id in seen:
                    ambiguous.add(c.external_id)
                    continue
                seen.add(c.external_id)
                if self.in_scope(c.title_observed,c.detail_url_observed):found.append(c)
        found=[c for c in found if c.external_id not in ambiguous]
        return ListingPage(candidates=found[:limit],truncated=len(found)>limit or bool(ambiguous),empty_evidence='API retorna lista estruturalmente vazia' if not data else None,
            diagnostics=['Identidades repetidas excluídas para revisão: '+', '.join(sorted(ambiguous))] if ambiguous else [])
    def confirm_identity(self,c,html,url):
        self._check_candidate(c);self.validate_detail_url(url);row=self._json(html)
        # The API repeats an abbreviated title, which may consist only of short
        # acronyms (e.g. FAPE AL 26). Compare this structured field in full;
        # prose keyword matching intentionally discards such short words.
        observed=' '.join((c.title_observed or '').split()).casefold()
        abbreviated=row.get('eventoNomeAbreviado') if isinstance(row,dict) else None
        title_matches=isinstance(abbreviated,str) and bool(observed) and observed==' '.join(abbreviated.split()).casefold()
        if self.candidate_from_url(url).external_id!=c.external_id or not isinstance(row,dict) or row.get('eventoURL')!=c.external_id or row.get('eventoTipo')!='concursos' or not title_matches:raise ValueError('detalhe Cebraspe incompatível')
    def validate_document_url(self,url,c):
        self._check_candidate(c);p=self._destination(url)
        if p.hostname!='cdn.cebraspe.org.br' or p.query or not re.fullmatch('/concursos/'+re.escape(c.external_id)+r'/arquivos/[A-Za-z0-9_.-]+\.pdf',p.path,re.I):raise ValueError('documento Cebraspe de outro evento')
    def documents(self,html,c):
        self.confirm_identity(c,html,c.detail_url_observed);row=self._json(html);result=[]
        for field in ('arquivosEdital','arquivosGabarito'):
            docs=row.get(field)
            if docs is None:continue
            if not isinstance(docs,list):raise ValueError('lista documental Cebraspe inválida')
            for item in docs:
                if not isinstance(item,dict):raise ValueError('documento Cebraspe inválido')
                extension = item.get('tipoExtensaoArquivo')
                filename = item.get('nomeArquivo')
                if extension not in ('_.pdf', '_pdf'):
                    if isinstance(filename, str) and filename.lower().endswith('.pdf'):
                        raise ValueError('PDF Cebraspe com tipo ainda não interpretado')
                    if extension not in ('_doc', '_docx', '_.doc', '_.docx', '_html', '_.html'):
                        raise ValueError('formato documental Cebraspe não interpretado')
                    continue  # Non-PDF attachments remain in the preserved API response.
                if item.get('isGuid') is not False:raise ValueError('rota GUID Cebraspe ainda não homologada')
                url='https://cdn.cebraspe.org.br/concursos/'+c.external_id+'/arquivos/'+item['nomeArquivo']
                self.validate_document_url(url,c)
                doc=document(self.source,item['descricaoArquivo'],url)
                label=folded(doc.title)
                if 'retifica' in label or 'errata' in label:
                    doc.kind='retificacao'
                elif 'prorroga' in label:
                    doc.kind='prorrogacao'
                elif doc.kind=='edital' and re.search(r'\blocais\b.*\bprovas?\b',label):
                    doc.kind='outro'
                result.append(doc)
        return result


class CesgranrioAdapter(PilotHTMLAdapter):
    source='cesgranrio_open'
    detail_pattern=r'/api/PortalEventoConteudos/publico/(\d+)'
    document_identity_pattern=r'/eventos/(\d+)/'
    api='https://concursos.cesgranrio.org.br/api/PortalEventos'
    def __init__(self):super().__init__(self.source,self.api+'?nome=&status=&page=1&pageSize=10')
    def validate_listing_url(self,url):
        p=self._destination(url);q=parse_qs(p.query,keep_blank_values=True)
        if p.hostname!=self.portal_host or p.path!='/api/PortalEventos' or set(q)!={'nome','status','page','pageSize'} or q['nome']!=[''] or q['status']!=[''] or q['pageSize']!=['10'] or len(q['page'])!=1 or not re.fullmatch(r'[1-9]\d{0,4}',q['page'][0]):raise ValueError('listagem Cesgranrio fora da API observada')
    @staticmethod
    def _json(html):
        if len(html.encode('utf-8'))>2*1024*1024:raise ValueError('JSON Cesgranrio excede limite')
        try:body=json.loads(html)
        except ValueError:visible_soup(html);raise ValueError('Cesgranrio requer API JSON observada') from None
        if not isinstance(body,dict) or body.get('success') is not True:raise ValueError('resposta Cesgranrio incompleta')
        return body.get('data')
    def parse_listing(self,html,url,limit=200):
        self.validate_listing_url(url)
        if not 1<=limit<=10000:raise ValueError('limite inválido')
        data=self._json(html);page=int(parse_qs(urlsplit(url).query)['page'][0])
        if not isinstance(data,dict) or not isinstance(data.get('items'),list) or any(type(data.get(k)) is not int for k in ('currentPage','pageSize','totalPages','totalCount','nextPage')) or type(data.get('hasNextPage')) is not bool:raise ValueError('paginação Cesgranrio incompleta')
        count=data['totalCount'];pages=data['totalPages']
        if count<0 or data['currentPage']!=page or data['pageSize']!=10 or pages!=(count+9)//10 or page>max(1,pages) or data['hasNextPage']!=(page<pages) or data['nextPage']!=page+1 or len(data['items'])!=min(10,max(0,count-(page-1)*10)):raise ValueError('totais Cesgranrio incompatíveis')
        found=[];seen=set()
        for row in data['items']:
            if not isinstance(row,dict) or type(row.get('id')) is not int or row['id']<=0 or not isinstance(row.get('nomeFantasia'),str):raise ValueError('identidade Cesgranrio incompleta')
            key=str(row['id'])
            if key in seen:raise ValueError('identidade Cesgranrio duplicada')
            seen.add(key)
            scope=row['nomeFantasia']+' '+str(row.get('descricao',''))
            if row.get('exibirPortal') is True and row.get('tipoEvento')==1 and self.in_scope(scope,url) and re.search('concurso|seletiv|seleção|seleç',scope,re.I):
                found.append(self.candidate_from_url('https://concursos.cesgranrio.org.br/api/PortalEventoConteudos/publico/'+key,row['nomeFantasia']))
        return ListingPage(candidates=found[:limit],truncated=len(found)>limit,
            next_urls=[self.api+'?nome=&status=&page='+str(page+1)+'&pageSize=10'] if data['hasNextPage'] else [],
            empty_evidence='API pública sem eventos (totalCount=0)' if count==0 else None,
            terminal_evidence='Última página dos totais da API pública' if not data['hasNextPage'] else None)
    def confirm_identity(self,c,html,url):
        self._check_candidate(c);self.validate_detail_url(url)
        if self.candidate_from_url(url).external_id!=c.external_id:raise ValueError('evento Cesgranrio incompatível')
        # API eventoId incorrectly repeats content IDs (283 etc). Identity uses
        # the requested event route AND the exact event directory of each PDF.
        self.documents(html,c)
    def validate_document_url(self,url,c):
        self._check_candidate(c);p=self._destination(url);q=parse_qs(p.query,keep_blank_values=True)
        if p.hostname!=self.portal_host or not re.fullmatch('/media/gpoweb-prd-hibrido3/eventos/'+re.escape(c.external_id)+r'/conteudos/[a-f0-9-]{36}\.pdf',p.path,re.I):raise ValueError('arquivo Cesgranrio fora do evento')
        if q and (set(q)!={'sv','se','sr','sp','sig'} or any(len(v)!=1 or not v[0] for v in q.values()) or q['sr']!=['c'] or q['sp']!=['r']):raise ValueError('parâmetros documentais Cesgranrio fora do contrato')
    def documents(self,html,c):
        self._check_candidate(c);rows=self._json(html)
        if not isinstance(rows,list):raise ValueError('conteúdos Cesgranrio inválidos')
        result=[];seen=set()
        for row in rows:
            if not isinstance(row,dict) or row.get('publico') is not True or not isinstance(row.get('titulo'),str) or not isinstance(row.get('texto'),str):raise ValueError('conteúdo público Cesgranrio inválido')
            for a in visible_soup(row['texto']).select('a[href]'):
                url=a['href']
                if not urlsplit(url).path.lower().endswith('.pdf'):continue
                self.validate_document_url(url,c)
                if url not in seen:
                    doc=document(self.source,row['titulo'],url)
                    doc.doc_id=self.source+'-'+hashlib.sha256(url.split('?',1)[0].encode()).hexdigest()[:18]
                    result.append(doc);seen.add(url)
        if not result:raise ValueError('nenhum PDF associado ao evento Cesgranrio')
        return result


BATCH60_MAJOR_ADAPTERS=(IBAMAdapter(),FCCAdapter(),CebraspeAdapter(),CesgranrioAdapter(),AvaliaAdapter())
