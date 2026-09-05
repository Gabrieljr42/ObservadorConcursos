# Investigação do crawl-all — 2026-08-30

## Conclusão

O número inicial de 55 concursos não era o universo das 99 fontes. O `MASTER_SOURCES` tinha 99 definições, mas o PostgreSQL tinha somente 8 linhas em `sources` (IDs 1–8), todas ativas. O crawl-all consulta `sources` no banco, não percorre diretamente `MASTER_SOURCES`; portanto, a execução anterior percorreu exatamente 8 fontes e persistiu 55 concursos.

FUMARC era a fonte de banco ID 8, embora seja a definição de catálogo nº 16. Ela não foi a causa comprovada de uma interrupção: o `CrawlRun` disponível para ela terminou com sucesso, e não há `UniqueViolation`, `IntegrityError` ou `PendingRollbackError` nos logs da execução auditada. A hipótese não é sustentada pela evidência atual.

Foi encontrada uma segunda falha real: o hash de conteúdo da FUMARC incluía `__metadata`/etag e `OData__UIVersionString` voláteis do SharePoint. Isso gerava falso `updated` em toda nova leitura. O hash agora normaliza esses metadados, mantendo o payload completo em `raw_data`.

## Evidência e ações

- Estado antes da correção: 8 fontes ativas, 55 concursos, 76 `CrawlRun`s, 1.386 publicações e 347 versões.
- `POST /sources/presets/seed-all`: 99 fontes, `created=91`, `updated=5`, `unchanged=3`. Nenhuma fonte ou concurso foi apagado.
- Cinco fontes com `processed>0` no audit foram executadas individualmente: CONSULPAM (9), IBAM (26), IBADE (6), FGV (4) e CEBRASPE (6). Todas persistiram no banco e não houve falha de transação.
- FUMARC foi executada duas vezes após a normalização: a primeira migração produziu `updated=33`; a segunda produziu `unchanged=33`, `versions_created=0`. Na execução final do crawl-all, também ficou `unchanged=33`.
- Foi executado um único crawl-all manual, task `fe65f4aa-5e98-42e1-8f8c-547f0b77a9b9`, de 15:40:36 a 16:02:05, com 99/99 fontes. O task automático horário que ficou reservado às 16:00 foi revogado para não duplicar a investigação.
- Ao terminar: lock Redis liberado, nenhuma tarefa ativa e nenhuma mensagem de erro transacional nos logs.

O código também passou a sincronizar idempotentemente o catálogo no início do crawl-all enfileirado, síncrono e agendado. Isso impede que uma instalação nova ou parcialmente inicializada volte a executar silenciosamente apenas um subconjunto antigo de fontes. Fontes existentes marcadas como inativas continuam inativas; a sincronização não faz deleções.

## Totais do crawl-all final

| Métrica | Valor |
|---|---:|
| Fontes no catálogo/audit | 99 |
| Fontes no PostgreSQL | 99 |
| Fontes ativas | 99 |
| Candidatos encontrados | 578 |
| Candidatos rejeitados | 313 |
| Processados | 265 |
| Inseridos | 157 |
| Atualizados | 21 |
| Inalterados | 87 |
| Versões criadas | 178 |
| Notificações criadas | 15 |
| Concursos persistidos no PostgreSQL | 263 |
| Publicações persistidas | 3.034 |
| Versões persistidas | 675 |
| CrawlRuns persistidos | 184 |

Os invariantes principais fecham: `578 = 313 + 265` e `265 = 157 + 21 + 87`. O banco tinha 106 concursos após os testes direcionados; os 157 novos inseridos na rodada final resultaram nos 263 atuais.

Status de concursos persistidos: `Inscrições abertas=137`, `Em andamento=43`, `Encerrado=17`, `Inscrições em breve=7` e `NULL/sem status=59`. “Inscrições em breve” é conhecido, mas não foi contado como inscrição aberta; `NULL` é o grupo desconhecido.

