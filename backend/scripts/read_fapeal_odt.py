"""Offline bounded text extraction of already acquired FAPEAL ODT annexes."""
import hashlib,io,json,zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

def main():
    source=Path('/evidence/contract-documents-20260909T144432Z');out=Path('/evidence/odt-text-current');out.mkdir(exist_ok=True)
    report=[]
    for row in json.loads((source/'report.json').read_text())['documents']:
        if row['format']!='odt':continue
        record={'url':row['url'],'sha256':row['sha256']};report.append(record)
        try:
            raw=(source/(row['sha256']+'.odt')).read_bytes()
            if len(raw)>15_000_000 or hashlib.sha256(raw).hexdigest()!=row['sha256']:raise ValueError('ODT hash/byte limit')
            with zipfile.ZipFile(io.BytesIO(raw))as z:
                entries=z.infolist();names=z.namelist()
                if len(entries)>1000 or len(names)!=len(set(names)) or sum(e.file_size for e in entries)>50_000_000:raise ValueError('ODT package limit')
                if z.read('mimetype')!=b'application/vnd.oasis.opendocument.text':raise ValueError('ODT mimetype mismatch')
                if z.getinfo('content.xml').file_size>8_000_000:raise ValueError('ODT XML limit')
                xml=z.read('content.xml').decode('utf-8-sig')
                if '<!DOCTYPE' in xml.upper() or '<!ENTITY' in xml.upper():raise ValueError('ODT XML declarations rejected')
                tree=ET.fromstring(xml);ns='{urn:oasis:names:tc:opendocument:xmlns:text:1.0}'
                paragraphs=[{'paragraph':i,'text':''.join(n.itertext())}for i,n in enumerate(tree.iter(),1) if n.tag in (ns+'p',ns+'h')]
                pending=[n for n in names if n.startswith(('Pictures/','Object','Thumbnails/'))]
            (out/(row['sha256']+'.json')).write_text(json.dumps({'paragraphs':paragraphs,'pending_assets':pending,'layout_review_pending':True,'page_mapping':None},ensure_ascii=False),encoding='utf-8')
            record.update(paragraphs=len(paragraphs),pending_assets=pending)
        except Exception as e:record['error']=type(e).__name__+': '+str(e)
    (out/'verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps({'attempted':len(report),'read':sum('paragraphs'in r for r in report),'paragraphs':sum(r.get('paragraphs',0)for r in report)}))

if __name__=='__main__':main()
