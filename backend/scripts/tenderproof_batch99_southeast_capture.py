"""Bounded public captures for batch99 southeast/northeast personnel scope."""
from pathlib import Path
import json,argparse
from concurrent.futures import ThreadPoolExecutor
import tenderproof_batch60_major_capture as capture
KEYS='fapemig_selection fapes_selection fapesq_selection fapepi_selection fapema_selection fapece_selection fapern_selection fapeal_selection facepe_selection fapesb_selection faperj_selection fapesp_selection'.split()
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--targets');p.add_argument('--phase',default='initial');a=p.parse_args()
 capture.FIXTURES=Path(__file__).resolve().parents[1]/'tests/fixtures/tenderproof_batch99_southeast';capture.FIXTURES.mkdir(parents=True,exist_ok=True)
 inventory=json.loads((Path(__file__).resolve().parents[2]/'docs/tenderproof-sources-99.json').read_text(encoding='utf-8'))['sources']
 targets=json.loads(Path(a.targets).read_text(encoding='utf-8')) if a.targets else {s['source_type']:s['listing_urls'][0] for s in inventory if s['source_type'] in KEYS}
 rows=list(ThreadPoolExecutor(6).map(capture.fetch,targets.items()))
 (capture.FIXTURES/('manifest-'+a.phase+'.json')).write_text(json.dumps(rows,indent=2,ensure_ascii=False),encoding='utf-8');print(json.dumps(rows,ensure_ascii=False))
