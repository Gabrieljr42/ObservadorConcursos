"""Save the real unresolved Barra Longa effects as a draft; never clear the gate."""
import json
from pathlib import Path
from app.tenderproof.continuous_store import get_continuous_store
from app.tenderproof.store import get_store
from app.tenderproof import review_cases
from delivery_next_reextract_six_2026 import AUTHORIZATION

ROOT = Path('/var/lib/observador/tenderproof/product-completion')

def main():
    packet = json.loads((ROOT / 'delivery-elo-review-20260909.json').read_text())
    queue, store = get_continuous_store(), get_store()
    run = store.get_run(packet['run_id'])
    case = review_cases.read(queue, packet['case']['id'], run.owner_user_id)
    base = 'a5a7ff5a11bef285d389bd71a5e2d53b8ad5e82dec8d545edcea653c0fbef5a2'
    later = '5780db65b9a5c7fd1aa63336be35d7763fd271710144a0b8c409c4da90fa201a'
    documents = {doc['artifact']['sha256']: doc for doc in case['documents']}
    assert set(documents) == {base, later}
    new_pages = {page['page_number']: page['text'] for page in documents[later]['pages']}
    stage_snippet = '8.1 O Processo Seletivo Público constará de prova Objetiva de Múltipla Escolha e Títulos.'
    final_snippet = new_pages[5][new_pages[5].index('Até 30/11/2026'):new_pages[5].index('No prazo máximo')]
    title_snippet = new_pages[5][new_pages[5].index('Até 13/11/2026'):new_pages[5].index('Até 30/11/2026')]
    def change(name, previous, new, page, snippet):
        assert snippet in new_pages[page]
        return {'field_name': name, 'previous': previous, 'new': new,
            'provenance': [{'document_sha256': later, 'page': page, 'snippet': snippet}]}
    decisions = [
        {'sha256': base, 'page': 1, 'snippet': 'PROCESSO SELETIVO PÚBLICO - EDITAL Nº 01/2026',
         'effect': 'reflected_in_selected_document',
         'reason': 'Edital-base preservado. Campos alterados pela retificação permanecem pendentes de composição; não há aprovação deste rascunho.'},
        {'sha256': later, 'page': 1, 'snippet': stage_snippet, 'effect': 'field_changes',
         'reason': 'Conferência automatizada autorizada: substitui TAF por títulos, acrescenta entrega de títulos e muda prazo de resultado final. Inscrições18/08a18/09 às15h e prova objetiva18/10 permanecem iguais. A composição inicial desses efeitos ainda não é suportada; manter gate pendente.',
         'changes': [change('etapas_prova', 'Objetiva de Múltipla Escolha e TAF', 'Objetiva de Múltipla Escolha e Títulos', 1, stage_snippet),
                     change('resultado_final_prazo', '2026-11-17', '2026-11-30', 5, final_snippet),
                     change('entrega_titulos_prazo', None, '2026-11-13', 5, title_snippet)]},
    ]
    if case.get('draft') == decisions:
        result = {'draft_revision': case['draft_revision'], 'idempotent': True}
    else:
        result = review_cases.save_draft(queue, run, case['id'], case['revision_hash'], case.get('draft_revision', 0), decisions)
    assert queue.review_for_run(run)['pending']
    path = ROOT / 'delivery-elo-effects-draft-20260909.json'
    path.write_text(json.dumps({'authorization': AUTHORIZATION, 'case_id': case['id'],
        'draft_saved': result, 'decisions': decisions, 'publication_performed': False}, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'receipt': str(path), 'case_id': case['id'], 'draft': result, 'review_pending': True}))

if __name__ == '__main__':
    main()
