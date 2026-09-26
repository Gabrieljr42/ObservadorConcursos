"""Real proposal/application must retain an explicitly reviewed time on the same day."""
import hashlib
from datetime import datetime
from app.tenderproof.delivery_precise_schedules import CASES
from app.tenderproof.demo_pdf import make_text_pdf
from app.tenderproof.pdf_text import extract_pages
from app.tenderproof.fields import extract_fields
from test_tenderproof_publication import env, proposal, apply, PDF_PAGE_1


def test_same_day_time_precision_is_applied_and_idempotent(env, monkeypatch):
    db, _, _, contest, run, store = env
    text = 'Inscrições de 10/03/2026 às 10h até 19/04/2026 às 17h.\nHorário de Brasília.\nProva objetiva em 10/05/2026.'
    content = make_text_pdf([PDF_PAGE_1, text])
    run.artifact.sha256 = hashlib.sha256(content).hexdigest()
    run.artifact.byte_len = len(content)
    store.save_artifact_file(run.artifact, content)
    candidate = run.candidates[0]
    monkeypatch.setitem(CASES, (candidate.source, candidate.external_id, run.artifact.sha256), {
        'zone': (2, 'Horário de Brasília.'),
        'registration': (2, 'Inscrições de 10/03/2026 às 10h até 19/04/2026 às 17h.'),
        'exam': (2, 'Prova objetiva em 10/05/2026.'),
        'start': '2026-03-10T10:00:00-03:00', 'end': '2026-04-19T17:00:00-03:00',
        'exam_value': '2026-05-10', 'note': 'Fixture with explicit source timezone.',
    })
    pages, *_ = extract_pages(content, artifact_id=run.artifact.artifact_id)
    run.fields = extract_fields(candidate=candidate, artifact=run.artifact, pages=pages)
    approved = proposal(env, fields=('inscricao_inicio', 'inscricao_fim'))
    result = apply(env, approved)
    assert result['state'] == 'applied' and result['version_id'] is not None
    assert set(result['result']['diff']) >= {'inscricao_inicio', 'inscricao_fim'}
    assert 'T17:00:00-03:00' in result['result']['diff']['inscricao_fim']['new']
    assert apply(env, approved)['version_id'] == result['version_id']


def test_date_only_cannot_erase_existing_same_day_time(env):
    db, _, _, contest, run, _ = env
    end = next(field.value for field in run.fields if field.field_name == 'inscricao_fim')
    contest.inscricao_fim = datetime.fromisoformat(end).replace(hour=17)
    db.commit()
    approved = proposal(env, fields=('inscricao_fim',))
    result = apply(env, approved)
    db.refresh(contest)
    assert result['state'] == 'no_change'
    assert contest.inscricao_fim.hour == 17
