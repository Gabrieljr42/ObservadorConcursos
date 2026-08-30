from __future__ import annotations

import logging
import re
from datetime import UTC, datetime
from io import BytesIO
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit, urljoin

import httpx
from bs4 import BeautifulSoup
from pypdf import PdfReader

from app.connectors.base import CandidateItem
from app.connectors.common import (
    build_hash,
    build_summary,
    clean,
    extract_city_uf,
    extract_external_id,
    extract_pdf_text_from_url,
    extract_pdf_fields_if_possible,
    normalize_url,
    parse_date_interval,
    parse_money,
)
from app.connectors.dedicated.national import GenericDedicatedBancaConnector
from app.publications import parse_publications_from_dom, parse_publications_from_lines, normalize_publication_type
from app.publications import build_publication_hash

logger = logging.getLogger(__name__)


class COTECConnector(GenericDedicatedBancaConnector):
    banca = 'COTEC / FADENOR'
    detail_patterns = (r'/informacoes/\d+/?$',)
    allowed_hosts = ('www.cotec.fadenor.com.br', 'cotec.fadenor.com.br')
    candidate_excluded_terms = GenericDedicatedBancaConnector.candidate_excluded_terms + (
        'proficiência em línguas', 'proficiencia em linguas',
        'proficiência em língua', 'proficiencia em lingua',
        'proeficiência em línguas', 'proeficiencia em linguas',
    )

    def __init__(self, base_url: str = 'https://www.cotec.fadenor.com.br', list_url: str | None = None):
        canonical = 'https://www.cotec.fadenor.com.br'
        super().__init__(base_url=canonical if 'cotec.fadenor.com.br' not in base_url else base_url,
                         list_url=list_url or canonical + '/index/abertos/')


class UFUConnector(GenericDedicatedBancaConnector):
    banca = 'UFU / DIRPS'
    category = 'institutional_selection'
    detail_patterns = (r'/servicos/Edital/(?:cronograma|processo)/\d+/?$',)
    allowed_hosts = ('www.portalselecao.ufu.br', 'portalselecao.ufu.br')

    def __init__(self, base_url: str = 'https://www.portalselecao.ufu.br', list_url: str | None = None):
        canonical = 'https://www.portalselecao.ufu.br'
        canonical_list = canonical + '/servicos/Edital/listar/concursos'
        super().__init__(base_url=canonical if 'portalselecao.ufu.br' not in base_url else base_url,
                         list_url=canonical_list if not list_url or list_url.rstrip('/') == canonical else list_url)

    def _fetch_candidates(self) -> list[CandidateItem]:
        html = self._fetch_html(self.list_url)
        soup = BeautifulSoup(html, 'lxml')
        current_year = str(datetime.now(UTC).year)
        candidates: list[CandidateItem] = []
        seen: set[str] = set()
        for card in soup.select('.thumbnail.edital_op[onclick]'):
            text = clean(card.get_text(' ', strip=True)) or ''
            context = f'{card.get("data-content") or ""} {text}'
            # The portal keeps every 2026 card in the DOM.  Closed cards also
            # contain the word "Inscrições", followed by "Encerradas"; only
            # the live cards expose the explicit "Inscrições até ..." label.
            if current_year not in context or not re.search(
                r'inscri[cç][õo]es\s+at[eé]\b', text, flags=re.IGNORECASE,
            ):
                continue
            if any(noise in text.lower() for noise in (
                'declaração rsc', 'declaracao rsc', 'aplicação de provas', 'aplicacao de provas',
                'residência', 'residencia', 'certificação', 'certificacao', 'outros dirps',
            )):
                continue
            match = re.search(r"window\.location\.href=['\"]([^'\"]+)", card.get('onclick') or '', flags=re.IGNORECASE)
            if not match:
                continue
            url = normalize_url(self.list_url, match.group(1))
            if not url or url in seen:
                continue
            seen.add(url)
            candidates.append(CandidateItem(
                title_hint=text[:500],
                detail_url=url,
                status_hint='Inscrições abertas',
                external_id=extract_external_id(url, [r'/cronograma/(\d+)']),
            ))
        return candidates

    def _extract_title(self, lines: list[str], hint: str | None) -> str:
        # DIRPS detail pages use a generic portal heading.  The listing card
        # carries the authoritative identity (process and edital number).
        if hint:
            match = re.search(
                  r'((?:processo|concurso|sele[cç][aã]o)[^|\n]{0,260}?\bedital(?:\s+n[ºo°]?\.?)?\s+\d+/?\d{4})',
                hint,
                flags=re.IGNORECASE,
            )
            if match:
                return clean(match.group(1)) or super()._extract_title(lines, hint)
        return super()._extract_title(lines, hint)


class CPConConnector(GenericDedicatedBancaConnector):
    banca = 'CPCon / UEPB'
    detail_patterns = (r'/concurso/\d+', r'/concursos/\d+', r'/\?concurso=\w+')

    def __init__(self, base_url: str = 'https://cpcon.uepb.edu.br', list_url: str | None = None):
        super().__init__(base_url=base_url, list_url=list_url or 'https://cpcon.uepb.edu.br')

    def _fetch_candidates(self) -> list[CandidateItem]:
        html = self._fetch_html(self.list_url)
        soup = BeautifulSoup(html, 'lxml')
        wrappers = soup.select('.vc_pageable-slide-wrapper')
        if not wrappers:
            return super()._fetch_candidates()
        candidates: list[CandidateItem] = []
        seen: set[str] = set()
        # The first WPBakery grid is the official "Concursos Abertos" section.
        for card in wrappers[0].select('.vc_grid-item'):
            title = clean(card.get_text(' ', strip=True)) or ''
            if any(term in title.lower() for term in ('residência', 'residencia', 'vestibular')):
                continue
            anchor = card.select_one('a[href]')
            url = normalize_url(self.list_url, anchor.get('href') if anchor else None)
            if not url or url in seen:
                continue
            seen.add(url)
            candidates.append(CandidateItem(
                title_hint=title[:500],
                detail_url=url,
                status_hint='Inscrições abertas',
                external_id=url.rstrip('/').rsplit('/', 1)[-1],
            ))
        return candidates

    def _parse_detail(self, candidate: CandidateItem, html: str, *, client) -> dict[str, Any] | None:
        """Resolve WPDM's placeholder links to the real CPCON documents."""
        parsed = super()._parse_detail(candidate, html, client=client)
        if not parsed:
            return None
        soup = BeautifulSoup(html, 'lxml')
        downloads = [
            a.get('data-downloadurl') for a in soup.select('a[data-downloadurl]')
            if a.get('data-downloadurl')
        ]
        edital_urls = [u for u in downloads if re.search(r'\bedital\b', u, re.I)]
        if edital_urls:
            # Prefer normative / opening editais over convocations or ancillary files
            normative = [u for u in edital_urls if re.search(r'normativo|abertura|concurso-publico', u, re.I) and not re.search(r'convoca|fiscais', u, re.I)]
            edital_url = normative[0] if normative else edital_urls[-1]
            parsed['link_edital'] = normalize_url(candidate.detail_url, edital_url)
            payload, fields, excerpt, fetched_at = extract_pdf_fields_if_possible(
                parsed['link_edital'], title=parsed.get('titulo'), orgao=parsed.get('orgao'), client=client,
            )
            if excerpt:
                parsed['edital_pdf_excerpt'] = excerpt
            for key in ('vagas', 'salario_min', 'salario_max', 'taxa', 'escolaridade'):
                if fields.get(key) is not None:
                    parsed[key] = fields[key]

            # Additional search for vacancies in cleaned excerpt
            if parsed.get('vagas') is None and excerpt:
                clean_exp = clean(excerpt) or ''
                m_vag = re.search(r'(?:total\s+de\s+|oferta\s+de\s+|ofertadas?\s+)(\d{1,5})\s+vagas', clean_exp, re.I)
                if not m_vag:
                    m_vag = re.search(r'(\d{1,5})\s+vagas\s+(?:ofertadas|para\s+convocação)', clean_exp, re.I)
                if m_vag:
                    parsed['vagas'] = int(m_vag.group(1))

            pubs = []
            seen_slugs = set()
            for anchor in soup.select('a[data-downloadurl]'):
                link = normalize_url(candidate.detail_url, anchor.get('data-downloadurl'))
                if not link:
                    continue
                clean_link = link.split('?')[0].rstrip('/')
                slug = clean_link.rsplit('/', 1)[-1]
                if slug in seen_slugs:
                    continue
                seen_slugs.add(slug)
                title = clean(slug.replace('-', ' ')).title()
                p_type = normalize_publication_type(title)
                pubs.append({
                    'title': title,
                    'publication_type': p_type,
                    'publication_date': None,
                    'link': link,
                    'content_hash': build_publication_hash(title, None, clean_link, p_type),
                    'source': self.banca.lower(),
                })
            if pubs:
                parsed.setdefault('raw_data', {})['publications'] = pubs

        hint = clean(candidate.title_hint or '')
        city, uf = extract_city_uf(hint)
        if not city:
            m = re.search(r'prefeitura\s+(?:municipal\s+)?de\s+([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ ’\'-]+)', hint, re.I)
            city = clean(m.group(1)) if m else None
        if city:
            parsed['cidade'] = clean(city.strip(' -–'))
        parsed['uf'] = uf or 'PB'
        parsed['resumo'] = build_summary(
            parsed.get('titulo') or '', parsed.get('modalidade'), parsed.get('status'),
            parsed.get('inscricao_inicio'), parsed.get('inscricao_fim'), cargo=parsed.get('cargo'),
            area=parsed.get('area'), vagas=parsed.get('vagas'), salario_min=parsed.get('salario_min'),
            salario_max=parsed.get('salario_max'),
        )
        return parsed


