"""Schooling fee schedules with corroborating written amounts."""
import re
import unicodedata
from app.tenderproof.contracts import ExtractedField, FieldState

HEADER = re.compile(r'O valor correspondente à Taxa de Inscrição para cada cargo será de:', re.I)
ROW = re.compile(
    r'\s*[a-z]\)\s*Nível\s+(Médio/Técnico|Superior):\s*'
    r'R[$]\s*(\d+),00\s*\(([^)]+)\)\s*[;.]', re.I)


def _words(n):
    units = ['zero', 'um', 'dois', 'tres', 'quatro', 'cinco', 'seis', 'sete', 'oito', 'nove']
    tens = ['', '', 'vinte', 'trinta', 'quarenta', 'cinquenta', 'sessenta', 'setenta', 'oitenta', 'noventa']
    if n < 10:
        return units[n]
    if n < 20:
        return ['dez', 'onze', 'doze', 'treze', 'quatorze', 'quinze', 'dezesseis', 'dezessete', 'dezoito', 'dezenove'][n - 10]
    if n == 100:
        return 'cem'
    if 20 <= n < 100:
        return tens[n // 10] + (' e ' + units[n % 10] if n % 10 else '')
    if 100 < n < 1000:
        hundreds = ['', 'cento', 'duzentos', 'trezentos', 'quatrocentos', 'quinhentos', 'seiscentos', 'setecentos', 'oitocentos', 'novecentos']
        return hundreds[n // 100] + (' e ' + _words(n % 100) if n % 100 else '')
    return None


def extract_fees(artifact, pages, evidence):
    found, problem = [], None
    for page in pages:
        for header in HEADER.finditer(page.text):
            tail = page.text[header.end():]
            end = re.search(r'\n\s*\d+(?:\.\d+)+\.', tail)
            body = tail[:end.start()] if end else tail
            rows = list(ROW.finditer(body))
            snippet = page.text[header.start():header.end() + len(body)]
            found.append((page, snippet, rows))
            if page.error or page.truncated or not end or ROW.sub('', body).strip():
                problem = 'Tabela de taxas publicada; interpretação integral pendente'
            if len(rows) != 2 or {r[1].lower() for r in rows} != {'médio/técnico', 'superior'}:
                problem = 'Escolaridades da tabela de taxas ainda não interpretadas'
    if not found:
        return None
    values, conflict = [], False
    for page, snippet, rows in found:
        schedule = {}
        for row in rows:
            amount = int(row[2])
            written = ' '.join(row[3].lower().split())
            written = ''.join(c for c in unicodedata.normalize('NFD', written) if not unicodedata.combining(c))
            expected = _words(amount)
            if expected is None or amount <= 0:
                problem = 'Valor por extenso ainda não interpretado'
            elif written not in {_words(n) + ' reais' for n in range(2, 1000)}:
                problem = 'Valor por extenso ainda não interpretado'
            elif written != expected + ' reais':
                conflict = True
            schedule['superior' if row[1].lower() == 'superior' else 'medio_tecnico'] = str(amount) + '.00'
        values.append(schedule)
    conflict = conflict or any(value != values[0] for value in values[1:])
    state = FieldState.FAILED if problem else FieldState.CONFLICT if conflict else FieldState.SUPPORTED
    return ExtractedField(field_name='taxas_inscricao', state=state,
        value=values[0] if state == FieldState.SUPPORTED else None,
        reason=problem or ('Taxas divergentes entre numerais, texto por extenso ou tabelas; revisão necessária' if conflict else None),
        evidence=[evidence(artifact=artifact, page=p, snippet=s) for p, s, _ in found])
