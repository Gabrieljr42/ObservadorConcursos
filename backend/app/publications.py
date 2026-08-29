from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urljoin

from bs4 import BeautifulSoup


def clean(value: Any) -> str | None:
    if value is None:
        return None
    text = ' '.join(str(value).strip().split())
    return text or None


def normalize_publication_type(title: str | None) -> str:
    text = (title or '').lower()
    if any(k in text for k in ['errata', 'retifica', 'rerratifica']):
        return 'errata'
    if any(k in text for k in ['edital', 'portaria', 'decreto', 'termo de convocação', 'normativo']):
        return 'edital'
    if 'gabarito' in text:
        return 'gabarito'
    if any(k in text for k in ['homologa', 'homologação', 'homologacao']):
        return 'homologacao'
    if any(k in text for k in ['resultado', 'classifica', 'aprovad', 'desempenho', 'nota']):
        return 'resultado'
    if any(k in text for k in ['convoca', 'chamada']):
        return 'convocacao'
    if any(k in text for k in ['lista', 'inscrito', 'inscritos', 'concorrência', 'concorrencia', 'relação de']):
        return 'lista_inscritos'
    if any(k in text for k in ['recurso', 'julgamento', 'impugna', 'resposta', 'parecer']):
        return 'recurso'
    if any(k in text for k in ['comunicado', 'aviso', 'nota oficial', 'informativo', 'esclarecimento']):
        return 'comunicado'
    if any(k in text for k in ['cronograma', 'calendário', 'calendario']):
        return 'outro'
    return 'outro'


def build_publication_hash(title: str | None, publication_date: str | None, link: str | None, publication_type: str | None) -> str:
    raw = '|'.join([
        clean(title) or '',
        clean(publication_date) or '',
        clean(link) or '',
        clean(publication_type) or '',
    ]).lower()
    return hashlib.sha256(raw.encode('utf-8')).hexdigest()


def _is_date_line(line: str) -> bool:
    return bool(re.fullmatch(r'\d{1,2}/\d{1,2}/\d{4}', line.strip()))


def _iso_date(line: str | None) -> str | None:
    if not line:
        return None
    match = re.search(r'(\d{1,2})/(\d{1,2})/(\d{4})', line)
    if not match:
        return None
    day, month, year = map(int, match.groups())
    try:
        return datetime(year, month, day, tzinfo=timezone.utc).isoformat()
    except ValueError:
        return None


def _is_noise_title(line: str) -> bool:
    lowered = line.strip().lower().strip(' •\t\r\n-–—|')
    if not lowered or len(lowered) < 3:
        return True
    noise_exact = {
        'download', 'publicações', 'publicacoes', 'arquivos disponíveis', 'arquivos disponiveis',
        'vagas', 'vaga', 'qtde.', 'extrato e legislação', 'extrato e legislacao',
        'informações gerais', 'informacoes gerais', 'voltar', 'contato', 'contatos',
        'termos de uso', 'termo de uso', 'central de ajuda', 'ajuda', 'institucional',
        'politica de privacidade', 'política de privacidade', 'legal', 'início', 'inicio',
        'home', 'principal', 'menu principal', 'perguntas', 'perguntas frequentes', 'faq',
        'legislação', 'legislacao', 'sobre', 'sobre nós', 'quem somos', 'equipe',
        'ouvidoria', 'transparência', 'transparencia', 'fale conosco', 'área do candidato',
        'area do candidato', 'login', 'acessar', 'cadastre-se', 'cadastro',
    }
    if lowered in noise_exact:
        return True
    if any(phrase in lowered for phrase in (
        'termos de uso', 'politica de privacidade', 'política de privacidade',
        'central de ajuda', 'área do candidato', 'area do candidato', 'todos os direitos reservados',
    )):
        return True
    return False


