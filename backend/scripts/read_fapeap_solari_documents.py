"""Read captured FAPEAP documents offline, retaining failed and unsupported cases."""
import json,hashlib
from pathlib import Path
from app.tenderproof.processing import extract_pages_isolated
from app.tenderproof.docx_text import extract_docx

def main():
    source=Path('/evidence/solari-complete');out=Path('/evidence/document-reading');out.mkdir(exist_ok=True)
    report={'documents':[],'source_integrated':False,'published':False}
    for doc in json.loads((source/'report.json').read_text())['documents']:
        if 'sha256' not in doc:continue
        sha=doc['sha256'];row={**doc};report['documents'].append(row)
        try:
            raw=(source/(sha+'.'+doc['format'])).read_bytes()
            if hashlib.sha256(raw).hexdigest()!=sha:raise ValueError('Input hash mismatch')
            if doc['format']=='pdf':
                pages,total,processed,truncated,errors=extract_pages_isolated(raw,artifact_id='fapeap-'+sha,owner_id='fapeap-source-audit',max_bytes=30*1024*1024,max_pages=200)
                (out/(sha+'-pages.json')).write_text(json.dumps([p.model_dump(mode='json') for p in pages],ensure_ascii=False),encoding='utf-8')
                row.update(total_pages=total,processed_pages=processed,truncated=truncated,errors=errors,empty_pages=sum(not p.text.strip() for p in pages))
            elif doc['format']=='zip' and '.docx' in doc['url'].lower():
                result=extract_docx(raw);(out/(sha+'-word.json')).write_text(json.dumps(result,ensure_ascii=False),encoding='utf-8');row.update(paragraphs=len(result['paragraphs']),pending_features=result['pending_features'],layout_review_required=True)
            else:row['reading_pending']='format_requires_reader'
        except Exception as e:row['error']=type(e).__name__+': '+str(e)
        (out/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
        print(json.dumps({'files':len(report['documents']),'pages':row.get('processed_pages'),'error':row.get('error')}),flush=True)
    report['finished']=True;(out/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')

if __name__=='__main__':main()
