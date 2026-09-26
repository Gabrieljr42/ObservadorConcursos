"""Four batch30 contracts observed on 2026-09-08 UTC; no coverage claim from registration."""
from __future__ import annotations
import base64
import json
import re
from datetime import datetime, timezone
from urllib.parse import parse_qs, unquote, urlsplit, urlencode
from app.tenderproof.contracts import DiscoveredCandidate
from app.tenderproof.pilot_adapters import PilotHTMLAdapter, document_kind, folded, visible_soup
from app.tenderproof.source_adapter_base import ListingPage, SourcePageBlocked
from app.tenderproof.validation import title_is_corroborated

BROWSER_UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'


class HeadingAdapter(PilotHTMLAdapter):
    """Title corroboration complements route identity; PDFs still require revalidation."""
    identity_selector = 'h1, h2'

    def confirm_identity(self, candidate, html, url):
        soup = self._check_detail(candidate, html, url)
        headings = ' '.join(node.get_text(' ', strip=True) for node in soup.select(self.identity_selector))
        if not candidate.title_observed or not title_is_corroborated(candidate.title_observed, headings):
            raise ValueError('título do concurso incompatível com detalhe')
        if not self.documents(html, candidate):
            raise ValueError('detalhe sem documento oficial associado')


class IBFCAdapter(HeadingAdapter):
    source = 'ibfc_open'
    # Observed rich-text titles spill outside an empty h2 into sibling p/h5
    # nodes. Keep corroboration inside the contest header, excluding document
    # lists, inscription metadata and unrelated headings elsewhere on the page.
    identity_selector = '.dados > h2, .dados > h2 ~ p:not([class]), .dados > h2 ~ h5'
    detail_pattern = r'/informacoes/(\d+)/?'
    document_identity_pattern = r'/informacoes/(\d+)/?'
    candidate_selector = 'a.lista-concurso[href]'
    ready_selectors = ('a.lista-concurso[href]', 'p.nenhum')
    listing_query_keys = ()
    document_hosts = ('servidor-arquivos.ibfc.org.br', 'anexos-r2.selecao.net.br', 'anexos.cdn.selecao.net.br')

    def __init__(self):
        super().__init__(self.source, 'https://concursos.ibfc.org.br/index/abertos/',
                         listing_paths=('/index/abertos/', '/index/1/', '/index/3/'), document_hosts=self.document_hosts)

    def _title(self, anchor):
        title = anchor.select_one('.texto_cliente')
        return title.get_text(' ',strip=True) if title else None

    def parse_listing(self, html, url, limit=200):
        page = super().parse_listing(html,url,limit)
        soup = visible_soup(html)
        marker = soup.select_one('p.nenhum')
        if not page.candidates and marker and folded(marker.get_text(' ',strip=True)) == 'nenhum item cadastrado.':
            page.empty_evidence = marker.get_text(' ',strip=True)
            page.terminal_evidence = 'marcador explícito IBFC nesta aba'
        return page

    def document_route(self, parts):
        return parts.path.startswith(('/arquivos-publicos/', '/uploads/747/concursos/'))

    def validate_document_url(self,url,candidate):
        self._check_candidate(candidate)
        parts = self._destination(url)
        if parts.query or not parts.path.lower().endswith('.pdf'):
            raise ValueError('rota documental IBFC inválida')
        if parts.hostname == 'servidor-arquivos.ibfc.org.br':
            if not re.fullmatch(r'/arquivos-publicos/[^/]+\.pdf', parts.path, re.I):
                raise ValueError('diretório documental IBFC incompatível')
        elif parts.hostname in self.document_hosts:
            if not re.fullmatch(r'/uploads/747/concursos/'+re.escape(candidate.external_id)+r'/anexos/[^/]+\.pdf', parts.path,re.I):
                raise ValueError('documento IBFC de outro concurso/tenant')
        else:
            raise ValueError('host documental IBFC incompatível')


