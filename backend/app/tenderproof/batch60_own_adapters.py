"""Own-portal contracts observed on 2026-09-08; sampled coverage only."""
import re
from urllib.parse import urlsplit
from app.tenderproof.pilot_adapters import PilotHTMLAdapter, visible_soup, folded, document_kind
from app.tenderproof.validation import title_is_corroborated


class ObservedHeadingAdapter(PilotHTMLAdapter):
    listing_query_keys=()
    def confirm_identity(self,candidate,html,url):
        soup=self._check_detail(candidate,html,url)
        headings=' '.join(n.get_text(' ',strip=True) for n in soup.select(self.identity_selector))
        if not candidate.title_observed or not title_is_corroborated(candidate.title_observed,headings):
            raise ValueError('título observado incompatível com detalhe')
        if not self.documents(html,candidate):
            raise ValueError('detalhe sem documento oficial associado')


class MSConcursosAdapter(ObservedHeadingAdapter):
    source='msconcursos_open'
    detail_pattern=r'/concurso/(\d+)/[a-z0-9-]+'
    document_identity_pattern=detail_pattern
    candidate_selector='a.saiba-mais[href]'
    ready_selectors=('a.saiba-mais[href]',)
    identity_selector='h3.titulo'
    document_hosts=('msconcursos.com.br',)
    def __init__(self):
        super().__init__(self.source,'https://msconcursos.com.br/',document_hosts=())
    def _title(self,anchor):
        card=anchor.find_parent(class_='concurso')
        title=card.select_one('h3.titulo') if card else None
        return title.get_text(' ',strip=True) if title else None
    def document_route(self,p):
        return p.path.startswith('/arquivos/')
    def validate_document_url(self,url,candidate):
        self._check_candidate(candidate);p=self._destination(url)
        if p.query or not re.fullmatch(r'/arquivos/[A-Za-z0-9_-]+/documentos/[^/]+\.pdf',p.path,re.I):
            raise ValueError('diretório documental MS incompatível')
    def documents(self,html,candidate):
        soup=visible_soup(html)
        base=soup.select_one('base[href]')
        if not base or base['href']!='https://msconcursos.com.br/':
            raise ValueError('base documental MS ausente ou incompatível')
        # The observed base resolves relative download paths at the site root.
        for a in soup.select('a[href]'):
            if a['href'].startswith('arquivos/'):
                a['href']='https://msconcursos.com.br/'+a['href']
        return super().documents(str(soup),candidate)
    def _document_title(self,anchor):
        row=anchor.find_parent('li');name=row.select_one('.nome') if row else None
        if not name:return ''
        for date in name.select('small'):date.decompose()
        return name.get_text(' ',strip=True).rstrip(' -')


class ConsepAdapter(ObservedHeadingAdapter):
    source='consep_open'
    detail_pattern=r'/concurso/[A-Za-z0-9-]+/(\d+)/'
    document_identity_pattern=detail_pattern
    candidate_selector='a[href*="/concurso/"]'
    ready_selectors=('a[href*="/concurso/"]',)
    identity_selector='.meio_esq fieldset:first-of-type .texto_justificado'
    document_hosts=('www.consep-pi.com.br',)
    def __init__(self):
        super().__init__(self.source,'https://www.consep-pi.com.br',listing_paths=('', '/concursos','/status-concurso/Aberto/1/','/status-concurso/Em-Andamento/2/','/status-concurso/Encerrado/3/'))
    def _title(self,anchor):return anchor.get_text(' ',strip=True)
    def document_route(self,p):return p.path.startswith('/admin/upload/documentos/')
    def validate_document_url(self,url,candidate):
        self._check_candidate(candidate);p=self._destination(url)
        if p.query or not re.fullmatch(r'/admin/upload/documentos/[a-f0-9]+\.pdf',p.path):
            raise ValueError('diretório documental CONSEP incompatível')
    def documents(self,html,candidate):
        docs=super().documents(html,candidate)
        for doc in docs:
            # Portal puts municipality before the explicit original-notice label.
            if re.fullmatch(r'.+ - edital - teste seletivo \d{4}',folded(doc.title)):
                doc.kind='edital'
        return docs


class FunvapiAdapter(ObservedHeadingAdapter):
    source='funvapi_open'
    detail_pattern=r'(/index\.php/\d{4}/\d{2}/\d{2}/[a-z0-9-]+/)'
    document_identity_pattern=detail_pattern
    candidate_selector='.flexslider a[href], h2.entry-title a[href]'
    ready_selectors=('.entry-title',)
    identity_selector='h1.entry-title'
    document_hosts=('funvapi.com.br',)
    def __init__(self):
        super().__init__(self.source,'https://funvapi.com.br/',listing_paths=('/','/index.php/category/concursos/','/index.php/category/concursos-em-andamento/','/index.php/category/concursos-realizados/'))
    def _title(self,anchor):
        title=anchor.select_one('.entry-title')
        return (title or anchor).get_text(' ',strip=True)
    def document_route(self,p):return p.path.startswith('/wp-content/uploads/')
    def validate_document_url(self,url,candidate):
        self._check_candidate(candidate);p=self._destination(url)
        if p.query or not re.fullmatch(r'/wp-content/uploads/\d{4}/\d{2}/[^/]+\.pdf',p.path,re.I):
            raise ValueError('diretório documental FUNVAPI incompatível')
    def confirm_identity(self,candidate,html,url):
        super().confirm_identity(candidate,html,url)
        canonical=visible_soup(html).select_one('link[rel=canonical][href]')
        if not canonical or canonical['href']!=candidate.detail_url_observed:
            raise ValueError('identidade canônica FUNVAPI incompatível')


BATCH60_OWN={a.source:a for a in (MSConcursosAdapter(),ConsepAdapter(),FunvapiAdapter())}
