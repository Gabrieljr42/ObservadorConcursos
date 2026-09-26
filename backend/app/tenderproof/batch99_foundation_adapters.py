"""Bounded personnel contracts supported by September 2026 official captures."""
import hashlib
import re
from datetime import datetime, timezone
from urllib.parse import urljoin, urlsplit

from bs4 import BeautifulSoup
from app.tenderproof.contracts import DiscoveredCandidate
from app.tenderproof.pilot_adapters import PilotHTMLAdapter, folded, visible_soup
from app.tenderproof.batch60_major_adapters import document
from app.tenderproof.validation import title_is_corroborated


class PersonnelWordPressAdapter(PilotHTMLAdapter):
    listing_query_keys = ()
    heading_selector = ''
    documents_selector = ''

    def in_scope(self, title, url):
        text = folded(title + ' ' + url)
        return super().in_scope(title, url) and not any(term in text for term in (
            'bolsista', 'bolsa', 'fomento', 'vestibular', 'licitacao', 'fornecedores'))

    def _title(self, anchor):
        return anchor.get_text(' ', strip=True)

    def confirm_identity(self, candidate, html, url):
        if len(html.encode('utf8')) > 2 * 1024 * 1024:
            raise ValueError('detalhe excede 2 MiB')
        soup = self._check_detail(candidate, html, url)
        canonicals = soup.select('link[rel=canonical]')
        if len(canonicals) != 1 or canonicals[0].get('href') != url:
            raise ValueError('identidade canônica da fundação incompatível')
        titles = {node.get_text(' ', strip=True) for node in soup.select(self.heading_selector)}
        if len(titles) != 1 or not candidate.title_observed or not title_is_corroborated(candidate.title_observed, next(iter(titles))):
            raise ValueError('título da fundação incompatível ou ambíguo')
        number_pattern = r'(?<![\d/])\d{2,3}/\d{4}(?!\d)'
        expected_numbers = set(re.findall(number_pattern, candidate.title_observed))
        if expected_numbers and set(re.findall(number_pattern, next(iter(titles)))) != expected_numbers:
            raise ValueError('número/ano do cabeçalho incompatível')
        if not self.in_scope(candidate.title_observed, url):
            raise ValueError('seleção fora do escopo de pessoal')

    def validate_document_url(self, url, candidate):
        self._check_candidate(candidate)
        p = self._destination(url)
        if p.hostname != self.portal_host or p.query or not re.fullmatch(r'/wp-content/uploads/\d{4}/\d{2}/[^/]+\.pdf', p.path, re.I):
            raise ValueError('documento fora do diretório oficial observado')

    def documents(self, html, candidate):
        self.confirm_identity(candidate, html, candidate.detail_url_observed)
        soup = visible_soup(html)
        docs, seen = [], set()
        for anchor in soup.select(self.documents_selector):
            url = urljoin(candidate.detail_url_observed, anchor['href'])
            if not urlsplit(url).path.lower().endswith('.pdf'):
                continue
            self.validate_document_url(url, candidate)
            if url in seen:
                continue
            seen.add(url)
            docs.append(document(self.source, self.document_title(anchor), url))
        return docs

    def document_title(self, anchor):
        return anchor.get_text(' ', strip=True)


class FUNPECAdapter(PersonnelWordPressAdapter):
    source = 'funpec_selection'
    detail_pattern = r'/processo-seletivo/([a-z0-9_-]+)/'
    document_identity_pattern = r'funpec\.br/processo-seletivo/([a-z0-9_-]+)/'
    candidate_selector = 'a[href*="/processo-seletivo/"]'
    ready_selectors = (candidate_selector,)
    listing_query_keys = ('pagina',)
    heading_selector = 'h1.display-4'
    documents_selector = '.funpec-selection-process-content .wp-block-file a[href]'

    def __init__(self):
        super().__init__(self.source, 'https://funpec.br/processos-seletivos/', listing_paths=(
            '/processos-seletivos/', '/processos-seletivos/novos/',
            '/processos-seletivos/em-andamento/', '/processos-seletivos/encerrados/'))

    def documents(self, html, candidate):
        docs = super().documents(html, candidate)
        # Real detail 12/2026 currently links an EDITAL 13/2026. Preserve the
        # contradiction as an impediment rather than accepting an adjacent call.
        numbers = set(re.findall(r'(?<![\d/])\d{2}/\d{4}(?!\d)', candidate.title_observed or ''))
        for doc in docs:
            if doc.kind == 'edital' and numbers:
                declared = set(re.findall(r'(?<![\d/])\d{2}/\d{4}(?!\d)', doc.title))
                if declared != numbers:
                    raise ValueError('número/ano do edital FUNPEC diverge do processo observado')
        return docs


