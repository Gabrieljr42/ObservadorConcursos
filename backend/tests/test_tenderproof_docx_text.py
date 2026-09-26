import io
import zipfile
import pytest
from app.tenderproof.docx_text import extract_docx


def package(parts):
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w') as z:
        for name, text in parts.items(): z.writestr(name, text)
    return buffer.getvalue()


def xml(text):
    return '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:p><w:r><w:t>'+text+'</w:t></w:r></w:p></w:document>'


def test_body_and_notes_keep_distinct_locations_without_inventing_pages():
    r = extract_docx(package({'word/document.xml':xml('Declaração'), 'word/footnotes.xml':xml('Nota')}))
    assert [p['text'] for p in r['paragraphs']] == ['Declaração','Nota']
    assert r['paragraphs'][1]['part'] == 'word/footnotes.xml'
    assert r['review_required'] and not r['page_mapping_available']


def test_entities_are_rejected_and_images_remain_pending():
    with pytest.raises(ValueError, match='declarations'):
        extract_docx(package({'word/document.xml':'<!DOCTYPE test [<!ENTITY x "bad">]>'+xml('&x;')}))
    r=extract_docx(package({'word/document.xml':xml('Texto'), 'word/media/image.png':b'image'}))
    assert r['pending_features'][0]['feature']=='non_text_content'
