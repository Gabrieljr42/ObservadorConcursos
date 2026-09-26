"""Close the pinned Pedrinhas review through normal proposal controls."""
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from sqlalchemy import select
from app.database import SessionLocal
from app.models import User
from app.tenderproof import amendment, publication, review_cases
from app.tenderproof.continuous_store import get_continuous_store
from app.tenderproof.publication_models import PublicationOutbox
from app.tenderproof.store import get_store

ROOT = Path('/var/lib/observador/tenderproof/product-completion')
INPUT = ROOT / 'delivery-pedrinhas-input-20260909.json'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--apply-receipt', type=Path)
    args = parser.parse_args()
    payload = json.loads(INPUT.read_text(encoding='utf-8'))
    assert payload['concurso_id'] == 3
    assert payload['amendment_document']['sha256'] == 'abf214200dfba8427d9597ac905e5b1b6a3e7920f03b642dcdcbbd22060c0bbd'
    queue, store = get_continuous_store(), get_store()
    run = store.get_run(payload['run_id'])
    with SessionLocal() as db:
        user = db.get(User, run.owner_user_id)
        publication.authorize(user)
        report = {'authorization': payload['authorization'], 'input': str(INPUT)}
        if args.apply_receipt:
            saved = json.loads(args.apply_receipt.read_text(encoding='utf-8'))['proposal']
            proposal = publication.get_proposal(db, saved['id'], user)
            assert proposal['proposal_hash'] == saved['proposal_hash']
            if proposal['state'] == 'proposed':
                publication.approve_proposal(db, proposal_id=proposal['id'], proposal_hash=proposal['proposal_hash'],
                    fields=list(payload['changes']), user=user, store=store, authorization=payload['authorization'])
            result = publication.apply_proposal(db, proposal_id=proposal['id'], proposal_hash=proposal['proposal_hash'], user=user, store=store)
            repeated = publication.apply_proposal(db, proposal_id=proposal['id'], proposal_hash=proposal['proposal_hash'], user=user, store=store)
            assert result['version_id'] == repeated['version_id']
            report['application'] = result
            report['idempotent_version'] = repeated['version_id']
            report['verification'] = amendment.verify_applied(db, proposal['id'], user)
            assert report['verification']['ok']
            outbox = db.scalar(select(PublicationOutbox).where(PublicationOutbox.proposal_id == proposal['id']))
            if outbox:
                report['notifications'] = publication.drain_outbox(db, outbox_id=outbox.id, user=user)
            report['review_after'] = queue.review_for_run(run)
            assert not report['review_after']['pending']
        else:
            case = review_cases.read(queue, payload['case_id'], run.owner_user_id)
            decisions = []
            for document in case['documents']:
                sha = document['artifact']['sha256']
                changes = sha == payload['amendment_document']['sha256']
                decision = {'sha256': sha, 'page': 1, 'snippet': document['pages'][0]['text'][:2000],
                    'effect': 'field_changes' if changes else 'reflected_in_selected_document',
                    'reason': ('Conferência automatizada sob autorização delegada do usuário em 09/09/2026, sem alegar leitura humana. ' +
                        ('O ato altera inscrições e prova; manter pendência até aplicação dos três campos propostos com proveniência.' if changes else
                         'Este é o edital-base selecionado, preservado como versão histórica. A mudança posterior é atribuída exclusivamente à retificação.'))}
                if changes:
                    decision['changes'] = [{'field_name': name, **value} for name,value in payload['changes'].items()]
                decisions.append(decision)
            report['document_review'] = review_cases.approve(queue, store, run, payload['case_id'], payload['review_hash'], decisions)
            assert queue.review_for_run(run)['pending']
            report['proposal'] = amendment.create_proposal(db, user=user, **payload)
        stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
        receipt = ROOT / ('delivery-pedrinhas-' + ('applied-' if args.apply_receipt else 'proposed-') + stamp + '.json')
        receipt.write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str), encoding='utf-8')
        view = report.get('application') or report['proposal']
        print(json.dumps({'receipt': str(receipt), 'proposal_id': view['id'], 'proposal_hash': view['proposal_hash'],
                          'state': view['state'], 'version_id': view.get('version_id')}, ensure_ascii=False))


if __name__ == '__main__':
    main()
