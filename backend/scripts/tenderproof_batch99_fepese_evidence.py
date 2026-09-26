"""Reproduce FEPESE inspected family and preserved amendment-only impediment."""
import hashlib,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from bs4 import BeautifulSoup
from app.tenderproof.batch99_fepese_adapter import FepeseAdapter,HOSTS
OWN=Path('tests/fixtures/tenderproof_batch99_own');FIX=Path('tests/fixtures/tenderproof_batch99_fepese')

def rows(root):
    found=[]
    for manifest in root.glob('*manifest.json'):
        data=json.loads(manifest.read_text(encoding='utf-8'))
        for row in data.get('pages',[]):
            if row.get('source')=='fepese_open':found.append((manifest,row))
    return found

def main():
    a=FepeseAdapter();captures=rows(OWN)+rows(FIX);errors=[];proof=[]
    for path,r in captures:
        raw=(path.parent/r['file']).read_bytes()
        valid=len(raw)==r['bytes'] and hashlib.sha256(raw).hexdigest()==r['sha256']
        if not valid:errors.append(r['file'])
        proof.append({k:r[k] for k in ('url','status','bytes','sha256','file')})
    listing=next((path,r) for path,r in captures if r.get('kind')=='listing0')
    lhtml=(listing[0].parent/listing[1]['file']).read_text(encoding=listing[1]['encoding'])
    page=a.parse_listing(lhtml,listing[1]['url'],200)
    observed_hosts={__import__('urllib.parse',fromlist=['urlsplit']).urlsplit(n['href']).hostname for n in BeautifulSoup(lhtml,'html.parser').select(a.candidate_selector)}
    sources=[]
    for c in page.candidates:
        home=next((p,r) for p,r in captures if r['url']==c.detail_url_observed and '?go=' not in r['url'])
        html=(home[0].parent/home[1]['file']).read_text(encoding=home[1]['encoding'])
        target=a.detail_resource_urls(html,c.detail_url_observed)[0]
        tab=next((p,r) for p,r in captures if r['url']==target)
        body=(tab[0].parent/tab[1]['file']).read_text(encoding=tab[1]['encoding'])
        composed=a.compose_detail(html,c.detail_url_observed,[{'url':target,'body':body}])
        a.confirm_identity(c,composed,c.detail_url_observed)
        docs=a.documents(composed,c)
        try:a.choose_document(docs);blocked=False
        except ValueError:blocked=True
        sources.append({'candidate':c.model_dump(mode='json'),'resource_url':target,'documents':[d.model_dump(mode='json') for d in docs],'original_selection_blocked':blocked})
    report={'source':'fepese_open','adapter_implemented':True,'source_homologated':False,'scope':'Only three inspected official contest subdomains; no invented download URL or retification promotion','observed_listing_hosts':sorted(observed_hosts),'inspected_hosts':list(HOSTS),'listing_coverage':'partial, other hosts not covered by this contract','candidates':sources,'captures':proof,'sha_errors':errors,'tests':'tests/test_tenderproof_batch99_fepese.py:3passed','live_report':'docs/tenderproof-batch99-fepese-live.json if executed after central integration','limitations':['All3 visible principal labels point to_TR01.pdf amendments','No original filename is guessed by deleting_TR01','No validPDFsample or fullcoverage is claimed','No changes to FAPESC adapter or central registry']}
    live_path=Path('../docs/tenderproof-batch99-fepese-live.json')
    if live_path.exists():
        live=json.loads(live_path.read_text(encoding='utf-8'))
        attempts=[attempt for cycle in live['cycles'] for attempt in cycle['attempts']]
        report['live']={'cycles':len(live['cycles']),'attempts':len(attempts),'valid_samples':sum(attempt['validation_status']=='valid' for attempt in attempts),'all_original_selections_blocked':all('nenhum edital principal' in (attempt['error'] or '') for attempt in attempts),'driver_cleanup':live['driver_cleanup'],'downloaded_artifacts':sum(bool(attempt['artifact']) for attempt in attempts),'listing_coverage':[cycle['coverage'] for cycle in live['cycles']]}
    Path('../docs/tenderproof-batch99-fepese-investigation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'candidates':len(sources),'observed_listing_hosts':len(observed_hosts),'all_blocked':all(s['original_selection_blocked'] for s in sources),'hash_errors':errors}))
    assert not errors

if __name__=='__main__':main()
