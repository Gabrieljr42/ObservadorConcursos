# Revisão independente T005 r4 — run `tp-reviewed-afd39853…`

Data: 2026-09-13. Read-only; sem importação/deploy/piloto.

## Gate import + proposta canônica — BLOQUEIA

A nova evidência corrige o escopo: store descartável, basename sob `artifact_dir`, catálogo com `cargos=null`, datas iguais e prova/taxa não publicáveis; `_revalidate→create_proposal` reporta `eligible_fields=["cargos"]`, baseline null, `apply=false`. SHA/bytes do PDF (`a5a7ff…ef5a2`, 429261), 7 microáreas e valores canônicos conferem. `pytest` dirigido: **39 passed**.

Há, contudo, perda no envelope persistido `T005-concurso32-reviewed-run-owner1.json`: o campo `cargos.evidence` contém apenas 3 itens, todos do cargo 7, enquanto as derivações r2 preservam 21 itens (3 por microárea). Assim, o payload usado no import/proposta não comprova individualmente as sete linhas, apesar de a derivação auxiliar fazê-lo. Regenerar o envelope/run preservando as 21 evidências e repetir hash, import dry-run e proposta isolada. API/deploy pode permanecer liberada; import/proposta canônica não.
