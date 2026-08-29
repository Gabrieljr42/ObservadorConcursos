from datetime import datetime, timezone

import pytest

from app.connectors.configurable import SourceDefinition
from app.connectors.institutional import InstitutionalSelectionConnector


def connector(source_type: str = 'fap_test') -> InstitutionalSelectionConnector:
    return InstitutionalSelectionConnector(SourceDefinition(
        source_type=source_type,
        name=source_type,
        banca=source_type.upper(),
        base_url='https://example.org',
        list_urls=['https://example.org/editais'],
        category='institutional_selection',
        default_uf='GO',
    ))


def valid_args(**overrides):
    args = dict(
        title='Processo Seletivo Simplificado 01/2026',
        orgao='Fundação estadual',
        cidade='Goiânia',
        uf='GO',
        inicio=datetime.now(timezone.utc),
        fim=datetime.now(timezone.utc),
        edital_url='https://example.org/edital.pdf',
        cargo_candidates=['Analista'],
        text='Edital para contratação temporária de profissionais.',
    )
    args.update(overrides)
    return args


@pytest.mark.parametrize('title,text', [
    ('Chamada pública para seleção de propostas de pesquisa', 'Processo seletivo de projetos de pesquisa e fomento.'),
    ('Edital de evento científico 04/2026', 'Seleção de propostas para realização de eventos científicos.'),
    ('Prêmio inovação 02/2026', 'Processo seletivo para premiação de pesquisadores.'),
    ('Chamada para mobilidade acadêmica', 'Seleção de bolsistas para intercâmbio e mobilidade.'),
    ('Edital de compras 03/2026', 'Licitação para compra de equipamentos e contratação de fornecedor.'),
    ('Oferta tecnológica 01/2026', 'Seleção de empresas para transferência de tecnologia.'),
    ('Programa PIBIC 2026', 'Processo seletivo de bolsistas de iniciação científica.'),
])
def test_rejects_non_personnel_calls_even_with_selection_words(title, text):
    assert not connector()._is_valid_certame(**valid_args(
        title=title, text=text, cargo_candidates=['Pesquisador', 'Coordenador']
    ))


@pytest.mark.parametrize('source_type,title,text', [
    ('fapeg_selection', 'PSS FAPEG 009/2024 - Analista de Ciência e Tecnologia',
     'Processo seletivo simplificado para contratação temporária de analistas.'),
    ('fapergs_selection', 'Processo Seletivo Simplificado FAPERGS 01/2025',
     'Contratação temporária de Agente Administrativo para preenchimento de vagas.'),
    ('fapemat_selection', 'Edital de seleção pública FAPEMAT 02/2026',
     'Seleção pública de pessoal para cargo de apoio técnico institucional.'),
])
def test_accepts_real_foundation_personnel_selection(source_type, title, text):
    assert connector(source_type)._is_valid_certame(**valid_args(
        title=title, text=text, cargo_candidates=['Analista']
    ))


@pytest.mark.parametrize('text', [
    'Processo seletivo para contratação de empresa fornecedora.',
    'Chamada de fomento a projetos de pesquisa; processo seletivo de propostas.',
    'Seleção de bolsistas para mestrado e doutorado.',
])
def test_incidental_processo_seletivo_does_not_release_call(text):
    assert not connector()._is_valid_certame(**valid_args(
        title='Edital 01/2026', text=text, cargo_candidates=['Coordenador']
    ))


def test_accepts_stage_and_institutional_support_when_linked_to_vacancy():
    assert connector()._is_valid_certame(**valid_args(
        title='Seleção pública de estágio 01/2026',
        text='Vagas de estágio e apoio técnico institucional com vínculo definido.',
        cargo_candidates=['Estagiário'],
    ))