class FADEAdapter(PersonnelWordPressAdapter):
    source = 'fade_selection'
    detail_pattern = r'/([a-z0-9-]+-edital-\d+-\d{4}-fade-ufpe)/'
    document_identity_pattern = r'fade\.org\.br/([a-z0-9-]+-edital-\d+-\d{4}-fade-ufpe)/'
    candidate_selector = 'h2.wppsac-post-title a[href]'
    ready_selectors = (candidate_selector,)
    heading_selector = 'article h1.cm-entry-title'
    documents_selector = 'article .cm-entry-summary a[href]'

    def __init__(self):
        super().__init__(self.source, 'https://fade.org.br', listing_paths=('', '/'))

    def in_scope(self, title, url):
        return super().in_scope(title, url) and 'cadastro' in folded(title) and 'edital' in folded(title)

    def document_title(self, anchor):
        title = super().document_title(anchor)
        return re.sub(r'^Download do (Edital \d+/\d{4}) completo$', r'\1', title, flags=re.I)

    def documents(self, html, candidate):
        docs = super().documents(html, candidate)
        expected = set(re.findall(r'\d{3}/\d{4}', candidate.title_observed or ''))
        for doc in docs:
            if doc.kind == 'edital' and expected and set(re.findall(r'\d{3}/\d{4}', doc.title)) != expected:
                raise ValueError('número/ano do edital FADE incompatível')
        return docs


class FAPERGSAdapter(PilotHTMLAdapter):
    source = 'fapergs_selection'
    detail_pattern = r'/(selecao-2025)'
    document_identity_pattern = r'fapergs\.rs\.gov\.br/(selecao-\d{4})'
    candidate_selector = 'a[href]'
    listing_query_keys = ()
    ready_selectors = ('h1.artigo__titulo',)

    def __init__(self):
        super().__init__(self.source, 'https://fapergs.rs.gov.br/selecao-2025',
                         document_hosts=('admin.fapergs.rs.gov.br',))

    def _candidates(self, html, url, limit):
        soup = visible_soup(html)
        heading = soup.select_one('h1.artigo__titulo')
        if heading is None or heading.get_text(' ', strip=True) != 'Processo Seletivo 2025':
            return []
        # Both strings are literal visible site/contest headings. The added
        # institution disambiguates the otherwise entirely generic PDF title.
        institution = soup.select_one('h1.text-hide')
        if institution is None or not institution.get_text(' ', strip=True).startswith('FAPERGS -'):
            return []
        return [self.candidate_from_url(url, 'FAPERGS - ' + heading.get_text(' ', strip=True))]

    def confirm_identity(self, candidate, html, url):
        if len(html.encode('utf8')) > 2 * 1024 * 1024:
            raise ValueError('detalhe excede 2 MiB')
        self._check_detail(candidate, html, url)
        expected = self._candidates(html, url, 1)
        if len(expected) != 1 or candidate.title_observed != expected[0].title_observed:
            raise ValueError('identidade FAPERGS 2025 incompatível')

    def validate_document_url(self, url, candidate):
        self._check_candidate(candidate)
        p = self._destination(url)
        if p.hostname not in self.allowed_hosts or p.query or not re.fullmatch(r'/upload/arquivos/\d{6}/[a-z0-9-]+\.pdf', p.path):
            raise ValueError('PDF FAPERGS fora do diretório observado')

    def documents(self, html, candidate):
        self.confirm_identity(candidate, html, candidate.detail_url_observed)
        soup = visible_soup(html)
        result, seen = [], set()
        for anchor in soup.select('ul.lista-texto a[download][href]'):
            url = urljoin(candidate.detail_url_observed, anchor['href'])
            if not urlsplit(url).path.lower().endswith('.pdf'):
                continue
            self.validate_document_url(url, candidate)
            if url in seen:
                continue
            seen.add(url)
            title = re.sub(r'\s*\(\.pdf .*?\)\s*$', '', anchor.get_text(' ', strip=True), flags=re.I)
            doc = document(self.source, title, url)
            if folded(title) != 'edital contratacao temporaria':
                doc.kind = 'outro'
            result.append(doc)
        return result


