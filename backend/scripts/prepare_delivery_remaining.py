"""Create reviewable publication proposals for preserved runs only."""
import json
import sys
sys.path.insert(0, '/app')
from app.database import SessionLocal
from app.models import User
from app.tenderproof import publication
from app.tenderproof.store import get_store

RUNS = {
    'idib_362': 'tp-tcj-b6372819d87e51c185e6427865a5bf62-1',
    'cebraspe_ponta_pora': 'tp-tcj-2b58bacc0b6a5a028ffc292908b9b6da-1',
    'fepese_caxambu': 'tp-tcj-8c4428c810c45812a92132a23bf42958-1',
}

def main():
    store = get_store(); result = {}
    with SessionLocal() as db:
        for label, run_id in RUNS.items():
            run = store.get_run(run_id)
            item = {'run_id': run_id}
            try:
                if run is None:
                    raise ValueError('run_missing')
                user = db.get(User, run.owner_user_id)
                proposal = publication.create_proposal(db, run=run, user=user, store=store)
                item['proposal'] = proposal
            except Exception as exc:
                db.rollback()
                item['error'] = {'type': type(exc).__name__, 'message': str(exc)}
            result[label] = item
    print(json.dumps(result, ensure_ascii=False, default=str))

if __name__ == '__main__': main()
