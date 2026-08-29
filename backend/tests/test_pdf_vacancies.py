from app.pdf.parsers.ibfc import _extract_total_vagas


def test_extract_total_vagas_from_compact_jobs_table():
    text = '''
    CÓD EMPREGOS ESCOLARIDADE VAGAS TOTAL
    101 Analista Superior 5 + 3 + CR 08 + CR
    102 Assistente Médio 2 + CR 02 + CR
    103 Técnico Médio 10 + 5 + CR 15 + CR
    AP – Ampla Concorrência
    '''
    assert _extract_total_vagas(text) == 25


def test_extract_total_vagas_from_funcern_annex():
    text = '''
    ANEXO I
    QUADRO DE CARGOS
    Cargo 1: Analista
    TOTAL
    5
    Cargo 2: Assistente
    TOTAL
    1 + 1 CR
    ANEXO II
    CRONOGRAMA
    '''
    assert _extract_total_vagas(text) == 6


def test_extract_total_vagas_from_ieses_coded_annex():
    text = '''
    ANEXO I – CÓDIGO, CARGO, VAGAS E SALÁRIO
    CÓDIGO CARGO VAGAS SALÁRIO JORNADA SEMANAL
    2018 TÉCNICO DE GÁS NATURAL – ELÉTRICA 1 R$ 5.429,62 40 h
    2021 TÉCNICO DE GÁS NATURAL – MECÂNICA 1 R$ 5.429,62 40 h
    BENEFÍCIOS:
    Auxílio alimentação
    ANEXO II – CÓDIGOS, CARGOS E ESCOLARIDADE
    '''
    assert _extract_total_vagas(text) == 2