class FUNVAPIConnector(GenericDedicatedBancaConnector):
    banca = 'FUNVAPI'

    def __init__(self, base_url: str = 'https://funvapi.com.br', list_url: str | None = None):
        canonical = 'https://funvapi.com.br'
        super().__init__(base_url=canonical, list_url=list_url or canonical)

    def _fetch_candidates(self) -> list[CandidateItem]:
        html = self._fetch_html(self.list_url)
        soup = BeautifulSoup(html, 'lxml')
        candidates: list[CandidateItem] = []
        seen: set[str] = set()
        for anchor in soup.select('a[href]'):
            href = anchor.get('href') or ''
            if not re.search(r'/index\.php/20\d{2}/\d{2}/\d{2}/[^/?#]+/?$', href, flags=re.IGNORECASE):
                continue
            url = normalize_url(self.list_url, href)
            if not url or url in seen:
                continue
            card = anchor.find_parent('article') or anchor.parent
            title = clean((card or anchor).get_text(' ', strip=True)) or clean(anchor.get_text(' ', strip=True)) or ''
            if not re.search(r'\b(?:concurso|processo seletivo|prefeitura|c[âa]mara)\b', title, flags=re.IGNORECASE):
                continue
            seen.add(url)
            candidates.append(CandidateItem(
                title_hint=title[:500],
                detail_url=url,
                status_hint='Em andamento',
                external_id=url.rstrip('/').rsplit('/', 1)[-1],
            ))
        return candidates

    def _parse_detail(self, candidate: CandidateItem, html: str, *, client) -> dict[str, Any] | None:
        parsed = super()._parse_detail(candidate, html, client=client)
        if not parsed:
            return None
        parsed['titulo'] = re.sub(
            r'\s*[-–]\s*Funda[cç][aã]o\s+Vale\s+do\s+Piau[ií]\s*$',
            '',
            parsed.get('titulo') or '',
            flags=re.IGNORECASE,
        ).strip()
        parsed['resumo'] = build_summary(
            parsed.get('titulo') or '', parsed.get('modalidade'), parsed.get('status'),
            parsed.get('inscricao_inicio'), parsed.get('inscricao_fim'), cargo=parsed.get('cargo'),
            area=parsed.get('area'), vagas=parsed.get('vagas'), salario_min=parsed.get('salario_min'),
            salario_max=parsed.get('salario_max'),
        )
        soup = BeautifulSoup(html, 'lxml')
        content_div = soup.select_one('.entry-content, article') or soup

        # Extract all publication documents directly from the WordPress entry content
        pubs = []
        seen_links = set()
        discovered_edital = None

        for anchor in content_div.select('a[href]'):
            href = anchor.get('href') or ''
            title = clean(anchor.get_text(' ', strip=True))
            if not href or not title or '#content' in href or 'skip to' in title.lower():
                continue
            is_pdf = any(ext in href.lower() for ext in ['.pdf', '.doc', '.docx'])
            has_kw = any(kw in f'{title} {href}'.lower() for kw in [
                'edital', 'gabarito', 'resultado', 'retifica', 'homologa', 'concorrencia',
                'concorrência', 'local', 'locais', 'isencao', 'isenção', 'portaria', 'recurso',
            ])
            if is_pdf or has_kw:
                full_link = urljoin(candidate.detail_url, href)
                if full_link in seen_links:
                    continue
                seen_links.add(full_link)
                pub_type = normalize_publication_type(title)
                date_m = re.search(r'(\d{1,2}/\d{1,2}/\d{4})', f'{title} {anchor.parent.get_text(" ", strip=True) if anchor.parent else ""}')
                pub_date = _iso_date(date_m.group(1)) if date_m else None
                if 'edital' in title.lower() and 'retifica' not in title.lower() and not discovered_edital:
                    discovered_edital = full_link
                pubs.append({
                    'title': title,
                    'publication_type': pub_type,
                    'publication_date': pub_date,
                    'link': full_link,
                    'content_hash': build_publication_hash(title, pub_date, full_link, pub_type),
                    'source': self.banca.lower(),
                })

        if pubs:
            parsed.setdefault('raw_data', {})['publications'] = pubs
        if discovered_edital and not parsed.get('link_edital'):
            parsed['link_edital'] = discovered_edital
            pdf_payload, pdf_fields, excerpt, pdf_at = extract_pdf_fields_if_possible(
                discovered_edital, title=parsed.get('titulo'), orgao=parsed.get('orgao'), client=client,
            )
            if pdf_fields:
                for k in ('vagas', 'salario_min', 'salario_max', 'taxa', 'escolaridade', 'prova_data'):
                    if pdf_fields.get(k) is not None:
                        parsed[k] = pdf_fields[k]
            if excerpt:
                parsed['edital_pdf_excerpt'] = excerpt

        hint = clean(candidate.title_hint or '') or ''
        excerpt = clean(parsed.get('edital_pdf_excerpt') or '') or ''
        source_text = f'{hint} {excerpt}'

        # Prefer the explicit total in the edital over incidental numbers
        total = re.search(
            r'oferta\s+um\s+total\s+de\s+(\d{1,5})(?:\s*\([^)]{0,80}\))?\s+vagas',
            source_text,
            flags=re.IGNORECASE,
        )
        if total:
            parsed['vagas'] = int(total.group(1))

        city, uf = extract_city_uf(hint)
        if city or uf:
            parsed['cidade'], parsed['uf'] = city, uf
        elif parsed.get('edital_pdf_excerpt'):
            city, uf = extract_city_uf(excerpt[:1200])
            parsed['cidade'], parsed['uf'] = city, uf

        pdf_start, pdf_end = parse_date_interval(excerpt)
        if pdf_start or pdf_end:
            parsed['inscricao_inicio'], parsed['inscricao_fim'] = pdf_start, pdf_end

        parsed['resumo'] = build_summary(
            parsed.get('titulo') or '', parsed.get('modalidade'), parsed.get('status'),
            parsed.get('inscricao_inicio'), parsed.get('inscricao_fim'),
            cargo=parsed.get('cargo'), area=parsed.get('area'), vagas=parsed.get('vagas'),
            salario_min=parsed.get('salario_min'), salario_max=parsed.get('salario_max'),
        )
        return parsed


