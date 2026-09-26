"""Read/apply the expanded FAPEG daily policy through authenticated operator API."""
import argparse,json,re
from datetime import datetime,timezone
from pathlib import Path
import httpx


def main():
    parser=argparse.ArgumentParser();mode=parser.add_mutually_exclusive_group();mode.add_argument('--apply',action='store_true');mode.add_argument('--cycle-status',action='store_true');args=parser.parse_args()
    root=Path('.tenderproof/product-completion/fapeg')
    credentials=Path('.tenderproof/local-pilot/ACESSO-LOCAL.md').read_text(encoding='utf-8')
    email=re.search(r'E-mail:\s*([^\r\n]+)',credentials)[1].strip(' `')
    password=re.search(r'Senha:\s*([^\r\n]+)',credentials)[1].strip(' `')
    report={'at':datetime.now(timezone.utc).isoformat(),'applied':args.apply}
    with httpx.Client(base_url='http://localhost:13000/api',trust_env=False,timeout=90) as client:
        login=client.post('/auth/login',json={'email':email,'password':password});login.raise_for_status()
        client.headers['Authorization']='Bearer '+login.json()['access_token']
        if args.cycle_status:
            configured=json.loads((root/'runtime-expanded-configuration.json').read_text(encoding='utf-8'))
            cycle_id=configured['collection']['cycle_id']
            response=client.get('/tenderproof/continuous/cycles/'+cycle_id);response.raise_for_status()
            result={'at':datetime.now(timezone.utc).isoformat(),'cycle':response.json()}
            (root/'runtime-expanded-cycle.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
            jobs=result['cycle']['jobs'];counts={}
            for job in jobs:counts[job['kind']+':'+job['status']]=counts.get(job['kind']+':'+job['status'],0)+1
            print(json.dumps({'cycle_id':cycle_id,'status':result['cycle']['status'],'jobs':counts,'reasons':result['cycle']['reasons']}));return
        response=client.get('/tenderproof/continuous/status');response.raise_for_status()
        before=next(c for c in response.json()['sources'] if c['source']=='fapeg_selection');report['before']=before
        if args.apply:
            catalogue=client.get('/tenderproof/continuous/catalogue');catalogue.raise_for_status()
            entry=next(c for c in catalogue.json() if c['source']=='fapeg_selection')
            if entry['adapter']!='FapegAdapter' or len(entry['listing_urls'])!=4:raise ValueError('Runtime has not loaded expanded FAPEG source')
            policy={**before['policy'],'enabled':True,'mode':'real','interval_s':86400,'max_listing_pages':500,'max_candidates':1000,'max_documents':500,'cycle_timeout_s':86400}
            response=client.put('/tenderproof/continuous/sources/fapeg_selection',json=policy);response.raise_for_status();report['configuration']=response.json();report['catalogue']=entry
            response=client.post('/tenderproof/continuous/sources/fapeg_selection/collect');response.raise_for_status();report['collection']=response.json()
            response=client.get('/tenderproof/continuous/cycles/'+report['collection']['cycle_id']);response.raise_for_status();report['cycle']=response.json()
        path=root/('runtime-expanded-configuration.json' if args.apply else 'runtime-before-expanded-configuration.json')
        path.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
        print(json.dumps({'saved':str(path),'known_candidates':before['known_candidates'],'cycles':before['cycles'][:1],'collection':report.get('collection')}))


if __name__=='__main__':main()
