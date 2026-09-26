# Parecer independente pós-apply T005 — semântica da prova

Data: 2026-09-13. Auditoria bounded, somente leitura; nenhuma mutação executada.

## Decisão: ACEITA no escopo aplicado; sem proposta corretiva de cargos

A retificação canônica registra `etapas_prova`: anterior **Objetiva de Múltipla Escolha e TAF**, vigente **Objetiva de Múltipla Escolha e Títulos**, com proveniência no SHA `5780db65…fa201a` (p.1), em `docs/execucao/tarefas/T005-review-T004-fields.json`.

Há um TAF nos artefatos de derivação (`T005-concurso32-derivation-a.json` e `-b.json`, campo auxiliar `provas`), mas ele **não foi promovido** ao payload de cargos aplicado: o `fields[0].value` do `T005-concurso32-reviewed-run-owner1.json` contém somente os campos canônicos de cargo, sem `provas`/`prova_observacao`; o gate pós-apply também não registra esse campo. Portanto a versão 89 não contradiz a retificação no escopo `approved_fields=[cargos]`. O TAF nas derivações é evidência auxiliar stale/incompatível e não deve ser exibido como estado vigente.

Os sete cards estão íntegros: microáreas 03, 04, 05, 07, 09, 12 e 15; cada um com 1 vaga imediata/1 ampla/0 PcD/CR nulo, R$ 3.242,00, 40h/semana, taxa R$ 162,10 e requisitos presentes. O gate pós-apply confirma 7 cargos, 7 vagas e versão 89/outbox 89/notificação 88, com replay idempotente.

Conclusão: liberar a semântica de versão 89 no escopo aplicado. Não abrir proposta corretiva limitada; abrir apenas incidente documental se a UI efetivamente renderizar o TAF a partir da derivação auxiliar.
