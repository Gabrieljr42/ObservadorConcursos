"""Bounded captures of observed final-batch organizer routes."""
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timezone
from pathlib import Path
import tenderproof_batch60_own_capture as capture

def main():
    capture.FIX=capture.ROOT/'tests/fixtures/tenderproof_batch99_own'
    capture.FIX.mkdir(parents=True,exist_ok=True)
    plan=json.loads((capture.ROOT.parent/'docs/tenderproof-rollout-plan.json').read_text(encoding='utf-8'))
    group=next(b for b in plan['batches'] if b['cumulative_sources']==99)['strategy_groups']['organizers_and_verbena']
    inv=json.loads((capture.ROOT.parent/'docs/tenderproof-sources-99.json').read_text(encoding='utf-8'))
    targets=[(s['source_type'],o.get('final_url',o['requested_url']),f'listing{i}') for s in inv['sources'] if s['source_type'] in group for i,o in enumerate(s['url_observations'])]
    phase='initial'
    if len(sys.argv)>1:
        path=Path(sys.argv[1]);phase=path.stem
        targets=[tuple(r) for r in json.loads(path.read_text(encoding='utf-8'))]
    with ThreadPoolExecutor(4) as pool:rows=list(pool.map(capture.fetch,targets))
    report={'observed_at':datetime.now(timezone.utc).isoformat(),'scope':'Observed public routes; TLS verified; redirects recorded only; 2MiB25s per request; no browser or PDF acquisition; not certification.','pages':rows}
    (capture.FIX/f'{phase}-manifest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    for row in rows:print(json.dumps({k:row.get(k) for k in ('source','status','bytes','title','location','error_type')},ensure_ascii=True),flush=True)

if __name__=='__main__':main()
