from types import SimpleNamespace
from app.notifications import alert_matches_concurso, should_notify_version


def test_alert_finds_verified_job_with_empty_legacy_cargo():
    contest = SimpleNamespace(titulo='Concurso CREA-MG', orgao='CREA-MG', banca='FUMARC',
        cargo=None, cargos=[{'nome': 'Profissional de Nível Superior - Arquivista'}],
        area=None, cidade=None, uf=None, resumo=None, raw_data={})
    alert = SimpleNamespace(uf=None, cidade=None, banca=None, area=None, status=None,
        cargo_keyword='Arquivista', only_open=False)
    assert alert_matches_concurso(alert, contest)
    alert.cargo_keyword = 'Enfermeiro'
    assert not alert_matches_concurso(alert, contest)


def test_existing_job_update_versions_are_relevant_without_rewriting_history():
    assert should_notify_version(SimpleNamespace(change_type='updated', changed_fields={'cargos': {'old': None, 'new': [{'nome': 'A'}]}}))
    assert not should_notify_version(SimpleNamespace(change_type='updated', changed_fields={'titulo': {'old': 'A', 'new': 'B'}}))
