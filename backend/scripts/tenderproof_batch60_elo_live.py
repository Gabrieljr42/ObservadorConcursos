"""Two bounded ELO cycles through the centrally registered adapter."""
import os
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.tenderproof.batch60_elo_adapter import BATCH60_ELO_ADAPTERS
from tenderproof_batch30_institutional_live import SanitizedDriver
import tenderproof_pilot_live as probe

if __name__=='__main__':
    probe.PILOT_ADAPTERS=BATCH60_ELO_ADAPTERS
    probe.CapturingDriver=SanitizedDriver
    probe.ROOT=Path('.tenderproof/r60elo').resolve()
    probe.CAPTURE=Path('tests/fixtures/tenderproof_batch60_own')
    probe.REPORT=Path('../docs/tenderproof-batch60-elo-live.json')
    os.environ['TENDERPROOF_ARTIFACT_DIR']=str(probe.ROOT/'artifacts')
    os.environ['TENDERPROOF_PROCESSING_DIR']=str(probe.ROOT/'processing')
    probe.main()
