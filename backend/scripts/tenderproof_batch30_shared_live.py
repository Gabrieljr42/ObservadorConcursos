"""Execute bounded batch30 shared-source proof using the existing pilot harness."""
import tenderproof_pilot_live as harness
from app.tenderproof.batch30_shared_adapters import BATCH30_SHARED_ADAPTERS
from pathlib import Path
import os
harness.PILOT_ADAPTERS=BATCH30_SHARED_ADAPTERS
harness.CAPTURE=Path('tests/fixtures/tenderproof_batch30_shared')
harness.REPORT=Path('../docs/tenderproof-batch30-shared-live.json')
harness.ROOT=Path('.tenderproof/batch30-shared-live-20260908').resolve()
os.environ['TENDERPROOF_ARTIFACT_DIR']=str(harness.ROOT/'artifacts')
if __name__=='__main__':harness.main()
