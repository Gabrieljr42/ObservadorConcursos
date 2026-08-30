from __future__ import annotations

import logging
import re
import unicodedata
from typing import Any

from bs4 import BeautifulSoup

from app.connectors.base import CandidateItem
from app.connectors.common import extract_pdf_link
from app.connectors.configurable import ConfigurableHTMLConnector, SourceDefinition

logger = logging.getLogger(__name__)


class InstitutionalSelectionConnector(ConfigurableHTMLConnector):
    """Connector for State Research Foundations (FAPEMIG, FAPES, FAPESP, etc.) and university foundations.

    Strictly separates institutional hiring / personnel selection from scientific
    research grants (fomento / projetos de pesquisa / bolsas acadêmicas puras).
    """

    category = 'institutional_selection'

    # These terms are deliberately not sufficient on their own.  In particular,
    # ``processo seletivo`` occurs frequently in calls for research proposals.
    PERSONNEL_TERMS: tuple[str, ...] = (
        'concurso publico', 'selecao publica', 'selecao de pessoal',
        'contratacao de pessoal', 'contratacao temporaria', 'quadro temporario',
        'emprego', 'cargo', 'cargos', 'funcao', 'funcoes', 'vaga', 'vagas',
        'servidor', 'servidores', 'pessoal', 'profissional', 'profissionais',
        'estagio', 'apoio tecnico', 'apoio institucional', 'colaborador',
    )

    NON_PERSONNEL_TERMS: tuple[str, ...] = (
        'compra', 'fornecedor', 'licitacao', 'dispensa de licitacao', 'pregao',
        'tomada de precos', 'contratacao de empresa', 'pessoa juridica',
        'oferta tecnologica', 'transferencia de tecnologia', 'fomento',
        'projeto de pesquisa', 'projetos de pesquisa', 'chamada universal',
        'auxilio a pesquisa', 'subvencao economica', 'financiamento de laboratorio',
        'evento cientifico', 'eventos cientificos', 'premio', 'premiacao',
        'mobilidade academica', 'bolsa de mestrado', 'bolsa de doutorado',
        'pos-doutorado', 'iniciacao cientifica', 'pibic', 'pibiti', 'pibic em',
        'bolsista academico', 'concessao de bolsas', 'selecao de bolsistas',
        'publicacao de artigos', 'apoio a editacao', 'taxa de bancada',
    )

    _STRONG_PERSONNEL_PATTERNS: tuple[re.Pattern[str], ...] = (
        re.compile(r'\bconcurso\s+publico\b'),
        re.compile(r'\bselecao\s+publica\b.{0,100}\b(?:pessoal|cargo|funcao|vaga|profissional|contrat)', re.S),
        re.compile(r'\bprocesso\s+seletivo\s+simplificado\b.{0,160}\b(?:contrat|cargo|funcao|vaga|pessoal|profissional|temporar)', re.S),
        re.compile(
            r'\bprocesso\s+seletivo\b.{0,220}\b(?:contrat|cargo|funcao|vaga|cadastro\s+de\s+reserva|'
            r'profissional|cuidador|analista|assistente|advogado|programador|jornalista|secretari)',
            re.S,
        ),
        re.compile(r'\bcontratacao\s+(?:temporaria|de\s+pessoal)\b'),
        re.compile(r'\bcontratacao\s+(?:clt|celetista)\b'),
        re.compile(
            r'\bselecao\s+de\s+(?:auxiliar|analista|assistente|tecnico|profissional|cuidador|advogado|'
            r'programador|jornalista|secretari|contador|engenheir|estagiari|fiscal)',
        ),
        re.compile(r'\b(?:emprego|cargo|funcao|vaga|vagas)\b.{0,100}\b(?:contrat|selec|edital|temporar)', re.S),
        re.compile(r'\b(?:estagio|apoio\s+tecnico|apoio\s+institucional)\b.{0,120}\b(?:vaga|selec|contrat|vincul|profissional|atuac)', re.S),
    )

    def __init__(self, definition: SourceDefinition, base_url: str | None = None, list_url: str | None = None):
        super().__init__(definition, base_url, list_url)
        self.category = 'institutional_selection'

    @staticmethod
    def _normalized(value: str) -> str:
        value = unicodedata.normalize('NFKD', value.lower())
        return ''.join(ch for ch in value if not unicodedata.combining(ch))

    @classmethod
    def has_personnel_evidence(cls, title: str | None, text: str) -> bool:
        """Reusable semantic gate for dedicated institutional connectors."""
        if not title:
            return False
        normalized_title = cls._normalized(title)
        if any(term in normalized_title for term in cls.NON_PERSONNEL_TERMS):
            return False
        if any(pattern.search(normalized_title) for pattern in cls._STRONG_PERSONNEL_PATTERNS):
            return True

        haystack = cls._normalized(f'{title} {text[:5000]}')
        strong_matches = [
            match
            for pattern in cls._STRONG_PERSONNEL_PATTERNS
            if (match := pattern.search(haystack)) is not None
        ]
        if not strong_matches:
            return False

        # Navigation words such as “Compras” must not veto a real selection.
        # Reject an excluded concept only when it is close to the selection
        # evidence (i.e. belongs to the edital itself, not a distant menu).
        for term in cls.NON_PERSONNEL_TERMS:
            start = haystack.find(term)
            while start >= 0:
                if any(abs(start - match.start()) <= 320 for match in strong_matches):
                    return False
                start = haystack.find(term, start + len(term))
        return True

    def _fetch_candidates(self) -> list[CandidateItem]:
        raw_candidates = super()._fetch_candidates()
        candidates = [
            c for c in raw_candidates
            if self.has_personnel_evidence(c.title_hint, c.title_hint)
        ]
        if candidates:
            return candidates

        # Check if the list URL itself is a dedicated process page (e.g. /selecao-2025)
        urls_to_scan = [self.list_url] if self._explicit_list_url else (
            self.definition.list_urls if self.definition.list_urls else [self.list_url]
        )
        for scan_url in urls_to_scan:
            try:
                html = self._fetch_html(scan_url)
                soup = BeautifulSoup(html, 'lxml')
                page_title = soup.title.get_text(' ', strip=True) if soup.title else ''
                text = soup.get_text(' ', strip=True)
                if self.has_personnel_evidence(page_title, text):
                    status_hint = self._infer_status(text)
                    if self.mode == 'open' and status_hint in ('Finalizado', 'Encerrado'):
                        continue
                    # Discover primary edital PDF or documents
                    pdf_link = extract_pdf_link(soup, scan_url)
                    if pdf_link or any(a.get('href', '').endswith('.pdf') for a in soup.select('a[href]')):
                        candidates.append(CandidateItem(
                            title_hint=page_title[:500],
                            detail_url=scan_url,
                            status_hint=status_hint,
                            external_id=scan_url.rstrip('/').rsplit('/', 1)[-1],
                        ))
            except Exception as exc:
                logger.debug('Institutional candidate check failed for %s: %s', scan_url, exc)

        if not candidates:
            if raw_candidates:
                self.mark_empty_evidence(
                    kind='institutional_non_personnel_fomento',
                    value=f'{len(raw_candidates)} calls evaluated; all are research fomento / zero personnel hiring',
                    source=self.list_url,
                )
            # A zero-row result is ambiguous: the selector may be broken, the
            # content may be JS-only, or the portal may really be empty.  Do
            # not manufacture institutional evidence when no official row or
            # explicit empty-state/API evidence was discovered.

        return candidates

    def _is_valid_certame(
        self,
        title: str | None,
        orgao: str | None,
        cidade: str | None,
        uf: str | None,
        inicio,
        fim,
        edital_url: str | None,
        cargo_candidates: list[str],
        text: str,
    ) -> bool:
        if not title:
            return False

        if not self.has_personnel_evidence(title, text):
            return False

        return super()._is_valid_certame(
            title=title,
            orgao=orgao or self.definition.default_orgao or self.banca,
            cidade=cidade or self.definition.default_cidade,
            uf=uf or self.definition.default_uf,
            inicio=inicio,
            fim=fim,
            edital_url=edital_url,
            cargo_candidates=cargo_candidates,
            text=text,
        )