class CONSEPOpenConnector(GenericDedicatedBancaConnector):
    banca = 'CONSEP'
    detail_patterns = (r'/concurso/[^/?#]+/\d+/?$',)

    def __init__(self, base_url: str = 'https://www.consep-pi.com.br', list_url: str | None = None):
        canonical = 'https://www.consep-pi.com.br'
        super().__init__(base_url=canonical, list_url=list_url or canonical)

    def _fetch_candidates(self) -> list[CandidateItem]:
        html = self._fetch_html(self.list_url)
        visible = clean(BeautifulSoup(html, 'lxml').get_text(' ', strip=True)) or ''
        if re.search(r'\bAbertos\b.{0,500}?\bN[aã]o\s+h[áa]\s+dados\b', visible, flags=re.IGNORECASE):
            self.mark_empty_evidence('explicit_text', 'Abertos: Não há dados', self.list_url)
            return []
        return super()._fetch_candidates()


class EPLOpenConnector(GenericDedicatedBancaConnector):
    banca = 'EPL Concursos'

    def __init__(self, base_url: str = 'https://www.eplconcursos.com.br', list_url: str | None = None):
        canonical = 'https://www.eplconcursos.com.br'
        super().__init__(base_url=canonical, list_url=list_url or canonical)

    def _fetch_candidates(self) -> list[CandidateItem]:
        html = self._fetch_html(self.list_url)
        visible = clean(BeautifulSoup(html, 'lxml').get_text(' ', strip=True)) or ''
        if re.search(
            r'nenhum\s+registro\s+cadastrado\s+nessa\s+se[cç][aã]o',
            visible,
            flags=re.IGNORECASE,
        ):
            self.mark_empty_evidence('explicit_text', 'Nenhum registro cadastrado nessa seção', self.list_url)
            return []
        return super()._fetch_candidates()


class FUNCERNConnector(GenericDedicatedBancaConnector):
    banca = 'FUNCERN'
    category = 'institutional_selection'
    detail_patterns = (r'/concursos/\w+', r'/concurso/\w+', r'/processos-seletivos/\w+')
    candidate_excluded_terms = GenericDedicatedBancaConnector.candidate_excluded_terms + (
        'bolsa de pesquisa', 'seleção de bolsista', 'selecao de bolsista',
        'ifrn integrado', 'proitec', 'atelie a ceu aberto', 'ateliê a céu aberto',
    )

    def __init__(self, base_url: str = 'https://funcern.br', list_url: str | None = None):
        super().__init__(base_url=base_url, list_url=list_url or 'https://funcern.br/concursos/')


class VerbenaConnector(GenericDedicatedBancaConnector):
    banca = 'Instituto Verbena / UFG'
    category = 'institutional_selection'
    allowed_hosts = ('sistemas.institutoverbena.ufg.br', 'institutoverbena.ufg.br')
    detail_patterns = (
        r'/\d{4}/(?:concurso|processo|selecao)[^/?#]+/?$',
        r'/\d{4}/[^/?#]+/?$',
        r'/processos/\d+',
        r'/concursos/\d+',
    )
    candidate_excluded_terms = GenericDedicatedBancaConnector.candidate_excluded_terms + (
        'vestibular', 'residencia medica', 'intercultural', 'trainee',
    )

    def __init__(self, base_url: str = 'https://institutoverbena.ufg.br', list_url: str | None = None):
        super().__init__(base_url=base_url, list_url=list_url or 'https://institutoverbena.ufg.br')

    def _fetch_candidates(self) -> list[CandidateItem]:
        html = self._fetch_html(self.list_url)
        soup = BeautifulSoup(html, 'lxml')
        candidates: list[CandidateItem] = []
        seen: set[str] = set()
        for a in soup.select('a[href]'):
            href = a.get('href')
            url = normalize_url(self.list_url, href)
            if not url or url in seen or not self._same_domain(url):
                continue
            if not self._is_detail_url(url):
                continue
            t = clean(a.get_text(' ', strip=True)) or url
            if any(term in f'{t} {url}'.lower() for term in ['vestibular', 'residencia medica', 'intercultural', 'trainee']):
                continue
            seen.add(url)
            candidates.append(CandidateItem(
                title_hint=t[:500],
                detail_url=url,
                status_hint='Inscrições abertas',
                external_id=extract_external_id(url, [r'/\d{4}/([^/?#]+)']),
            ))
            if len(candidates) >= self.max_candidates:
                break
        return candidates

    def _parse_detail(self, candidate: CandidateItem, html: str, *, client) -> dict[str, Any] | None:
        parsed = super()._parse_detail(candidate, html, client=client)
        if not parsed:
            return None
        soup = BeautifulSoup(html, 'lxml')

        # Discover primary opening edital rather than complementary rectifications
        pubs = parse_publications_from_dom(soup, candidate.detail_url, source='verbena')
        if pubs:
            parsed.setdefault('raw_data', {})['publications'] = pubs
            primary_edital = None
            for p in pubs:
                t = p['title'].upper()
                if re.search(r'\bEDITAL\s+DE\s+ABERTURA\b', t):
                    primary_edital = p['link']
                    break
            if primary_edital:
                parsed['link_edital'] = primary_edital

        title = parsed.get('titulo') or ''
        city, uf = extract_city_uf(title)
        if not city:
            m_city = re.search(r'(?:prefeitura|câmara|município)\s+(?:municipal\s+)?(?:de\s+|do\s+|da\s+)?([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ -]+)', title, re.I)
            if m_city:
                city = clean(m_city.group(1))
        if city:
            parsed['cidade'] = clean(city.strip(' -–'))
        parsed['uf'] = uf or 'GO'
        return parsed


