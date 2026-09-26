"""Measured final-batch gate. Explicit blocked sources are never certified."""
import argparse
import hashlib
import json
from datetime import datetime,timezone
from pathlib import Path
from xml.etree import ElementTree

DOCS=Path('../docs');BACKEND=Path('.')
def read(name):return json.loads((DOCS/name).read_text(encoding='utf-8-sig'))
def junit(path):
    suites=list(ElementTree.parse(path).getroot().iter('testsuite'))
    result={k:sum(int(s.get(k,0)) for s in suites) for k in ('tests','failures','errors','skipped')}
    result['passed']=result['tests']-result['failures']-result['errors']-result['skipped']
    return result

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--accept-bounded',action='store_true')
    parser.add_argument('--mixed-reports',nargs='+',required=True)
    args=parser.parse_args()
    audit=read('tenderproof-batch99-current-validation.json');assert not audit['audit_errors']
    valid={r['source'] for r in audit['sources'] if r['samples']}
    assert valid and all(r['two_cycles_same_candidate_verified'] for r in audit['sources'] if r['samples'])
    replay_names=['tenderproof-batch99-continuous-replay13.json','tenderproof-batch99-continuous-replay-sections.json','tenderproof-batch99-continuous-replay-fapese.json']
    recovery_names=['tenderproof-batch99-recovery-validation13.json','tenderproof-batch99-sections-recovery-validation.json','tenderproof-batch99-fapese-recovery-validation.json']
    replay_sources=set();recovery_sources=set();mixed_sources=set()
    for name in replay_names:
        report=read(name);assert report['passed']
        for row in report['sources']:
            assert row['passed'] and len(row['cycles'])==2
            assert all(c['valid_observations']==1 and c['observations']==1 for c in row['cycles'])
            replay_sources.add(row['source'])
    for name in recovery_names:
        report=read(name);assert report['passed']
        for row in report['sources']:
            assert row['passed'] and row['crash_exitcode']==73 and row['recover_exitcode']==0
            assert row['recovered']['driver_calls']==0 and row['recovered']['downloads']==0
            assert row['recovered']['observations']==1 and row['recovered']['repeat_result']['status']=='not_claimed'
            recovery_sources.add(row['source'])
    for name in args.mixed_reports:
        report=read(name);assert report['passed'] and len(report['rounds'])==2
        for row in report['rounds']:
            assert row['initial_backlog']>0 and row['final_backlog']==0
            assert row['workers_confirmed_terminal'] and row['actual_workers_confirmed_terminal']
        mixed_sources.update(report['valid_sources'])
    assert replay_sources==recovery_sources==mixed_sources==valid
    publication=read('tenderproof-batch99-publication-live.json')
    assert publication['temporary_database_removed'] and publication['counts']['notifications']==0
    assert {r['source'] for r in publication['samples']}==valid
    assert publication['sources_with_creation']==['legatus_open']
    material=read('tenderproof-batch99-material-update.json');assert material['passed'] and material['temporary_volume_removed']
    regression=junit(BACKEND/'.tenderproof/batch99-integrated-regression.xml')
    pg=junit(BACKEND/'.tenderproof/batch99-post-final-postgres.xml')
    assert regression['passed']>=1050 and regression['errors']==regression['failures']==0
    assert pg['passed']>=89 and pg['errors']==pg['failures']==pg['skipped']==0
    review=read('tenderproof-batch99-post-review.json')
    assert review['outcome']=='no_confirmed_blocking_acquisition_defect_downstream_access_corrected'
    assert review['final_postgresql_validation']['cleanup']['container_absent']
    assert read('tenderproof-batch99-identity-review.json')['remediation']['state']=='implemented_verified'
    operations=read('tenderproof-batch99-operations-review.json')
    # The operations review must state its own pass decision after verifying
    # backups, resources and the explicit scope of inherited runtime evidence.
    assert operations.get('passed') is True
    final_review=read('tenderproof-batch99-final-review.json')
    assert final_review['passed'] and final_review['outcome']=='technical_integration_approved_for_bounded_partial_scope'
    plan=read('tenderproof-rollout-plan.json');batch=next(b for b in plan['batches'] if b['cumulative_sources']==99)
    assert next(b for b in plan['batches'] if b['cumulative_sources']==60)['gate']=='accepted_bounded_partial_scope_with_blocked_sources'
    blocked=set(batch['sources'])-valid
    acceptance=read('tenderproof-rollout-acceptance.json');rows={r['source']:r for r in acceptance['sources']}
    assert all(rows[s]['blocker'] and rows[s]['next_action'] for s in blocked)
    names=['tenderproof-batch99-current-validation.json','tenderproof-batch99-publication-live.json','tenderproof-batch99-material-update.json','tenderproof-batch99-post-review.json','tenderproof-batch99-identity-review.json','tenderproof-batch99-operations-review.json','tenderproof-batch99-final-review.json',*replay_names,*recovery_names,*args.mixed_reports]
    report={'validated_at':datetime.now(timezone.utc).isoformat(),'passed':True,'accepted':args.accept_bounded,
        'scope':'Bounded sampled acquisition, continuous tracking, deduplication and recovery. Canonical review exercised for every valid source; only one new source created a contest. Blocked sources excluded; no full-source coverage or production activation.',
        'valid_sample_sources':sorted(valid),'blocked_sources':sorted(blocked),'registration':audit['registration'],
        'regression':regression,'postgres_tests':pg,'canonical_creation_sources':publication['sources_with_creation'],
        'canonical_blocked_sources':sorted({s['source'] for s in publication['samples'] if s['state']=='blocked'}),
        'production_enabled':False,'input_reports':[{'file':name,'sha256':hashlib.sha256((DOCS/name).read_bytes()).hexdigest()} for name in names]}
    (DOCS/'tenderproof-batch99-gate-validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    if args.accept_bounded:
        state='accepted_bounded_partial_scope_with_blocked_sources'
        for source in valid:
            row=rows[source];row['homologation_state']='partial'
            row['homologation_scope']='Dois ciclos com PDF oficial, coleta contínua, deduplicação e retomada comprovados no escopo restrito; publicação sujeita às guardas documentadas.'
            row['next_action']='Acompanhar alterações e ampliar cobertura somente com novas evidências; revisar impedimentos canônicos quando presentes.'
            row['evidence'].append('tenderproof-batch99-gate-validation.json')
        acceptance['batch99_gate']=state;acceptance['sources']=list(rows.values())
        batch['gate']=state;batch['accepted_at']=report['validated_at'];batch['accepted_sources']=sorted(valid);batch['blocked_sources']=sorted(blocked)
        for filename,value in [('tenderproof-rollout-acceptance.json',acceptance),('tenderproof-rollout-plan.json',plan)]:
            (DOCS/filename).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'passed':True,'accepted':args.accept_bounded,'partial_sources':len(valid),'blocked_sources':len(blocked),'regression':regression,'postgres':pg}))

if __name__=='__main__':main()
