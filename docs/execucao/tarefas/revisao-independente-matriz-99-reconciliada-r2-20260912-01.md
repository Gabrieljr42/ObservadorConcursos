# Revisão independente — matriz reconciliada das 99 fontes r2

Data: 2026-09-12

## Gate matriz/estado final — DEVOLVIDO

As validações estruturais passam: CSV tem 99 linhas, `numero`/fonte únicos e os enums/somas em `matriz-cobertura-99-reconciliada-20260912.json` batem. Porém o overlay final está obsoleto: em `reconciled_overlays.T010`, `targeted_parser:[1,6]` e `reviewed_run_applied:[16]` devem ser substituídos por aplicação comprovada de 1/6/7 (versões 82/83/84, UI/GET e replays) e insuficientes/no_change 5/8/14/16; 15 continua mismatch/do_not_dispatch. `T011.targeted_parser_ready:[17]` deve virar DEVOLVIDO/retorno para correção; 18/20/22–25 insuficientes e 21 DO_NOT_RETRY permanecem. `numero` é número da fonte, não concurso: CSV 19=access_open→concurso 1, 17=imeso_open→6, 22=abcp_open→7, 34=contemax_open→17.

## Gate arquivos canônicos — DEVOLVIDO

`entrega-fontes-atual.csv` está reconciliado apenas como inventário/source-level (99 linhas; não incorpora os novos receipts por concurso). `tenderproof-product-status.json` também não representa o estado atual: mantém delivery 32/31, 48 versões, 47 notificações e 99 cargos, enquanto receipts finais registram 33/32, 84 versões, 83 notificações e 124 cargos. Preservar esses snapshots como históricos, mas não os chamar de estado atual; gerar atualização canônica após corrigir os overlays acima. T007 está corretamente limitado: 30 fallback `reference_only` + 4 documentos integrais não equivalem a integração source-wide.
