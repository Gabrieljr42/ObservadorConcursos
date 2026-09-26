"""Propose or apply the three independently checked, pinned cargo tables."""
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from sqlalchemy import select
from app.database import SessionLocal
from app.models import User
from app.tenderproof import publication
from app.tenderproof.publication_models import PublicationOutbox
from app.tenderproof.store import get_store

ROOT = Path('/var/lib/observador/tenderproof/product-completion')
TARGETS = [
    (4, 'jcm_open', '81a021874d8e426e69ad4018ca468513f5918c4bbfdac648e236465a08fdb4e8', 5),
    (9, 'cebraspe_open', 'd09cd7a25a66696b4f30b718ee5a0acc3867b6f1892ec1f5c33c3efca6b2dd49', 7),
    (10, 'fepese_open', 'a23c6ecd25f7a80d1bf6ed790673082f21bf45936ef64e1573856448be08dc11', 20),
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--apply-receipt', type=Path)
    args = parser.parse_args()
    authorization = json.loads((ROOT / 'delivery-pedrinhas-input-20260909.json').read_text())['authorization']
    store = get_store()
    saved = json.loads(args.apply_receipt.read_text()) if args.apply_receipt else None
    report = {'authorization': authorization, 'review': 'Independent PDF comparison, corrected requirements and fees; automated, no human reading claimed.', 'items': []}
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    path = ROOT / ('delivery-roles-' + ('applied-' if saved else 'proposed-') + stamp + '.json')
    for concurso_id, source, sha, count in TARGETS:
        run = store.get_run('delivery-roles-20260909-v3-' + sha[:16])
        assert run and run.source == source and run.artifact.sha256 == sha
        field = next(f for f in run.fields if f.field_name == 'cargos')
        assert field.state.value == 'supported' and len(field.value) == count
        with SessionLocal() as db:
            user = db.get(User, run.owner_user_id)
            if not saved:
                view = publication.create_proposal(db, run=run, concurso_id=concurso_id, user=user, store=store, authorization=authorization)
                assert 'cargos' in view['eligible_fields'], view['blocked_fields'].get('cargos')
            else:
                pinned = next(i['proposal'] for i in saved['items'] if i['concurso_id'] == concurso_id)
                view = publication.get_proposal(db, pinned['id'], user)
                assert view['proposal_hash'] == pinned['proposal_hash']
                if view['state'] == 'proposed':
                    publication.approve_proposal(db, proposal_id=view['id'], proposal_hash=view['proposal_hash'], fields=['cargos'], user=user, store=store, authorization=authorization)
                view = publication.apply_proposal(db, proposal_id=view['id'], proposal_hash=view['proposal_hash'], user=user, store=store)
                repeated = publication.apply_proposal(db, proposal_id=view['id'], proposal_hash=view['proposal_hash'], user=user, store=store)
                assert view['version_id'] == repeated['version_id']
                outbox = db.scalar(select(PublicationOutbox).where(PublicationOutbox.proposal_id == view['id']))
                if outbox:
                    publication.drain_outbox(db, outbox_id=outbox.id, user=user)
            report['items'].append({'concurso_id': concurso_id, 'count': count, 'fields': ['cargos'], 'proposal': view})
            path.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str), encoding='utf-8')
    print(json.dumps({'receipt': str(path), 'items': [{'concurso_id': i['concurso_id'], 'id': i['proposal']['id'], 'hash': i['proposal']['proposal_hash'], 'state': i['proposal']['state'], 'version_id': i['proposal'].get('version_id')} for i in report['items']]}))


if __name__ == '__main__':
    main()
