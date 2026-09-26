# Relatório r3 — matriz atual reconciliada das 99 fontes

Revisão offline/read-only. Baselines preservados: `docs/entrega-fontes-atual.csv`, `docs/tenderproof-product-status.json` e T005. A versão r3 é a atual:

- `matriz-fontes-99-reconciliada-r3-20260912.csv`: 99 linhas, `numero` como ID da fonte, ponteiros aos baselines e snapshots explícitos: concursos 33, fontes 32, cargos_arrays 124, publicações 34, versões 84, outbox 84, notificações 83 e propostas 86.
- `matriz-fontes-99-reconciliada-r3-20260912.json`: contrato, enums, overlays e dimensões de cobertura.

Overlays preservados: fonte 19→concurso 1 (applied/UI, versão 82), 17→6 (83), 22→7 (84); fonte 34→17 **DEVOLVIDO r2**. T010 5/8/14/16 permanecem insuficientes (fontes 38/45/76/18); 15 permanece mismatch (fonte 6). ID17/T011 não é parser-ready até novo aceite; ID21 continua `DO_NOT_RETRY`.

A correção separa explicitamente outbox (84) de notificações (83); não há equivalência implícita. Validação: 99 linhas, 99 números/fontes únicos e enums consistentes. Nenhuma integração certificada foi promovida. Solicita-se revisão independente r3.

