"""FAPES public menu and individual call panels, with explicit historical gaps."""
import json
import re
from datetime import datetime, timezone
from urllib.parse import urlsplit, unquote, quote

from app.tenderproof.contracts import DiscoveredCandidate, DocumentCandidate
from app.tenderproof.fapes_panels import discover_sections, parse_file_panels
from app.tenderproof.fapes_documents import document_manifest
from app.tenderproof.pilot_adapters import folded
from app.tenderproof.source_adapter_base import HTMLSourceAdapter, ListingPage


def exact(expected):
    def validate(target):
        if target != expected:
            raise ValueError('redirecionamento altera identidade FAPES')
    return validate


class FapesAdapter(HTMLSourceAdapter):
    source = 'fapes_selection'
    listing_urls = ('https://fapes.es.gov.br/editais',)
    allowed_hosts = ('fapes.es.gov.br',)
    ready_selectors = ('ul.galeriade-arquivos',)
    observed_url_paths = ()
    document_identity_pattern = r'(?!)'
    implementation_state = 'partial'
    implementation_scope = 'Menu atual e painéis individuais; históricos anuais, classificação e publicação pendentes.'

    def validate_listing_url(self, url):
        p = urlsplit(url)
        path = unquote(p.path)
        if (p.scheme != 'https' or p.netloc != self.allowed_hosts[0] or p.query or p.fragment
                or not re.fullmatch(r'/[\w/-]+', path) or p.path != quote(path, safe='/')):
            raise ValueError('seção fora do contrato FAPES')

    def acquire_listing(self, url, fetch):
        self.validate_listing_url(url)
        root = self.listing_urls[0]
        response = fetch(root, exact(root), 2 * 1024 * 1024)
        exact(root)(response.url_final)
        menu = response.content.decode('utf-8-sig')
        sections = discover_sections(menu)
        body = menu
        if url != root:
            if url not in sections:
                raise ValueError('seção não observada no menu atual FAPES')
            response = fetch(url, exact(url), 4 * 1024 * 1024)
            exact(url)(response.url_final)
            body = response.content.decode('utf-8-sig')
        return json.dumps({'format': 'fapes-section/1', 'url': url, 'menu': menu, 'html': body}, ensure_ascii=False)

    def _section(self, html, url):
        self.validate_listing_url(url)
        data = json.loads(html)
        if data.get('format') != 'fapes-section/1' or data.get('url') != url:
            raise ValueError('prova de seção divergente FAPES')
        sections = discover_sections(data['menu'])
        if url != self.listing_urls[0] and url not in sections:
            raise ValueError('seção sem vínculo com o menu FAPES')
        return data, sections

    def parse_listing(self, html, url, limit=200):
        if type(limit) is not int or not 1 <= limit <= 10000:
            raise ValueError('limite inválido')
        data, sections = self._section(html, url)
        if url == self.listing_urls[0]:
            return ListingPage(next_urls=sections)
        panels = parse_file_panels(data['html'])
        annual = [p for p in panels if re.fullmatch(r'(?:editais encerrados|resultados? editais) \d{4}', folded(p['title']))]
        current = [p for p in panels if p not in annual]
        return ListingPage(candidates=[self.candidate_from_url(url + '#panel-' + p['panel_id'], p['title']) for p in current[:limit]],
            truncated=bool(annual) or len(current) > limit,
            diagnostics=['Painel anual exige separar identidades: ' + p['title'] for p in annual]
                + ['Compatibilidade e completude documental exigem conferência.'])

    def validate_detail_url(self, url):
        section, marker, fragment = url.partition('#')
        self.validate_listing_url(section)
        if not marker or not re.fullmatch(r'panel-\d+', fragment):
            raise ValueError('identidade do painel FAPES ausente')

    def candidate_from_url(self, url, title=None):
        self.validate_detail_url(url)
        identity = urlsplit(url).fragment.removeprefix('panel-')
        return DiscoveredCandidate(candidate_id='fapes-panel-' + identity, source=self.source,
            external_id=identity, detail_url_observed=url, title_observed=title,
            observed_at=datetime.now(timezone.utc))

    def _candidate(self, candidate, url):
        self.validate_detail_url(url)
        if (candidate.source != self.source or candidate.detail_url_observed != url
                or candidate.external_id != urlsplit(url).fragment.removeprefix('panel-')):
            raise ValueError('candidato FAPES divergente')

    def acquire_detail(self, url, candidate, fetch):
        self._candidate(candidate, url)
        proof = self.acquire_listing(url.split('#')[0], fetch)
        self._manifest(proof, candidate)
        return proof

    def _manifest(self, html, candidate):
        self._candidate(candidate, candidate.detail_url_observed)
        data, _ = self._section(html, candidate.detail_url_observed.split('#')[0])
        panels = [p for p in parse_file_panels(data['html']) if p['panel_id'] == candidate.external_id]
        if len(panels) != 1:
            raise ValueError('painel FAPES não localizado univocamente')
        return document_manifest(panels[0])

    def confirm_identity(self, candidate, html, url):
        self._candidate(candidate, url)
        self._manifest(html, candidate)

    def documents(self, html, candidate):
        grouped = {}
        for row in self._manifest(html, candidate)['documents']:
            grouped.setdefault(row['url'], []).append(row)
        result = []
        for url, rows in grouped.items():
            kinds = {r['kind'] for r in rows}
            if len(kinds) != 1:
                raise ValueError('rótulos conflitantes para o mesmo documento FAPES')
            result.append(DocumentCandidate(doc_id=rows[0]['doc_id'], title=' / '.join(dict.fromkeys(r['title'] for r in rows)),
                kind=rows[0]['kind'], url_requested=url,
                reason_chosen='Documento vinculado ao painel oficial; modalidade e efeitos pendentes de conferência. '
                    + 'Atualizações observadas: ' + ', '.join(dict.fromkeys(r['updated_at'] for r in rows))))
        return result

    def validate_document_url(self, url, candidate):
        self._candidate(candidate, candidate.detail_url_observed)
        p = urlsplit(url)
        path = unquote(p.path)
        if (p.scheme != 'https' or p.netloc != self.allowed_hosts[0] or p.query or p.fragment
                or not path.startswith('/Media/fapes/') or not path.lower().endswith(('.pdf', '.docx', '.doc'))
                or any(s in ('.', '..') for s in path.split('/')) or '\\' in path or '%' in path):
            raise ValueError('destino documental fora do contrato FAPES')

    def choose_document(self, docs):
        originals = [d for d in docs if d.kind == 'edital']
        if len(originals) != 1:
            raise ValueError('edital original ausente ou ambíguo FAPES')
        return originals[0]
