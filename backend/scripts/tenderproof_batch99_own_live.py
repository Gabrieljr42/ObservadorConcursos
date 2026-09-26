"""Two bounded real cycles for the final-batch own organizer contracts."""
import os
import argparse
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.tenderproof.batch99_own_adapters import BATCH99_OWN_ADAPTERS
from app.tenderproof.batch99_ieses_adapter import BATCH99_IESES_ADAPTERS
from app.tenderproof.batch99_verbena_adapter import BATCH99_VERBENA_ADAPTERS
from tenderproof_batch30_institutional_live import SanitizedDriver
import tenderproof_pilot_live as probe

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sources',nargs='+')
    parser.add_argument('--root',default='.tenderproof/r99own')
    parser.add_argument('--report',default='../docs/tenderproof-batch99-own-live.json')
    args=parser.parse_args()
    probe.PILOT_ADAPTERS=tuple(a for a in (*BATCH99_OWN_ADAPTERS,*BATCH99_IESES_ADAPTERS,*BATCH99_VERBENA_ADAPTERS) if not args.sources or a.source in args.sources)
    probe.CapturingDriver=SanitizedDriver
    probe.ROOT=Path(args.root).resolve()
    probe.CAPTURE=Path('tests/fixtures/tenderproof_batch99_own')
    probe.REPORT=Path(args.report)
    os.environ['TENDERPROOF_ARTIFACT_DIR']=str(probe.ROOT/'artifacts')
    os.environ['TENDERPROOF_PROCESSING_DIR']=str(probe.ROOT/'processing')
    probe.main()
