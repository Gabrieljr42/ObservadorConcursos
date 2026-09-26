import json

import pytest
from fastapi import HTTPException

from app.models import Source
from app.tenderproof import registration_targets as targets, ocr_regions, review_cases
from app.tenderproof.registration_effects import preview_registration_effects
from test_tenderproof_registration_effects import region as effect_region
from test_tenderproof_publication import env
from test_tenderproof_review_cases import setup_case


@pytest.mark.parametrize('cargos,status', [
    (None, 'missing_roles'), ([], 'missing_roles'),
    ([{'nome': 'Engenheiro Civil'}], 'missing_role'),
    ([{'nome': 'Analista em Comércio Exterior'}, {'nome': 'analista em comércio exterior'}], 'ambiguous_role'),
    ([{'nome': 'Analista em Comercio Exterior'}], 'missing_role'),
])
def test_cargo_requires_unique_exact_name(cargos, status):
    effect = preview_registration_effects('facepe_selection', effect_region())[0]
    assert targets.compare_role(effect, cargos)['status'] == status


def test_comparison_preserves_other_roles_and_returns_baseline():
    effect = preview_registration_effects('facepe_selection', effect_region())[0]
    cargos = [{'nome': 'Engenheiro Civil'}, {'nome': 'Analista em Comércio Exterior', 'remuneracao': '3950.00'}]
    before = json.dumps(cargos)
    result = targets.compare_role(effect, cargos)
    assert result['cargo_index'] == 1 and result['cargo_snapshot'] == cargos[1]
    assert result['cargo_hash'] == review_cases.digest(cargos[1])
    assert result['proposed_registration']['end'] == '2027-08-30'
    assert json.dumps(cargos) == before


def test_catalogue_identity_integrity_and_no_mutation(env, monkeypatch):
    queue, case, _ = setup_case(env)
    db, _, _, contest, run, store = env
    # Exercise the common comparison with a synthetic gazette raster. The
    # production interpreter stays restricted to FACEPE.
    monkeypatch.setattr(targets, 'preview_registration_effects', lambda source, r: preview_registration_effects('facepe_selection', r))
    lines = effect_region()['text'].splitlines()
    page = {'page_number': 1, 'extraction_method': 'ocr_tesseract', 'extractor_version': 'fixture',
            'ocr': {'image_width': 1000, 'image_height': 1000, 'image_sha256': 'a'*64,
                    'words': [{'text': text, 'bbox': [10, 10+i*30, 900, 20]} for i, text in enumerate(lines)]}}
    region = ocr_regions.region_from_page(page, run.artifact.sha256, [0,0,10000,10000])
    with queue._db(write=True) as connection:
        row = connection.execute('SELECT payload FROM document_effect_cases WHERE id=?', (case['id'],)).fetchone()
        payload = json.loads(row['payload'])
        payload['documents'][0]['pages'] = [page]
        payload['ocr_regions'] = [region | {'preview_effects': [{'forged': True}]}]
        connection.execute('UPDATE document_effect_cases SET payload=? WHERE id=?', (json.dumps(payload), case['id']))
    call = lambda **kw: targets.compare_catalogue(db, queue, kw.get('store',store), kw.get('run',run), case['id'], kw.get('revision_hash',case['revision_hash']), region['id'])
    assert call()['comparisons'][0]['status'] == 'missing_roles'
    contest.cargos = [{'nome': 'Analista em Comércio Exterior'}]
    db.commit()
    initial = (contest.inscricao_inicio, contest.inscricao_fim, json.dumps(contest.cargos))
    result = call()
    assert result['comparisons'][0]['status'] == 'matched' and result['published'] is False
    assert result['effects'][0]['new_period']['end'] == '2027-08-30'
    db.refresh(contest)
    assert initial == (contest.inscricao_inicio, contest.inscricao_fim, json.dumps(contest.cargos))
    assert review_cases.read(queue, case['id'], run.owner_user_id)['approved_at'] is None
    contest.external_id = 'different-selection'
    db.commit()
    assert call()['status'] == 'missing_contest'
    contest.external_id = run.candidates[0].external_id
    contest.link_pagina = 'https://example.invalid/other'
    db.commit()
    assert call()['status'] == 'identity_mismatch'
    db.add(Source(name='Duplicate', source_type=run.source, base_url='https://example.invalid'))
    db.commit()
    assert call()['status'] == 'ambiguous_identity'
    for overrides in ({'revision_hash':'0'*64}, {'run':run.model_copy(update={'owner_user_id':2})}):
        with pytest.raises(HTTPException): call(**overrides)
    monkeypatch.setattr(store, 'load_artifact_bytes', lambda artifact: b'tampered')
    with pytest.raises(HTTPException): call()
