"""Independent review: POST limits, DNS guard and absence of fallback."""
import time

import httpx
import pytest

from app.tenderproof.http_driver import BoundedHTTPDriver, ContinuousDriver
from app.tenderproof.security import DestinationBlocked, TenderProofSettings
from app.tenderproof.solari_adapter import HtmlBlockError
from test_tenderproof_document_post import observed


def test_post_public_host_resolving_private_is_rejected_before_transport(observed, monkeypatch):
    adapter, candidate, document, _ = observed
    monkeypatch.setattr('app.tenderproof.http_driver.socket.getaddrinfo',
                        lambda *args, **kwargs: [(2, 1, 6, '', ('127.0.0.1', 443))])
    client = httpx.Client(transport=httpx.MockTransport(lambda request: pytest.fail('private DNS reached transport')))
    driver = BoundedHTTPDriver(adapter.source, TenderProofSettings(allowlist_hosts=adapter.allowed_hosts), client=client)
    driver.candidate = candidate
    try:
        with pytest.raises(DestinationBlocked, match='DNS'):
            driver.download_document(document, candidate, max_bytes=100)
        assert driver.requests == 0
    finally:
        driver.close()
    assert client.is_closed


@pytest.mark.parametrize('advertised', [False, True])
def test_post_response_byte_budget_without_trusting_content_length(observed, monkeypatch, advertised):
    adapter, candidate, document, _ = observed
    monkeypatch.setattr('app.tenderproof.http_driver._public_dns', lambda host: None)
    class Body(httpx.SyncByteStream):
        def __iter__(self):
            yield b'%PDF-1.7\n'
            yield b'x' * 101
    headers = {'Content-Length': '10000'} if advertised else {}
    client = httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(200, headers=headers, stream=Body())))
    driver = BoundedHTTPDriver(adapter.source, TenderProofSettings(allowlist_hosts=adapter.allowed_hosts), client=client)
    driver.candidate = candidate
    try:
        with pytest.raises(ValueError, match='limite'):
            driver.download_document(document, candidate, max_bytes=100)
        assert driver.requests == 1
    finally:
        driver.close()
    assert client.is_closed


def test_post_total_deadline_checked_on_stream_yield(observed, monkeypatch):
    adapter, candidate, document, _ = observed
    monkeypatch.setattr('app.tenderproof.http_driver._public_dns', lambda host: None)
    class Body(httpx.SyncByteStream):
        def __iter__(self):
            driver.deadline = time.monotonic() - 1
            yield b'%PDF-1.7\n'
    client = httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(200, stream=Body())))
    driver = BoundedHTTPDriver(adapter.source, TenderProofSettings(allowlist_hosts=adapter.allowed_hosts), client=client)
    driver.candidate = candidate
    try:
        with pytest.raises(TimeoutError, match='prazo total'):
            driver.download_document(document, candidate, max_bytes=100)
        assert driver.requests == 1
    finally:
        driver.close()
    assert client.is_closed


@pytest.mark.parametrize('failure', [HtmlBlockError('not PDF'), httpx.ConnectError('connection failed')])
def test_post_error_never_invokes_enabled_browser_fallback(observed, monkeypatch, failure):
    adapter, candidate, document, _ = observed
    monkeypatch.setenv('TENDERPROOF_BROWSER_LIVE_ENABLED', 'true')
    driver = ContinuousDriver(adapter.source, TenderProofSettings(allowlist_hosts=adapter.allowed_hosts), allow_browser=True)
    def fail(*args, **kwargs):
        raise failure
    monkeypatch.setattr(driver.http, 'download_document', fail)
    monkeypatch.setattr(driver, '_fallback', lambda *args: pytest.fail('POST attempted browser fallback'))
    try:
        with pytest.raises(type(failure)):
            driver.download_document(document, candidate, max_bytes=100)
        assert driver.browser is None
    finally:
        driver.close()
    assert driver.http.client.is_closed
