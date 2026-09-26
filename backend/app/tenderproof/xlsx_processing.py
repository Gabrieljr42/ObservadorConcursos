"""Fixed, credential-free subprocess for bounded workbook cell reading."""
import hashlib,json,os,subprocess,sys
from pathlib import Path
from app.tenderproof.xlsx_text import MAX_INPUT,MAX_OUTPUT


def extract_xlsx_isolated(content):
    if not content or len(content)>MAX_INPUT:raise ValueError('XLSX input bounds')
    env={k:os.environ[k] for k in ('SYSTEMROOT','WINDIR','TEMP','TMP') if k in os.environ}
    result=subprocess.run([sys.executable,'-I','-S',str(Path(__file__).with_name('xlsx_text.py'))],input=content,
        stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=30,env=env,check=False)
    if len(result.stdout)>MAX_OUTPUT:raise ValueError('XLSX output bounds')
    data=json.loads(result.stdout)
    if result.returncode or data.get('error'):raise ValueError('XLSX reading failed: '+str(data.get('error','worker failure')))
    if data.get('input_sha256')!=hashlib.sha256(content).hexdigest():raise ValueError('XLSX reader input identity mismatch')
    return data
