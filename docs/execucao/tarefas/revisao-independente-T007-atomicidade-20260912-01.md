# Revisão independente T007 — atomicidade e reconciliação

Data: 2026-09-12. **ACEITO — gate de código/reparo versionado.**

A causa está comprovada: `raw_data.tenderproof.amendments` vazio produzia `documents=[]`; o apply antigo passava `publications=[]` e registrava `no_change`, enquanto o crawler já havia materializado `link_edital`. A correção gera referência explícita com `source=concurso.link_edital`, `normalized_link_fallback` e `reference_only`, usando o mesmo hash/date normalization do crawler. Fallback preexistente é reutilizado; uma única `document_added` e `PublicationOutbox` são criados. Estado parcial, baseline concorrente, rollback de lote, replay idempotente e retificação posterior por mesma URL estão cobertos pelos testes/evidência; não há evento retroativo.

A suíte própria não pôde ser executada neste host: Python/pytest ausentes e Docker bloqueado por permissão. A evidência entregue registra SQLite 9, PostgreSQL isolado 15 e POST 7 pass. Gate de reparo: backup atual, proposta/autorizações serializadas e aplicação somente após integração.
