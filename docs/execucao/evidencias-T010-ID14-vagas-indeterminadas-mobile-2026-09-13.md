# T010/ID14 — Quantidade de vagas imediatas indeterminada

## Correção

`vagas_imediatas` agora é tratado como campo potencialmente ausente/nulo no contrato mobile. O formatter e o card nunca interpolam `null`, `undefined` ou `NaN`: exibem `Quantidade de vagas imediatas: ainda não confirmada`. Zero inteiro permanece visível como `0 vaga(s) imediata(s)`. Cotas PPP/AC/PcD, cadastro de reserva, remuneração e jornada continuam independentes.

O caso ID14 cobre duas funções de Professor de Física, vagas nulas/indefinidas, jornada nula e unidade/etapa preservadas; também mantém regressões ID8 PPP e benefícios.

## Validação

- `tests/cargo-formatting.test.cjs`: 8/8.
- `npx tsc --noEmit`: passou.
- `node --test tests/*.test.cjs`: 46/46.
- `npm run build`: export web passou.

Sem backend, dados ou deploy alterados. Revisão independente solicitada antes de publicação.
