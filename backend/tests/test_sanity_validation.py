from datetime import datetime, timezone

from app.audit_validation import validate_concurso_sanity
from app.connectors.common import extract_city_uf
from app.publications import is_valid_publication_title


def test_sanity_rejects_inverted_registration_interval():
    result = validate_concurso_sanity({
        'inscricao_inicio': '2026-09-02',
        'inscricao_fim': '2026-09-01',
    })
    assert result['valid'] is False
    assert 'inscricao_interval_inverted' in result['errors']


def test_sanity_rejects_inverted_salary_interval():
    result = validate_concurso_sanity({'salario_min': 'R$ 5.000,00', 'salario_max': 'R$ 4.000,00'})
    assert result['valid'] is False
    assert 'salary_interval_inverted' in result['errors']


def test_sanity_rejects_invalid_uf_and_semantic_city():
    result = validate_concurso_sanity({'uf': 'XX', 'cidade': 'Clique aqui'})
    assert result['valid'] is False
    assert {'invalid_uf', 'semantic_city'} <= set(result['errors'])


def test_sanity_rejects_noise_as_salary_or_edital():
    result = validate_concurso_sanity({
        'salario_min': 'Taxa de inscrição R$ 80,00',
        'link_edital': 'https://example.org/politica-de-privacidade.pdf',
    })
    assert result['valid'] is False
    assert {'salary_semantic_noise', 'invalid_edital_link'} <= set(result['errors'])


def test_sanity_reports_year_like_vacancy_without_imposing_a_maximum():
    result = validate_concurso_sanity({'vagas': 2026})
    assert result['valid'] is True
    assert 'vagas_looks_like_year' in result['warnings']


def test_city_parser_rejects_interface_actions():
    assert extract_city_uf('Inscreva - SE') == (None, None)
    assert extract_city_uf('LEIA - SE') == (None, None)


def test_publication_noise_is_blocked():
    for title in ('Menu', 'Rodapé', 'Social', 'Manual do candidato', 'Aviso'):
        assert not is_valid_publication_title(title)


def test_sanity_warns_about_implausible_proof_date():
    result = validate_concurso_sanity({
        'edital_data': datetime(2026, 8, 10, tzinfo=timezone.utc),
        'prova_data': datetime(2026, 8, 1, tzinfo=timezone.utc),
    })
    assert result['valid'] is True
    assert 'proof_before_notice' in result['warnings']
