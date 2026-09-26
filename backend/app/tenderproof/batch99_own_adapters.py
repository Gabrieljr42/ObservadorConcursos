"""Final-batch organizer contracts from individually preserved official captures."""
import re
import json
from urllib.parse import urljoin,parse_qs,urlsplit
from datetime import datetime,timezone
from app.tenderproof.contracts import DiscoveredCandidate
from app.tenderproof.batch30_own_adapters import HeadingAdapter
from app.tenderproof.batch60_major_adapters import document
from app.tenderproof.pilot_adapters import visible_soup,folded,PilotHTMLAdapter
from app.tenderproof.validation import title_is_corroborated


class LegatusAdapter(HeadingAdapter):
    source='legatus_open'
    candidate_selector='.card-concursos a.stretched-link[href]'
    ready_selectors=('.card-concursos',)
    detail_pattern=r'/concursos/(\d+)/(?!download/)[a-z0-9-]+/'
    document_identity_pattern=r'legatus\.org\.br/concursos/(\d+)/(?!download/)[a-z0-9-]+/'
    identity_selector='h4.title-concurso'
    listing_query_keys=()
    def __init__(self):
        super().__init__(self.source,'https://www.legatus.org.br',listing_paths=('', '/', '/concursos/abertos/','/concursos/andamento/','/concursos/homologados/','/concursos/proximos-concursos/'))
    def _title(self,a):
        card=a.find_parent(class_='card-concursos')
        title=card.select_one('.card-header h3') if card else None
        return title.get_text(' ',strip=True) if title else None
    def validate_document_url(self,url,c):
        self._check_candidate(c);p=self._destination(url)
        if p.hostname!=self.portal_host or p.query or not re.fullmatch(r'/concursos/\d+/download/',p.path):
            raise ValueError('documento Legatus fora da rota observada')
    def documents(self,html,c):
        self._check_candidate(c)
        soup=visible_soup(html);docs=[];seen=set()
        for a in soup.select('a[href]'):
            url=urljoin(c.detail_url_observed,a['href'])
            if not re.fullmatch(r'https://www\.legatus\.org\.br/concursos/\d+/download/',url):continue
            self.validate_document_url(url,c)
            if url in seen:continue
            seen.add(url);title=a.get_text(' ',strip=True)
            d=document(self.source,title,url)
            if d.kind=='edital' and not re.search(r'\babertura (?:do concurso|das inscricoes)\b',folded(title)):
                d.kind='outro'
            docs.append(d)
        return docs


class KLCAdapter(HeadingAdapter):
    source='klc_open'
    candidate_selector='#submenu_result a[href]'
    ready_selectors=('#submenu_result',)
    identity_selector='title'
    document_identity_pattern=r'klcconcursos\.com\.br/\?pag=mco&id=(\d+)'
    def __init__(self):
        super().__init__(self.source,'https://www.klcconcursos.com.br?pag=&sub=2')
        self.document_hosts=(self.portal_host,)
    def validate_listing_url(self,url):
        p=self._destination(url);q=parse_qs(p.query,keep_blank_values=True)
        if p.hostname!=self.portal_host or p.path not in ('','/') or q.get('pag')!=[''] or q.get('sub') not in (['0'],['1'],['2'],['3']) or set(q)!={'pag','sub'}:
            raise ValueError('aba KLC fora do contrato observado')
    def validate_detail_url(self,url):
        p=self._destination(url);q=parse_qs(p.query,keep_blank_values=True)
        if p.hostname!=self.portal_host or p.path not in ('','/') or set(q)!={'pag','id'} or q.get('pag')!=['mco'] or len(q.get('id',[]))!=1 or not re.fullmatch(r'\d{1,8}',q['id'][0]):
            raise ValueError('identidade de detalhe KLC inválida')
    def candidate_from_url(self,url,title=None):
        self.validate_detail_url(url);external=parse_qs(urlsplit(url).query)['id'][0]
        return DiscoveredCandidate(candidate_id=f'{self.source}-{external}',external_id=external,source=self.source,
            title_observed=title,detail_url_observed=url,observed_at=datetime.now(timezone.utc))
    def _title(self,a):
        heading=a.select_one('h3')
        return heading.get_text(' ',strip=True) if heading else None
    def parse_listing(self,html,url,limit=200):
        page=super().parse_listing(html,url,limit)
        marker=visible_soup(html).select_one('#submenu_result > div > p')
        if not page.candidates and marker and marker.get_text(' ',strip=True)=='Nenhum concurso':
            page.empty_evidence='Nenhum concurso'
            page.terminal_evidence='marcador explícito da aba KLC solicitada'
        return page
    def document_route(self,p):return p.path.startswith('/editais/')
    def confirm_identity(self,c,html,url):
        super().confirm_identity(c,html,url)
        expected=set(re.findall(r'\b\d{3}-\d{4}\b',c.title_observed or ''))
        title=visible_soup(html).select_one('title')
        if expected and set(re.findall(r'\b\d{3}-\d{4}\b',title.get_text()))!=expected:
            raise ValueError('número/ano KLC incompatível com a listagem')
    def validate_document_url(self,url,c):
        self._check_candidate(c);p=self._destination(url)
        if p.hostname!=self.portal_host or p.query or not re.fullmatch(r'/editais/[a-f0-9]{32}\.pdf',p.path):
            raise ValueError('documento KLC fora do diretório observado')


