# Revisão independente — suporte mobile `vagas_ppp`

Data: 2026-09-13

## Gate código/UI — ACEITA

`CargoDetalhado.vagas_ppp` e o payload flat usam a chave real `vagas_ppp`; `cotasCargo` rotula humanamente `PPP`, aceita somente números finitos positivos e mantém AC/PcD e demais categorias. Zero, ausente, negativo, `NaN`/infinito e legado não numérico são omitidos. `resumoCargo` mostra 9 vagas imediatas e a distribuição `Ampla concorrência: 6; PcD: 1; PPP: 2`, sem somar CR; `vagas_cadastro_reserva=11` permanece separado. Benefícios continuam calculados por cargo, sem mistura.

## Evidência/liberação — ACEITA

- Testes dirigidos de quotas/cargo/benefícios: 8/8 PASS.
- Suíte mobile: 45/45 PASS.
- `npx tsc --noEmit`: PASS.
- `npm run build` (Expo web, 23 rotas): PASS.

**Libero deploy.**
