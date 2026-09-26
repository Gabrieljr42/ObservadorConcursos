"""Controlled canonical conflicts; title alone never establishes sameness."""
import pytest
from fastapi import HTTPException
from app.tenderproof import canonical, publication as pub
from test_tenderproof_publication import env


@pytest.mark.parametrize('title,expected', [
    ('Conceição da Barra de Minas-MG - Concurso Público 001/2026', 'concurso_publico'),
    ('Conceição da Barra de Minas-MG - Processo Seletivo Público 001/2026', 'processo_seletivo'),
    ('PROCESSO SELETIVO SIMPLIFICADO 01/2026', 'processo_seletivo'),
    ('Concurso público e processo seletivo 01/2026', None),
    ('Seleção 001/2026', None),
    ('Concurso 001/2026', None),
])
def test_explicit_title_family(title, expected):
    assert canonical.explicit_modality(title) == expected


@pytest.mark.parametrize('cross_source', [False, True])
def test_distinct_modality_cannot_associate_even_with_identical_notice(env, monkeypatch, cross_source):
    from app.models import Source
    db, _, _, target, run, store = env
    target.titulo = 'Concurso Público 01/2026 Prefeitura Municipal De Exemplo'
    db.commit()
    source_id = target.source_id
    if cross_source:
        source = Source(name='Controlled alias', source_type=run.source, base_url='https://novo.ibgpconcursos.com.br')
        db.add(source)
        db.commit()
        source_id = source.id
    # Isolate identity resolution after successful evidence revalidation.
    monkeypatch.setattr(pub, '_revalidate', lambda *args: ({
        'titulo': 'Processo Seletivo Público 01/2026 Prefeitura Municipal De Exemplo',
        'orgao': target.orgao, 'edital_numero': target.edital_numero}, {}))
    with pytest.raises(HTTPException, match='modalidades distintas') as exc:
        canonical.resolve(db, run, store, target.id, source_id)
    assert exc.value.status_code == 422
    assert target.titulo.startswith('Concurso Público')


def modality_run(env, number, modality):
    import hashlib
    from app.tenderproof.demo_pdf import make_text_pdf
    from app.tenderproof.mock_demo import PDF_PAGE_1
    from app.tenderproof.fields import extract_fields
    from app.tenderproof.pdf_text import extract_pages
    from app.tenderproof.source_adapters import get_source_adapter
    _, _, _, _, template, store = env
    run = template.model_copy(deep=True)
    run.run_id = f'modality-{number}'
    candidate = get_source_adapter(run.source).candidate_from_url(
        f'https://novo.ibgpconcursos.com.br/concurso.jsp?cod={number}',
        f'{modality} Prefeitura Municipal de Exemplo MG')
    content = make_text_pdf([PDF_PAGE_1.replace('Concurso Publico', modality)
                            .replace('concurso publico', modality)
                            .replace('cod=42', f'cod={number}')])
    run.artifact.artifact_id = f'modality-artifact-{number}'
    run.artifact.sha256 = hashlib.sha256(content).hexdigest()
    run.artifact.byte_len = len(content)
    run.artifact.url_final = run.artifact.url_final.replace('/42/', f'/{number}/')
    run.artifact.url_requested = run.artifact.url_final
    run.document.url_requested = run.artifact.url_final
    run.candidates = [candidate]
    run.selected_candidate_id = candidate.candidate_id
    store.save_artifact_file(run.artifact, content)
    pages, *_ = extract_pages(content, artifact_id=run.artifact.artifact_id)
    run.fields = extract_fields(candidate=candidate, artifact=run.artifact, pages=pages)
    return run


@pytest.mark.parametrize('families', [
    ('Concurso Publico', 'Processo Seletivo Publico'),
    ('Processo Seletivo Publico', 'Concurso Publico'),
])
def test_two_modalities_publish_separately_preserving_original_identity(env, families):
    from sqlalchemy import select
    from app.models import Concurso, ConcursoVersion
    from app.tenderproof.publication_models import CanonicalIdentity
    from test_tenderproof_canonical import approve
    from test_tenderproof_publication import apply, count
    db, _, user, old, _, store = env
    db.delete(old)
    db.commit()
    first = modality_run(env, 42, families[0])
    p = pub.create_proposal(db, run=first, user=user, store=store)
    one = apply(env, approve(env, p))
    old_claims = {c.key: c.concurso_id for c in db.scalars(select(CanonicalIdentity))}
    second = modality_run(env, 77, families[1])
    q = pub.create_proposal(db, run=second, user=user, store=store)
    assert q['action'] == 'create'
    assert q['identity']['keys'][1][1] == 'organization_notice_modality'
    two = apply(env, approve(env, q))
    assert one['concurso_id'] != two['concurso_id']
    assert count(db, Concurso) == count(db, ConcursoVersion) == 2
    for key, target_id in old_claims.items():
        assert db.get(CanonicalIdentity, key).concurso_id == target_id
    for run, target_id in ((first, one['concurso_id']), (second, two['concurso_id'])):
        again = run.model_copy(deep=True)
        again.run_id += '-next'
        result = pub.create_proposal(db, run=again, user=user, store=store)
        assert result['action'] == 'update' and result['concurso_id'] == target_id
    # A third external identifier with the second family remains a possible
    # duplicate, even though its common legacy claim belongs to the first one.
    duplicate = modality_run(env, 88, families[1])
    with pytest.raises(HTTPException) as exc:
        pub.create_proposal(db, run=duplicate, user=user, store=store)
    assert exc.value.status_code == 409
    ambiguous = modality_run(env, 99, 'Selecao')
    with pytest.raises(HTTPException) as exc:
        pub.create_proposal(db, run=ambiguous, user=user, store=store)
    assert exc.value.status_code == 409


def test_proposal_predating_first_identity_requires_recomparison(env):
    from test_tenderproof_canonical import approve
    from test_tenderproof_publication import apply
    db, _, user, old, _, store = env
    db.delete(old)
    db.commit()
    first = modality_run(env, 42, 'Concurso Publico')
    second = modality_run(env, 77, 'Processo Seletivo Publico')
    p = approve(env, pub.create_proposal(db, run=first, user=user, store=store))
    q = approve(env, pub.create_proposal(db, run=second, user=user, store=store))
    apply(env, p)
    with pytest.raises(HTTPException) as exc:
        apply(env, q)
    assert exc.value.status_code == 409
    fresh = pub.create_proposal(db, run=second, user=user, store=store)
    assert fresh['proposal_hash'] != q['proposal_hash']
    assert apply(env, approve(env, fresh))['state'] == 'applied'
