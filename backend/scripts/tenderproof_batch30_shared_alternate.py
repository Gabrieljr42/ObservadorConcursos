"""Observed status tabs, bounded alternate sampling after explicit first-page blockers."""
import tenderproof_pilot_live as harness
from app.tenderproof.source_adapters import get_source_adapter
from pathlib import Path
import os
harness.PILOT_ADAPTERS=tuple(get_source_adapter(s) for s in ('cotec_open','rbo_open','quadrix_open'))
for a in harness.PILOT_ADAPTERS:
 url='https://'+a.portal_host+'/index/1/';a.validate_listing_url(url);a.listing_urls=(url,)
harness.CAPTURE=Path('tests/fixtures/tenderproof_batch30_shared')
harness.REPORT=Path('../docs/tenderproof-batch30-shared-alternate-live.json')
harness.ROOT=Path('.tenderproof/batch30-shared-live-20260908').resolve()
os.environ['TENDERPROOF_ARTIFACT_DIR']=str(harness.ROOT/'artifacts')
if __name__=='__main__':harness.main()
