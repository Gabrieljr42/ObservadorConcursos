"""Re-read preserved CRIS PDF and prepare a normal, unapplied cargo proposal."""
import json
from pathlib import Path
from delivery_next_reextract_quadrix_msconcursos import reextract, proposal, evidence_fields, AUTHORIZATION
from app.database import SessionLocal
from app.tenderproof.store import get_store

def main():
    store = get_store()
    original, run = reextract(store.get_run('tpr-9b5c05415be6'), store)
    jobs = next(field for field in run.fields if field.field_name == 'cargos')
    assert len(jobs.value) == 2 and jobs.value[0]['remuneracao'] == '1726.52'
    with SessionLocal() as db:
        prepared = proposal(db, run, store)
    path = Path('/var/lib/observador/tenderproof/product-completion/delivery-cris-jobs-proposed-20260909.json')
    path.write_text(json.dumps({'authorization': AUTHORIZATION, 'proposal': prepared,
        'artifact_sha256': run.artifact.sha256, 'fields': evidence_fields(run)}, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'receipt': str(path), 'proposal': prepared}, ensure_ascii=False))

if __name__ == '__main__':
    main()
