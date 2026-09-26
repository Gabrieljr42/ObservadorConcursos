"""Apply the reviewed initial ELO composition using the ordinary publication facade."""
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

PROPOSAL = 'tpa-663ecb1ce990af4cc1c784310cf8b78b'
HASH = '663ecb1ce990af4cc1c784310cf8b78b7ba3f5a9766ba97e73208c470b36a3d8'

def main():
    with SessionLocal() as db:
        record = db.get(PublicationProposal, PROPOSAL)
        assert record and record.proposal_hash == HASH
        payload = record.payload
        assert payload['initial_fields']['inscricao_inicio']['value'] == '2026-08-18T15:00:00-03:00'
        assert payload['initial_fields']['inscricao_fim']['value'] == '2026-09-18T15:00:00-03:00'
        assert payload['initial_fields']['prova_data']['value'] == '2026-10-18'
        assert payload['changes']['etapas_prova']['new'] == 'Objetiva de Múltipla Escolha e Títulos'
        fields = ['titulo', 'orgao', 'edital_numero', 'inscricao_inicio', 'inscricao_fim', 'prova_data',
                  'etapas_prova', 'resultado_final_prazo', 'entrega_titulos_prazo']
        user, store, queue = db.get(User, record.owner_user_id), get_store(), get_continuous_store()
        if record.state == 'proposed':
            publication.approve_proposal(db, proposal_id=PROPOSAL, proposal_hash=HASH, fields=fields,
                user=user, store=store, authorization=payload['authorization'])
        result = publication.apply_proposal(db, proposal_id=PROPOSAL, proposal_hash=HASH, user=user, store=store)
        again = publication.apply_proposal(db, proposal_id=PROPOSAL, proposal_hash=HASH, user=user, store=store)
        assert result['version_id'] == again['version_id'] and result['state'] == 'applied'
        verification = amendment.verify_applied(db, PROPOSAL, user)
        assert verification['ok']
        assert not queue.review_for_run(store.get_run(record.run_id))['pending']
        outbox = db.scalar(select(PublicationOutbox).where(PublicationOutbox.proposal_id == PROPOSAL))
        notifications = publication.drain_outbox(db, outbox_id=outbox.id, user=user)
        path = Path('/var/lib/observador/tenderproof/product-completion') / (
            'delivery-elo-applied-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ') + '.json')
        path.write_text(json.dumps({'application': result, 'verification': verification,
            'idempotent_version': again['version_id'], 'notifications': notifications,
            'authorization': payload['authorization']}, ensure_ascii=False, indent=2, default=str), encoding='utf-8')
        print(json.dumps({'receipt': str(path), 'concurso_id': result['concurso_id'],
            'version_id': result['version_id'], 'state': result['state'], 'review_pending': False}))

if __name__ == '__main__':
    main()
