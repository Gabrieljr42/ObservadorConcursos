"""Parse complete, explicitly ordered job tables without proximity-based money matching.

The supported layout identifies salary and fee as separate columns. Unknown
layouts or partially parsed tables remain implementation work, never absent data.
"""
import re
from decimal import Decimal

HEADER = re.compile(r'Cargo\s+Vagas\s+Vencimentos\s+Carga\s+Horária\s+'
                    r'Escolaridade\s+e\s+Exigências\s+Taxa\s+de\s+inscrição', re.I)
SECTION = re.compile(r'^\s*\d+\.\s+[A-ZÁÉÍÓÚÂÊÔÃÕÇ][A-ZÁÉÍÓÚÂÊÔÃÕÇ ]{4,}$', re.M)
MONEY = r'(?:\d{1,3}(?:\.\d{3})+|\d+),\d{2}'
ROW = re.compile(
    r'(?P<name>[A-ZÁÉÍÓÚÂÊÔÃÕÇ][A-ZÁÉÍÓÚÂÊÔÃÕÇ /()–\-]+?)\s+'
    r'(?P<vacancies>\d+(?:\s*\+\s*CR)?|CR)\s+R\$\s*(?P<salary>'+MONEY+r')\s+'
    r'(?P<hours>\d{1,3}\s*h(?:oras)?\s+semanais\b[\s\S]*?)'
    r'(?P<requirements>Ensino\s+[\s\S]*?)\s+R\$\s*(?P<fee>'+MONEY+r')'
    r'(?=\s|$)')


def _money(value):
    return format(Decimal(value.replace('.', '').replace(',', '.')), '.2f')


def ordered_job_tables(pages):
    """Return (rows with page/header/row evidence, unresolved recognized tables).

    Complete table consumption is required. Continuations across pages require
    a separate layout contract and are explicitly unresolved here.
    """
    result, unresolved = [], []
    for page in pages:
        # Numbered prose profiles publish job data outside the table contract.
        # Surface this implementation gap instead of silently omitting cargos.
        if (re.search(r'^\s*\d+(?:\.\d+)*\s+CARGO\s+\d+\s*:', page.text, re.M | re.I)
                and re.search(r'REQUISITOS\s*:', page.text, re.I)
                and re.search(r'REMUNERA[ÇC][ÃA]O\s*:', page.text, re.I)):
            unresolved.append((page, 'perfis de cargos em texto; associação integral com vagas e taxas ainda pendente'))
        for header in HEADER.finditer(page.text):
            end = SECTION.search(page.text, header.end())
            if end is None:
                unresolved.append((page, 'tabela sem fim comprovado na mesma página'))
                continue
            body = page.text[header.end():end.start()]
            matches = list(ROW.finditer(body))
            remainder = ROW.sub('', body).strip()
            if not matches or remainder:
                unresolved.append((page, 'tabela publicada com linhas ou colunas ainda não interpretadas'))
                continue
            parsed = []
            for match in matches:
                vacancy = match['vacancies']
                job = {
                    'nome': ' '.join(match['name'].split()),
                    'vagas_imediatas': int(re.match(r'\d+', vacancy)[0]) if re.match(r'\d+', vacancy) else 0,
                    'cadastro_reserva': 'CR' in vacancy,
                    'remuneracao': _money(match['salary']),
                    'moeda': 'BRL',
                    'jornada': ' '.join(match['hours'].split()),
                    'requisitos': ' '.join(match['requirements'].split()),
                    'taxa_inscricao': _money(match['fee']),
                }
                parsed.append((job, page, header.group(0), match.group(0)))
            result.extend(parsed)
    names = [row[0]['nome'] for row in result]
    if len(names) != len(set(names)):
        unresolved.extend((row[1], 'cargo repetido requer conferência de escopo') for row in result)
        result = []
    return result, unresolved
