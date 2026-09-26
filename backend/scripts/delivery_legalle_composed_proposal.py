"""Prepare Garibaldi's initial composed proposal without applying it.

The case has one base edital and three later documents.  Each field change is
bound to the retification that actually proves it; the publication module
keeps all three document hashes in the proposal.
"""
import copy
import json
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import select

from app.database import SessionLocal
from app.models import Source, User
from app.tenderproof import amendment, review_cases
from app.tenderproof.continuous_store import get_continuous_store
from app.tenderproof.store import get_store

ROOT = Path('/var/lib/observador/tenderproof/product-completion')
INPUT = ROOT / 'delivery-legalle-review-20260909T224829575588Z.json'
RUN_ID = 'tp-tcj-b043232758f45dcaabd67471231c3608-1'
CASE_ID = 'drc-01fce885628b488085ea2a34fe8487b1'
AUTHORIZATION = {
    'actor_kind': 'delegated_automation',
    'human_read': False,
    'delegation_reference': 'user-attachment:6b86284b-154e-4ef6-88a1-6318513307e3/pasted-text-1.txt',
    'delegation_sha256': 'a8d5f58a652eaed76d186385e12dadf9cbc4acf71cca71d5535a1797aca059f6',
}


def _identity(run, source):
    fields = {field.field_name: field.value for field in run.fields}
    candidate = next(item for item in run.candidates if item.candidate_id == run.selected_candidate_id)
    return {
        'source_id': source.id,
        'external_id': candidate.external_id,
        'edital_numero': fields['edital_numero'],
        'orgao': fields['orgao'],
        'titulo': fields['titulo'],
        'detail_url': candidate.detail_url_observed,
    }


def _doc(case, title, identity):
    item = next(item for item in case['documents'] if (item.get('document') or item).get('title') == title)
    manifest = item.get('document') or item
    artifact = item['artifact']
    return {
        'sha256': artifact['sha256'],
        'url': artifact.get('url_final') or artifact.get('url_requested'),
        'title': manifest.get('title'),
        'kind': manifest.get('kind'),
        'identity': identity,
        'artifact': artifact,
    }, item


def _proof(item, source_url, needle):
    pages = item['pages']
    page = next((page for page in pages if needle in page.get('text', '')), None)
    if page is None:
        raise ValueError(f'trecho literal ausente: {needle!r}')
    text = page['text']
    start = text.index(needle)
    # Keep the complete sentence/row used by the decision while retaining a
    # literal substring of the revalidated page.
    snippet = text[start:start + len(needle)]
    return {'sha256': item['artifact']['sha256'], 'page': page['page_number'],
            'snippet': snippet, 'source_url': source_url}


def _updated_jobs(base_jobs):
    result = copy.deepcopy(base_jobs)
    # The first review canonicalized the table's ``até 20h`` notation to the
    # stored ``20 horas semanais`` value; retain that exact representation on
    # revalidation so a retry compares the same documented snapshot.
    for job in result:
        if isinstance(job.get('jornada'), str) and job['jornada'].startswith('até '):
            job['jornada'] = job['jornada'][4:]
    role = next((job for job in result if job.get('nome') == 'Secretário de Escola'), None)
    if role is None:
        raise ValueError('quadro-base sem Secretário de Escola')
    if role.get('jornada') != '20 horas semanais' or role.get('remuneracao') != '2682.07':
        raise ValueError('valores-base do Secretário não correspondem à página 3')
    role['jornada'] = '40 horas semanais'
    return result


