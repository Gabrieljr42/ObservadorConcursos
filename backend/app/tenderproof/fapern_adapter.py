"""Public FAPERN catalogue through the state service and its RN Drive share."""
import hashlib
import json
import re
from datetime import datetime, timezone
from urllib.parse import parse_qs, urlencode, urlsplit
from app.tenderproof.contracts import DiscoveredCandidate, DocumentCandidate
from app.tenderproof.fapern_drive import ROOT, canonical_path
from app.tenderproof.fapern_listing import PORTAL, SHARE, share_token, discover_share, acquire_directory
from app.tenderproof.source_adapter_base import HTMLSourceAdapter, ListingPage
from app.tenderproof.pilot_adapters import document_kind, folded


def folder_url(share,path):
    return share+'?'+urlencode({'path':'/'+canonical_path(path)[len(ROOT):].rstrip('/')})


def folder(url):
    base,sep,query=url.partition('?');share_token(base)
    values=parse_qs(query,keep_blank_values=True)
    if not sep or set(values)!={'path'} or len(values['path'])!=1:
        raise ValueError('pasta pública sem caminho único')
    relative=values['path'][0]
    if not relative.startswith('/') or relative=='/' or relative.endswith('/'):
        raise ValueError('caminho de pasta inválido')
    path=canonical_path(ROOT+relative[1:]+'/')
    if folder_url(base,path)!=url: raise ValueError('URL de pasta não canônica')
    return base,path


