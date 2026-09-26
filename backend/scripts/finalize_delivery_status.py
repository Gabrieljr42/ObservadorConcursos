"""Record the scoped delivery without granting full-source certification."""
import csv
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STATUS = ROOT / 'docs/tenderproof-product-status.json'
EVIDENCE = ROOT / 'backend/.tenderproof/product-completion'
PUBLISHED = {
    'access_open': [1], 'abcp_open': [2, 7], 'fenix_open': [3],
    'jcm_open': [4], 'institutoconsulplan_open': [5], 'imeso_open': [6],
    'idib_open': [8], 'cebraspe_open': [9], 'fepese_open': [10],
}

def main():
    status = json.loads(STATUS.read_text(encoding='utf-8'))
    snapshot = json.loads((EVIDENCE / 'delivery-snapshot-20260909-final.json').read_text(encoding='utf-8-sig'))
    runtime = {s['source']: s for s in snapshot['sources']}
    evidence = ['docs/ENTREGA-2026-09-09.md',
                'backend/.tenderproof/product-completion/delivery-app-20260909.json',
                'backend/.tenderproof/product-completion/delivery-snapshot-20260909-final.json']
    status.setdefault('historical_full_inventory_goal', status['goal'])
    status['goal'] = 'Close a usable, scoped source-to-app delivery and explicitly document residual work; full integration of all 99 is not claimed.'
    status['updated_at'] = datetime.now(timezone.utc).isoformat()
    status['delivery'] = {
        'state': 'closed_with_documented_residual_work',
        'scope': 'Selected contests and supported fields, not whole-source integration',
        'catalogue_contests': 10, 'catalogue_sources': 9,
        'new_contests_this_delivery': 7,
        'sources_with_historical_successful_detail_jobs': 76,
        'fully_integrated_sources': 0,
        'pending_document_contest_ids': [2, 3],
        'known_amended_deadline_not_yet_applied_contest_ids': [3],
        'published_contests_by_source': PUBLISHED,
        'application_url': 'http://127.0.0.1:13000/inicio',
        'source_matrix': 'docs/entrega-fontes-2026-09-09.csv',
        'evidence': evidence,
        'solari': {'authorized_usd':20, 'reserved_usd':5.26, 'new_sessions_this_delivery':0, 'confirmed_billed_usd':None},
    }
    matrix = []
    for source in status['sources']:
        key = source['source']
        operational = runtime.get(key, {})
        successes = operational.get('historical_detail_jobs', {}).get('succeeded', 0)
        ids = PUBLISHED.get(key, [])
        missing = not source.get('current_adapter')
        if ids:
            next_action = ('Retificação de Pedrinhas com novas datas ainda não aplicada; aviso no aplicativo.' if key == 'fenix_open'
                           else 'Garça publicada; três documentos novos de Ibiúna pendentes.' if key == 'abcp_open'
                           else 'Ampliar campos e cobertura além da seleção publicada; sem aceite integral.')
            for name in ('catalogue_publication_and_sync', 'visual_app_verification'):
                requirement = source['requirements'][name]
                requirement['state'] = 'partial'
                requirement['evidence'] = list(dict.fromkeys(requirement.get('evidence', []) + evidence))
                requirement['next_action'] = next_action
        elif missing:
            next_action = 'Bloqueio individual em docs/ENTREGA-BLOQUEIOS-FONTES.md; retomar somente com mudança verificável ou alternativa concreta.'
        elif successes:
            next_action = 'Reutilizar os runs preservados: conferir identidade/campos e retificações; preparar proposta e fechar até o aplicativo.'
        else:
            next_action = 'Adaptador sem trabalho de detalhe bem-sucedido neste snapshot; examinar erro existente antes de repetir coleta.'
        matrix.append({'numero':source['number'], 'fonte':key, 'nome':source['name'],
            'adaptador':source.get('current_adapter') or '',
            'coletas_detalhe_bem_sucedidas_historicas':successes,
            'concursos_no_aplicativo':','.join(map(str,ids)),
            'integracao_fonte_completa':'nao', 'proxima_acao':next_action})
    path = ROOT / 'docs/entrega-fontes-2026-09-09.csv'
    with path.open('w', encoding='utf-8-sig', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=list(matrix[0]), delimiter=';')
        writer.writeheader()
        writer.writerows(matrix)
    STATUS.write_text(json.dumps(status, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'sources':len(matrix), 'sources_in_app':len(PUBLISHED), 'contests_in_app':sum(map(len,PUBLISHED.values())), 'without_app':sum(not row['concursos_no_aplicativo'] for row in matrix)}, ensure_ascii=False))

if __name__ == '__main__':
    main()
