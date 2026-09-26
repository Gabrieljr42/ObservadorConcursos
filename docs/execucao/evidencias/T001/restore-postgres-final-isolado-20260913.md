# Restore PostgreSQL final isolado — T001

Resultado: **DOCKER_RECONCILED_RESTORE_PASS** em `2026-09-13T07:09:23.2022328-03:00`.

- Daemon recuperado: Docker Desktop 4.41.2 / Engine 28.1.1; seis serviços do `observador-pilot` e volumes canônicos preservados.
- Dump usado: `/backups/pilot-20260913T073116707Z-postgres.dump`, 496.170 bytes; `pg_restore --list` passou.
- Isolamento: container novo `observador-final-restore-pg-20260913T051500Z`, volume novo homônimo, `--network none`, backup montado read-only; banco `restore_final_20260913`.
- Restore: `pg_restore --no-owner --exit-on-error` retornou código 0.
- Contagens restauradas: 33 concursos, 99 fontes, 180 cargos, 34 publicações, 91 versões, 95 propostas, 91 outbox, 90 notificações e zero em `push_devices`, `push_deliveries` e `push_delivery_attempts`.
- `document_review` não possui tabela PostgreSQL (0); esse estado pertence ao SQLite operacional, conforme contrato.

Não houve mutação no banco/volumes canônicos, importação de ID5, publicação de Garibaldi ou remoção de recursos. Container e volume temporários foram preservados para evidência.
