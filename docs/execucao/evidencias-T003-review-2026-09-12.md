# T003 — revisão de contrato visual e testes (2026-09-12)

## Reconciliação

O código de `mobile/` já implementa os critérios declarados: `formatPublishedTemporal` preserva datas de calendário e só exibe horário quando a precisão é `instant`; horários sem offset exibem `fuso não informado`; eventos de retificação mostram anterior/vigente com rótulos de domínio; `resumoCargo` separa vagas imediatas/cadastro, remuneração e jornada; a busca rotula a contagem como `Seleções`; Salvos usa quatro leituras limitadas para atravessar o lock inicial do SQLite.

Não encontrei defeito interno pequeno pendente nesta revisão. Os testes direcionados passaram:

```text
npx tsc --noEmit                                      PASS
node --test tests/amendment-effects.test.cjs tests/cargo-formatting.test.cjs tests/search-filters.test.cjs tests/official-links.test.cjs tests/registration-status.test.cjs  PASS (16/16)
```

## READY_FOR_REVIEW — gate visual real

O integrador precisa, no build implantado, abrir `/inicio`, confirmar a contagem `Seleções`, abrir um registro com retificação e conferir: rótulos de domínio; períodos date-only sem hora inventada; eventos com hora/fuso explícitos ou `fuso não informado`; bloco `Cargos e requisitos` sem `undefined`; e retorno após reload. Para o registro 33/Garibaldi, conferir os 13 cargos e as mudanças documentadas de jornada/remuneração. Registrar URL/origem, horário, screenshot/recibo e qualquer divergência; não tratar GET/API isolado como aceite visual.
