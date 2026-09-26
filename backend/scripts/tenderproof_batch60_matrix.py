"""Publish current batch evidence states without granting the next rollout gate."""
import json
from pathlib import Path

DOCS=Path('../docs')

def main():
    report=json.loads((DOCS/'tenderproof-batch60-current-validation.json').read_text(encoding='utf-8'))
    acceptance=json.loads((DOCS/'tenderproof-rollout-acceptance.json').read_text(encoding='utf-8'))
    if acceptance.get('batch60_gate')=='accepted_bounded_partial_scope_with_blocked_sources':
        raise ValueError('Batch60 is accepted; preserve accepted evidence rows and use the rollout matrix generator directly.')
    existing={row['source']:row for row in acceptance['sources']}
    publication_path=DOCS/'tenderproof-batch60-publication-live.json'
    publication=json.loads(publication_path.read_text(encoding='utf-8')) if publication_path.exists() else {}
    for row in report['sources']:
        samples=row['samples']
        registered=row['adapter_registered']
        references=sorted({sample['report'] for sample in samples})
        urls={}
        for name in references:
            origin=json.loads((DOCS/name).read_text(encoding='utf-8'))
            for cycle in origin.get('cycles',[]):
                if cycle['source']!=row['source']:continue
                for capture in cycle.get('captures',[]):
                    urls[capture['url']]={'url':capture['url'],'observed_at':capture.get('observed_at',origin.get('observed_at')),
                        'state':'captured_official_listing','sha256':capture.get('sha256')}
        evidence={'source':row['source'],'offline_validation':'tested' if registered else 'pending',
            'live_adapter_observation':'observed_valid_sample' if samples else ('observed_document_blocked' if registered else 'pending'),
            'homologation_state':'pending' if samples else 'blocked',
            'homologation_scope':'Batch60 quality gate pending; verified primary document samples only.' if samples else 'Not homologated; documented external or documentary impediment.',
            'last_validation':report['generated_at'],'evidence':['tenderproof-batch60-current-validation.json',*references],
            'samples':[{'external_id':s['external_id'],'cycle':s['cycle'],'run_id':s['run_id'],
                'document_sha256':s['artifact_sha256'],'evidence':s['report']} for s in samples],
            'coverage':row['coverage'],'browser_dependency':'HTTP evidence; zero browser sessions',
            'limitations':['Bounded official routes only; no whole-source certification.','Batch60 acceptance and batch99 expansion remain pending.'],
            'blocker':row['blocker'],'next_action':'Complete measured quality gate before expanding.' if samples else 'Resolve documented impediment and validate official original PDF.'}
        if urls:evidence['verified_urls']=list(urls.values())
        publication_samples=[s for s in publication.get('samples',[]) if s['source']==row['source']]
        if publication_samples:
            evidence['evidence'].append(publication_path.name)
            evidence['canonical_publication']={'states':sorted({s['state'] for s in publication_samples}),
                'blockers':sorted({s['reason'] for s in publication_samples if s.get('reason')}),
                'production':False}
            evidence['limitations'].extend(evidence['canonical_publication']['blockers'])
        if row['source']=='zambini_open':evidence['limitations'].append('Valid sample is historical archive; current listing had an explicit empty marker.')
        if row['source'] in ('consulplan_open','institutoconsulplan_open'):
            evidence['limitations'].append('Two original catalogue IDs share the observed portal and PDF; not independent documents or automatic canonical merge.')
        existing[row['source']]=evidence
    acceptance['sources']=list(existing.values())
    acceptance['batch60_gate']='not_accepted'
    (DOCS/'tenderproof-rollout-acceptance.json').write_text(json.dumps(acceptance,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('30 batch60 evidence states updated; gate remains pending')

if __name__=='__main__':main()
