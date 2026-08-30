from __future__ import annotations

import hashlib
import json
import re
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any
from urllib.parse import parse_qs, unquote, urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from app.pdf.extractor import extract_pdf_text_from_url
from app.pdf.parsers.ibfc import parse_ibfc_pdf

MONTHS_PT = {
    'janeiro': 1,
    'fevereiro': 2,
    'março': 3,
    'marco': 3,
    'abril': 4,
    'maio': 5,
    'junho': 6,
    'julho': 7,
    'agosto': 8,
    'setembro': 9,
    'outubro': 10,
    'novembro': 11,
    'dezembro': 12,
}

UF_RE = re.compile(r'\b([A-Z]{2})\b')
CITY_UF_RE = re.compile(r'\b([A-ZÁÉÍÓÚÂÊÔÃÕÇ][A-Za-zÀ-ÿ .\'’\-]{2,90})\s*[-/]\s*([A-Z]{2})\b')
VALID_UFS = {
    'AC', 'AL', 'AP', 'AM', 'BA', 'CE', 'DF', 'ES', 'GO', 'MA', 'MT', 'MS',
    'MG', 'PA', 'PB', 'PR', 'PE', 'PI', 'RJ', 'RN', 'RS', 'RO', 'RR', 'SC',
    'SP', 'SE', 'TO',
}
SEMANTIC_CITY_VALUES = {
    'inscreva', 'inscreva-se', 'clique aqui', 'concurso público',
    'processo seletivo', 'edital', 'saiba mais', 'detalhes', 'acessar',
    'online', 'leia', 'leia mais', 'ver edital', 'ver detalhes', 'confira',
}
SEMANTIC_CITY_PREFIX_RE = re.compile(
    r'^(?:inscreva(?:-se)?|clique(?:\s+aqui)?|acesse|saiba(?:\s+mais)?|'
    r'leia(?:\s+mais)?|confira|ver(?:\s+(?:edital|detalhes))?)\b',
    re.IGNORECASE,
)
MONEY_RE = re.compile(r'R\$\s*\d{1,3}(?:\.\d{3})*,\d{2}')
DATE_NUM_RE = re.compile(r'\b(\d{1,2})/(\d{1,2})/(\d{2,4})\b')
DATE_PT_RE = re.compile(r'\b(\d{1,2})\s+de\s+([a-zçãé]+)\s+de\s+(\d{4})\b', re.IGNORECASE)
DATE_TOKEN_PATTERN = (
    r'(?:'
    r'\d{1,2}/\d{1,2}/\d{2,4}(?:\s*(?:às|as|-)?\s*\d{1,2}[:h]\d{2})?'
    r'|'
    r'\d{1,2}\s+de\s+[a-zçãé]+\s+de\s+\d{4}'
    r')'
)

AREA_RULES = [
    ('assistencia_social', ['assistente social', 'serviço social', 'servico social', 'cras', 'creas']),
    ('administrativa', ['assistente administrativo', 'auxiliar administrativo', 'agente administrativo', 'analista administrativo', 'administração', 'administracao', 'oficial administrativo']),
    ('educacao', ['professor', 'pedagogo', 'educador', 'monitor escolar', 'magistério', 'magisterio']),
    ('saude', ['agente comunitário de saúde', 'agente comunitario de saude', 'agente de combate às endemias', 'agente de combate as endemias', 'acs', 'ace', 'enfermeiro', 'técnico de enfermagem', 'tecnico de enfermagem', 'médico', 'medico', 'dentista', 'farmacêutico', 'farmaceutico', 'fisioterapeuta', 'nutricionista', 'saúde', 'saude']),
    ('juridica', ['procurador', 'advogado', 'analista jurídico', 'analista juridico', 'defensor público', 'defensor publico']),
    ('seguranca_publica', ['guarda municipal', 'policial', 'bombeiro', 'agente penitenciário', 'agente penitenciario']),
    ('fiscal_tributaria', ['fiscal', 'tributário', 'tributario', 'auditor']),
    ('tecnologia_informacao', ['informática', 'informatica', 'desenvolvedor', 'programador', 'tecnologia da informação', 'tecnologia da informacao', 'suporte técnico de tecnologia', 'suporte tecnico de tecnologia', 'analista de sistemas', 'técnico em informática', 'tecnico em informatica']),
    ('engenharia_arquitetura', ['engenheiro', 'engenharia', 'arquiteto', 'arquitetura']),
    ('contabilidade_financas', ['contador', 'contábil', 'contabil', 'tesoureiro', 'finanças', 'financas']),
    ('psicologia', ['psicólogo', 'psicologo', 'psicologia']),
    ('comunicacao', ['jornalista', 'comunicação', 'comunicacao', 'publicidade']),
    ('meio_ambiente', ['biólogo', 'biologo', 'meio ambiente', 'ambiental']),
]

HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/124.0.0.0 Safari/537.36'
    ),
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
    'Cache-Control': 'no-cache',
    'Pragma': 'no-cache',
    'Upgrade-Insecure-Requests': '1',
}


def clean(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.replace('\xa0', ' ')
    value = re.sub(r'\s+', ' ', value).strip(' \t\r\n:-–—')
    return value or None


def text_lines(soup: BeautifulSoup) -> list[str]:
    for tag in soup(['script', 'style', 'noscript']):
        tag.decompose()
    lines = [clean(line) for line in soup.get_text('\n', strip=True).split('\n')]
    return [line for line in lines if line]


def normalize_url(base: str, href: str | None) -> str | None:
    if not href:
        return None
    href = href.strip()
    if href.lower().startswith('javascript:') or href == '#':
        return None
    return urljoin(base, href)


def extract_external_id(url: str, patterns: list[str]) -> str | None:
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None


def parse_money(value: str | None) -> Decimal | None:
    if not value:
        return None
    match = MONEY_RE.search(value)
    raw = match.group(0) if match else str(value)
    raw = raw.replace('R$', '').strip()
    # Already-normalized decimal strings can arrive from PDF parsers/JSON
    # (e.g. "1673.24"). Do not treat the dot as thousands separator.
    if ',' not in raw and re.fullmatch(r'\d+(?:\.\d{1,2})?', raw):
        try:
            return Decimal(raw)
        except (InvalidOperation, ValueError):
            return None
    raw = raw.replace('.', '').replace(',', '.').strip()
    try:
        return Decimal(raw)
    except (InvalidOperation, ValueError):
        return None


def parse_numeric_date(day: str, month: str, year: str, hour: str | None = None, minute: str | None = None) -> datetime | None:
    try:
        y = int(year)
        if y < 100 and len(year) <= 2:
            y += 2000
        # Some legacy portals use 01/01/0001 as a database sentinel for an
        # unknown end date. Never expose that impossible date as real data.
        if y < 1900:
            return None
        return datetime(y, int(month), int(day), int(hour or 0), int(minute or 0), tzinfo=UTC)
    except ValueError:
        return None


def parse_pt_date(day: str, month_name: str, year: str, hour: str | None = None, minute: str | None = None) -> datetime | None:
    month = MONTHS_PT.get(month_name.lower().replace('ç', 'c')) or MONTHS_PT.get(month_name.lower())
    if not month:
        return None
    return parse_numeric_date(day, str(month), year, hour, minute)


def first_date(value: str | None) -> datetime | None:
    if not value:
        return None
    num = re.search(r'(\d{1,2})/(\d{1,2})/(\d{2,4})(?:\s*(?:às|as|-)?\s*(\d{1,2})[:h](\d{2}))?', value, flags=re.IGNORECASE)
    if num:
        return parse_numeric_date(num.group(1), num.group(2), num.group(3), num.group(4), num.group(5))
    pt = re.search(r'(\d{1,2})\s+de\s+([a-zçãé]+)\s+de\s+(\d{4})(?:\s*(?:às|as)?\s*(\d{1,2})[:h](\d{2}))?', value, flags=re.IGNORECASE)
    if pt:
        return parse_pt_date(pt.group(1), pt.group(2), pt.group(3), pt.group(4), pt.group(5))
    return None


def parse_date_interval(value: str | None) -> tuple[datetime | None, datetime | None]:
    if not value:
        return None, None

    # Many Brazilian portals abbreviate a range as ``17 de agosto a 08 de
    # outubro de 2026``.  The year belongs to the second date, so the generic
    # full-date matcher would otherwise skip the first date and fall back to an
    # unrelated legal/publication date.
    shared_year = re.search(
        r'(\d{1,2})\s+de\s+([a-zçãé]+)(?:\s+de\s+(\d{4}))?\s+'
        r'(?:a|até|e|[-–])\s*(\d{1,2})\s+de\s+([a-zçãé]+)\s+de\s+(\d{4})',
        value,
        flags=re.IGNORECASE,
    )
    if shared_year:
        first_year = shared_year.group(3) or shared_year.group(6)
        start = parse_pt_date(shared_year.group(1), shared_year.group(2), first_year)
        end = parse_pt_date(shared_year.group(4), shared_year.group(5), shared_year.group(6), '23', '59')
        if start and end:
            return start, end

    # Detail pages commonly mention a law/publication date before the actual
    # registration window. Prefer an interval explicitly attached to the
    # registration/period label so that e.g. ``17 de março de 1995`` cannot be
    # paired with a later registration date.
    contextual_patterns = [
        rf'(?:no\s+)?per[ií]odo\s+(?:de\s+)?({DATE_TOKEN_PATTERN}).{{0,160}}?(?:a|até|e|[-–])\s*({DATE_TOKEN_PATTERN})',
        rf'inscri[cç][oõ]e?s?.{{0,250}}?(?:de|:)\s*({DATE_TOKEN_PATTERN}).{{0,160}}?(?:a|até|e|[-–])\s*({DATE_TOKEN_PATTERN})',
    ]
    for pattern in contextual_patterns:
        match = re.search(pattern, value, flags=re.IGNORECASE | re.DOTALL)
        if not match:
            continue
        start = first_date(match.group(1))
        end = first_date(match.group(2))
        if start and end:
            # A date written without a time represents the full end day.
            if not re.search(r'\d{1,2}[:h]\d{2}', match.group(2)):
                end = end.replace(hour=23, minute=59)
            return start, end

    # Numeric format: 04/05/2026 - 10:00 até 08/06/2026 - 17:00
    nums = list(re.finditer(r'(\d{1,2})/(\d{1,2})/(\d{2,4})(?:\s*(?:às|as|-)?\s*(\d{1,2})[:h](\d{2}))?', value, flags=re.IGNORECASE))
    if len(nums) >= 2:
        start = parse_numeric_date(nums[0].group(1), nums[0].group(2), nums[0].group(3), nums[0].group(4), nums[0].group(5))
        end = parse_numeric_date(nums[1].group(1), nums[1].group(2), nums[1].group(3), nums[1].group(4), nums[1].group(5))
        return start, end

    # Short numeric format: 19/05/26 09:00 até 20/06/26 16:00
    shorts = list(re.finditer(r'(\d{1,2})/(\d{1,2})/(\d{2})(?:\s*(\d{1,2})[:h](\d{2}))?', value, flags=re.IGNORECASE))
    if len(shorts) >= 2:
        start = parse_numeric_date(shorts[0].group(1), shorts[0].group(2), shorts[0].group(3), shorts[0].group(4), shorts[0].group(5))
        end = parse_numeric_date(shorts[1].group(1), shorts[1].group(2), shorts[1].group(3), shorts[1].group(4), shorts[1].group(5))
        return start, end

    # PT long format: das 9 horas do dia 17 de maio de 2021 às 23 horas e 59 minutos do dia 08 de julho de 2021.
    pts = list(DATE_PT_RE.finditer(value))
    if len(pts) >= 2:
        start = parse_pt_date(pts[0].group(1), pts[0].group(2), pts[0].group(3))
        end = parse_pt_date(pts[1].group(1), pts[1].group(2), pts[1].group(3), '23', '59')
        return start, end
    return None, None


def extract_city_uf(value: str | None) -> tuple[str | None, str | None]:
    if not value:
        return None, None

    location_match = re.search(
        r'\bVagas?\s+para\s*:\s*([^,;\n]{2,80}?)\s*/\s*([A-Z]{2})\b',
        value,
        flags=re.IGNORECASE,
    )
    if location_match and location_match.group(2).upper() in VALID_UFS:
        return clean(location_match.group(1).title()), location_match.group(2).upper()

    # Prefer organization-aware patterns before the generic "Cidade - UF" pattern.
    # Otherwise values like "PREFEITURA MUNICIPAL DE CARBONITA/MG" are parsed as
    # city="Prefeitura Municipal De Carbonita".
    org_match = re.search(
        r'\b(?:PREFEITURA|CÂMARA|CAMARA)\s+(?:MUNICIPAL\s+)?(?:DE|DA|DO)?\s*'
        r'([A-ZÁÉÍÓÚÂÊÔÃÕÇ][A-ZÁÉÍÓÚÂÊÔÃÕÇ .\-]{2,80}?)\s*[-/]\s*([A-Z]{2})\b',
        value,
        flags=re.IGNORECASE,
    )
    if org_match:
        uf = org_match.group(2).upper()
        if uf in VALID_UFS:
            return clean(org_match.group(1).title()), uf

    match = CITY_UF_RE.search(value)
    if match:
        city = clean(match.group(1).title())
        if city:
            marker = re.search(r'\b(?:Prefeitura|Câmara|Camara|Município|Municipio)\b', city, flags=re.IGNORECASE)
            if marker:
                city = city[marker.end():].strip()
                city = re.sub(r'^(?:Municipal\s+)?(?:De|Da|Do)?\s*', '', city, flags=re.IGNORECASE).strip()
        uf = match.group(2).upper()
        if uf not in VALID_UFS:
            return None, None
        # Narrative fragments such as "conclusão da avaliação e - OU" are not cities.
        if city.casefold().strip(' .-_/') in {value.casefold() for value in SEMANTIC_CITY_VALUES} or SEMANTIC_CITY_PREFIX_RE.match(city):
            return None, None
        if len(city.split()) > 8 or any(token in city.lower() for token in (
            'conclus', 'avaliação', 'resultado', 'inscriç', 'conselho regional',
            'autarquia municipal', 'agência de', 'agencia de',
        )):
            return None, None
        return city, uf
    return None, None


def status_from_dates(start: datetime | None, end: datetime | None, fallback: str | None = None) -> str | None:
    now = datetime.now(UTC)
    if start and start > now:
        return 'Inscrições em breve'
    if end and end >= now:
        return 'Inscrições abertas'
    if fallback:
        return fallback
    if end and end < now:
        return 'Encerrado'
    return None


def classify_area(*values: str | None) -> str | None:
    text = ' '.join([value or '' for value in values]).lower()
    if any(token in text for token in ['jovem aprendiz', 'nível médio', 'nivel medio', 'ensino médio', 'ensino medio']):
        # only return this if no stronger signal exists
        fallback = 'nivel_medio_tecnico'
    else:
        fallback = None
    for area, keywords in AREA_RULES:
        if any(keyword in text for keyword in keywords):
            return area
    return fallback


def detect_area_hits(*values: str | None) -> set[str]:
    """Return all areas matched by the supplied text.

    This is intentionally stricter than ``classify_area`` when used with lists
    of jobs: a certame with Assistente Social + Administrativo + Saúde should
    not collapse to whichever keyword appears first.
    """
    text = ' '.join([value or '' for value in values]).lower()
    hits: set[str] = set()
    for area, keywords in AREA_RULES:
        if any(keyword in text for keyword in keywords):
            hits.add(area)
    if not hits and any(token in text for token in ['jovem aprendiz', 'nível médio', 'nivel medio', 'ensino médio', 'ensino medio']):
        hits.add('nivel_medio_tecnico')
    return hits


def classify_area_from_many(candidates: list[str] | tuple[str, ...], *context: str | None) -> str | None:
    """Classify certames that may contain several cargos.

    If several real career areas appear in the job list, return ``multiplas``.
    If all jobs point to one area, return it. Falls back to context only when
    job titles do not provide any signal.
    """
    hits: set[str] = set()
    for candidate in candidates:
        hits.update(detect_area_hits(candidate))

    # Ignore generic nivel_medio_tecnico when stronger areas were found.
    strong_hits = {hit for hit in hits if hit != 'nivel_medio_tecnico'}
    if len(strong_hits) >= 2:
        return 'multiplas'
    if len(strong_hits) == 1:
        return next(iter(strong_hits))
    if hits:
        return next(iter(hits))
    return classify_area(*context)


def build_hash(data: dict[str, Any]) -> str:
    raw = json.dumps(data, ensure_ascii=False, sort_keys=True, default=str)
    return hashlib.sha256(raw.encode('utf-8')).hexdigest()


def unwrap_pdf_url(url: str | None) -> str | None:
    """Return the direct PDF URL when a site wraps it in a reader URL."""
    if not url:
        return None
    parsed = urlparse(url)
    query = parse_qs(parsed.query)
    for key in ('pdf', 'arquivo', 'file', 'url'):
        values = query.get(key)
        if values:
            candidate = unquote(values[0])
            if candidate.lower().endswith('.pdf') or '.pdf' in candidate.lower():
                return candidate
    return url


def extract_pdf_link(soup: BeautifulSoup, base_url: str) -> str | None:
    """Find the most likely edital PDF.

    Prefer direct/main edital links and avoid errata/results/appeals when there
    is a better option. Also unwrap reader URLs like leitor-rybena?pdf=...
    so the PDF downloader receives application/pdf instead of HTML.
    """
    preferred: list[str] = []
    fallback: list[str] = []
    bad_terms = [
        'errata', 'resultado', 'recurso', 'gabarito', 'homologa', 'convoca',
        'lista', 'laudo', 'definitiva', 'preliminar', 'isencao', 'isenção',
        'comunicado', 'decisao', 'decisão', 'local de prova', 'julgamento',
        'cronograma', 'ética', 'etica', 'termos', 'instruc', 'formulário',
        'formulario', 'anexo',
    ]
    good_terms = ['edital', 'consolidado', 'retificado', 'retificada', 'conforme errata']
    for anchor in soup.select('a[href]'):
        href = anchor.get('href')
        url = unwrap_pdf_url(normalize_url(base_url, href))
        if not url:
            continue
        text = clean(anchor.get_text(' ', strip=True)) or ''
        lowered = f'{text} {url}'.lower()
        looks_download = '.pdf' in lowered or 'download' in lowered or 'arquivo' in lowered or 'leitor-rybena' in lowered
        if not looks_download:
            continue
        if any(key in lowered for key in good_terms) and not any(bad in lowered for bad in bad_terms if bad not in {'errata'}):
            preferred.append(url)
        elif any(key in lowered for key in good_terms):
            # Use edital-conforme-errata only if nothing cleaner exists.
            fallback.insert(0, url)
        elif not any(bad in lowered for bad in bad_terms):
            fallback.append(url)
    return preferred[0] if preferred else (fallback[0] if fallback else None)


def extract_pdf_fields_if_possible(edital_url: str | None, *, title: str | None, orgao: str | None, client: httpx.Client) -> tuple[dict[str, Any], dict[str, Any], str | None, datetime | None]:
    pdf_payload: dict[str, Any] = {'ok': False, 'url': edital_url, 'error': None, 'pages': None, 'text_hash': None}
    fields: dict[str, Any] = {
        'cargo': None,
        'area': None,
        'cidade': None,
        'uf': None,
        'vagas': None,
        'salario_min': None,
        'salario_max': None,
        'escolaridade': None,
        'taxa': None,
        'prova_data': None,
        'raw_pdf_fields': {},
    }
    excerpt = None
    extracted_at = None
    if not edital_url:
        return pdf_payload, fields, excerpt, extracted_at
    extraction = extract_pdf_text_from_url(edital_url, client=client)
    pdf_payload.update({'ok': extraction.ok, 'error': extraction.error, 'pages': extraction.pages, 'text_hash': extraction.text_hash})
    if extraction.ok and extraction.text:
        extracted_at = datetime.now(UTC)
        excerpt = extraction.text[:4000]
        parsed = parse_ibfc_pdf(extraction.text, title=title, orgao=orgao)
        fields.update(parsed)
    return pdf_payload, fields, excerpt, extracted_at


def build_summary(title: str, modalidade: str | None, status: str | None, inicio: datetime | None, fim: datetime | None, **extra: Any) -> str:
    parts = [title]
    if modalidade:
        parts.append(modalidade)
    if status:
        parts.append(f'Situação: {status}')
    if inicio or fim:
        parts.append(f'Inscrições: {inicio.isoformat() if inicio else "?"} a {fim.isoformat() if fim else "?"}')
    if extra.get('cargo'):
        parts.append(f'Cargo: {extra["cargo"]}')
    if extra.get('area'):
        parts.append(f'Área: {extra["area"]}')
    if extra.get('vagas') is not None:
        parts.append(f'Vagas: {extra["vagas"]}')
    return ' | '.join(parts)