class FAPEXAdapter(PilotHTMLAdapter):
    """Public notices are separate from the CPF/password-only HR portal."""
    source = 'fapex_selection'
    detail_pattern = r'/Fapex/Site/Principal/Edital/detalhe/id/([A-Za-z0-9_-]+)'
    document_identity_pattern = r'(?!)'  # opaque case-sensitive IDs are not printed in PDFs
    candidate_selector = 'a[href*="/Fapex/Site/Principal/Edital/detalhe/id/"]'
    ready_selectors = (candidate_selector,)
    listing_query_keys = ()

    def __init__(self):
        super().__init__(self.source, 'https://fapex.org.br:443/Fapex/Site/Principal/Edital/index')

    def _title(self, anchor):
        heading = anchor.parent.select_one('h4')
        return heading.get_text(' ', strip=True) if heading else None

    def in_scope(self, title, url):
        text = folded(title)
        return not any(t in text for t in ('bolsista', 'bolsa', 'fomento', 'projetos de pesquisa', 'vestibular')) and bool(re.search(r'estagiari|contratacao|selecao de pessoal|emprego|seleciona\s+profissiona|selecao\s+para\s+profissiona', text))

    def confirm_identity(self, candidate, html, url):
        if len(html.encode('utf8')) > 2097152:
            raise ValueError('detalhe excede 2 MiB')
        soup = self._check_detail(candidate, html, url)
        markers = soup.select('#redesSociais')
        headings = markers[0].parent.find_all('p', recursive=False) if len(markers) == 1 else []
        if len(headings) < 2 or not folded(headings[0].get_text(' ', strip=True)).startswith('data de lancamento'):
            raise ValueError('cabeçalho público FAPEX ausente')
        title = headings[1].get_text(' ', strip=True)
        if not candidate.title_observed or not title_is_corroborated(candidate.title_observed, title) or not self.in_scope(title, url):
            raise ValueError('título ou escopo de pessoal FAPEX incompatível')

    def validate_document_url(self, url, candidate):
        self._check_candidate(candidate)
        p = self._destination(url)
        if p.hostname != self.portal_host or p.query or not re.fullmatch(r'/Fapex/Harp/sys/web/pub/arquivos/pdf/editais/[A-Za-z0-9_!.-]+\.pdf', p.path):
            raise ValueError('documento FAPEX fora do diretório público de editais')

    def documents(self, html, candidate):
        self.confirm_identity(candidate, html, candidate.detail_url_observed)
        docs, seen = [], set()
        for anchor in visible_soup(html).select('ul.w3-ul a[href]'):
            url = urljoin(candidate.detail_url_observed, anchor['href'])
            if not urlsplit(url).path.lower().endswith('.pdf'):
                continue
            self.validate_document_url(url, candidate)
            if url in seen:
                continue
            seen.add(url)
            label = anchor.select_one('p.cp')
            title = label.get_text(' ', strip=True) if label else ''
            doc = document(self.source, title, url)
            doc.kind = 'edital' if folded(title) == 'abertura e inscricoes' else 'outro'
            docs.append(doc)
        return docs


BATCH99_FOUNDATION_ADAPTERS = {a.source: a for a in (FUNPECAdapter(), FADEAdapter(), FAPERGSAdapter())}
BATCH99_FOUNDATION_PUBLIC_ALTERNATIVE_ADAPTERS = {a.source: a for a in (FAPEXAdapter(),)}


