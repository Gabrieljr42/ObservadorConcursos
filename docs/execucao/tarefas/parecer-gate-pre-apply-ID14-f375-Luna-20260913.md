# Gate final pré-apply ID14 — proposta `tpp-c3f5d96741ac903d3c70469a4af3972a`

Data: 2026-09-13. Revisão read-only; nenhum approve/apply executado.

## Decisão: BLOQUEIA approve+apply exclusivo

O gate está tecnicamente delimitado: run `tp-reviewed-f3755a775f9b16a6a1ca2aeb5b0ea45c`, estado `proposed`, baseline `cargos=null`, `eligible_fields=[cargos]`, exatamente duas funções PF, sem identity/inscrição/prova; contagens 93 propostas, 89 versões, 89 outbox e 88 notificações. SHA/bytes do artefato conferem. Os cargos têm vagas/jornada nulas, cadastro-reserva apenas textual e remuneração por hora/etapa com observação explícita “não é mensal”.

O bloqueio é de apresentação canônica: `mobile/src/utils/cargos.ts` monta `${cargo.vagas_imediatas} vaga(s) imediata(s)` sem tratar `null`, portanto o payload aprovado exibiria literalmente **“null vaga(s) imediata(s)”**. A observação de cadastro reserva esclarece a ausência de quantidade, e jornada nula vira “ainda não confirmada”; remuneração + observação não mensal é segura. Contudo, o card de vagas continua enganoso. A suíte existente `node --test mobile/tests/cargo-formatting.test.cjs` passa 7/7, mas não cobre `vagas_imediatas=null`.

Próximo passo exato: corrigir/testar a formatação de vagas nulas para “quantidade de oportunidades não informada” (sem converter para zero), repetir validação visual/automatizada e só então reabrir este gate. Nenhuma mutação operacional está autorizada.
