from __future__ import annotations

import re
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

AREA_RULES: dict[str, list[str]] = {
    'assistencia_social': ['assistente social', 'serviço social', 'servico social', 'cras', 'creas'],
    'administrativa': ['assistente administrativo', 'analista administrativo', 'auxiliar administrativo', 'administração', 'administracao'],
    'educacao': ['professor', 'pedagogo', 'educador', 'monitor escolar', 'docente'],
    'saude': ['enfermeiro', 'técnico de enfermagem', 'tecnico de enfermagem', 'médico', 'medico', 'fisioterapeuta', 'nutricionista', 'farmacêutico', 'farmaceutico'],
    'juridica': ['advogado', 'procurador', 'analista jurídico', 'analista juridico', 'direito'],
    'seguranca_publica': ['guarda municipal', 'policial', 'bombeiro', 'agente penitenciário', 'agente penitenciario'],
    'fiscal_tributaria': ['auditor fiscal', 'fiscal de tributos', 'fiscal tributário', 'fiscal tributario'],
    'tecnologia_informacao': ['técnico em informática', 'tecnico em informatica', 'analista de sistemas', 'desenvolvedor', 'programador', 'tecnologia da informação', 'tecnologia da informacao'],
    'engenharia_arquitetura': ['engenheiro', 'engenharia', 'arquiteto', 'arquitetura'],
    'contabilidade_financas': ['contador', 'contabilidade', 'financeiro', 'finanças', 'financas'],
    'psicologia': ['psicólogo', 'psicologo', 'psicologia'],
    'comunicacao': ['jornalista', 'publicitário', 'publicitario', 'comunicação', 'comunicacao'],
    'meio_ambiente': ['meio ambiente', 'ambiental', 'biólogo', 'biologo'],
}

CARGO_KEYWORDS = [
    'assistente', 'analista', 'técnico', 'tecnico', 'professor', 'médico', 'medico',
    'enfermeiro', 'engenheiro', 'fiscal', 'advogado', 'procurador', 'contador',
    'psicólogo', 'psicologo', 'jovem aprendiz', 'aprendiz', 'guarda municipal',
]

CARGO_LABEL_RE = re.compile(
    r'\b(?:cargo|emprego|fun[cç][aã]o)\b\s*(?:p[uú]blico)?\s*[:\-–]\s*([^\n]{3,120})',
    flags=re.IGNORECASE,
)
MONEY_RE = re.compile(r'R\$\s*\d{1,3}(?:\.\d{3})*,\d{2}')
DATE_RE = re.compile(r'\b\d{2}/\d{2}/\d{4}\b')
CITY_UF_RE = re.compile(r'\b([A-ZÁÉÍÓÚÂÊÔÃÕÇ][A-Za-zÀ-ÿ .\'’\-]{2,80})\s*[-/]\s*([A-Z]{2})\b')


def parse_ibfc_pdf(text: str, *, title: str | None = None, orgao: str | None = None) -> dict[str, Any]:
    normalized = _normalize_text(text)
    search_text = '\n'.join(normalized.splitlines()[:2500])
    first_pages_text = normalized[:12000]

    is_jovem_aprendiz = _is_jovem_aprendiz(first_pages_text, title)
    cargos = _extract_cargos(search_text, title=title, is_jovem_aprendiz=is_jovem_aprendiz)
    escolaridades = _extract_escolaridades(search_text)
    salarios = _extract_money_values_near(search_text, ['vencimento', 'salário', 'salario', 'remuneração', 'remuneracao'])
    taxa = _extract_taxa(search_text)
    vagas_total = _extract_total_vagas(search_text)
    prova_data = _extract_prova_data(search_text)
    cidade, uf = _extract_city_uf(search_text)

    cargo = cargos[0] if len(cargos) == 1 else None
    area = _classify_area(' '.join([title or '', orgao or '', cargo or '', ' '.join(cargos[:10])]))
    if is_jovem_aprendiz and not area:
        area = 'nivel_medio_tecnico'

    salario_min = min(salarios) if salarios else None
    salario_max = max(salarios) if salarios else None
    escolaridade = escolaridades[0] if len(escolaridades) == 1 else None

    return {
        'cargo': cargo,
        'area': area,
        'cidade': cidade,
        'uf': uf,
        'vagas': vagas_total,
        'salario_min': salario_min,
        'salario_max': salario_max,
        'escolaridade': escolaridade,
        'taxa': taxa,
        'prova_data': prova_data,
        'raw_pdf_fields': {
            'cargos_extraidos': cargos[:50],
            'escolaridades_extraidas': escolaridades,
            'salarios_extraidos': [str(value) for value in salarios[:30]],
            'taxas_extraidas': [str(taxa)] if taxa is not None else [],
            'vagas_total': vagas_total,
            'cidade_extraida': cidade,
            'uf_extraida': uf,
            'prova_data': prova_data.isoformat() if prova_data else None,
            'area_classificada': area,
            'jovem_aprendiz_detectado': is_jovem_aprendiz,
        },
    }


