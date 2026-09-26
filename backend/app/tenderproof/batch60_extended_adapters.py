"""Observed CPCON WordPress downloads and Gualimp public AJAX detail."""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from html import escape, unescape
from urllib.parse import parse_qs, urlencode, urlsplit

from bs4 import BeautifulSoup

from app.tenderproof.contracts import DiscoveredCandidate, DocumentCandidate
from app.tenderproof.pilot_adapters import PilotHTMLAdapter, document_kind, folded, visible_soup
from app.tenderproof.validation import title_is_corroborated


class CPCONAdapter(PilotHTMLAdapter):
    detail_pattern = r'/([a-z0-9][a-z0-9-]+)/'
    # Restrict PDF URL identity extraction to this official host. A bare /slug/
    # regex incorrectly interpreted ordinary dates and /progep/ as contest IDs.
    document_identity_pattern = r'cpcon\.uepb\.edu\.br/(?!(?:sigeps-app|wp-content|wp-admin|download)/)([a-z0-9][a-z0-9-]+)/'
    candidate_selector = 'a.vc_gitem-link[href][title]'
    ready_selectors = (candidate_selector,)
    listing_query_keys = ()
    document_hosts = ('cpcon.uepb.edu.br',)

    def __init__(self):
        super().__init__('cpcon_open', 'https://cpcon.uepb.edu.br', listing_paths=('', '/'))

    def _title(self, anchor):
        return anchor.get('title')

    def in_scope(self, title, url):
        return super().in_scope(title, url) and 'residencia' not in folded(title) and bool(re.search(r'concurso publico|processo seletivo|\bpss\b', folded(title)))

    def confirm_identity(self, candidate, html, url):
        soup = self._check_detail(candidate, html, url)
        canonical = soup.select_one('link[rel=canonical]')
        if canonical and canonical.get('href') != url:
            raise ValueError('identidade canônica CPCON incompatível')
        title = ' '.join(n.get_text(' ', strip=True) for n in soup.select('h2.title'))
        if not candidate.title_observed or not title_is_corroborated(candidate.title_observed, title):
            raise ValueError('título CPCON incompatível')
        if not self.documents(html, candidate):
            raise ValueError('detalhe CPCON sem publicações oficiais')

    def validate_document_url(self, url, candidate):
        self._check_candidate(candidate)
        p = self._destination(url)
        q = parse_qs(p.query, keep_blank_values=True)
        if p.hostname != self.portal_host or not re.fullmatch(r'/download/[a-z0-9-]+/', p.path) or set(q) != {'wpdmdl', 'refresh'} or any(len(v) != 1 for v in q.values()) or not re.fullmatch(r'\d{1,9}', q['wpdmdl'][0]) or not re.fullmatch(r'[A-Za-z0-9]{10,80}', q['refresh'][0]):
            raise ValueError('download CPCON fora do contrato observado')

    def documents(self, html, candidate):
        self._check_candidate(candidate)
        soup = visible_soup(html)
        docs, seen = [], set()
        for anchor in soup.select('tr.__dt_row a[data-downloadurl]'):
            url = anchor['data-downloadurl']
            self.validate_document_url(url, candidate)
            p = urlsplit(url)
            stable = p._replace(query=urlencode({'wpdmdl': parse_qs(p.query)['wpdmdl'][0]})).geturl()
            if stable in seen:
                continue
            seen.add(stable)
            heading = anchor.find_parent('tr').select_one('td.__dt_col_title strong')
            title = heading.get_text(' ', strip=True) if heading else ''
            docs.append(DocumentCandidate(doc_id='cpcon-doc-' + hashlib.sha256(stable.encode()).hexdigest()[:16], title=title, url_requested=url, kind=document_kind(title, url)))
        return docs


