"""Apply the reviewed batch under the user's 2026-09-09 authorization.

Uses ordinary publication guards; hashes and fields are pinned to that review.
No collection, permission change, direct catalogue write or paid processing.
"""
import json
from datetime import datetime, timezone
from pathlib import Path
from app.database import SessionLocal
from app.models import User
from app.tenderproof.publication_models import PublicationProposal
from app.tenderproof.publication import approve_proposal, apply_proposal, get_proposal
from app.tenderproof.store import get_store

BASE_FIELDS = ['titulo', 'orgao', 'edital_numero', 'inscricao_inicio', 'inscricao_fim']
PROPOSALS = [
    ('tpp-2eed3f07a9ec541023f84e38bd0c463a', 'bc515e08a0e2bb2dfe3224ac4b198f0b16a18f9dafceea46f08ad256019c2c4c', BASE_FIELDS + ['prova_data']),
    ('tpp-7a2b5eeacf764476090fdf2073985f7f', '8f748f1ca83b9cb95ec0ded506fdbf2f422716f4f76263dc6e6c2da30706b02d', BASE_FIELDS),
    ('tpp-2e3e9a0fcde2c34490f9f9a0f5b94027', '8612f58d408bec402c4853693f25cc8e1c8589445e13c25f8579a46db7fa7232', BASE_FIELDS),
    ('tpp-ea29153c0ae799f739c1d3da5537bbd7', '22803906ecdfd34242fbe921623bd4f967d5bf3404397affcc96da44af086aec', BASE_FIELDS),
    ('tpp-da2c7e234ffe849e9ad63d59a20c19dc', '180be561c445cfa0b1ab856d8d57d0b463c892780b3d8a0d023db215810ac10e', BASE_FIELDS),
    ('tpp-0477b006bf4c0d77f3380039348de9ba', '1e561750f15a84c28a99f0e34740dee42ab234462b4a67c732b04d3931d23493', BASE_FIELDS),
    ('tpp-3fa0e13d962d3b4e15feaf66b55cf318', '6d7d085d68673c16012904addb36e3c2a00e0433189112c743fe7fcd089d6b1e', BASE_FIELDS),
]

def main():
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    output = Path('/var/lib/observador/tenderproof/product-completion/lote-01-review') / ('application-' + stamp + '.json')
    report = {'authorization': 'User instruction on 2026-09-09: Não precisa pedir minha permissão, se achar que precisa ir, pode ir. Applied to the seven independently reviewed batch candidates; unproven fields excluded.', 'review_reference': 'docs/ENTREGA-LOTE-01-CONFERENCIA.md', 'proposals': []}
    for proposal_id, expected_hash, fields in PROPOSALS:
        item = {'proposal_id': proposal_id, 'proposal_hash': expected_hash, 'fields': fields}
        with SessionLocal() as db:
            try:
                proposal = db.get(PublicationProposal, proposal_id)
                if proposal is None or proposal.proposal_hash != expected_hash:
                    raise ValueError('Reviewed proposal missing or changed')
                user = db.get(User, proposal.owner_user_id)
                store = get_store()
                if proposal.state == 'applied':
                    item['application'] = get_proposal(db, proposal_id, user)
                    item['already_applied'] = True
                else:
                    item['approval'] = approve_proposal(db, proposal_id=proposal_id, proposal_hash=expected_hash, fields=fields, user=user, store=store)
                    item['application'] = apply_proposal(db, proposal_id=proposal_id, proposal_hash=expected_hash, user=user, store=store)
            except Exception as exc:
                db.rollback()
                item['error'] = str(getattr(exc, 'detail', str(exc)))
        report['proposals'].append(item)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str), encoding='utf-8')
    print(json.dumps({'receipt': str(output), 'results': [{'proposal_id': i['proposal_id'], 'state': i.get('application', {}).get('state'), 'concurso_id': i.get('application', {}).get('concurso_id'), 'version_id': i.get('application', {}).get('version_id'), 'error': i.get('error')} for i in report['proposals']]}, ensure_ascii=False))

if __name__ == '__main__':
    main()
