# Matriz de validação UI T010/T011 — somente leitura

Para cada registro válido, abrir `/concurso/{id}` no app e conferir somente os 1–3 textos/campos listados no JSON homônimo. Os alvos são claims conferidos nos pacotes aceitos; não promover campos `pending` nem aplicar/publicar.

## Resultado da corrida UI

**NÃO ACEITA.** As 14 rotas abriram, mas todas não exibiram a seção `Cargos e requisitos` e mostraram `CARGO: Pendente de conferência`. Detalhes por ID, preservando os checks originais, estão no campo `ui_validation.results` do JSON: 1 mostrou apenas Birigui; 5 Unaí+data; 6 Berizal; 7 Garça; 8 Reriutaba; 14 FAPESE; 16 Osvaldo com `document_review pending`; 17/22/23/24 nenhum alvo; 18 apenas Quadrix; 20 apenas data; 25 apenas datas, sem 432 vagas. Nenhum registro pode ser marcado como aceite visual.

### Revalidação posterior ID1

A falha acima permanece histórica. Após o primeiro apply, o coordenador observou em `/concurso/1` todos os alvos do ID1, e a leitura independente confirmou detalhe/checkpoint, proposta `tpp-32d777ecadaaad5a790f95d7d4dd0e05` `applied`, versão 82 e uma única alteração material (`cargos`). Evidência específica: `evidencia-piloto-T010-ID1-gate-2026-09-12.md` e `.json`. Portanto, **ID1 ACEITA neste gate**, sem alterar a decisão geral da matriz.

Válidos: T010 `1,5,6,7,8,14,16`; T011 `17,18,20,22,23,24,25` (14 registros). Rotas e alvos completos estão em `matriz-validacao-ui-T010-T011-2026-09-12.json`.

Excluídos/bloqueios preservados: T010/15 — `do_not_dispatch`: identidade PDF Edital 010/2025 diverge do alvo de catálogo 005/2025 e não há entidade preservada compatível; T011/21 — `do_not_retry`: aguarda conferência das quatro retificações Funvapi e nova run/revalidação.

Estado read-only observado: API health HTTP 200; snapshot de checkpoint documentado com 33 concursos, 32 fontes e 112 cargos. T010/T011 permanecem `reference_only`, não aplicados.
