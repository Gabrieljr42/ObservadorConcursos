"""Reuse the bounded pilot harness for two batch30 sources; no production writes."""
import os
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.tenderproof.source_adapters import SOURCE_ADAPTERS
from app.tenderproof.batch30_edital_adapters import BATCH30_EDITAL_ADAPTERS
import tenderproof_pilot_live as probe

if __name__=='__main__':
    probe.PILOT_ADAPTERS=BATCH30_EDITAL_ADAPTERS
    SOURCE_ADAPTERS.update({a.source:a for a in BATCH30_EDITAL_ADAPTERS})
    probe.ROOT=Path('.tenderproof/batch30-edital-live-20260908').resolve()
    probe.CAPTURE=Path('tests/fixtures/tenderproof_batch30_edital')
    probe.REPORT=Path('../docs/tenderproof-batch30-edital-live.json')
    os.environ['TENDERPROOF_ARTIFACT_DIR']=str(probe.ROOT/'artifacts')
    probe.main()
