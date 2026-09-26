# Revisão independente T010/ID1 — gate código r3

Status: DEVOLVIDA

## Evidências

- `backend\\.venv\\Scripts\\python.exe -m pytest -q tests/test_access_birigui_jobs.py tests/test_reviewed_run_import.py tests/test_tenderproof_publication.py`: 15 testes passaram.
- `backend\\.venv\\Scripts\\python.exe -m pytest -q tests/test_tenderproof_publication_postgres.py`: 15 testes ignorados; não há `TENDERPROOF_TEST_POSTGRES_URL` de PostgreSQL descartável explícito, portanto cleanup PG não foi exercitado.
- Extração local do `docs/execucao/evidencias/T010/id1.pdf` reproduziu SHA `de7a...31087`, 21 páginas e `extract_fields` retornando `cargos` flat com 10 (9 AC/1 PcD), R$30,53/hora-aula, jornada/requisitos. Comparação contra `T010-reviewed-run-id1.json` confirmou valores e cinco snippets verbatim (inclusive o texto extraído com `�`).
- Parser falha fechado no SHA e em alteração estrutural; o contrato flat foi confirmado por `mobile/tests/cargo-formatting.test.cjs` (3/3) e `npx tsc --noEmit`.

## Bloqueio P1

`tests/test_tenderproof_publication.py::test_access_birigui_reviewed_run_revalidates_cargos_and_material_diff` não prova “diff material real”: cria a proposta e só verifica `eligible_fields`/payload `proposed`; não executa `approve_proposal`/`apply` nem afirma `result.diff` contendo `cargos`/mudança. O nome do teste promete esse gate, mas a asserção pode passar com campo elegível sem alteração canônica aplicada.

Gate: DEVOLVIDA. Reparo: adicionar asserção de baseline distinta e fluxo approve/apply isolado, verificando diff material, versão/outbox (e executar a variante PostgreSQL quando fixture estiver disponível).