def main():
    draft = json.loads(INPUT.read_text(encoding='utf-8'))
    if draft.get('publication_performed'):
        raise ValueError('recibo indica publicação; abortando')
    queue, store = get_continuous_store(), get_store()
    run = store.get_run(RUN_ID)
    if not run or run.run_id != RUN_ID:
        raise ValueError('run LEGALLE ausente')
    case = review_cases.read(queue, CASE_ID, run.owner_user_id)
    if case['run_id'] != RUN_ID:
        raise ValueError('caso não corresponde ao run')
    with SessionLocal() as db:
        source = db.scalar(select(Source).where(Source.source_type == run.source))
        user = db.get(User, run.owner_user_id)
        if not source or not user:
            raise ValueError('fonte ou usuário ausente')
        identity = _identity(run, source)
        base, base_item = _doc(case, 'Edital nº 04/2025 - Abertura e Inscrições', identity)
        classification, class_item = _doc(case, 'Retificação da Classificação Final', identity)
        schedule, schedule_item = _doc(case, 'Retificação do Cronograma', identity)
        workload, workload_item = _doc(case, 'Retificação', identity)

        # Reuse the same extraction that create_proposal revalidates, so the
        # structured previous value is not caller-supplied.
        documents = amendment._case_documents(case, queue, store, run)
        initial_fields = amendment._initial_fields(run, documents)
        base_jobs = initial_fields.get('cargos', {}).get('value')
        if not isinstance(base_jobs, list) or len(base_jobs) != 13:
            raise ValueError('quadro-base não foi extraído integralmente')
        # Match the canonical representation persisted by the earlier review
        # before using this snapshot as the proposal's ``previous`` value.
        for job in base_jobs:
            if isinstance(job.get('jornada'), str) and job['jornada'].startswith('até '):
                job['jornada'] = job['jornada'][4:]
        updated_jobs = _updated_jobs(base_jobs)

        class_snippet = _proof(class_item, classification['url'],
                               'Divulga a Retificação da Classificação Final do Processo\nSeletivo Simplificado')
        schedule_snippet = _proof(schedule_item, schedule['url'],
                                   'Realização do Sorteio Público de Desempate e Resultado do Processo\nSeletivo 22/12/25\nHomologação do Processo Seletivo 22/12/25')
        workload_snippet = _proof(workload_item, workload['url'],
                                  'Secretário de Escola CR*(2) 40h*(4) R$ 2.682,07 Ensino Médio')
        inscription_p1 = _proof(base_item, base['url'],
                               'do dia 05 de novembro de 2025 às 18 horas do dia 24 de novembro de\n2025')
        inscription_p4 = _proof(base_item, base['url'], 'até as 18 horas do último dia de inscrições')
        inscription_p12 = _proof(base_item, base['url'],
                                 'Período de inscrições e Envio dos Títulos 05/11/25 24/11/25')

        decisions = [
            {'sha256': classification['sha256'], 'page': class_snippet['page'],
             'snippet': class_snippet['snippet'], 'effect': 'no_field_change',
             'reason': 'A lista retificada altera resultados individuais; não altera os campos canônicos do concurso.',},
            {'sha256': schedule['sha256'], 'page': schedule_snippet['page'],
             'snippet': schedule_snippet['snippet'], 'effect': 'field_changes',
             'reason': 'A retificação altera o resultado final e a homologação do cronograma oficial.',
             'changes': [{'field_name': 'resultado_final_prazo', 'previous': '2025-12-17', 'new': '2025-12-22',
                          'provenance': [schedule_snippet]}]},
            {'sha256': workload['sha256'], 'page': workload_snippet['page'],
             'snippet': workload_snippet['snippet'], 'effect': 'field_changes',
             'reason': 'A retificação corrige a jornada do cargo e mantém seu vencimento básico.',
             'changes': [{'field_name': 'cargos', 'previous': base_jobs, 'new': updated_jobs,
                          'provenance': [workload_snippet]}]},
            {'sha256': base['sha256'], 'page': 1,
             'snippet': 'MUNICÍPIO DE GARIBALDI\nPROCESSO SELETIVO SIMPLIFICADO\nEDITAL Nº 04/2025',
             'effect': 'reflected_in_selected_document',
             'reason': 'O edital-base fornece a identidade, o período inicial e o quadro publicado.',},
        ]
        # A failed retry may have committed the review decision before the
        # proposal transaction was reached. Reuse that exact decision set
        # instead of turning a safe retry into a 409 or a second review.
        if case.get('decisions'):
            review = {'id': CASE_ID, 'revision_hash': case['revision_hash'],
                      'decisions': case['decisions'], 'reused': True}
        else:
            review = review_cases.approve(queue, store, run, CASE_ID, case['revision_hash'], decisions)
        if not queue.review_for_run(run).get('pending'):
            raise ValueError('o gate foi limpo antes da aplicação')

        changes = {
            'resultado_final_prazo': {
                'previous': '2025-12-17', 'new': '2025-12-22',
                'reason': 'A retificação do cronograma desloca resultado e homologação para 22/12/2025.',
                'provenance': [schedule_snippet],
            },
            'cargos': {
                'previous': base_jobs, 'new': updated_jobs,
                'reason': 'A retificação de 06/11/2025 corrige Secretário de Escola para 40 horas, mantendo R$ 2.682,07.',
                'provenance': [workload_snippet],
            },
        }
        events = [
            {'name': 'Resultado final', 'date': '2025-12-22', 'precision': 'day', 'timezone': None,
             'provenance': [schedule_snippet]},
            {'name': 'Homologação', 'date': '2025-12-22', 'precision': 'day', 'timezone': None,
             'provenance': [schedule_snippet]},
            {'name': 'Inscrições e envio dos títulos/experiência profissional',
             'date': '2025-11-05', 'end_date': '2025-11-24', 'end_time': '18:00',
             'precision': 'local_time', 'timezone': 'America/Sao_Paulo',
             'provenance': [inscription_p1, inscription_p4, inscription_p12]},
        ]
        amendment_documents = [classification, schedule, workload]
        proposal = amendment.create_proposal(
            db, concurso_id=None, source_id=source.id, user=user, base_document=base,
            amendment_document=workload, amendment_documents=amendment_documents,
            changes=changes,
            reason='Publicação inicial composta pelo edital-base de Garibaldi e pelas retificações de cronograma, jornada e classificação.',
            authorization=AUTHORIZATION, events=events, run=run, queue=queue, store=store,
            review_case_id=CASE_ID, review_hash=case['revision_hash'])
        if proposal['state'] != 'proposed' or proposal['concurso_id'] is not None:
            raise ValueError('proposta não ficou revisável sem concurso canônico')
        stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
        receipt = ROOT / f'delivery-legalle-composed-proposed-{stamp}.json'
        receipt.write_text(json.dumps({'run_id': RUN_ID, 'case_id': CASE_ID,
            'review': review, 'proposal': proposal, 'publication_performed': False},
            ensure_ascii=False, indent=2, default=str), encoding='utf-8')
        print(json.dumps({'receipt': str(receipt), 'proposal_id': proposal['id'],
                          'proposal_hash': proposal['proposal_hash'], 'state': proposal['state'],
                          'concurso_id': proposal['concurso_id'],
                          'initial_fields': sorted((proposal.get('initial_fields') or {}).keys()),
                          'changed_fields': sorted(proposal.get('changes', {}).keys())}, ensure_ascii=False))


if __name__ == '__main__':
    main()
