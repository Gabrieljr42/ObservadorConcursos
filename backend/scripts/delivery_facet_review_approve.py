"""Record the checked effect of the Floresta fee-waiver result, without publishing."""
import json
import re
from pathlib import Path
from app.tenderproof.continuous_store import get_continuous_store
from app.tenderproof.store import get_store
from app.tenderproof import review_cases
from delivery_next_reextract_facet_title import AUTHORIZATION

ROOT = Path('/var/lib/observador/tenderproof/product-completion')
RESULT_SHA = '2037e1a1d6d3a77bca2243562c42de5fe8b71f915a49e166d431e7aa3c8c12e9'
BASE_SHA = 'd049b7595f6ed8d7282d82580b0a0de67b24fa8fe2935f1764c3cd5970043221'

def main():
    packet = json.loads((ROOT / 'delivery-facet-review-20260909.json').read_text())
    case = packet['case']
    assert case['id'] == 'drc-5ad9f0b120754b18aa9fe7a7c75c1600'
    by_hash = {document['artifact']['sha256']: document for document in case['documents']}
    assert set(by_hash) == {RESULT_SHA, BASE_SHA}
    result = by_hash[RESULT_SHA]
    assert len(result['pages']) == 192
    assert all(not page['error'] and not page['truncated'] for page in result['pages'])
    rows = [line for page in result['pages'] for line in page['text'].splitlines() if re.match(r'^\d{6,}\s', line)]
    assert len(rows) == 4780
    header = 'PREFEITURA MUNICIPAL DE FLORESTA-PE\nCONCURSO PÚBLICO - 01/2026\nORGANIZAÇÃO: FACET CONCURSOS\nRESULTADO PRELIMINAR DOS PEDIDOS DE ISENÇÃO'
    assert all(header in page['text'] for page in result['pages'])
    decisions = [
        {'sha256': RESULT_SHA, 'page': 1, 'snippet': header, 'effect': 'no_field_change',
         'reason': 'Conferência automatizada sob autorização delegada: as 192 páginas contêm cabeçalhos de cargos, 4780 linhas individuais de resultado de isenção e paginação. Conteúdo não individual conferido integralmente, sem mudança de inscrições, prova, cargos, vagas ou vencimentos. As decisões individuais não alteram o valor geral da taxa.'},
        {'sha256': BASE_SHA, 'page': 1,
         'snippet': 'PREFEITURA MUNICIPAL DE\nFLORESTA /PE\nCONCURSO PÚBLICO\nEDITAL 01/2026',
         'effect': 'reflected_in_selected_document',
         'reason': 'Conferência automatizada sob autorização delegada: este é o próprio edital selecionado; identidade, inscrições de24/08a01/10/2026 e prova prevista01/11/2026 foram conferidas nas páginas1,2e9. Não há alteração posterior desses campos no resultado de isenção.'},
    ]
    queue, store = get_continuous_store(), get_store()
    run = store.get_run(packet['run_id'])
    approved = review_cases.approve(queue, store, run, case['id'], case['revision_hash'], decisions)
    output = ROOT / 'delivery-facet-review-approved-20260909.json'
    output.write_text(json.dumps({'authorization': AUTHORIZATION, 'approval': approved,
        'decisions': decisions, 'review': queue.review_for_run(run)}, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'receipt': str(output), 'case_id': case['id'], 'review': queue.review_for_run(run)}, ensure_ascii=False))

if __name__ == '__main__':
    main()
