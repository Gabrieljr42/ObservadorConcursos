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
    if '@' in lowered or 'email-protection' in lowered:
        return True
    if re.fullmatch(r'\d{1,2}/\d{1,2}/\d{4}', lowered):
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
        'aceitar', 'recusar', 'fechar', 'continuar', 'privacidade', 'cookies',
        'concursos', 'concursos realizados', 'concursos em andamento', 'concursos abertos',
        'processos seletivos', 'editais', 'homologados', 'fundação', 'fundacao',
        'ibade', 'todos', 'concluídos', 'concluidos', 'em andamento', 'menu', 'rodapé',
        'rodape', 'footer', 'social', 'manual', 'manual do candidato', 'documento',
        'documentos', 'aviso',
    }
    if lowered in noise_exact:
        return True
    if any(phrase in lowered for phrase in (
        'termos de uso', 'politica de privacidade', 'política de privacidade',
        'central de ajuda', 'área do candidato', 'area do candidato', 'todos os direitos reservados',
        'aviso de privacidade', 'aviso de cookies', 'política de cookies',
        'pular para o conteúdo', 'pular para o conteudo', 'skip to content',
        'breadcrumb', 'menu principal', 'preferências de cookies', 'preferencias de cookies',
    )):
        return True
    return False


_PUBLICATION_TOKENS = (
    'edital', 'retifica', 'rerratifica', 'errata', 'gabarito', 'resultado',
    'convoca', 'comunicado', 'recurso', 'homologa', 'lista', 'inscrito',
    'anexo', 'portaria', 'decreto', 'aviso', 'cronograma', 'parecer',
    'resposta', 'laudo', 'isenção', 'isencao', 'concorrência', 'concorrencia',
    'classifica', 'aprovad', 'devolução', 'devolucao',
)


def _has_publication_token(value: str | None) -> bool:
    lowered = (value or '').casefold()
    return any(token in lowered for token in _PUBLICATION_TOKENS)


def _is_chrome_anchor(anchor) -> bool:
    """Reject navigation/consent/social chrome by DOM structure."""
    chrome_tokens = (
        'header', 'footer', 'navbar', 'nav-', 'menu', 'breadcrumb', 'sidebar',
        'social', 'cookie', 'privacy', 'privacidade', 'consent', 'modal',
    )
    for parent in [anchor, *anchor.parents]:
        if getattr(parent, 'name', None) in {'nav', 'header', 'footer', 'aside'}:
            return True
        classes = ' '.join(parent.get('class', [])) if hasattr(parent, 'get') else ''
        marker = f'{parent.get("id", "") if hasattr(parent, "get") else ""} {classes}'.casefold()
        if any(token in marker for token in chrome_tokens):
            return True
    return False


def is_publication_anchor(anchor) -> bool:
    """Return whether an anchor can belong to a document/publication row."""
    href = (anchor.get('href') or '').strip()
    if not href or href.startswith('#') or href.casefold().startswith(('javascript:', 'mailto:')) or _is_chrome_anchor(anchor):
        return False
    lowered = href.casefold()
    if any(token in lowered for token in ('/privacidade', 'privacy', 'cookies', '/login', 'email-protection')):
        return False
    return True


def publication_title_from_anchor(anchor) -> str | None:
    """Get a document label, including rows whose action is only DOWNLOAD."""
    title = clean(anchor.get_text(' ', strip=True))
    generic_labels = {
        'download', 'baixar', 'clique aqui', 'ver documento', 'abrir', 'visualizar',
    }
    if title and title.casefold() not in generic_labels and not _is_date_line(title):
        title = re.sub(r'^\d{1,2}/\d{1,2}/\d{4}\s*[-–]?\s*', '', title)
        return re.sub(r'\s*\(abre em nova janela\)\s*$', '', title, flags=re.IGNORECASE).strip()

    # IBADE and similar portals put the date/title/action in one list item.
    # Search only compact row-like ancestors so a footer or whole-card title
    # cannot be borrowed as the publication label.
    for parent in anchor.parents:
        name = getattr(parent, 'name', None)
        classes = ' '.join(parent.get('class', [])) if hasattr(parent, 'get') else ''
        marker = f'{parent.get("id", "") if hasattr(parent, "get") else ""} {classes}'.casefold()
        row_like = name in {'li', 'tr'} or any(token in marker for token in (
            'list-group-item', 'document', 'publication', 'arquivo', 'download',
        ))
        if not row_like:
            continue
        for node in parent.select('h1, h2, h3, h4, h5, h6, p, td, small, span'):
            value = clean(node.get_text(' ', strip=True))
            if not value or value.casefold() == (title or '').casefold() or _is_date_line(value):
                continue
            if is_valid_publication_title(value) and _has_publication_token(value):
                value = re.sub(r'^\d{1,2}/\d{1,2}/\d{4}\s*[-–]?\s*', '', value)
                return re.sub(r'\s*\(abre em nova janela\)\s*$', '', value, flags=re.IGNORECASE).strip()
    fallback = re.sub(r'^\d{1,2}/\d{1,2}/\d{4}\s*[-–]?\s*', '', title or '')
    return re.sub(r'\s*\(abre em nova janela\)\s*$', '', fallback, flags=re.IGNORECASE).strip() or None


