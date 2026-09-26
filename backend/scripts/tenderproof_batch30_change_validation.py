"""Explicit controlled HTML mutations over an isolated copy of valid batch30 data.

No new URL is requested: the added principal exists only inside this offline
fixture. Source disappearance and document change were not observed live.
"""
import hashlib
import argparse
import json
import os
import shutil
import sys
from pathlib import Path
from datetime import datetime, timezone
from urllib.parse import urljoin, urlsplit, urlunsplit
from bs4 import BeautifulSoup
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.tenderproof.continuous import ContinuousEngine
from app.tenderproof.continuous_store import ContinuousStore
from app.tenderproof.source_adapters import get_source_adapter
from app.tenderproof.store import TenderProofStore
from tenderproof_pilot_continuous_replay import PreservedDriver, capture


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--kind', choices=('principal','complementary'), default='principal')
    parser.add_argument('--root', default='.tenderproof/batch30-change-validation-20260908')
    parser.add_argument('--output', default='../docs/tenderproof-batch30-change-validation.json')
    args=parser.parse_args()
    original=Path('.tenderproof/batch30-continuous-replay-verified-20260908').resolve()
    root=Path(args.root).resolve()
    assert original.parent==root.parent and original!=root and not root.exists()
    assert not any(path.is_symlink() for path in original.rglob('*'))
    original_hash=hashlib.sha256((original/'continuous.sqlite3').read_bytes()).hexdigest()
    # Verified replay has finished; this copies only that disposable evidence
    # volume. All subsequent queue/operational mutations target the copy.
    shutil.copytree(original,root)
    os.environ.update(TENDERPROOF_ARTIFACT_DIR=str(root/'artifacts'),
        TENDERPROOF_CONTINUOUS_ENABLED='true',TENDERPROOF_CONTINUOUS_OPERATOR_USER_IDS='901',
        TENDERPROOF_BROWSER_LIVE_ENABLED='false',TENDERPROOF_PUBLICATION_ENABLED='false')
    source='exame_open';adapter=get_source_adapter(source)
    queue=ContinuousStore(root/'continuous.sqlite3')
    observation=queue.observations(901,source=source)[0]
    run=TenderProofStore().get_run(observation['run_id'])
    candidate=next(c for c in run.candidates if c.candidate_id==run.selected_candidate_id)
    report=json.loads(Path('../docs/tenderproof-batch30-shared-live.json').read_text(encoding='utf-8'))
    cycle=next(c for c in report['cycles'] if c['source']==source)
    attempt=next(a for a in cycle['attempts'] if a['candidate']['external_id']==candidate.external_id)
    roots=[Path('tests/fixtures/tenderproof_batch30_shared')]
    listing=capture(cycle['captures'][0],roots);detail=capture(attempt['captures'][0],roots)
    fixture=dict(run=run,candidate=candidate,pdf=TenderProofStore().load_artifact_bytes(run.artifact),
        listing_url=cycle['captures'][0]['url'],listing_html=listing,detail_html=detail,
        replay_document_url=run.document.url_requested)
    adapter.validate_listing_url(fixture['listing_url']);adapter.listing_urls=(fixture['listing_url'],)
    soup=BeautifulSoup(listing,'lxml');removed=0
    for anchor in list(soup.select('a[href]')):
        if urljoin(fixture['listing_url'],anchor['href'])==candidate.detail_url_observed:
            anchor.decompose();removed+=1
    assert removed
    fixture['listing_html']=str(soup)
    assert candidate.external_id not in {c.external_id for c in adapter.parse_listing(fixture['listing_html'],fixture['listing_url']).candidates}
    drivers=[]
    class CountingDriver(PreservedDriver):
        download_calls=0
        def download(self,url,*,max_bytes):
            self.download_calls+=1
            return super().download(url,max_bytes=max_bytes)
    def factory(source,settings,**kwargs):
        driver=CountingDriver(fixture);drivers.append(driver);return driver
    engine=ContinuousEngine(queue=queue,driver_factory=factory)
    output=dict(validated_at=datetime.now(timezone.utc).isoformat(),source=source,candidate=candidate.external_id,
        simulation=True,scope='Controlled EXAME HTML mutations only; not a real source change.',
        root=str(root),mutation_kind=args.kind,network_requests=0,canonical_writes=0,browser_sessions=0,steps=[])
    def state():
        with queue._db() as db:
            return dict(db.execute('SELECT * FROM known_candidates WHERE owner=? AND source=? AND candidate_key=?',
                (901,source,candidate.external_id)).fetchone())
    def execute(name):
        with queue._db(write=True) as db:
            db.execute('UPDATE known_candidates SET next_check=0,last_checked=-1 WHERE owner=? AND source=? AND candidate_key=?',
                (901,source,candidate.external_id))
        cycle_id=engine.enqueue(901,source,force=True)
        for _ in range(6):
            jobs=engine.ready_jobs()
            if not jobs:break
            engine.process_job(jobs[0])
        observations=queue.observations(901,source=source)
        output['steps'].append(dict(name=name,cycle_status=queue.cycle(cycle_id,901)['status'],
            observations=len(observations),valid=sum(o['summary'].get('validation_status')=='valid' for o in observations),
            review_required=sum(o['summary'].get('validation_status')=='document_review_required' for o in observations),
            documentary_holds=sum(bool(o['summary'].get('document_review',{}).get('pending')) for o in observations)))
        return observations
    observations=execute('candidate removed from observed listing')
    assert len(observations)==1 and observations[0]['summary']['validation_status']=='valid'
    valid_run=state()['last_valid_run_id']
    assert hashlib.sha256(TenderProofStore().load_artifact_bytes(TenderProofStore().get_run(valid_run).artifact)).hexdigest()==run.artifact.sha256
    downloads_before_change=sum(d.download_calls for d in drivers)
    assert downloads_before_change==1
    soup=BeautifulSoup(detail,'lxml');parts=urlsplit(run.document.url_requested)
    changed_url=urlunsplit((parts.scheme,parts.netloc,parts.path.rsplit('/',1)[0]+'/controlled-change.pdf','',''))
    anchor=soup.new_tag('a',href=changed_url)
    anchor.string='Edital de abertura - SIMULAÇÃO de segunda versão' if args.kind=='principal' else 'Retificação de prazo - SIMULAÇÃO'
    (soup.body or soup).append(anchor);fixture['detail_html']=str(soup)
    docs=adapter.documents(fixture['detail_html'],candidate)
    assert len([d for d in docs if d.kind=='edital'])==(2 if args.kind=='principal' else 1)
    for name in ('new document requires review','repeat unchanged new manifest'):
        observations=execute(name)
        assert len(observations)==2
        if args.kind=='principal':
            assert sum(o['summary'].get('validation_status')=='valid' for o in observations)==1
            review=next(o for o in observations if o['summary'].get('validation_status')=='document_review_required')
            assert not review['summary']['document_bytes_verified']
            assert state()['last_valid_run_id']==valid_run
            assert sum(d.download_calls for d in drivers)==downloads_before_change
        else:
            assert all(o['summary']['validation_status']=='valid' for o in observations)
            assert all(o['summary']['document_review']['pending'] for o in observations)
            from app.tenderproof.publication import _assert_document_review_clear
            from fastapi import HTTPException
            try:
                _assert_document_review_clear(run)
            except HTTPException as error:
                assert error.status_code==409
            else:
                raise AssertionError('old run bypassed current documentary hold')
            assert hashlib.sha256(TenderProofStore().load_artifact_bytes(TenderProofStore().get_run(state()['last_valid_run_id']).artifact)).hexdigest()==run.artifact.sha256
    assert all(d.closed for d in drivers)
    assert hashlib.sha256((original/'continuous.sqlite3').read_bytes()).hexdigest()==original_hash
    output.update(passed=True,original_volume_unchanged=True,downloads=sum(d.download_calls for d in drivers),
        last_valid_sha256=run.artifact.sha256,drivers_closed=len(drivers))
    Path(args.output).write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(output['steps']))


if __name__=='__main__':main()