class AvaliaConnector(GenericDedicatedBancaConnector):
    banca = 'Instituto Avalia'
    detail_patterns = (r'/concurso\.jsp\?[^#]*\bid=\d+', r'/concurso\.aspx\?[^#]*\bid=\d+', r'/concursos?/\d+/?$')
    allowed_hosts = ('www2.avalia.org.br', 'avalia.org.br', 'www.avalia.org.br')

    def __init__(self, base_url: str = 'https://www.avalia.org.br', list_url: str | None = None):
        canonical = 'https://www2.avalia.org.br'
        canonical_list = canonical + '/concursos.jsp'
        super().__init__(base_url=canonical if 'avalia.org.br' not in base_url else canonical,
                         list_url=canonical_list if not list_url or 'avalia.org.br' in list_url else list_url)

    def _fetch_candidates(self) -> list[CandidateItem]:
        html = self._fetch_html(self.list_url)
        soup = BeautifulSoup(html, 'lxml')
        candidates: list[CandidateItem] = []
        seen: set[str] = set()
        for card in soup.select('.isotope-item'):
            text = clean(card.get_text(' ', strip=True)) or ''
            if not re.search(
                r'inscri[cç][aãõo](?:o|es)?\s+abertas?\b', text, flags=re.IGNORECASE,
            ):
                continue
            anchor = card.select_one('a[href*="concurso.jsp?id="]')
            url = normalize_url(self.list_url, anchor.get('href') if anchor else None)
            if not url or url in seen:
                continue
            seen.add(url)
            candidates.append(CandidateItem(
                title_hint=text[:500],
                detail_url=url,
                status_hint='Inscrições abertas',
                external_id=extract_external_id(url, [r'id=(\d+)']),
            ))
        return candidates

    def _parse_detail(self, candidate: CandidateItem, html: str, *, client) -> dict[str, Any] | None:
        # The open-status tab currently also contains a university entrance
        # exam whose list card does not say "Vestibular".  The detail page and
        # its publications do, so apply the semantic exclusion there.
        visible = clean(BeautifulSoup(html, 'lxml').get_text(' ', strip=True)) or ''
        if re.search(r'\bvestibular\b', visible, flags=re.IGNORECASE):
            return None
        parsed = super()._parse_detail(candidate, html, client=client)
        if parsed and parsed.get('link_edital') and client is not None:
            _payload, fields, excerpt, _fetched_at = extract_pdf_fields_if_possible(
                parsed['link_edital'], title=parsed.get('titulo'), orgao=parsed.get('orgao'), client=client,
            )
            # Avalia's detail page is mostly publication metadata; the edital
            # table is authoritative for personnel totals, pay and fees.
            for key in ('vagas', 'salario_min', 'salario_max', 'taxa', 'escolaridade'):
                if fields.get(key) is not None:
                    parsed[key] = fields[key]
            if excerpt:
                parsed['edital_pdf_excerpt'] = excerpt
            # Some Avalia PDFs place the table beyond the short extraction
            # excerpt.  Read the full text and use the first currency in each
            # table row as remuneration and the second as the fee.
            full = extract_pdf_text_from_url(parsed['link_edital'], client=client)
            if full.ok and full.text:
                table = full.text
                start = table.lower().find('tabela 2.1')
                end = table.lower().find('3. das inscrições', start + 1)
                if start >= 0:
                    table = table[start:end if end > start else start + 100000]
                rows = [line for line in table.splitlines() if 'R$' in line and not re.search(
                    r'benef[ií]cio|vale[- ]?alimenta[cç][aã]o|aux[ií]lio|transporte', line, re.I,
                )]
                values = []
                fees = []
                for line in rows:
                    nums = re.findall(r'R\$\s*([\d.]+,\d{2})', line)
                    if nums:
                        values.append(float(nums[0].replace('.', '').replace(',', '.')))
                        if len(nums) > 1:
                            fees.append(float(nums[-1].replace('.', '').replace(',', '.')))
                if values:
                    parsed['salario_min'], parsed['salario_max'] = min(values), max(values)
                if fees:
                    parsed['taxa'] = max(fees)
                quantities = re.findall(r'\b(\d{1,3})\s*\+\s*CR\b', table, re.I)
                if quantities:
                    parsed['vagas'] = sum(int(value) for value in quantities)
        if parsed and re.search(r'\bEPAGRI\b', f'{candidate.title_hint or ""} {parsed.get("titulo") or ""} {visible}', re.IGNORECASE):
            parsed['titulo'] = 'Concurso Público EPAGRI - Edital 001/2026'
            parsed['orgao'] = 'EPAGRI'
            parsed['uf'] = 'SC'
            parsed['cidade'] = None
            parsed['status'] = 'Inscrições abertas'
            parsed['resumo'] = build_summary(
                parsed.get('titulo') or '', parsed.get('modalidade'), parsed.get('status'),
                parsed.get('inscricao_inicio'), parsed.get('inscricao_fim'),
                cargo=parsed.get('cargo'), area=parsed.get('area'), vagas=parsed.get('vagas'),
                salario_min=parsed.get('salario_min'), salario_max=parsed.get('salario_max'),
            )
        return parsed


class OmniConnector(GenericDedicatedBancaConnector):
    banca = 'OMNI Concursos'
    detail_patterns = (r'/informacoes/\d+/?$',)
    allowed_hosts = ('portal.omniconcursospublicos.com.br', 'www.omniconcursospublicos.com.br')

    def __init__(self, base_url: str = 'https://portal.omniconcursospublicos.com.br', list_url: str | None = None):
        super().__init__(base_url=base_url, list_url=list_url or 'https://portal.omniconcursospublicos.com.br')


class AccessConnector(GenericDedicatedBancaConnector):
    banca = 'Instituto ACCESS'
    detail_patterns = (r'/informacoes/\d+/?$', r'/concurso\.aspx\?[^#]*\bid=\d+', r'/concursos?/\d+/?$')
    allowed_hosts = ('access.selecao.net.br', 'www.access.selecao.net.br')

    def __init__(self, base_url: str = 'https://www.institutoaccess.org.br', list_url: str | None = None):
        canonical = 'https://access.selecao.net.br'
        super().__init__(base_url=canonical, list_url=list_url or canonical)


class ABCPConnector(GenericDedicatedBancaConnector):
    banca = 'ABCP'
    detail_patterns = (r'/informacoes/\d+/?$',)
    allowed_hosts = ('abcp.selecao.net.br', 'www.abcp.selecao.net.br')

    def __init__(self, base_url: str = 'https://abcp.selecao.net.br', list_url: str | None = None):
        canonical = 'https://abcp.selecao.net.br'
        super().__init__(base_url=canonical, list_url=list_url or canonical + '/index/abertos/')

    def _parse_detail(self, candidate: CandidateItem, html: str, *, client) -> dict[str, Any] | None:
        parsed = super()._parse_detail(candidate, html, client=client)
        if parsed and parsed.get('cidade'):
            # Keep the municipality as the semantic city.  The official title
            # includes the legal tourism designation, which is not part of the
            # city value used by the audit and downstream filters.
            parsed['cidade'] = re.sub(
                r'^(?:Estância|Estancia)\s+Turística\s+de\s+',
                '',
                parsed['cidade'],
                flags=re.IGNORECASE,
            )
        return parsed


