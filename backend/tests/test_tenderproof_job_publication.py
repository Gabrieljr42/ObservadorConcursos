import hashlib

from app.models import ConcursoVersion
from app.tenderproof import publication as pub
from app.tenderproof.demo_pdf import make_text_pdf
from app.tenderproof.fields import extract_fields
from app.tenderproof.pdf_text import extract_pages
from app.versioning import normalize_for_compare
from test_tenderproof_job_tables import HEADER, ROW
from test_tenderproof_publication import env, proposal, apply, count, PDF_PAGE_1


def prepare_jobs(env):
    _, _, _, _, run, store = env
    content = make_text_pdf([PDF_PAGE_1, HEADER + ROW + '3. DAS INSCRIÇÕES\n'])
    run.artifact.sha256 = hashlib.sha256(content).hexdigest()
    run.artifact.byte_len = len(content)
    store.save_artifact_file(run.artifact, content)
    pages, *_ = extract_pages(content, artifact_id=run.artifact.artifact_id)
    run.fields = extract_fields(candidate=run.candidates[0], artifact=run.artifact, pages=pages)
    return run.field_map()['cargos'].value


def test_jobs_review_apply_repeat_and_rollback_preserve_other_fields(env):
    db, _, user, contest, run, store = env
    jobs = prepare_jobs(env)
    p = proposal(env, fields=('cargos',))
    result = apply(env, p)
    db.refresh(contest)
    assert contest.cargos == jobs
    assert str(contest.salario_min).startswith('3500')
    assert result['result']['diff']['cargos']['new'][0]['taxa_inscricao'] == '50.00'
    assert apply(env, p)['version_id'] == result['version_id']
    assert count(db, ConcursoVersion) == 1
    pub.rollback_proposal(db, proposal_id=p['id'], reason='Revisão da tabela', user=user)
    db.refresh(contest)
    assert contest.cargos is None
    assert count(db, ConcursoVersion) == 2


def test_forged_salary_cannot_be_published(env):
    db, _, user, contest, run, store = env
    prepare_jobs(env)
    run.field_map()['cargos'].value[0]['remuneracao'] = '50.00'
    p = pub.create_proposal(db, run=run, concurso_id=contest.id, user=user, store=store)
    assert 'cargos' not in p['eligible_fields']
    assert 'cargos' in p['blocked_fields']


def test_job_dictionary_order_does_not_create_change():
    assert normalize_for_compare([{'nome': 'A', 'remuneracao': '10.00'}], field='cargos') == normalize_for_compare([{'remuneracao': '10.00', 'nome': 'A'}], field='cargos')


def test_old_revision_only_compatible_with_null_jobs():
    old = {'values': {'titulo': 'A'}, 'latest_version_id': 1}
    assert pub._same_revision({'values': {'titulo': 'A', 'cargos': None}, 'latest_version_id': 1}, old)
    assert not pub._same_revision({'values': {'titulo': 'A', 'cargos': [{'nome': 'B'}]}, 'latest_version_id': 1}, old)
