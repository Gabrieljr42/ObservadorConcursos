"""Observed catalogue/detail contracts; aliases retain original source IDs."""
import re
from urllib.parse import urlsplit
from app.tenderproof.batch60_own_adapters import ObservedHeadingAdapter
from app.tenderproof.pilot_adapters import visible_soup,folded


class ConsulplanAdapter(ObservedHeadingAdapter):
    detail_pattern=r'/([a-z][a-z0-9-]*\d{4})'
    document_identity_pattern=detail_pattern
    candidate_selector='a.btn-concurso-secondary[href]'
    ready_selectors=('a.btn-concurso-secondary[href]',)
    identity_selector='main > .row.mt-4 > .col-md-10 > h3'
    document_hosts=('cdnsite.institutoconsulplan.org.br',)
    def __init__(self,source):
        super().__init__(source,'https://institutoconsulplan.org.br/Concursos',document_hosts=self.document_hosts)
    def _title(self,a):
        card=a.find_parent(class_='card-body');heading=card.select_one('h5.card-title') if card else None
        return heading.get_text(' ',strip=True) if heading else None
    def _scope_title(self,a):
        card=a.find_parent(class_='card-body')
        return card.get_text(' ',strip=True) if card else ''
    def in_scope(self,title,url):
        return super().in_scope(title,url) and not re.search(r'\b(?:pases|processo seletivo seriado|vestibular)\b',folded(title))
    def document_route(self,p):return p.path.startswith('/concursos/')
    def validate_document_url(self,url,candidate):
        self._check_candidate(candidate);p=self._destination(url)
        if p.hostname not in self.document_hosts or p.query or not re.fullmatch(r'/concursos/\d+/[a-f0-9]{32}\.pdf',p.path):
            raise ValueError('rota documental Instituto Consulplan incompatível')
    def confirm_identity(self,candidate,html,url):
        super().confirm_identity(candidate,html,url)
        canonical=visible_soup(html).select_one('link[rel=canonical][href]')
        if not canonical or canonical['href']!=candidate.detail_url_observed:
            raise ValueError('identidade canônica Instituto Consulplan incompatível')
    def documents(self,html,candidate):
        docs=super().documents(html,candidate)
        header=visible_soup(html).select_one('main > .row.mt-4')
        logo=header.select_one('.col-md-2 img[src]') if header else None
        match=re.fullmatch(r'https://cdnsite\.institutoconsulplan\.org\.br/logoConcursos/logo_(\d+)_\d+\.png',logo['src']) if logo else None
        directories={urlsplit(d.url_requested).path.split('/')[2] for d in docs}
        if not match or directories!={match[1]}:
            raise ValueError('diretório documental não corroborado pelo ID do cabeçalho Consulplan')
        return docs


class ZambiniAdapter(ObservedHeadingAdapter):
    detail_pattern=r'/portal/concursos/ver/(\d+)'
    document_identity_pattern=detail_pattern
    candidate_selector='a[href*="/concursos/ver/"]:has(h1.concurso-title)'
    ready_selectors=('h1.concurso-title',)
    identity_selector='h4.section-title'
    document_hosts=('www.zambini.org.br',)
    empty_patterns=(r'No momento não temos nenhum concurso em andamento\.',)
    def __init__(self):
        super().__init__('zambini_open','https://www.zambini.org.br/portal/concursos',listing_paths=('/portal/concursos','/portal/concursos/','/portal/concursos/encerrados'))
    def _title(self,a):return a.select_one('h1.concurso-title').get_text(' ',strip=True)
    def document_route(self,p):return p.path.startswith('/portal/assets/publicacoes/')
    def validate_document_url(self,url,candidate):
        self._check_candidate(candidate);p=self._destination(url)
        if p.query or not re.fullmatch(r'/portal/assets/publicacoes/[a-f0-9]{32}\.pdf',p.path):
            raise ValueError('diretório documental Zambini incompatível')
    def documents(self,html,candidate):
        docs=super().documents(html,candidate)
        for doc in docs:
            if doc.kind=='edital' and not re.match(r'^edital\s+\d+\s*-',folded(doc.title)):
                doc.kind='outro'
        return docs


BATCH60_CATALOGUE_ADAPTERS=tuple([ConsulplanAdapter(s) for s in ('consulplan_open','institutoconsulplan_open')]+[ZambiniAdapter()])