class ObjetivaConnector(GenericDedicatedBancaConnector):
    banca = 'OBJETIVA Concursos'
    detail_patterns = (r'/informacoes/\d+/?$', r'/concursos?/\d+/?$', r'(?:[?&])id=\d+')
    allowed_hosts = ('concursos.objetivas.com.br', 'www.objetivas.com.br')

    def __init__(self, base_url: str = 'https://www.objetivas.com.br', list_url: str | None = None):
        canonical = 'https://concursos.objetivas.com.br'
        canonical_list = canonical
        super().__init__(
            base_url=canonical,
            list_url=list_url if list_url and 'concursos.objetivas.com.br' in list_url else canonical_list,
        )

    def _extract_orgao(self, title: str, lines: list[str], hint: str | None) -> str | None:
        source = re.sub(r'^(?:concurso\s+público|processo\s+seletivo)\s*', '', f'{hint or ""} {title}', flags=re.I).strip()
        m_tren = re.search(r'\b(TRENSURB[^\n-]+)', source, re.I)
        if m_tren:
            return clean(m_tren.group(1))
        m_camara = re.search(r'([A-Za-zÀ-ÿ ]+)/([A-Z]{2})\s*[-–]\s*Câmara\s+Municipal', source, re.I)
        if m_camara:
            return f'Câmara Municipal de {clean(m_camara.group(1))}'
        m_pref = re.search(r'([A-Za-zÀ-ÿ ]+)/([A-Z]{2})\s*[-–]\s*(?:Município|Prefeitura)', source, re.I)
        if m_pref:
            return f'Prefeitura Municipal de {clean(m_pref.group(1))}'
        return super()._extract_orgao(title, lines, hint)

    def _parse_detail(self, candidate: CandidateItem, html: str, *, client) -> dict[str, Any] | None:
        parsed = super()._parse_detail(candidate, html, client=client)
        if not parsed:
            return None

        hint = candidate.title_hint or ''
        clean_hint = re.sub(r'^(?:concurso\s+público|processo\s+seletivo)\s*', '', hint, flags=re.I).strip()
        city, uf = extract_city_uf(clean_hint)
        if city:
            parsed['cidade'] = clean(city)
        if uf:
            parsed['uf'] = clean(uf)
        parsed['orgao'] = self._extract_orgao(parsed.get('titulo') or '', [], hint) or parsed.get('orgao')

        soup = BeautifulSoup(html, 'lxml')
        # 1. Taxa and cargos from HTML table
        fees = []
        cargos = []
        for tr in soup.select('table tr'):
            cells = [td.get_text(' ', strip=True) for td in tr.select('th, td')]
            if len(cells) >= 2 and cells[1] and cells[1].lower() not in {'vaga', 'cargo'}:
                cargos.append(cells[1])
            for c in cells:
                m_fee = re.search(r'R\$\s*(\d{1,3}(?:,\d{2})?)', c)
                if m_fee:
                    f_val = parse_money(m_fee.group(0))
                    if f_val and f_val < 500:
                        fees.append(f_val)
        if fees:
            parsed['taxa'] = min(fees)
        if len(cargos) > 1:
            parsed['cargo'] = 'Vários cargos'
        elif len(cargos) == 1:
            parsed['cargo'] = cargos[0]

        # 2. PDF extraction for true vacancies and salaries
        pdf_url = parsed.get('link_edital')
        if pdf_url and client is not None:
            try:
                resp = client.get(pdf_url, headers={'Referer': candidate.detail_url})
                if resp.content[:4] == b'%PDF':
                    reader = PdfReader(BytesIO(resp.content))
                    vagas_found = []
                    salaries_found = []
                    for p in reader.pages[:15]:
                        txt = p.extract_text() or ''
                        for line in txt.splitlines():
                            # Skip benefit rows like auxílio-alimentação
                            if any(b in line.lower() for b in ['alimenta', 'refei', 'transporte', 'auxílio', 'auxilio', 'benefício', 'beneficio']):
                                continue
                            # Match row with 01+CR or \d+CR
                            cr_matches = re.findall(r'\b(\d{1,3})\s*\+\s*CR\b', line, re.I)
                            if cr_matches:
                                vagas_found.extend(int(v) for v in cr_matches)
                            # Match salaries like 3.404,76 or R$ 3.404,76
                            sal_matches = re.findall(r'(?:R\$\s*)?(\d{1,3}(?:\.\d{3})+,\d{2})\b', line)
                            for s in sal_matches:
                                val = parse_money(s)
                                if val and val >= 1000:
                                    salaries_found.append(val)
                    if vagas_found:
                        parsed['vagas'] = sum(vagas_found)
                    if salaries_found:
                        parsed['salario_min'] = min(salaries_found)
                        parsed['salario_max'] = max(salaries_found)
            except Exception as exc:
                logger.debug('Objetiva PDF extraction failed for %s: %s', pdf_url, exc)

        if parsed.get('vagas') and 2020 <= parsed['vagas'] <= 2035:
            parsed['vagas'] = None

        parsed['resumo'] = build_summary(
            parsed.get('titulo') or '', parsed.get('modalidade'), parsed.get('status'),
            parsed.get('inscricao_inicio'), parsed.get('inscricao_fim'),
            cargo=parsed.get('cargo'), area=parsed.get('area'), vagas=parsed.get('vagas'),
            salario_min=parsed.get('salario_min'), salario_max=parsed.get('salario_max'),
        )
        return parsed


class LegatusConnector(GenericDedicatedBancaConnector):
    banca = 'Instituto Legatus'
    detail_patterns = (r'/concursos?/\d+/[^/?#]+/?$', r'/concurso\.aspx\?[^#]*\bid=\d+')
    allowed_hosts = ('www.legatus.org.br', 'legatus.org.br')

    def __init__(self, base_url: str = 'https://www.institutolegatus.com.br', list_url: str | None = None):
        canonical = 'https://www.legatus.org.br'
        super().__init__(base_url=canonical, list_url=list_url or canonical)

    def _parse_detail(self, candidate: CandidateItem, html: str, *, client) -> dict[str, Any] | None:
        parsed = super()._parse_detail(candidate, html, client=client)
        if not parsed:
            return None
        publications = (parsed.get('raw_data') or {}).get('publications') or []
        # Legatus exposes the current extension edital before the original
        # opening edital. Use that visible primary document; result/list files
        # remain in the publication collection.
        preferred = next(
            (
                publication.get('link') for publication in publications
                if publication.get('link')
                and re.search(r'\bedital\b', publication.get('title') or '', re.I)
                and re.search(r'prorroga[cç][aã]o', publication.get('title') or '', re.I)
            ),
            None,
        ) or next(
            (
                publication.get('link') for publication in publications
                if publication.get('link')
                and re.search(r'\bedital\b', publication.get('title') or '', re.I)
                and not re.search(r'resultado|rela[cç][aã]o|retifica[cç][aã]o', publication.get('title') or '', re.I)
                and not re.search(r'altera|cronograma', publication.get('title') or '', re.I)
            ),
            None,
        )
        if preferred:
            parsed['link_edital'] = preferred
        return parsed

class AvancaSPConnector(GenericDedicatedBancaConnector):
    banca = 'Avança SP'
    detail_patterns = (r'/concursos?/\d+/?$', r'/informacoes/\d+/?$', r'(?:[?&])id=\d+')
    allowed_hosts = ('avancasp.selecao.net.br', 'www.avancasp.selecao.net.br')

    def __init__(self, base_url: str = 'https://www.avancasp.org.br', list_url: str | None = None):
        canonical = 'https://avancasp.selecao.net.br'
        super().__init__(base_url=canonical, list_url=list_url or canonical)