def _normalize_text(value: str) -> str:
    value = value.replace('\xa0', ' ')
    value = re.sub(r'(?<=\w)-\s*\n\s*(?=\w)', '', value)  # joins words split by hyphen at line break
    value = re.sub(r'[ \t]+', ' ', value)
    value = re.sub(r'\n{3,}', '\n\n', value)
    return value.strip()


def _is_jovem_aprendiz(text: str, title: str | None) -> bool:
    lowered = ' '.join([title or '', text[:6000]]).lower()
    return any(token in lowered for token in ['jovem aprendiz', 'formação para o mundo do trabalho', 'formacao para o mundo do trabalho'])


def _extract_cargos(text: str, *, title: str | None, is_jovem_aprendiz: bool) -> list[str]:
    if is_jovem_aprendiz:
        return ['Jovem Aprendiz / Formação para o Mundo do Trabalho']

    found: list[str] = []
    for match in CARGO_LABEL_RE.finditer(text):
        value = _clean_candidate(match.group(1))
        if _looks_like_cargo(value):
            found.append(value)

    # Common IBFC tables may have uppercase cargo names without an explicit label.
    for line in text.splitlines():
        candidate = _clean_candidate(line)
        if not candidate or len(candidate) > 90:
            continue
        lowered = candidate.lower()
        if any(keyword in lowered for keyword in CARGO_KEYWORDS):
            if _looks_like_cargo(candidate):
                found.append(candidate.title() if candidate.isupper() else candidate)

    # Last fallback: some cards carry the only useful role in the title.
    if title:
        title_candidate = _clean_candidate(title.split(' - ')[-1])
        if any(keyword in title_candidate.lower() for keyword in CARGO_KEYWORDS) and _looks_like_cargo(title_candidate):
            found.insert(0, title_candidate)

    return _unique_preserve_order(found)[:80]


def _looks_like_cargo(value: str) -> bool:
    lowered = value.lower()
    blocked_fragments = [
        'edital', 'cronograma', 'inscrição', 'inscricao', 'recurso', 'prova objetiva',
        'conteúdo', 'conteudo', 'laudo médico', 'laudo medico', 'fiscal de sala',
        'examinador', 'candidato', 'devidamente preenchidos', 'orientações', 'orientacoes',
        'responsabilidade exclusiva', 'atendimento especial', 'diagnosticada', 'envio do laudo',
    ]
    if any(item in lowered for item in blocked_fragments):
        return False
    if len(value) < 3 or len(value) > 120:
        return False
    if DATE_RE.search(value) or MONEY_RE.search(value):
        return False
    if value.count('.') >= 2:
        return False
    # Most real job names are short noun phrases, not full legal/instructional sentences.
    if len(value.split()) > 12:
        return False
    return True


def _clean_candidate(value: str) -> str:
    value = re.sub(r'\s+', ' ', value).strip(' :-–—\t')
    value = re.sub(r'^(?:cargo|emprego|fun[cç][aã]o)\s*(?:p[uú]blico)?\s*[:\-–]\s*', '', value, flags=re.IGNORECASE)
    value = re.sub(r'\s+\d+$', '', value).strip()
    return value


def _extract_escolaridades(text: str) -> list[str]:
    patterns = [
        ('Ensino Fundamental', r'ensino fundamental'),
        ('Ensino Médio/Técnico', r'ensino m[eé]dio\s*/?\s*t[eé]cnico|nível m[eé]dio\s*/?\s*t[eé]cnico|nivel medio\s*/?\s*tecnico'),
        ('Ensino Médio', r'ensino m[eé]dio|nível m[eé]dio|nivel medio'),
        ('Ensino Técnico', r'ensino t[eé]cnico|curso t[eé]cnico'),
        ('Ensino Superior', r'ensino superior|nível superior|nivel superior|gradua[cç][aã]o'),
        ('Pós-graduação', r'p[oó]s[- ]gradua[cç][aã]o|especializa[cç][aã]o'),
    ]
    lowered = text.lower()
    found = [label for label, pattern in patterns if re.search(pattern, lowered, flags=re.IGNORECASE)]
    return _unique_preserve_order(found)


