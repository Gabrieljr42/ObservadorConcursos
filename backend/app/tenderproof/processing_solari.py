"""Opt-in Solari Sandbox HTTP boundary; no calls at import/construction.

Official contract: https://docs.getsolari.com/api-reference/sandboxes .
Lifecycle and transfer live exercised 2026-09-07; first extraction blocked because
base lacks pypdf. The revised zipapp bundles a pinned pure-Python copy offline;
this revision awaits its own live authorization. No installs/templates/ports.
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from urllib.parse import quote, urlsplit

import httpx

from app.tenderproof.processing import ProcessingError, ProcessingLimits
from app.tenderproof.solari_budget import configured_budget


class SolariSandboxProcessor:
    hourly_usd = 0.086  # Conservative Free rate: 1 CPU + 2 GB; not a provider invoice.
    tariff_source = 'https://docs.getsolari.com/pricing (2026-09-07; Free 1 vCPU/2 GB)'
    base_url = 'https://api.getsolari.com'

    def __init__(self, api_key: str, *, live_authorized: bool = False,
                 authorized_resources: int = 1, authorized_seconds: float = 60,
                 http: httpx.Client | None = None):
        if not api_key:
            raise ProcessingError('provider_unavailable')
        self._api_key = api_key
        self._budget = configured_budget()
        self._authorized = live_authorized
        self._remaining = authorized_resources
        self._seconds = authorized_seconds
        self._http = http or httpx.Client(follow_redirects=False, trust_env=False)
        self._deadlines: dict[str, float] = {}
        from app.tenderproof.processing_bundle import build_processing_bundle
        self._bundle, self.bundle_manifest = build_processing_bundle()

    def _request(self, method, path, *, body=None, headers=None, content=None,
                 timeout=10, max_bytes=1_100_000, authenticated=True):
        url = self.base_url + path if path.startswith('/') else path
        parsed = urlsplit(url)
        if parsed.scheme != 'https' or parsed.netloc != 'api.getsolari.com' or parsed.username or parsed.fragment:
            raise ProcessingError('provider_failure')
        request_headers = dict(headers or {})
        if authenticated:
            request_headers['Authorization'] = 'Bearer ' + self._api_key
        started = time.monotonic()
        try:
            with self._http.stream(method, url, json=body, content=content, headers=request_headers,
                                   timeout=max(0.01, timeout), follow_redirects=False) as response:
                chunks, size = [], 0
                for chunk in response.iter_bytes():
                    size += len(chunk)
                    if size > max_bytes:
                        raise ProcessingError('output_limit')
                    if time.monotonic() - started > timeout:
                        raise ProcessingError('timeout')
                    chunks.append(chunk)
                raw = b''.join(chunks)
                return response.status_code, raw
        except ProcessingError:
            raise
        except httpx.TimeoutException:
            raise ProcessingError('timeout') from None
        except Exception:
            raise ProcessingError('provider_failure') from None

    def _json(self, method, path, **kwargs):
        status, raw = self._request(method, path, **kwargs)
        if status not in (200, 201):
            raise ProcessingError('provider_failure')
        try:
            result = json.loads(raw)
            if not isinstance(result, dict):
                raise ValueError()
            return result
        except Exception:
            raise ProcessingError('provider_failure') from None

    def create(self, key: str, limits: ProcessingLimits) -> str:
        if not self._authorized or self._remaining < 1 or limits.total_seconds > self._seconds:
            raise ProcessingError('live_authorization_required')
        self._remaining -= 1  # Ambiguous response consumes authorization; never create a replacement.
        reservation = self._budget.reserve('sandbox', maximum_seconds=limits.total_seconds,
                                           hourly_usd=str(self.hourly_usd), tariff=self.tariff_source) if self._budget else None
        started = time.monotonic()
        data = self._json('POST', '/sandboxes', headers={'Idempotency-Key': key},
                          body={'kind': 'sandbox', 'template': 'base', 'cpu': 1, 'memMb': 2048,
                                'timeoutMs': max(1000, int(limits.total_seconds * 1000)),
                                'lifecycle': {'onTimeout': 'kill', 'autoResume': False},
                                'metadata': {'tenderproof_job': key}, 'envs': {}},
                          timeout=min(10, limits.operation_seconds, limits.total_seconds))
        resource = data.get('sandboxId')
        if not isinstance(resource, str) or not resource:
            raise ProcessingError('provider_failure')
        self._deadlines[resource] = started + limits.total_seconds
        if reservation:
            try:
                self._budget.created(reservation, resource)
            except Exception:
                self.close(resource)
                raise
        return resource

    def process(self, resource, content, limits, cancelled):
        prefix = '/sandboxes/' + quote(resource, safe='')

        def remaining():
            if cancelled():
                raise ProcessingError('cancelled')
            available = self._deadlines.get(resource, 0) - time.monotonic()
            if available <= 0:
                raise ProcessingError('timeout')
            return min(available, limits.operation_seconds)

        for name, payload in [('tenderproof-worker.pyz', self._bundle), ('tenderproof-input.pdf', content)]:
            signed = self._json('GET', prefix + '/files/upload-url?path=' + quote('/tmp/' + name, safe=''),
                                timeout=remaining())
            status, _ = self._request('PUT', signed.get('url', ''), content=payload,
                                      authenticated=False, timeout=remaining())
            if status != 200:
                raise ProcessingError('provider_failure')
        result = self._json('POST', prefix + '/exec', timeout=remaining(),
                            body={'cmd': 'python3',
                                  'args': ['-I', '-S', '/tmp/tenderproof-worker.pyz', '/tmp/tenderproof-input.pdf',
                                           '/tmp/tenderproof-output.json', str(limits.max_pages), str(limits.max_output_bytes)],
                                  'timeoutMs': max(1, int(remaining() * 1000))}, max_bytes=4096)
        if result.get('exitCode') not in (0, 1):
            raise ProcessingError('provider_failure')
        signed = self._json('GET', prefix + '/files/download-url?path=%2Ftmp%2Ftenderproof-output.json',
                            timeout=remaining())
        status, output = self._request('GET', signed.get('url', ''), authenticated=False,
                                       timeout=remaining(), max_bytes=limits.max_output_bytes)
        if status != 200:
            raise ProcessingError('provider_failure')
        return output

    def close(self, resource):
        # DELETE 200 {ok:true} is documented as completed release for Sandbox
        # (different from Browser DELETE 204, which only acknowledges a request).
        result = self._json('DELETE', '/sandboxes/' + quote(resource, safe=''), timeout=10)
        if result.get('ok') is True and self._budget:
            self._budget.closed(resource)
        return result.get('ok') is True

    def status(self, resource):
        status, raw = self._request('GET', '/sandboxes/' + quote(resource, safe=''), timeout=10)
        if status != 200:
            return 'unknown'  # 404 is not proof of termination.
        try:
            state = json.loads(raw).get('state')
            return state if state in ('running', 'paused', 'gone', 'releasing', 'starting', 'archived') else 'unknown'
        except Exception:
            return 'unknown'