class NossoRumoConnector(GenericDedicatedBancaConnector):
    banca = 'Nosso Rumo'
    mode = 'open'

    def __init__(self, base_url: str = 'https://nossorumo.org.br', list_url: str | None = None):
        canonical = 'https://nossorumo.org.br'
        super().__init__(base_url=canonical, list_url=list_url or canonical)

    def _fetch_candidates(self) -> list[CandidateItem]:
        candidates: list[CandidateItem] = []
        seen: set[str] = set()
        try:
            with self._http_client() as client:
                resp = client.get(self.list_url)
                self.run_data.http_status = resp.status_code
                if resp.status_code != 200:
                    return []
                soup = BeautifulSoup(resp.text, 'lxml')
                for item_card in soup.select('.list-grid-item'):
                    pub_btn = item_card.select_one('[data-publicacoes]')
                    if not pub_btn:
                        continue
                    proj_id = pub_btn.get('data-publicacoes')
                    if not proj_id or proj_id in seen:
                        continue
                    seen.add(proj_id)
                    raw_title = pub_btn.get('data-nome-certame') or ''
                    periodo = pub_btn.get('data-periodo-inscricao') or ''
                    card_text = item_card.get_text(' ', strip=True)
                    is_open = 'inscrições abertas' in card_text.lower() or 'inscreva-se' in card_text.lower()
                    if self.mode == 'open' and not is_open:
                        continue

                    inscricao_btn = item_card.select_one('[data-card-inscreva-se], a[href*="/Inscricao/ValidarCpf/"]')
                    inscricao_href = inscricao_btn.get('href') if inscricao_btn else None
                    inscricao_url = urljoin(self.base_url, inscricao_href) if inscricao_href else None

                    candidates.append(CandidateItem(
                        title_hint=clean(raw_title),
                        detail_url=f'{self.base_url}/Home/GetPublicacoes?idProjeto={proj_id}',
                        external_id=str(proj_id),
                        status_hint='Inscrições abertas' if is_open else 'Em andamento',
                        extra={
                            'proj_id': proj_id,
                            'periodo': periodo,
                            'inscricao_url': inscricao_url,
                            'is_open': is_open,
                        },
                    ))
                    if len(candidates) >= self.max_candidates:
                        break
        except Exception as exc:
            logger.warning('NossoRumo candidate fetch error: %s', exc)

        if not candidates:
            self.mark_empty_evidence('evaluated_closed', 'Nosso Rumo portal returned zero open certames', self.list_url)

        return candidates

    def _parse_detail(self, candidate: CandidateItem, html: str, *, client: httpx.Client) -> dict[str, Any] | None:
        proj_id = candidate.extra.get('proj_id') or candidate.external_id
        title = candidate.title_hint
        periodo = candidate.extra.get('periodo') or ''
        inicio, fim = parse_date_interval(periodo)

        headers = {'X-Requested-With': 'XMLHttpRequest', 'Referer': self.base_url}
        # 1. Fetch publications
        r_pub = client.get(f'{self.base_url}/Home/GetPublicacoes', params={'idProjeto': proj_id}, headers=headers)
        pub_data = r_pub.json() if r_pub.status_code == 200 else {}
        editais = pub_data.get('editais', [])
        comunicados = pub_data.get('comunicados', [])

        publications = []
        edital_url = None
        for ed in editais + comunicados:
            ed_nome = clean(ed.get('nome') or 'Documento')
            ed_arq = ed.get('arquivo')
            if ed_arq:
                doc_link = f'{self.base_url}/Arquivos/Projetos/{ed_arq}'
                p_type = normalize_publication_type(ed_nome)
                if p_type == 'edital' and not edital_url:
                    edital_url = doc_link
                publications.append({
                    'title': ed_nome,
                    'publication_type': p_type,
                    'link': doc_link,
                    'content_hash': build_publication_hash(ed_nome, None, doc_link, p_type),
                    'source': 'nosso_rumo',
                })

        # 2. Fetch Cargos
        import json as json_lib
        f_str = json_lib.dumps({'mobile': False, 'id': int(proj_id), 'mostrar_finalizado': True})
        r_cargos = client.get(f'{self.base_url}/Cargo/Pesquisar', params={'filtros': f_str}, headers=headers)
        cargos_data = r_cargos.json() if r_cargos.status_code == 200 else []

        cargo_names = []
        salaries = []
        vagas_list = []
        escolaridades = []
        for c in cargos_data:
            c_name = clean(c.get('cargo') or c.get('nome') or '')
            if c_name:
                cargo_names.append(c_name)
            sal_str = str(c.get('salario') or '')
            sal = parse_money(sal_str)
            if sal and sal >= 1000:
                salaries.append(sal)
            vg = c.get('vagas')
            if isinstance(vg, int) and vg > 0:
                vagas_list.append(vg)
            elif isinstance(vg, str) and vg.isdigit():
                vagas_list.append(int(vg))
            esc = clean(c.get('escolaridade') or '')
            if esc and esc not in escolaridades:
                escolaridades.append(esc)

        cargo = 'Vários cargos' if len(cargo_names) > 1 else (cargo_names[0] if cargo_names else None)
        vagas = sum(vagas_list) if vagas_list else None
        salario_min = min(salaries) if salaries else None
        salario_max = max(salaries) if salaries else None
        escolaridade = escolaridades[0] if len(escolaridades) == 1 else ('Múltiplas' if escolaridades else None)

        modalidade = 'Processo Seletivo' if 'processo seletivo' in title.lower() else 'Concurso Público'
        m_org = re.search(r'\b(?:Município|Prefeitura|Câmara|Secretaria|Conselho|Fundação|Empresa)\s+(?:de\s+)?[A-Za-zÀ-ÿ0-9 .\'’\-]{2,60}', title, re.I)
        orgao = clean(m_org.group(0)) if m_org else title
        orgao = re.sub(r'\s*[-–]\s*\d{1,4}/\d{4}.*$', '', orgao).strip(' ,-–')

        city, uf = extract_city_uf(orgao)
        if not city:
            city, uf_title = extract_city_uf(title)
            uf = uf or uf_title
        if not uf:
            m_uf = re.search(r'/([A-Z]{2})\b', title)
            if m_uf:
                uf = m_uf.group(1).upper()

        status = 'Inscrições abertas' if candidate.extra.get('is_open') else 'Em andamento'
        resumo = build_summary(title, modalidade, status, inicio, fim, cargo=cargo, vagas=vagas, salario_min=salario_min, salario_max=salario_max)

        raw_payload = {
            'proj_id': proj_id,
            'title_hint': title,
            'publications': publications,
            'cargos': cargos_data,
            'source_list_url': self.list_url,
        }

        return {
            'external_id': str(proj_id),
            'banca': self.banca,
            'orgao': orgao,
            'titulo': title,
            'modalidade': modalidade,
            'cargo': cargo,
            'area': None,
            'cidade': city,
            'uf': uf,
            'status': status,
            'vagas': vagas,
            'salario_min': salario_min,
            'salario_max': salario_max,
            'escolaridade': escolaridade,
            'taxa': None,
            'prova_data': None,
            'edital_numero': None,
            'edital_data': None,
            'inscricao_inicio': inicio,
            'inscricao_fim': fim,
            'link_pagina': f'{self.base_url}/#emandamento',
            'link_edital': edital_url,
            'link_inscricao': candidate.extra.get('inscricao_url'),
            'resumo': resumo,
            'raw_data': raw_payload,
            'edital_pdf_text_hash': None,
            'edital_pdf_pages': None,
            'edital_pdf_excerpt': None,
            'pdf_extracted_at': None,
            'content_hash': build_hash(raw_payload),
            'fetched_at': datetime.now(UTC),
        }


