"""Verify owner-authorized access to workbook produced by the recurring queue."""
import hashlib,json,re
from datetime import datetime,timezone
from pathlib import Path
import httpx


def main():
    root=Path('.tenderproof/product-completion/fapeg')
    queued=json.loads((root/'current-queue-evidence.json').read_text(encoding='utf-8'))
    job=next(j for j in queued['jobs'] if j['title'].startswith('45/2025 |'))
    if job['status']!='succeeded':raise ValueError('Scheduled call not finished')
    credentials=Path('.tenderproof/local-pilot/ACESSO-LOCAL.md').read_text(encoding='utf-8')
    email=re.search(r'E-mail:\s*([^\r\n]+)',credentials)[1].strip(' `')
    password=re.search(r'Senha:\s*([^\r\n]+)',credentials)[1].strip(' `')
    with httpx.Client(base_url='http://localhost:13000/api',timeout=30,trust_env=False) as client:
        response=client.post('/auth/login',json={'email':email,'password':password});response.raise_for_status()
        client.headers['Authorization']='Bearer '+response.json()['access_token']
        response=client.get('/tenderproof/runs/'+job['run_id']);response.raise_for_status();run=response.json()
        report={'at':datetime.now(timezone.utc).isoformat(),'cycle_id':queued['cycle']['cycle_id'],'job_id':job['job_id'],'run_id':job['run_id'],
            'execution_status':run['execution_status'],'validation_status':run['validation_status'],'workbooks':[],'published':False,'source_integrated':False}
        for extra in run['supplementary_documents']:
            if extra['document'].get('file_format')!='xlsx':continue
            artifact=extra['artifact'];response=client.get('/tenderproof/runs/'+run['run_id']+'/artifacts/'+artifact['artifact_id']);response.raise_for_status()
            sha=hashlib.sha256(response.content).hexdigest()
            if sha!=artifact['sha256'] or len(response.content)!=artifact['byte_len']:raise ValueError('Served artifact identity differs')
            report['workbooks'].append({'sha256':sha,'byte_len':len(response.content),'api_content_type':response.headers.get('content-type'),
                'content_disposition':response.headers.get('content-disposition'),'extractor_version':extra['reading']['extractor_version'],
                'cells':sum(len(s['cells']) for s in extra['reading']['sheets']),'owner_api_access_verified':True})
        if not report['workbooks']:raise ValueError('No preserved workbook in queued run')
    (root/'runtime-workbook-access.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(report))


if __name__=='__main__':main()
