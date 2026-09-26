"""Create the real Barra Longa initial composed proposal, without applying it.

The script consumes the approved document-effect case and writes only a
normal ``PublicationProposal`` in ``proposed`` state.  It never creates a
``Concurso`` row and never calls the apply endpoint.
"""
import json
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import select

from app.database import SessionLocal
from app.models import Source, User
from app.tenderproof import amendment, review_cases
from app.tenderproof.continuous_store import get_continuous_store
from app.tenderproof.store import get_store

ROOT = Path('/var/lib/observador/tenderproof/product-completion')
DRAFT_RECEIPT = ROOT / 'delivery-elo-effects-draft-20260909.json'
RUN_ID = 'tp-tcj-e637bc3b81b257e6a60e57a48f2d767d-1'
CASE_ID = 'drc-d75046086a8844b48da951df3b4bb2ee'


def _document(case, sha, identity):
    item = next(document for document in case['documents'] if document['artifact']['sha256'] == sha)
    artifact = item['artifact']
    manifest = item.get('document') or item
    url = artifact.get('url_final') or artifact.get('url_requested')
    return {'sha256': sha, 'url': url, 'title': manifest.get('title'),
            'kind': manifest.get('kind'), 'identity': identity, 'artifact': artifact}


def _provenance(item, source_url):
    value = dict(item)
    value['source_url'] = source_url
    value['sha256'] = value.get('sha256') or value.get('document_sha256')
    return value


def main():
    draft = json.loads(DRAFT_RECEIPT.read_text(encoding='utf-8'))
    if draft.get('publication_performed'):
        raise ValueError('O rascunho indica publicação; abortando o preparo inicial')
    queue, store = get_continuous_store(), get_store()
    run = store.get_run(RUN_ID)
    if not run:
        raise ValueError(f'run ausente: {RUN_ID}')
    case_id = draft.get('case_id') or CASE_ID
    if case_id != CASE_ID:
        raise ValueError('caso ELO inesperado')
    case = review_cases.read(queue, case_id, run.owner_user_id)
    if case['run_id'] != RUN_ID:
        raise ValueError('caso não corresponde ao run ELO')
    source_fields = {field.field_name: field.value for field in run.fields}
    candidate = next(item for item in run.candidates if item.candidate_id == run.selected_candidate_id)
    with SessionLocal() as db:
        source = db.scalar(select(Source).where(Source.source_type == run.source))
        if not source:
            raise ValueError(f'fonte sem registro: {run.source}')
        identity = {'source_id': source.id, 'external_id': candidate.external_id,
                    'edital_numero': source_fields.get('edital_numero'),
                    'orgao': source_fields.get('orgao'), 'titulo': source_fields.get('titulo'),
                    'detail_url': candidate.detail_url_observed}
        if not all(identity.get(name) for name in ('external_id', 'edital_numero', 'orgao', 'titulo')):
            raise ValueError('identidade ELO incompleta no run')
        by_sha = {item['artifact']['sha256']: item for item in case['documents']}
        decisions = draft.get('decisions') or case.get('draft')
        if not decisions:
            raise ValueError('rascunho ELO sem decisões documentais')
        amendment_decision = next(item for item in decisions if item.get('effect') == 'field_changes')
        later_sha = amendment_decision['sha256']
        base_sha = next(item['sha256'] for item in decisions if item.get('effect') != 'field_changes')
        base = _document(case, base_sha, identity)
        later = _document(case, later_sha, identity)
        later_url = later['url']
        changes = {}
        for item in amendment_decision.get('changes') or []:
            name = item['field_name']
            changes[name] = {
                'previous': item.get('previous'), 'new': item.get('new'),
                'reason': 'A retificação ELO comprova a alteração deste efeito documental.',
                'provenance': [_provenance(proof, later_url) for proof in item.get('provenance') or []],
            }
        events = [
            {'name': 'Etapas da prova', 'value': changes['etapas_prova']['new'],
             'provenance': changes['etapas_prova']['provenance']},
            {'name': 'Resultado final', 'date': changes['resultado_final_prazo']['new'],
             'end_time': '23:59', 'precision': 'local_time', 'timezone': None,
             'provenance': changes['resultado_final_prazo']['provenance']},
            {'name': 'Entrega dos títulos', 'date': changes['entrega_titulos_prazo']['new'],
             'end_time': '23:59', 'precision': 'local_time', 'timezone': None,
             'provenance': changes['entrega_titulos_prazo']['provenance']},
        ]
        assert all('Até as 23h59' in event['provenance'][0]['snippet'] for event in events[1:])
        # Approving this review leaves the field-changing document pending by
        # design.  Application, which would finalize the gate, is deliberately
        # outside this script.
        review = review_cases.approve(queue, store, run, case_id, case['revision_hash'], decisions)
        if not queue.review_for_run(run).get('pending'):
            raise ValueError('o gate documental foi limpo antes da aplicação')
        user = db.get(User, run.owner_user_id)
        proposal = amendment.create_proposal(
            db, concurso_id=None, source_id=source.id, user=user,
            base_document=base, amendment_document=later, changes=changes,
            reason='Publicação inicial composta pelo edital-base e pela retificação ELO de Barra Longa.',
            authorization=draft.get('authorization'), events=events, run=run, queue=queue, store=store,
            review_case_id=case_id, review_hash=case['revision_hash'])
        if proposal['state'] != 'proposed' or proposal['concurso_id'] is not None:
            raise ValueError('proposta inicial não ficou revisável sem concurso canônico')
        stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
        receipt = ROOT / f'delivery-elo-composed-proposed-{stamp}.json'
        receipt.write_text(json.dumps({'run_id': RUN_ID, 'case_id': case_id,
            'review': review, 'proposal': proposal, 'publication_performed': False},
            ensure_ascii=False, indent=2, default=str), encoding='utf-8')
        print(json.dumps({'receipt': str(receipt), 'proposal_id': proposal['id'],
                          'proposal_hash': proposal['proposal_hash'], 'state': proposal['state'],
                          'concurso_id': proposal['concurso_id']}, ensure_ascii=False))


if __name__ == '__main__':
    main()