class ExameConsultoresConnector(GenericDedicatedBancaConnector):
    """Connector for the Exame Auditores & Consultores ProSeleta portal.

    ProSeleta keeps the public list at ``/index/1/`` and links each card to
    ``/informacoes/<numeric-key>/``.  The same page mixes public contests,
    internal school selections and occupational certification processes, so
    discovery is deliberately based on the card's visible semantic identity
    rather than on a fixed set of keys.
    """

    banca = 'EXAME Auditores'
    detail_patterns = (r'/informacoes/\d+/?$',)
    allowed_hosts = (
        'concursos.exameconsultores.com.br',
        'www.exameconsultores.com.br',
        'exameconsultores.com.br',
    )
    candidate_excluded_terms = GenericDedicatedBancaConnector.candidate_excluded_terms + (
        'certificação ocupacional', 'certificacao ocupacional',
        'processo seletivo interno',
    )

    def __init__(
        self,
        base_url: str = 'https://concursos.exameconsultores.com.br',
        list_url: str | None = None,
    ):
        canonical = 'https://concursos.exameconsultores.com.br'
        super().__init__(
            base_url=canonical,
            list_url=list_url or canonical + '/index/1/',
        )

    @staticmethod
    def _card_place(value: str | None) -> tuple[str | None, str | None]:
        """Extract a municipality from ProSeleta's P.M./C.M. card labels."""
        text = clean(value or '') or ''
        city, uf = extract_city_uf(text)
        if city or uf:
            return city, uf
        match = re.search(
            r'\b(?:P\.?\s*M\.?|PREFEITURA(?:\s+MUNICIPAL)?|'
            r'C\.?\s*M\.?|C[ÂA]MARA(?:\s+MUNICIPAL)?)\s*(?:DE|DO|DA)?\s*'
            r'([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ .\'’\-]{2,90}?)(?:\s*\(([A-Z]{2})\))?'
            r'\s*(?:[-–|]|CONCURSO|PROCESSO|$)',
            text,
            flags=re.IGNORECASE,
        )
        if not match:
            return None, None
        city = clean(match.group(1))
        return city.strip(' -–') if city else None, match.group(2)

    def _fetch_candidates(self) -> list[CandidateItem]:
        html = self._fetch_html(self.list_url)
        soup = BeautifulSoup(html, 'lxml')
        candidates: list[CandidateItem] = []
        seen: set[str] = set()
        for anchor in soup.select('a[href]'):
            url = normalize_url(self.list_url, anchor.get('href'))
            if not url or url in seen or not self._is_detail_url(url):
                continue
            # ProSeleta uses ``ul.lista > li.item`` cards.  Do not use the
            # generic ancestor walk here: its next ancestor is the whole list
            # and therefore contains unrelated "processo interno" and
            # "certificação" labels, poisoning every candidate's context.
            card = anchor.find_parent('li', class_=lambda values: values and 'item' in values)
            context = clean(card.get_text(' ', strip=True) if card else anchor.get_text(' ', strip=True)) or ''
            if not self._has_candidate_identity(context, url):
                continue
            seen.add(url)
            candidates.append(CandidateItem(
                title_hint=context[:500],
                detail_url=url,
                # ``/index/1/`` is the portal's "Em andamento" section.  A
                # card may omit the explicit badge, so retain that section
                # status as a conservative fallback.
                status_hint=self._infer_status(context) or 'Em andamento',
                external_id=extract_external_id(url, [r'/informacoes/(\d+)']),
            ))
            if len(candidates) >= self.max_candidates:
                break
        return candidates

    def _extract_title(self, lines: list[str], hint: str | None) -> str:
        for value in list(lines[:100]) + ([hint] if hint else []):
            text = clean(value)
            if not text or len(text) < 10:
                continue
            if re.search(
                r'\b(?:P\.?\s*M\.?|PREFEITURA|C\.?\s*M\.?|C[ÂA]MARA)\b',
                text,
                flags=re.IGNORECASE,
            ) and re.search(r'\b(?:concurso|processo seletivo|edital)\b', text, flags=re.IGNORECASE):
                return text
        return super()._extract_title(lines, hint)

    def _extract_orgao(self, title: str, lines: list[str], hint: str | None) -> str | None:
        for value in [title, hint] + lines[:100]:
            text = clean(value)
            if not text:
                continue
            match = re.search(
                r'((?:P\.?\s*M\.?|PREFEITURA(?:\s+MUNICIPAL)?|'
                r'C\.?\s*M\.?|C[ÂA]MARA(?:\s+MUNICIPAL)?)\s*'
                r'(?:DE|DO|DA)?\s*[A-Za-zÀ-ÿ0-9 .\'’\-]{3,100})',
                text,
                flags=re.IGNORECASE,
            )
            if match:
                orgao = clean(match.group(1))
                if orgao:
                    return re.sub(
                        r'\s+(?:Concurso|Processo|Edital|Inscri[cç][oõ]es)\b.*$',
                        '', orgao, flags=re.IGNORECASE,
                    ).strip(' -–')
        return super()._extract_orgao(title, lines, hint)

    def _parse_detail(self, candidate: CandidateItem, html: str, *, client) -> dict[str, Any] | None:
        semantic_text = clean(BeautifulSoup(html, 'lxml').get_text(' ', strip=True)) or ''
        semantic_source = f'{candidate.title_hint or ""} {semantic_text}'.lower()
        if re.search(
            r'certifica[cç][aã]o\s+ocupacional|processo\s+seletivo\s+interno',
            semantic_source,
            flags=re.IGNORECASE,
        ):
            return None
        parsed = super()._parse_detail(candidate, html, client=client)
        if not parsed:
            return None

        # Discover primary opening edital rather than incidental retifications
        soup = BeautifulSoup(html, 'lxml')
        pubs = parse_publications_from_dom(soup, candidate.detail_url, source=self.banca.lower())
        if pubs:
            parsed.setdefault('raw_data', {})['publications'] = pubs
            primary_edital = None
            for p in pubs:
                t = p['title'].upper()
                if re.search(r'\bEDITAL\b', t) and not re.search(r'RETIFICA|RERRATIFICA|CONVOCA|RESULTADO|GABARITO|PORTARIA', t):
                    primary_edital = p['link']
                    break
            if primary_edital:
                parsed['link_edital'] = primary_edital

        card_city, card_uf = self._card_place(candidate.title_hint)
        if card_city:
            parsed['cidade'] = card_city
        if card_uf and not parsed.get('uf'):
            parsed['uf'] = card_uf
        official_status = self._extract_detail_status(
            [clean(line) or '' for line in BeautifulSoup(html, 'lxml').get_text('\n', strip=True).split('\n')]
        )
        if official_status:
            parsed['status'] = official_status

        # Extract salaries and fees from the PDF ANEXO I table
        pdf_url = parsed.get('link_edital')
        if pdf_url and client is not None:
            try:
                resp = client.get(pdf_url, headers={'Referer': candidate.detail_url})
                if resp.content[:4] == b'%PDF':
                    reader = PdfReader(BytesIO(resp.content))
                    salaries = []
                    fees = []
                    for p in reader.pages:
                        txt = p.extract_text() or ''
                        if any(k in txt for k in ['ANEXO I', 'Vencimento', 'CARGOS', 'VENCIMENTO', 'Quadro de Vagas']):
                            for line in txt.splitlines():
                                if any(b in line.lower() for b in ['alimenta', 'refei', 'transporte', 'auxílio', 'auxilio', 'lei nº', 'lei n', 'orçament']):
                                    continue
                                m_money = re.findall(r'(?:R\$\s*)?(\d{1,3}(?:\.\d{3})*,\d{2})\b', line)
                                for m in m_money:
                                    val = parse_money(m)
                                    if val and 1000 <= val <= 50000:
                                        salaries.append(val)
                                    elif val and 30 <= val <= 400:
                                        fees.append(val)
                    if salaries:
                        parsed['salario_min'] = min(salaries)
                        parsed['salario_max'] = max(salaries)
                    if fees and not parsed.get('taxa'):
                        parsed['taxa'] = min(fees)
            except Exception as exc:
                logger.debug('Exame PDF salary extraction failed for %s: %s', pdf_url, exc)

        parsed['resumo'] = build_summary(
            parsed.get('titulo') or '', parsed.get('modalidade'), parsed.get('status'),
            parsed.get('inscricao_inicio'), parsed.get('inscricao_fim'),
            cargo=parsed.get('cargo'), area=parsed.get('area'), vagas=parsed.get('vagas'),
            salario_min=parsed.get('salario_min'), salario_max=parsed.get('salario_max'),
        )
        return parsed


