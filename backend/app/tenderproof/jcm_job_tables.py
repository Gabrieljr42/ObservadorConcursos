"""Complete JCM tables with independent vacancy, salary, fee and exam columns."""
import re
from decimal import Decimal
from app.tenderproof.job_tables import MONEY, _money


HEADER = re.compile(
    r'Denominação\s+Vagas\s+Requisitos Mínimos\s*/\s+Escolaridade\s+'
    r'Venci-\s+mento\s+\(BASE\)\s+R\$\s+Carga\s+Horária\s+Semanal\s+'
    r'Taxa de\s+Inscrição\s+R\$\s+Provas\s+Ampla\s+Concorrência\s+PcD\s+'
    r'Tipo\s+Nº de\s+Questões\s+Pontos\s+Por\s+Questão\s+Por\s+Prova')
ROW_PREFIX = (r'(?P<name>[A-ZÀ-Ý][A-Za-zÀ-ÿ\s/()–-]+?)\s+'
              r'(?P<ac>\d+)\s+(?P<pcd>\d+|–)\s+')
REQUIREMENT_START = r'(?:Ensino|Formação|Curso|Superior|Alfabetizado|Ser Alfabetizado)\b'
ROW_START = re.compile(ROW_PREFIX + r'(?=' + REQUIREMENT_START + r')')
ROW = re.compile(
    ROW_PREFIX + r'(?P<requirements>' + REQUIREMENT_START + r'[A-Za-zÀ-ÿ\d\s/().,:;“”"-]*?)\s+'
    r'(?P<salary>'+MONEY+r')\s+(?P<hours>\d{1,3})\s*h\s+'
    r'(?P<fee>'+MONEY+r')\s+'
    r'(?P<subjects>[A-Za-zÀ-ÿ. \t]+(?:\n[A-Za-zÀ-ÿ. \t]+)*)\s+'
    r'(?P<exam_numbers>(?:\d+(?:,\d+)?\s+)+)'
    r'(?:(?:Prática\s+Apto\s*/\s*Inapto|Títulos\s+-\s+-\s+\d+,\d+)\s*)?')
END = re.compile(r'_{3,}\s*\n')


def extract_jcm_tables(pages):
    rows, unresolved = [], []
    for page in pages:
        if not re.search(r'Denominação\s+Vagas\s+Requisitos', page.text):
            continue
        headers = list(HEADER.finditer(page.text))
        if len(headers) != 1 or page.truncated or page.error:
            unresolved.append((page, 'quadro JCM com cabeçalho ou página incompleta'))
            continue
        header = headers[0]
        end = END.search(page.text, header.end())
        if not end:
            unresolved.append((page, 'fim do quadro JCM não comprovado'))
            continue
        body = page.text[header.end():end.start()]
        matches = list(ROW.finditer(body))
        # A missing salary/fee must not make the requirements swallow the next
        # job. Every recognized vacancy row must have its own complete match.
        if (not matches or any(ROW_START.search(m['requirements']) for m in matches)
                or ROW.sub('', body).strip()):
            unresolved.append((page, 'linhas do quadro JCM ainda não interpretadas integralmente'))
            continue
        parsed = []
        for match in matches:
            subjects = [s for s in match['subjects'].splitlines() if s.strip()]
            numbers = [Decimal(n.replace(',', '.')) for n in match['exam_numbers'].split()]
            n = len(subjects)
            if (len(numbers) != 3*n or any(numbers[i] != int(numbers[i]) for i in range(n))
                    or any(numbers[i]*numbers[n+i] != numbers[2*n+i] for i in range(n))):
                unresolved.append((page, 'colunas das provas não corroboram a separação da linha'))
                break
            if match['pcd'] == '–' and '– = Não há reserva imediata de vaga PcD' not in page.text[end.end():]:
                unresolved.append((page, 'marcador de vagas PcD sem legenda'))
                break
            parsed.append(({
                'nome': ' '.join(match['name'].split()),
                'vagas_imediatas': int(match['ac']) + (0 if match['pcd'] == '–' else int(match['pcd'])),
                'cadastro_reserva': None,
                'remuneracao': _money(match['salary']), 'moeda': 'BRL',
                'jornada': match['hours'] + ' h semanais',
                'requisitos': ' '.join(match['requirements'].split()),
                'taxa_inscricao': _money(match['fee']),
            }, page, header.group(0), match.group(0)))
        else:
            rows.extend(parsed)
    if len({r[0]['nome'] for r in rows}) != len(rows):
        unresolved.extend((r[1], 'cargo JCM repetido requer conferência de escopo') for r in rows)
    return rows, unresolved
