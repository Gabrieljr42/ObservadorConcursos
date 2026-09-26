"""Identity and direct registration periods in FAPED personnel notices."""
import re

from app.tenderproof.contracts import ExtractedField, FieldState

_TITLE = re.compile(r'^EDITAL DE PROCESSO SELETIVO SIMPLIFICADO\s+N[º°.o]*\s*(\d{1,4}/\d{4})\s*$', re.I | re.M)
_ORG = re.compile(r'^Funda[çc][ãa]o de Apoio [àa] Pesquisa e ao Desenvolvimento\s*[-–—]\s*FAPED\s*$', re.I | re.M)
_REG = re.compile(r'A inscri[çc][ãa]o ser[áa] realizada de\s+(?P<start>\d{2}/\d{2}/\d{4})\s+[aà]\s+(?P<end>\d{2}/\d{2}/\d{4})\s+at[ée]\s+(?:[01]?\d|2[0-3])h[0-5]\dmin\s*,', re.I)
_REG_PREFIX = re.compile(r'A inscri[çc][ãa]o ser[áa] realizada de\b', re.I)


def extract_faped_fields(candidate, artifact, pages, evidence, date_value):
    if candidate.source != 'faped_selection':
        return {}
    result = {}
    first = [p for p in pages if p.page_number == 1]
    observed = set(re.findall(r'\b\d{1,4}/\d{4}\b', candidate.title_observed or ''))
    titles = [(p, m) for p in first for m in _TITLE.finditer(p.text)]
    orgs = [(p, m) for p in first for m in _ORG.finditer(p.text)]
    for name, matches in (('titulo', titles), ('orgao', orgs)):
        valid = len(matches) == 1 and not matches[0][0].error and not matches[0][0].truncated
        if name == 'titulo':
            valid = valid and len(observed) == 1 and matches[0][1][1] in observed
        result[name] = ExtractedField(field_name=name, state=FieldState.SUPPORTED if valid else FieldState.FAILED,
            value=matches[0][1].group(0).strip() if valid else None,
            reason=None if valid else 'Identidade no cabeçalho FAPED exige conferência ou interpretação adicional',
            evidence=[evidence(artifact=artifact, page=p, snippet=m.group(0)) for p, m in matches])
    starts, ends, matches, invalid = set(), set(), [], False
    for page in pages:
        invalid |= len(list(_REG_PREFIX.finditer(page.text))) != len(list(_REG.finditer(page.text)))
        for match in _REG.finditer(page.text):
            start, end = date_value(match['start']), date_value(match['end'])
            invalid |= bool(page.error or page.truncated or not start or not end or (start and end and start > end))
            starts.add(start)
            ends.add(end)
            matches.append((page, match))
    for name, values in (('inscricao_inicio', starts), ('inscricao_fim', ends)):
        state = FieldState.FAILED if invalid or not matches else FieldState.CONFLICT if len(values) > 1 else FieldState.SUPPORTED
        result[name] = ExtractedField(field_name=name, state=state,
            value=next(iter(values)) if state == FieldState.SUPPORTED else None,
            reason=None if state == FieldState.SUPPORTED else 'Período direto de inscrição FAPED incompleto, inválido ou divergente; interpretação/conferência pendente',
            evidence=[evidence(artifact=artifact, page=p, snippet=m.group(0)) for p, m in matches])
    return result
