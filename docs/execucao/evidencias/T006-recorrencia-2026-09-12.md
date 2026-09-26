# Evidência T006 — recorrência read-only

Observação: 2026-09-12T23:54:52.8250128Z (UTC), sem disparar ciclo/tarefa.

## API

- Login autenticado: HTTP 200.
- `GET http://127.0.0.1:18000/tenderproof/continuous/status`: HTTP 200; `operationally_enabled=true`, `operator_authorized=true`, `publication_enabled=false`; 89 fontes habilitadas; 282 ciclos retornados; 63 ciclos em estado ativo ou pendente (`active`, `running`, `queued`, `retry`, `recover`); ciclos históricos parciais/sucedidos presentes.
- `GET http://127.0.0.1:18000/tenderproof/continuous/metrics`: HTTP 200; `measured_at=1789257296.80688`; `jobs_by_status={deferred:11913, failed:1920, queued:5727, retry:862, running:1, succeeded:5473}`, `retry_attempts=4237`, `completed_cycles_by_source=89`.
- Health já conferido: `GET /health` HTTP 200 (`status=ok`, `env=local-pilot`).

## O que fica comprovado e limites

O estado persistido da recorrência, ciclos ativos/histórico e fila de jobs estão vivos e consultáveis; publicação continua desabilitada. A evidência anterior de status vivo (`evidencias-status-2026-09-12.md`) registrou API, worker, scheduler, PostgreSQL e Redis ativos/saudáveis. Estas consultas não provam, sozinhas, identidade de processo do worker/scheduler nem push nativo; push/dispositivo permanece dependência separada de T009.
