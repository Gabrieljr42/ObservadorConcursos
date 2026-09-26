"""Rebuild regional investigation evidence from immutable bounded captures."""
import hashlib
import json
from pathlib import Path
from collections import defaultdict
from datetime import datetime, timezone

FIX=Path('tests/fixtures/tenderproof_batch99_regions')
NOTES={
 'fapesc_selection':'Official delegated archive2022; original001/2022 and two amendments observed. PDF has two leading LF bytes; exact transport preserved, transport signature accepts bounded prefix but production strict parser rejects; two failed offline cycles preserved. No byte repair or certification.',
 'fundect_selection':'Observed consultations page contains research funding/productivity, PICTEC and event programmes. No scoped personnel notice proved in bounded sample; not certified empty.',
 'fapemat_selection':'Observed official www.fapemat.mt.gov.br redirect and editais_1. No scoped personnel sample. Shared host /web/secitec content belongs to SECITEC and cannot prove FAPEMAT selection.',
 'fapeg_selection':'SEAD official listing links FAPEG009/2024 contest59. Original button177 exports by POST. Header Content-Type application/x-www-form-urlencoded required by observed downloader. First headerless500 preserved; corrected exact official request returns PDF29pages. Typed POST integration completed, 2real cycles valid29pages/sameSHA, recovery without repost tested.',
 'fapdf_selection':'Observed current editais-fapdf-20261 lists science and innovation funding. No scoped personnel sample proved; not certified empty.',
 'fapt_selection':'Official /fapt/editais/31uugl1y7as4 resolves to public programme listing. No scoped personnel sample proved. FAPTO is a different foundation and not substituted.',
 'fapeam_selection':'Official editais/?aba=editais-abertos contains funding programmes. Scientific/logo competitions and bursary selection are outside personnel scope.',
 'fapespa_selection':'Reviewed archive PSS001/2025, current /chamadas/ section proves temporary personnel selection. Original PDF is explicitly reviewed official indexed evidence, absent from current section links. This is not a claim of discovery in current HTML or complete2026coverage.',
 'fapeap_selection':'Old fapeap.ap.gov.br has verified TLS hostname mismatch. Legitimate official fapeap.portal.ap.gov.br and /publicacoes both200. Current Centelha/PROFIX/research/startup programmes are out of personnel scope. Old TLS failure is not attributed to new portal.',
 'faperr_selection':'Observed current homepage/public calls do not prove personnel selection. No reliable empty marker or broad coverage conclusion.',
 'fapero_selection':'Official category concursos-e-convocacoes/?e=2503 contains selections of OTHER agencies including SEDAM/IDEP despite FAPERO breadcrumb. Cannot bind those to FAPERO. Institutional publications include procurement/material acquisition. No personnel sample proved; no fake empty contract.',
 'fapac_selection':'Official /98-2/ lists OSC institutional calls, scientific bursaries Maes da Ciencia and Mentes Azuis. Those are outside personnel scope; no scoped sample proved.'}

def main():
    grouped=defaultdict(list);errors=[];count=0
    for manifest in sorted(FIX.glob('*manifest.json')):
        data=json.loads(manifest.read_text(encoding='utf-8'))
        for row in data.get('pages',data.get('documents',[])):
            if not isinstance(row,dict) or row.get('source') not in NOTES:continue
            out={k:row[k] for k in ('source','url','basis','observed_at','tls_verified','method','body','headers','status','location','bytes','sha256','file','pages','error_type','error','client_closed') if k in row}
            out['manifest']=str(manifest)
            if row.get('file'):
                file=FIX/row['file'];raw=file.read_bytes();count+=1
                ok=len(raw)==row['bytes'] and hashlib.sha256(raw).hexdigest()==row['sha256']
                out['durable_bytes_sha_verified']=ok
                if not ok:errors.append(str(file))
            grouped[row['source']].append(out)
    live_path=Path('../docs/tenderproof-batch99-regions-live.json')
    live=json.loads(live_path.read_text(encoding='utf-8')) if live_path.exists() else None
    samples=[]
    for path in (live_path,Path('../docs/tenderproof-batch99-fapeg-live.json')):
        if not path.exists():continue
        report_live=json.loads(path.read_text(encoding='utf-8'))
        for cycle in report_live['cycles']:
            for attempt in cycle['attempts']:
                sample={'source':cycle['source'],'cycle':cycle['cycle'],'execution_status':attempt['execution_status'],'validation_status':attempt['validation_status'],'error':attempt['error'],'report':str(path),'run_id':attempt['run_id'],'driver_cleanup':report_live.get('driver_cleanup')}
                artifact=attempt.get('artifact')
                if artifact:
                    file=Path(report_live['root'])/'artifacts'/artifact['storage_path']
                    raw=file.read_bytes()
                    valid=len(raw)==artifact['byte_len'] and hashlib.sha256(raw).hexdigest()==artifact['sha256']
                    sample.update(sha256=artifact['sha256'],bytes=len(raw),pages=attempt['total_pages'],durable_bytes_sha_verified=valid,acquisition_request=attempt['document'].get('acquisition_request'))
                    if not valid:errors.append(str(file))
                samples.append(sample)
    report={'generated_at':datetime.now(timezone.utc).isoformat(),'scope':'12regional institutional personnel sources; bounded public verified TLS; no production/browser/login; funding/bolsas/procurement excluded','gate99_accepted':False,'captured_records_verified':count,'hash_errors':errors,'sources':[{'source':source,'finding':note,'captures':grouped[source]} for source,note in NOTES.items()],'live_report':str(live_path) if live else None,'live_samples':samples,'counts':{'investigated_sources':12,'implemented_contracts':3,'sources_with_two_valid_real_cycles':sum(sum(x['validation_status']=='valid' and x['source']==source for x in samples)>=2 for source in NOTES),'valid_real_samples':sum(x['validation_status']=='valid' for x in samples),'sources_without_scoped_contract':9,'implemented_sources_with_parser_block':1},'limitations':['12 investigations are not12integrated adapters','Historical reviewed archives explicitly narrower than whole institution','No scoped sample found is not proof of legitimate empty list','POST method/body identity is persisted; historical GET manifests unchanged','Live/replay/recovery/capacity gates are separate from capture inspection']}
    Path('../docs/tenderproof-batch99-regions-investigation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'sources':len(NOTES),'capture_records':count,'hash_errors':errors}))
    assert not errors

if __name__=='__main__':main()
