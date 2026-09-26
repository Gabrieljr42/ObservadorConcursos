"""Bounded public HTTP acquisition with an explicitly enabled browser fallback."""
from __future__ import annotations

from app.tenderproof.pdf_header import has_pdf_header

import ipaddress
import os
import socket
import time
from dataclasses import replace
from urllib.parse import urljoin, urlsplit

import httpx

from app.tenderproof.security import DestinationBlocked, TenderProofSettings
from app.tenderproof.source_adapters import get_source_adapter, SourcePageBlocked
from app.tenderproof.tls_chain import source_tls_verification
from app.tenderproof.solari_adapter import DownloadedBytes, HtmlBlockError, SolariBrowserAdapter, SolariConfig


def _public_dns(host):
    addresses = socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
    if not addresses or any(not ipaddress.ip_address(item[4][0]).is_global for item in addresses):
        raise DestinationBlocked("destino DNS não público")


class BoundedHTTPDriver:
    """One job, one deadline, bounded redirects/bytes, no credentials or cookies.

    An injected httpx client is useful for independent deterministic fixtures.
    Production always verifies TLS and ignores proxy/environment credentials.
    """
    session_id = None
    replay_available = False

    def __init__(self, source, settings=None, *, client=None):
        self.adapter = get_source_adapter(source)
        self.settings = settings or TenderProofSettings.from_env()
        self.deadline = time.monotonic() + self.settings.limits.total_timeout_s
        self.client = client or httpx.Client(follow_redirects=False, trust_env=False, timeout=12,
                                             verify=source_tls_verification(source),
                                             headers={"User-Agent": "ObservadorDeConcursos/1.0"})
        self.candidate = None
        self._notes = []
        self.requests = 0
        self.request_guard = None

    def remaining(self):
        remaining = self.deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError("prazo total de aquisição excedido")
        return remaining

    def _fetch(self, url, validator, max_bytes, *, acquisition_request=None, public_listing_request=None):
        if public_listing_request is not None:
            from app.tenderproof.fapeam_listing import FapeamListingRequest
            from app.tenderproof.fapern_listing import FapernDirectoryRequest
            if type(public_listing_request) not in (FapeamListingRequest,FapernDirectoryRequest) or acquisition_request is not None:
                raise ValueError('contrato de requisição de listagem inválido')
            public_listing_request.transport(url, self.adapter.source)
            max_bytes = min(max_bytes, (4 if type(public_listing_request) is FapernDirectoryRequest else 2)*1024*1024)
        requested, chain = url, []
        for _ in range(4):
            if self.request_guard is not None:
                self.request_guard()
            self.remaining()
            validator(url)
            _public_dns(urlsplit(url).hostname)
            if self.requests >= self.settings.limits.max_navigations:
                raise ValueError("limite de requisições por trabalho atingido")
            self.requests += 1
            header_provider = getattr(self.adapter, "request_headers", None)
            public_headers = header_provider(url) if callable(header_provider) else {}
            document_headers=getattr(self.adapter,'document_request_headers',None)
            if self.candidate is not None and callable(document_headers):
                public_headers={**public_headers,**document_headers(url,self.candidate)}
            if not isinstance(public_headers, dict) or any(
                not isinstance(name, str) or name.lower() not in ("user-agent", "accept", "x-tenantid", "referer") or not isinstance(value, str)
                or len(value) > 500 or '\r' in value or '\n' in value
                or (name.lower()=='referer' and (self.candidate is None or value!=self.candidate.detail_url_observed))
                for name, value in public_headers.items()
            ):
                raise ValueError("cabeçalhos públicos fora do contrato de aquisição")
            request_options = {}
            method = "GET"
            if public_listing_request is not None:
                request = public_listing_request.transport(url, self.adapter.source)
                method = request['method']
                public_headers = {**public_headers, 'Content-Type': request['content_type']}
                # Only the fixed public RN Drive request can supply Depth and
                # Basic identification; it encodes a published share token with
                # an empty password, never user or environment credentials.
                public_headers.update(request.get('headers',{}))
                request_options['content'] = request['body'].encode('ascii')
            if acquisition_request is not None:
                from app.tenderproof.contracts import DocumentAcquisitionRequest
                request = DocumentAcquisitionRequest.model_validate(acquisition_request)
                method = request.method
                public_headers = {**public_headers, "Content-Type": request.content_type}
                request_options['content'] = request.body.encode('ascii')
            with self.client.stream(method, url, headers=public_headers, timeout=max(0.1, min(12, self.remaining())), **request_options) as response:
                chain.append(url)
                if response.is_redirect:
                    if acquisition_request is not None or public_listing_request is not None:
                        raise ValueError("redirect POST não contratado")
                    target = urljoin(url, response.headers.get("location", ""))
                    validator(target)  # BEFORE issuing the next request
                    if target in chain:
                        raise ValueError("redirect circular")
                    url = target
                    continue
                response.raise_for_status()
                length = response.headers.get("content-length")
                if length and int(length) > max_bytes:
                    raise ValueError("Content-Length excede limite")
                chunks, size = [], 0
                # Inspect each transport yield: buffering to 64 KiB can hide a
                # slow stream from the total deadline for minutes.
                for chunk in response.iter_bytes():
                    self.remaining()
                    size += len(chunk)
                    if size > max_bytes:
                        raise ValueError("resposta excede limite de bytes")
                    chunks.append(chunk)
                self._notes.append(f"http: {response.status_code}, {size} bytes, {len(chain)-1} redirects")
                return DownloadedBytes(url_requested=requested, url_final=url,
                                       content=b"".join(chunks), content_type=response.headers.get("content-type"),
                                       redirect_chain=chain, mechanism="http",
                                       pagination_headers={k:response.headers[k] for k in ('x-wp-total','x-wp-totalpages') if k in response.headers})
        raise ValueError("limite de redirects excedido")

    def _html(self,result):
        if has_pdf_header(result.content):
            raise ValueError("documento recebido no lugar de listagem/detalhe")
        from bs4 import UnicodeDammit
        encoding=getattr(self.adapter,'html_encoding',None)
        if encoding:return result.content.decode(encoding)
        return UnicodeDammit(result.content, is_html=True).unicode_markup or ""

    def open_listing(self, url):
        acquire = getattr(self.adapter, 'acquire_listing', None)
        if callable(acquire):
            return acquire(url, self._fetch)
        return self._html(self._fetch(url, self.adapter.validate_listing_url, 2 * 1024 * 1024))

    def set_candidate(self, candidate):
        self.adapter.validate_detail_url(candidate.detail_url_observed)
        # Section based sources (for example FATEC and FAPESE) intentionally
        # share one listing/detail URL. Their external identity is bound to the
        # observed section title, so reconstruct with that title and retain
        # the same strict source/ID comparison used by URL-addressed sources.
        expected = self.adapter.candidate_from_url(
            candidate.detail_url_observed, candidate.title_observed
        )
        if (candidate.source, candidate.external_id) != (expected.source, expected.external_id):
            raise ValueError('candidato incompatível com destino do driver')
        self.candidate = candidate

    def open_detail(self, url):
        if self.candidate is None or self.candidate.detail_url_observed != url:
            self.candidate = self.adapter.candidate_from_url(url)
        self.set_candidate(self.candidate)
        acquire = getattr(self.adapter, 'acquire_detail', None)
        if callable(acquire):
            detail = acquire(url, self.candidate, self._fetch)
            if not isinstance(detail, str) or len(detail.encode('utf-8')) > 2 * 1024 * 1024:
                raise ValueError('detalhe adquirido excede contrato de tamanho')
            self.adapter.confirm_identity(self.candidate, detail, url)
            return detail
        # Detail redirects cannot silently select a different contest.
        def validate(target):
            self.adapter.validate_detail_url(target)
            if target != url:
                raise ValueError("redirect de detalhe altera identidade")
        html = self._html(self._fetch(url, validate, 2 * 1024 * 1024))
        resource_provider = getattr(self.adapter, 'detail_resource_urls', None)
        if not callable(resource_provider):
            return html
        urls = resource_provider(html, url)
        validator = getattr(self.adapter, 'validate_detail_resource_url', None)
        composer = getattr(self.adapter, 'compose_detail', None)
        if (not isinstance(urls, (list, tuple)) or len(urls) > 2
                or any(not isinstance(item, str) for item in urls)
                or len(set(urls)) != len(urls) or not callable(validator) or not callable(composer)):
            raise ValueError('contrato de recursos do detalhe inválido')
        # Validate the entire plan before issuing any supplementary request.
        for resource_url in urls:
            validator(resource_url, self.candidate)
        resources = []
        for resource_url in urls:
            def validate_resource(target, expected=resource_url):
                validator(target, self.candidate)
                if target != expected:
                    raise ValueError('redirect altera recurso documental associado')
            response = self._fetch(resource_url, validate_resource, 2 * 1024 * 1024)
            resources.append({'url': resource_url, 'body': self._html(response)})
        composed = composer(html, url, resources)
        if not isinstance(composed, str) or len(composed.encode('utf-8')) > 2 * 1024 * 1024:
            raise ValueError('detalhe composto excede contrato de tamanho')
        return composed

    def download(self, url, *, max_bytes):
        if self.candidate is None:
            raise ValueError("download exige detalhe associado")
        redirect_validator = getattr(self.adapter, 'validate_document_redirect', None)
        def validate(target):
            self.adapter.validate_document_url(target, self.candidate)
            if callable(redirect_validator):
                redirect_validator(target, url, self.candidate)
        result = self._fetch(url, validate,
                             min(max_bytes, self.settings.limits.max_download_bytes))
        if not has_pdf_header(result.content):
            raise HtmlBlockError("resposta não é PDF")
        return result

    def download_workbook(self,document,candidate,*,max_bytes):
        if self.adapter.source!='fapeg_selection' or document.file_format!='xlsx' or self.candidate!=candidate:
            raise ValueError('Planilha fora do candidato associado')
        self.adapter.validate_document_url(document.url_requested,candidate)
        from app.tenderproof.fapeg_workbook import acquire_public_workbook
        result,_metadata=acquire_public_workbook(document.url_requested,self._fetch,max_bytes=min(max_bytes,self.settings.limits.max_download_bytes))
        return result

    def download_document(self, document, candidate, *, max_bytes):
        if self.candidate is None or (candidate.source,candidate.external_id,candidate.detail_url_observed)!=(self.candidate.source,self.candidate.external_id,self.candidate.detail_url_observed):
            raise ValueError('exportação POST exige detalhe associado')
        if document.acquisition_request is None:
            raise ValueError('download_document exige contrato POST explícito')
        validator = getattr(self.adapter, 'validate_document_request', None)
        if not callable(validator):
            raise ValueError('fonte não possui contrato POST')
        validator(document,candidate)
        def validate(target):
            self.adapter.validate_document_url(target,candidate)
            if target != document.url_requested:
                raise ValueError('destino POST alterou identidade')
            validator(document,candidate)
        result = self._fetch(document.url_requested,validate,min(max_bytes,self.settings.limits.max_download_bytes),acquisition_request=document.acquisition_request)
        if not has_pdf_header(result.content):
            raise HtmlBlockError('resposta POST não é PDF')
        return result

    def observed_json(self): return []
    def session_records(self): return []
    def replay_url(self): return None
    def diagnostics(self): return list(self._notes)
    def close(self): self.client.close()


