"""Bounded live proof; Zambini archive selected explicitly, default empty preserved."""
import argparse
import os
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.tenderproof.source_adapters import get_source_adapter
from app.tenderproof.batch60_catalogue_adapters import BATCH60_CATALOGUE_ADAPTERS
import tenderproof_pilot_live as probe

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sources',nargs='*')
    parser.add_argument('--archive-zambini',action='store_true')
    parser.add_argument('--root',default='.tenderproof/b60cat')
    parser.add_argument('--report',default='../docs/tenderproof-batch60-catalogue-live.json')
    args=parser.parse_args()
    adapters=tuple(get_source_adapter(a.source) for a in BATCH60_CATALOGUE_ADAPTERS if not args.sources or a.source in args.sources)
    for a in adapters:
        if a.source=='zambini_open' and args.archive_zambini:
            a.listing_urls=('https://www.zambini.org.br/portal/concursos/encerrados',)
    probe.PILOT_ADAPTERS=adapters
    probe.ROOT=Path(args.root).resolve()
    probe.CAPTURE=Path('tests/fixtures/tenderproof_batch60_own')
    probe.REPORT=Path(args.report)
    os.environ['TENDERPROOF_ARTIFACT_DIR']=str(probe.ROOT/'artifacts')
    probe.main()
