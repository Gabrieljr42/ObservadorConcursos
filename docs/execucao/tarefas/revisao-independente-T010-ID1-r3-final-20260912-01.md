# Revisão independente T010/ID1 — gate código r3 final

Status: ACEITA (com risco P2 registrado)

- Suíte direcionada após a correção: `backend\\.venv\\Scripts\\python.exe -m pytest -q tests/test_access_birigui_jobs.py tests/test_reviewed_run_import.py tests/test_tenderproof_publication.py` → 20/20 PASS. O teste ID1 agora percorre envelope → `import_reviewed_run` → `store.get_run` → `_revalidate` → `create_proposal`, preserva `units` e demonstra baseline `cargos=None` contra payload flat não vazio; portanto há diferença material, não apenas `eligible_fields`.
- Extração real de `id1.pdf`: SHA `de7a554e…31087`, 21 páginas; `extract_fields` retorna Professor Auxiliar, 10 (9 AC/1 PcD), R$30,53 BRL/hora-aula e jornada/requisitos. SHA/estrutura alterados falham fechado; contrato mobile flat: 3/3 e `npx tsc --noEmit` PASS.
- PostgreSQL: `tests/test_tenderproof_publication_postgres.py` → 15 skipped, pois não existe URL descartável explícita; cleanup PG permanece não exercitado neste ambiente.

Risco P2: `_run_id` inclui `Evidence.evidence_id`; regenerar o mesmo envelope com UUIDs novos muda o run_id, embora retry do envelope byte-a-byte seja idempotente. Além disso, o envelope possui um único `title`, copiado para candidate e document; não há conflito no ID1, mas títulos históricos distintos não são representáveis.

Gate: ACEITA; deploy pode prosseguir. Recomenda-se normalizar IDs de evidência ou documentar que a idempotência exige envelope imutável, e repetir a suíte PG em fixture isolada.
