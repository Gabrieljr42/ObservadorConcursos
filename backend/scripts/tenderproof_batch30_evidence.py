"""Consolidate batch30 evidence; bounded acceptance requires all measured gates."""
import argparse
import json
import sys
from pathlib import Path
from datetime import datetime, timezone
from xml.etree import ElementTree
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.tenderproof.source_adapters import SOURCE_ADAPTERS

DOCS=Path('../docs')
REPORTS=[
    'tenderproof-batch30-shared-live.json','tenderproof-batch30-shared-alternate-live.json',
    'tenderproof-batch30-edital-live.json','tenderproof-batch30-own-live.json',
    'tenderproof-batch30-institutional-live.json','tenderproof-batch30-reis-json-live.json',
    'tenderproof-batch30-ufu-live.json','tenderproof-batch30-ufu-ta-live.json',
    'tenderproof-batch30-uniselva-live.json',
]


def read(name): return json.loads((DOCS/name).read_text(encoding='utf-8'))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--accept-bounded',action='store_true')
    args=parser.parse_args()
    plan=read('tenderproof-rollout-plan.json')
    batch=next(b for b in plan['batches'] if b['cumulative_sources']==30)
    sources=batch['sources']
    accepted=args.accept_bounded or batch['gate']=='accepted_bounded_partial_scope_with_blocked_sources'
    assert len(sources)==20 and all(s in SOURCE_ADAPTERS for s in sources)
    reports={name:read(name) for name in REPORTS}
    replay=read('tenderproof-batch30-continuous-replay-verified.json')
    blocked=read('tenderproof-batch30-blocked-replay.json')
    assert replay['passed'] and blocked['passed']
    material=read('tenderproof-batch30-material-update.json')
    assert material['passed'] and {r['database'] for r in material['executions']}=={'sqlite','postgresql'}
    mixed=read('tenderproof-batch30-mixed-retry1-validation.json')
    assert mixed['passed'] and len(mixed['rounds'])==2
    for iteration in mixed['rounds']:
        assert iteration['initial_backlog']==40 and iteration['final_backlog']==0 and iteration['exitcodes']==[0,0]
        assert len(iteration['sources'])==20 and sum(r['valid_observations']==1 for r in iteration['sources'])==16
    byte_gate=read('tenderproof-batch30-byte-gate-validation.json')
    assert byte_gate['passed'] and byte_gate['tests']['regression']['passed']==718
    recovery_name='tenderproof-batch30-byte-gate-recovery.json' if accepted else 'tenderproof-batch30-document-gate-recovery.json'
    recovery=read(recovery_name)
    assert recovery['passed'] and {r['source'] for r in recovery['sources']}=={r['source'] for r in replay['sources']}
    assert {r['source'] for r in replay['sources']+blocked['sources']}==set(sources)
    junit=Path('.tenderproof/batch30-final-contract-tests.xml')
    suites=list(ElementTree.parse(junit).getroot().iter('testsuite'))
    assert sum(int(s.get('tests',0)) for s in suites)==132
    assert not any(int(s.get('failures',0))+int(s.get('errors',0)) for s in suites)
    rows=[]
    for source in sources:
        cycles=[(name,r) for name,data in reports.items() for r in data['cycles'] if r['source']==source]
        valid=[(name,r,a) for name,r in cycles for a in r['attempts'] if a.get('validation_status')=='valid' and a.get('durable_hash_verified')]
        evidence=list(dict.fromkeys(name for name,_ in cycles))
        continuous='tenderproof-batch30-continuous-replay-verified.json' if valid else 'tenderproof-batch30-blocked-replay.json'
        limitations=['Only bounded official samples; no whole-source coverage certification.',
                      'Bounded queue proof uses retry_base_s=1; default30 failed the five-minute rehearsal. Documentary effects are not interpreted or released automatically; unacquired supplementary bytes are outside monitoring.']
        shared_evidence=['tenderproof-batch30-document-gate-validation.json','tenderproof-batch30-byte-gate-validation.json','tenderproof-batch30-mixed-validation.json','tenderproof-batch30-mixed-retry1-validation.json']
        if valid:
            shared_evidence.append(recovery_name)
        if source=='exame_open':
            shared_evidence.extend(['tenderproof-batch30-change-validation.json','tenderproof-batch30-complementary-change-validation.json','tenderproof-batch30-document-hold-publication.json','tenderproof-batch30-material-update.json'])
        if source=='ufu_selection':limitations.append('Technical-administrative notice validated. Teacher selections with general/specific complementary notices require joint review.')
        if source=='reisesreis_open':limitations.append('Fresh JSON-preserving capture replaces initial transformed listing for replay. Terminal evidence covers current API filter only.')
        if source=='ibfc_open':limitations.append('Observed rich-text heading repaired and tested. Selection490 has three original notices; selection494 course/apprentice scope not homologated.')
        blocker=None if valid else {
            'rbo_open':'Sampled details have a retified notice or no PDF; no unambiguous original acquired.',
            'idecan_open':'No contest files in sampled portal; official alternate portal returned403.',
            'ibfc_open':'Sample496 only retified; sample490 has three distinct original notices requiring explicit review.',
            'admtec_open':'Sample121 only retified; other samples contain malformed official URLs with literal question marks in filenames.',
        }[source]
        rows.append(dict(source=source,offline_validation='tested',
            live_adapter_observation='observed_valid_sample' if valid else 'observed_document_blocked',
            homologation_state=('partial' if valid else 'blocked') if accepted else 'pending',
            homologation_scope=('Bounded sampled route and primary document only; no whole-source certification.' if valid else 'Not homologated; observed documentary impediment retained.') if accepted else 'Batch30 acceptance pending; bounded evidence only.',
            last_validation=datetime.now(timezone.utc).isoformat(),
            evidence=['tenderproof-batch30-current-validation.json',continuous,*shared_evidence,*evidence],
            samples=[dict(external_id=a['candidate']['external_id'],cycle=r['cycle'],run_id=a['run_id'],document_sha256=a['artifact']['sha256'],evidence=name) for name,r,a in valid],
            coverage='partial',browser_dependency='HTTP samples; zero browser sessions',
            limitations=limitations,blocker=blocker,next_action=('Expand route/document coverage within measured limits.' if valid else 'Resolve documented official-document impediment before homologation.') if accepted else 'Complete the remaining batch quality gate evidence before expansion.'))
    gate='accepted_bounded_partial_scope_with_blocked_sources' if accepted else 'not_accepted'
    output=dict(observed_at=datetime.now(timezone.utc).isoformat(),batch_gate=gate,
        tests=dict(passed=132,failed=0,junit='backend/'+str(junit).replace('\\','/')),
        continuous_replay=dict(valid_sources=16,blocked_sources=4,cycles=40,jobs=80,network_requests=0),
        integrated_validation='tenderproof-batch30-byte-gate-validation.json',
        mixed_queue_validation='tenderproof-batch30-mixed-retry1-validation.json',
        material_update_validation='tenderproof-batch30-material-update.json',
        whole_source_coverage_certified=False,production_enabled=False,
        real_process_recovery_sources=16,controlled_document_change_sources=['exame_open'],sources=rows)
    (DOCS/'tenderproof-batch30-current-validation.json').write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    acceptance=read('tenderproof-rollout-acceptance.json');existing={r['source']:r for r in acceptance['sources']}
    existing.update({r['source']:r for r in rows});acceptance['sources']=list(existing.values())
    acceptance['batch30_gate']=gate
    (DOCS/'tenderproof-rollout-acceptance.json').write_text(json.dumps(acceptance,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    if accepted:
        batch['gate']=gate
        batch['accepted_at']=output['observed_at']
        batch['accepted_sources']=16
        batch['blocked_sources']=['rbo_open','idecan_open','ibfc_open','admtec_open']
        batch['scope']='Sampled routes and primary documents only; blocked sources excluded from homologation; production remains disabled.'
        batch['operational_rehearsal']={'retry_base_s':1,'workers':2,'same_host_sqlite':True,'jobs_per_round':40,'rounds':2,'production_throughput_certified':False}
        batch['evidence']=list(dict.fromkeys(batch['evidence']+[recovery_name,'tenderproof-batch30-byte-gate-validation.json','tenderproof-batch30-material-update.json','tenderproof-batch30-mixed-validation.json','tenderproof-batch30-mixed-retry1-validation.json']))
        (DOCS/'tenderproof-rollout-plan.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('20 source records updated; '+gate+'; production remains disabled')


if __name__=='__main__':main()
