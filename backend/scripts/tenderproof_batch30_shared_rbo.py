"""Observed finalized tab, explicit historical scope after current RBO blockers."""
import tenderproof_pilot_live as harness
from app.tenderproof.source_adapters import get_source_adapter
from pathlib import Path
import os
adapter=get_source_adapter('rbo_open');url='https://rboconcursos.selecao.net.br/index/3/';adapter.validate_listing_url(url);adapter.listing_urls=(url,)
harness.PILOT_ADAPTERS=(adapter,);harness.CAPTURE=Path('tests/fixtures/tenderproof_batch30_shared');harness.REPORT=Path('../docs/tenderproof-batch30-shared-rbo-historical-live.json');harness.ROOT=Path('.tenderproof/batch30-shared-live-20260908').resolve();os.environ['TENDERPROOF_ARTIFACT_DIR']=str(harness.ROOT/'artifacts')
if __name__=='__main__':harness.main()
