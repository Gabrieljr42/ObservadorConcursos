"""Explicit update titles must reach review without becoming opening notices."""
import pytest

from app.tenderproof.pilot_adapters import document_kind


@pytest.mark.parametrize('title,expected', [
    ('Retificação nº 01', 'retificacao'),
    ('Retificação I do Edital Completo 14/08/2026', 'retificacao'),
    ('EDITAL DE RETIFICAÇÃO Nº 03/2026', 'retificacao'),
    ('Errata 01 - Alteração da vaga', 'retificacao'),
    ('Retificação do Cronograma', 'retificacao'),
    ('01 - Retificação ao Edital', 'retificacao'),
    ('Prorrogação do Prazo de Validade do Edital', 'prorrogacao'),
    ('Edital de Prorrogação das Inscrições', 'prorrogacao'),
    ('Resultado final retificado', 'resultado'),
    ('Gabarito após retificação', 'gabarito'),
    ('Anexo I - Quadro de vagas retificado', 'anexo'),
    ('Edital retificado', 'outro'),
    ('Resposta ao pedido de retificação', 'outro'),
    ('Solicitação de prorrogação', 'outro'),
    ('Retificações solicitadas pelos candidatos', 'outro'),
    ('Edital nº 003 - Retificação nº 01 05/02/2024', 'retificacao'),
    ('COMUNICADO 001 – PRORROGAÇÃO DO PERÍODO DE INSCRIÇÕES – CARGO: 101', 'prorrogacao'),
    ('Edital nº 006 - Prorrogação do Período de Realização das Inscrições', 'prorrogacao'),
    ('Edital nº 97 - Ampliação de vagas', 'retificacao'),
    ('Retificação do resultado final', 'retificacao'),
    ('Edital nº 38 – Inclusão de candidato sub judice.', 'outro'),
    ('Edital nº 328 – Inclusão de candidata sub judice.', 'outro'),
    ('Edital n° 83 – Edital de Posse', 'outro'),
    ('Edital nº 62 - Posse', 'outro'),
    ('Edital n. 89 - Deferimento de Pedido de Final de Lista', 'outro'),
    ('Edital de abertura - Agente de Inclusão Social', 'edital'),
    ('Edital do Concurso Público 002/2027', 'edital'),
])
def test_explicit_update_labels(title, expected):
    assert document_kind(title, 'https://official.test/document.pdf') == expected


def test_filename_cannot_establish_update_kind():
    assert document_kind('Baixar documento', 'https://official.test/retificacao.pdf') == 'outro'
