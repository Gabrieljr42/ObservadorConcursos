"""Strict parser for the public RN Drive directory linked by Portal do Cidadão.

The share token must come from that official service. Parsing one directory is
not proof of complete source coverage or personnel eligibility.
"""
import re
import xml.etree.ElementTree as ET
from urllib.parse import unquote, urlsplit, quote

ROOT = '/public.php/webdav/'


def canonical_path(value):
    parsed = urlsplit(value)
    if parsed.scheme or parsed.netloc or parsed.query or parsed.fragment:
        raise ValueError('caminho WebDAV fora do compartilhamento público')
    path = unquote(parsed.path, errors='strict')
    if (not path.startswith(ROOT) or '\\' in path or any(ord(c)<32 for c in path)
            or '%' in path or any(part in ('.','..') for part in path.split('/'))):
        raise ValueError('caminho WebDAV inválido')
    return path


def parse_directory(content, requested_path):
    parent = canonical_path(requested_path)
    if not parent.endswith('/') or len(content)>4*1024*1024:
        raise ValueError('diretório ou tamanho de resposta inválido')
    if re.search(br'<!\s*(?:DOCTYPE|ENTITY)\b',content,re.I):
        raise ValueError('declarações XML externas não permitidas')
    root = ET.fromstring(content)
    if root.tag != '{DAV:}multistatus':
        raise ValueError('resposta de listagem WebDAV ausente')
    rows=[]; seen=set(); self_seen=False
    for response in root.findall('{DAV:}response'):
        raw = response.findtext('{DAV:}href')
        if not raw:
            raise ValueError('identidade ausente na listagem')
        path = canonical_path(raw)
        if path in seen:
            raise ValueError('entrada repetida na listagem')
        seen.add(path)
        props = [ps.find('{DAV:}prop') for ps in response.findall('{DAV:}propstat')
                 if re.fullmatch(r'HTTP/\d(?:\.\d)? 200 OK',ps.findtext('{DAV:}status',''))]
        if len(props)!=1 or props[0] is None:
            raise ValueError('propriedades incompletas na listagem')
        prop=props[0]; collection=prop.find('.//{DAV:}collection') is not None
        if path.rstrip('/') == parent.rstrip('/'):
            if not collection:
                raise ValueError('origem não é diretório')
            self_seen=True
            continue
        if not path.startswith(parent) or '/' in path[len(parent):].rstrip('/'):
            raise ValueError('entrada fora do diretório solicitado')
        if collection != path.endswith('/'):
            raise ValueError('tipo de entrada contradiz caminho')
        size=prop.findtext('{DAV:}getcontentlength')
        if not collection and (size is None or not size.isdigit()):
            raise ValueError('tamanho do documento ausente')
        rows.append({'name':path[len(parent):].rstrip('/'),'path':path,
                     'url':'https://drive.rn.gov.br'+quote(path,safe='/'),
                     'is_directory':collection,'bytes':None if collection else int(size),
                     'etag':prop.findtext('{DAV:}getetag'),'modified':prop.findtext('{DAV:}getlastmodified'),
                     'content_type':prop.findtext('{DAV:}getcontenttype')})
    if not self_seen or len(rows)>10000:
        raise ValueError('cobertura do diretório não verificável')
    return rows
