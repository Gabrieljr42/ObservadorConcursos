"""Merge successful observed exports, retaining failed attempts and source evidence."""
import hashlib
import json
from pathlib import Path


def main():
    root=Path('.tenderproof/product-completion/fapeg')
    batches=['documents-20260909T180651Z','documents-20260909T181044Z']
    resolved={};attempts=[];originals=[]
    for batch in batches:
        directory=root/batch
        report=json.loads((directory/'report.json').read_text(encoding='utf-8'))
        if not report['driver_closed']:raise ValueError('Driver not closed')
        for doc in report['documents']:
            attempts.append({'batch':batch,'doc_id':doc['doc_id'],'error':doc.get('error'),'sha256':doc.get('sha256')})
            if not doc.get('sha256'):continue
            sha=doc['sha256'];file=directory/(sha+'.pdf')
            if hashlib.sha256(file.read_bytes()).hexdigest()!=sha:raise ValueError('PDF digest mismatch')
            pages=json.loads((directory/(sha+'-pages.json')).read_text(encoding='utf-8'))
            resolved[doc['doc_id']]={**doc,'batch':batch,'empty_pages':[p['page_number'] for p in pages if not p['text'].strip()],'control_character_pages':[p['page_number'] for p in pages if any(ord(c)<32 and c not in '\n\r\t' for c in p['text'])]}
            if doc['kind']=='edital':originals.append(sha)
    result={'source':'fapeg_selection','scope':'All25 public export buttons in current SEAD/FAPEG009/2024 detail; other FAPEG calls and later summons website remain pending','documents':list(resolved.values()),'attempts':attempts,'pdf_count':len(resolved),'pdf_pages':sum(d['processed_pages'] for d in resolved.values()),'original_repeated_identically':len(originals)==2 and len(set(originals))==1,'all_drivers_closed':True,'runtime_reload_pending':True,'source_integrated':False,'published':False}
    assert result['pdf_count']==25
    (root/'personnel-export-completion.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:result[k] for k in ('pdf_count','pdf_pages','original_repeated_identically')}))
    print(json.dumps({'empty_pages':sum(len(d['empty_pages']) for d in resolved.values()),'control_character_pages':sum(len(d['control_character_pages']) for d in resolved.values())}))


if __name__=='__main__':main()
