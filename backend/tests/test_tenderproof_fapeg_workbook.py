import json
import pytest
from app.tenderproof.fapeg_workbook import acquire_public_workbook,share_folder
from app.tenderproof.solari_adapter import DownloadedBytes

SHARE='https://goiasgovbr-my.sharepoint.com/:x:/g/personal/public_department/'+('a'*40)+'?e=AbCd12'
GUID='12345678-1234-4321-9876-123456789abc'
ROOT='https://goiasgovbr-my.sharepoint.com/personal/public_department/_layouts/15/'
VIEWER=ROOT+'Doc.aspx?sourcedoc=%7B'+GUID+'%7D&action=default'
DOWNLOAD=ROOT+'download.aspx?UniqueId='+GUID+'&Translate=false'
MIME='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'


def run(fields=None,viewer=VIEWER,body=b'PK\x03\x04package',mime=MIME,redirect=None):
    requests=[]
    metadata={'FileName':'New academic calls.xlsx','FileGetUrl':DOWNLOAD,'ViewOnly':False}
    metadata.update(fields or {})
    def fetch(url,validate,max_bytes):
        requests.append(url);validate(url)
        if url==SHARE:
            validate(viewer)
            return DownloadedBytes(url_requested=url,url_final=viewer,content=json.dumps(metadata).encode(),content_type='text/html',redirect_chain=[url,viewer])
        if redirect:validate(redirect)
        return DownloadedBytes(url_requested=url,url_final=url,content=body,content_type=mime)
    return acquire_public_workbook(SHARE,fetch,max_bytes=1024),requests


def test_public_viewer_identity_and_bytes_preserved():
    (data,meta),requests=run()
    assert data.url_requested==SHARE and data.url_final==DOWNLOAD
    assert meta['document_id']==GUID and data.content==b'PK\x03\x04package'
    assert requests==[SHARE,DOWNLOAD]


@pytest.mark.parametrize('fields',[
    {'ViewOnly':True},{'FileName':'programmes.xlsm'},
    {'FileGetUrl':DOWNLOAD.replace(GUID,'98765432-1234-4321-9876-123456789abc')},
    {'FileGetUrl':DOWNLOAD.replace('public_department','other_department')},
    {'FileGetUrl':DOWNLOAD+'&access_token=unobserved'},
])
def test_viewer_permissions_and_identity_reject_download(fields):
    with pytest.raises(ValueError):run(fields=fields)


@pytest.mark.parametrize('viewer',[
    'https://login.microsoftonline.com/',VIEWER.replace('public_department','another_department'),
    VIEWER+'&sourcedoc=%7B'+GUID+'%7D',
])
def test_redirect_requires_same_public_folder_and_unique_id(viewer):
    with pytest.raises(ValueError):run(viewer=viewer)


def test_authentication_html_and_unobserved_download_redirect_fail_closed():
    with pytest.raises(ValueError):run(body=b'<html>sign in</html>')
    with pytest.raises(ValueError):run(mime='text/html')
    with pytest.raises(ValueError):run(redirect='https://login.microsoftonline.com/')
    with pytest.raises(ValueError):run(body=b'PK\x03\x04'+b'x'*1024)


@pytest.mark.parametrize('url',[SHARE.replace('https:','http:'),SHARE.replace('goiasgovbr-my','other'),SHARE+'&auth=secret',SHARE+'#x'])
def test_only_observed_fapeg_tenant_share_shape(url):
    with pytest.raises(ValueError):share_folder(url)


def test_acquisition_requires_manifest_membership_and_preserves_pdf_validation():
    from types import SimpleNamespace
    from app.tenderproof.acquisition import AcquisitionService
    from app.tenderproof.fapeg_adapter import FapegAdapter
    from app.tenderproof.contracts import DocumentCandidate
    candidate=FapegAdapter().candidate_from_url('https://goias.gov.br/fapeg/new-call-23-2028/','23/2028 | Future call')
    doc=DocumentCandidate(doc_id='workbook',title='Academic programmes',url_requested=SHARE,kind='anexo',file_format='xlsx')
    (download,_),_=run()
    from dataclasses import replace
    from app.tenderproof.security import TenderProofSettings
    service=AcquisitionService(replace(TenderProofSettings(),allowlist_hosts=FapegAdapter().allowed_hosts))
    driver=SimpleNamespace(download_workbook=lambda *a,**k:download,download=lambda *a,**k:download)
    with pytest.raises(ValueError):service.fetch_document(driver,candidate=candidate,document=doc)
    service.last_candidate=(candidate.source,candidate.external_id,candidate.detail_url_observed)
    service.last_documents=[doc]
    assert service.fetch_document(driver,candidate=candidate,document=doc).content==download.content
    pdf=doc.model_copy(update={'file_format':'pdf'})
    service.last_documents=[pdf]
    with pytest.raises(ValueError):service.fetch_document(driver,candidate=candidate,document=pdf)


def test_source_manifest_includes_workbook_and_original_without_omitting_link():
    from app.tenderproof.fapeg_adapter import FapegAdapter
    adapter=FapegAdapter();candidate=adapter.candidate_from_url('https://goias.gov.br/fapeg/new-call-23-2028/','23/2028 | Future call')
    html='<article><h1 class="entry-title">FAPEG 23/2028</h1><div class="entry-content"><a href="https://goias.gov.br/fapeg/wp-content/uploads/2028/09/original.pdf">Edital</a><a href="'+SHARE+'">Academic programmes</a></div></article>'
    docs=adapter.documents(html,candidate)
    assert len(docs)==2 and adapter.choose_document(docs).file_format=='pdf'
    assert [d.file_format for d in adapter.supplementary_documents(docs,adapter.choose_document(docs))]==['xlsx']
