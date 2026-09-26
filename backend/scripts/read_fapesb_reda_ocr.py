"""Raster OCR for acquired REDA scanned summons and damaged native-font gazette text."""
from pathlib import Path
import hashlib,json,subprocess,sys

def main():
    root=Path('/evidence');source=root/'current-documents-20260909T165904Z'
    quality=sys.argv[1:]==['--quality-audit']
    if sys.argv[1:] and not quality:raise ValueError('Unknown arguments')
    out=root/('reda-quality-ocr' if quality else 'reda-ocr');out.mkdir(exist_ok=True);report=[]
    hashes=[d['sha256'] for d in json.loads((root/'reda-text-quality-audit.json').read_text())['pending']] if quality else ['86cfb1521b49fe06b98f108364a8b896394c02cef78b018c7844405be78815f8','e54f08e5dea91d1925e69b4721d51c35b358da0f5f7a3d66325892f318426279']
    for sha in hashes:
        if len(sha)!=64 or any(c not in '0123456789abcdef' for c in sha):raise ValueError('Invalid digest')
        file=source/(sha+'.pdf');target=out/(sha+'.json')
        if hashlib.sha256(file.read_bytes()).hexdigest()!=sha:raise ValueError('Input hash mismatch')
        row={'sha256':sha};report.append(row)
        try:
            subprocess.run([sys.executable,'-m','scripts.faperr_raster_ocr_worker',str(file),str(target),'20','8388608','170'],check=True,timeout=180)
            r=json.loads(target.read_text());row.update(state='succeeded',pages=len(r['pages']),empty_pages=sum(not p['text'].strip() for p in r['pages']))
        except Exception as e:row.update(state='failed',error_type=type(e).__name__)
        (out/'verification.json').write_text(json.dumps(report,indent=2));print(json.dumps(row),flush=True)

if __name__=='__main__':main()
