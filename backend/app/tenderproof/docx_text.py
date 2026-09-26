"""Bounded OOXML text inventory. Paragraph locations are not PDF page numbers."""
import hashlib
import io
import re
import zipfile
from xml.etree import ElementTree as ET

VERSION = 'tenderproof-docx-text/1'
W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'


def extract_docx(content):
    if len(content) > 15_000_000:
        raise ValueError('DOCX input limit')
    with zipfile.ZipFile(io.BytesIO(content)) as archive:
        entries = archive.infolist()
        names = [entry.filename for entry in entries]
        if (len(entries) > 1000 or len(set(names)) != len(names)
                or sum(e.file_size for e in entries) > 50_000_000):
            raise ValueError('DOCX package limit or duplicate entries')
        if 'word/document.xml' not in names:
            raise ValueError('DOCX document part missing')
        parts = [n for n in names if re.fullmatch(r'word/(?:document|header\d*|footer\d*|footnotes|endnotes|comments)\.xml', n)]
        paragraphs = []
        pending = []
        for name in parts:
            if archive.getinfo(name).file_size > 8_000_000:
                raise ValueError('DOCX XML part limit')
            xml = archive.read(name).decode('utf-8-sig')
            if re.search(r'<!DOCTYPE|<!ENTITY', xml, re.I):
                raise ValueError('DOCX XML declarations forbidden')
            root = ET.fromstring(xml)
            for index, node in enumerate(root.iter(W + 'p'), 1):
                text = ''.join((child.text or '') if child.tag == W+'t' else '\t' if child.tag == W+'tab' else '\n'
                    for child in node.iter() if child.tag in (W+'t', W+'tab', W+'br', W+'cr'))
                if text.strip():
                    paragraphs.append({'part': name, 'paragraph': index, 'text': text})
            for tag in ('altChunk', 'del', 'ins', 'object'):
                if next(root.iter(W+tag), None) is not None:
                    pending.append({'part': name, 'feature': tag})
        for name in names:
            if name.startswith(('word/media/', 'word/embeddings/')):
                pending.append({'part': name, 'feature': 'non_text_content'})
    return {'input_sha256': hashlib.sha256(content).hexdigest(), 'extractor_version': VERSION,
        'method': 'ooxml_paragraphs', 'paragraphs': paragraphs, 'pending_features': pending,
        'review_required': True, 'page_mapping_available': False, 'published': False}