O endpoint `/concursos` respondeu com 200 itens quando chamado no limite máximo da API (`limit=200`); o total de 263 vem da consulta direta ao PostgreSQL, que é a fonte de verdade para contagem completa.

## Audit versus produção

O audit `backend/audit_live_99.json` foi gerado às 10:26:49 com 99 fontes, 578 candidatos e 265 processados. A comparação por `source_type` contra o `CrawlRun` final encontrou:

- 0 divergências de `status`, `candidates_found`, `candidates_rejected` ou `processed`;
- 0 fontes do audit ausentes no banco;
- 0 fontes do banco ausentes no audit;
- 0 fontes com `processed>0` e zero concursos no banco;
- 0 fontes com status `success` e zero concursos no banco;
- 0 fontes ativas sem `CrawlRun`.

O audit informa `total_visible_valid_items=541`, mas isso é uma métrica de observação/visibilidade e não uma contagem de linhas a inserir. Não foi usado como substituto do banco. A diferença para os 263 persistidos é esperada por rejeição de qualidade, itens sem persistência e deduplicação entre fontes.

A categoria “candidatos>0 e processados=0” contém 10 fontes: FCC, Cesgranrio, IDCAP, Águia, FACET, APTA, Publiconsult, Sigma, W2 e Fênix. São casos de rejeição total/estado vazio reportado, não perda silenciosa após commit.

## Funil completo por fonte

`Audit C/R/P` = candidatos/rejeitados/processados no audit. `Run C/R/P` = os mesmos campos do `CrawlRun` final. `I/U/N` = inseridos/atualizados/inalterados nessa rodada. `DB` = concursos atualmente ligados à fonte. O código de erro é detalhado na seção seguinte.