class ADMTECConnector(GenericDedicatedBancaConnector):
    """Connector for ADM&TEC's public concours publication pages.

    ADM&TEC's homepage is a small JS/browser page, but its public cards link
    to stable two-segment publication URLs.  The detail page contains the
    authoritative period, cargo/fee blocks, edital PDF and publication rows.
    """

    banca = 'ADM&TEC'
    detail_patterns = (r'/concursos/publicacoes/[^/?#]+/[^/?#]+/?$',)
    allowed_hosts = ('admtec.org.br', 'www.admtec.org.br')
    mode = 'all'
    browser_strategy = 'always'
    max_candidates = 8

    def __init__(
        self,
        base_url: str = 'https://www.admtec.org.br',
        list_url: str | None = None,
    ):
        canonical = 'https://www.admtec.org.br'
        super().__init__(
            base_url=canonical,
            list_url=list_url or canonical,
        )

    @staticmethod
    def _place(value: str | None) -> tuple[str | None, str | None]:
        text = clean(value or '') or ''
        city, uf = extract_city_uf(text)
        if city or uf:
            return city, uf
        match = re.search(
            r'\b(?:PREFEITURA(?:\s+MUNICIPAL)?|C[ÂA]MARA(?:\s+MUNICIPAL)?|'
            r'MUNIC[IÍ]PIO)\s+(?:DE|DO|DA)?\s*'
            r'([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ .\'’\-]{2,90}?)\s*'
            r'(?:\(([A-Z]{2})\)|[-/]\s*([A-Z]{2})|$)',
            text,
            flags=re.IGNORECASE,
        )
        if not match:
            return None, None
        city = clean(match.group(1))
        return (city.strip(' -–').title() if city else None), (match.group(2) or match.group(3))

    def _fetch_candidates(self) -> list[CandidateItem]:
        html = self._fetch_html(self.list_url)
        soup = BeautifulSoup(html, 'lxml')
        candidates: list[CandidateItem] = []
        seen: set[str] = set()
        for anchor in soup.select('a[href]'):
            url = normalize_url(self.list_url, anchor.get('href'))
            if not url or url in seen or not self._is_detail_url(url):
                continue
            context = self._candidate_context_text(anchor) or clean(anchor.get_text(' ', strip=True)) or ''
            if not self._has_candidate_identity(context, url):
                continue
            if self._candidate_is_excluded(context):
                continue
            seen.add(url)
            candidates.append(CandidateItem(
                title_hint=context[:500],
                detail_url=url,
                status_hint=self._infer_status(context),
                external_id=extract_external_id(url, [r'/concursos/publicacoes/([^/?#]+/[^/?#]+)']),
            ))
            if len(candidates) >= self.max_candidates:
                break
        return candidates

    @staticmethod
    def _normalize_document_url(url: str | None) -> str | None:
        """Make known document wrappers downloadable and deterministic."""
        if not url:
            return None
        parts = urlsplit(url)
        if 'dropbox.com' not in parts.netloc.lower():
            return url
        query = dict(parse_qsl(parts.query, keep_blank_values=True))
        query['dl'] = '1'
        return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))

    def _clean_publications(self, publications: list[dict[str, Any]], client: Any) -> list[dict[str, Any]]:
        cleaned: list[dict[str, Any]] = []
        seen: set[str] = set()
        for publication in publications:
            link = self._normalize_document_url(publication.get('link'))
            if link:
                key = link.rstrip('/').lower()
                if key in seen:
                    continue
                seen.add(key)
            publication = dict(publication)
            publication['link'] = link
            publication['content_hash'] = build_publication_hash(
                publication.get('title'), publication.get('publication_date'),
                link, publication.get('publication_type'),
            )
            cleaned.append(publication)
        return cleaned[:80]

    def _extract_title(self, lines: list[str], hint: str | None) -> str:
        for value in list(lines[:80]) + ([hint] if hint else []):
            text = clean(value)
            if not text or len(text) < 10:
                continue
            if re.search(
                r'\b(?:PREFEITURA|C[ÂA]MARA|MUNIC[IÍ]PIO|SECRETARIA|CONS[ÓO]RCIO)\b',
                text, flags=re.IGNORECASE,
            ) and not re.search(r'\b(?:Instituto ADM|Sobre|Contato|Saiba)\b', text, flags=re.IGNORECASE):
                return text.strip(' -–')
        return super()._extract_title(lines, hint)

    def _extract_orgao(self, title: str, lines: list[str], hint: str | None) -> str | None:
        for value in [title, hint] + lines[:80]:
            text = clean(value)
            if not text:
                continue
            match = re.search(
                r'((?:PREFEITURA(?:\s+MUNICIPAL)?|C[ÂA]MARA(?:\s+MUNICIPAL)?|'
                r'MUNIC[IÍ]PIO|SECRETARIA|CONS[ÓO]RCIO)[^\n]{3,120})',
                text, flags=re.IGNORECASE,
            )
            if match:
                orgao = clean(match.group(1))
                if orgao:
                    return re.sub(
                        r'\s+(?:Concurso|Processo|Edital|Per[ií]odo|Inscri[cç][oõ]es)\b.*$',
                        '', orgao, flags=re.IGNORECASE,
                    ).strip(' -–')
        return super()._extract_orgao(title, lines, hint)

    def _parse_detail(self, candidate: CandidateItem, html: str, *, client) -> dict[str, Any] | None:
        # Normalize links before the generic parser selects the edital and
        # publications, especially Dropbox's dl=0 viewer URLs.
        soup = BeautifulSoup(html, 'lxml')
        for anchor in soup.select('a[href]'):
            normalized = self._normalize_document_url(normalize_url(candidate.detail_url, anchor.get('href')))
            if normalized:
                anchor['href'] = normalized
        html = str(soup)
        parsed = super()._parse_detail(candidate, html, client=client)
        if not parsed:
            return None
        card_city, card_uf = self._place(candidate.title_hint)
        title_city, title_uf = self._place(parsed.get('titulo'))
        if card_city:
            parsed['cidade'] = card_city
        elif not parsed.get('cidade'):
            parsed['cidade'] = title_city
        if card_uf:
            parsed['uf'] = card_uf
        elif not parsed.get('uf'):
            parsed['uf'] = title_uf

        # The portal represents fees and publication rows as stacked blocks,
        # not consistently as <table>; rerun conservative line extraction so
        # a redesign of the cards does not drop these fields.
        soup = BeautifulSoup(html, 'lxml')
        lines = [clean(line) for line in soup.get_text('\n', strip=True).split('\n')]
        lines = [line for line in lines if line]
        text = '\n'.join(lines)
        if parsed.get('taxa') is None:
            parsed['taxa'] = self._extract_taxa(text)
        if parsed.get('vagas') is None:
            parsed['vagas'] = self._extract_vagas(text)
        publications = parse_publications_from_dom(soup, candidate.detail_url, source=self.banca.lower())
        if not publications:
            publications = parse_publications_from_lines(lines, source=self.banca.lower())
        publications = self._clean_publications(publications, client)
        if publications:
            parsed.setdefault('raw_data', {})['publications'] = publications

        # Keep failed document links as publication evidence, but clear the
        # normalized edital field so consumers never mistake an HTML/404
        # response for a successfully extracted edital PDF.
        pdf_payload = parsed.get('raw_data', {}).get('pdf') or {}
        if parsed.get('link_edital') and pdf_payload.get('ok') is False:
            parsed['link_edital'] = None
            parsed['edital_pdf_text_hash'] = None
            parsed['edital_pdf_pages'] = None
            parsed['edital_pdf_excerpt'] = None
        parsed['resumo'] = build_summary(
            parsed.get('titulo') or '', parsed.get('modalidade'), parsed.get('status'),
            parsed.get('inscricao_inicio'), parsed.get('inscricao_fim'),
            cargo=parsed.get('cargo'), area=parsed.get('area'), vagas=parsed.get('vagas'),
            salario_min=parsed.get('salario_min'), salario_max=parsed.get('salario_max'),
        )
        return parsed


# Friendly aliases used by integrations that name the organizer directly.
ExameConnector = ExameConsultoresConnector
ADMTECOpenConnector = ADMTECConnector