class ADMTECAdapter(HeadingAdapter):
    source='admtec_open'
    # The portal migrated its public catalogue from the legacy encoded route
    # to WordPress-like slugs in 2026. Keep both observed contracts so old
    # captures remain replayable while current cards are discoverable.
    detail_pattern=r'/(?:concursos/publicacoes/([A-Za-z0-9=]+/[A-Za-z0-9=]+)|concurso/([A-Za-z0-9][A-Za-z0-9-]*))/?'
    document_identity_pattern=detail_pattern
    candidate_selector='a[href*="/concursos/publicacoes/"], a[href*="/concurso/"]'
    ready_selectors=('a[href*="/concursos/publicacoes/"], a[href*="/concurso/"]',)
    listing_query_keys=()
    document_hosts=('cdn-arquivo.concursos.srv.br', 'webapp412434.ip-45-56-76-193.cloudezapp.io')

    def __init__(self):
        super().__init__(self.source,'https://admtec.org.br/',document_hosts=self.document_hosts)

    def request_headers(self,url):
        return {'User-Agent':BROWSER_UA} if urlsplit(url).hostname=='admtec.org.br' else {}

    def candidate_from_url(self, url, title=None):
        self.validate_detail_url(url)
        match=re.fullmatch(self.detail_pattern, urlsplit(url).path)
        external=match.group(1) or match.group(2)
        return DiscoveredCandidate(candidate_id=f'{self.source}-{external}', external_id=external,
            source=self.source, title_observed=title, detail_url_observed=url,
            observed_at=datetime.now(timezone.utc))

    @staticmethod
    def decoded_ids(external):
        if external.startswith('concursos/publicacoes/'):
            external=external.split('/',2)[-1]
        try:
            parts=[base64.b64decode(part,validate=True).decode('ascii') for part in external.split('/')]
        except (ValueError,UnicodeError):
            raise ValueError('identidade ADMTEC não corresponde aos tokens observados') from None
        if len(parts)!=2 or any(not re.fullmatch(r'\d{1,8}',part) for part in parts):
            raise ValueError('identidade ADMTEC inválida')
        return parts

    def _title(self,anchor):
        card=anchor.find_parent(class_='concurso')
        if card:
            title=card.select_one('.elementor-image-box-title, h1, h2, h3, h4, h5')
            if title:
                return title.get_text(' ',strip=True)
            text=' '.join(card.get_text(' ',strip=True).split())
            return re.split(r'\s+Fase:\s*',text,maxsplit=1,flags=re.I)[0] or None
        card=anchor.find_parent(class_='price-table-wrapper')
        title=card.select_one('.title-concurso') if card else None
        if title:
            # The listing uses compact state suffix '(AL)', whereas the detail
            # spells ALAGOAS; municipality identity remains fully preserved.
            return re.sub(r'\s*\([A-Z]{2}\)\s*$','',title.get_text(' ',strip=True))
        return None

    def parse_listing(self,html,url,limit=200):
        if 'navegador incompativel' in folded(visible_soup(html).get_text(' ',strip=True)):
            raise SourcePageBlocked('portal requer User-Agent de navegador compatível; não é vazio')
        return super().parse_listing(html,url,limit)

    def document_route(self,parts):
        return parts.path.startswith('/AdmTec/') or parts.path.startswith('/wp-content/uploads/')

    def validate_document_url(self,url,candidate):
        self._check_candidate(candidate)
        parts=self._destination(url)
        if parts.hostname == 'cdn-arquivo.concursos.srv.br':
            process=self.decoded_ids(candidate.external_id)[1].zfill(5)
            valid=bool(re.fullmatch(r'/AdmTec/'+process+r'/PUBLICACOES/[^/]+\.pdf',parts.path,re.I))
        elif parts.hostname == 'webapp412434.ip-45-56-76-193.cloudezapp.io':
            # Current WordPress detail pages link their own media files. The
            # detail identity is established before this URL is validated.
            valid=bool(re.fullmatch(r'/wp-content/uploads/\d{4}/\d{2}/[^/]+\.pdf',parts.path,re.I))
        else:
            valid=False
        if parts.hostname not in self.document_hosts or parts.query or not valid:
            raise ValueError('documento ADMTEC de outro processo ou diretório')


