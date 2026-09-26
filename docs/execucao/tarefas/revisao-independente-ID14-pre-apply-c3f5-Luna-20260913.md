# Revisão independente — gate final ID14

**Decisão: LIBERA condicionalmente approve+apply exclusivo, somente após aceite do web deploy.**

O run `tp-reviewed-f3755a775f9b16a6a1ca2aeb5b0ea45c` e a proposta `tpp-c3f5d96741ac903d3c70469a4af3972a` estão `proposed`, com owner 1, hash/bytes do artefato conferidos, `eligible_fields=[cargos]`, baseline `cargos=null`, e nenhum campo fora de cargos. O envelope contém exatamente os dois papéis PF, evidências dos itens 2.2/2.4/3.2/3.3, vagas imediatas e jornada nulas, observação textual de cadastro-reserva e remuneração por hora/etapa explicitamente não mensal; não inventa quantidade, salário mensal ou emprego. Contagens registradas: 93 propostas, 89 versões, 89 outbox, 88 notificações.

A correção mobile preserva CR separado, renderiza vagas desconhecidas honestamente, mantém jornada nula e unidades; suíte dirigida **21/21 PASS** e `npx tsc --noEmit` PASS. Nenhuma mutação foi feita. Após recibo de web deploy aceito, aplicar apenas esta proposta com CAS/hash/owner e verificar uma única versão/outbox/notificação.
