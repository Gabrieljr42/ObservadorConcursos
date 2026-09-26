"""Exact timing from reviewed preserved schedules, with explicit timezone proof."""
from app.tenderproof.contracts import ExtractedField, FieldState

CASES = {
    ('elo_open', '129', 'a5a7ff5a11bef285d389bd71a5e2d53b8ad5e82dec8d545edcea653c0fbef5a2'): {
        'zone': (1, 'Toda menção a horário neste Edital terá como referência o horário oficial da cidade de Brasília-DF.'),
        'registration': (23, '18/08/2026 a 18/09/2026\n15h do dia\n18/08/2026 às 15h\ndo dia 18/09/2026\nInscrições dos Candidatos no processo seletivo;'),
        'exam': (23, '18/10/2026\nConforme previsto\nno ANEXO I deste\nEdital\nRealização das Provas: Objetiva de Múltipla Escolha e TAF;'),
        'start': '2026-08-18T15:00:00-03:00', 'end': '2026-09-18T15:00:00-03:00',
        'exam_value': '2026-10-18',
        'note': 'Datas do edital-base, com Brasília expresso. A retificação troca TAF por títulos e deve ser composta pelo gate documental antes de publicar; não altera a data da prova objetiva.',
    },
    ('objetiva_open', '2590', 'ab4f9d155273cc688f84191993102dba4298b20b009b93132ba0e99ed521112a'): {
        'zone': (46, 'Todos os horários mencionados neste edital e na publicidade oficial do certame referem -se ao Horário de Brasília (DF).'),
        'registration': (46, '12/05/2026 Abertura do período para solicitação de inscrição – Às 13h'),
        'registration_end': (46, '10/06/2026 Encerramento do período para solicitação de inscrição – Às 13h'),
        'exam': (46, '05/07/2026 Aplicação da prova objetiva'),
        'start': '2026-05-12T13:00:00-03:00', 'end': '2026-06-10T13:00:00-03:00',
        'exam_value': '2026-07-05',
        'note': 'Concurso 001/2026, edital de abertura 013/2026. Inscrições às13h de Brasília. Prova objetiva com data comum, sem inferir horário.',
    },
    ('institutomais_open', '10630', '6a7db20c0ef15757ae7188be095b67b46cc76ff505fab019c97be41edce0c800'): {
        'zone': (1, 'Todas as etapas constantes neste Edital serão realizadas observando-se o horário de Brasília/DF.'),
        'registration': (6, 'de 12 de janeiro a 12 de fevereiro de 2026, iniciando-se às 10h do dia 12 de janeiro de 2026, e encerrando -se,\nimpreterivelmente, às 17h do dia 12 de fevereiro de 2026, observado o horário de Brasília/DF'),
        'exam': (51, '22/03/2026 Aplicação das Provas Objetivas e Dissertativa'),
        'start': '2026-01-12T10:00:00-03:00', 'end': '2026-02-12T17:00:00-03:00',
        'exam_value': '2026-03-22',
        'note': 'Inscrições das10h do primeiro dia às17h do último, Brasília. Provas em turnos distintos por cargo, sem horário único inferido.',
    },
    ('ibam_open', '364', '4c2d85e7c9f1db1eb49b4f4f853117cd0ab73128da0a9d7aabcb339753f9e496'): {
        'zone': (3, 'Os horários estabelecidos neste Edital seguem o horário oficial de Brasília/DF.'),
        'registration': (8, 'O site estará disponível para inscrição no período entre 0h00 do dia 10/08/26 e 23h59 do\ndia 08/10/26.'),
        'exam': (13, '6.3. Realização das Provas\n6.3.1. As provas serão aplicadas na data e horários estabelecidos a seguir:\nCargos: Auditor Fiscal Municipal e Analista Fiscal Municipal ( Áreas: Tecnologia da\nInformação; Engenharia Civil; Contabilidade; Direito)\nData: 29 de novembro de 2026'),
        'start': '2026-08-10T00:00:00-03:00', 'end': '2026-10-08T23:59:00-03:00',
        'exam_value': '2026-11-29',
        'note': 'Inscrições de0h a23h59, Brasília. Provas às09h10 ou16h10 por cargo; o campo comum preserva somente29/11.',
    },
    ('exame_open', '525', '404fa4ff67f8dab7edfcf650b62fe1975c6f38285a7240b9eb540670b23d3455'): {
        'zone': (1, 'Toda menção a horário neste Edital terá como\nreferência o horário oficial de Brasília/DF.'),
        'registration': (13, 'Período de inscrições 22/07/2026 a 24/07/2026\n(das 9h do primeiro dia às\n23h59 do último dia)'),
        'exam': (13, 'Aplicação da Prova Objetiva de Múltipla Escolha 23/08/2026 (às 8h)'),
        'start': '2026-07-22T09:00:00-03:00', 'end': '2026-07-24T23:59:00-03:00',
        'exam_value': '2026-08-23T08:00:00-03:00',
        'note': 'Certificação ocupacional, sem garantia de investidura ou nomeação. Horários de Brasília expressos no edital.',
    },
    ('cotec_open', '32', 'b6f8fcb5ec3f1ff27269f93175ac5bc7c0f807c503522935dcfc5c7c12dc3626'): {
        'zone': (1, 'Os horários estabelecidos neste Edital referem -se à hora oficial de Brasília-DF.'),
        'registration': (2, 'Inscrições (com pagamento da taxa) Das 08h do dia 10/09/2026 às\n17h do dia 07/10/2026'),
        'exam': (2, 'Aplicação das Provas de Múltipla Escolha 13/12/2026'),
        'start': '2026-09-10T08:00:00-03:00', 'end': '2026-10-07T17:00:00-03:00',
        'exam_value': '2026-12-13',
        'note': 'Período de inscrição com pagamento. Pré-inscrição para isenção separada:07/09/2026 às08h a09/09/2026 às17h, Brasília; não é o período pago. Provas têm data comum, sem inferir horário único.',
    },
    ('consep_open', '200', 'e9939c6f32a278ea36da589aa668b3b1565835768d94ad228a16529211f4c99a'): {
        'registration': (1, 'As inscrições serão realizadas no período de 12 a 19 de janeiro de 2026.'),
        'registration_end': (2, '19 horas do dia 19 de janeiro de 2026.'),
        'exam': (5, 'As provas objetivas serão realizadas dia 1º de fevereiro de 2026, a partir das 8h00min\n(horário local) com três horas de duração, sendo este horário (8h00min) o limite para ingressar\nno local de aplicação das provas.'),
        'start': '2026-01-12', 'end': '2026-01-19',
        'exam_value': '2026-02-01',
        'note': 'Período começa em 12/01 sem horário inicial expresso; encerramento comprovado às 19h no dia 19/01, em horário local, sem fuso informado. Prova permanece somente com dia, pois o edital informa horário local sem fuso canônico.',
    },
}

