"""Observed Gestor Editais contracts; IDECAN document access remains blocked.

IDECAN currently exposes a real list and explicit 'no files posted' details.
Its separate ASP.NET site is linked by the official institution but returned
403 on both home/detail on 2026-09-08 UTC; it is not silently substituted.
"""
import re
from app.tenderproof.pilot_adapters import EditalVerAdapter, folded
from app.tenderproof.validation import title_is_corroborated


class AguiaAdapter(EditalVerAdapter):
    def __init__(self):
        super().__init__('aguia_open', 'portal.institutoaguia.org.br', 'cdn.institutoaguia.org.br')

    def documents(self, html, candidate):
        documents = super().documents(html, candidate)
        for document in documents:
            # Actual rows include 'edital das inscrições deferidas' and
            # 'edital da avaliação de títulos'. Neither is an opening notice.
            if document.kind == 'edital' and not re.match(r'^edital\s+de\s+abertura\b', folded(document.title)):
                document.kind = 'outro'
        return documents


class IdecanAdapter(EditalVerAdapter):
    implementation_state = 'partial'
    implementation_scope = 'observed listing/detail identity; principal document unavailable in sampled portal'

    def __init__(self):
        super().__init__('idecan_open', 'portal.concursos.idecan.org.br', 'portal.concursos.idecan.org.br')
        self.listing_urls = ('https://portal.concursos.idecan.org.br/edital/index/abertos',)
        self.listing_paths = ('/edital/index/abertos', '/edital')

    def document_route(self, parts):
        # No contest document route was observed. Policies linked to another
        # host must not stand in for missing notices. Future discovery refuses
        # acquisition until an official document route is reviewed.
        return False

    def validate_document_url(self, url, candidate):
        self._check_candidate(candidate)
        raise ValueError('IDECAN: documento oficial ainda não observado; contrato documental pendente')

    def confirm_identity(self, candidate, html, url):
        soup = self._check_detail(candidate, html, url)
        title = ' '.join(p.get_text(' ',strip=True) for p in soup.select('p.text-16'))
        if not candidate.title_observed or not title_is_corroborated(candidate.title_observed, title):
            raise ValueError('título do detalhe IDECAN incompatível')
        if not soup.select_one('#arquivos'):
            raise ValueError('área documental IDECAN ausente; possível layout incompleto')


BATCH30_EDITAL_ADAPTERS = (AguiaAdapter(), IdecanAdapter())