class ContinuousDriver:
    """Browser fallback is lazy, single-use and contained in the job deadline."""
    def __init__(self, source, settings=None, *, allow_browser=False):
        self.source = source
        self.settings = settings or TenderProofSettings.from_env()
        self.http = BoundedHTTPDriver(source, self.settings)
        self.browser = None
        self.allow_browser = allow_browser
        self._detail_url = None
        self._using_browser_detail = False
        self._notes = []
        self._session_observer = None

    def set_request_guard(self, guard):
        self.http.request_guard = guard

    def set_session_observer(self, observer):
        if self.browser is not None:
            raise RuntimeError("observador precisa ser registrado antes do browser")
        self._session_observer = observer

    def _fallback(self, reason):
        if not self.allow_browser or os.getenv("TENDERPROOF_BROWSER_LIVE_ENABLED", "false").lower() != "true":
            raise ValueError("aquisição HTTP inconclusiva; fallback browser não habilitado")
        remaining = self.http.remaining()
        if remaining <= 45:
            raise TimeoutError("janela restante insuficiente para browser e encerramento")
        if self.browser is None:
            limits = replace(self.settings.limits, total_timeout_s=remaining-45, replay_deadline_s=0)
            self.browser = SolariBrowserAdapter(SolariConfig.from_env(), replace(self.settings, limits=limits),
                                               source=self.source, session_observer=self._session_observer)
            self._notes.append(f"fallback browser: {reason}; reserva de encerramento=45s")
        return self.browser

    def open_listing(self, url):
        self.http.adapter.validate_listing_url(url)
        try:
            html = self.http.open_listing(url)
            page = self.http.adapter.parse_listing(html, url, 1)
            # A navigation menu can exist in a JavaScript shell with zero
            # loaded contests (IBGP). Links alone do not avoid browser fallback.
            if page.candidates or page.empty_evidence:
                return html
        except (httpx.HTTPError, OSError, SourcePageBlocked):
            if not self.allow_browser:
                raise
        if not self.allow_browser:
            return html
        return self._fallback("listagem HTTP sem candidatos/estado conclusivo").open_listing(url)

    def set_candidate(self, candidate):
        self.http.set_candidate(candidate)

    def open_detail(self, url):
        self.http.adapter.validate_detail_url(url)
        self._detail_url = url
        try:
            html = self.http.open_detail(url)
            if self.http.adapter.documents(html, self.http.candidate):
                return html
        except (httpx.HTTPError, OSError, SourcePageBlocked):
            if not self.allow_browser:
                raise
        if not self.allow_browser:
            return html
        self._using_browser_detail = True
        return self._fallback("detalhe HTTP sem documentos").open_detail(url)

    def download(self, url, *, max_bytes):
        if self._using_browser_detail:
            return self.browser.download(url, max_bytes=max_bytes)
        try:
            return self.http.download(url, max_bytes=max_bytes)
        except (httpx.HTTPError, HtmlBlockError, OSError):
            if not self.allow_browser:
                raise
        browser = self._fallback("download HTTP indisponível")
        browser.open_detail(self._detail_url)
        self._using_browser_detail = True
        return browser.download(url, max_bytes=max_bytes)

    def download_workbook(self,document,candidate,*,max_bytes):
        if self._using_browser_detail:raise ValueError('Planilha exige detalhe HTTP associado')
        return self.http.download_workbook(document,candidate,max_bytes=max_bytes)

    def download_document(self, document, candidate, *, max_bytes):
        # POST export is public HTTP only; never replay through a browser or GET.
        if self._using_browser_detail:
            raise ValueError('exportação POST exige detalhe HTTP associado')
        return self.http.download_document(document,candidate,max_bytes=max_bytes)

    @property
    def session_id(self): return self.browser.session_id if self.browser else None
    @property
    def replay_available(self): return self.browser.replay_available if self.browser else False
    def replay_url(self): return self.browser.replay_url() if self.browser else None
    def observed_json(self): return self.browser.observed_json() if self.browser else []
    def session_records(self): return self.browser.session_records() if self.browser else []
    def diagnostics(self): return self.http.diagnostics() + self._notes + (self.browser.diagnostics() if self.browser else [])
    def close(self):
        try:
            if self.browser:
                self.browser.close()
        finally:
            self.http.close()


def build_continuous_driver(source, settings=None, allow_browser=False):
    return ContinuousDriver(source, settings, allow_browser=allow_browser)
