import pytest
from app.tenderproof.fapern_drive import parse_directory, canonical_path, ROOT


def response(path,collection=False):
    return f'<d:response><d:href>{path}</d:href><d:propstat><d:prop><d:resourcetype>{"<d:collection/>" if collection else ""}</d:resourcetype><d:getcontentlength>123</d:getcontentlength></d:prop><d:status>HTTP/1.1 200 OK</d:status></d:propstat></d:response>'


def document(*items):
    return ('<d:multistatus xmlns:d="DAV:">'+''.join(items)+'</d:multistatus>').encode()


def test_unicode_names_direct_children_and_identity():
    rows=parse_directory(document(response(ROOT,True),response(ROOT+'Sele%c3%a7%c3%a3o%2042.pdf')),ROOT)
    assert rows[0]['name']=='Seleção 42.pdf' and rows[0]['bytes']==123
    assert rows[0]['url']=='https://drive.rn.gov.br/public.php/webdav/Sele%C3%A7%C3%A3o%2042.pdf'


@pytest.mark.parametrize('path',['https://evil.invalid/x','//evil.invalid/x',ROOT+'../x',ROOT+'%2e%2e/x',ROOT+'%252e%252e/x',ROOT+'x?download=1',ROOT+'%00',ROOT+'x\\y'])
def test_outside_paths_and_double_encoding_rejected(path):
    with pytest.raises(ValueError): canonical_path(path)


def test_duplicate_nested_and_missing_root_rejected():
    for data in [document(response(ROOT,True),response(ROOT+'a.pdf'),response(ROOT+'a.pdf')),
                 document(response(ROOT,True),response(ROOT+'child/nested.pdf')),
                 document(response(ROOT+'a.pdf')),
                 b'<!DOCTYPE a [<!ENTITY x "value">]><a/>']:
        with pytest.raises(ValueError):parse_directory(data,ROOT)
