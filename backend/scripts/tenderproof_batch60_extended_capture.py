"""Bounded public captures of observed CPCON/Gualimp routes."""
import argparse
import json
from pathlib import Path
import tenderproof_batch60_blockers as capture_tool

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--targets', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    capture_tool.FIXTURES = Path('tests/fixtures/tenderproof_batch60_extended')
    capture_tool.FIXTURES.mkdir(parents=True, exist_ok=True)
    rows = [capture_tool.capture(row) for row in json.loads(args.targets.read_text(encoding='utf8'))]
    args.output.write_text(json.dumps({'scope': 'Observed public links and literal public AJAX calls; verified TLS, 25s/2MiB limit, no login/publication', 'pages': rows}, ensure_ascii=False, indent=2), encoding='utf8')
    print(json.dumps([{k:r.get(k) for k in ('source','url','status','bytes','error')} for r in rows],indent=2))
