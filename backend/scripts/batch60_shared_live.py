"""Two bounded public HTTP cycles for the three proved contracts; no publication."""
import os
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.tenderproof.batch60_shared_adapters import BATCH60_SHARED_ADAPTERS
import tenderproof_pilot_live as probe

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument('--sources',nargs='*')
    parser.add_argument('--root',default='.tenderproof/b60share')
    parser.add_argument('--report',default='../docs/tenderproof-batch60-shared-live.json')
    args=parser.parse_args()
    probe.PILOT_ADAPTERS=tuple(a for a in BATCH60_SHARED_ADAPTERS if not args.sources or a.source in args.sources)
    probe.ROOT=Path(args.root).resolve()
    probe.CAPTURE=Path('tests/fixtures/tenderproof_batch60_shared')
    probe.REPORT=Path(args.report)
    os.environ['TENDERPROOF_ARTIFACT_DIR']=str(probe.ROOT/'artifacts')
    probe.main()
