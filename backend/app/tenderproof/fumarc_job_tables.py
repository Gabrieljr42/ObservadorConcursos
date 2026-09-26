"""Complete FUMARC monthly-hours table; column totals must corroborate rows."""
import re
from app.tenderproof.job_tables import MONEY, _money

HEADER = re.compile(r'Cargo\s+Escolaridade/Requisitos\s+Carga\s+horária\s+Vagas\*\s+Total\s+de\s+vagas\s+Salário inicial\s+da carreira\s+AC\s+PCD\s+PN\s+PI\s+PQ', re.I)
CELL = r'(?:\d+|CR|-)'
ROW = re.compile(r'(?P<name>[^\d]+?)\s+(?P<requirements>Ensino\s+[\s\S]+?)\s+'
    r'(?P<hours>\d{1,3})\s+horas/mês\s+'
    + r'\s+'.join(r'(?P<'+key+'>'+CELL+r')' for key in ('ac','pcd','pn','pi','pq','total'))
    + r'\s+R\$\s*(?P<salary>'+MONEY+r')(?=\s|$)', re.I)


def extract_fumarc_tables(pages):
    result, unresolved = [], []
    for page in pages:
        for header in HEADER.finditer(page.text):
            end = re.search(r'Legenda:\s*CR\s*>\s*Cadastro de Reserva\.', page.text[header.end():], re.I)
            if not end or page.error or page.truncated:
                unresolved.append((page, 'quadro FUMARC incompleto ou sem legenda CR'))
                continue
            body = page.text[header.end():header.end()+end.start()]
            rows = list(ROW.finditer(body))
            if not rows or ROW.sub('', body).strip():
                unresolved.append((page, 'linhas/colunas do quadro FUMARC ainda não interpretadas'))
                continue
            parsed = []
            for row in rows:
                cells = [row[key].upper() for key in ('ac','pcd','pn','pi','pq')]
                total = row['total'].upper()
                reserve = total == 'CR'
                numeric = [int(x) if x.isdigit() else 0 for x in cells]
                valid = (cells == ['CR','-','-','-','-']) if reserve else (
                    total.isdigit() and 'CR' not in cells and sum(numeric) == int(total))
                if (not valid or int(row['hours']) <= 0
                        or re.search(r'R\$|horas/mês', row['requirements'], re.I)):
                    unresolved.append((page, 'total de vagas ou jornada FUMARC inconsistente'))
                    parsed = []
                    break
                job = {'nome': ' '.join(row['name'].split()),
                       'requisitos': ' '.join(row['requirements'].split()),
                       'jornada': row['hours'] + ' horas/mês',
                       'vagas_imediatas': 0 if reserve else int(total),
                       'cadastro_reserva': reserve,
                       'remuneracao': _money(row['salary']), 'moeda': 'BRL',
                       'taxa_inscricao': None}
                parsed.append((job, page, header.group(0), row.group(0)))
            result.extend(parsed)
    names = [job['nome'] for job, *_ in result]
    if len(names) != len(set(names)):
        unresolved.extend((page, 'cargo repetido no quadro FUMARC') for _, page, _, _ in result)
        result = []
    return result, unresolved
