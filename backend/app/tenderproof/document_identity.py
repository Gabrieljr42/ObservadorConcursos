"""Stable comparison identities only: never rewrite acquired/persisted URLs.

AWS query handling preserves the existing continuous-store convention.
Cesgranrio SAS rotation: tenderproof-batch60-major-sas-identity.json.
CPCON refresh rotation: tenderproof-batch60-cpcon-refresh-proof.json.
Unknown hosts, routes, query names and permission shapes retain all parameters.
"""
import json
import hashlib
import re
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


def document_identity_url(url):
    """Strip only recognized ephemeral values for signatures/comparisons."""
    if not isinstance(url,str):
        return url
    try:
        parts=urlsplit(url)
        pairs=parse_qsl(parts.query,keep_blank_values=True)
    except ValueError:
        return url
    if not pairs:
        return url
    # Retain legacy AWS behavior, including existing aliases (Expires etc.).
    retained=[(k,v) for k,v in pairs if not k.lower().startswith('x-amz-')
        and k.lower() not in ('signature','awsaccesskeyid','expires')]
    if len(retained)!=len(pairs):
        return urlunsplit((parts.scheme,parts.netloc,parts.path,urlencode(sorted(retained)),parts.fragment))
    if parts.scheme!='https' or parts.fragment:
        return url
    query=dict(pairs)
    if len(query)!=len(pairs) or any(not v for v in query.values()):
        return url
    uuid=r'[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}'
    if (parts.netloc=='concursos.cesgranrio.org.br'
            and re.fullmatch(r'/media/gpoweb-prd-hibrido3/eventos/\d+/conteudos/'+uuid+r'\.pdf',parts.path,re.I)
            and set(query)=={'sv','se','sr','sp','sig'} and query['sr']=='c' and query['sp']=='r'):
        return urlunsplit((parts.scheme,parts.netloc,parts.path,'',''))
    if (parts.netloc=='cpcon.uepb.edu.br' and re.fullmatch(r'/download/[a-z0-9-]+/',parts.path)
            and set(query)=={'wpdmdl','refresh'} and re.fullmatch(r'\d{1,9}',query['wpdmdl'])
            and re.fullmatch(r'[A-Za-z0-9]{10,80}',query['refresh'])):
        return urlunsplit((parts.scheme,parts.netloc,parts.path,urlencode({'wpdmdl':query['wpdmdl']}),''))
    return url


def document_identity(doc):
    parts=urlsplit(document_identity_url(doc['url']))
    query=tuple(sorted(parse_qsl(parts.query,keep_blank_values=True)))
    request=doc.get('acquisition_request')
    if request is not None:
        from app.tenderproof.contracts import DocumentAcquisitionRequest
        request=DocumentAcquisitionRequest.model_validate(request).model_dump(mode='json')
        query=(query,('acquisition_request',json.dumps(request,sort_keys=True,separators=(',',':'))))
    if doc.get('file_format','pdf')!='pdf':
        query=(query,('file_format',doc['file_format']))
    return (parts.scheme,parts.netloc,parts.path,query,doc.get('title'),doc.get('kind'))


def document_manifest(document):
    # Keep historical GET manifests byte-compatible; POST identity is additive.
    item={'title':document.title,'url':document.url_requested,'kind':document.kind}
    if document.file_format != 'pdf':item['file_format']=document.file_format
    if document.acquisition_request is not None:
        item['acquisition_request']=document.acquisition_request.model_dump(mode='json')
    return item


_URL=re.compile(r'https?://[^\s<>"\']+')


def signature_value(value):
    """Copy nested signature data, including URLs embedded in validation text."""
    if isinstance(value,dict):
        return {key:signature_value(item) for key,item in value.items()}
    if isinstance(value,list):
        return [signature_value(item) for item in value]
    if isinstance(value,tuple):
        return tuple(signature_value(item) for item in value)
    if isinstance(value,str):
        def replace(match):
            original=match.group()
            url=original.rstrip('.,;)]}')
            return document_identity_url(url)+original[len(url):]
        return _URL.sub(replace,value)
    return value


def signature_manifest(manifest):
    """Stable ordering and duplicate elimination after ephemeral URL rotation."""
    normalized=[signature_value(doc) for doc in manifest]
    unique={json.dumps(doc,sort_keys=True,ensure_ascii=False):doc for doc in normalized}
    return sorted(unique.values(),key=lambda doc:(doc['url'],doc['title'],json.dumps(doc,sort_keys=True,ensure_ascii=False)))


def observation_signature(summary,validation,extractors,*,normalize=True):
    if normalize:
        summary=signature_value(summary)
        summary['documents']=signature_manifest(summary['documents'])
        validation=signature_value(validation)
    data={'summary':summary,'validation':validation,'extractors':sorted(extractors)}
    return hashlib.sha256(json.dumps(data,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