| # | source_type | Audit C/R/P | Run C/R/P | I/U/N | DB | status | erro |
|---:|---|---:|---:|---:|---:|---|---|
| 1 | ibfc_open | 0/0/0 | 0/0/0 | 0/0/0 | 1 | empty_valid | — |
| 2 | ibgp_open | 15/0/15 | 15/0/15 | 0/15/0 | 15 | success | — |
| 3 | imeso_open | 2/0/2 | 2/0/2 | 0/0/2 | 3 | success | — |
| 4 | fundep_open | 2/1/1 | 2/1/1 | 0/0/1 | 2 | success | — |
| 5 | aocp_open | 0/0/0 | 0/0/0 | 0/0/0 | 0 | blocked | CloudflareChallenge |
| 6 | idecan_open | 0/0/0 | 0/0/0 | 0/0/0 | 1 | empty_valid | — |
| 7 | consulplan_open | 0/0/0 | 0/0/0 | 0/0/0 | 0 | empty_valid | CloudflareChallenge |
| 8 | fumarc_open | 34/1/33 | 34/1/33 | 0/0/33 | 33 | success | — |
| 9 | consulpam_open | 25/16/9 | 25/16/9 | 0/0/9 | 9 | success | — |
| 10 | ibam_open | 30/4/26 | 30/4/26 | 0/0/26 | 26 | success | — |
| 11 | ibade_open | 6/0/6 | 6/0/6 | 0/0/6 | 6 | success | — |
| 12 | seprod_open | 0/0/0 | 0/0/0 | 0/0/0 | 0 | degraded | UnconfirmedEmpty |
| 13 | fcc_open | 30/30/0 | 30/30/0 | 0/0/0 | 0 | empty_valid | — |
| 14 | fgv_open | 30/26/4 | 30/26/4 | 0/0/4 | 4 | success | — |
| 15 | cebraspe_open | 6/0/6 | 6/0/6 | 0/0/6 | 6 | success | — |
| 16 | cesgranrio_open | 4/4/0 | 4/4/0 | 0/0/0 | 0 | degraded | AllCandidatesRejected |
| 17 | idcap_open | 25/25/0 | 25/25/0 | 0/0/0 | 0 | empty_valid | — |
| 18 | omni_open | 2/0/2 | 2/0/2 | 2/0/0 | 2 | success | — |
| 19 | access_open | 2/0/2 | 2/0/2 | 2/0/0 | 2 | success | — |
| 20 | exame_open | 6/2/4 | 6/2/4 | 4/0/0 | 4 | success | — |
| 21 | epl_open | 0/0/0 | 0/0/0 | 0/0/0 | 0 | empty_valid | — |
| 22 | abcp_open | 4/0/4 | 4/0/4 | 4/0/0 | 4 | success | — |
| 23 | unifil_open | 0/0/0 | 0/0/0 | 0/0/0 | 0 | blocked | CloudflareChallenge |
| 24 | objetiva_open | 12/0/12 | 12/0/12 | 10/2/0 | 10 | success | — |
| 25 | leandroferreira_open | 0/0/0 | 0/0/0 | 0/0/0 | 0 | failed | Error |
| 26 | cotec_open | 2/0/2 | 2/0/2 | 2/0/0 | 2 | success | — |
| 27 | aguia_open | 25/25/0 | 25/25/0 | 0/0/0 | 0 | empty_valid | — |
| 28 | iuds_open | 0/0/0 | 0/0/0 | 0/0/0 | 0 | degraded | UnconfirmedEmpty |
| 29 | reisesreis_open | 0/0/0 | 0/0/0 | 0/0/0 | 0 | degraded | UnconfirmedEmpty |
| 30 | msconcursos_open | 25/23/2 | 25/23/2 | 2/0/0 | 2 | success | — |
| 31 | facet_open | 25/25/0 | 25/25/0 | 0/0/0 | 0 | empty_valid | — |
| 32 | educapb_open | 0/0/0 | 0/0/0 | 0/0/0 | 0 | degraded | UnconfirmedEmpty |
| 33 | admtec_open | 4/0/4 | 4/0/4 | 4/0/0 | 4 | success | — |
| 34 | contemax_open | 0/0/0 | 0/0/0 | 0/0/0 | 0 | failed | Error |
| 35 | cpcon_open | 10/0/10 | 10/0/10 | 10/0/0 | 10 | success | — |
| 36 | funvapi_open | 7/1/6 | 7/1/6 | 6/0/0 | 6 | success | — |
| 37 | consep_open | 0/0/0 | 0/0/0 | 0/0/0 | 0 | empty_valid | — |
| 38 | institutoconsulplan_open | 0/0/0 | 0/0/0 | 0/0/0 | 0 | empty_valid | — |
| 39 | avalia_open | 2/1/1 | 2/1/1 | 1/0/0 | 1 | success | — |
| 40 | ufu_selection | 11/0/11 | 11/0/11 | 11/0/0 | 11 | success | — |
| 41 | idgran_open | 0/0/0 | 0/0/0 | 0/0/0 | 0 | failed | Error |
| 42 | quadrix_open | 2/0/2 | 2/0/2 | 2/0/0 | 2 | success | — |
| 43 | gualimp_open | 0/0/0 | 0/0/0 | 0/0/0 | 0 | degraded | UnconfirmedEmpty |
| 44 | verbena_selection | 5/1/4 | 5/1/4 | 4/0/0 | 4 | success | — |
| 45 | idib_open | 6/0/6 | 6/0/6 | 6/0/0 | 6 | success | — |
| 46 | jcm_open | 0/0/0 | 0/0/0 | 0/0/0 | 0 | empty_valid | — |
| 47 | elo_open | 7/0/7 | 7/0/7 | 7/0/0 | 7 | success | — |
| 48 | apta_open | 25/25/0 | 25/25/0 | 0/0/0 | 0 | empty_valid | — |
| 49 | legalle_open | 25/21/4 | 25/21/4 | 4/0/0 | 4 | success | — |
| 50 | rbo_open | 2/0/2 | 2/0/2 | 2/0/0 | 2 | success | — |
| 51 | shdias_open | 0/0/0 | 0/0/0 | 0/0/0 | 0 | blocked | CloudflareChallenge |
| 52 | zambini_open | 0/0/0 | 0/0/0 | 0/0/0 | 0 | empty_valid | — |
| 53 | nossorumo_open | 2/0/2 | 2/0/2 | 1/1/0 | 1 | success | — |
| 54 | avancasp_open | 6/0/6 | 6/0/6 | 5/1/0 | 5 | success | — |
| 55 | institutomais_open | 18/1/17 | 18/1/17 | 15/2/0 | 15 | success | — |
| 56 | publiconsult_open | 14/14/0 | 14/14/0 | 0/0/0 | 0 | empty_valid | — |
| 57 | klc_open | 0/0/0 | 0/0/0 | 0/0/0 | 0 | empty_valid | — |
| 58 | sigma_open | 1/1/0 | 1/1/0 | 0/0/0 | 0 | empty_valid | — |
| 59 | w2_open | 10/10/0 | 10/10/0 | 0/0/0 | 0 | empty_valid | — |
| 60 | fenix_open | 25/25/0 | 25/25/0 | 0/0/0 | 0 | empty_valid | — |
| 61 | oppus_open | 0/0/0 | 0/0/0 | 0/0/0 | 0 | degraded | UnconfirmedEmpty |
| 62 | legatus_open | 12/1/11 | 12/1/11 | 11/0/0 | 11 | success | — |
| 63 | fepese_open | 13/0/13 | 13/0/13 | 13/0/0 | 13 | success | — |
| 64 | funcern_selection | 2/0/2 | 2/0/2 | 2/0/0 | 2 | success | — |
| 65 | fapemig_selection | 0/0/0 | 0/0/0 | 0/0/0 | 0 | degraded | UnconfirmedEmpty |
| 66 | fapes_selection | 0/0/0 | 0/0/0 | 0/0/0 | 0 | degraded | UnconfirmedEmpty |
| 67 | fapesq_selection | 0/0/0 | 0/0/0 | 0/0/0 | 0 | degraded | UnconfirmedEmpty |
| 68 | uniselva_selection | 9/7/2 | 9/7/2 | 2/0/0 | 2 | success | — |
| 69 | fafipa_open | 9/0/9 | 9/0/9 | 9/0/0 | 9 | success | — |
| 70 | ieses_open | 26/23/3 | 26/23/3 | 3/0/0 | 3 | success | — |
| 71 | funpec_selection | 10/0/10 | 10/0/10 | 10/0/0 | 10 | success | — |
| 72 | fade_selection | 0/0/0 | 0/0/0 | 0/0/0 | 0 | degraded | UnconfirmedEmpty |
| 73 | fapex_selection | 0/0/0 | 0/0/0 | 0/0/0 | 0 | degraded | UnconfirmedEmpty |
| 74 | fatec_selection | 3/0/3 | 3/0/3 | 3/0/0 | 3 | success | — |
| 75 | faped_selection | 0/0/0 | 0/0/0 | 0/0/0 | 0 | degraded | UnconfirmedEmpty |
| 76 | fapese_selection | 0/0/0 | 0/0/0 | 0/0/0 | 0 | degraded | UnconfirmedEmpty |
| 77 | fapepi_selection | 0/0/0 | 0/0/0 | 0/0/0 | 0 | empty_valid | — |
| 78 | fapema_selection | 0/0/0 | 0/0/0 | 0/0/0 | 0 | degraded | UnconfirmedEmpty |
| 79 | fapece_selection | 0/0/0 | 0/0/0 | 0/0/0 | 0 | failed | Error |
| 80 | fapern_selection | 0/0/0 | 0/0/0 | 0/0/0 | 0 | degraded | UnconfirmedEmpty |
| 81 | fapeal_selection | 0/0/0 | 0/0/0 | 0/0/0 | 0 | degraded | UnconfirmedEmpty |
| 82 | facepe_selection | 0/0/0 | 0/0/0 | 0/0/0 | 0 | degraded | UnconfirmedEmpty |
| 83 | fapesb_selection | 0/0/0 | 0/0/0 | 0/0/0 | 0 | degraded | UnconfirmedEmpty |
| 84 | faperj_selection | 0/0/0 | 0/0/0 | 0/0/0 | 0 | degraded | UnconfirmedEmpty |
| 85 | fapesp_selection | 0/0/0 | 0/0/0 | 0/0/0 | 0 | degraded | UnconfirmedEmpty |
| 86 | fappr_selection | 0/0/0 | 0/0/0 | 0/0/0 | 0 | degraded | UnconfirmedEmpty |
| 87 | fapesc_selection | 0/0/0 | 0/0/0 | 0/0/0 | 0 | degraded | UnconfirmedEmpty |
| 88 | fapergs_selection | 0/0/0 | 0/0/0 | 0/0/0 | 0 | degraded | UnconfirmedEmpty |
| 89 | fundect_selection | 0/0/0 | 0/0/0 | 0/0/0 | 0 | degraded | UnconfirmedEmpty |
| 90 | fapemat_selection | 0/0/0 | 0/0/0 | 0/0/0 | 0 | degraded | UnconfirmedEmpty |
| 91 | fapeg_selection | 0/0/0 | 0/0/0 | 0/0/0 | 0 | degraded | UnconfirmedEmpty |
| 92 | fapdf_selection | 0/0/0 | 0/0/0 | 0/0/0 | 0 | degraded | UnconfirmedEmpty |
| 93 | fapt_selection | 0/0/0 | 0/0/0 | 0/0/0 | 0 | degraded | UnconfirmedEmpty |
| 94 | fapeam_selection | 0/0/0 | 0/0/0 | 0/0/0 | 0 | degraded | UnconfirmedEmpty |
| 95 | fapespa_selection | 0/0/0 | 0/0/0 | 0/0/0 | 0 | degraded | UnconfirmedEmpty |
| 96 | fapeap_selection | 0/0/0 | 0/0/0 | 0/0/0 | 0 | degraded | UnconfirmedEmpty |
| 97 | faperr_selection | 0/0/0 | 0/0/0 | 0/0/0 | 0 | degraded | UnconfirmedEmpty |
| 98 | fapero_selection | 0/0/0 | 0/0/0 | 0/0/0 | 0 | degraded | UnconfirmedEmpty |
| 99 | fapac_selection | 0/0/0 | 0/0/0 | 0/0/0 | 0 | degraded | UnconfirmedEmpty |