def _extract_money_values_near(text: str, anchors: list[str]) -> list[Decimal]:
    values: list[Decimal] = []
    lines = text.splitlines()
    lowered_lines = [line.lower() for line in lines]

    for anchor in anchors:
        anchor_lower = anchor.lower()
        for idx, lowered in enumerate(lowered_lines):
            if anchor_lower not in lowered:
                continue
            same_line_values = [_parse_money(match.group(0)) for match in MONEY_RE.finditer(lines[idx])]
            same_line_values = [value for value in same_line_values if value is not None]
            if same_line_values:
                values.extend(same_line_values)
                continue
            if idx + 1 < len(lines):
                values.extend(_parse_money(match.group(0)) for match in MONEY_RE.finditer(lines[idx + 1]))

    if values:
        return _unique_decimals([value for value in values if value is not None])

    lowered = text.lower()
    for anchor in anchors:
        start = 0
        while True:
            idx = lowered.find(anchor.lower(), start)
            if idx == -1:
                break
            window = text[max(0, idx - 120): idx + 250]
            values.extend(_parse_money(match.group(0)) for match in MONEY_RE.finditer(window))
            start = idx + len(anchor)
    return _unique_decimals([value for value in values if value is not None])


def _extract_taxa(text: str) -> Decimal | None:
    lowered = text.lower()
    if re.search(r'taxa\s+de\s+inscri[cç][aã]o\s+gratuita|inscri[cç][aã]o\s+gratuita', lowered, flags=re.IGNORECASE):
        return Decimal('0')
    taxas = _extract_money_values_near(text, ['taxa de inscrição', 'taxa de inscricao', 'valor da inscrição', 'valor da inscricao'])
    return min(taxas) if taxas else None


def _parse_money(value: str) -> Decimal | None:
    normalized = value.replace('R$', '').replace('.', '').replace(',', '.').strip()
    try:
        return Decimal(normalized)
    except (InvalidOperation, ValueError):
        return None


def _extract_total_vagas(text: str) -> int | None:
    # Compact jobs tables often expose the official TOTAL column as "08 + CR".
    jobs_start = re.search(r'\bC[ÓO]D\s+EMPREGOS\b', text, flags=re.IGNORECASE)
    if jobs_start:
        jobs_end = re.search(
            r'\bAP\s*[–-]\s*Ampla\s+Concorr[êe]ncia\b',
            text[jobs_start.start():],
            flags=re.IGNORECASE,
        )
        section_end = jobs_start.start() + jobs_end.start() if jobs_end else min(len(text), jobs_start.start() + 12000)
        section = text[jobs_start.start():section_end]
        totals: list[int] = []
        for line in section.splitlines()[1:]:
            # The row may contain AP/PcD/reserve cells before the official
            # TOTAL column. In the extracted table, TOTAL is the last N + CR.
            matches = re.findall(r'\b(\d{1,4})\s*\+\s*CR\b', line, flags=re.IGNORECASE)
            if matches:
                totals.append(int(matches[-1]))
        if totals and 0 < sum(totals) < 10000:
            return sum(totals)

    # FUNCERN-style annex: each Cargo block has a TOTAL row. Sum the total
    # column only, avoiding double-counting its AP/PcD/racial components.
    annex_match = re.search(r'\bANEXO\s+I\b\s*\n\s*QUADRO\s+DE\s+CARGOS', text, flags=re.IGNORECASE)
    if annex_match:
        annex_end = re.search(r'\bANEXO\s+II\b', text[annex_match.end():], flags=re.IGNORECASE)
        end = annex_match.end() + annex_end.start() if annex_end else min(len(text), annex_match.end() + 100000)
        annex = text[annex_match.start():end]
        total_values: list[int] = []
        for block in re.split(r'\bCargo\s+\d+\s*:', annex, flags=re.IGNORECASE)[1:]:
            total_line = re.search(r'\bTOTAL\b\s*\n\s*([^\n]+)', block, flags=re.IGNORECASE)
            if not total_line:
                continue
            value = total_line.group(1)
            with_reserve = re.search(r'\b(\d{1,4})\s*\+\s*\d*\s*CR\b', value, flags=re.IGNORECASE)
            if with_reserve:
                total_values.append(int(with_reserve.group(1)))
                continue
            numbers = [int(number) for number in re.findall(r'\b\d{1,4}\b', value)]
            if numbers:
                total_values.append(numbers[-1])
        if total_values and 0 < sum(total_values) < 10000:
            return sum(total_values)

    # IESES/SCGÁS-style Annex I: one row per numeric job code, with the
    # vacancy quantity immediately before the R$ salary column.
    coded_annex = re.search(
        r'\bANEXO\s+I\b[^\n]*\bC[ÓO]DIGO\b[^\n]*\bCARGO\b[^\n]*\bVAGAS\b[^\n]*\bSAL[ÁA]RIO\b',
        text,
        flags=re.IGNORECASE,
    )
    if coded_annex:
        coded_end = re.search(
            r'\b(?:BENEF[ÍI]CIOS|ANEXO\s+II)\b',
            text[coded_annex.end():],
            flags=re.IGNORECASE,
        )
        end = coded_annex.end() + coded_end.start() if coded_end else min(len(text), coded_annex.end() + 10000)
        section = text[coded_annex.end():end]
        quantities: list[int] = []
        for line in section.splitlines():
            row = re.match(
                r'^\s*\d{3,6}\s+.+?\s+(\d{1,4})\s+R\$\s*\d',
                line,
                flags=re.IGNORECASE,
            )
            if row:
                quantities.append(int(row.group(1)))
        if quantities and 0 < sum(quantities) < 10000:
            return sum(quantities)

    # Only trust occurrences in the same short line/row. Do not let \s+ cross
    # headings like "2. DO CURSO E VAGAS\nVagas 40" and capture the section number.
    line_patterns = [
        r'\bVagas\b\s*[:\-–]?\s*(\d{1,5})\b',
        r'\bTotal\s+de\s+vagas\b\s*[:\-–]?\s*(\d{1,5})\b',
        r'\b(\d{1,5})\s+vagas\s+(?:imediatas|ofertadas|previstas)\b',
    ]
    for line in text.splitlines():
        clean_line = re.sub(r'\s+', ' ', line).strip()
        if not clean_line:
            continue
        for pattern in line_patterns:
            match = re.search(pattern, clean_line, flags=re.IGNORECASE)
            if match:
                value = int(match.group(1))
                if 0 < value < 10000:
                    return value

    # Fallback for wrapped text near an explicit "DO CURSO"/"QUADRO" section.
    for match in re.finditer(r'\bVagas\b\s*[:\-–]?\s*(\d{1,5})\b', text, flags=re.IGNORECASE):
        value = int(match.group(1))
        if 0 < value < 10000:
            return value
    return None