class FapernAdapter(HTMLSourceAdapter):
    source='fapern_selection'
    listing_urls=(PORTAL+'1',)
    allowed_hosts=('www.cidadao.rn.gov.br','drive.rn.gov.br')
    ready_selectors=('#filestable',)
    observed_url_paths=()
    document_identity_pattern=r'(?!)'
    implementation_state='partial'
    implementation_scope='Descoberta dinâmica Portal do Cidadão e RN Drive; bolsas, financiamento e seleções exigem classificação documental. OCR e publicação pendentes.'

    def validate_listing_url(self,url):
        if url!=self.listing_urls[0]: folder(url)

    def validate_detail_url(self,url):
        _,path=folder(url)
        if len(path[len(ROOT):].strip('/').split('/'))<2:
            raise ValueError('detalhe deve identificar uma seleção dentro do acervo')

    def candidate_from_url(self,url,title=None):
        self.validate_detail_url(url);share,path=folder(url)
        identity=share_token(share)+':'+path[len(ROOT):].rstrip('/')
        return DiscoveredCandidate(candidate_id='fapern-'+hashlib.sha256(identity.encode()).hexdigest()[:24],
            source=self.source,external_id=identity,detail_url_observed=url,
            title_observed=title or path.rstrip('/').rsplit('/',1)[-1],observed_at=datetime.now(timezone.utc))

    def _bound(self,url,fetch):
        proof=discover_share(fetch)
        if url==self.listing_urls[0]: return proof,ROOT
        share,path=folder(url)
        if share!=proof['share_url']: raise ValueError('pasta não corresponde ao vínculo oficial FAPERN atual')
        return proof,path

    def acquire_listing(self,url,fetch):
        self.validate_listing_url(url);proof,path=self._bound(url,fetch)
        rows=acquire_directory(fetch,proof['share_url'],path)
        return json.dumps({'format':'fapern-directory/1','url':url,'proof':proof,'path':path,'rows':rows},ensure_ascii=False)

    def _parsed(self,html,url):
        data=json.loads(html)
        if data.get('format')!='fapern-directory/1' or data.get('url')!=url:
            raise ValueError('resposta FAPERN não corresponde à URL')
        share_token(data['proof']['share_url'])
        expected=ROOT if url==self.listing_urls[0] else folder(url)[1]
        if data['path']!=expected or url!=self.listing_urls[0] and folder(url)[0]!=data['proof']['share_url']:
            raise ValueError('identidade da pasta diverge do vínculo oficial')
        return data

    def parse_listing(self,html,url,limit=200):
        if type(limit) is not int or not 1<=limit<=10000: raise ValueError('limite inválido')
        data=self._parsed(html,url);path=data['path'];rows=data['rows']
        is_selection=len(path[len(ROOT):].strip('/').split('/'))>=2 and any(not r['is_directory'] for r in rows)
        if is_selection:
            candidates=[self.candidate_from_url(url)]
            next_urls=[] # All descendants belong to this detail's manifest.
        else:
            candidates=[]
            next_urls=[folder_url(data['proof']['share_url'],r['path']) for r in rows if r['is_directory']]
        return ListingPage(candidates=candidates,next_urls=next_urls,truncated=False,
            diagnostics=['Diretório público enumerado por Depth 1; documentos não classificam automaticamente a seleção como pessoal.'])

    def _candidate(self,candidate,url):
        expected=self.candidate_from_url(url)
        if candidate.source!=self.source or candidate.external_id!=expected.external_id or candidate.detail_url_observed!=url:
            raise ValueError('identidade do candidato FAPERN divergente')

    def acquire_detail(self,url,candidate,fetch):
        self._candidate(candidate,url);proof,path=self._bound(url,fetch)
        queue=[path];seen=set();files=[]
        while queue:
            current=queue.pop(0)
            if current in seen: raise ValueError('diretório repetido no manifesto')
            seen.add(current)
            if len(seen)>100 or len(files)>1000: raise ValueError('manifesto excede limites de aquisição')
            for row in acquire_directory(fetch,proof['share_url'],current):
                if row['is_directory']: queue.append(row['path'])
                else: files.append(row)
        if len(files)>1000: raise ValueError('manifesto excede limite de documentos')
        return json.dumps({'format':'fapern-directory/1','url':url,'proof':proof,'path':path,'rows':files},ensure_ascii=False)

    def confirm_identity(self,candidate,html,url):
        self._candidate(candidate,url);self._parsed(html,url)

    def documents(self,html,candidate):
        data=self._parsed(html,candidate.detail_url_observed);self._candidate(candidate,candidate.detail_url_observed)
        docs=[]
        for row in data['rows']:
            path=canonical_path(row['path'])
            if row['is_directory'] or not path.startswith(data['path']): raise ValueError('arquivo fora da seleção')
            name=row['name']
            relative=path[len(ROOT):];directory,filename=relative.rsplit('/',1)
            url=data['proof']['share_url']+'/download?'+urlencode({'path':'/'+directory,'files':filename})
            label=folded(name)
            kind=document_kind(name,url)
            if re.search(r'retific|errata|prorrog',label):
                kind='prorrogacao' if 'prorrog' in label else 'retificacao'
            elif re.search(r'edital\s+(?:de\s+)?abertura',label): kind='edital'
            elif re.fullmatch(r'(?:doe\s*-\s*)?edital\s+(?:n[º°o.]?\s*)?\d{1,4}[\s/-]+\d{4}\s*\.pdf',label):
                kind='edital'
            elif kind in ('edital','consolidado'): kind='outro'
            docs.append(DocumentCandidate(doc_id='fapern-doc-'+hashlib.sha256(path.encode()).hexdigest()[:24],
                title=name,kind=kind,url_requested=url,reason_chosen='Arquivo enumerado na pasta oficial FAPERN; rótulo e escopo exigem conferência do PDF.'))
        return docs

    def validate_document_url(self,url,candidate):
        self._candidate(candidate,candidate.detail_url_observed)
        share,root=folder(candidate.detail_url_observed)
        base,sep,query=url.partition('?');q=parse_qs(query,keep_blank_values=True)
        if base!=share+'/download' or not sep or set(q)!={'path','files'} or any(len(v)!=1 for v in q.values()):
            raise ValueError('download fora do compartilhamento FAPERN')
        directory,name=q['path'][0],q['files'][0]
        if not directory.startswith('/') or '/' in name or not name:
            raise ValueError('arquivo público inválido')
        path=canonical_path(ROOT+directory[1:].rstrip('/')+'/'+name)
        if not path.startswith(root): raise ValueError('documento pertence a outra seleção')

    def choose_document(self,docs):
        originals=[d for d in docs if d.kind=='edital']
        if len(originals)!=1: raise ValueError('edital original ausente ou ambíguo na pasta FAPERN')
        return originals[0]
