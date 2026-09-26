"""FUMARC public API adapter with replayable per-contest document evidence."""
import json
import re
from datetime import datetime, timezone
from types import SimpleNamespace
from urllib.parse import parse_qs, urlsplit

from app.tenderproof import fumarc_api
from app.tenderproof.fumarc_detail import acquire_detail, MAX_BYTES
from app.tenderproof.fumarc_publications import downloadable_pdf
from app.tenderproof.contracts import DiscoveredCandidate, DocumentCandidate
from app.tenderproof.pilot_adapters import document_kind, folded
from app.tenderproof.source_adapter_base import HTMLSourceAdapter
from app.tenderproof.security import validate_destination


class FumarcAdapter(HTMLSourceAdapter):
    source = 'fumarc_open'
    listing_urls = (fumarc_api.HOME,)
    allowed_hosts = (fumarc_api.HOST,)
    ready_selectors = ()
    observed_url_paths = ('/_api/web/lists/',)
    document_identity_pattern = r'(?:\?|&)concurso=(\d+)'

    def validate_listing_url(self, url):
        if url != fumarc_api.HOME:
            fumarc_api.validate_listing_url(url)

    def request_headers(self, url):
        return {'Accept': 'application/json;odata=verbose'}

    def acquire_listing(self, url, fetch):
        self.validate_listing_url(url)
        target = fumarc_api.listing_url() if url == fumarc_api.HOME else url
        def validate(actual):
            fumarc_api.validate_listing_url(actual)
            if actual != target:
                raise ValueError('redirect altera listagem FUMARC')
        result = fetch(target, validate, MAX_BYTES)
        if result.url_final != target or len(result.content) > MAX_BYTES:
            raise ValueError('resposta de listagem fora do contrato')
        body = result.content.decode('utf-8-sig')
        fumarc_api.parse_listing(body, target)
        return json.dumps({'fumarc_listing': {'url': target, 'body': json.loads(body)}})

    def parse_listing(self, html, url, limit=200):
        self.validate_listing_url(url)
        if len(html.encode('utf-8')) > MAX_BYTES:
            raise ValueError('listagem excede limite')
        data = json.loads(html)
        if 'fumarc_listing' in data:
            resource = data['fumarc_listing']
            if url != fumarc_api.HOME and resource['url'] != url:
                raise ValueError('listagem preservada difere do destino')
            return fumarc_api.parse_listing(json.dumps(resource['body']), resource['url'], limit)
        return fumarc_api.parse_listing(html, url, limit)

    def validate_detail_url(self, url):
        validate_destination(url, allowlist=self.allowed_hosts)
        parts = urlsplit(url)
        query = parse_qs(parts.query, keep_blank_values=True)
        if (parts.scheme != 'https' or parts.hostname != fumarc_api.HOST or parts.port not in (None, 443)
                or parts.path != '/SitePages/Home.aspx' or parts.fragment or set(query) != {'concurso'}
                or len(query['concurso']) != 1 or not re.fullmatch(r'[1-9]\d*', query['concurso'][0])):
            raise ValueError('detalhe FUMARC sem identidade única')

    def candidate_from_url(self, url, title=None):
        self.validate_detail_url(url)
        identity = parse_qs(urlsplit(url).query)['concurso'][0]
        return DiscoveredCandidate(candidate_id=f'{self.source}-{identity}', source=self.source,
            external_id=identity, detail_url_observed=url, title_observed=title, observed_at=datetime.now(timezone.utc))

    def acquire_detail(self, url, candidate, fetch):
        self._candidate(candidate, url)
        return acquire_detail(candidate.external_id, fetch)

    def _candidate(self, candidate, url):
        expected = self.candidate_from_url(url)
        if (candidate.source != self.source or candidate.external_id != expected.external_id
                or candidate.detail_url_observed != url):
            raise ValueError('candidato FUMARC incompatível')

    def _replay(self, html, candidate):
        self._candidate(candidate, candidate.detail_url_observed)
        if len(html.encode('utf-8')) > MAX_BYTES:
            raise ValueError('detalhe excede limite')
        data = json.loads(html)
        if data.get('source') != self.source or data.get('contest_id') != int(candidate.external_id):
            raise ValueError('evidência de outro concurso')
        resources = data.get('resources')
        if not isinstance(resources, list) or not resources:
            raise ValueError('recursos de detalhe ausentes')
        query = parse_qs(urlsplit(resources[0]['url']).query)
        stamp = re.search(r"datetime'([^']+)'", query.get('$filter', [''])[0])
        if not stamp:
            raise ValueError('janela de detalhe ausente')
        now = datetime.strptime(stamp[1], '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc)
        position = 0
        def fetch(url, validator, max_bytes):
            nonlocal position
            validator(url)
            if position >= len(resources) or resources[position]['url'] != url:
                raise ValueError('evidência documental incompleta ou fora de sequência')
            content = json.dumps(resources[position]['body'], ensure_ascii=False).encode('utf-8')
            position += 1
            return SimpleNamespace(content=content, url_final=url)
        replay = json.loads(acquire_detail(candidate.external_id, fetch, now))
        if position != len(resources):
            raise ValueError('recursos documentais não associados')
        return replay

    def confirm_identity(self, candidate, html, url):
        self._candidate(candidate, url)
        self._replay(html, candidate)

    def documents(self, html, candidate):
        data = self._replay(html, candidate)
        result = []
        for resource in data['resources'][1:]:
            for row in resource['body']['d']['results']:
                url = downloadable_pdf(row)
                if not url:
                    continue
                description = row['Arquivo'].get('Description') or ''
                title = ' — '.join(dict.fromkeys(x.strip() for x in (row['Title'], description) if x.strip()))
                kind = document_kind(title, url)
                if 'edital' in folded(title) and 'consolidado' in folded(title):
                    kind = 'consolidado'
                result.append(DocumentCandidate(doc_id=f"fumarc-{candidate.external_id}-{row['Id']}",
                    title=title, url_requested=url, kind=kind,
                    reason_chosen=f"Publicação {row['Id']} associada pela API ao ConcursoId {candidate.external_id}; download permitido."))
        return result

    def validate_document_url(self, url, candidate):
        self._candidate(candidate, candidate.detail_url_observed)
        # Acquisition association is checked by documents(); publication also
        # revalidates the actual PDF identity against organization and notice.
        downloadable_pdf({'TipoPublicacao': 'Arquivo', 'PermitirDownload': True, 'Arquivo': {'Url': url}})

    def supplementary_documents(self, docs, chosen):
        matches = [d for d in docs if d.kind == 'anexo'
                   and re.search(r'\bquadro\s+de\s+cargos\b', folded(d.title))]
        if len(matches) > 1:
            raise ValueError('quadros de cargos concorrentes exigem seleção documental')
        return matches
