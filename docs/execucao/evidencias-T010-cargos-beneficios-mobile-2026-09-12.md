# T010/ID7 — Benefícios dos cargos no mobile

## Antes

`/concurso/[id]` renderizava `resumoCargo(cargo)`, mas não apresentava `cargo.beneficios`; por isso a API podia persistir `['auxílio alimentação R$ 680,00', 'vale-transporte']` sem qualquer representação na tela.

## Depois

Cada cargo com array não vazio mostra a seção acessível `Benefícios:` e uma linha por benefício, preservando acentos, valores e ordem. Arrays vazios, ausentes ou payloads legados inválidos são omitidos sem JSON bruto, `undefined` ou erro. Cargos múltiplos são processados independentemente. Native e backend não foram alterados.

## Evidência automatizada

- `mobile/tests/cargo-formatting.test.cjs`: casos de array UTF-8, vazio, legado inválido e múltiplos cargos; 5/5 passando.
- `npx tsc --noEmit`: passou.
- `node --test tests/*.test.cjs`: 43/43 passando.
- `npm run build`: export web passou.

Revisão independente solicitada antes de deploy.
