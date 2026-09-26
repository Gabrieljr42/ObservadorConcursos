"""FACEPE personnel discovery via SAD; observed Drive files require review."""
import hashlib
import json
import re
from datetime import datetime, timezone
from urllib.parse import urlsplit, parse_qs

from app.tenderproof.contracts import DiscoveredCandidate, DocumentCandidate
from app.tenderproof.facepe_listing import (
    SAD_ROOT, validate_listing_url, folder_identity, parse_sad_listing, parse_drive_rows,
)
from app.tenderproof.pilot_adapters import folded, document_kind
from app.tenderproof.source_adapter_base import HTMLSourceAdapter, ListingPage


class FacepeAdapter(HTMLSourceAdapter):
    source = 'facepe_selection'
    listing_urls = (SAD_ROOT,)
    allowed_hosts = ('www.sad.pe.gov.br', 'drive.google.com', 'drive.usercontent.google.com')
    ready_selectors = ('[itemprop="articleBody"]',)
    observed_url_paths = ()
    document_identity_pattern = r'(?!)'
    implementation_state = 'partial'
    implementation_scope = 'Seleções de pessoal vinculadas pela SAD; carregamento integral do Drive, OCR e revisão documental pendentes.'

    def validate_listing_url(self, url):
        validate_listing_url(url)

    def _identity(self, url):
        base, sep, fragment = url.partition('#')
        validate_listing_url(base)
        match = re.fullmatch(r'folder-([A-Za-z0-9_-]{10,100})', fragment)
        if not sep or not match:
            raise ValueError('Detalhe FACEPE sem vínculo SAD/pasta')
        return base, match[1]

    def validate_detail_url(self, url):
        self._identity(url)

    def candidate_from_url(self, url, title=None):
        _, identity = self._identity(url)
        return DiscoveredCandidate(candidate_id='facepe-' + identity, source=self.source,
            external_id=identity, detail_url_observed=url, title_observed=title,
            observed_at=datetime.now(timezone.utc))

    def parse_listing(self, html, url, limit=200):
        if type(limit) is not int or not 1 <= limit <= 10000:
            raise ValueError('Limite de candidatos inválido')
        parsed = parse_sad_listing(html, url)
        return ListingPage(
            candidates=[self.candidate_from_url(url + '#folder-' + x['folder_id'],
                x['agency_observed'] + ' — ' + x['title_observed']) for x in parsed['items'][:limit]],
            next_urls=parsed['next_urls'], truncated=len(parsed['items']) > limit,
            diagnostics=[parsed['diagnostic'], 'Ausência de FACEPE nesta página não certifica fonte vazia.'])

    def _candidate_identity(self, candidate, url):
        base, identity = self._identity(url)
        if (candidate.source != self.source or candidate.external_id != identity
                or candidate.detail_url_observed != url):
            raise ValueError('Identidade do candidato FACEPE divergente')
        return base, identity

    def _folder(self, sad_html, base, identity):
        matches = [x for x in parse_sad_listing(sad_html, base)['items'] if x['folder_id'] == identity]
        if len(matches) != 1:
            raise ValueError('Pasta não vinculada à FACEPE na página oficial SAD')
        return matches[0]

    def acquire_detail(self, url, candidate, fetch):
        base, identity = self._candidate_identity(candidate, url)
        def exact(expected):
            def validate(target):
                if target != expected:
                    raise ValueError('Redirecionamento altera o vínculo documental FACEPE')
            return validate
        sad = fetch(base, exact(base), 1024*1024).content.decode('utf-8-sig')
        folder = self._folder(sad, base, identity)
        folder_identity(folder['url'])
        drive = fetch(folder['url'], exact(folder['url']), 1024*1024).content.decode('utf-8-sig')
        return json.dumps({'format': 'facepe-sad-drive/1', 'sad_html': sad,
                           'folder_url': folder['url'], 'drive_html': drive}, ensure_ascii=False)

    def _parsed(self, html, candidate):
        base, identity = self._candidate_identity(candidate, candidate.detail_url_observed)
        if len(html.encode('utf-8')) > 2*1024*1024:
            raise ValueError('Detalhe composto FACEPE excede limite')
        data = json.loads(html)
        if not isinstance(data, dict) or data.get('format') != 'facepe-sad-drive/1':
            raise ValueError('Formato do detalhe FACEPE inválido')
        folder = self._folder(data['sad_html'], base, identity)
        if data['folder_url'] != folder['url']:
            raise ValueError('Pasta adquirida diverge do vínculo SAD')
        return parse_drive_rows(data['drive_html'], folder['url'])

    def confirm_identity(self, candidate, html, url):
        self._candidate_identity(candidate, url)
        self._parsed(html, candidate)

    def documents(self, html, candidate):
        parsed = self._parsed(html, candidate)
        docs = []
        for row in parsed['items']:
            if row['type_observed'] != 'PDF':
                continue
            name = folded(row['name'])
            plain = re.sub(r'^\d+(?:\.\d+)*[.\s_-]*', '', name)
            if plain in ('edital.pdf', 'edital de abertura.pdf'):
                kind = 'edital'
            elif re.search(r'\berrata\b|\bretificacao\b', name):
                kind = 'retificacao'
            else:
                kind = document_kind(row['name'], row['view_url'])
                if kind in ('edital', 'consolidado'):
                    kind = 'outro'
            # Public Drive download template verified against viewer URLs and
            # redirects. The ID originates in this folder's observed row.
            target = 'https://drive.usercontent.google.com/uc?id=' + row['file_id'] + '&export=download'
            docs.append(DocumentCandidate(doc_id='facepe-' + hashlib.sha256(
                (candidate.external_id + ':' + row['file_id']).encode()).hexdigest()[:24],
                title=row['name'], kind=kind, url_requested=target,
                reason_chosen='Arquivo observado na pasta ' + parsed['folder_id']
                    + ' vinculada pela SAD; download derivado do contrato público Drive. Rótulo exige conferência do conteúdo.'))
        return docs

    def validate_document_url(self, url, candidate):
        self._candidate_identity(candidate, candidate.detail_url_observed)
        p = urlsplit(url)
        q = parse_qs(p.query, keep_blank_values=True)
        if (p.scheme != 'https' or p.netloc != 'drive.usercontent.google.com' or p.fragment
                or p.path not in ('/uc', '/download') or set(q) != {'id', 'export'}
                or q['export'] != ['download'] or len(q['id']) != 1
                or not re.fullmatch(r'[A-Za-z0-9_-]{10,100}', q['id'][0])):
            raise ValueError('Destino documental FACEPE fora do contrato Drive')

    def choose_document(self, docs):
        originals = [x for x in docs if x.kind == 'edital']
        if len(originals) != 1:
            raise ValueError('Edital original FACEPE ausente ou ambíguo')
        return originals[0]

    def validate_document_redirect(self, target, requested, candidate):
        self.validate_document_url(requested, candidate)
        self.validate_document_url(target, candidate)
        if parse_qs(urlsplit(target).query)['id'] != parse_qs(urlsplit(requested).query)['id']:
            raise ValueError('Redirecionamento altera arquivo Drive solicitado')
