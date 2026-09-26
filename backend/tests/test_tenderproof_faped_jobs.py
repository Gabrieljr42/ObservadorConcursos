from datetime import datetime, timezone
import pytest
from app.tenderproof.contracts import Artifact, PageText
from app.tenderproof.faped_jobs import extract_jobs
from app.tenderproof.fields import _evidence


def pages():
    texts = ['Cargo N.º de Vagas Carga-horária Salário Base (bruto)\nPesquisador de Campo\n02 6 horas diárias R$ 5.432,10',
        'Cargo Pré-requisito\nI. Ter habilitação.\nII. Formação superior em ciências ou',
        '3. DA INSCRIÇÃO\nData de pagamento: 01/01/2027.\nPesquisador de Campo\nProfissional de Nível\nSuperior\náreas afins.\nIII. Disponibilidade para viagens.']
    return [PageText(artifact_id='doc', page_number=i + 1, text=t) for i,t in enumerate(texts)]


def extract(items):
    artifact = Artifact(artifact_id='doc', sha256='a' * 64, byte_len=123,
        url_requested='https://faped.org.br/files/uploads/document/new.pdf',
        url_final='https://faped.org.br/files/uploads/document/new.pdf', downloaded_at=datetime.now(timezone.utc))
    return extract_jobs(artifact, items, _evidence)


def test_dynamic_job_and_split_requirements_preserve_correct_units_and_evidence():
    items = pages(); field = extract(items)
    assert field.state.value == 'supported'
    job = field.value[0]
    assert job['nome'] == 'Pesquisador de Campo' and job['vagas_imediatas'] == 2
    assert job['remuneracao'] == '5432.10' and job['jornada'] == '6 horas diárias'
    assert 'ciências ou áreas afins' in job['requisitos'] and 'pagamento' not in job['requisitos']
    assert job['cadastro_reserva'] is None and job['taxa_inscricao'] is None
    for evidence in field.evidence:
        assert evidence.snippet in items[evidence.page_number - 1].text


@pytest.mark.parametrize('index,old,new', [
    (0,'6 horas diárias','6 horas semanais'),
    (0,'6 horas diárias','0 horas diárias'),
    (0,'02 6','00 6'),
    (0,'R$ 5.432,10','R$ 5.432,10\nOutra vaga 01 8 horas diárias R$ 8.000,00'),
    (2,'Pesquisador de Campo','Outro Cargo'),
    (2,'III.','IV.'),
    (2,'viagens.','viagens'),
    (2,'viagens.','viagens.\n3.2.4. Documentos de inscrição.'),
])
def test_ambiguous_rows_or_incomplete_requirements_remain_pending(index,old,new):
    items=pages();items[index].text=items[index].text.replace(old,new)
    field=extract(items)
    assert field.state.value == 'failed' and field.value is None


def test_missing_or_damaged_continuation_does_not_support_job():
    assert extract(pages()[:2]).state.value == 'failed'
    items=pages();items[2].truncated=True
    assert extract(items).state.value == 'failed'
    items=pages();items[1].error='unreadable'
    assert extract(items).state.value == 'failed'