def _extract_city_uf(text: str) -> tuple[str | None, str | None]:
    patterns = [
        r'todas\s+as\s+etapas.{0,120}?realizadas\s+em\s+([A-ZÁÉÍÓÚÂÊÔÃÕÇ][A-Za-zÀ-ÿ .\'’\-]{2,80})\s*[-/]\s*([A-Z]{2})',
        r'curso\s+ser[aá]\s+realizado\s+em\s+([A-ZÁÉÍÓÚÂÊÔÃÕÇ][A-Za-zÀ-ÿ .\'’\-]{2,80})\s*[-/]\s*([A-Z]{2})',
        r'local\s+[^\n]{0,80}?em\s+([A-ZÁÉÍÓÚÂÊÔÃÕÇ][A-Za-zÀ-ÿ .\'’\-]{2,80})\s*[-/]\s*([A-Z]{2})',
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE | re.DOTALL)
        if match:
            return _clean_city(match.group(1)), match.group(2).upper()

    match = CITY_UF_RE.search(text[:12000])
    if match:
        return _clean_city(match.group(1)), match.group(2).upper()
    return None, None


def _clean_city(value: str) -> str:
    value = re.sub(r'\s+', ' ', value).strip(' .:-–—')
    value = re.sub(r'^(?:a|o|as|os|em)\s+', '', value, flags=re.IGNORECASE)
    return value


def _extract_prova_data(text: str) -> datetime | None:
    patterns = [
        r'prova(?:s)?\s+objetiva(?:s)?.{0,160}?(\d{2}/\d{2}/\d{4})',
        r'aplica[cç][aã]o\s+da(?:s)?\s+prova(?:s)?.{0,160}?(\d{2}/\d{2}/\d{4})',
        r'data\s+da(?:s)?\s+prova(?:s)?.{0,160}?(\d{2}/\d{2}/\d{4})',
        r'realiza[cç][aã]o\s+da\s+1[ªa]\s+etapa.{0,160}?(\d{2}/\d{2}/\d{4})',
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE | re.DOTALL)
        if match:
            try:
                return datetime.strptime(match.group(1), '%d/%m/%Y').replace(tzinfo=UTC)
            except ValueError:
                return None
    return None


def _classify_area(text: str) -> str | None:
    lowered = text.lower()
    for area, keywords in AREA_RULES.items():
        if any(keyword in lowered for keyword in keywords):
            return area
    return None


def _unique_preserve_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    unique: list[str] = []
    for value in values:
        key = value.strip().lower()
        if not key or key in seen:
            continue
        seen.add(key)
        unique.append(value.strip())
    return unique


def _unique_decimals(values: list[Decimal]) -> list[Decimal]:
    seen: set[str] = set()
    unique: list[Decimal] = []
    for value in values:
        key = str(value)
        if key in seen:
            continue
        seen.add(key)
        unique.append(value)
    return unique
