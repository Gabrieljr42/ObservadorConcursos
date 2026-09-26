# Evidência T007 — atomicidade do lote normalizado

## Estado observado

- Proposta: `tpr-4391918df249356b748f6b97691e0756`.
- Hash: `4391918df249356b748f6b97691e07561dea54466e202a2eb3e4af6e21d9052f`.
- Os dois `POST /apply` retornaram HTTP 200 com `state=no_change`, `applied=[]` e `skipped=[1..32]`.
- Persistência: 32 linhas em `concurso_publications`, criadas entre `20:34:58.546957` e `20:34:58.819127`, todas com `provenance.kind=normalized_link_fallback`.
- Persistência relacionada: `concurso_versions` com `change_type=document_added`: 0; outbox total: 49; proposta persistida `no_change`, com `applied=[]` e `skipped=[1..32]`.
- O detalhe base `GET /concursos/1` possui `publications: null`, mas esse não é o contrato de leitura das publicações. A rota documentada `GET /concursos/1/publications` retorna a linha fallback criada, com título/link/hash/proveniência e timestamp. O checkpoint exige autenticação e não foi usado nesta checagem; portanto o `null` do detalhe foi removido como falso bug de contrato.
- Logs da API registram os dois POSTs como 200. Logs do worker no mesmo intervalo mostram tarefas contínuas individuais; não há origem suficiente para atribuir a criação das 32 linhas.

## Decisão operacional

O lote permanece em execução por falha concreta de atomicidade e trilha de auditoria. Os dados existentes são preservados. Não há correção SQL direta, nova aplicação, crawl amplo ou publicação adicional até T007 corrigir e revalidar o fluxo normal com versão/outbox e recibo coerentes.
