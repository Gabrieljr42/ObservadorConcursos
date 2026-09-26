"""Two offline cycles of exact official FAPESC payload including leadingLF."""
import hashlib
import json
import os
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.tenderproof.batch99_regions_adapters import FapescSelectionAdapter
from app.tenderproof.solari_adapter import DownloadedBytes
from tenderproof_batch60_recovered_live import RecoveredCaptureDriver
import tenderproof_pilot_live as probe

FIX=Path('tests/fixtures/tenderproof_batch99_regions')
PAYLOADS={}
for manifest in ('alternate-manifest.json','contest-manifest.json'):
    for row in json.loads((FIX/manifest).read_text(encoding='utf-8'))['pages']:
        if row['source']=='fapesc_selection':
            raw=(FIX/row['file']).read_bytes()
            assert hashlib.sha256(raw).hexdigest()==row['sha256']
            PAYLOADS[row['url']]=raw
row=json.loads((FIX/'fapesc-pdf-manifest.json').read_text(encoding='utf-8'))['documents'][0]
raw=(FIX/row['file']).read_bytes()
assert hashlib.sha256(raw).hexdigest()==row['sha256']
PAYLOADS[row['url']]=raw

class PreservedCaptureDriver(RecoveredCaptureDriver):
    instances=[]
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs);self.instances.append(self)
    def _fetch(self,url,validator,max_bytes):
        validator(url)
        content=PAYLOADS[url]
        if len(content)>max_bytes:raise ValueError('preserved payload exceeds limit')
        return DownloadedBytes(url_requested=url,url_final=url,content=content,content_type='application/pdf' if url==row['url'] else 'text/html')

if __name__=='__main__':
    probe.ROOT=Path('.tenderproof/r99regions-pdf-replay').resolve()
    if probe.ROOT.exists():raise ValueError('preserve existing replay')
    probe.CAPTURE=FIX
    probe.REPORT=Path('../docs/tenderproof-batch99-regions-pdf-replay.json')
    probe.PILOT_ADAPTERS=(FapescSelectionAdapter(),)
    probe.CapturingDriver=PreservedCaptureDriver
    os.environ['TENDERPROOF_ARTIFACT_DIR']=str(probe.ROOT/'artifacts')
    os.environ['TENDERPROOF_PROCESSING_DIR']=str(probe.ROOT/'processing')
    probe.main()
    report=json.loads(probe.REPORT.read_text(encoding='utf-8'))
    report.update(scope='Two OFFLINE cycles, exact preserved official bytes, no new HTTP, no byte repair',network_requests=0,magic_header_policy='At most16 ASCII space/tab/CR/LF bytes; downstream PDF parser required',driver_cleanup={'instances':len(PreservedCaptureDriver.instances),'all_clients_closed':all(d.client.is_closed for d in PreservedCaptureDriver.instances)})
    report['passed']=all(a['validation_status']=='valid' and a['durable_hash_verified'] and a['artifact']['sha256']==row['sha256'] for c in report['cycles'] for a in c['attempts']) and len(report['cycles'])==2
    probe.REPORT.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    assert report['passed'] and report['driver_cleanup']['all_clients_closed']
