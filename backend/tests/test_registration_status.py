from datetime import datetime, timezone
from types import SimpleNamespace
import pytest
from app.registration_status import registration_situation


def contest(start=None, end=None, status=None):
    return SimpleNamespace(inscricao_inicio=datetime.fromisoformat(start) if start else None,
                           inscricao_fim=datetime.fromisoformat(end) if end else None, status=status)


@pytest.mark.parametrize('start,end,expected', [
    ('2026-08-31','2026-10-08','open'),
    ('2026-08-25','2026-09-08','closed'),
    ('2026-08-21','2026-09-04','closed'),
    ('2026-11-17','2026-12-17','upcoming'),
    ('2026-10-30','2026-12-01','upcoming'),
    ('2026-10-13','2026-11-13','upcoming'),
    ('2026-09-04','2026-10-07','open'),
    ('2026-09-02','2026-10-05','open'),
    ('2026-08-21','2026-09-10','open'),
    ('2026-02-02','2026-03-04','closed'),
])
def test_actual_initial_catalogue(start, end, expected):
    assert registration_situation(contest(start, end), now=datetime(2026,9,9,20,tzinfo=timezone.utc)) == expected


def test_unknown_is_not_open():
    assert registration_situation(contest()) == 'unknown'
    assert registration_situation(contest(status='Em andamento')) == 'unknown'


def test_end_date_inclusive_brazilian_calendar():
    c = contest('2026-08-21T00:00:00+00:00','2026-09-10T00:00:00+00:00')
    assert registration_situation(c, now=datetime.fromisoformat('2026-09-11T02:59:00+00:00')) == 'open'
    assert registration_situation(c, now=datetime.fromisoformat('2026-09-11T03:00:00+00:00')) == 'closed'


def test_reopening_instant_overrides_historical_label():
    c = contest('2026-09-09T10:00:00-03:00','2026-09-11T10:00:00-03:00','Encerrado')
    assert registration_situation(c, now=datetime.fromisoformat('2026-09-09T12:59:59+00:00')) == 'upcoming'
    assert registration_situation(c, now=datetime.fromisoformat('2026-09-09T13:00:00+00:00')) == 'open'
    assert registration_situation(c, now=datetime.fromisoformat('2026-09-11T13:00:00+00:00')) == 'closed'


def test_invalid_period_cannot_become_open():
    assert registration_situation(contest('2026-10-01','2026-09-01', 'Inscrições abertas')) == 'unknown'


def test_documented_midnight_is_an_instant():
    c = contest('2026-09-09T10:00:00-03:00','2026-09-11T00:00:00-03:00')
    c.raw_data = {'tenderproof': {'amendments': [{'periods': {'current': {'precision': 'instant'}}}]}}
    assert registration_situation(c, now=datetime.fromisoformat('2026-09-11T02:59:59+00:00')) == 'open'
    assert registration_situation(c, now=datetime.fromisoformat('2026-09-11T03:00:00+00:00')) == 'closed'
