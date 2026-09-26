# Revisão independente — matriz de fontes r3 final

Data: 2026-09-12

## Gate r3 — ACEITA

CSV/JSON r3 são equivalentes no recorte validado: 99 linhas, 99 `numero` únicos, 99 fontes únicas, enums consistentes e zero divergência dos campos históricos contra `docs/entrega-fontes-atual.csv`. Cada linha separa corretamente o snapshot atual: 33 concursos, 32 fontes, 124 cargos_arrays, 34 publicações, 84 versões, 84 outbox, 83 notificações e 86 propostas; não há linha residual com outbox 83. Overlays confirmados: fonte 19→concurso 1/v82, 17→6/v83, 22→7/v84; 34→17 DEVOLVIDO r2; T010 5/8/14/16 insuficientes e 15 mismatch; T011 18/20/22–25 insuficientes, 21 DO_NOT_RETRY e 17 não parser-ready.

## Baselines/liberação — ACEITA

Baselines `entrega-fontes-atual.csv` e `tenderproof-product-status.json` permanecem preservados e apenas referenciados; `authoritative:false`, overlays de concurso não promovem integração source-wide e T007 `reference_only` continua delimitado. **Liberado apontar os documentos centrais à matriz r3.**
