import pytest
from app.tenderproof.contracts import PageText
from app.tenderproof.fumarc_job_tables import extract_fumarc_tables

HEADER = 'Cargo Escolaridade/Requisitos Carga\nhorária Vagas* Total de vagas Salário inicial\nda carreira AC PCD PN PI PQ\n'
BODY = ('Técnico Novo Ensino Médio completo. Disponibilidade para viagens.\n'
        '180 horas/mês 6 1 3 - - 10 R$ 4.542,72\n'
        'Profissional - Contabilidade Ensino Superior completo em Ciências Contábeis e registro no CRC.\n'
        '200 horas/mês CR - - - - CR R$ 8.991,81\n')
END = 'Legenda:\nCR > Cadastro de Reserva.'


def parse(body=BODY, end=END):
    return extract_fumarc_tables([PageText(artifact_id='annex',page_number=1,text=HEADER+body+end)])


def test_monthly_hours_salary_reserve_and_total_keep_column_meaning():
    rows, errors = parse()
    assert not errors and len(rows) == 2
    first, second = [row[0] for row in rows]
    assert first['vagas_imediatas'] == 10 and first['cadastro_reserva'] is False
    assert first['jornada'] == '180 horas/mês' and first['remuneracao'] == '4542.72'
    assert first['taxa_inscricao'] is None
    assert second['cadastro_reserva'] is True and second['vagas_imediatas'] == 0
    assert second['remuneracao'] == '8991.81' and 'CRC' in second['requisitos']
    for job,page,header,row in rows:
        assert header in page.text and row in page.text


@pytest.mark.parametrize('body', [
    BODY.replace('3 - - 10', '3 - - 11'),
    BODY.replace('CR - - - - CR', 'CR 1 - - - CR'),
    BODY + 'Linha adicional não interpretada\n',
    BODY.replace('180 horas', '0 horas'),
    BODY.replace('R$ 4.542,72', ''),
])
def test_inconsistent_or_unconsumed_table_is_pending(body):
    rows, errors = parse(body)
    assert errors


def test_reserve_needs_explicit_legend():
    rows, errors = parse(end='')
    assert not rows and errors
