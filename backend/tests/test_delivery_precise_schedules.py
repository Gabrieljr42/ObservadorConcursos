from types import SimpleNamespace
import pytest
from app.tenderproof.delivery_precise_schedules import CASES, extract_precise_schedule


def test_complete_local_time_without_zone_cannot_publish_an_offset(monkeypatch):
    identity = ('local_fixture', '1', 'f' * 64)
    monkeypatch.setitem(CASES, identity, {
        'registration': (1, 'Inscrições de 12 a 19 de janeiro de 2026.'),
        'registration_end': (1, '19 horas do dia 19 de janeiro de 2026.'),
        'exam': (1, 'Prova em 01/02/2026.'),
        'start': '2026-01-12', 'end': '2026-01-19T19:00:00-03:00',
        'exam_value': '2026-02-01', 'note': 'No source timezone.',
    })
    page = SimpleNamespace(page_number=1, error=None, truncated=False,
        text='Inscrições de 12 a 19 de janeiro de 2026.\n19 horas do dia 19 de janeiro de 2026.\nProva em 01/02/2026.')
    with pytest.raises(RuntimeError, match='evidência explícita de fuso'):
        extract_precise_schedule(SimpleNamespace(source=identity[0], external_id=identity[1]),
            SimpleNamespace(sha256=identity[2]), [page], None)

@pytest.mark.parametrize('identity', list(CASES))
def test_changed_artifact_is_not_given_reviewed_times(identity):
    source, external_id, _ = identity
    assert extract_precise_schedule(SimpleNamespace(source=source, external_id=external_id),
        SimpleNamespace(sha256='0' * 64), [], None) == []

@pytest.mark.parametrize('identity', list(CASES))
def test_times_without_their_timezone_evidence_fail_closed(identity):
    source, external_id, sha = identity
    case = CASES[identity]
    pages = {}
    for key in ('registration', 'exam'):
        number, snippet = case[key]
        pages[number] = pages.get(number, '') + '\n' + snippet
    supplied = [SimpleNamespace(page_number=number, text=text, error=None, truncated=False)
                for number, text in pages.items()]
    result = extract_precise_schedule(SimpleNamespace(source=source, external_id=external_id),
        SimpleNamespace(sha256=sha), supplied, None)
    assert len(result) == 3 and all(field.state.value == 'failed' and field.value is None for field in result)
