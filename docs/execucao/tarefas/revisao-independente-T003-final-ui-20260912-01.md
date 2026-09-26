# Revisão independente T003 — gate UI final

Status: ACEITA.

- Critério em `tarefas/T003.md` é explícito: a busca deve exibir a contagem rotulada como “Seleções”. A evidência implantada confirma `/busca`: `RESULTADOS ENCONTRADOS` e `33 Seleções`, além de `/concurso/33` com 13 cargos sem `undefined`, temporalidade, retificações, histórico e reload preservados conforme o recibo do coordenador.
- `mobile`: `npx tsc --noEmit` PASS; suíte declarada de retificação/formatação/filtros/links/status: 16/16 PASS.
- O cartão da home `/inicio` rotulado `33 CONCURSOS LISTADOS` não viola o critério específico: ele é um resumo de concursos do catálogo, enquanto a contagem de resultados da busca é a que T003 exige como “Seleções”. A nota anterior que pedia `/inicio` era ambígua e não está respaldada pelo texto do aceite; não há divergência real a devolver.

Gate: ACEITA. Mantém-se apenas recomendação editorial opcional de uniformizar “Seleções” na home se o produto quiser uma taxonomia única; não é bloqueio de T003.
