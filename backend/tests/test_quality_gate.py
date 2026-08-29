from datetime import datetime, timezone
import pytest

from app.connectors.base import BaseConnector
from app.connectors.configurable import ConfigurableHTMLConnector, SourceDefinition
from app.connectors.institutional import InstitutionalSelectionConnector


def test_base_quality_gate_rejects_junk():
    connector = BaseConnector(base_url='https://example.com')

    # Junk navigation titles
    assert not connector._is_valid_certame(
        title='Para saber mais informações clique aqui',
        orgao=None,
        cidade=None,
        uf=None,
        inicio=None,
        fim=None,
        edital_url=None,
        cargo_candidates=[],
        text='Página inicial do portal de concursos e notícias.',
    )

    assert not connector._is_valid_certame(
        title='Concursos',
        orgao=None,
        cidade=None,
        uf=None,
        inicio=None,
        fim=None,
        edital_url=None,
        cargo_candidates=[],
        text='Área do candidato e legislação',
    )


def test_base_quality_gate_accepts_valid_certame():
    connector = BaseConnector(base_url='https://example.com')
    now = datetime.now(timezone.utc)

    assert connector._is_valid_certame(
        title='Concurso Público - Edital 01/2026',
        orgao='Prefeitura Municipal de Belo Horizonte',
        cidade='Belo Horizonte',
        uf='MG',
        inicio=now,
        fim=now,
        edital_url='https://example.com/edital.pdf',
        cargo_candidates=['Assistente Social', 'Médico'],
        text='Edital de abertura de inscrições para diversos cargos.',
    )


def test_institutional_quality_gate_rejects_pure_research_grants():
    definition = SourceDefinition(
        source_type='fapemig_test',
        name='FAPEMIG Test',
        banca='FAPEMIG',
        base_url='https://fapemig.br',
        list_urls=['https://fapemig.br/editais'],
        category='institutional_selection',
    )
    connector = InstitutionalSelectionConnector(definition)

    # Pure research grant / scientific funding
    assert not connector._is_valid_certame(
        title='Chamada Universal 01/2026 - Apoio a Projetos de Pesquisa Científica',
        orgao='FAPEMIG',
        cidade='Belo Horizonte',
        uf='MG',
        inicio=None,
        fim=None,
        edital_url='https://fapemig.br/edital-pesquisa.pdf',
        cargo_candidates=[],
        text='Concessão de auxílio à pesquisa e fomento a laboratórios de pesquisa acadêmica.',
    )


def test_institutional_quality_gate_accepts_personnel_selection():
    definition = SourceDefinition(
        source_type='fapemig_test',
        name='FAPEMIG Test',
        banca='FAPEMIG',
        base_url='https://fapemig.br',
        list_urls=['https://fapemig.br/editais'],
        category='institutional_selection',
    )
    connector = InstitutionalSelectionConnector(definition)

    # Real personnel hiring / selection process
    assert connector._is_valid_certame(
        title='Processo Seletivo Simplificado 02/2026 - Contratação de Pessoal Temporário',
        orgao='FAPEMIG',
        cidade='Belo Horizonte',
        uf='MG',
        inicio=datetime.now(timezone.utc),
        fim=datetime.now(timezone.utc),
        edital_url='https://fapemig.br/edital-selecao.pdf',
        cargo_candidates=['Analista Técnico', 'Assistente Administrativo'],
        text='Seleção pública para contratação de pessoal e formação de cadastro reserva.',
    )
