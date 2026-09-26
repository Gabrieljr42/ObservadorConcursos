"""FAPED vacancy table and its split, explicitly named requirements table."""
import re
from app.tenderproof.contracts import ExtractedField, FieldState
from app.tenderproof.job_tables import MONEY, _money

HEADER = re.compile(r'Cargo\s+N\.[º°o]\s+de Vagas\s+Carga-horária\s+Salário Base\s*\(bruto\)', re.I)
ROW = re.compile(r'\s*(?P<name>[A-Za-zÀ-ÿ][A-Za-zÀ-ÿ \n-]+?)\s+(?P<vacancies>\d+)\s+(?P<hours>\d{1,2})\s+horas diárias\s+R\$\s*(?P<salary>' + MONEY + r')\s*', re.I)
REQ = re.compile(r'Cargo\s+Pré-requisito\s*\n(?P<body>I\.[\s\S]+)$', re.I)


def _roman(number):
    result = ''
    for value, letter in ((100,'C'),(90,'XC'),(50,'L'),(40,'XL'),(10,'X'),(9,'IX'),(5,'V'),(4,'IV'),(1,'I')):
        while number >= value:
            result += letter
            number -= value
    return result


def extract_jobs(artifact, pages, evidence):
    tables = [(p, m) for p in pages for m in HEADER.finditer(p.text)]
    if not tables:
        return None
    snippets = [(p, m.group(0)) for p, m in tables]
    def pending(reason):
        return ExtractedField(field_name='cargos', state=FieldState.FAILED,
            reason='Quadro FAPED publicado; interpretação integral pendente: ' + reason,
            evidence=[evidence(artifact=artifact, page=p, snippet=s) for p, s in snippets])
    if len(tables) != 1:
        return pending('quadros concorrentes')
    page, header = tables[0]
    row = ROW.fullmatch(page.text[header.end():])
    if not row or page.error or page.truncated:
        return pending('linhas ou limite do quadro de vagas não interpretados')
    if not 1 <= int(row['hours']) <= 24 or int(row['vacancies']) < 1:
        return pending('jornada ou quantidade de vagas inválida')
    snippets.append((page, row.group(0)))
    name = ' '.join(row['name'].split())
    requirements = [(p, m) for p in pages for m in REQ.finditer(p.text)]
    if len(requirements) != 1:
        return pending('quadro de pré-requisitos não é único')
    req_page, req = requirements[0]
    next_pages = [p for p in pages if p.page_number == req_page.page_number + 1]
    if len(next_pages) != 1 or any(p.error or p.truncated for p in [req_page, *next_pages]):
        return pending('continuação de requisitos incompleta')
    continuation_page = next_pages[0]
    name_pattern = r'\s+'.join(re.escape(word) for word in name.split())
    continuation = re.search(r'^' + name_pattern + r'\s+Profissional de Nível\s+Superior\s*\n(?P<body>[\s\S]+)$', continuation_page.text, re.M | re.I)
    if not continuation:
        return pending('continuação sem nome de cargo e escolaridade corroborados')
    combined = req['body'].rstrip() + ' ' + continuation['body'].strip()
    if re.search(r'^\s*\d+(?:\.\d+)+\.|https?://|R\$|\bDA INSCRI[ÇC][ÃA]O\b', combined, re.M | re.I):
        return pending('texto de outra seção misturado aos requisitos')
    items = list(re.finditer(r'(?:^|\n)([IVXLCDM]+)\.\s+([^\n]+(?:\n(?![IVXLCDM]+\.\s)[^\n]+)*)', combined))
    if (not items or [m[1] for m in items] != [_roman(i) for i in range(1, len(items) + 1)]
            or ''.join(m.group(0) for m in items) != combined or not combined.rstrip().endswith('.')):
        return pending('sequência ou término dos requisitos não corroborados')
    snippets.extend([(req_page, req.group(0)), (continuation_page, continuation.group(0))])
    job = {'nome': name, 'vagas_imediatas': int(row['vacancies']), 'cadastro_reserva': None,
        'remuneracao': _money(row['salary']), 'moeda': 'BRL', 'jornada': row['hours'] + ' horas diárias',
        'requisitos': 'Profissional de Nível Superior. ' + ' '.join(combined.split()), 'taxa_inscricao': None}
    return ExtractedField(field_name='cargos', state=FieldState.SUPPORTED, value=[job],
        evidence=[evidence(artifact=artifact, page=p, snippet=s) for p, s in snippets])
