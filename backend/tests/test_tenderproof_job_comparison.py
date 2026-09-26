from copy import deepcopy
from types import SimpleNamespace
import pytest
from app.tenderproof.compare import compare
from app.tenderproof.contracts import ExtractedField
from app.tenderproof.service import read_only_baseline_from_concurso


JOB = {'nome': 'Agente', 'vagas_imediatas': 2, 'cadastro_reserva': None,
       'remuneracao': '3242.00', 'moeda': 'BRL', 'jornada': '40h',
       'requisitos': 'Ensino médio completo', 'taxa_inscricao': '90.00'}


def comparison(baseline, state='supported', value=None):
    result = compare(baseline={'cargos': baseline}, baseline_collected_at=None,
                     baseline_origin='controlled prior record', fields=[ExtractedField(
                         field_name='cargos', state=state, value=value or [deepcopy(JOB)])])
    return next(f for f in result.fields if f.field_name == 'cargos')


def test_jobs_are_compared_and_canonical_baseline_is_read_only():
    jobs = [deepcopy(JOB)]
    baseline, _, _ = read_only_baseline_from_concurso(SimpleNamespace(cargos=jobs, prova_data='2026-11-29'))
    assert baseline['cargos'] == jobs
    assert baseline['prova_data'] == '2026-11-29'
    assert comparison(baseline['cargos']).agreement.value == 'agree'
    assert comparison(None).agreement.value == 'no_baseline'
    assert jobs == [JOB]


@pytest.mark.parametrize('key,value', [
    ('cadastro_reserva', False), ('vagas_imediatas', 3),
    ('remuneracao', '90.00'), ('taxa_inscricao', '3242.00'),
    ('jornada', '30h'), ('requisitos', 'Ensino superior'),
])
def test_changed_job_attribute_is_not_hidden(key, value):
    previous = deepcopy(JOB)
    previous[key] = value
    assert comparison([previous]).agreement.value == 'diverge'


@pytest.mark.parametrize('state', ['failed', 'unknown', 'conflict'])
def test_pending_jobs_never_compare_as_supported(state):
    row = comparison([JOB], state=state)
    assert row.tenderproof_value is None
    assert row.tenderproof_state.value == state
    assert row.agreement.value == 'no_evidence'