class GualimpAdapter(PilotHTMLAdapter):
    candidate_selector = 'a[href*="/processos_de_selecao/ps.html?detail="]'
    ready_selectors = (candidate_selector,)
    document_hosts = ('gualimpconsultoria.com.br',)
    detail_host = 'gualimpconsultoria.com.br'
    document_identity_pattern = r'ps\.html\?detail=(\d+)'
    listing_query_keys = ()

    def __init__(self):
        super().__init__('gualimp_open', 'https://www.gualimp.com.br/concursos/', document_hosts=self.document_hosts)

    def request_headers(self, url):
        from app.tenderproof.batch60_recovered_adapters import BROWSER_UA
        return {'User-Agent': BROWSER_UA} if urlsplit(url).hostname in self.allowed_hosts else {}

    def validate_detail_url(self, url):
        p = self._destination(url)
        q = parse_qs(p.query, keep_blank_values=True)
        if p.hostname != self.detail_host or p.path != '/processos_de_selecao/ps.html' or set(q) != {'detail'} or len(q['detail']) != 1 or not re.fullmatch(r'\d{1,8}', q['detail'][0]):
            raise ValueError('detalhe Gualimp fora do contrato')

    def candidate_from_url(self, url, title=None):
        self.validate_detail_url(url)
        external = parse_qs(urlsplit(url).query)['detail'][0]
        return DiscoveredCandidate(candidate_id=self.source+'-'+external, source=self.source, external_id=external, title_observed=title, detail_url_observed=url, observed_at=datetime.now(timezone.utc))

    def _title(self, anchor):
        heading = anchor.find_previous('h4')
        if heading is None:
            return None
        values = []
        for node in heading.contents:
            if getattr(node, 'name', None) == 'br':
                break
            values.append(node.get_text(' ', strip=True) if hasattr(node, 'get_text') else str(node))
        return ' '.join(values).strip()

    def detail_resource_urls(self, html, url):
        self.validate_detail_url(url)
        # Require the literal observed public script contract, not just an empty
        # placeholder that could belong to any page or application.
        required = ('funcao_:\'load_ps\', id_concurso', 'funcao_:\'load_publicacoes\', id_concurso', 'urlParams.get(\'detail\')', '"/include/php/ajax.php"')
        if not all(marker in html for marker in required):
            raise ValueError('script público Gualimp mudou ou está ausente')
        identity = self.candidate_from_url(url).external_id
        return ['https://' + self.detail_host + '/include/php/ajax.php?' + urlencode({'funcao_': function, 'id_concurso': identity}) for function in ('load_ps', 'load_publicacoes')]

    def validate_detail_resource_url(self, url, candidate):
        self._check_candidate(candidate)
        p = self._destination(url)
        q = parse_qs(p.query, keep_blank_values=True)
        if p.hostname != self.detail_host or p.path != '/include/php/ajax.php' or set(q) != {'funcao_', 'id_concurso'} or any(len(v) != 1 for v in q.values()) or q['funcao_'][0] not in ('load_ps', 'load_publicacoes') or q['id_concurso'] != [candidate.external_id]:
            raise ValueError('recurso Gualimp de outro concurso ou função')

    def compose_detail(self, html, url, resources):
        expected = self.detail_resource_urls(html, url)
        if len(resources) != 2 or [r.get('url') for r in resources] != expected:
            raise ValueError('recursos Gualimp ausentes, duplicados ou de outra identidade')
        candidate = self.candidate_from_url(url)
        for resource in resources:
            self.validate_detail_resource_url(resource['url'], candidate)
        identity = json.loads(resources[0]['body'])
        publications = json.loads(resources[1]['body'])
        if not isinstance(identity, list) or len(identity) != 1 or not isinstance(identity[0], dict):
            raise ValueError('resposta de identidade Gualimp inválida')
        fields = ('ds_concurso', 'nr_concurso', 'ds_cliente', 'ds_cidade', 'ds_estado')
        if any(not isinstance(identity[0].get(k), str) or not identity[0][k].strip() for k in fields):
            raise ValueError('identidade Gualimp incompleta')
        if not isinstance(publications, list) or not publications or any(not isinstance(value, str) for value in publications):
            raise ValueError('publicações Gualimp incompletas')
        title = ' '.join(identity[0][k].strip() for k in fields)
        # Preserve exact transport evidence inside inert text, and separately
        # render the observed JSON publication HTML for existing page parsers.
        evidence = escape(json.dumps(resources, ensure_ascii=False))
        return '<section data-gualimp-detail="' + candidate.external_id + '"><h1>' + escape(title) + '</h1><div class="gualimp-publications">' + ''.join(publications) + '</div></section><script type="application/json" id="gualimp-transport-evidence">' + evidence + '</script>'

    def confirm_identity(self, candidate, html, url):
        soup = self._check_detail(candidate, html, url)
        section = soup.select_one('section[data-gualimp-detail]')
        if section is None or section['data-gualimp-detail'] != candidate.external_id:
            raise ValueError('detalhe Gualimp sem recursos associados à identidade')
        heading = section.select_one('h1')
        title = heading.get_text(' ', strip=True) if heading else ''
        if not candidate.title_observed or not title_is_corroborated(candidate.title_observed, title):
            raise ValueError('título Gualimp incompatível')
        # Compare the observed NNN/YYYY identifier with the structured response,
        # not with document titles elsewhere in the page. Read the preserved
        # evidence so already captured composed details retain compatibility.
        number_pattern = r'(?<![\d/])(\d{3}/\d{4})(?!\d)'
        observed_numbers = set(re.findall(number_pattern, candidate.title_observed))
        if observed_numbers:
            try:
                evidence = BeautifulSoup(html, 'html.parser').select_one('#gualimp-transport-evidence')
                resources = json.loads(unescape(evidence.get_text())) if evidence else []
                resource = resources[0]
                self.validate_detail_resource_url(resource['url'], candidate)
                if parse_qs(urlsplit(resource['url']).query)['funcao_'] != ['load_ps']:
                    raise ValueError('recurso não contém identidade')
                identity = json.loads(resource['body'])
                if not isinstance(identity, list) or len(identity) != 1:
                    raise ValueError('identidade não é única')
                number = identity[0]['nr_concurso']
                if not isinstance(number, str) or set(re.findall(number_pattern, number)) != observed_numbers:
                    raise ValueError('identificador divergente')
            except (ValueError, TypeError, KeyError, IndexError, AttributeError) as exc:
                raise ValueError('número/ano Gualimp incompatível com a listagem') from exc
        if not self.documents(html, candidate):
            raise ValueError('Gualimp sem documento oficial')

    def document_route(self, p):
        return p.path.startswith('/attachment/docs/')

    def validate_document_url(self, url, candidate):
        self._check_candidate(candidate)
        p = self._destination(url)
        if p.hostname != self.detail_host or p.query or not re.fullmatch(r'/attachment/docs/[0-9_]+\.pdf', p.path):
            raise ValueError('documento fora do diretório público Gualimp')


BATCH60_EXTENDED_ADAPTERS = {adapter.source: adapter for adapter in (CPCONAdapter(), GualimpAdapter())}
