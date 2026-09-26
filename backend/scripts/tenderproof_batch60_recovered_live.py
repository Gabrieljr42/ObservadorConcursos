"""Two bounded real cycles; no publication, browser or production activation."""
import argparse
import os
import sys
from pathlib import Path

from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.tenderproof.batch60_recovered_adapters import BATCH60_RECOVERED_ADAPTERS
import tenderproof_pilot_live as probe


class RecoveredCaptureDriver(probe.CapturingDriver):
    def _save(self, kind, url, html):
        # Keep malformed SHDIAS trailing publication HTML for faithful replay.
        soup = BeautifulSoup(html, 'html.parser')
        for node in soup.select('input[type=hidden]'):
            node.attrs.pop('value', None)
        super()._save(kind, url, str(soup))
        self.captures[-1]['format'] = 'decoded public HTML; hidden input values removed with html.parser; fixture hash only'


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sources', nargs='*')
    parser.add_argument('--root', default='.tenderproof/r60rec')
    parser.add_argument('--report', default='../docs/tenderproof-batch60-recovered-live.json')
    args = parser.parse_args()
    probe.PILOT_ADAPTERS = tuple(a for name, a in BATCH60_RECOVERED_ADAPTERS.items() if not args.sources or name in args.sources)
    if not probe.PILOT_ADAPTERS:
        parser.error('no supported source selected')
    probe.CapturingDriver = RecoveredCaptureDriver
    probe.ROOT = Path(args.root).resolve()
    if probe.ROOT.exists():
        parser.error('isolated root already exists; preserve earlier evidence and choose a fresh root')
    probe.CAPTURE = Path('tests/fixtures/tenderproof_batch60_blockers')
    probe.REPORT = Path(args.report)
    os.environ['TENDERPROOF_ARTIFACT_DIR'] = str(probe.ROOT / 'artifacts')
    os.environ['TENDERPROOF_PROCESSING_DIR'] = str(probe.ROOT / 'processing')
    probe.main()