def is_valid_publication_title(title: str | None) -> bool:
    """Return whether a visible label can represent an official publication.

    Global navigation and consent links frequently contain words such as
    ``aviso`` or ``documento``.  They are not publications and must be
    rejected before the broader publication-token test runs.
    """
    if _is_noise_title(title or ''):
        return False
    lowered = (title or '').casefold()
    if any(term in lowered for term in (
        'aviso de privacidade', 'aviso de cookies', 'política de privacidade',
        'politica de privacidade', 'política de cookies', 'politica de cookies',
        'pular para', 'skip to', 'preferências de cookies', 'preferencias de cookies',
        'login', 'home', 'início', 'inicio', 'menu', 'breadcrumb', 'privacidade', 'cookies',
        'aceitar', 'recusar', 'fechar', 'continuar',
    )):
        return False
    if _is_noise_title(title) or not _has_publication_token(title) and len(lowered) <= 12:
        return False
    return len(lowered) >= 4


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
            if not title or not is_valid_publication_title(title):
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
        if not is_publication_anchor(anchor):
            continue
        title = publication_title_from_anchor(anchor)
        href = anchor.get('href')
        if not title or not href or not is_valid_publication_title(title):
            continue
        lowered_title = title.lower()
        if any(noise in lowered_title for noise in (
            'inscrições abertas', 'inscricoes abertas', 'inscrição online', 'inscricao online',
            'inscreva-se', 'área do candidato', 'area do candidato',
            'menu principal', 'perguntas frequentes', 'fale conosco',
        )):
            continue
        context = title
        for parent in anchor.parents:
            name = getattr(parent, 'name', None)
            classes = ' '.join(parent.get('class', [])) if hasattr(parent, 'get') else ''
            marker = f'{parent.get("id", "") if hasattr(parent, "get") else ""} {classes}'.casefold()
            if name in {'li', 'tr'} or any(token in marker for token in ('list-group-item', 'document', 'publication', 'arquivo')):
                context = clean(parent.get_text(' ', strip=True)) or title
                break
        full_context = f'{title} {context}'.lower()
        valid_tokens = (
            'edital', 'resultado', 'gabarito', 'retifica', 'rerratifica', 'errata',
            'comunicado', 'convoca', 'recurso', 'publica', 'homologa', 'cronograma',
            'impugna', 'relat', 'julgamento', 'anexo', 'laudo', 'portaria', 'decreto',
            'termo', 'resposta', 'parecer', 'nota', 'aviso', 'declarat', 'isenção',
            'isencao', 'concorrência', 'concorrencia', 'local', 'locais', 'inscrito',
            'inscritos', 'homologados', 'classifica', 'aprovad', 'devolução', 'devolucao',
        )
        is_pdf_or_doc = any(href.lower().endswith(ext) or ext in href.lower() for ext in ('.pdf', '.doc', '.docx', 'download', 'arquivo='))
        if not (any(token in full_context for token in valid_tokens) or is_pdf_or_doc):
            continue
        date_context = context
        if not re.search(r'\b\d{1,2}/\d{1,2}/\d{4}\b', date_context):
            # Simple cards often have a generic div (title + date) instead of
            # a semantic li/tr.  Accept only a small ancestor so a page-wide
            # date cannot be borrowed from another publication.
            for parent in anchor.parents:
                value = clean(parent.get_text(' ', strip=True)) or ''
                if len(title) < len(value) <= 500 and re.search(r'\b\d{1,2}/\d{1,2}/\d{4}\b', value):
                    date_context = value
                    break
        date_match = re.search(r'\b(\d{1,2}/\d{1,2}/\d{4})\b', f'{date_context} {title}')
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