class SectionIdentityAdapter(PilotHTMLAdapter):
    """Observed section IDs share a real URL; a URL alone is never a contest."""
    listing_query_keys = ()
    document_identity_pattern = r'(?!)'  # No contest URL ID exists on these pages.

    def validate_detail_url(self, url):
        self.validate_listing_url(url)

    def candidate_from_url(self, url, title=None):
        self.validate_detail_url(url)
        external = self.section_identity(title) if title else None
        if title and not external:
            raise ValueError('título sem identificador de seção observado')
        # The HTTP driver's URL-only context carries NO external ID. Discovery,
        # confirmation and canonical.context reject it as a publishable candidate.
        suffix = hashlib.sha256((external or 'transport-context').encode()).hexdigest()[:16]
        return DiscoveredCandidate(candidate_id=self.source+'-'+suffix, source=self.source,
            external_id=external, title_observed=title, detail_url_observed=url,
            observed_at=datetime.now(timezone.utc))

    def _check_candidate(self, candidate):
        expected = self.candidate_from_url(candidate.detail_url_observed, candidate.title_observed)
        if not candidate.external_id or candidate.source != self.source or candidate.external_id != expected.external_id:
            raise ValueError('identidade de seção ausente ou incompatível')

    def _candidates(self, html, url, limit):
        return [self.candidate_from_url(url, title) for title, _ in self.sections(html)][:limit]

    def section(self, candidate, html):
        self._check_candidate(candidate)
        if len(html.encode('utf8')) > 2097152:
            raise ValueError('detalhe excede 2 MiB')
        matches = [(title, node) for title, node in self.sections(html)
                   if self.section_identity(title) == candidate.external_id]
        if len(matches) != 1 or matches[0][0] != candidate.title_observed:
            raise ValueError('seção documental ausente, duplicada ou incompatível')
        return matches[0][1]

    def confirm_identity(self, candidate, html, url):
        self.validate_detail_url(url)
        if url != candidate.detail_url_observed:
            raise ValueError('URL de seção incompatível')
        self.section(candidate, html)

    def validate_document_url(self, url, candidate):
        # The service binds the actual selected section before download; the
        # driver's title-free context is permitted only to enforce transport.
        self.validate_detail_url(candidate.detail_url_observed)
        if candidate.source != self.source:
            raise ValueError('contexto de outra fonte')
        if candidate.external_id:
            self._check_candidate(candidate)
        p = self._destination(url)
        if p.hostname != self.portal_host or p.query or not re.fullmatch(self.document_path, p.path, re.I):
            raise ValueError('documento fora do diretório da fundação')

    def documents(self, html, candidate):
        scope = self.section(candidate, html)
        docs, seen = [], set()
        for anchor in scope.select('a[href]'):
            url = urljoin(candidate.detail_url_observed, anchor['href'])
            if not urlsplit(url).path.lower().endswith('.pdf'):
                continue
            self.validate_document_url(url, candidate)
            if url in seen:
                continue
            seen.add(url)
            docs.append(document(self.source, anchor.get_text(' ', strip=True), url))
        return docs


class FATECAdapter(SectionIdentityAdapter):
    source = 'fatec_selection'
    ready_selectors = ('table#ProcessosSeletivos',)
    document_path = r'/doc\.licitacoes/edital_\d{12}-fatec\.pdf'
    document_identity_pattern = r'(?:processo\s+seletivo|edital)[^\n]{0,30}?(\d{4}/\d{7}-\d{2})'

    def __init__(self):
        super().__init__(self.source, 'https://www.fatecsm.org.br/processos-seletivos/')

    def section_identity(self, title):
        match = re.match(r'^Processo Seletivo (\d{4}/\d{7}-\d{2}) - ', title or '')
        return match[1] if match else None

    def sections(self, html):
        soup = visible_soup(html)
        result = []
        for row in soup.select('table#ProcessosSeletivos tbody > tr'):
            cells = row.find_all('td', recursive=False)
            if len(cells) != 5:
                raise ValueError('linha FATEC fora do contrato de cinco colunas')
            number, description = (cells[i].get_text(' ', strip=True) for i in (1, 3))
            text = folded(description)
            if not re.fullmatch(r'\d{4}/\d{7}-\d{2}', number):
                raise ValueError('identificador FATEC inválido')
            if any(t in text for t in ('bolsista', 'bolsa', 'fomento', 'vestibular', 'licitacao')):
                continue
            if not re.search(r'auxiliar|assistente|analista|tutor|psicolog|estagiar|pessoa fisica|tecnico|professor', text):
                continue
            result.append(('Processo Seletivo '+number+' - '+description, cells[4]))
        return result


