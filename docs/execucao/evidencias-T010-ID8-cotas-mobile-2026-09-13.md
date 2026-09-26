# T010/ID8 — Cotas imediatas no detalhe do cargo

## Contrato confirmado

O envelope real usa `vagas_ampla_concorrencia`, `vagas_pcd` e `vagas_ppp`; o teste backend de ID8 confirma Guarda Civil Municipal com 9 imediatas: AC 6, PcD 1 e PPP 2, além de 11 em cadastro de reserva.

## Ajuste mobile

`src/utils/cargos.ts` agora centraliza `cotasCargo`, incluindo PPP e demais categorias somente quando o número é positivo e finito. A linha humana `Distribuição das vagas imediatas` mantém AC/PcD e passa a mostrar PPP 2. Zero, ausente e legado inválido são omitidos. O total imediato e o cadastro de reserva permanecem separados; CR 11 não é agregado às cotas.

## Validação

- `tests/cargo-formatting.test.cjs`: ID8, soma/CR, múltiplas categorias, zero/ausente/legado e regressões de benefícios; 7/7.
- `npx tsc --noEmit`: passou.
- `node --test tests/*.test.cjs`: 45/45.
- `npm run build`: export web passou.

Sem backend, dados ou deploy alterados. Revisão independente solicitada antes de publicação.
