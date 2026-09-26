"""Bounded own-portal acquisition; official observed IBFC ongoing tab."""
import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.tenderproof.batch30_own_adapters import BATCH30_OWN_ADAPTERS
from tenderproof_batch30_institutional_live import SanitizedDriver
import tenderproof_pilot_live as probe

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sources', nargs='*')
    parser.add_argument('--report', default='../docs/tenderproof-batch30-own-live.json')
    parser.add_argument('--root', default='.tenderproof/batch30-own-live-20260908')
    args = parser.parse_args()
    probe.PILOT_ADAPTERS = tuple(a for a in BATCH30_OWN_ADAPTERS if not args.sources or a.source in args.sources)
    if not probe.PILOT_ADAPTERS:
        parser.error('no supported source selected')
    for adapter in probe.PILOT_ADAPTERS:
        if adapter.source == 'ibfc_open':
            # Current open tab has the observed legitimate empty marker. This
            # ongoing tab is linked by the same official site and allowed.
            adapter.listing_urls = ('https://concursos.ibfc.org.br/index/1/',)
    probe.CapturingDriver = SanitizedDriver
    probe.ROOT = Path(args.root).resolve()
    probe.CAPTURE = Path('tests/fixtures/tenderproof_batch30_own')
    probe.REPORT = Path(args.report)
    os.environ['TENDERPROOF_ARTIFACT_DIR'] = str(probe.ROOT/'artifacts')
    probe.main()
