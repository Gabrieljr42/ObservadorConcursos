"""Five-minute demo artifacts, strictly offline and disposable databases."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import json
import os
import tempfile
from time import perf_counter
from app.tenderproof.publication_demo import run_demo
from app.tenderproof.recovery import Strategy
from app.tenderproof.recovery_store import RecoveryStore
from app.tenderproof.recovery_validation import validate_strategy, load_snapshot, POLICY
from app.tenderproof.service import TenderProofService
from app.tenderproof.store import TenderProofStore
from app.tenderproof.sources import IMESO_SOURCE, IMESO_LISTING, build_imeso_mock_driver


def main():
    report = {'label':'Demonstração offline pequena; sem alegação estatística', 'publication':run_demo()}
    with tempfile.TemporaryDirectory(prefix='tenderproof-demo-') as directory:
        root=Path(directory)
        os.environ['TENDERPROOF_ARTIFACT_DIR']=str(root/'artifacts')
        os.environ['TENDERPROOF_PROCESSING_DIR']=str(root/'processing')
        good=Strategy(cards=('.old-card','.new-card'),details=('.detail',),documents=('.notice',))
        bad=Strategy(cards=('.broken',),details=('a',),documents=('a',))
        # Server-owned full ten-case suite, never modified by the strategy.
        good_report, bad_report=validate_strategy(good),validate_strategy(bad)
        report['recovery']={'correct_strategy':good_report,'incorrect_strategy':bad_report}
        if not good_report['passed']:
            raise RuntimeError('demo strategy did not pass independent suite')
        store=RecoveryStore(root/'recovery.sqlite3')
        proposal=store.propose(1,good)
        proposal=store.validate(1,proposal['id'])
        proposal=store.observe(1,proposal['id'],load_snapshot('09_recovered_navigation'),POLICY)
        proposal=store.review(1,proposal['id'],True,'Explicit synthetic demo review')
        proposal=store.activate(1,proposal['id'])
        report['recovery']['active']=proposal['state']
        report['recovery']['rollback']=store.rollback(1,proposal['id'],'Synthetic demonstration')['state']
        started=perf_counter()
        service=TenderProofService(TenderProofStore())
        run=service.start_discovery(build_imeso_mock_driver(),source=IMESO_SOURCE,listing_url=IMESO_LISTING,is_synthetic=True,owner_user_id=1)
        run=service.select_and_process(run.run_id,'imeso-42',build_imeso_mock_driver())
        report['imeso']={'run':run.model_dump(mode='json'),'elapsed_s':perf_counter()-started}
        if run.execution_status!='completed': raise RuntimeError(run.error)
        broken={'02_changed_layout','04_false_empty','09_recovered_navigation'}
        report['metrics']={'correct_recoveries':{'numerator':sum(c['passed'] and c['actual']=='recovered' for c in good_report['cases'] if c['name'] in broken),
                                               'denominator':len(broken)},
            'correct_scenario_diagnoses':{'numerator':sum(c['passed'] for c in good_report['cases']),'denominator':len(good_report['cases'])},
            'incorrect_strategies_accepted':{'numerator':int(bad_report['passed']),'denominator':1},
            'imeso_fields_present':{'numerator':sum(f.state=='supported' for f in run.fields),'denominator':6},
            'provider_resources_created':0,'provider_confirmed_cost':None}
    output=Path(__file__).resolve().parents[1]/'.tenderproof'/'demo-phases4-7.json'
    output.parent.mkdir(exist_ok=True)
    output.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'report':str(output),'metrics':report['metrics']},ensure_ascii=True))


if __name__=='__main__': main()
