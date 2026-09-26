# Evidência T006 — backup e restauração isolada

Data: 2026-09-12. Execução sequencial no projeto `observador-pilot`, preservando volumes e sem tocar outros projetos.

- Escritores `api`, `worker` e `scheduler` foram parados antes da cópia.
- Backup criado em `/backups/pilot-20260912T202500000Z-operational`; o bundle contém 11.027 arquivos e declara `canonical_database_included=false`.
- `operational_backup verify` passou no bundle de origem: `files=11027`.
- Restauração criada em `/backups/t006-restore-isolated-20260912T202500000Z`; `operational_backup restore` passou: `files=11027`.
- Validação independente comparou tamanho e SHA-256 dos 11.027 arquivos restaurados contra o manifesto da origem: `bad=[]`.
- `PRAGMA integrity_check` passou em `operational.sqlite3` e `continuous.sqlite3` restaurados (`ok`).
- O destino restaurado não recebe `backup-manifest.json` pela implementação atual; por isso a verificação final foi feita contra o manifesto da origem, arquivo a arquivo. Esse comportamento deve ser tratado como melhoria de ferramenta, não como falha de integridade desta restauração.
- `api`, `worker` e `scheduler` foram religados ao final; PostgreSQL/Redis permaneceram no mesmo volume e saudáveis.
- Após o religamento, `GET http://127.0.0.1:18000/health` respondeu HTTP 200 com `status=ok`, `app=Observador de Concursos`, `env=local-pilot`.
- PostgreSQL também foi validado: dump atual em `/backups/t006-postgres-20260912.dump` foi restaurado no banco novo `t006_restore_iso_20260912` com `pg_restore --no-owner --exit-on-error`. Contagens restaurado/canônico coincidiram: concursos 32, fontes 99, publicações 0, versões 48, notificações 47, alertas 1, favoritos 1, propostas 65 e outbox 48. O banco canônico não foi sobrescrito; o banco isolado e o dump foram preservados para inspeção.
