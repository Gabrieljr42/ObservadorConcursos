from __future__ import annotations

import json
import logging
import os
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

# Ensure backend root is in sys.path when invoked as ``python scripts/...``.
BACKEND_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND_ROOT))

from app.audit_validation import (  # noqa: E402
    AUDIT_FIELDS,
    build_field_audit,
    has_value,
    normalize_for_audit,
)
from app.connectors.common import (  # noqa: E402
    HEADERS,
    clean,
    extract_city_uf,
    first_date,
    parse_date_interval,
    parse_money,
)
from app.connectors.registry import MASTER_SOURCES, get_connector  # noqa: E402
from app.publications import (  # noqa: E402
    is_publication_anchor,
    is_valid_publication_title,
    publication_title_from_anchor,
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger('live_audit_99')

EVIDENCE_PATH = Path(os.environ.get('AUDIT_EVIDENCE_PATH', BACKEND_ROOT / 'live_evidence.json'))


def serialize_val(val: Any) -> Any:
    if isinstance(val, datetime):
        return val.isoformat()
    if isinstance(val, Decimal):
        return float(val)
    if isinstance(val, dict):
        return {k: serialize_val(v) for k, v in val.items()}
    if isinstance(val, list):
        return [serialize_val(x) for x in val]
    return val


def load_independent_evidence() -> dict[str, dict[str, Any]]:
    """Load human/independently observed evidence, never crawler output."""
    if not EVIDENCE_PATH.exists():
        return {}
    with EVIDENCE_PATH.open('r', encoding='utf-8') as handle:
        data = json.load(handle)
    observations = data.get('observations', {}) if isinstance(data, dict) else {}
    return observations if isinstance(observations, dict) else {}


def _same_host(left: str, right: str) -> bool:
    left_host = urlparse(left).netloc.casefold().removeprefix('www.')
    right_host = urlparse(right).netloc.casefold().removeprefix('www.')
    return bool(left_host and left_host == right_host)


def _canonical_url(url: str) -> str:
    parsed = urlparse(url)
    path = parsed.path.rstrip('/') or '/'
    return f'{parsed.scheme.casefold()}://{parsed.netloc.casefold()}{path}' + (f'?{parsed.query}' if parsed.query else '')


def _official_text(soup: BeautifulSoup) -> str:
    # Remove global chrome before independent extraction. This is deliberately
    # separate from connector parsing so the audit does not reuse crawler data.
    clean_soup = BeautifulSoup(str(soup), 'lxml')
    for tag in clean_soup(['script', 'style', 'noscript', 'svg', 'nav', 'footer', 'header', 'aside']):
        tag.decompose()
    return '\n'.join(line for line in (clean(x) for x in clean_soup.get_text('\n', strip=True)) if line)


def _official_publications(soup: BeautifulSoup, page_url: str) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    seen: set[str] = set()
    publication_tokens = (
        'edital', 'retifica', 'errata', 'gabarito', 'resultado', 'convoca',
        'comunicado', 'recurso', 'homologa', 'lista', 'inscrito', 'anexo',
        'portaria', 'decreto', 'aviso', 'cronograma', 'parecer', 'resposta',
        'devolução', 'devolucao',
    )
    for anchor in soup.select('a[href]'):
        if not is_publication_anchor(anchor):
            continue
        title = publication_title_from_anchor(anchor)
        href = anchor.get('href')
        if not title or not href or not is_valid_publication_title(title):
            continue
        link = urljoin(page_url, href)
        context = title
        for parent in anchor.parents:
            if getattr(parent, 'name', None) in {'li', 'tr'}:
                context = clean(parent.get_text(' ', strip=True)) or title
                break
        haystack = f'{title} {context or ""} {link}'.casefold()
        if not any(token in haystack for token in publication_tokens) and not any(
            suffix in link.casefold() for suffix in ('.pdf', '.doc', '.docx', 'download', 'arquivo=')
        ):
            continue
        key = _canonical_url(link)
        if key in seen:
            continue
        seen.add(key)
        results.append({'title': title, 'link': link})
    return results[:80]


def _first_heading(soup: BeautifulSoup) -> str | None:
    generic_headings = (
        'informações do concurso', 'informacoes do concurso', 'detalhes do concurso',
        'detalhes do processo', 'detalhes do edital', 'concursos em andamento',
        'concursos abertos', 'concursos', 'processos seletivos', 'editais',
        'arquivos', 'documentos', 'home', 'início', 'inicio', 'área do candidato',
        'area do candidato', 'portal de seleção', 'portal de selecao', 'ver edital',
        'encontre seu próximo caminho', 'encontre seu proximo caminho',
    )
    identity_terms = (
        'concurso', 'processo seletivo', 'edital', 'prefeitura', 'câmara', 'camara',
        'tribunal', 'universidade', 'secretaria', 'órgão', 'orgao', 'autarquia',
    )
    for heading in soup.select('h1, h2'):
        value = clean(heading.get_text(' ', strip=True)) or ''
        lowered = value.casefold()
        if value and len(value) >= 8 and not any(term in lowered for term in (
            'aviso de privacidade', 'aviso de cookies', 'copyright', 'versão', 'versao', 'version',
            'login', *generic_headings,
        )) and any(term in lowered for term in identity_terms):
            return value
    # A document title is useful only when it identifies a certame.  Brand or
    # navigation titles are not independent contest values and must stay UNKNOWN.
    title = soup.select_one('title')
    value = clean(title.get_text(' ', strip=True)) or '' if title else ''
    lowered = value.casefold()
    if value and len(value) >= 8 and any(term in lowered for term in (
        'concurso', 'processo seletivo', 'edital', 'prefeitura', 'câmara', 'camara',
        'tribunal', 'universidade', 'secretaria',
    )) and not any(term in lowered for term in (
        'aviso de privacidade', 'aviso de cookies', 'copyright', 'versão', 'versao', 'version',
        'login', *generic_headings,
    )):
        return value
    return None


def _extract_official_expected(soup: BeautifulSoup, page_url: str) -> tuple[dict[str, Any], dict[str, Any]]:
    text = _official_text(soup)
    title = _first_heading(soup)
    expected: dict[str, Any] = {}
    if title:
        expected['titulo'] = title

    orgao_match = re.search(
        r'\b((?:PREFEITURA|C[ÂA]MARA|SECRETARIA|MINIST[ÉE]RIO|TRIBUNAL|CONSELHO|UNIVERSIDADE|FUNDAÇÃO|FUNDACAO|AUTARQUIA|EMPRESA)[^\n.;]{3,140})',
        text,
        flags=re.IGNORECASE,
    )
    if orgao_match:
        expected['orgao'] = clean(orgao_match.group(1))

    haystack = f'{title or ""}\n{text[:8000]}'.casefold()
    if 'concurso público' in haystack or 'concurso publico' in haystack:
        expected['modalidade'] = 'Concurso Público'
    elif 'processo seletivo simplificado' in haystack:
        expected['modalidade'] = 'Processo Seletivo Simplificado'
    elif 'processo seletivo' in haystack or 'seleção pública' in haystack or 'selecao publica' in haystack:
        expected['modalidade'] = 'Processo Seletivo'

    status_match = re.search(r'\b(inscrições? abertas?|em andamento|inscrições? encerradas?|encerrado|finalizado)\b', haystack, re.I)
    if status_match:
        expected['status'] = clean(status_match.group(1))

    cidade, uf = extract_city_uf(f'{title or ""}\n{text[:8000]}')
    if cidade:
        cidade = re.sub(
            r'^(?:concurso|processo\s+seletivo|sele[cç][aã]o)(?:\s+p[úu]blic[oa])?\s+',
            '',
            cidade,
            flags=re.IGNORECASE,
        ).strip()
        cidade = re.sub(
            r'^(?:estância|estancia)\s+turística\s+de\s+',
            '',
            cidade,
            flags=re.IGNORECASE,
        ).strip()
    if cidade:
        expected['cidade'] = cidade
    if uf:
        expected['uf'] = uf

    vacancies = re.findall(
        r'(?:(?:total|oferece|oferta|preenchimento)[^\n]{0,60})?(\d{1,5})\s*(?:vagas?|vagas? imediatas?)\b',
        text,
        flags=re.IGNORECASE,
    )
    vacancy_values = [int(value) for value in vacancies if not 1900 <= int(value) <= 2100]
    if vacancy_values:
        expected['vagas'] = max(vacancy_values)

    money_by_context: dict[str, list[Decimal]] = {'salary': [], 'tax': []}
    for match in re.finditer(r'R\$\s*[\d.]+(?:,\d{2})?', text, re.I):
        value = parse_money(match.group(0))
        if value is None:
            continue
        context = text[max(0, match.start() - 100):match.end() + 100].casefold()
        if any(token in context for token in ('taxa de inscrição', 'taxa de inscricao', 'valor da taxa')):
            money_by_context['tax'].append(value)
        elif any(token in context for token in ('remuneração', 'remuneracao', 'vencimento', 'salário', 'salario')) and value >= 1000:
            money_by_context['salary'].append(value)
    if money_by_context['salary']:
        expected['salario_min'] = float(min(money_by_context['salary']))
        expected['salario_max'] = float(max(money_by_context['salary']))
    if money_by_context['tax']:
        expected['taxa'] = float(money_by_context['tax'][0])

    registration = re.search(
        r'inscri(?:ç|c)[õo]es?[^\n]{0,180}?\b\d{1,2}/\d{1,2}/\d{2,4}\b[^\n]{0,80}?\b\d{1,2}/\d{1,2}/\d{2,4}\b',
        text,
        flags=re.IGNORECASE,
    )
    if registration:
        start, end = parse_date_interval(registration.group(0))
        if start:
            expected['inscricao_inicio'] = start
        if end:
            expected['inscricao_fim'] = end

    edital_number = re.search(r'\bedital\s*(?:n[º°o.]?\s*)?(\d{1,4}(?:/\d{4})?)', text, re.I)
    if edital_number:
        expected['edital_numero'] = edital_number.group(1)

    prova = re.search(r'(?:prova|avaliação|avaliacao)[^\n]{0,120}?(\d{1,2}/\d{1,2}/\d{2,4})', text, re.I)
    if prova:
        value = first_date(prova.group(1))
        if value:
            expected['prova_data'] = value

    publications = _official_publications(soup, page_url)
    # Do not treat the requested detail URL as an independent observation: it
    # may have been supplied by the crawler.  Only record a page link when the
    # official document exposes it independently as canonical metadata.
    canonical = soup.select_one('link[rel~="canonical"][href]')
    canonical_url = canonical.get('href') if canonical else None
    if not canonical_url:
        og_url = soup.select_one('meta[property="og:url"][content], meta[name="twitter:url"][content]')
        canonical_url = og_url.get('content') if og_url else None
    if canonical_url:
        canonical_candidate = urljoin(page_url, canonical_url)
        canonical_parts = urlparse(canonical_candidate)
        # Reject CMS defaults such as ``http://localhost/...`` and a social
        # preview URL pointing at the portal home. Neither identifies this
        # certame independently.
        if (
            canonical_parts.netloc.casefold() not in {'localhost', '127.0.0.1', '0.0.0.0'}
            and canonical_parts.path.rstrip('/')
        ):
            expected['link_pagina'] = canonical_candidate
    edital_publications = [p for p in publications if 'edital' in p['title'].casefold() and p.get('link')]
    edital_link = next(
        (
            p['link'] for p in edital_publications
            if re.search(r'\bedital\s+de\s+abertura\b', p['title'], re.I)
            and not re.search(
                r'\b(?:aditivo|retifica|errata|rerratifica|resultado|gabarito|convoca|portaria|'
                r'cronograma|homologa|deferimento|isen[cç][aã]o|prorroga|altera|anexo)\b',
                p['title'],
                re.I,
            )
        ),
        None,
    )
    if not edital_link:
        edital_link = next(
            (
                p['link'] for p in edital_publications
                if not re.search(
                    r'\b(?:aditivo|retifica|errata|rerratifica|resultado|gabarito|convoca|portaria|'
                    r'cronograma|homologa|deferimento|isen[cç][aã]o|prorroga|altera|anexo)\b',
                    p['title'],
                    re.I,
                )
            ),
            None,
        )
    if not edital_link and edital_publications:
        edital_link = edital_publications[0]['link']
    if edital_link:
        expected['link_edital'] = edital_link
    inscription_candidates: list[tuple[int, str]] = []
    for anchor in soup.select('a[href]'):
        anchor_title = clean(anchor.get_text(' ', strip=True)) or ''
        href = anchor.get('href') or ''
        lowered = f'{anchor_title} {href}'.casefold()
        if not any(term in lowered for term in ('inscrição', 'inscricao', 'inscreva-se', 'inscreva', 'candidato')):
            continue
        resolved_href = urljoin(page_url, href)
        resolved_path = urlparse(resolved_href).path.casefold().rstrip('/')
        # Publication PDFs and candidate dashboards are not registration
        # endpoints.  A document titled "Resultado ... de Inscrição" must not
        # become the independent value for ``link_inscricao``.
        if (
            resolved_path.endswith(('.pdf', '.doc', '.docx'))
            or any(token in resolved_path for token in ('/arquivos/', '/download', '/painel'))
            or href.strip().startswith(('#', 'javascript:', 'mailto:'))
        ):
            continue
        if href.strip().endswith(('cod=', 'codigo=')):
            continue
        if resolved_path == '/candidato':
            continue
        priority = 0 if any(term in lowered for term in ('inscreva', 'inscrição', 'inscricao')) else 1
        inscription_candidates.append((priority, resolved_href))
    if inscription_candidates:
        expected['link_inscricao'] = min(inscription_candidates, key=lambda value: value[0])[1]

    publication_observation = {
        'observed': True,
        'source_url': page_url,
        'publications': publications,
        'expected_titles': [p['title'] for p in publications],
        'expected_links': [p['link'] for p in publications],
    }
    return expected, publication_observation


def collect_independent_evidence(defn, item: dict[str, Any] | None) -> dict[str, Any]:
    """Observe official list/detail pages with a parser independent of connectors."""
    evidence: dict[str, Any] = {
        'independent': False,
        'method': 'official_html_observer',
        'observed_at': datetime.now(timezone.utc).isoformat(),
        'expected': {},
        'known_null_fields': [],
        'evidence_urls': [defn.list_urls[0] if defn.list_urls else defn.base_url],
        'publication_observation': {'observed': False, 'expected_titles': [], 'expected_links': []},
        'visible_valid_items': None,
        'observation_error': None,
    }
    list_url = defn.list_urls[0] if defn.list_urls else defn.base_url
    detail_url = item.get('link_pagina') if item else None
    try:
        with httpx.Client(timeout=30.0, follow_redirects=True, headers=HEADERS, verify=False) as client:
            list_response = client.get(list_url)
            list_response.raise_for_status()
            list_soup = BeautifulSoup(list_response.text, 'lxml')
            list_links: set[str] = set()
            list_anchors = list_soup.select('a[href]')
            if defn.source_type == 'ibade_open':
                list_anchors = list_soup.select('#andamento a[href*="/edital/ver/"]')
            elif defn.source_type == 'ufu_selection':
                # UFU exposes live rows as clickable cards with an onclick
                # URL, not as anchors. Count those cards independently.
                current_year = str(datetime.now(timezone.utc).year)
                for card in list_soup.select('.thumbnail.edital_op[onclick]'):
                    card_text = clean(card.get_text(' ', strip=True)) or ''
                    if current_year not in card_text or not re.search(
                        r'inscri[cç][õo]es\s+at[eé]\b', card_text, re.I
                    ):
                        continue
                    if re.search(
                        r'declara[cç][aã]o\s+rsc|aplica[cç][aã]o\s+de\s+provas|'
                        r'resid[eê]ncia|certifica[cç][aã]o|outros\s+dirps',
                        card_text,
                        re.I,
                    ):
                        continue
                    match = re.search(
                        r"window\.location\.href=['\"]([^'\"]+)",
                        card.get('onclick') or '',
                        re.I,
                    )
                    if match:
                        list_links.add(_canonical_url(urljoin(str(list_response.url), match.group(1))))
                list_anchors = []
            elif defn.source_type == 'legalle_open':
                # Historical cards follow the live section; this source only
                # monitors the official links explicitly labelled open.
                list_anchors = [
                    anchor for anchor in list_anchors
                    if (clean(anchor.get_text(' ', strip=True)) or '').casefold() == 'inscrições abertas'
                ]
            elif defn.source_type == 'fafipa_open':
                live_anchors = []
                for anchor in list_anchors:
                    context_parts = []
                    for parent in anchor.parents:
                        if getattr(parent, 'name', None) not in {'li', 'article', 'div', 'section', 'tr'}:
                            continue
                        context = clean(parent.get_text(' ', strip=True)) or ''
                        if len(context) <= 1200:
                            context_parts.append(context)
                    if any(re.search(r'inscri[cç][õo]es\s+abertas?', value, re.I) for value in context_parts):
                        live_anchors.append(anchor)
                list_anchors = live_anchors
            elif defn.source_type == 'fenix_open':
                list_anchors = [
                    anchor for anchor in list_anchors
                    if (clean(anchor.get_text(' ', strip=True)) or '').casefold() == 'inscrições abertas'
                ]
            elif defn.source_type == 'institutomais_open':
                live_anchors = []
                for anchor in list_anchors:
                    label = clean(anchor.get_text(' ', strip=True)) or ''
                    contexts = []
                    for parent in anchor.parents:
                        if getattr(parent, 'name', None) not in {'li', 'article', 'div', 'section', 'tr'}:
                            continue
                        context = clean(parent.get_text(' ', strip=True)) or ''
                        if len(label) + 10 <= len(context) <= 1200:
                            contexts.append(context)
                    compact_context = min(contexts, key=len) if contexts else label
                    if re.search(r'resid[eê]ncia\s+m[eé]dica', compact_context, re.I):
                        continue
                    live_anchors.append(anchor)
                list_anchors = live_anchors
            elif defn.source_type == 'consulpam_open':
                list_anchors = [
                    anchor for anchor in list_anchors
                    if 'acao=ver&id=' in (anchor.get('href') or '')
                    and (
                        (row := anchor.find_parent('tr')) is not None
                        and (marker := row.select_one('img[alt]')) is not None
                        and re.search(r'abert|andament', clean(marker.get('alt')) or '', re.I)
                    )
                ]
            elif defn.source_type == 'cesgranrio_open':
                list_anchors = []
                for heading in list_soup.select('h3.t-entry-title'):
                    anchor = heading.select_one('a[href]')
                    card = heading.find_parent(class_='t-entry')
                    card_text = clean(card.get_text(' ', strip=True)) if card else ''
                    if not anchor or not card_text:
                        continue
                    if re.search(r'conclu[ií]d|vestibular', card_text, re.I):
                        continue
                    if re.search(r'em andamento', card_text, re.I):
                        list_anchors.append(anchor)
            elif defn.source_type == 'imeso_open':
                list_anchors = [
                    anchor for anchor in list_anchors
                    if '/edital/ver/' in (anchor.get('href') or '')
                    and re.search(
                        r'inscri[cç][oõ]es?\s+abert',
                        clean(anchor.get_text(' ', strip=True)) or '',
                        re.IGNORECASE,
                    )
                ]
            elif defn.source_type == 'funcern_selection':
                # FUNCERN's official page mixes two live contests with
                # historical/finalized cards.  Count only cards explicitly
                # marked as open, independently of the connector's output.
                live_anchors = []
                for anchor in list_anchors:
                    card = anchor.find_parent('article')
                    card_text = clean(card.get_text(' ', strip=True)) if card else ''
                    if re.search(r'inscri[cç][oõ]es\s+abertas?', card_text or '', re.I):
                        if re.search(
                            r'ifrn\s+integrado|proitec|bolsa\s+de\s+pesquisa|sele[cç][aã]o\s+de\s+bolsista',
                            card_text or '',
                            re.I,
                        ):
                            continue
                        live_anchors.append(anchor)
                list_anchors = live_anchors
            elif defn.source_type == 'facet_open':
                # FACET's homepage also contains an SEO archive of old
                # contests.  The live portal entries use the canonical
                # /informacoes/<id>/ route; the archive uses /concursos/.
                list_anchors = [
                    anchor for anchor in list_anchors
                    if re.search(r'/informacoes/\d+/?$', urljoin(str(list_response.url), anchor.get('href') or ''), re.I)
                ]
            elif defn.source_type == 'apta_open':
                # APTA exposes explicit counters for the tabs and keeps the
                # current contest in the active "Inscrições abertas" pane;
                # the remaining publication cards are finalized history.
                list_anchors = [
                    anchor for anchor in list_anchors
                    if re.search(r'/concursos/publicacoes/[^/?#]+/\d+/?$', urljoin(str(list_response.url), anchor.get('href') or ''), re.I)
                    and (
                        (pane := anchor.find_parent(class_=re.compile(r'\btab-pane\b')))
                        is not None
                        and 'active' in (pane.get('class') or [])
                    )
                ]
            for anchor in list_anchors:
                href = anchor.get('href') or ''
                url = urljoin(str(list_response.url), href)
                path = urlparse(url).path.casefold()
                label = clean(anchor.get_text(' ', strip=True)) or ''
                if (
                    defn.source_type == 'institutomais_open'
                    and re.search(r'/concursos/concursosencerrados/?$', path, re.I)
                ):
                    continue
                if defn.source_type == 'cotec_open' and re.search(
                    r'profici[eê]ncia\s+em\s+l[ií]nguas', label, re.I,
                ):
                    # COTEC publishes this language-proficiency exam in the
                    # same list, but the crawler's explicit monitor scope is
                    # personnel contests/selections.  Keep the visible count
                    # independent while applying the same semantic scope.
                    continue
                if defn.source_type == 'exame_open':
                    contexts = []
                    for parent in anchor.parents:
                        if getattr(parent, 'name', None) not in {'li', 'article', 'div', 'tr'}:
                            continue
                        context = clean(parent.get_text(' ', strip=True)) or ''
                        if len(label) + 10 <= len(context) <= 1000:
                            contexts.append(context)
                    compact_context = min(contexts, key=len) if contexts else label
                    if re.search(
                        r'certifica[cç][aã]o\s+ocupacional|processo\s+seletivo\s+interno',
                        compact_context,
                        re.I,
                    ):
                        continue
                allowed_hosts = {urlparse(str(list_response.url)).netloc.casefold().removeprefix('www.')}
                if defn.source_type == 'fundep_open':
                    allowed_hosts.update({'fundep.selecao.net.br', 'gestaodeconcursos.com.br'})
                elif defn.source_type == 'facet_open':
                    allowed_hosts.add('concursos.facetconcursos.com.br')
                if urlparse(url).netloc.casefold().removeprefix('www.') not in allowed_hosts or urlparse(url).fragment:
                    continue
                if path.endswith(('.pdf', '.doc', '.docx')) or url.rstrip('/') == str(list_response.url).rstrip('/'):
                    continue
                if defn.source_type == 'fundep_open':
                    contexts = []
                    for parent in anchor.parents:
                        if getattr(parent, 'name', None) not in {'li', 'article', 'div', 'tr'}:
                            continue
                        context = clean(parent.get_text(' ', strip=True)) or ''
                        if len(label) + 10 <= len(context) <= 1000:
                            contexts.append(context)
                    compact_context = min(contexts, key=len) if contexts else label
                    if re.search(r'vestibular|homologad|seriad|transfer[êe]ncia', compact_context, re.I):
                        continue
                is_candidate_path = bool(re.search(r'/(?:concursos?|processos?-seletivos?|informacoes|detalhe|edital)/[^/?#]+', path))
                is_candidate_path = is_candidate_path or bool(re.search(r'(?:[?&](?:id|cod|codigo)=\d+)', url, re.IGNORECASE))
                has_identity = bool(re.search(r'concurso|processo seletivo|edital|prefeitura|câmara|camara|secretaria|tribunal|universidade|conselho|município|municipio', label, re.I))
                generic_detail_label = label.casefold() in {'mais detalhes', 'saiba mais', 'ver detalhes'}
                if is_candidate_path and (
                    has_identity
                    or generic_detail_label
                    or defn.source_type in {
                        'ibgp_open', 'imeso_open', 'cesgranrio_open', 'legalle_open', 'fenix_open',
                        'facet_open', 'funcern_selection',
                    }
                ):
                    list_links.add(_canonical_url(url))
            if list_links:
                evidence['visible_valid_items'] = len(list_links)

            if not detail_url:
                evidence['observation_error'] = 'crawler sample has no official detail URL'
                return evidence
            detail_response = client.get(detail_url)
            detail_response.raise_for_status()
            detail_page_url = str(detail_response.url)
            detail_soup = BeautifulSoup(detail_response.text, 'lxml')
            expected, pub_obs = _extract_official_expected(detail_soup, detail_page_url)
            evidence['expected'] = expected
            evidence['publication_observation'] = pub_obs
            evidence['evidence_urls'].append(detail_page_url)
            if expected.get('link_edital'):
                evidence['evidence_urls'].append(expected['link_edital'])
            evidence['independent'] = bool(expected.get('titulo') or pub_obs.get('expected_titles'))
    except Exception as exc:
        evidence['observation_error'] = f'{exc.__class__.__name__}: {str(exc)[:240]}'
    return evidence


def _merge_evidence(static: dict[str, Any], dynamic: dict[str, Any]) -> dict[str, Any]:
    merged = dict(dynamic)
    merged['expected'] = {**dynamic.get('expected', {}), **static.get('expected', {})}
    merged['known_null_fields'] = sorted(set(dynamic.get('known_null_fields', [])) | set(static.get('known_null_fields', [])))
    merged['evidence_urls'] = list(dict.fromkeys([*dynamic.get('evidence_urls', []), *static.get('evidence_urls', [])]))
    merged['publication_observation'] = static.get('publication_observation') or dynamic.get('publication_observation', {})
    if static.get('visible_valid_items') is not None:
        merged['visible_valid_items'] = static['visible_valid_items']
    merged['independent'] = bool(static.get('independent') or dynamic.get('independent'))
    merged['method'] = '+'.join(dict.fromkeys(filter(None, [dynamic.get('method'), static.get('method')])))
    if static.get('observed_at'):
        merged['static_observed_at'] = static['observed_at']
    return merged


def _actual_sample(item: dict[str, Any]) -> dict[str, Any]:
    return {field: serialize_val(item.get(field)) for field in AUDIT_FIELDS}


def _audit_publications(
    expected_observation: dict[str, Any] | None,
    actual: list[dict[str, Any]],
    *,
    actual_observed: bool = True,
) -> dict[str, Any]:
    actual = [p for p in actual if isinstance(p, dict)]
    invalid_actual = [p.get('title') for p in actual if not is_valid_publication_title(p.get('title'))]
    expected_observation = expected_observation or {}
    expected_titles = expected_observation.get('expected_titles') or []
    expected_links = expected_observation.get('expected_links') or []
    actual_titles = [p.get('title') for p in actual if has_value(p.get('title'))]
    actual_links = [p.get('link') for p in actual if has_value(p.get('link'))]
    result: dict[str, Any] = {
        'status': 'UNKNOWN',
        'expected_count': len(expected_titles),
        'actual_count': len(actual) if actual_observed else None,
        'expected_titles': expected_titles[:80],
        'actual_titles': actual_titles[:80],
        'invalid_actual_titles': invalid_actual[:20],
        'missing_titles': [],
        'missing_links': [],
    }
    if not actual_observed:
        return result
    if invalid_actual:
        result['status'] = 'MISMATCH'
    if expected_titles or expected_links:
        result['missing_titles'] = []
        for position, title in enumerate(expected_titles):
            title_match = any(
                normalize_for_audit('titulo', title) == normalize_for_audit('titulo', actual_title)
                for actual_title in actual_titles
            )
            if title_match:
                continue
            # A portal may render two labels for the same document (for
            # example a short card label and a detailed row label). When the
            # official URL is the same, this is a label variant, not a missing
            # publication.
            expected_link = expected_links[position] if position < len(expected_links) else None
            same_link = expected_link and any(
                normalize_for_audit('link_edital', expected_link) == normalize_for_audit('link_edital', actual_link)
                for actual_link in actual_links
            )
            if not same_link:
                result['missing_titles'].append(title)
        result['missing_links'] = [
            link for link in expected_links
            if not any(normalize_for_audit('link_edital', link) == normalize_for_audit('link_edital', actual_link) for actual_link in actual_links)
        ]
        if not result['missing_titles'] and not result['missing_links'] and not invalid_actual:
            result['status'] = 'MATCH'
        elif result['status'] != 'MISMATCH':
            result['status'] = 'MISMATCH'
    return result


def _verification_status(entry: dict[str, Any], evidence: dict[str, Any], field_audit: dict[str, str] | None, publication_audit: dict[str, Any] | None) -> str:
    crawler_status = entry.get('crawler_status')
    if crawler_status == 'blocked' or entry.get('http_status') in (401, 403, 429):
        return 'BLOCKED'
    if crawler_status == 'failed':
        return 'FAILED_EXTERNAL'
    if crawler_status == 'empty_valid':
        return 'EMPTY_VERIFIED' if entry.get('empty_evidence') else 'NOT_AUDITED'
    if crawler_status != 'success':
        return 'NOT_AUDITED'
    if not evidence.get('independent') or not evidence.get('expected'):
        return 'NOT_AUDITED'
    if not field_audit or not any(value == 'MATCH' for value in field_audit.values()):
        return 'NOT_AUDITED'
    if any(value == 'MISMATCH' for value in field_audit.values()):
        return 'BROKEN'
    if publication_audit and publication_audit.get('status') == 'MISMATCH':
        return 'BROKEN'
    visible = entry.get('visible_valid_items')
    if visible is None:
        return 'NOT_AUDITED'
    if visible != entry.get('processed', 0):
        return 'PARTIAL'
    return 'VERIFIED'


def _not_audited_reason(entry: dict[str, Any], evidence: dict[str, Any], field_audit: dict[str, str] | None) -> str:
    """Return one explicit reason whenever independent verification is inconclusive."""
    crawler_status = entry.get('crawler_status')
    if crawler_status != 'success':
        return f'NOT_AUDITED_REASON: crawler_status={crawler_status or "unknown"}'
    if not evidence.get('independent'):
        return 'NOT_AUDITED_REASON: no_independent_official_observation'
    if not evidence.get('expected'):
        return 'NOT_AUDITED_REASON: no_independent_official_value'
    if not field_audit or not any(value == 'MATCH' for value in field_audit.values()):
        return 'NOT_AUDITED_REASON: no_comparable_field_match'
    if entry.get('visible_valid_items') is None:
        return 'NOT_AUDITED_REASON: no_independent_visible_valid_count'
    return 'NOT_AUDITED_REASON: verification_criteria_inconclusive'


def audit_single_source(index: int, defn, static_evidence: dict[str, dict[str, Any]] | None = None) -> dict[str, Any]:
    source_type = defn.source_type
    base_url = defn.base_url
    list_url = defn.list_urls[0] if defn.list_urls else base_url
    start_time = time.monotonic()
    res_entry: dict[str, Any] = {
        'index': index,
        'source_type': source_type,
        'name': defn.name,
        'canonical_name': defn.banca,
        'category': defn.category,
        'url': list_url,
        'base_url': base_url,
        'status': 'degraded',
        'crawler_status': 'degraded',
        'verification_status': 'NOT_AUDITED',
        'http_status': None,
        'browser_used': False,
        'technology': 'HTML',
        'visible_valid_items': None,
        'candidates_found': 0,
        'candidates_rejected': 0,
        'processed': 0,
        'empty_evidence': None,
        'error_type': None,
        'error_message': None,
        'sample': None,
        'field_audit': None,
        'publication_audit': None,
        'evidence_urls': [list_url],
        'duration_seconds': 0.0,
    }
    try:
        connector = get_connector(source_type, base_url=base_url, list_url=list_url)
        if hasattr(connector, 'crawl_with_diagnostics'):
            crawl_res = connector.crawl_with_diagnostics()
            items = crawl_res.items
            run_data = crawl_res.run_data
            res_entry['crawler_status'] = run_data.status
            res_entry['http_status'] = run_data.http_status
            res_entry['browser_used'] = run_data.browser_used
            res_entry['candidates_found'] = run_data.candidates_found
            res_entry['candidates_rejected'] = run_data.candidates_rejected
            res_entry['empty_evidence'] = run_data.diagnostics_payload.get('empty_evidence')
            res_entry['error_type'] = run_data.error_type
            res_entry['error_message'] = run_data.error_message
        else:
            items = connector.crawl()
            res_entry['crawler_status'] = 'success' if items else 'degraded'
            res_entry['candidates_found'] = len(items)

        res_entry['status'] = res_entry['crawler_status']
        res_entry['processed'] = len(items)
        sample_static = (static_evidence or {}).get(source_type, {})
        sample_url = sample_static.get('sample_url')
        sample = next((item for item in items if sample_url and _canonical_url(item.get('link_pagina', '')) == _canonical_url(sample_url)), None)
        if sample is None and not sample_url and items:
            sample = items[0]

        dynamic_evidence = collect_independent_evidence(defn, sample)
        evidence = _merge_evidence(sample_static, dynamic_evidence)
        res_entry['visible_valid_items'] = evidence.get('visible_valid_items')
        res_entry['evidence_urls'] = list(dict.fromkeys([*res_entry['evidence_urls'], *evidence.get('evidence_urls', [])]))

        if sample is not None:
            actual = _actual_sample(sample)
            expected = evidence.get('expected') or {}
            field_audit = build_field_audit(expected, actual, known_null_fields=evidence.get('known_null_fields', []))
            actual_pubs = (sample.get('raw_data') or {}).get('publications') or []
            publication_audit = _audit_publications(evidence.get('publication_observation'), actual_pubs)
            res_entry['sample'] = {
                'expected': serialize_val(expected),
                'actual': actual,
                'field_audit': field_audit,
                'publication_audit': publication_audit,
                'evidence_urls': evidence.get('evidence_urls', []),
                'observation_method': evidence.get('method'),
                'observed_at': evidence.get('observed_at'),
            }
            res_entry['field_audit'] = field_audit
            res_entry['publication_audit'] = publication_audit
        elif evidence.get('expected'):
            # Never compare evidence for one contest with another crawler item.
            res_entry['sample'] = {
                'expected': serialize_val(evidence.get('expected')),
                'actual': None,
                'field_audit': {field: 'UNKNOWN' for field in AUDIT_FIELDS},
                'publication_audit': _audit_publications(
                    evidence.get('publication_observation'), [], actual_observed=False,
                ),
                'evidence_urls': evidence.get('evidence_urls', []),
                'observation_method': evidence.get('method'),
            }
            res_entry['field_audit'] = res_entry['sample']['field_audit']
            res_entry['publication_audit'] = res_entry['sample']['publication_audit']

        if evidence.get('observation_error'):
            res_entry.setdefault('audit_notes', []).append(evidence['observation_error'])
        res_entry['verification_status'] = _verification_status(
            res_entry, evidence, res_entry.get('field_audit'), res_entry.get('publication_audit'),
        )
        if res_entry['verification_status'] == 'NOT_AUDITED':
            res_entry.setdefault('audit_notes', []).append(
                _not_audited_reason(res_entry, evidence, res_entry.get('field_audit')),
            )
    except Exception as exc:
        res_entry['crawler_status'] = 'failed'
        res_entry['status'] = 'failed'
        res_entry['error_type'] = exc.__class__.__name__
        res_entry['error_message'] = str(exc)
        res_entry['verification_status'] = 'FAILED_EXTERNAL'
        logger.warning('Source %02d (%s) failed: %s', index, source_type, exc)

    res_entry['duration_seconds'] = round(time.monotonic() - start_time, 2)
    logger.info(
        '[%02d/%02d] %s -> crawler=%s verification=%s (items: %s, %ss)',
        index, len(MASTER_SOURCES), source_type, res_entry['crawler_status'],
        res_entry['verification_status'], res_entry['processed'], res_entry['duration_seconds'],
    )
    return res_entry


def _count_by(sources: list[dict[str, Any]], field: str, allowed: tuple[str, ...]) -> dict[str, int]:
    return {value: sum(1 for source in sources if source.get(field) == value) for value in allowed}


def main() -> None:
    static_evidence = load_independent_evidence()
    print(f'Starting Full LIVE Audit of {len(MASTER_SOURCES)} sources with independent evidence checks...')
    start_total = time.monotonic()
    results_by_index: dict[int, dict[str, Any]] = {}
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_map = {
            executor.submit(audit_single_source, idx, definition, static_evidence): idx
            for idx, definition in enumerate(MASTER_SOURCES, 1)
        }
        for future in as_completed(future_map):
            idx = future_map[future]
            try:
                results_by_index[idx] = future.result()
            except Exception as exc:
                logger.error('Critical error executing source index %s: %s', idx, exc)

    ordered_sources = [results_by_index[i] for i in range(1, len(MASTER_SOURCES) + 1)]
    crawler_values = ('success', 'empty_valid', 'blocked', 'failed', 'degraded')
    verification_values = ('VERIFIED', 'EMPTY_VERIFIED', 'BLOCKED', 'FAILED_EXTERNAL', 'PARTIAL', 'BROKEN', 'NOT_AUDITED')
    crawler_counts = _count_by(ordered_sources, 'crawler_status', crawler_values)
    verification_counts = _count_by(ordered_sources, 'verification_status', verification_values)
    total_duration = round(time.monotonic() - start_total, 2)
    total_processed = sum(int(source.get('processed') or 0) for source in ordered_sources)
    total_candidates = sum(int(source.get('candidates_found') or 0) for source in ordered_sources)
    visible_values = [source.get('visible_valid_items') for source in ordered_sources if isinstance(source.get('visible_valid_items'), int)]
    summary = {
        'total_sources': len(ordered_sources),
        **crawler_counts,
        'crawler_status_counts': crawler_counts,
        'verification_status_counts': verification_counts,
        'total_candidates': total_candidates,
        'total_processed': total_processed,
        'total_visible_valid_items': sum(visible_values) if visible_values else None,
        'total_items': total_processed,
        'duration_seconds': total_duration,
    }
    final_payload = {
        'generated_at': datetime.now(timezone.utc).isoformat(),
        'code_revision': 'final-audit-independent-evidence-2026-08-29',
        'evidence_policy': 'MATCH requires an independently observed official value; crawler-only values are UNKNOWN',
        'summary': summary,
        'sources': ordered_sources,
    }
    out_path = BACKEND_ROOT / 'audit_live_99.json'
    with out_path.open('w', encoding='utf-8') as handle:
        json.dump(final_payload, handle, indent=2, ensure_ascii=False)
    print('\n==================================================')
    print('CRAWLER STATUS:')
    for value in crawler_values:
        print(f'  {value:14s}: {crawler_counts[value]}')
    print('VERIFICATION STATUS:')
    for value in verification_values:
        print(f'  {value:14s}: {verification_counts[value]}')
    print(f'  Candidates      : {total_candidates}')
    print(f'  Processed       : {total_processed}')
    print(f'  Duration        : {total_duration}s')
    print('==================================================')
    print(f'Saved to {out_path}')


if __name__ == '__main__':
    main()
