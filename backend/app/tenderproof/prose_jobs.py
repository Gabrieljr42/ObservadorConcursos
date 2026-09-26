"""Complete numbered job profiles joined to an explicit vacancy matrix.

This contract accepts one observed Cebraspe layout; incomplete or different
layouts fail explicitly. Evidence remains split by original physical page.
"""
import re
from app.tenderproof.job_tables import _money, MONEY


def _norm(text):
    return ' '.join(text.split()).casefold()


def extract_prose_jobs(pages):
    if (not pages or any(p.error or p.truncated for p in pages)
            or [p.page_number for p in pages]!=list(range(1,len(pages)+1))):
        return [],[], 'páginas incompletas ou fora de ordem'
    text=''; spans=[]
    for page in pages:
        start=len(text); text+=page.text; spans.append((start,len(text),page)); text+='\n'
    def evidence(start,end):
        return [(p,p.text[max(0,start-a):min(b,end)-a])
                for a,b,p in spans if max(a,start)<min(b,end)]
    def fail(reason):
        return [],[],reason
    headings=list(re.finditer(r'^\s*(\d+) DOS CARGOS\s*$',text,re.M))
    if len(headings)!=1:
        return fail('seção completa de perfis de cargos não identificada')
    heading=headings[0]
    end=re.search(r'^\s*\d+ [A-ZÀ-Ý][A-ZÀ-Ý ]{5,}$',text[heading.end():],re.M)
    if not end:
        return fail('fim da seção de cargos não comprovado')
    start=heading.end(); stop=start+end.start(); body=text[start:stop]
    profile=re.compile(
        r'\s*'+re.escape(heading[1])+r'\.\d+ CARGO (?P<id>\d+): (?P<name>[^\n]+)\n'
        r'REQUISITOS?: (?P<requirements>[\s\S]+?)\nATRIBUI[ÇC][ÕO]ES: [\s\S]+?'
        r'\nREMUNERA[ÇC][ÃA]O: R\$ (?P<salary>'+MONEY+r')\.\s*'
        r'CARGA HOR[ÁA]RIA: (?P<hours>\d+ horas semanais)\.\s*')
    matches=list(profile.finditer(body))
    if not matches or profile.sub('',body).strip():
        return fail('perfis incompletos ou formato de requisitos/remuneração não suportado')
    ids=[m['id'] for m in matches]
    if len(set(ids))!=len(ids):return fail('identificadores de cargo repetidos')
    matrix=re.compile(
        r'Cargo/Área\s+Vagas imediatas\s+Cadastro de Reserva\s+'
        r'\(excluídas as vagas\s+imediatas\)\s+Total\s+\(incluídas\s+as vagas\s+'
        r'imediatas\) AC PCD\s+PPIQ Total AC PCD\s+PPIQ Total\s+'
        r'(?P<rows>[\s\S]+?)'
        r'\*Não há vaga para o provimento imediato, mantendo-se o cadastro de reserva\.')
    matrices=list(matrix.finditer(text))
    if len(matrices)!=1:return fail('quadro de vagas e significado do asterisco não comprovados')
    table=matrices[0]
    row=re.compile(r'\s*Cargo (?P<id>\d+): (?P<name>[\s\S]+?)\s+'
                   r'(?P<values>(?:\d+|\*)(?:\s+(?:\d+|\*)){8})\s*(?=Cargo |$)')
    rows=list(row.finditer(table['rows']))
    if not rows or row.sub('',table['rows']).strip():return fail('quadro de vagas parcialmente interpretado')
    if sorted(m['id'] for m in rows)!=sorted(ids):return fail('cargos do quadro e dos perfis divergem')
    fee=re.compile(r'^\s*\d+ DAS INSCRIÇÕES NO CONCURSO PÚBLICO\s*\n'
                   r'\d+\.1 TAXA: R\$ (?P<fee>'+MONEY+r')\.[ \t]*(?=\n|$)',re.M)
    fees=list(fee.finditer(text))
    if len(fees)!=1 or len(re.findall(r'\bTAXA\s*:',text))!=1:
        return fail('taxa única de inscrição não comprovada')
    jobs=[]; ev=evidence(table.start(),table.end())+evidence(fees[0].start(),fees[0].end())
    by_id={m['id']:m for m in rows}
    for m in matches:
        r=by_id[m['id']]
        if _norm(r['name'])!=_norm(m['name']):return fail('nome de cargo diverge entre perfil e quadro')
        values=[0 if v=='*' else int(v) for v in r['values'].split()]
        if sum(values[:3])!=values[3] or sum(values[4:7])!=values[7] or values[3]+values[7]!=values[8]:
            return fail('totais do quadro de vagas inconsistentes')
        jobs.append({'nome':' '.join(m['name'].split()),'vagas_imediatas':values[3],
            'cadastro_reserva':values[7]>0,'remuneracao':_money(m['salary']),'moeda':'BRL',
            'jornada':m['hours'],'requisitos':' '.join(m['requirements'].split()),
            'taxa_inscricao':_money(fees[0]['fee'])})
        ev.extend(evidence(start+m.start(),start+m.end()))
    return jobs,ev,None
