"""Two real bounded regional selection samples in a fresh isolated volume."""
import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.tenderproof.batch99_fepese_adapter import BATCH99_FEPESE_ADAPTERS
from tenderproof_batch60_recovered_live import RecoveredCaptureDriver
import tenderproof_pilot_live as probe


class AuditedCaptureDriver(RecoveredCaptureDriver):
    instances = []

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.instances.append(self)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sources', nargs='*')
    parser.add_argument('--root', default='.tenderproof/r99fepese')
    parser.add_argument('--report', default='../docs/tenderproof-batch99-fepese-live.json')
    args = parser.parse_args()
    probe.PILOT_ADAPTERS = tuple(a for name,a in BATCH99_FEPESE_ADAPTERS.items() if not args.sources or name in args.sources)
    probe.CapturingDriver = AuditedCaptureDriver
    probe.ROOT = Path(args.root).resolve()
    if probe.ROOT.exists():
        parser.error('isolated root exists; preserve prior evidence')
    probe.CAPTURE = Path('tests/fixtures/tenderproof_batch99_fepese')
    probe.REPORT = Path(args.report)
    os.environ['TENDERPROOF_ARTIFACT_DIR'] = str(probe.ROOT/'artifacts')
    os.environ['TENDERPROOF_PROCESSING_DIR'] = str(probe.ROOT/'processing')
    probe.main()
    report = json.loads(probe.REPORT.read_text(encoding='utf8'))
    report['driver_cleanup'] = {'instances': len(AuditedCaptureDriver.instances), 'all_clients_closed': all(driver.client.is_closed for driver in AuditedCaptureDriver.instances)}
    probe.REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf8')
    assert report['driver_cleanup']['all_clients_closed']
