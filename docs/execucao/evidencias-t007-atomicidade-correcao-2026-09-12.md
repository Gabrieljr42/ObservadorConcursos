# Evidência T007 — correção de atomicidade e reconciliação (2026-09-12)

## Causa comprovada

O dry-run `tpr-4391918df249356b748f6b97691e0756` carregava documentos apenas de `raw_data.tenderproof.amendments`. Nos 32 alvos esse conjunto estava vazio. O apply então enviava `raw_data.publications=[]` a `_sync_publications`; como não havia link-fallback nesse payload, o retorno era `created=[]`, e a proposta era gravada como `no_change/skipped` sem `concurso_versions`/outbox. Em paralelo, o crawler havia materializado as 32 linhas `normalized_link_fallback` pela coluna normalizada `link_edital`. Não há evidência para atribuir a persistência ao apply.

## Correção

- `apply_normalized_link_proposal` agora materializa, quando não há bytes/documentos preservados, uma referência explícita somente-leitura derivada de `link_edital`, título/edital e data do alvo, com `provenance.kind=normalized_link_fallback`, `reference_only=true` e hash compatível com `_sync_publications`.
- Se a linha fallback já existir (estado parcial), o apply reutiliza a linha e cria uma única versão `document_added` + outbox; não duplica nem transforma referência em documento lido.
- A normalização de data mantém o hash estável entre SQLite e PostgreSQL (round-trip de timezone).
- Toda a operação permanece em uma transação; exceção/concorrência faz rollback. Repetição de proposta aplicada retorna o recibo persistido.

## Reprodução isolada

Foi iniciado e removido o contêiner privado `t007-pg-review-20260912` (`postgres:17-alpine`, usuário/banco `fixture/tenderproof_acceptance`, porta loopback aleatória); nenhum serviço/piloto compartilhado foi reiniciado ou mutado.

Resultado: `tests/test_tenderproof_publication_postgres.py` — **15 passed**, incluindo criação de schema, `INSERT ... ON CONFLICT ... RETURNING`, atomicidade, retry/outbox, concorrência e rollback.

## Testes direcionados

`tests/test_publication_fallback.py` — **9 passed**:

- aplicação inicial e replay idempotente;
- fallback já persistido sem evento (reconciliação);
- conflito tardio em lote (rollback de todos os alvos);
- deduplicação e retificação posterior na mesma URL;
- reparo versionado, limitado, auditável e sem reescrever observação.

`tests/test_tenderproof_publication_post.py` — **7 passed**; PostgreSQL opt-in anterior — 15 pass.

## Gate

Implementação e evidência prontas para revisão independente. A aplicação/reparo dos 32 registros no piloto permanece bloqueada até revisão do diff, backup e proposta serializada autorizada. Nenhum evento retroativo foi inventado; a reconciliação registra `original_observed_at` e `source=normalized_link_repair` quando usada.

## Recibo de repetição — mesmo ambiente (2026-09-12)

Runtime local usado pelo executor (sem instalação global):

```text
backend/.venv/Scripts/python.exe
Python 3.12.0
pytest 9.1.1 | SQLAlchemy 2.0.39 | psycopg 3.2.6
Docker 28.1.1
```

Comandos e saídas resumidas:

```text
cd backend
.venv\Scripts\python.exe -m pytest -q tests/test_publication_fallback.py tests/test_tenderproof_publication_post.py
16 passed, 205 warnings

docker run --rm -d --name t007-pg-recheck-20260912 \
  -e POSTGRES_USER=fixture -e POSTGRES_PASSWORD=fixture \
  -e POSTGRES_DB=tenderproof_acceptance -p 127.0.0.1::5432 postgres:17-alpine
$env:TENDERPROOF_TEST_POSTGRES_URL=postgresql+psycopg://fixture:fixture@127.0.0.1:<porta>/tenderproof_acceptance
.venv\Scripts\python.exe -m pytest -q tests/test_tenderproof_publication_postgres.py
15 passed, 337 warnings
docker rm -f t007-pg-recheck-20260912
```

O container foi novo, sem volume/montagem e removido após o teste. O Python empacotado que falhou no integrador não é o runtime usado aqui; o venv do projeto contém `pytest` e os drivers necessários. Não houve alteração no piloto.

## Correção do gate pós-integração (sem piloto)

Reproduzidos em isolamento os dois defeitos reportados após a aplicação dos 32 registros:

1. `GET /tenderproof/publications/proposals/{id}` assumia `payload.run` e lançava `KeyError: 'run'` para `normalized_link_reference`/`normalized_link_repair`. `proposal_view` agora serializa esses tipos com contrato estável, `targets`/`requested_ids` e sem fingir um `TenderProofRun`.
2. `ConcursoPublicationOut` agora expõe `reference_only`. A propriedade deriva `raw_data.provenance.reference_only` e também reconhece o legado `kind=normalized_link_fallback`, preservando dados antigos; novos fallbacks persistem o marcador explícito.

Teste dirigido no mesmo venv: `tests/test_publication_fallback.py` — **11 passed**, incluindo GET HTTP da proposta e serialização da publicação. Nenhuma rota do piloto foi chamada e nenhum serviço foi reiniciado.
