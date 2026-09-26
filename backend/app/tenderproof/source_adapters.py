"""Source contracts shared by interactive review and continuous acquisition.

Registration certifies an implemented strategy, not the current completeness of
the portal. Every page carries its own evidence of truncation/empty/end state.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from html import escape
from typing import Protocol
from urllib.parse import parse_qs, urljoin, urlsplit, urlunsplit

from bs4 import BeautifulSoup

from app.tenderproof.contracts import DiscoveredCandidate, DocumentCandidate
from app.tenderproof.security import DEFAULT_ALLOWLIST, validate_destination
from app.tenderproof.source_parsers import (
    parse_listing_candidates, parse_document_candidates, confirm_identity, choose_edital,
)
from app.tenderproof.sources import IMESO_LISTING, imeso_candidates, imeso_documents, confirm_imeso_identity


from app.tenderproof.source_adapter_base import (ListingPage, SourcePageBlocked, SourceAdapter, HTMLSourceAdapter)


class IBGPAdapter(HTMLSourceAdapter):
    source = "ibgp_open"
    listing_urls = ("https://novo.ibgpconcursos.com.br/inscricoes_abertas.jsp",)
    # Tab destinations observed on the official listing on 2026-09-07.
    listing_paths = ("/inscricoes_abertas.jsp", "/index.jsp", "/inscricoes_em_andamento.jsp",
                     "/inscricoes_encerradas.jsp", "/concursos.jsp")
    allowed_hosts = ("novo.ibgpconcursos.com.br", "ibgpconcursos.com.br")
    ready_selectors = ("a[href*='concurso.jsp?cod=']",)
    observed_url_paths = ("/rest/concurso",)
    document_identity_pattern = r"cod\s*=\s*(\d{1,12})"
    empty_patterns = (r"Nenhum concurso (?:com inscrições abertas|disponível)(?: no momento)?[.!]?", r"Não há concursos com inscrições abertas(?: no momento)?[.!]?")

    def _candidates(self, html, url, limit):
        return parse_listing_candidates(html, base_url=url, limit=limit)

    def validate_detail_url(self, url):
        validate_destination(url, allowlist=self.allowed_hosts)
        parts = urlsplit(url)
        query = parse_qs(parts.query)
        if parts.scheme != "https" or parts.hostname != "novo.ibgpconcursos.com.br" or parts.path != "/concurso.jsp" or set(query) != {"cod"} or len(query["cod"]) != 1 or not query["cod"][0].isdigit():
            raise ValueError("identidade de URL IBGP inválida")

    def confirm_identity(self, candidate, html, url):
        self.validate_detail_url(url)
        if candidate.source != self.source or url != candidate.detail_url_observed:
            raise ValueError("fonte ou detalhe não corresponde ao candidato")
        confirm_identity(candidate=candidate, detail_html=html, detail_url=url)

    def candidate_from_url(self, url, title=None):
        self.validate_detail_url(url)
        cod = parse_qs(urlsplit(url).query)["cod"][0]
        return DiscoveredCandidate(candidate_id=f"cand-{cod}", external_id=cod, source=self.source,
                                   detail_url_observed=url, title_observed=title, observed_at=datetime.now(timezone.utc))

    def documents(self, html, candidate):
        return parse_document_candidates(html, base_url=candidate.detail_url_observed)

    def validate_document_url(self, url, candidate):
        validate_destination(url, allowlist=self.allowed_hosts)
        if candidate.source != self.source:
            raise ValueError("documento pertence a outra fonte")


class IMESOAdapter(HTMLSourceAdapter):
    source = "imeso_open"
    listing_urls = ("https://portal.imeso.com.br/edital", IMESO_LISTING)
    listing_paths = ("/edital", "/edital/", "/edital/searchEdital")
    allowed_hosts = ("portal.imeso.com.br", "cdn.imeso.com.br", "s3.us-east-1.amazonaws.com")
    ready_selectors = ("a[href*='/edital/ver/']",)
    observed_url_paths = ("/edital/searchEdital",)
    document_identity_pattern = r"/edital/ver/(\d+)"
    empty_patterns = (r"Nenhum (?:edital|concurso|processo seletivo) (?:encontrado|disponível)(?: no momento)?[.!]?", r"Não há editais (?:disponíveis|abertos)(?: no momento)?[.!]?")

    def _candidates(self, html, url, limit):
        return imeso_candidates(html, url, limit)

    def validate_detail_url(self, url):
        validate_destination(url, allowlist=self.allowed_hosts)
        parts = urlsplit(url)
        if parts.scheme != "https" or parts.hostname != "portal.imeso.com.br" or not re.fullmatch(r"/edital/ver/\d+/?", parts.path) or parts.query:
            raise ValueError("identidade de URL IMESO inválida")

    def confirm_identity(self, candidate, html, url):
        self.validate_detail_url(url)
        if candidate.source != self.source:
            raise ValueError("candidato pertence a outra fonte")
        confirm_imeso_identity(candidate, html, url)

    def candidate_from_url(self, url, title=None):
        self.validate_detail_url(url)
        cod = urlsplit(url).path.rstrip("/").split("/")[-1]
        return DiscoveredCandidate(candidate_id=f"imeso-{cod}", external_id=cod, source=self.source,
                                   detail_url_observed=url, title_observed=title, observed_at=datetime.now(timezone.utc))

    def documents(self, html, candidate):
        return imeso_documents(html, candidate)

    def validate_document_url(self, url, candidate):
        validate_destination(url, allowlist=self.allowed_hosts)
        if candidate.source != self.source or not imeso_documents(f'<a href="{escape(url, quote=True)}">Edital</a>', candidate):
            raise ValueError("destino documental IMESO sem identidade verificável")


from app.tenderproof.pilot_adapters import PILOT_ADAPTERS
from app.tenderproof.batch30_shared_adapters import BATCH30_SHARED_ADAPTERS
from app.tenderproof.batch30_edital_adapters import BATCH30_EDITAL_ADAPTERS
from app.tenderproof.batch30_own_adapters import BATCH30_OWN_ADAPTERS
from app.tenderproof.batch30_institutional_adapters import BATCH30_INSTITUTIONAL_ADAPTERS
from app.tenderproof.batch30_uniselva_adapter import BATCH30_UNISELVA_ADAPTERS
from app.tenderproof.batch60_own_adapters import BATCH60_OWN
from app.tenderproof.batch60_shared_adapters import BATCH60_SHARED_ADAPTERS
from app.tenderproof.batch60_recovered_adapters import BATCH60_RECOVERED_ADAPTERS
from app.tenderproof.batch60_major_adapters import BATCH60_MAJOR_ADAPTERS
from app.tenderproof.batch60_catalogue_adapters import BATCH60_CATALOGUE_ADAPTERS
from app.tenderproof.batch60_extended_adapters import BATCH60_EXTENDED_ADAPTERS
from app.tenderproof.batch60_elo_adapter import BATCH60_ELO_ADAPTERS
from app.tenderproof.batch60_contemax_adapter import ContemaxAdapter
from app.tenderproof.batch99_own_adapters import BATCH99_OWN_ADAPTERS
from app.tenderproof.batch99_ieses_adapter import BATCH99_IESES_ADAPTERS
from app.tenderproof.batch99_verbena_adapter import BATCH99_VERBENA_ADAPTERS
from app.tenderproof.batch99_foundation_adapters import BATCH99_FOUNDATION_ADAPTERS
from app.tenderproof.batch99_foundation_adapters import BATCH99_FOUNDATION_PUBLIC_ALTERNATIVE_ADAPTERS
from app.tenderproof.batch99_foundation_adapters import BATCH99_FOUNDATION_SECTION_ADAPTERS
from app.tenderproof.batch99_foundation_adapters import BATCH99_FOUNDATION_FAPESE_ADAPTERS
from app.tenderproof.batch99_fepese_adapter import BATCH99_FEPESE_ADAPTERS
from app.tenderproof.batch99_regions_adapters import BATCH99_REGIONS_ADAPTERS
from app.tenderproof.batch99_southeast_adapters import BATCH99_SOUTHEAST_ADAPTERS

SOURCE_ADAPTERS: dict[str, SourceAdapter] = {adapter.source: adapter for adapter in (IBGPAdapter(), IMESOAdapter(), *PILOT_ADAPTERS, *BATCH30_SHARED_ADAPTERS, *BATCH30_EDITAL_ADAPTERS, *BATCH30_OWN_ADAPTERS, *BATCH30_INSTITUTIONAL_ADAPTERS, *BATCH30_UNISELVA_ADAPTERS)}
SOURCE_ADAPTERS.update(BATCH60_OWN)
SOURCE_ADAPTERS.update({a.source:a for a in BATCH60_SHARED_ADAPTERS})
SOURCE_ADAPTERS.update(BATCH60_RECOVERED_ADAPTERS)
SOURCE_ADAPTERS.update({a.source:a for a in BATCH60_MAJOR_ADAPTERS})
SOURCE_ADAPTERS.update({a.source:a for a in BATCH60_CATALOGUE_ADAPTERS})
SOURCE_ADAPTERS.update(BATCH60_EXTENDED_ADAPTERS)
SOURCE_ADAPTERS.update({a.source:a for a in (*BATCH60_ELO_ADAPTERS, ContemaxAdapter())})
SOURCE_ADAPTERS.update({a.source:a for a in BATCH99_OWN_ADAPTERS})
SOURCE_ADAPTERS.update({a.source:a for a in BATCH99_IESES_ADAPTERS})
SOURCE_ADAPTERS.update({a.source:a for a in BATCH99_VERBENA_ADAPTERS})
SOURCE_ADAPTERS.update(BATCH99_FOUNDATION_ADAPTERS)
SOURCE_ADAPTERS.update(BATCH99_FOUNDATION_PUBLIC_ALTERNATIVE_ADAPTERS)
SOURCE_ADAPTERS.update(BATCH99_FOUNDATION_SECTION_ADAPTERS)
SOURCE_ADAPTERS.update(BATCH99_FOUNDATION_FAPESE_ADAPTERS)
SOURCE_ADAPTERS.update(BATCH99_FEPESE_ADAPTERS)
SOURCE_ADAPTERS.update(BATCH99_REGIONS_ADAPTERS)
SOURCE_ADAPTERS.update({a.source:a for a in BATCH99_SOUTHEAST_ADAPTERS})
from app.tenderproof.idib_adapter import IdibAdapter
SOURCE_ADAPTERS['idib_open']=IdibAdapter()
from app.tenderproof.jcm_adapter import JcmAdapter
SOURCE_ADAPTERS['jcm_open'] = JcmAdapter()
from app.tenderproof.fumarc_adapter import FumarcAdapter
SOURCE_ADAPTERS['fumarc_open'] = FumarcAdapter()
from app.tenderproof.faped_adapter import FapedAdapter
SOURCE_ADAPTERS['faped_selection'] = FapedAdapter()
from app.tenderproof.fapeam_adapter import FapeamAdapter
SOURCE_ADAPTERS['fapeam_selection'] = FapeamAdapter()
from app.tenderproof.facepe_adapter import FacepeAdapter
SOURCE_ADAPTERS['facepe_selection'] = FacepeAdapter()
from app.tenderproof.fapern_adapter import FapernAdapter
SOURCE_ADAPTERS['fapern_selection'] = FapernAdapter()
from app.tenderproof.fapesq_adapter import FapesqAdapter
SOURCE_ADAPTERS['fapesq_selection'] = FapesqAdapter()
from app.tenderproof.fapes_adapter import FapesAdapter
SOURCE_ADAPTERS['fapes_selection'] = FapesAdapter()
from app.tenderproof.fapepi_adapter import FapepiAdapter
SOURCE_ADAPTERS['fapepi_selection'] = FapepiAdapter()
from app.tenderproof.fapema_adapter import FapemaAdapter
SOURCE_ADAPTERS['fapema_selection'] = FapemaAdapter()
from app.tenderproof.funcap_adapter import FuncapAdapter
SOURCE_ADAPTERS['fapece_selection'] = FuncapAdapter()
from app.tenderproof.fapeal_adapter import FapealAdapter
SOURCE_ADAPTERS['fapeal_selection'] = FapealAdapter()
from app.tenderproof.fundect_adapter import FundectAdapter
SOURCE_ADAPTERS['fundect_selection'] = FundectAdapter()
from app.tenderproof.fapdf_adapter import FapdfAdapter
SOURCE_ADAPTERS['fapdf_selection'] = FapdfAdapter()
from app.tenderproof.fapt_adapter import FaptAdapter
SOURCE_ADAPTERS['fapt_selection'] = FaptAdapter()
from app.tenderproof.fapeap_adapter import FapeapAdapter
SOURCE_ADAPTERS['fapeap_selection'] = FapeapAdapter()


def get_source_adapter(source: str) -> SourceAdapter:
    try:
        return SOURCE_ADAPTERS[source]
    except KeyError:
        raise ValueError("fonte TenderProof não suportada") from None

from app.tenderproof.faperr_adapter import FaperrAdapter
SOURCE_ADAPTERS['faperr_selection'] = FaperrAdapter()

from app.tenderproof.fapero_adapter import FaperoAdapter
SOURCE_ADAPTERS['fapero_selection'] = FaperoAdapter()
from app.tenderproof.fapac_adapter import FapacAdapter
SOURCE_ADAPTERS['fapac_selection'] = FapacAdapter()
from app.tenderproof.fapemig_adapter import FapemigAdapter
SOURCE_ADAPTERS['fapemig_selection'] = FapemigAdapter()
from app.tenderproof.fapesb_reda_adapter import FapesbRedaAdapter
SOURCE_ADAPTERS['fapesb_selection'] = FapesbRedaAdapter()

from app.tenderproof.fapeg_adapter import FapegAdapter
SOURCE_ADAPTERS['fapeg_selection'] = FapegAdapter()
