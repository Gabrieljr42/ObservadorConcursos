# Revisão independente — correção mobile ID14

Data: 2026-09-13. Read-only; sem deploy ou mutação operacional.

## Decisão: ACEITA para deploy; desbloqueia o gate de apresentação da proposta ID14

`CargoDetalhado.vagas_imediatas` agora aceita `number | null`; `vagasImediatasCargo` rejeita `null`, `undefined`, `NaN`, infinitos, fracionários e negativos, preservando zero real. `textoVagasImediatas` produz “Quantidade de vagas imediatas: ainda não confirmada” quando indeterminado. `resumoCargo` usa esse formatter; jornada nula continua “ainda não confirmada”; remuneração mantém moeda e observação de unidade hora/etapa. Cotas AC/PcD/PPP continuam independentes, e CR/observação não é convertido em vagas imediatas.

`ConcursoCard` soma apenas números válidos, preserva zero e mostra mensagem explícita se qualquer cargo tiver quantidade desconhecida; não gera `null`, `undefined` ou `NaN`.

Checks: `node --test mobile/tests/cargo-formatting.test.cjs mobile/tests/search-filters.test.cjs mobile/tests/official-links.test.cjs mobile/tests/amendment-effects.test.cjs mobile/tests/registration-status.test.cjs` — **21/21 PASS**, incluindo o novo caso ID14 nulo/undefined/NaN e zero. `npx tsc --noEmit` — **PASS**. Build Expo não foi executado por produzir artefatos, fora do escopo read-only; permanece verificação operacional separada.

Conclusão: correção suficiente para deploy; o bloqueio anterior de apresentação (“null vaga(s) imediata(s)”) foi eliminado. Isso não executa nem autoriza automaticamente approve/apply; o gate backend ID14 deve manter suas condições próprias.
