"""Public Uniselva JSON contract observed in official Angular bundle, 2026-09-08.

Only personnel notices are eligible. Registration does not certify 35-page coverage.
"""
from __future__ import annotations

import hashlib
import json
import re
from urllib.parse import parse_qs, quote, unquote, urlencode

from app.tenderproof.contracts import DocumentCandidate
from app.tenderproof.pilot_adapters import PilotHTMLAdapter, document_kind, folded
from app.tenderproof.source_adapter_base import ListingPage, SourcePageBlocked
from app.tenderproof.validation import title_is_corroborated


class UniselvaAdapter(PilotHTMLAdapter):
    source = 'uniselva_selection'
    detail_pattern = r'/SelecaoSimplificada/([1-9]\d{0,8})'
    document_identity_pattern = detail_pattern
    ready_selectors = ()
    document_hosts = ('web.fundacaouniselva.org.br',)
    observed_url_paths = ('/SelecaoSimplificada', '/Editais/')
    implementation_scope = 'API pública; seleções de pessoal; paginação limitada pelo orçamento de coleta'

    def __init__(self):
        super().__init__(self.source, self.listing_url(1), document_hosts=self.document_hosts)

    @staticmethod
    def listing_url(page):
        return 'https://api.fundacaouniselva.org.br/SelecaoSimplificada?' + urlencode({
            'pageNumber': page, 'pageSize': 9, 'isDescending': 'true', 'filter.isInscricaoAberta': 'false'})

    def validate_listing_url(self, url):
        p = self._destination(url)
        q = parse_qs(p.query, keep_blank_values=True)
        if (p.hostname != self.portal_host or p.path != '/SelecaoSimplificada'
                or set(q) != {'pageNumber', 'pageSize', 'isDescending', 'filter.isInscricaoAberta'}
                or any(len(v) != 1 for v in q.values())
                or not re.fullmatch(r'[1-9]\d{0,4}', q['pageNumber'][0])
                or q['pageSize'] != ['9'] or q['isDescending'] != ['true']
                or q['filter.isInscricaoAberta'] != ['false']):
            raise ValueError('URL fora do contrato público Uniselva')

    @staticmethod
    def _json(body):
        if len(body.encode('utf-8')) > 2 * 1024 * 1024:
            raise ValueError('resposta Uniselva excede 2 MiB')
        if any(x in body.casefold() for x in ('just a moment', 'verify you are human', 'access denied')):
            raise SourcePageBlocked('API Uniselva bloqueada; não é listagem vazia')
        try:
            data = json.loads(body)
        except (ValueError, TypeError):
            raise ValueError('resposta Uniselva não contém JSON público válido') from None
        if not isinstance(data, dict):
            raise ValueError('estrutura JSON Uniselva incompatível')
        return data

    @staticmethod
    def in_scope(title, url=''):
        text = folded(title)
        if any(x in text for x in ('bolsa', 'bolsista', 'vestibular', 'residencia', 'mestrado', 'doutorado', 'patrocinio')):
            return False
        return bool(re.search(r'contratacao|processo seletivo|selecao de (?:pessoal|profissionais)|banco de curriculos|vaga|concurso', text))

    def parse_listing(self, html, url, limit=200):
        self.validate_listing_url(url)
        if type(limit) is not int or not 1 <= limit <= 10000:
            raise ValueError('limite inválido')
        data = self._json(html)
        page = int(parse_qs(self._destination(url).query)['pageNumber'][0])
        for key in ('page', 'pageSize', 'total', 'totalPage'):
            if type(data.get(key)) is not int:
                raise ValueError('metadados de paginação Uniselva inválidos')
        total = data['total']
        items = data.get('items')
        if (data['page'] != page or data['pageSize'] != 9 or total < 0
                or data['totalPage'] != (total + 8) // 9
                or not isinstance(items, list) or page > max(1, data['totalPage'])
                or len(items) != min(9, max(0, total - (page - 1) * 9))):
            raise ValueError('paginação Uniselva inconsistente; vazio não confirmado')
        candidates, seen, excluded = [], set(), 0
        for item in items:
            if (not isinstance(item, dict) or type(item.get('id')) is not int or item['id'] <= 0
                    or not isinstance(item.get('titulo'), str) or not item['titulo'].strip()
                    or item['id'] in seen):
                raise ValueError('identidade de seleção inválida ou duplicada na página')
            seen.add(item['id'])
            if not self.in_scope(item['titulo']):
                excluded += 1
                continue
            candidates.append(self.candidate_from_url(
                f'https://api.fundacaouniselva.org.br/SelecaoSimplificada/{item["id"]}', item['titulo']))
        result = ListingPage(candidates=candidates[:limit], truncated=len(candidates) > limit)
        result.diagnostics.append(f'{excluded} itens fora do escopo de pessoal nesta página')
        if page < data['totalPage']:
            result.next_urls = [self.listing_url(page + 1)]
        elif not result.truncated:
            result.terminal_evidence = f'API: página {page}, total {total}, totalPage {data["totalPage"]}'
        if not candidates and (items or total == 0):
            result.empty_evidence = 'nenhuma seleção de pessoal nesta página JSON íntegra'
        if result.truncated:
            result.diagnostics.append('limite de candidatos atingido; cobertura parcial')
        return result

    def _detail(self, candidate, html):
        self._check_candidate(candidate)
        data = self._json(html)
        if (type(data.get('id')) is not int or str(data['id']) != candidate.external_id
                or not isinstance(data.get('titulo'), str) or not self.in_scope(data['titulo'])
                or not candidate.title_observed
                or not title_is_corroborated(candidate.title_observed, data['titulo'])
                or not isinstance(data.get('documentos'), list)):
            raise ValueError('identidade ou documentos Uniselva incompatíveis')
        return data

    def confirm_identity(self, candidate, html, url):
        self.validate_detail_url(url)
        if self.candidate_from_url(url).external_id != candidate.external_id:
            raise ValueError('detalhe pertence a outra seleção')
        self._detail(candidate, html)

    def validate_document_url(self, url, candidate):
        self._check_candidate(candidate)
        p = self._destination(url)
        if (p.hostname != self.document_hosts[0] or p.query
                or not re.fullmatch(r'/Editais/' + re.escape(candidate.external_id) + r'/[^/]+\.pdf', unquote(p.path), re.I)):
            raise ValueError('documento fora do diretório oficial da seleção Uniselva')

    def documents(self, html, candidate):
        data = self._detail(candidate, html)
        docs, seen = [], set()
        for item in data['documentos']:
            if not isinstance(item, dict) or type(item.get('idSelecao')) is not int or str(item['idSelecao']) != candidate.external_id:
                raise ValueError('associação documental Uniselva incompatível')
            if item.get('isExcluido') is True:
                continue
            title, url = item.get('descricao'), item.get('arquivo')
            if not isinstance(title, str) or not title.strip() or not isinstance(url, str):
                raise ValueError('manifesto documental Uniselva inválido')
            self.validate_document_url(url, candidate)
            url = quote(url, safe=':/%')
            if url in seen:
                continue
            seen.add(url)
            kind = document_kind(title, url)
            if 'portaria' in folded(title) or 'comissao' in folded(title):
                kind = 'outro'
            docs.append(DocumentCandidate(doc_id=hashlib.sha256(url.encode()).hexdigest()[:20], title=title,
                url_requested=url, kind=kind, reason_chosen='manifesto JSON oficial com idSelecao e diretório corroborados'))
        return docs


BATCH30_UNISELVA_ADAPTERS = (UniselvaAdapter(),)