def extract_precise_schedule(candidate, artifact, pages, evidence):
    case = CASES.get((candidate.source, candidate.external_id, artifact.sha256))
    if case is None:
        return []
    by_number = {page.page_number: page for page in pages}
    names = ('inscricao_inicio', 'inscricao_fim', 'prova_data')
    required = [case[key] for key in ('registration', 'exam')]
    if any('T' in case[key] for key in ('start', 'end', 'exam_value')) and 'zone' not in case:
        raise RuntimeError('Timestamp preciso exige evidência explícita de fuso.')
    if 'zone' in case:
        required.append(case['zone'])
    if 'registration_end' in case:
        required.append(case['registration_end'])
    if any(number not in by_number or by_number[number].error or by_number[number].truncated
           or snippet not in by_number[number].text for number, snippet in required):
        return [ExtractedField(field_name=name, state=FieldState.FAILED,
            reason='Cronograma/horário/fuso conferidos não foram reproduzidos; revisão necessária.') for name in names]
    values = (case['start'], case['end'], case['exam_value'])
    fields = []
    for name, value in zip(names, values):
        selected = [case['exam'] if name == 'prova_data' else case['registration']]
        if name == 'inscricao_fim' and 'registration_end' in case:
            selected = [case['registration_end']]
        if 'T' in value and 'zone' in case:
            selected.append(case['zone'])
        fields.append(ExtractedField(field_name=name, state=FieldState.SUPPORTED, value=value,
            original_value=selected[0][1], reason=case['note'],
            evidence=[evidence(artifact=artifact, page=by_number[number], snippet=snippet) for number, snippet in selected]))
    return fields
