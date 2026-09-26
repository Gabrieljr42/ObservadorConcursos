import json

import httpx
import pytest

from app.tenderproof.facepe_adapter import FacepeAdapter
from app.tenderproof.facepe_listing import SAD_ROOT
from app.tenderproof.http_driver import BoundedHTTPDriver

FOLDER_ID = 'aNewFolder987654'
FILE_ID = 'aNewDocument9876'
FOLDER = 'https://drive.google.com/drive/folders/' + FOLDER_ID + '?usp=sharing'
DOWNLOAD = 'https://drive.usercontent.google.com/uc?id=' + FILE_ID + '&export=download'


def sad(folder=FOLDER):
    return f'<div itemprop="articleBody"><p><span><strong>Fundação FACEPE</strong></span></p><p><a href="{folder}">Seleção 2031</a></p></div>'


def drive(name='2.Edital.pdf'):
    return f'<table role="grid" aria-rowcount="1"><tr data-id="{FILE_ID}" data-target="doc" aria-rowindex="1"><td data-column-id="16"><div aria-hidden="true"><svg><title>PDF</title></svg></div><strong>{name}</strong></td></tr></table>'


def composite(name='2.Edital.pdf'):
    return json.dumps({'format': 'facepe-sad-drive/1', 'sad_html': sad(), 'folder_url': FOLDER, 'drive_html': drive(name)})


def test_registered_http_pipeline_binds_current_sad_folder_and_download(monkeypatch):
    calls = []
    def handle(request):
        url = str(request.url)
        calls.append(url)
        if url == SAD_ROOT:
            return httpx.Response(200, text=sad())
        if url == FOLDER:
            return httpx.Response(200, text=drive())
        if url == DOWNLOAD:
            return httpx.Response(303, headers={'location': DOWNLOAD.replace('/uc?', '/download?')})
        assert url == DOWNLOAD.replace('/uc?', '/download?')
        return httpx.Response(200, content=b'%PDF-1.7\nfixture')
    monkeypatch.setattr('app.tenderproof.http_driver._public_dns', lambda _: None)
    driver = BoundedHTTPDriver('facepe_selection', client=httpx.Client(transport=httpx.MockTransport(handle)))
    try:
        page = driver.adapter.parse_listing(driver.open_listing(SAD_ROOT), SAD_ROOT)
        candidate = page.candidates[0]
        assert candidate.external_id == FOLDER_ID and not page.terminal_evidence
        html = driver.open_detail(candidate.detail_url_observed)
        docs = driver.adapter.documents(html, candidate)
        assert len(docs) == 1
        selected = driver.adapter.choose_document(docs)
        assert driver.download(selected.url_requested, max_bytes=1000).content.startswith(b'%PDF')
        assert calls == [SAD_ROOT, SAD_ROOT, FOLDER, DOWNLOAD, DOWNLOAD.replace('/uc?', '/download?')]
    finally:
        driver.close()


def test_redirect_cannot_switch_to_another_valid_public_drive_file(monkeypatch):
    calls = []
    def handle(request):
        calls.append(str(request.url))
        return httpx.Response(303, headers={'location': DOWNLOAD.replace(FILE_ID, 'otherDocument9876')})
    monkeypatch.setattr('app.tenderproof.http_driver._public_dns', lambda _: None)
    driver = BoundedHTTPDriver('facepe_selection', client=httpx.Client(transport=httpx.MockTransport(handle)))
    try:
        driver.set_candidate(driver.adapter.candidate_from_url(SAD_ROOT + '#folder-' + FOLDER_ID))
        with pytest.raises(ValueError, match='altera arquivo'):
            driver.download(DOWNLOAD, max_bytes=1000)
        assert calls == [DOWNLOAD]
    finally:
        driver.close()


@pytest.mark.parametrize('name', ['3.Errata ao Edital.pdf', '4.Retificação do Edital.pdf'])
def test_amendment_requires_review_without_becoming_original(name):
    adapter = FacepeAdapter()
    candidate = adapter.candidate_from_url(SAD_ROOT + '#folder-' + FOLDER_ID)
    docs = adapter.documents(composite(name), candidate)
    assert docs[0].kind == 'retificacao'
    with pytest.raises(ValueError):
        adapter.choose_document(docs)


@pytest.mark.parametrize('mutation', ['folder_url', 'sad_html', 'candidate_id'])
def test_detail_must_keep_official_agency_folder_binding(mutation):
    adapter = FacepeAdapter()
    candidate = adapter.candidate_from_url(SAD_ROOT + '#folder-' + FOLDER_ID)
    data = json.loads(composite())
    if mutation == 'folder_url':
        data['folder_url'] = FOLDER.replace(FOLDER_ID, 'unrelatedFolder9')
    elif mutation == 'sad_html':
        data['sad_html'] = sad().replace('FACEPE', 'Outra agência')
    else:
        candidate = candidate.model_copy(update={'external_id': 'unrelatedFolder9'})
    with pytest.raises(ValueError):
        adapter.documents(json.dumps(data), candidate)


@pytest.mark.parametrize('url', [DOWNLOAD + '&authuser=1', DOWNLOAD.replace('https:', 'http:'),
    DOWNLOAD.replace('drive.usercontent.google.com', 'accounts.google.com'), DOWNLOAD + '#x'])
def test_document_destination_is_narrow(url):
    adapter = FacepeAdapter()
    candidate = adapter.candidate_from_url(SAD_ROOT + '#folder-' + FOLDER_ID)
    with pytest.raises(ValueError):
        adapter.validate_document_url(url, candidate)
