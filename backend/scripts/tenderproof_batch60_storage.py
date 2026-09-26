"""Read-only size/hash measurement of the completed isolated batch60 replay."""
import hashlib
import json
from pathlib import Path
from datetime import datetime,timezone

def main():
    root=Path('.tenderproof/r60replay').resolve()
    replay=json.loads(Path('../docs/tenderproof-batch60-continuous-replay.json').read_text(encoding='utf-8'))
    assert replay['passed'] and Path(replay['root']).resolve()==root
    assert not any(p.is_symlink() for p in root.rglob('*'))
    files=[p for p in root.rglob('*') if p.is_file()]
    artifacts=[p for p in (root/'artifacts').rglob('*') if p.is_file()]
    unique={}
    total=0
    for path in artifacts:
        data=path.read_bytes()
        if not data.startswith(b'%PDF'):continue
        total+=1
        unique[hashlib.sha256(data).hexdigest()]=len(data)
    expected={row['document_sha256'] for row in replay['sources']}
    assert set(unique)==expected
    report={'measured_at':datetime.now(timezone.utc).isoformat(),'root':str(root),
        'scope':'Completed19-source two-cycle offline replay on one local shared volume; not production growth forecast.',
        'source_entries':len(replay['sources']),'pdf_files':total,'unique_pdf_hashes':len(unique),
        'physical_artifact_bytes':sum(p.stat().st_size for p in artifacts),'unique_pdf_bytes':sum(unique.values()),
        'all_volume_files':len(files),'all_volume_bytes':sum(p.stat().st_size for p in files),
        'sqlite_files':[{'file':p.relative_to(root).as_posix(),'bytes':p.stat().st_size} for p in files if p.suffix=='.sqlite3'],
        'retention_deletion_performed':False,'network_requests':0,'passed':True,
        'note':'Evidence retained. Two Consulplan source IDs may share a PDF hash; sources are not distinct documents.'}
    Path('../docs/tenderproof-batch60-storage-measurement.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report,ensure_ascii=True))

if __name__=='__main__':main()