class NossoRumoAdapter(PilotHTMLAdapter):
    source='nossorumo_open'
    ready_selectors=('[data-sobre-certame]',)
    listing_query_keys=()
    document_identity_pattern=r'nossorumo\.org\.br/Home/GetPublicacoes\?idProjeto=(\d+)'
    def __init__(self):super().__init__(self.source,'https://nossorumo.org.br/')
    def validate_detail_url(self,url):
        p=self._destination(url);q=parse_qs(p.query,keep_blank_values=True)
        if p.hostname!=self.portal_host or p.path!='/Home/GetPublicacoes' or set(q)!={'idProjeto'} or len(q['idProjeto'])!=1 or not re.fullmatch(r'\d{1,8}',q['idProjeto'][0]):
            raise ValueError('endpoint público Nosso Rumo fora do contrato')
    def candidate_from_url(self,url,title=None):
        self.validate_detail_url(url);external=parse_qs(urlsplit(url).query)['idProjeto'][0]
        return DiscoveredCandidate(candidate_id=f'{self.source}-{external}',external_id=external,source=self.source,
            title_observed=title,detail_url_observed=url,observed_at=datetime.now(timezone.utc))
    def _candidates(self,html,url,limit):
        soup=visible_soup(html);result=[];seen={}
        for card in soup.select('[data-sobre-certame]'):
            external=card['data-sobre-certame'];heading=card.select_one('h5.titulo-concursos [title]')
            if not re.fullmatch(r'\d{1,8}',external) or heading is None:continue
            title=heading['title']
            if external in seen:
                if seen[external]!=title:raise ValueError('identidade Nosso Rumo duplicada com título divergente')
                continue
            seen[external]=title
            if not self.in_scope(title,url):continue
            # Literal GetPublicacoes route and idProjeto field in observed JS.
            result.append(self.candidate_from_url('https://nossorumo.org.br/Home/GetPublicacoes?idProjeto='+external,title))
            if len(result)>=limit:break
        return result
    def _payload(self,html):
        if len(html.encode('utf-8'))>2097152:raise ValueError('JSON Nosso Rumo excede 2 MiB')
        data=json.loads(html)
        if not isinstance(data,dict) or not isinstance(data.get('projeto'),str) or not isinstance(data.get('editais'),list):
            raise ValueError('JSON público Nosso Rumo sem identidade/manifesto')
        return data
    def confirm_identity(self,c,html,url):
        self._check_candidate(c);self.validate_detail_url(url)
        if self.candidate_from_url(url).external_id!=c.external_id:raise ValueError('projeto Nosso Rumo divergente')
        data=self._payload(html)
        if not c.title_observed or not title_is_corroborated(c.title_observed,data['projeto']):
            raise ValueError('título Nosso Rumo incompatível')
        numbers=set(re.findall(r'\b\d{2}/\d{4}\b',c.title_observed))
        if numbers and set(re.findall(r'\b\d{2}/\d{4}\b',data['projeto']))!=numbers:
            raise ValueError('número/ano Nosso Rumo incompatível')
    def validate_document_url(self,url,c):
        self._check_candidate(c);p=self._destination(url)
        if p.hostname!=self.portal_host or p.query or not re.fullmatch(r'/Arquivos/Projetos/'+re.escape(c.external_id)+r'-\d+-\d+\.pdf',p.path):
            raise ValueError('PDF Nosso Rumo de outro projeto ou rota')
    def documents(self,html,c):
        self.confirm_identity(c,html,c.detail_url_observed)
        result=[];seen=set()
        for row in self._payload(html)['editais']:
            if not isinstance(row,dict) or type(row.get('id')) is not int or not isinstance(row.get('nome'),str) or not isinstance(row.get('arquivo'),str):
                raise ValueError('publicação Nosso Rumo inválida')
            if row['id'] in seen:raise ValueError('publicação Nosso Rumo duplicada')
            seen.add(row['id'])
            if not re.fullmatch(re.escape(c.external_id)+'-'+str(row['id'])+r'-\d+\.pdf',row['arquivo']):
                raise ValueError('arquivo Nosso Rumo não corrobora projeto/publicação')
            url='https://nossorumo.org.br/Arquivos/Projetos/'+row['arquivo']
            self.validate_document_url(url,c);result.append(document(self.source,row['nome'],url))
        return result


BATCH99_OWN_ADAPTERS=(LegatusAdapter(),KLCAdapter(),NossoRumoAdapter())
