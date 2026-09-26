"""Replay internal notification matching for the three applied cargo versions."""
import json
from datetime import datetime, timezone
from pathlib import Path
from app.database import SessionLocal
from app.models import Concurso, ConcursoVersion, User
from app.notifications import create_notifications_for_version
from app.tenderproof.publication import authorize


def main():
    report = {'external_delivery': False, 'versions': []}
    with SessionLocal() as db:
        authorize(db.get(User, 1))
        for version_id, concurso_id in ((16, 4), (17, 9), (18, 10)):
            version = db.get(ConcursoVersion, version_id)
            contest = db.get(Concurso, concurso_id)
            assert version and version.concurso_id == contest.id and 'cargos' in version.changed_fields
            first = create_notifications_for_version(db, concurso=contest, version=version)
            db.commit()
            repeated = create_notifications_for_version(db, concurso=contest, version=version)
            db.commit()
            assert repeated == 0
            report['versions'].append({'version_id': version_id, 'created': first, 'repeated_created': repeated})
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    path = Path('/var/lib/observador/tenderproof/product-completion') / ('delivery-job-notifications-' + stamp + '.json')
    path.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report | {'receipt': str(path)}))


if __name__ == '__main__':
    main()
