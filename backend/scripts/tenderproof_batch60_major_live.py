"""Two bounded HTTP cycles through the existing service; registry local to process."""
import os
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.tenderproof.batch60_major_adapters import BATCH60_MAJOR_ADAPTERS
from app.tenderproof.source_adapters import SOURCE_ADAPTERS
from tenderproof_batch30_institutional_live import SanitizedDriver
from tenderproof_batch60_major_capture import sanitize_json
import tenderproof_pilot_live as probe

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sources',nargs='*')
    parser.add_argument('--root',default='.tenderproof/batch60-major-live-20260908')
    parser.add_argument('--report',default='../docs/tenderproof-batch60-major-live.json')
    args=parser.parse_args()
    adapters=tuple(a for a in BATCH60_MAJOR_ADAPTERS if not args.sources or a.source in args.sources)
    SOURCE_ADAPTERS.update({a.source:a for a in adapters})
    probe.PILOT_ADAPTERS=adapters
    redact_existing=probe.redact
    probe.redact=lambda value:sanitize_json(redact_existing(value))
    probe.CapturingDriver=SanitizedDriver
    probe.ROOT=Path(args.root).resolve();probe.CAPTURE=Path('tests/fixtures/tenderproof_batch60_major');probe.REPORT=Path(args.report)
    os.environ['TENDERPROOF_ARTIFACT_DIR']=str(probe.ROOT/'artifacts')
    probe.main()
