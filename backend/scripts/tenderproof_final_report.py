"""Generate final scoped delivery report only after all rollout gates pass."""
import json
from datetime import datetime,timezone
from pathlib import Path

DOCS=Path('../docs')
def read(name):return json.loads((DOCS/name).read_text(encoding='utf-8-sig'))
def main():
    gate=read('tenderproof-batch99-gate-validation.json');assert gate['passed'] and gate['accepted']
    matrix=read('tenderproof-rollout-matrix.json');assert matrix['total_sources']==99
    rows=matrix['sources'];implemented=[r for r in rows if r['adapter']]
    homologated=[r for r in rows if r['homologation_state']=='partial']
    blocked=[r for r in rows if r['homologation_state']=='blocked']
    assert len(homologated)+len(blocked)==99
    report={'generated_at':datetime.now(timezone.utc).isoformat(),
        'delivery_scope':'Etapas11–13 entregues com aceite por amostras e impedimentos explícitos; não significa99adaptadores ou99fontes homologadas.',
        'stages':{
            '11':{'state':'accepted_bounded_partial_scope','pilot_sources':10,'evidence':'tenderproof-rollout-acceptance.json','whole_source_coverage':False},
            '12':{'state':'implemented_and_validated_in_isolation','behavior':['Criação e atualização com revisão e evidência','Identidade explícita, aliases e concorrência sem fusão textual','Preservação de desconhecidos e conflitos','Versões, outbox transacional, idempotência e rollback','Autenticação e isolamento entre usuários','Link autenticado de documento POST e página oficial','Migração explícita para concursos distintos na mesma URL'],'production_enabled':False},
            '13':{'state':'all99_investigated_bounded_gates_accepted_with_exclusions','cumulative_gates':[10,30,60,99],'full99_integration_claimed':False}},
        'counts':{'inventory_sources':99,'implemented_adapters_including_partial':len(implemented),
            'fully_implemented_contracts':sum(r['implementation_state']=='implemented' for r in rows),
            'partial_implementations':sum(r['implementation_state']=='partial' for r in rows),
            'without_adapter':99-len(implemented),'sources_with_live_adapter_evidence':sum(r['live_adapter_observation'] in ('observed_document_blocked','observed_valid_sample','observed','observed_previous_stage') for r in rows),
            'homologated_for_partial_scope':len(homologated),'without_homologation':len(blocked),'whole_source_coverage_certified':0},
        'tests':{'integrated':gate['regression'],'final_postgresql':gate['postgres_tests'],
            'note':'Suítes focais e PostgreSQL se sobrepõem; não somar como testes únicos. Alterações posteriores de FAPESE/codificação têm provas focais próprias.'},
        'batch99':{'sources_with_two_valid_live_cycles':len(gate['valid_sample_sources']),
            'real_process_crash_recovery_sources':len(gate['valid_sample_sources']),
            'canonical_creation_sources':gate['canonical_creation_sources'],'canonical_review_blocked_sources':gate['canonical_blocked_sources'],
            'publication_evidence':'tenderproof-batch99-publication-live.json','material_update_evidence':'tenderproof-batch99-material-update.json',
            'new_document_review':'Novos manifestos e identidade da requisição entram em revisão; retificações não são aplicadas automaticamente.'},
        'production':{'collection_activated':False,'publication_activated':False,'real_notifications_sent':0,'production_database_migrated':False,
            'activation_requirements':['Backup e migração explícita no banco alvo, com reconciliação manual se houver conflitos','Configuração deliberada de operador, fontes e limites','Aceitação das restrições por fonte antes de qualquer ativação']},
        'remaining_sources':[{'source':r['source'],'name':r['name'],'adapter':r['adapter'],'reason':r['blocker'],'next_action':r['next_action']} for r in blocked],
        'operational_evidence':'tenderproof-batch99-operations-review.json',
        'main_reports':['tenderproof-rollout-matrix.json','tenderproof-rollout-matrix.md','tenderproof-rollout-plan.json','tenderproof-rollout-acceptance.json','tenderproof-batch99-gate-validation.json','tenderproof-batch99-current-validation.json','tenderproof-batch99-post-review.json','tenderproof-batch99-identity-migration.md','tenderproof-batch99-final-review.json','tenderproof-ui-validation.json']}
    (DOCS/'tenderproof-phases11-13-final.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report['counts']))

if __name__=='__main__':main()