## Erros e leitura prática

- 3 fontes bloqueadas por Cloudflare: AOCP, UniFil e SHDias.
- 4 falhas externas isoladas: Leandro Ferreira (DNS), CONTEMAX (connection refused), IDGRAN (DNS) e FAPECE (DNS).
- 34 fontes `degraded` com `UnconfirmedEmpty`: não apresentaram candidatos nem evidência explícita de estado vazio; foram registradas e a execução continuou.
- 1 fonte `degraded` com `AllCandidatesRejected`: Cesgranrio teve 4 candidatos, todos rejeitados pelo quality gate.
- 10 fontes tinham candidatos observados, mas zero processados porque todos foram rejeitados/considerados inválidos; estão visíveis na tabela com `C/R/P` e `DB=0`.

Nenhuma dessas situações matou o crawl-all. Cada fonte recebeu seu `CrawlRun`, e as fontes posteriores continuaram sendo executadas.

## Verificação técnica da hipótese FUMARC

O banco mostrou 33 concursos FUMARC e versões antigas cujo conteúdo semântico era igual, mas cujo `raw_data.sharepoint_item.__metadata.etag`/`OData__UIVersionString` mudava entre leituras. A constraint PostgreSQL `uq_concurso_publication_hash` continua presente. O sincronismo de publicações usa deduplicação no payload e `ON CONFLICT DO NOTHING`; o serviço faz rollback por fonte e registra falha em transação separada. Os testes de resiliência cobrem `UniqueViolation` forçada, recuperação do próximo source, lock tokenizado e ausência de `PendingRollbackError`.

## Testes

`python -m pytest backend/tests -q`:

```text
138 passed, 2 skipped, 281 warnings
```

As warnings são principalmente depreciações de `datetime.utcnow()`/HTTPX em código existente. O mobile não foi alterado nesta investigação.
