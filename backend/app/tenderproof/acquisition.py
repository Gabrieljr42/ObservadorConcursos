"""TenderProof Fase 1 — aquisição limitada IBGP via sessão rastreável."""

from __future__ import annotations

from app.tenderproof.pdf_header import has_pdf_header

import re
import uuid
from datetime import datetime, timezone
from urllib.parse import urljoin, urlsplit, parse_qs

from bs4 import BeautifulSoup

from app.tenderproof.contracts import (
    SUPPORTED_SOURCE,
    DiscoveredCandidate,
    DocumentCandidate,
)
from app.tenderproof.security import (
    DestinationBlocked,
    TenderProofSettings,
    validate_destination,
    validate_redirect_chain,
)
from app.tenderproof.solari_adapter import DownloadedBytes, ObservedJson, SolariDriver
from app.tenderproof.source_adapters import get_source_adapter

LISTING_URL = "https://novo.ibgpconcursos.com.br/inscricoes_abertas.jsp"

# Public aliases retained for scripts and callers of the original demo.
from app.tenderproof.source_parsers import (
    parse_listing_candidates, parse_document_candidates, choose_edital,
    confirm_identity, filter_structured_observations,
)


class AcquisitionService:
    def __init__(self, settings: TenderProofSettings | None = None) -> None:
        self.settings = settings or TenderProofSettings.from_env()
        self.last_recovery_report = None
        self.last_listing_page = None
        self.last_documents = []
        self.last_candidate = None

    def discover(
        self,
        driver: SolariDriver,
        *,
        listing_url: str = LISTING_URL,
        source: str = SUPPORTED_SOURCE,
        owner_user_id: int | None = None,
    ) -> tuple[list[DiscoveredCandidate], list[ObservedJson]]:
        validate_destination(listing_url, allowlist=self.settings.allowlist_hosts)
        adapter = get_source_adapter(source)
        adapter.validate_listing_url(listing_url)
        html = driver.open_listing(listing_url)
        page = adapter.parse_listing(html, listing_url, self.settings.limits.max_candidates)
        self.last_listing_page = page
        candidates = page.candidates
        if not candidates and not page.empty_evidence and owner_user_id is not None:
            from app.tenderproof.recovery_integration import recover_listing_candidates
            from app.tenderproof.recovery_router import get_recovery_store
            candidates, self.last_recovery_report = recover_listing_candidates(get_recovery_store(),
                owner_user_id=owner_user_id, source=source, html=html,
                listing_url=listing_url, settings=self.settings)
        if not candidates and not page.empty_evidence:
            raise ValueError("listagem vazia não confirmada; catálogo preservado, investigação necessária")
        observed = adapter.filter_observations(driver.observed_json())
        return candidates, observed

    def select_and_fetch(
        self,
        driver: SolariDriver,
        *,
        candidate: DiscoveredCandidate,
        detail_html_override: str | None = None,
    ) -> tuple[DocumentCandidate, DownloadedBytes, list[ObservedJson]]:
        self.last_documents = []
        self.last_candidate = None
        validate_destination(candidate.detail_url_observed, allowlist=self.settings.allowlist_hosts)
        adapter = get_source_adapter(candidate.source)
        adapter.validate_detail_url(candidate.detail_url_observed)
        bind_candidate = getattr(driver, 'set_candidate', None)
        if callable(bind_candidate):
            bind_candidate(candidate)
        html = detail_html_override if detail_html_override is not None else driver.open_detail(
            candidate.detail_url_observed
        )
        adapter.confirm_identity(candidate, html, candidate.detail_url_observed)
        docs = adapter.documents(html, candidate)
        if len(docs) > self.settings.limits.max_documents:
            raise ValueError("documentos excedem o limite; seleção parcial não autoriza escolher edital")
        self.last_documents = docs
        self.last_candidate = (candidate.source, candidate.external_id, candidate.detail_url_observed)
        chosen = adapter.choose_document(docs)
        if chosen.file_format!='pdf':raise ValueError('Edital principal exige PDF')
        downloaded = self.fetch_document(driver, candidate=candidate, document=chosen)
        observed = adapter.filter_observations(driver.observed_json())
        return chosen, downloaded, observed

    def fetch_document(self, driver, *, candidate, document):
        """Download only a document in the current identity-confirmed detail."""
        if (self.last_candidate != (candidate.source, candidate.external_id, candidate.detail_url_observed)
                or not any(d.model_dump() == document.model_dump() for d in self.last_documents)):
            raise ValueError('documento adicional não pertence ao detalhe observado')
        adapter = get_source_adapter(candidate.source)
        chosen = document
        validate_destination(chosen.url_requested, allowlist=self.settings.allowlist_hosts)
        adapter.validate_document_url(chosen.url_requested, candidate)
        if chosen.file_format=='xlsx':
            if candidate.source!='fapeg_selection' or chosen.kind!='anexo' or chosen.acquisition_request is not None:
                raise ValueError('Planilha fora do contrato de anexos FAPEG')
            download_workbook=getattr(driver,'download_workbook',None)
            if not callable(download_workbook):raise ValueError('Driver não suporta aquisição de planilha')
            downloaded=download_workbook(chosen,candidate,max_bytes=self.settings.limits.max_download_bytes)
            from app.tenderproof.fapeg_workbook import validate_workbook_result
            validate_workbook_result(chosen.url_requested,downloaded,self.settings.limits.max_download_bytes)
            validate_redirect_chain([downloaded.url_requested,*(downloaded.redirect_chain or []),downloaded.url_final],allowlist=self.settings.allowlist_hosts)
            chosen.url_final=downloaded.url_final
            return downloaded
        if chosen.acquisition_request is not None:
            request_validator = getattr(adapter, 'validate_document_request', None)
            download_document = getattr(driver, 'download_document', None)
            if not callable(request_validator) or not callable(download_document):
                raise ValueError('exportação POST não suportada; GET não é substituto')
            request_validator(chosen, candidate)
            downloaded = download_document(chosen, candidate, max_bytes=self.settings.limits.max_download_bytes)
        else:
            downloaded = driver.download(chosen.url_requested, max_bytes=self.settings.limits.max_download_bytes)
        if downloaded.url_requested != chosen.url_requested:
            raise ValueError("download não corresponde ao documento solicitado")
        final_url = validate_redirect_chain(
            [downloaded.url_requested, *(downloaded.redirect_chain or []), downloaded.url_final],
            allowlist=self.settings.allowlist_hosts,
        )
        for hop in [*(downloaded.redirect_chain or []), downloaded.url_final]:
            adapter.validate_document_url(hop, candidate)
        if chosen.acquisition_request is not None and any(hop != chosen.url_requested for hop in [*(downloaded.redirect_chain or []), final_url]):
            raise ValueError('redirect POST não contratado')
        chosen.url_final = final_url
        self._validate_payload(downloaded)
        return downloaded

    def _validate_payload(self, downloaded: DownloadedBytes) -> None:
        content = downloaded.content
        if len(content) > self.settings.limits.max_download_bytes:
            raise ValueError(f"conteúdo acima do limite de {self.settings.limits.max_download_bytes} bytes")
        if not content:
            raise ValueError("download vazio")
        text_head = content[:2048].lstrip()[:64].lower()
        if has_pdf_header(content):
            return
        if text_head.startswith((b"<!doctype html", b"<html", b"<head", b"<body")):
            raise ValueError("página HTML recebida no lugar de PDF")
        raise ValueError("conteúdo não parece ser PDF (bytes iniciais inválidos)")


def new_run_id() -> str:
    return f"tpr-{uuid.uuid4().hex[:12]}"
