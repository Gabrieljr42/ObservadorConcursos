"""Read acquired DOC bytes with Antiword inside an offline bounded container."""
import argparse
import hashlib
import json
import os
import subprocess
from pathlib import Path


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('manifest',type=Path)
    args=parser.parse_args()
    output=Path('/output')
    records=[]
    for row in json.loads(args.manifest.read_text(encoding='utf-8')):
        record=dict(row)
        try:
            file=Path('/input',row['relative_file']).resolve()
            file.relative_to('/input')
            raw=file.read_bytes()
            if len(raw)>15_000_000 or hashlib.sha256(raw).hexdigest()!=row['sha256']:
                raise ValueError('DOC hash or size mismatch')
            if not raw.startswith(bytes.fromhex('d0cf11e0a1b11ae1')):
                raise ValueError('DOC binary signature mismatch')
            process=subprocess.run(['/reader/usr/bin/antiword','-m','UTF-8.txt',str(file)],
                env={**os.environ,'ANTIWORDHOME':'/reader/usr/share/antiword'},capture_output=True,timeout=30)
            if process.returncode:
                raise ValueError('Antiword failed: '+process.stderr.decode('utf-8',errors='replace')[:1000])
            if len(process.stdout)>5_000_000:
                raise ValueError('DOC text output limit')
            text=process.stdout.decode('utf-8')
            if not text.strip():
                raise ValueError('DOC without extractable text')
            data={'input_sha256':row['sha256'],'source':row['source'],'url':row['url'],
                'reader':'Antiword; see audit-tools/antiword/package-receipt.json',
                'method':'plain_text_lines','text':text,'line_count':len(text.splitlines()),
                'warning':process.stderr.decode('utf-8',errors='replace'),
                'page_mapping_available':False,'review_required':True,'published':False,
                'formatting_images_and_embedded_objects_review_pending':True}
            (output/(row['sha256']+'.json')).write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
            record.update(characters=len(text),lines=len(text.splitlines()))
        except Exception as exc:
            record['error']=type(exc).__name__+': '+str(exc)
        records.append(record)
        (output/'verification.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'attempted':len(records),'read':sum('characters' in r for r in records),
        'characters':sum(r.get('characters',0) for r in records),'errors':[r for r in records if r.get('error')]}))


if __name__=='__main__':
    main()