class FAPPRAdapter(SectionIdentityAdapter):
    source = 'fappr_selection'
    ready_selectors = ('h1.page-title', '.spoiler-content h4')
    document_path = r'/sites/fundacao-araucaria/arquivos_restritos/files/documento/\d{4}-\d{2}/[^/]+\.pdf'
    document_identity_pattern = r'\b(?:ps|edital)\s+(\d{2}/\d{4}|\d{3}/\d{2})\b'

    def __init__(self):
        super().__init__(self.source, 'https://www.fappr.pr.gov.br/Pagina/Processos-Seletivos')

    def expanded(self, html):
        soup = BeautifulSoup(html, 'lxml')
        # These literal accordion containers carry the public historical years.
        # Expand only this observed UI structure, never arbitrary hidden nodes.
        for node in soup.select('article.node--type-pagina .spoiler > .spoiler-content'):
            if node.get('style', '').replace(' ', '').rstrip(';') == 'display:none':
                node.attrs.pop('style')
        return str(soup)

    def parse_listing(self, html, url, limit=200):
        if len(html.encode('utf8')) > 2097152:
            raise ValueError('listagem excede 2 MiB')
        return super().parse_listing(self.expanded(html), url, limit)

    def section_identity(self, title):
        match = re.match(r'^Fundação Araucária - (PS \d{2}/\d{4}|Edital \d{3}/\d{2}):', title or '')
        return match[1].split(' ', 1)[1] if match else None

    def sections(self, html):
        soup = visible_soup(self.expanded(html))
        heading = soup.select_one('h1.page-title')
        if heading is None or heading.get_text(' ', strip=True) != 'Processos Seletivos':
            return []
        result = []
        for heading in soup.select('article.node--type-pagina .spoiler-content h4'):
            title = heading.get_text(' ', strip=True)
            title = ' '.join(title.split())
            text = folded(title)
            full_title = 'Fundação Araucária - ' + title
            if not self.section_identity(full_title) or any(t in text for t in (
                    'bolsista', 'bolsa', 'fomento', 'vestibular', 'eleicao', 'representante sindical')):
                continue
            if not any(t in text for t in ('estagio', 'aprendiz', 'emprego publico')):
                continue
            siblings = []
            for node in heading.next_siblings:
                if getattr(node, 'name', None) == 'h4':
                    break
                siblings.append(str(node))
            result.append((full_title, BeautifulSoup(''.join(siblings), 'lxml')))
        return result


# Separate export: do not enable until same-URL distinct-contest canonical and
# driver-context proofs have been reviewed. These are implemented, not live-approved.
BATCH99_FOUNDATION_SECTION_ADAPTERS = {a.source: a for a in (FATECAdapter(), FAPPRAdapter())}


class FAPESEAdapter(SectionIdentityAdapter):
    """Personnel RPA calls on the observed public PRONERA programme page."""
    source = 'fapese_selection'
    ready_selectors = ('h1.page-title', 'main a.button-card h4.button-card__title')
    document_path = r'/wp-content/uploads/\d{4}/\d{2}/Edital-\d{3}\.\d{4}-RPA-PRONERA-\d{4}_assinado_assinado\.pdf'
    document_identity_pattern = r'\bedital\s*(?:n[ºo°.]*)?\s*(\d{3}/\d{4})\b'

    def __init__(self):
        super().__init__(self.source, 'https://www.fapese.org.br/pronera/')

    def section_identity(self, title):
        match = re.match(r'^FAPESE - PRONERA - EDITAL Nº (\d{3}/\d{4}) - ', title or '')
        return match[1] if match else None

    def validate_document_url(self, url, candidate):
        super().validate_document_url(url, candidate)
        match = re.search(r'/Edital-(\d{3})\.(\d{4})-RPA-PRONERA-', urlsplit(url).path)
        if not match or (candidate.external_id and candidate.external_id != match[1]+'/'+match[2]):
            raise ValueError('número/ano do PDF PRONERA diverge da seção')

    def sections(self, html):
        soup = visible_soup(html)
        headings = [h.get_text(' ', strip=True) for h in soup.select('h1.page-title')]
        canonical = [a.get('href') for a in soup.select('link[rel=canonical]')]
        if headings != ['Pronera'] or canonical != [self.listing_urls[0]]:
            raise ValueError('cabeçalho ou canonical PRONERA incompatível')
        result = []
        for anchor in soup.select('main a.button-card[href]'):
            headers = anchor.select('h4.button-card__title')
            if len(headers) != 1:
                raise ValueError('cartão PRONERA sem título documental único')
            label = ' '.join(headers[0].get_text(' ', strip=True).split())
            match = re.fullmatch(r'\d{2}/\d{2}/\d{4} - (EDITAL Nº \d{3}/\d{4} - CHAMADA PÚBLICA PARA FORMAÇÃO DE CADASTRO RESERVA PARA PRESTADORES DE SERVIÇO/PESSOA FÍSICA)', label)
            if not match:
                continue
            title = 'FAPESE - PRONERA - '+match[1]
            # Anchor labels carry the number and personnel scope. Preserve the
            # actual URL and isolate this single card from other programme calls.
            scope = BeautifulSoup('<div>'+str(anchor)+'</div>', 'lxml')
            scope.select_one('a').clear()
            scope.select_one('a').append(match[1])
            result.append((title, scope))
        return result


BATCH99_FOUNDATION_FAPESE_ADAPTERS = {a.source: a for a in (FAPESEAdapter(),)}
