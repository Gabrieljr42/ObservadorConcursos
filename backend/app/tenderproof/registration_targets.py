"""Read-only comparison of scoped amendments with the current catalogue.

This is deliberately separate from publication: matching a name is not an
approval of the amendment or evidence of its original act.
"""
import hashlib

from fastapi import HTTPException
from sqlalchemy import select

from app.models import Concurso, Source
from app.tenderproof import ocr_regions, review_cases
from app.tenderproof.contracts import Artifact
from app.tenderproof.registration_effects import preview_registration_effects


def compare_role(effect, cargos):
    name = ' '.join(effect['scope']['name'].casefold().split())
    if not isinstance(cargos, list) or not cargos:
        return {'status': 'missing_roles', 'message': 'Os cargos deste concurso ainda precisam ser extraídos e conferidos.'}
    matches = [(index, role) for index, role in enumerate(cargos)
               if isinstance(role, dict) and isinstance(role.get('nome'), str)
               and ' '.join(role['nome'].casefold().split()) == name]
    if len(matches) != 1:
        return {'status': 'ambiguous_role' if matches else 'missing_role',
                'message': 'Há mais de um cargo com esse nome; confira a especialidade e a localidade.' if matches
                else 'A função citada no ato não corresponde a um cargo cadastrado neste concurso.'}
    index, role = matches[0]
    return {'status': 'matched', 'cargo_index': index, 'cargo_name': role['nome'],
            'cargo_snapshot': role, 'cargo_hash': review_cases.digest(role),
            'message': 'Cargo localizado. Confira o ato original e aprove o efeito documental antes da publicação.',
            'proposed_registration': {'start': effect['new_period']['start'],
                                      'end': effect['new_period']['end'],
                                      'end_time': effect['new_period']['end_time']}}


def compare_catalogue(db, queue, store, run, case_id, revision_hash, region_id):
    case = review_cases.read(queue, case_id, run.owner_user_id)
    if case['run_id'] != run.run_id or case['revision_hash'] != revision_hash:
        raise HTTPException(409, 'A revisão mudou; atualize antes de conferir o cargo')
    with queue._db() as connection:
        if review_cases.revision(queue, run, connection) != case['revision']:
            raise HTTPException(409, 'Os documentos mudaram; prepare uma nova revisão')
    region = next((item for item in case.get('ocr_regions', []) if item['id'] == region_id), None)
    if not region:
        raise HTTPException(404, 'Região não encontrada nesta revisão')
    document = next((doc for doc in case['documents'] if doc['artifact']['sha256'] == region['document_sha256']), None)
    page = next((item for item in document['pages'] if item['page_number'] == region['page_number']), None) if document else None
    if page is None:
        raise HTTPException(409, 'Página da região não encontrada nesta revisão')
    artifact = Artifact.model_validate(document['artifact'])
    content = store.load_artifact_bytes(artifact)
    if content is None or hashlib.sha256(content).hexdigest() != artifact.sha256:
        raise HTTPException(409, 'PDF preservado ausente ou divergente')
    # Never accept suggestions supplied by the browser or persisted previews.
    ocr_regions.decision_text(case, document, page, {'region_id': region_id})
    rebuilt = ocr_regions.region_from_page(page, artifact.sha256, region['bounds'])
    effects = preview_registration_effects(run.source, rebuilt)
    if not effects:
        raise HTTPException(409, 'Nenhuma reabertura por função reproduzida nesta região')
    candidate = next((c for c in run.candidates if c.candidate_id == run.selected_candidate_id), None)
    if not candidate or candidate.source != run.source or not candidate.external_id:
        raise HTTPException(409, 'Candidato sem identidade correspondente à fonte')
    sources = list(db.scalars(select(Source).where(Source.source_type == run.source)))
    contests = list(db.scalars(select(Concurso).where(Concurso.source_id.in_([s.id for s in sources]),
                                                   Concurso.external_id == candidate.external_id)))
    base = {'case_id': case_id, 'revision_hash': revision_hash, 'region_id': region_id,
            'review_required': True, 'published': False, 'effects': effects}
    if len(sources) != 1 or len(contests) > 1:
        return base | {'status': 'ambiguous_identity', 'message': 'Identidade duplicada no catálogo; revise a associação antes de alterar cargos.'}
    if not contests:
        return base | {'status': 'missing_contest', 'message': 'Este concurso ainda não possui cadastro correspondente no catálogo. Extraia e confira a identidade e os cargos do edital original primeiro.'}
    contest = contests[0]
    from app.tenderproof.publication import _same_url, _revision
    if not _same_url(contest.link_pagina, candidate.detail_url_observed):
        return base | {'status': 'identity_mismatch', 'message': 'A página do concurso cadastrado diverge da origem desta coleta; confira a identidade.'}
    return base | {'status': 'compared', 'concurso_id': contest.id, 'title': contest.titulo,
                   'catalogue_revision': _revision(db, contest),
                   'comparisons': [compare_role(effect, contest.cargos) for effect in effects]}
