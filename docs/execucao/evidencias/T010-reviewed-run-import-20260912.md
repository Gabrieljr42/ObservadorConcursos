# T010 ID1 — importação versionada do reviewed run

Escopo desta entrega: somente preparar o caminho local para T010/ID1. Nenhum
payload de T010/T011 foi importado, nenhum POST foi feito e o piloto não foi
consultado ou alterado.

## Contrato `tenderproof.reviewed-run.v1`

O envelope exige `source`, `concurso_id`, `external_id`, título/URL, artefato
com SHA-256/tamanho e exatamente uma fonte de bytes (`content_path` ou
`content_base64`). Cada campo exige estado comprovado implicitamente
`SUPPORTED`, ao menos uma `Evidence` com SHA/página/trecho/método. `cargos`
deve ser lista canônica; unidades ficam dentro do valor (por exemplo
`carga_horaria`/`unidade_temporal`). `pending_fields` deve ser lista vazia e
`reference_only=true`; campos pendentes, inferências, duplicatas e bytes
incompatíveis são rejeitados antes de qualquer escrita.

O envelope exige `owner_user_id` positivo, que será usado pelo endpoint normal
para autorizar a proposta. `units` é preservado em cada `ExtractedField`, sem
inferência ou descarte.

`import_reviewed_run(..., dry_run=True)` valida e retorna o `run_id`
determinístico, sem escrita. Com `dry_run=False`, grava o artefato pelo
`TenderProofStore.commit_run_artifact`, que reivindica run e `artifact_id` sob
o mesmo lock transacional; repetição é idempotente e conteúdo/SHA diferente
para o mesmo ID provoca conflito forte. O resultado é um
`TenderProofRun` normal, portanto a proposta posterior usa o endpoint normal;
não há SQL ad hoc nem escrita no catálogo.

CLI operável no container (a partir de `backend/`):

`python scripts/import_reviewed_run.py envelope.json` (dry-run padrão)  
`python scripts/import_reviewed_run.py envelope.json --artifact /path/doc.pdf --apply`

## Recibo

Ambiente: `backend/.venv/Scripts/python.exe`.  
Comando: `python -m pytest -q tests/test_reviewed_run_import.py tests/test_tenderproof_publication.py`  
Resultado: **18 passed** (SQLite isolado; inclui dry-run, aplicação, repetição,
conflito de run e `artifact_id`, cargos/unidades, rejeição de pending e falha
de SHA sem persistência).

O teste PostgreSQL opt-in (`TENDERPROOF_TEST_POSTGRES_URL`) não foi executado:
nenhuma URL descartável explícita estava configurada. O importador não toca
PostgreSQL; a proposta normal existente mantém seus testes PostgreSQL isolados.

## Fechamento do bloqueio documental ID1

`fields.extract_fields` agora chama `access_birigui_jobs` somente para
`access_open/183` e o SHA `de7a...1087`. A página 2 é exigida e deve conter,
verbatim, cargo, requisito, jornada, `R$ 30,53 hora-aula` e a contagem `09 01
10`; qualquer SHA/estrutura diferente retorna `FAILED`. O valor publicado usa
o contrato flat: `vagas_imediatas=10`, `vagas_ampla_concorrencia=9`,
`vagas_pcd=1`, `cadastro_reserva=null`, `remuneracao="30.53"`, `moeda="BRL"`,
`remuneracao_observacao="por hora-aula"`, jornada e requisitos.

Teste ponta a ponta isolado confirmou `extract_fields → _revalidate →
import_reviewed_run → store.get_run → create_proposal`: `cargos` é elegível,
unidades sobrevivem ao round-trip e persistem no payload flat da proposta,
com baseline `cargos=null`; remuneração genérica/prova continuam bloqueadas
por escopo. O extrator também falha fechado para página com `error` ou
`truncated`, e unidades participam do `run_id` determinístico.
