"""Observed FUNDEP/FACET/EDUCA contracts, 2026-09-08; no full-coverage claim.

JCM and IDIB remain unregistered: captures do not prove a document contract.
"""
import re
from urllib.parse import urlsplit

from app.tenderproof.batch30_shared_adapters import ObservedNetAdapter, R2, OLD, tabs
from app.tenderproof.validation import title_is_corroborated
from app.tenderproof.pilot_adapters import folded


def observed_text(value):
    if any(ch in value for ch in ('Ã','Â')):
        for encoding in ('latin1','cp1252'):
            try:
                return value.encode(encoding).decode('utf-8')
            except UnicodeError:
                pass
    return value


class FundepAdapter(ObservedNetAdapter):
    candidate_selector = 'a[href*="fundep.selecao.net.br/informacoes/"]'
    ready_selectors = (candidate_selector,)
    implementation_scope = 'visible FUNDEP current listing; AJAX Ver Mais historical expansion not yet acquired'

    def __init__(self):
        super().__init__('fundep_open', 'https://www.gestaodeconcursos.com.br/site/site/default.aspx',
            '590', ('/site/site/Default.aspx', '/site/Site/Default.aspx'), R2)
        self.allowed_hosts = (*self.allowed_hosts, 'fundep.selecao.net.br')

    def validate_detail_url(self, url):
        p = self._destination(url)
        if p.hostname != 'fundep.selecao.net.br' or p.query or not re.fullmatch(self.detail_pattern, p.path):
            raise ValueError('detalhe fora da plataforma FUNDEP observada')

    def in_scope(self, title, url):
        return super().in_scope(title, url) and 'titulo para especialistas' not in folded(title)

    def _title(self, anchor):
        prefix = str(anchor.get('id', '')).removesuffix('_url')
        for root in anchor.parents:
            node = root.find(id=prefix + '_spanNomeSite') if prefix else None
            if node:
                return observed_text(node.get_text(' ',strip=True))
        return None

    def confirm_identity(self, candidate, html, url):
        soup = self._check_detail(candidate, html, url)
        docs = self.documents(html, candidate)
        text = ' '.join(h.get_text(' ',strip=True) for h in soup.select('.dados h2'))
        # FUNDEP header uses acronym FUMEP; the linked official notice title
        # supplies the municipality present in the listing. Both are preserved.
        text += ' ' + ' '.join(doc.title for doc in docs)
        if not docs or not candidate.title_observed or not title_is_corroborated(candidate.title_observed, text):
            raise ValueError('identidade FUNDEP não corroborada no detalhe e manifesto')


class FacetAdapter(ObservedNetAdapter):
    candidate_selector = 'h3 a[href], .dados > a[href]'

    def confirm_identity(self, candidate, html, url):
        soup = self._check_detail(candidate, html, url)
        # Observed invalid h2>p is repaired by lxml into a sibling paragraph.
        header = soup.select_one('.dados')
        text = observed_text(' '.join(h.get_text(' ',strip=True) for h in header.find_all(['h2','p'], recursive=False))) if header else ''
        if not candidate.title_observed or not title_is_corroborated(candidate.title_observed, text) or not self.documents(html,candidate):
            raise ValueError('identidade FACET incompatível com dados do detalhe')


BATCH60_SHARED_ADAPTERS = (
    FundepAdapter(),
    FacetAdapter('facet_open', 'https://concursos.facetconcursos.com.br/', '781',
        tabs('abertos',1,2,3,4,5,7), (*R2,*OLD)),
    ObservedNetAdapter('educapb_open', 'https://ps-adm-871.selecao.net.br/', '871',
        tabs('abertos',1,2,3,4,5), R2),
)
