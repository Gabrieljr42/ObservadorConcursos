"""JCM's public competition portal, observed September 2026."""
import re
from urllib.parse import parse_qs
from app.tenderproof.pilot_adapters import SelecaoNetAdapter, folded


class JcmAdapter(SelecaoNetAdapter):
    # The portal declares and serves ISO-8859-1, including accented city names.
    html_encoding = 'iso-8859-1'
    empty_patterns = (r'Nenhum item cadastrado\.',)

    def __init__(self):
        super().__init__('jcm_open', 'concursos.concursosjcm.com.br', '17',
                         tabs=('abertos', '1', '3', '4', '5'))

    def validate_listing_url(self, url):
        p = self._destination(url)
        if not p.query:
            return super().validate_listing_url(url)
        query = parse_qs(p.query, keep_blank_values=True)
        if (p.hostname != self.portal_host or p.path not in self.listing_paths
                or set(query) != {'ord', 'dir', 'pg', 'q', 'pp'}
                or any(len(v) != 1 for v in query.values())
                or any(query[k] != [''] for k in ('ord', 'dir', 'q'))
                or query['pp'] != ['10'] or not re.fullmatch(r'[1-9]\d{0,4}', query['pg'][0])):
            raise ValueError('paginação JCM fora do contrato observado')

    def documents(self, html, candidate):
        docs = super().documents(html, candidate)
        for doc in docs:
            title = folded(doc.title)
            if re.match(r'^edital\s*-\s*retificado\b', title):
                doc.kind = 'consolidado'
            elif re.match(r'^retificacao\s+\d+\s+ao\s+edital\b', title):
                doc.kind = 'retificacao'
        return docs
