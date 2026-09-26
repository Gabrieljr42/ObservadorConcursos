"""Source-specific read of an acquired PDF in a 1GB offline container; no global engine change."""
import hashlib,json,signal
from pathlib import Path
from pypdf import PdfReader
import io

def main():
    out=Path('/evidence/profix-native-recovery.json')
    sha='4ba3220bff199a24aa617a22bcd68f2f10a893ebc751363cd5cf11588af49c75'
    raw=(Path('/evidence/current-documents-20260909T160517Z')/(sha+'.pdf')).read_bytes()
    def timeout(*args):raise TimeoutError('source read exceeded 180 seconds')
    signal.signal(signal.SIGALRM,timeout);signal.alarm(180)
    result={'input_sha256':sha,'pages':[],'source_integrated':False,'review_required':True}
    try:
        if len(raw)>30*1024*1024 or hashlib.sha256(raw).hexdigest()!=sha:raise ValueError('input bounds/hash')
        reader=PdfReader(io.BytesIO(raw),strict=True)
        if reader.is_encrypted or len(reader.pages)>200:raise ValueError('PDF bounds')
        result['total_pages']=len(reader.pages);size=0
        for n,page in enumerate(reader.pages,1):
            text=page.extract_text() or '';size+=len(text.encode('utf-8','backslashreplace'))
            if size>8*1024*1024:raise ValueError('output bounds')
            result['pages'].append({'page_number':n,'text':text,'invalid_unicode_positions':[i for i,c in enumerate(text) if 0xD800<=ord(c)<=0xDFFF]})
        result['state']='succeeded'
    except Exception as exc:result.update(state='failed',error=type(exc).__name__+': '+str(exc))
    finally:signal.alarm(0)
    out.write_text(json.dumps(result,ensure_ascii=True),encoding='utf-8')
    print(json.dumps({'state':result['state'],'pages':len(result['pages']),'empty_pages':sum(not p['text'].strip() for p in result['pages']),'error':result.get('error')}))

if __name__=='__main__':main()