def parse_publications_from_lines(lines: list[str], *, source: str | None = None) -> list[dict[str, Any]]:
    """Extract a conservative publication list from visible portal lines.

    Supports the two structures seen so far:
    - FUNDEP: Publicações -> title -> date -> Download -> ... -> Vagas
    - IMESO: ARQUIVOS DISPONÍVEIS -> VAGAS -> EXTRATO... -> date -> title -> DOWNLOAD
    """
    if not lines:
        return []

    start = None
    end = len(lines)
    normalized = [clean(line) or '' for line in lines]
    lower = [line.lower() for line in normalized]

    for idx, value in enumerate(lower):
        if value in {'publicações', 'publicacoes', 'arquivos disponíveis', 'arquivos disponiveis'}:
            start = idx + 1
            break
    if start is None:
        return []

    for idx in range(start, len(lines)):
        value = lower[idx]
        # In FUNDEP, Vagas means publication section ended. In IMESO, VAGAS may
        # be followed by file-category labels before publication rows. Keep it for
        # IMESO but stop for FUNDEP.
        if source == 'fundep' and value == 'vagas':
            end = idx
            break
        if value in {'sobre a imeso', 'contato', 'concursos', 'realizados'}:
            end = idx
            break

    section = normalized[start:end]
    publications: list[dict[str, Any]] = []
    seen: set[str] = set()

    # Pattern A: title, date, Download
    for idx, line in enumerate(section):
        if _is_date_line(line):
            publication_date = _iso_date(line)
            title = None
            # Usually the title is immediately before the date in FUNDEP.
            if idx > 0 and not _is_noise_title(section[idx - 1]) and not _is_date_line(section[idx - 1]):
                title = section[idx - 1]
            # IMESO often uses date, title, DOWNLOAD.
            if (not title or len(title) < 4) and idx + 1 < len(section) and not _is_noise_title(section[idx + 1]):
                title = section[idx + 1]
            if not title or _is_noise_title(title):
                continue
            pub_type = normalize_publication_type(title)
            content_hash = build_publication_hash(title, publication_date, None, pub_type)
            if content_hash in seen:
                continue
            seen.add(content_hash)
            publications.append({
                'title': title,
                'publication_type': pub_type,
                'publication_date': publication_date,
                'link': None,
                'content_hash': content_hash,
                'source': source,
            })

    return publications[:80]


def parse_publications_from_dom(soup: BeautifulSoup, base_url: str, *, source: str | None = None) -> list[dict[str, Any]]:
    """Extract publication title/date/link rows directly from portal DOM.

    This complements the legacy line parser and handles cards/tables where the
    anchor URL is otherwise lost when flattening text.
    """
    if not soup:
        return []
    results: list[dict[str, Any]] = []
    seen_links: dict[str, int] = {}
    for anchor in soup.select('a[href]'):
        title = clean(anchor.get_text(' ', strip=True))
        href = anchor.get('href')
        if not title or not href or _is_noise_title(title):
            continue
        lowered_title = title.lower()
        if any(noise in lowered_title for noise in (
            'inscrições abertas', 'inscricoes abertas', 'inscrição online', 'inscricao online',
            'inscreva-se', 'área do candidato', 'area do candidato',
            'menu principal', 'perguntas frequentes', 'fale conosco',
        )):
            continue
        context = clean(anchor.parent.get_text(' ', strip=True)) if anchor.parent else title
        full_context = f'{title} {context}'.lower()
        valid_tokens = (
            'edital', 'resultado', 'gabarito', 'retifica', 'rerratifica', 'errata',
            'comunicado', 'convoca', 'recurso', 'publica', 'homologa', 'cronograma',
            'impugna', 'relat', 'julgamento', 'anexo', 'laudo', 'portaria', 'decreto',
            'termo', 'resposta', 'parecer', 'nota', 'aviso', 'declarat', 'isenção',
            'isencao', 'concorrência', 'concorrencia', 'local', 'locais', 'inscrito',
            'inscritos', 'homologados', 'classifica', 'aprovad',
        )
        is_pdf_or_doc = any(href.lower().endswith(ext) or ext in href.lower() for ext in ('.pdf', '.doc', '.docx', 'download', 'arquivo='))
        if not (any(token in full_context for token in valid_tokens) or is_pdf_or_doc):
            continue
        date_match = re.search(r'\b(\d{1,2}/\d{1,2}/\d{4})\b', f'{context} {title}')
        publication_date = _iso_date(date_match.group(1)) if date_match else None
        link = urljoin(base_url, href)
        pub_type = normalize_publication_type(title)
        content_hash = build_publication_hash(title, publication_date, link, pub_type)
        normalized_link = link.rstrip('/').lower()
        if normalized_link in seen_links:
            existing_index = seen_links[normalized_link]
            existing = results[existing_index]
            if len(title) > len(existing['title']):
                results[existing_index] = {
                    'title': title,
                    'publication_type': pub_type,
                    'publication_date': publication_date or existing.get('publication_date'),
                    'link': link,
                    'content_hash': content_hash,
                    'source': source,
                }
            continue
        seen_links[normalized_link] = len(results)
        results.append({'title': title, 'publication_type': pub_type, 'publication_date': publication_date,
                        'link': link, 'content_hash': content_hash, 'source': source})
    return results[:80]
