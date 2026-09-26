# Evidência — aplicação Garibaldi

Proposta revisada e aplicada em 2026-09-12 pelo facade normal, sem SQL ad hoc:

- Proposta: `tpa-ff3ac1092183a78f6795b674c04bd942`, hash `ff3ac1092183a78f6795b674c04bd942f514025ecf0a029944d2a083e0da39b6`.
- Receipt: `backend/.tenderproof/product-completion/delivery-legalle-applied-20260912T203143950720Z.json`.
- Resultado: concurso `33`, versão `49`, estado `applied`, segunda aplicação idempotente no mesmo `version_id`, `review_pending=false`.
- API viva após sincronização: 33 seleções, 32 fontes, 112 cargos estruturados, 49 versões, 48 notificações, 0 favoritos e 1 alerta preservado.
- `GET /concursos/33` respondeu e mostrou 13 cargos. O campo estruturado `publications` permanece nulo e a tabela de publicações continua vazia; a resposta traz o edital/retificações no histórico `raw_data.tenderproof.amendments`. A aplicação foi de campos e identidade do certame, não de publicação estruturada.
- A proposta manteve autorização delegada com `human_read=false`; nenhuma leitura humana foi declarada.
