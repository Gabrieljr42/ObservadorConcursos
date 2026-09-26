from datetime import datetime, timezone

import pytest

from app.tenderproof.contracts import Artifact, DiscoveredCandidate, PageText
from app.tenderproof.fields import _DATE_TOKEN, _date_value, _evidence, extract_fields
from app.tenderproof.registration_lists import extract_lists


def row(label='Primeira', start='19 de junho de 2026', end='1º de julho de 2026'):
    return f'{label} lista de Candidatos\nComeço das inscrições: {start} às 10h\nFim das Inscrições: {end}\n'


def extract(text, **page_options):
    artifact = Artifact(artifact_id='doc', sha256='a' * 64, byte_len=123,
        url_requested='https://example.org/edital.pdf', url_final='https://example.org/edital.pdf',
        downloaded_at=datetime.now(timezone.utc))
    return extract_lists(artifact, [PageText(artifact_id='doc', page_number=3, text=text, **page_options)],
        _evidence, _DATE_TOKEN.pattern, _date_value)


def test_closed_and_open_lists_keep_separate_periods_and_literal_evidence():
    text = row() + row('Segunda', '8 de julho de 2026', 'As inscrições ficarão abertas até o novo edital de inscrições')
    result = extract(text)
    assert result.state.value == 'supported'
    assert result.value[0]['fim'] == '2026-07-01'
    assert result.value[1] == dict(lista='segunda', inicio='2026-07-08', fim=None,
        condicao_fim='até novo edital de inscrições')
    assert all(e.snippet in text and e.page_number == 3 for e in result.evidence)


def test_conflicting_repeated_list_is_not_silently_overwritten():
    assert extract(row() + row(end='2 de julho de 2026')).state.value == 'conflict'
    assert len(extract(row() + row()).value) == 1


@pytest.mark.parametrize('text', [row(end='ilegível'), row(start='31 de junho de 2026'),
    row(start='2 de julho de 2026'), row() + 'Quarta lista de Candidatos\nInscrições a definir'])
def test_unparsed_or_invalid_period_never_becomes_supported(text):
    result = extract(text)
    assert result.state.value == 'failed' and result.value is None


@pytest.mark.parametrize('options', [{'truncated': True}, {'error': 'text unavailable'}])
def test_damaged_page_does_not_support_period(options):
    assert extract(row(), **options).state.value == 'failed'


def test_unrelated_dates_do_not_create_lists():
    assert extract('Data da prova: 19/06/2026\nPagamento: 01/07/2026') is None


def test_field_pipeline_never_publishes_first_list_deadline_as_whole_selection():
    artifact = Artifact(artifact_id='doc', sha256='a' * 64, byte_len=123,
        url_requested='https://example.org/edital.pdf', url_final='https://example.org/edital.pdf',
        downloaded_at=datetime.now(timezone.utc))
    candidate = DiscoveredCandidate(candidate_id='lists', source='fapes_selection',
        title_observed='Seleção de estágio', detail_url_observed='https://example.org/selecao',
        observed_at=datetime.now(timezone.utc))
    text = row() + row('Segunda', '8 de julho de 2026', 'As inscrições ficarão abertas até o novo edital de inscrições')
    fields = {f.field_name: f for f in extract_fields(candidate=candidate, artifact=artifact,
        pages=[PageText(artifact_id='doc', page_number=3, text=text)])}
    assert fields['inscricao_listas'].state.value == 'supported'
    for name in ('inscricao_inicio', 'inscricao_fim'):
        assert fields[name].value is None and fields[name].state.value == 'failed'
        assert fields[name].evidence and 'listas' in fields[name].reason
