"""Update final-batch evidence rows, preserving all previous accepted batches."""
import json
from pathlib import Path

DOCS=Path('../docs')
def read(name):return json.loads((DOCS/name).read_text(encoding='utf-8-sig'))

def main():
    audit=read('tenderproof-batch99-current-validation.json')
    acceptance=read('tenderproof-rollout-acceptance.json')
    if acceptance.get('batch99_gate','').startswith('accepted'):raise ValueError('Preserve accepted gate; review before regenerating evidence rows')
    existing={r['source']:r for r in acceptance['sources']}
    findings={}
    for name in ('tenderproof-batch99-southeast-validation.json','tenderproof-batch99-regions-investigation.json','tenderproof-batch99-foundations-findings.json'):
        if not (DOCS/name).exists():continue
        for row in read(name)['sources']:
            findings[row['source']]={'note':row.get('finding',row.get('note',row.get('blocker','; '.join(row.get('findings',[])) or row.get('listing_discovery','')))),'captures':row.get('captures',[]),'report':name}
    own={
        'oppus_open':'Domínio oficial redireciona para conteúdo de cassino; nenhuma cadeia atual de concursos verificada. Identificar portal oficial funcional.',
        'nossorumo_open':'API pública verificada; dois ciclos receberam401 nos PDFs originais. Necessário acesso público funcional ao documento oficial.',
        'fepese_open':'Três subdomínios inspecionados exibem somente versõesTR01, mesmo sob rótuloEdital. Aguardar original oficial ou revisão explícita dos efeitos, sem promoção automática.',
        'ieses_open':'Somente SCGÁS2026 e CRMVSC2026 contratados; amostra documental SCGÁS001/2026. Dez outros subportais da primeira página ainda fora do contrato.',
        'verbena_selection':'Somente Câmara de Pires do Rio2026; banner oficial e título do detalhe revisado. Demais seleções e arquivo fora da cobertura.',
        'klc_open':'Aba oficial em andamento,199 candidatos observados; apenas amostra632 documentada.',
        'legatus_open':'Cards oficiais e amostra160 Tanque do Piauí, com original3181.',
        'fapex_selection':'Alternativa pública de editais, estágio nr2O; portalRHautenticado não utilizado. Ingresso em mestrado profissional excluído.'}
    publication=read('tenderproof-batch99-publication-live.json') if (DOCS/'tenderproof-batch99-publication-live.json').exists() else {}
    for row in audit['sources']:
        source=row['source'];samples=row['samples'];registered=row['adapter_registered'];detail=findings.get(source,{})
        note=own.get(source,detail.get('note'))
        if not note:raise ValueError('Missing explicit source finding: '+source)
        refs=sorted({s['report'] for s in samples}|{a['report'] for a in audit['attempts'] if a['source']==source})
        if detail.get('report'):refs.append(detail['report'])
        if source in own:refs.append('tenderproof-batch99-own-contracts.md')
        urls={}
        for capture in detail.get('captures',[]):
            if capture.get('url'):urls[capture['url']]={'url':capture['url'],'observed_at':capture.get('observed_at'),'state':capture.get('status'),'sha256':capture.get('sha256',capture.get('fixture_sha256'))}
        for name in refs:
            if not name.endswith('.json'):continue
            for cycle in read(name).get('cycles',[]):
                if cycle.get('source')!=source:continue
                for capture in cycle.get('captures',[]):
                    urls[capture['url']]={'url':capture['url'],'observed_at':capture.get('observed_at'),'state':'captured_listing','sha256':capture.get('sha256')}
        canonical=[s for s in publication.get('samples',[]) if s['source']==source]
        evidence={'source':source,'offline_validation':'tested' if registered else 'not_implemented',
            'live_adapter_observation':'observed_valid_sample' if samples else ('observed_document_blocked' if registered else 'investigated_no_adapter'),
            'homologation_state':'pending' if samples else 'blocked','homologation_scope':'Final batch gate pending; bounded evidence only.' if samples else 'Not homologated; explicit unresolved source/document scope.',
            'last_validation':audit['generated_at'],'evidence':['tenderproof-batch99-current-validation.json',*sorted(set(refs))],
            'samples':[{'external_id':s['external_id'],'cycle':s['cycle'],'run_id':s['run_id'],'document_sha256':s['artifact_sha256'],'evidence':s['report']} for s in samples],
            'coverage':row['coverage'],'browser_dependency':'HTTP only; no browser sessions used',
            'limitations':[note,'Sem certificação de cobertura integral; produção desativada.'],
            'blocker':None if samples else note,'next_action':'Concluir portão medido do lote99.' if samples else note}
        if urls:evidence['verified_urls']=list(urls.values())
        if canonical:
            evidence['canonical_publication']={'states':sorted({s['state'] for s in canonical}),'blockers':sorted({s['reason'] for s in canonical if s.get('reason')}),'production':False}
            evidence['evidence'].append('tenderproof-batch99-publication-live.json')
        existing[source]=evidence
    acceptance['sources']=list(existing.values());acceptance['batch99_gate']='not_accepted'
    (DOCS/'tenderproof-rollout-acceptance.json').write_text(json.dumps(acceptance,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('39 final-batch rows updated; previous gates preserved; final gate pending')

if __name__=='__main__':main()
