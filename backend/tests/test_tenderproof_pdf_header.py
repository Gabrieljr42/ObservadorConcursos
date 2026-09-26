import hashlib
import json
from pathlib import Path
from io import BytesIO
import pytest
from pypdf import PdfReader
from app.tenderproof.pdf_header import has_pdf_header
from app.tenderproof.acquisition import AcquisitionService
from app.tenderproof.http_driver import BoundedHTTPDriver
from app.tenderproof.solari_adapter import DownloadedBytes

@pytest.mark.parametrize('prefix',[b'',b'\n\n',b' '*16,b'\t\r\n '])
def test_ascii_prefix(prefix):
    raw=prefix+b'%PDF-1.7\n'
    before=hashlib.sha256(raw).hexdigest()
    assert has_pdf_header(raw)
    assert hashlib.sha256(raw).hexdigest()==before

@pytest.mark.parametrize('raw',[b' '*17+b'%PDF-1.7',b'\xef\xbb\xbf%PDF-1.7',b'x%PDF-1.7',b'<html>%PDF-1.7',b'<script>%PDF-1.7',b'\x00%PDF-1.7',b'\x0b%PDF-1.7',b'%PDFx',b''])
def test_reject_non_ascii_whitespace_or_excess(raw):
    assert not has_pdf_header(raw)

def test_observed_fapesc_raw_hash_and_parser():
    root=Path(__file__).parent/'fixtures/tenderproof_batch99_regions'
    row=json.loads((root/'fapesc-pdf-manifest.json').read_text(encoding='utf-8'))['documents'][0]
    raw=(root/row['file']).read_bytes()
    assert raw.startswith(b'\n\n%PDF-')
    assert len(raw)==715217
    assert hashlib.sha256(raw).hexdigest()==row['sha256']=='92564af99aebb45866f7ef60f5c34c08c1241ca08725b55623d8f06ac56ed8ae'
    assert has_pdf_header(raw)
    pdf=PdfReader(BytesIO(raw))
    assert len(pdf.pages)==25 and 'FAPESC' in pdf.pages[0].extract_text()
    # Production parser stays strict: header acceptance alone is not validity.
    from pypdf.errors import PdfReadError
    with pytest.raises(PdfReadError):PdfReader(BytesIO(raw),strict=True)
    with pytest.raises(ValueError):
        BoundedHTTPDriver._html(DownloadedBytes(url_requested=row['url'],url_final=row['url'],content=raw,content_type='application/pdf'))
