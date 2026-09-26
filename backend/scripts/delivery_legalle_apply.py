"""Apply the independently reviewed Garibaldi composition through the normal facade."""
import json
from datetime import datetime, timezone
from pathlib import Path
from sqlalchemy import select
from app.database import SessionLocal
from app.models import User
from app.tenderproof import publication, amendment
from app.tenderproof.continuous_store import get_continuous_store
from app.tenderproof.publication_models import PublicationProposal, PublicationOutbox
from app.tenderproof.store import get_store

PROPOSAL = 'tpa-ff3ac1092183a78f6795b674c04bd942'
HASH = 'ff3ac1092183a78f6795b674c04bd942f514025ecf0a029944d2a083e0da39b6'

def main():
    with SessionLocal() as db:
        record = db.get(PublicationProposal, PROPOSAL)
        assert record and record.proposal_hash == HASH and record.state == 'proposed'
        payload = record.payload
        fields = list(dict.fromkeys([*payload.get('initial_fields', {}), *payload.get('changes', {})]))
        assert fields and payload['authorization']['human_read'] is False
        user, store, queue = db.get(User, record.owner_user_id), get_store(), get_continuous_store()
        approved = publication.approve_proposal(db, proposal_id=PROPOSAL, proposal_hash=HASH,
            fields=fields, user=user, store=store, authorization=payload['authorization'])
        result = publication.apply_proposal(db, proposal_id=PROPOSAL, proposal_hash=HASH, user=user, store=store)
        again = publication.apply_proposal(db, proposal_id=PROPOSAL, proposal_hash=HASH, user=user, store=store)
        assert result['state'] == 'applied' and result['version_id'] == again['version_id']
        verification = amendment.verify_applied(db, PROPOSAL, user)
        assert verification['ok']
        outbox = db.scalar(select(PublicationOutbox).where(PublicationOutbox.proposal_id == PROPOSAL))
        notifications = publication.drain_outbox(db, outbox_id=outbox.id, user=user) if outbox else []
        path = Path('/var/lib/observador/tenderproof/product-completion') / (
            'delivery-legalle-applied-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ') + '.json')
        path.write_text(json.dumps({'approval': approved, 'application': result,
            'verification': verification, 'idempotent_version': again['version_id'],
            'notifications': notifications, 'fields': fields}, ensure_ascii=False, indent=2, default=str), encoding='utf-8')
        print(json.dumps({'receipt': str(path), 'concurso_id': result['concurso_id'],
            'version_id': result['version_id'], 'state': result['state'], 'idempotent': True,
            'review_pending': False}))

if __name__ == '__main__':
    main()