class InstitutoMaisAdapter(HeadingAdapter):
    source='institutomais_open'
    detail_pattern=r'/Concursos/Detalhe/(\d+)/?'
    document_identity_pattern=r'/Concursos/Detalhe/(\d+)'
    candidate_selector='a[href*="/Concursos/Detalhe/"]'
    ready_selectors=('a[href*="/Concursos/Detalhe/"]',)
    identity_selector='.TituloPagina'
    listing_query_keys=()
    document_hosts=('www.institutomais.org.br',)

    def __init__(self):
        super().__init__(self.source,'https://www.institutomais.org.br/Concursos/ConcursosAbertos',
                         listing_paths=('/Concursos/ConcursosAbertos','/Concursos/ConcursosEncerrados'))

    def _title(self,anchor):
        title=anchor.get_text(' ',strip=True)
        # The first link in each card is only an image; do not consume its ID.
        if not title:
            card=anchor.find_parent(class_='concurso')
            title=card.get_text(' ',strip=True) if card else ''
        return title or None

    def _candidates(self,html,url,limit):
        soup=visible_soup(html)
        for anchor in list(soup.select(self.candidate_selector)):
            if not anchor.get_text(' ',strip=True):
                anchor.decompose()
        return super()._candidates(str(soup),url,limit)

    def document_route(self,parts):
        return parts.path.startswith('/ckfinder/userfiles/files/')

    def validate_document_url(self,url,candidate):
        self._check_candidate(candidate)
        parts=self._destination(url)
        if parts.hostname not in self.document_hosts or parts.query or not re.fullmatch(r'/ckfinder/userfiles/files/[^/]+\.pdf',parts.path,re.I):
            raise ValueError('documento Instituto Mais fora do diretório oficial')

    def _document_title(self,anchor):
        for parent in anchor.parents:
            if parent.name in ('p','span'):
                text=' '.join(parent.get_text(' ',strip=True).split())
                if len(text)>len(anchor.get_text(' ',strip=True))+20:
                    text=re.sub(r'^.*?para visualizar\s+(?:o|a|os|as)\s*','',text,flags=re.I)
                    return text
            if parent.name in ('body','html'):
                break
        return anchor.get_text(' ',strip=True)


