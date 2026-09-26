"""Measured bounded batch60 gate; never certifies blocked portals or production."""
import argparse
import json
import hashlib
from pathlib import Path
from datetime import datetime,timezone
from xml.etree import ElementTree

DOCS=Path('../docs')
def read(name):return json.loads((DOCS/name).read_text(encoding='utf-8'))
def suite(path):
    rows=list(ElementTree.parse(path).getroot().iter('testsuite'))
    result={key:sum(int(r.get(key,0)) for r in rows) for key in ('tests','failures','errors','skipped')}
    assert result['tests'] and not result['failures'] and not result['errors'],result
    result['passed']=result['tests']-result['skipped']
    return result

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--accept-bounded',action='store_true')
    args=parser.parse_args()
    audit=read('tenderproof-batch60-current-validation.json')
    assert not audit['audit_errors']
    valid={r['source'] for r in audit['sources'] if r['samples']}
    blocked={r['source'] for r in audit['sources'] if not r['samples']}
    assert len(valid)==19 and len(blocked)==11 and all(r['two_cycles_same_candidate_verified'] for r in audit['sources'] if r['samples'])
    replay=read('tenderproof-batch60-continuous-replay.json')
    recovery=read('tenderproof-batch60-recovery-validation.json')
    mixed=read('tenderproof-batch60-mixed-validation.json')
    for proof in (replay,recovery):
        assert proof['passed'] and {r['source'] for r in proof['sources']}==valid
    assert recovery['resources']=={'child_processes_exited':38,'preserved_drivers_closed':True,'recovery_driver_calls':0,'recovery_downloads':0}
    assert mixed['passed'] and len(mixed['rounds'])==2
    for iteration in mixed['rounds']:
        assert iteration['initial_backlog']==42 and iteration['final_backlog']==0
        assert iteration['exitcodes']==[0,0] and iteration['workers_confirmed_terminal']
        assert {r['source'] for r in iteration['sources'] if r['valid_observations']==1}==valid
    publication=read('tenderproof-batch60-publication-live.json')
    assert {s['source'] for s in publication['samples']}==valid
    assert publication['temporary_database_removed'] and publication['counts']['notifications']==0
    assert len(publication['sources_with_creation'])==5
    assert all(s.get('repeat_same_result') or (s['state']=='blocked' and s.get('reason')) for s in publication['samples'])
    material=read('tenderproof-batch60-material-update.json')
    assert material['passed'] and material['temporary_volume_removed']
    assert {r['database'] for r in material['executions']}=={'sqlite','postgresql'}
    regression=suite('.tenderproof/batch60-integrated-regression.xml')
    postgres=suite('.tenderproof/batch60-postgres.xml')
    assert regression['passed']>=871 and postgres['skipped']==0
    # Final review/correction and container cleanup are independently recorded.
    review=read('tenderproof-batch60-review.json')
    cleanup=read('tenderproof-batch60-postgres-validation.json')
    assert review['status']=='corrected_and_focal_tests_passed' and review['validation']['exit_code']==0 and review['validation']['passed']>=28
    for path,digest in review['files_sha256'].items():
        assert hashlib.sha256((Path('..')/path).read_bytes()).hexdigest()==digest
    assert cleanup['passed'] and cleanup['container_removed'] and cleanup['removal_confirmation']
    now=datetime.now(timezone.utc).isoformat()
    report={'validated_at':now,'passed':True,'gate':'accepted_bounded_partial_scope_with_blocked_sources' if args.accept_bounded else 'ready_for_bounded_acceptance',
        'valid_document_sources':sorted(valid),'blocked_sources':sorted(blocked),
        'missing_adapters':audit['registration']['batch_missing_adapters'],
        'canonical_creation_sources':publication['sources_with_creation'],
        'canonical_blocked_sources':sorted(valid-set(publication['sources_with_creation'])),
        'regression':regression,'postgres_tests':postgres,'production_enabled':False,
        'scope':'Sampled discovery, acquisition, deduplication and recovery only. Five sources created isolated canonical entries; fourteen need stronger reviewed identity or explicit existing-target association. Eleven batch entries excluded from homologation; nine lack adapters. No whole-source certification.',
        'evidence':['tenderproof-batch60-current-validation.json','tenderproof-batch60-continuous-replay.json','tenderproof-batch60-recovery-validation.json','tenderproof-batch60-mixed-validation.json','tenderproof-batch60-publication-live.json','tenderproof-batch60-material-update.json','tenderproof-batch60-review.json','tenderproof-batch60-postgres-validation.json']}
    (DOCS/'tenderproof-batch60-gate-validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    if args.accept_bounded:
        acceptance=read('tenderproof-rollout-acceptance.json')
        for row in acceptance['sources']:
            if row['source'] not in valid|blocked:continue
            row['homologation_state']='partial' if row['source'] in valid else 'blocked'
            row['homologation_scope']=report['scope']
            row['evidence'].append('tenderproof-batch60-gate-validation.json')
            row['limitations']=[s for s in row['limitations'] if s!='Batch60 acceptance and batch99 expansion remain pending.']
            if row['source'] in valid:row['next_action']='Expand bounded coverage and resolve canonical review requirements where present.'
        acceptance['batch60_gate']=report['gate']
        (DOCS/'tenderproof-rollout-acceptance.json').write_text(json.dumps(acceptance,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
        plan=read('tenderproof-rollout-plan.json')
        batch=next(b for b in plan['batches'] if b['cumulative_sources']==60)
        batch.update(gate=report['gate'],accepted_at=now,accepted_sources=19,blocked_sources=sorted(blocked),
            missing_adapters=report['missing_adapters'],scope=report['scope'],evidence=report['evidence'])
        (DOCS/'tenderproof-rollout-plan.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(report['gate'])

if __name__=='__main__':main()
