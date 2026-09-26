"""Shared job profiles: preserve a joint vacancy row without dividing its total."""
import re
from app.tenderproof.contracts import ExtractedField, FieldState
from app.tenderproof.job_tables import MONEY, _money


def norm(value):
    return ' '.join(value.split()).casefold().replace(' e de ', ' e ')


def extract_joint_jobs(artifact, pages, evidence):
    headings = [(p, m) for p in pages for m in re.finditer(r'^\s*\d+ DOS CARGOS DE ', p.text, re.M)]
    if not headings:
        return None
    snippets = [(p, m.group()) for p, m in headings]
    def result(reason=None, value=None):
        return ExtractedField(field_name='cargos', state=FieldState.FAILED if reason else FieldState.SUPPORTED,
            value=value, reason=reason, evidence=[evidence(artifact=artifact, page=p, snippet=s) for p,s in snippets])
    def fail(reason):
        return result('Perfis conjuntos publicados; interpretação pendente: ' + reason)
    if len(headings) != 1 or any(p.error or p.truncated for p in pages) or [p.page_number for p in pages] != list(range(1,len(pages)+1)):
        return fail('seção repetida ou páginas incompletas')
    page, heading = headings[0]
    profile = re.match(r'(?P<name>[^:]+?)\nREQUISITOS?: (?P<req>[\s\S]+?)\nDESCRIÇÃO SUMÁRIA DAS ATIVIDADES: [\s\S]+?\nSUBSÍDIO: R\$ (?P<salary>' + MONEY + r') \([^\n]+\)\.\s*\n\d+ DOS REQUISITOS BÁSICOS PARA A INVESTIDURA NO CARGO', page.text[heading.end():])
    if not profile:
        return fail('limites do perfil, requisitos ou subsídio não corroborados')
    snippets.append((page, profile.group()))
    header = (r'Cargos\s+Vagas para\s+ampla\s+concorrência\s+'
        r'Vagas\s+reservadas\s+para\s+candidatos\s+com\s+deficiência\s+'
        r'Vagas\s+reservadas\s+para\s+candidatos\s+negros\s+'
        r'Vagas\s+reservadas\s+para\s+candidatos\s+indígenas\s+'
        r'Vagas\s+reservadas\s+para\s+candidatos\s+quilombolas\s+Total\s+')
    pattern = re.compile(header + r'(?P<name>[^\d]+?)\s+(?P<values>\d+ \+ CR(?:\s+\d+ \+ CR){5})\s+CR = cadastro de reserva\.\s+\d+\.\d+ DA LOTAÇÃO')
    tables = [(p,m) for p in pages for m in pattern.finditer(p.text)]
    if len(tables)!=1:
        return fail('quadro integral de vagas e reservas não reconhecido')
    table_page, table = tables[0]
    if table_page.page_number != page.page_number+1 or norm(table['name']) != norm(profile['name']):
        return fail('vínculo entre perfil conjunto e quadro de vagas não comprovado')
    numbers = [int(v) for v in re.findall(r'\d+',table['values'])]
    if sum(numbers[:-1]) != numbers[-1]:
        return fail('total de vagas diverge das modalidades')
    snippets.append((table_page, table.group()))
    fee_pattern = re.compile(r'^\s*(\d+) DAS INSCRIÇÕES PRELIMINARES NO CONCURSO PÚBLICO\s*\n\1\.1 TAXA: R\$ (?P<fee>'+MONEY+r')\.[ \t]*(?=\n|$)',re.M)
    fees = [(p,m) for p in pages for m in fee_pattern.finditer(p.text)]
    if len(fees)!=1 or sum(len(re.findall(r'\bTAXA\s*:',p.text)) for p in pages)!=1:
        return fail('taxa única de inscrição não comprovada')
    fee_page, fee = fees[0]
    snippets.append((fee_page,fee.group()))
    if any(re.search(r'JORNADA|CARGA HOR[ÁA]RIA',p.text) for p in pages):
        return fail('jornada publicada exige associação ao grupo')
    return result(value=[{'nome':' '.join(table['name'].split()),
        'vagas_imediatas':numbers[-1], 'cadastro_reserva':True,
        'remuneracao':_money(profile['salary']), 'moeda':'BRL', 'jornada':None,
        'requisitos':' '.join(profile['req'].split()), 'taxa_inscricao':_money(fee['fee'])}])
