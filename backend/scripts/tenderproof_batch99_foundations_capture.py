"""Bounded TLS captures of observed foundation routes; no coverage claim."""
import json
import sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import tenderproof_batch60_own_capture as capture

ROOT = Path(__file__).resolve().parents[1]
FIX = ROOT / 'tests/fixtures/tenderproof_batch99_foundations'
SOURCES = {'funpec_selection', 'fade_selection', 'fapex_selection', 'fatec_selection',
           'faped_selection', 'fapese_selection', 'fappr_selection', 'fapergs_selection'}

def main():
    FIX.mkdir(parents=True, exist_ok=True)
    capture.FIX = FIX
    if len(sys.argv) > 1:
        plan = Path(sys.argv[1])
        targets = json.loads(plan.read_text(encoding='utf8'))
        label = plan.stem
    else:
        inventory = json.loads((ROOT.parent/'docs/tenderproof-phases11-13-probe.json').read_text(encoding='utf8'))
        targets = [(s['source_type'], o.get('final_url', o['requested_url']), f'listing{i}')
                   for s in inventory['sources'] if s['source_type'] in SOURCES
                   for i, o in enumerate(s['url_observations'])]
        label = 'initial'
    with ThreadPoolExecutor(4) as pool:
        rows = list(pool.map(capture.fetch, targets))
    (FIX/(label+'-manifest.json')).write_text(json.dumps({'limits': '2MiB/25s, TLS verified, redirects recorded only, no PDF/browser', 'pages': rows}, ensure_ascii=False, indent=2)+'\n', encoding='utf8')
    for row in rows:
        print(json.dumps({k: row.get(k) for k in ('source', 'kind', 'status', 'bytes', 'location', 'error_type')}, ensure_ascii=True), flush=True)

if __name__ == '__main__':
    main()
