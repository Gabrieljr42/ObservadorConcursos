"""Build the concrete amendment input from the prepared case; no publication."""
import json
import re
from pathlib import Path
from app.database import SessionLocal
from app.models import Concurso
from app.versioning import jsonable

ROOT = Path('/var/lib/observador/tenderproof/product-completion')
RECEIPT = ROOT / 'delivery-pedrinhas-review-20260909T202819850380Z.json'
BASE = 'cb0848ea34d18877d37dd46059306ba6212b9b1c56828e33228fda2c609f84f3'
AMENDED = 'abf214200dfba8427d9597ac905e5b1b6a3e7920f03b642dcdcbbd22060c0bbd'


def main():
    prepared = json.loads(RECEIPT.read_text(encoding='utf-8'))
    case = prepared['case']
    documents = {d['artifact']['sha256']: d for d in case['documents']}
    assert {BASE, AMENDED}.issubset(documents)
    text = documents[AMENDED]['pages'][0]['text']
    def proof(article):
        match = re.search(r'Art\.0?' + str(article) + r'.*?(?=Art\.0?' + str(article + 1) + r')', text, re.S)
        if not match:
            raise ValueError('Artigo esperado ausente na página preservada')
        return {'sha256': AMENDED, 'page': 1, 'snippet': match[0].strip(),
                'source_url': documents[AMENDED]['artifact']['url_final']}
    with SessionLocal() as db:
        contest = db.get(Concurso, 3)
        assert contest.external_id == '129' and contest.edital_numero == '01/2026'
        identity = {'source_id': contest.source_id, 'external_id': contest.external_id, 'edital_numero': contest.edital_numero}
        def document(sha):
            d = documents[sha]
            return {'sha256': sha, 'url': d['artifact']['url_final'], 'title': d['document']['title'],
                    'identity': identity, 'artifact': d['artifact']}
        values = {'inscricao_inicio': '2026-09-09T10:00:00-03:00',
                  'inscricao_fim': '2026-09-11T10:00:00-03:00', 'prova_data': '2026-09-27'}
        current = {'start': values['inscricao_inicio'], 'end': values['inscricao_fim'],
                   'precision': 'instant', 'timezone': 'America/Sao_Paulo', 'provenance': [proof(1)]}
        payload = {
            'concurso_id': contest.id, 'run_id': prepared['run_id'],
            'case_id': case['id'], 'review_hash': case['revision_hash'],
            'base_document': document(BASE), 'amendment_document': document(AMENDED),
            'reason': 'Edital de 08/09/2026 reabre inscrições de Pedrinhas Paulista e altera a data da prova objetiva.',
            'authorization': {'actor_kind': 'delegated_automation', 'human_read': False,
                'delegation_reference': 'user-attachment:6b86284b-154e-4ef6-88a1-6318513307e3/pasted-text-1.txt',
                'delegation_sha256': 'a8d5f58a652eaed76d186385e12dadf9cbc4acf71cca71d5535a1797aca059f6'},
            'changes': {name: {'previous': jsonable(getattr(contest,name)), 'new': value,
                'reason': 'Novo prazo expresso no ato posterior de 08/09/2026.',
                'provenance': [proof(4 if name == 'prova_data' else 1)]} for name,value in values.items()},
            'periods': {'original': {'start': '2026-08-21', 'end': '2026-09-04', 'precision': 'day', 'timezone': None},
                        'current': current, 'reopenings': [current]},
            'events': [
                {'name': 'Pagamento da inscrição', 'date': '2026-09-11', 'precision': 'day', 'timezone': None, 'provenance': [proof(2)]},
                {'name': 'Homologação das inscrições', 'date': '2026-09-18', 'precision': 'day', 'timezone': None, 'provenance': [proof(3)]},
                {'name': 'Prova objetiva', 'date': '2026-09-27', 'start_time': '08:00', 'end_time': '11:00',
                 'precision': 'local_time', 'timezone': None, 'provenance': [proof(4)]},
                {'name': 'Gabarito', 'date': '2026-09-28', 'start_time': '18:00', 'time_qualifier': 'a partir de',
                 'precision': 'local_time', 'timezone': None, 'provenance': [proof(5)]},
            ],
        }
    path = ROOT / 'delivery-pedrinhas-input-20260909.json'
    if path.exists():
        raise ValueError('Input existente; não sobrescrever pacote já preparado')
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'input': str(path), 'case_id': case['id'], 'changes': values, 'events': len(payload['events'])}, ensure_ascii=False))


if __name__ == '__main__':
    main()
