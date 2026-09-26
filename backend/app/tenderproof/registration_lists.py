"""Distinct registration lists must not collapse to a single closing date."""
import re
from app.tenderproof.contracts import ExtractedField, FieldState

HEAD = r'^[ \t]*([A-Za-zÀ-ÿ]+)[ \t]+lista[ \t]+de[ \t]+Candidatos[ \t]*$'


def extract_lists(artifact, pages, evidence, date_token, date_value):
    header = re.compile(HEAD, re.I | re.M)
    row = re.compile(HEAD + r'\s*Começo das inscrições:[ \t]*(' + date_token + r')[^\n]*\n'
        r'Fim das Inscrições:[ \t]*(?P<end>' + date_token + r'|As inscrições ficarão abertas até o novo edital de inscrições)', re.I | re.M)
    found, expected, invalid = [], 0, False
    for page in pages:
        expected += len(list(header.finditer(page.text)))
        for match in row.finditer(page.text):
            start, end = date_value(match[2]), date_value(match['end'])
            open_end = match['end'].lower().startswith('as inscrições ficarão abertas')
            invalid |= bool(page.error or page.truncated or not start or (not end and not open_end) or (end and start > end))
            found.append((page,match.group(0),{'lista':match[1].lower(),'inicio':start,'fim':end,
                'condicao_fim':'até novo edital de inscrições' if open_end else None}))
    if not expected:
        return None
    values = {}
    conflict = False
    for _,_,value in found:
        if value['lista'] in values and values[value['lista']] != value:
            conflict = True
        values[value['lista']] = value
    failed = invalid or len(found) != expected
    state = FieldState.FAILED if failed else FieldState.CONFLICT if conflict else FieldState.SUPPORTED
    return ExtractedField(field_name='inscricao_listas',state=state,
        value=list(values.values()) if state == FieldState.SUPPORTED else None,
        reason='Listas de inscrição publicadas; interpretação completa pendente' if failed else
            'Períodos divergentes para a mesma lista de candidatos' if conflict else None,
        evidence=[evidence(artifact=artifact,page=p,snippet=s) for p,s,_ in found])
