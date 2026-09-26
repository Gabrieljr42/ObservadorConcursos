# Entrega lote 01 — preparação para revisão humana

Atualização da entrega: as quatro propostas abaixo foram autorizadas pelo usuário na resposta à pergunta que listou seus campos e datas. Foram aplicadas em 09/09/2026: JCM → concurso 4/versão 8; Instituto Consulplan → 5/9; IMESO → 6/10; ABCP Garça → 7/11. O texto de preparação abaixo permanece como histórico. Recibo: `backend/.tenderproof/product-completion/lote-01-review/application-20260909T200129665400Z.json`. Garça havia falhado por contenção de processamento; a correção passou a reutilizar processamento idêntico validado e aguardar capacidade de forma limitada, preservando os controles de publicação.

Observado em 2026-09-09 19:52 UTC. Foram usados os sete runs fornecidos e o usuário proprietário autenticado. A operação executou `document-review/.../prepare` e, quando não havia pendência documental, criou somente propostas em estado `proposed`. Nenhuma proposta foi aprovada ou aplicada.

## Propostas prontas para aprovação humana

| Fonte / concurso | Run | Proposal / hash | Campos elegíveis | Bloqueios preservados | Evidência principal |
|---|---|---|---|---|---|
| JCM 268 — Carmo da Cachoeira/MG | `tp-tcj-e57a86e6e2ff5da5868acf49a60ac403-4` | `tpp-2eed3f07a9ec541023f84e38bd0c463a` / `bc515e08a0e2bb2dfe3224ac4b198f0b16a18f9dafceea46f08ad256019c2c4c` | título, órgão, edital 001/2026, inscrições 17/11/2026–17/12/2026, prova 17/01/2027 | remuneração sem contexto; cargos pendentes no quadro JCM | SHA `81a021874d8e426e69ad4018ca468513f5918c4bbfdac648e236465a08fdb4e8`; PDF oficial `https://anexos-r2.selecao.net.br/uploads/17/concursos/268/anexos/aa5c4165-c626-4422-9506-dafd64a9e745.pdf` |
| Instituto Consulplan — Câmara de Unaí/MG | `tp-tcj-706b5bc7f1f75e5cb0c3c05c48bce934-3` | `tpp-7a2b5eeacf764476090fdf2073985f7f` / `8f748f1ca83b9cb95ec0ded506fdbf2f422716f4f76263dc6e6c2da30706b02d` | título, órgão, edital 1/2026, inscrições 30/10/2026–01/12/2026 | prova, remuneração e cargos pendentes | SHA `9bdb0e77fde501c33363ce636744b8be8107c64a996c1bde6b4aa2faa96dac32`; PDF oficial `https://cdnsite.institutoconsulplan.org.br/concursos/1333/dc1fe1e393a346f0803722772b630442.pdf` |
| IMESO 139 — Prefeitura de Berizal/MG | `tp-tcj-377fa72c32a2587eb20c8e068572a18b-1` | `tpp-2e3e9a0fcde2c34490f9f9a0f5b94027` / `8612f58d408bec402c4853693f25cc8e1c8589445e13c25f8579a46db7fa7232` | título, órgão, edital 001/2026, inscrições 13/10/2026–13/11/2026 | prova, remuneração e cargos pendentes | SHA `8e6fbc48ac7f54c492cc2beba78adc9216ba25fa781ba753d3e9e410fc7dd6dc`; PDF oficial `https://s3.us-east-1.amazonaws.com/cdn.imeso.com.br/edital/1/139/402c39f4f7ecc38a1905e41163fdc4be.pdf` |
| ABCP 2868 — Câmara de Garça/SP | `tp-tcj-b7b17f29eeac52a9a43f71c360753e43-1` | `tpp-ea29153c0ae799f739c1d3da5537bbd7` / `22803906ecdfd34242fbe921623bd4f967d5bf3404397affcc96da44af086aec` | título, órgão, edital 001/2026, inscrições 04/09/2026–07/10/2026 | prova, remuneração e cargos pendentes | SHA `00dc6e0d8e560b8b0a5aae557016d7e6a169b1ebc00aeb31d7ff95babf497b2a`; PDF oficial `https://anexos-r2.selecao.net.br/uploads/567/concursos/2868/anexos/6b72e3c6-333b-49b5-b871-801295856d49.pdf` |

Os quatro casos acima têm `document_review.pending=false`, estado de proposta `proposed`, e decisões de aprovação ainda vazias. O operador deve revisar os trechos/páginas no aplicativo antes de aprovar campos.

## Runs bloqueados nesta preparação

Esses três bloqueios foram resolvidos no fechamento: a causa era contenção do processador (`concurrency_limit`), não PDF inválido. Após reutilização validada e espera limitada, IDIB foi aplicado no concurso 8/versão 12, Cebraspe no 9/13 e FEPESE no 10/14. Os sete detalhes foram conferidos no aplicativo. Recibo final: `backend/.tenderproof/product-completion/lote-01-review/application-20260909T200304612528Z.json`. A tabela abaixo preserva o resultado da tentativa inicial.

| Fonte | Run | Resultado |
|---|---|---|
| IDIB 362 | `tp-tcj-b6372819d87e51c185e6427865a5bf62-1` | `prepare` respondeu 409 sem pendências; criação de proposta respondeu 422: processamento documental falhou ou excedeu limites. |
| Cebraspe Ponta Porã | `tp-tcj-2b58bacc0b6a5a028ffc292908b9b6da-1` | Mesmo resultado: 409 sem pendências e 422 no gate de processamento documental. |
| FEPESE Caxambu | `tp-tcj-8c4428c810c45812a92132a23bf42958-1` | Mesmo resultado: 409 sem pendências e 422 no gate de processamento documental. |

Não foi repetida coleta nem alterado extrator para esses três casos. Recibo operacional detalhado permanece em `backend/.tenderproof/product-completion/lote-01-review/preparation.json` no volume do piloto; `lote01-output.json` contém o resumo capturado da execução.