class ReisAdapter(HeadingAdapter):
    source='reisesreis_open'
    detail_pattern=r'/editais/(\d+)/?'
    document_identity_pattern=r'(?:reisauditores\.com\.br/editais/|editalId\s*[:=]\s*)(\d+)'
    candidate_selector='a[href*="/editais/"]'
    ready_selectors=('a[href*="/editais/"]',)
    document_hosts=('s3.amazonaws.com',)
    situation='PUBLICADO,INSCRICAO_ABERTA,ANDAMENTO'
    frontend='https://novo.reisauditores.com.br'
    api='https://api.gestaoselecoes.com.br/api/editais'
    tenant_id='reisauditores'
    frontend_listing_path='/concursos-em-andamento'
    detail_prefix='/editais/'

    def __init__(self):
        super().__init__(self.source,self.frontend+self.frontend_listing_path,document_hosts=(*self.document_hosts,'api.gestaoselecoes.com.br'))
        self.listing_urls=(self.api+'?page=0&size=9&situacao='+self.situation+'&order=DESC',)

    def request_headers(self,url):
        return {'X-TenantID':self.tenant_id,'Accept':'application/json'} if urlsplit(url).hostname=='api.gestaoselecoes.com.br' else {}

    def validate_listing_url(self,url):
        parts=self._destination(url)
        query=parse_qs(parts.query,keep_blank_values=True)
        expected={'page','size','situacao','order'}
        if parts.hostname!='api.gestaoselecoes.com.br' or parts.path!='/api/editais' or set(query)!=expected or any(len(v)!=1 for v in query.values()) or not re.fullmatch(r'\d{1,5}',query['page'][0]) or query['size']!=['9'] or query['situacao']!=[self.situation] or query['order']!=['DESC']:
            raise ValueError('URL fora da API pública Reis observada')

    def parse_listing(self,html,url,limit=200):
        self.validate_listing_url(url)
        if not 1<=limit<=10000 or len(html.encode('utf-8'))>2*1024*1024:
            raise ValueError('limite de listagem inválido')
        try:
            data=json.loads(html)
        except ValueError:
            visible_soup(html)
            raise ValueError('API Reis não devolveu JSON de listagem') from None
        page=int(parse_qs(urlsplit(url).query)['page'][0])
        if not isinstance(data,dict) or not isinstance(data.get('content'),list) or type(data.get('number')) is not int or data['number']!=page or type(data.get('totalPages')) is not int or type(data.get('totalElements')) is not int or type(data.get('last')) is not bool or data.get('size')!=9 or data.get('numberOfElements')!=len(data['content']) or len(data['content'])>9:
            raise ValueError('contrato de paginação Reis inconsistente')
        count=data['totalElements'];pages=data['totalPages']
        if count<0 or pages<0 or pages!=(count+8)//9 or data['last']!=(page+1>=pages) or page>max(0,pages-1):
            raise ValueError('total/fim da API Reis inconsistente')
        if len(data['content']) != min(9, max(0, count-page*9)):
            raise ValueError('quantidade de itens da página Reis inconsistente')
        candidates=[]
        seen_ids=set()
        for row in data['content']:
            if not isinstance(row,dict) or type(row.get('id')) is not int or row['id']<=0 or not isinstance(row.get('nomeOrgaoSolicitante'),str):
                raise ValueError('identidade de candidato Reis ausente')
            if row['id'] in seen_ids:
                raise ValueError('identidade duplicada na página Reis')
            seen_ids.add(row['id'])
            title=row['nomeOrgaoSolicitante']
            if self.in_scope(str(row.get('tipo',''))+' '+title,''):
                candidates.append(self.candidate_from_url(self.frontend+self.detail_prefix+str(row['id']),title))
        result=ListingPage(candidates=candidates[:limit],truncated=len(candidates)>limit)
        if not data['last']:
            result.next_urls=[self.api+'?'+urlencode({'page':page+1,'size':9,'situacao':self.situation,'order':'DESC'})]
        elif len(data['content'])==max(0,count-page*9):
            result.terminal_evidence='API pública Reis: last=true com totais consistentes'
        if not candidates and count==0 and not data['content'] and data.get('empty') is True:
            result.empty_evidence='API pública Reis: totalElements=0, empty=true e content=[]'
        if result.truncated:
            result.diagnostics.append('limite de candidatos atingido; cobertura parcial')
        return result

    def confirm_identity(self,candidate,html,url):
        soup=self._check_detail(candidate,html,url)
        islands=soup.select('astro-island[props]')
        identities=[]
        for island in islands:
            try:
                payload=json.loads(island['props'])
                identities.append(str(payload['edital'][1]['id'][1]))
            except (ValueError,KeyError,TypeError,IndexError):
                continue
        if identities!=[candidate.external_id]:
            raise ValueError('identidade estruturada do detalhe Reis incompatível')
        super().confirm_identity(candidate,html,url)

    def document_route(self,parts):
        return parts.path.startswith('/sgs.reisauditores.com.br/') and '/anexos/' in parts.path

    def validate_document_url(self,url,candidate):
        self._check_candidate(candidate)
        parts=self._destination(url)
        if parts.hostname not in self.document_hosts or parts.query or not re.fullmatch(r'/sgs\.reisauditores\.com\.br/[a-z0-9-]+/\d+/\d+-\d{4}/anexos/[^/]+\.pdf',parts.path,re.I):
            raise ValueError('documento Reis fora do tenant/diretório observado')

    def _document_title(self,anchor):
        row=anchor.find_parent('tr')
        cells=row.select('td') if row else []
        return cells[1].get_text(' ',strip=True) if len(cells)>=2 else anchor.get_text(' ',strip=True)


BATCH30_OWN_ADAPTERS=(IBFCAdapter(),ADMTECAdapter(),InstitutoMaisAdapter(),ReisAdapter())
