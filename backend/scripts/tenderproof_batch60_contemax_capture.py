"""Verify exact official Contemax paths over HTTPS, without redirects or TLS bypass."""
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import tenderproof_batch60_major_capture as capture
BASE='https://www.contemaxconsultoria.com.br'
TARGETS={'listing':BASE+'/site/concursos','cubati':BASE+'/site/concursos-em-andamento/prefeitura-municipal-de-cubati-pb','original':BASE+'/site/wp-content/uploads/2024/09/Edital-CUBATI.pdf'}
if __name__=='__main__':
 capture.FIXTURES=Path(__file__).resolve().parents[1]/'tests/fixtures/tenderproof_batch60_contemax'
 capture.FIXTURES.mkdir(parents=True,exist_ok=True)
 # Probe listing and detail first. Download the PDF only through the shared driver once a contract is verified.
 rows=list(ThreadPoolExecutor(2).map(capture.fetch,[(k,v) for k,v in TARGETS.items() if k!='original']))
 (capture.FIXTURES/'manifest-https.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps(rows,ensure_ascii=False))
