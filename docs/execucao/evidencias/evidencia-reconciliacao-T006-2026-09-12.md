# Reconciliação operacional T006 — 2026-09-12

## Consultas read-only atuais

- `GET http://127.0.0.1:18000/health`: HTTP 200, `status=ok`, `env=local-pilot`.
- Login autenticado e `GET /sync/checkpoint`: HTTP 200; leitura corrente observou 33 concursos, 32 fontes, 113 arrays de cargos, 1 alerta e 0 favoritos. Nenhuma escrita foi feita.
- `GET /tenderproof/continuous/status`: HTTP 200; `operationally_enabled=true`, `operator_authorized=true`, `publication_enabled=false`; fontes habilitadas e ciclos ativos/histórico presentes.

## Evidências reconciliadas

- Backup/restauração: 11.027 arquivos comparados por tamanho/SHA-256 (`bad=[]`), dois SQLite com `integrity_check=ok`, PostgreSQL restaurado em `t006_restore_iso_20260912` com contagens coincidentes; serviço religado e health 200. Fonte: `evidencias-backup-restore-2026-09-12.md`.
- Recorrência: `T006-recorrencia-2026-09-12.md` registra consultas atuais a `continuous/status` e `continuous/metrics` (HTTP 200), 89 fontes habilitadas, ciclos ativos/histórico e jobs vivos; `evidencias-status-2026-09-12.md` registra worker/scheduler ativos e saudáveis; publicação documental permaneceu desabilitada. O antigo nome `t006-recurrence-push-20260912.json` não é usado como artefato presente.
- Offline/UI/sincronização: T008 foi aceita operacionalmente, cobrindo alerta offline→false, retry após API retornar, reload/reopen, favorito salvar/remover, vazio legítimo, owner/isolation e preservação de preferências.
- Critério de reversibilidade: favorito/alerta de teste foram removidos pelo fluxo normal, com servidor e checkpoint confirmando ausência; preferência real não foi alterada.

## Decisão

**T006: PARCIALMENTE COBERTA / PRONTA PARA REVISÃO INDEPENDENTE**, não aceite integrado ainda. Não há pendência operacional de backup, persistência, recorrência ou offline no piloto. Bloqueios externos: dispositivo/emulador e transporte push nativo indisponíveis. Pendência interna separada: implementar/configurar registro de token e endpoint push nativo e então testar no dispositivo/emulador. Nenhum push externo foi enviado.
