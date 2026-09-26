"""OCR only original pages with invalid native Unicode; preserve the derivative mapping."""
import hashlib,json,subprocess,sys
from pathlib import Path
from pypdf import PdfReader,PdfWriter

def main():
    root=Path('/evidence');native=json.loads((root/'profix-native-recovery.json').read_text())
    original=root/'current-documents-20260909T160517Z'/(native['input_sha256']+'.pdf')
    if hashlib.sha256(original.read_bytes()).hexdigest()!=native['input_sha256']:raise ValueError('original hash mismatch')
    reader=PdfReader(original,strict=True);writer=PdfWriter();mapping=[]
    for p in native['pages']:
        if p['invalid_unicode_positions']:writer.add_page(reader.pages[p['page_number']-1]);mapping.append(p['page_number'])
    subset=root/'profix-unicode-affected.pdf';writer.write(subset)
    receipt={'original_sha256':native['input_sha256'],'derivative_sha256':hashlib.sha256(subset.read_bytes()).hexdigest(),'derivative_page_to_original_page':mapping,'review_required':True}
    (root/'profix-unicode-affected-receipt.json').write_text(json.dumps(receipt,indent=2))
    output=root/'profix-unicode-affected-ocr.json'
    subprocess.run([sys.executable,'-m','scripts.faperr_raster_ocr_worker',str(subset),str(output),'2','8388608','110'],check=True,timeout=120)
    result=json.loads(output.read_text())
    if result['input_sha256']!=receipt['derivative_sha256'] or len(result['pages'])!=len(mapping):raise ValueError('OCR mapping mismatch')
    for p,number in zip(result['pages'],mapping):
        if not p['text'].strip():raise ValueError('empty OCR')
        native['pages'][number-1].update(text=p['text'],text_origin='ocr_of_mapped_original_page',original_invalid_unicode_positions=native['pages'][number-1]['invalid_unicode_positions'],invalid_unicode_positions=[])
    native.update(recovery_mapping=receipt,review_required=True)
    (root/'profix-reconciled-pages.json').write_text(json.dumps(native,ensure_ascii=True))
    print(json.dumps({'pages':len(native['pages']),'ocr_original_pages':mapping,'empty_pages':sum(not p['text'].strip() for p in native['pages'])}))

if __name__=='__main__':main()
