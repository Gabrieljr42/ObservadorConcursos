# Decisões de execução

## 2026-09-13T15:42:06.1922146Z — UFU live R9

- Após deploy UFU R8/APTA R9, health/login/checkpoint/CAS e document-review do run `tp-reviewed-f3e9c58974f5f13419565aa22ded286d` passaram; source40/external1843 permanece ausente do catálogo.
- A única criação normal de proposta target nulo retornou HTTP 422 por falta de evidência reproduzida para título/órgão/edital. Não repetir, aprovar ou aplicar até diagnóstico/revisão; nenhuma proposta ou mutação canônica foi criada. Receipt `docs/execucao/evidencias/T012/ufu_selection/live-proposal-receipt-r9-20260913.json`.

## 2026-09-13T15:38:57.0951770Z — deploy UFU R8/APTA R9

- Aceito o redeploy restrito de `api/worker/scheduler` na imagem `sha256:9dfcaadfe6ec3f929e591c8f8ede2a8c407fd4ee51ed645645f597f80aa05935`; Postgres/Redis/web/volumes permaneceram intactos.
- Health/web 200, baseline 34/33/182, 98 propostas, 92 versões/outbox, 91 notificações, fav0/alert1/push0; runs UFU/APTA confirmados read-only. Smokes 3/3 APTA, 10/10 UFU e 16/16 contrato/batch. Nenhum import/proposal/approve/apply. Receipt `docs/execucao/evidencias/T012/backend-deploy-ufu-r8-apta-smoke-r2-20260913.json`.

## 2026-09-13T15:27:51.4039109Z — APTA R10

- APTA `source_id=48`, `external_id=708` foi importada uma única vez pelo fluxo normal após dois dry-runs estáveis: run `tp-reviewed-9ca7ffc16743d555cc227a038f337bfa`, owner1, target nulo, somente `titulo/orgao/edital_numero`, artefato SHA `db9c6d26…d79c` (362093 bytes/20 páginas).
- A única criação de proposta retornou HTTP 409 por document-review ainda pendente (`retificação` observada). Não repetir, aprovar ou aplicar até revisão independente; não houve proposta/version/outbox/notificação/cargo canônico novo. Receipt: `docs/execucao/evidencias/T012/apta_open/live-proposal-receipt-r10-20260913.json`.

## 2026-09-13 05:10:00 - reconciliação T004 r5 r2 (Luna integrador)

- A revisão `T004_FINAL_ACCEPT` é aceite somente no escopo read-only: `docs/execucao/evidencias/T004/revisao-final-T004-r2-Luna-20260913.json`, hash `588AE6689F204117704538C69218633E4AA6988AC4B9A08CE055C05056073C71`. T004 permanece `EM_REVISAO/PARCIAL`; não converter o aceite documental em conclusão global.
- A matriz r5 r2 substitui r4 como retrato corrente de cobertura/reconciliação, continua `authoritative=false`, 99/99 fontes. JSON SHA `1fd4946d9191eb76138db5cf6ddaed770311eb64719446006fe532e7810d2e86`; CSV SHA `ae313153cec371adc62452fc2ce0da5cad2d6f7f14a52a3e3e1f56668c5008d4`. `runtime_factory_absent=0`; oito `adapter_current=null` históricos não significam factory ausente; integração/homologação seguem não certificadas.
- ID5/Câmara Unaí está `LOCAL_REVIEWED_READY_FOR_IMPORT_PROPOSAL`, parser v5, run `tp-reviewed-40120e7a2b6662b131075dc416d2cb18`, proof supplement `tp-reviewed-1edc6badadc7a40c9fa6a0b2b220bf3`, gate local 14 pass; não foi importado, proposto, aprovado ou aplicado ao vivo. Garibaldi/33 está `GARIBALDI_OFFLINE_ACCEPT_WITH_BLOCKER`, com quatro metadados/ledger e dois testes offline, aguardando bytes/conteúdo exatos no volume e fluxo normal posterior até API/UI.
- IDs 18/20/22–25 mantêm blockers específicos T004/T011; ID15 permanece mismatch e ID21 `DO_NOT_RETRY`. Owners e condições de saída permanecem por registro; nenhum adapter/homologação ou publicação source-wide é inferido.
- Snapshot/contagens (33/180/34/91/95/91/90) continuam o último estado verificado pré-outage. Docker operacional está indisponível; restart exige autorização explícita e não é o único gate restante. Backup/restore operacional continua válido; restore PostgreSQL isolado segue pendente no estado `BLOCKED_AFTER_ESCALATED_PROBE` (alias `BLOCKED_DOCKER_502`).

## 2026-09-13 04:42:59 - fechamento operacional pré-T002 (Luna integrador)

- Snapshot vivo pós-v91 confirmado sem mutação: 33 concursos, 32 fontes de catálogo, 99 fontes configuradas, 180 cargos, 34 publicações, 91 versões/outbox, 90 notificações, 95 propostas e push_devices/deliveries/attempts=0. Favorito de teste id8 e alerta de teste id6 estão ausentes; alerta original id1 permanece ativo.
- Health/API e web estavam coerentes antes do backup: health 200; IDs 8/14/16/17/32 responderam; `/inicio` e `/tenderproof` 200; asset servido `entry-ed357d6cd1c2750f556e9ffd48d77343.js`, SHA `A6E23E…E5AB`; rota `prepare-preserved` existe e chamada sem autenticação retorna 401; push efetivo permanece disabled.
- Backup final oficial passou em `/backups/pilot-20260913T073116707Z`: dump PostgreSQL com `pg_restore --list` e bundle operacional verificado com 15.541 arquivos. Restore operacional foi criado em `/backups/final-restore-20260913T073116707Z-operational` sem tocar o volume canônico.
- O restore PostgreSQL isolado ficou `BLOCKED_AFTER_ESCALATED_PROBE` (alias operacional de `BLOCKED_DOCKER_502`): retry bounded não obteve resposta do daemon e health permaneceu indisponível. Não reiniciar globalmente, não prune/reset e não declarar fechamento final até T002 repetir somente o restore isolado quando o engine recuperar. Evidência: `docs/execucao/evidencias/fechamento-operacional-pre-T002-20260913.json`.
- Estados correntes para revisão: T001/T002 EM_REVISAO; T003/T005/T006/T007/T008/T009 CONCLUIDA/ACEITA; T004 EM_REVISAO/PARCIAL; T010 CONCLUIDA no escopo executável (IDs1,6,7,8,14,16 aplicados+UI; ID5 insuficiente; ID15 mismatch); T011 CONCLUIDA no escopo executável/PARCIAL (ID17 aceito; 18/20/22–25 insuficientes; 21 DO_NOT_RETRY). bdb86 permanece NEVER_APPROVE/NEVER_APPLY; proposta correta ID16 `tpp-1a0fc40cc8df713e6958de0f43efc032` permanece aplicada.

## HISTÓRICO SUPERSEDIDO — 2026-09-13 02:06:29 — reconciliação pós-gates T005/T010/T011 (Luna integrador)

> Supersedido pelo fechamento posterior: ID14 foi aplicado em v90 e ID16 foi aplicado em v91; a matriz r4 e o snapshot 180/91/91/90/95 são correntes. A proibição histórica de autorizar/aplicar ID14/ID16 não vigora após os gates independentes posteriores.

- Snapshot atual confirmado por API/PostgreSQL: 33 concursos, 32 fontes, 160 cargos, 89 versões, 89 outbox, 88 notificações e 93 propostas. Os números anteriores de 124 cargos/84 versões/83 notificações/86 propostas permanecem somente como histórico datado.
- T005/ID32 está aceito em v89; T011/ID17 está aceito em v86 após apply/replay e validação do payload; T010/ID8 está aceito em v87 (cargos) + v88 (`prova_data=2026-12-06`). Evidências: `docs/execucao/evidencias/T005/gate-pos-apply-20260913.json`, `docs/execucao/evidencias/T011/gate-ID17-r8-pos-apply-20260913.json` e `docs/execucao/evidencias/T010/gate-ID8-prova-data-pos-apply-20260913.json`.
- T010/ID14 tem import e proposta normal `tpp-c3f5d96741ac903d3c70469a4af3972a` em `proposed`, somente `cargos`; o web foi redeployado isoladamente, 23 rotas reais retornam 200 e a proposta aguarda revisão independente. ID16 não foi importado nem proposto: o envelope regenerado passa dry-run, mas gera `tp-reviewed-1f9a51cc55dc7312c5153645b45ab9bc`, divergente do run exigido `tp-reviewed-781d2b5...`.
- Preservar como histórico os estados anteriores que diziam T010 final/ID17 devolvido e snapshot 124 cargos. IDs 5/15 e demais insuficientes/`DO_NOT_RETRY` permanecem internos, com owner/próximo passo, sem promoção automática. Não autorizar/aplicar ID14 ou ID16 sem revisão independente correspondente.

## 2026-09-12 — baseline e escopo

- Reutilizar as evidências atuais de `docs/VERIFICACAO-REAL-2026-09-12.md`, `docs/ENTREGA-ATUAL-OPERACAO.md` e `docs/OPERACAO-LOCAL.md`; não repetir suítes completas sem hipótese nova.
- Usar os scripts existentes como primeira linha de verificação. Serviços do piloto, volumes, credenciais e outros projetos Docker devem ser preservados.
- Publicação permitida somente pelo fluxo normal de proposta, autorização e aplicação auditada, para campos documentalmente conferidos. É proibido escrever diretamente no banco ou declarar leitura humana por automação.
- Builds, reinícios, migrações e publicações no piloto serão executados sequencialmente por T001.
- Nenhum gasto Solari até conferir controle persistido e cobrança efetiva; referência conhecida: US$20 autorizados e US$5,26 reservados.
- Números do baseline são datados e não devem virar valores fixos em testes (por exemplo, inscrições abertas).
- Ausência de adaptador é pendência técnica interna; só classificar como bloqueio externo após evidência específica de WAF, DNS, credencial ou indisponibilidade do serviço.

## 2026-09-12 17:56 - reconciliação da retomada (Luna integrador)

- Ponto de retomada: fechar T007 (atomicidade das 32 referências fallback) e executar a prova real pendente de T008; novas publicações documentais continuam suspensas até aceite dessas frentes.
- Garibaldi está aplicado como seleção 33 pelo fluxo normal e verificado com 13 cargos, versão 49 e 48 notificações (`evidencias-garibaldi-2026-09-12.md`, `evidencias-api-pos-garibaldi-2026-09-12.md`). T004 permanece em revisão do material restante; não tratar a aplicação como publicação estruturada.
- T010 e T011 deixam `PRONTA` e passam a `EM_REVISAO`: os 16 registros têm evidência read-only, sem proposta/aplicação; revisão independente e o gate P0 de T007 ainda faltam.
- Estado operacional somente leitura: API/web/worker/scheduler ativos, PostgreSQL/Redis saudáveis e `GET /health` HTTP 200. Alterações locais de código/documentação são numerosas e pré-existentes; não foram descartadas nem reescritas.

## Pendências prioritárias aceitas

Histórico legível; fuso explícito e distinção de precisão temporal; rótulo “seleções” em vez de “vagas”; publicações estruturadas; causas FAFIPA/FAPESB; persistência/offline/backup; matriz das 99 fontes.

## 2026-09-12 18:01 - atualização de gates (Luna integrador)

- T010/T011: os 16/16 pacotes foram ACEITOS em revisão independente, com campos pendentes preservados e `reference_only`; evidência: `docs/execucao/evidencias/revisao-independente-T010-T011-Luna-20260912.json`. O aceite documental não autoriza aplicação: T007/T008 continuam bloqueando.

## 2026-09-12 18:40 - aceite operacional T007 pós-redeploy (Luna integrador)

- T007 marcado CONCLUIDA/ACEITA: revisão `docs/execucao/tarefas/revisao-operacional-T007-pos-redeploy-20260912-01.md` confirma proposta GET 200/applied, health 200, 30 fallbacks `reference_only` e quatro documentos integrais nos concursos 3 e 32, totalizando 34 publicações; 32 versões/outbox/concurso e zero duplicatas.
- T008 r3 permanece em corrida real/revisão. T010/T011 continuam sem publicação.

## 2026-09-12 18:43 - estado de dispatch e aceite parcial T008 (Luna integrador)

- T007 permanece CONCLUÍDA/ACEITA operacionalmente, conforme revisão pós-redeploy.
- T008 recebe ACEITE PARCIAL: servidor confirmou alerta id `6` (`active=false`) e favorito id `8`/concurso `33`; gate único restante é confirmação CUA da remoção pela UI, reload/reconnect e comportamento legítimo de servidor ausente/vazio. Evidência: `docs/execucao/evidencias-T008-offline-window-2026-09-12.md`.
- T010/T011: manifestos r2 ACEITOS e PRONTOS PARA DISPATCH; não despachar enquanto o único bloqueio T008 não for confirmado.
- T007: correção de atomicidade implementada e testada, agora em revisão independente. Não executar no piloto nem reparar as 32 linhas existentes antes do aceite e do procedimento serializado.
- T008: primeira entrega DEVOLVIDA por corrida A→B/owner no sincronizador. Correção em andamento; sem build, reinício ou corrida no piloto nesta etapa.

## 2026-09-12 18:52:32 - aceite operacional T008 e liberação controlada T010/T011 (Luna integrador)

- T008 passa a CONCLUIDA/ACEITA: a corrida real confirmou remoção de alerta e favorito pela UI, reload/reconnect e estado legítimo no servidor; alerta de teste id `6` ausente, alerta original preservado e checkpoint com `alerts=1`, `favorites=0`. Evidência: `docs/execucao/evidencias-T008-offline-window-2026-09-12.md`.
- O bloqueio exclusivo de T010/T011 foi removido. Ambos permanecem PRONTOS PARA DISPATCH, condicionado a backup fresco/restore isolado, sublotes seriais e payloads `http_payload` exatos. Este gate não autoriza aprovação ou aplicação; qualquer mismatch interrompe a sequência.

## 2026-09-12 19:00 - dispatch interrompido no primeiro erro T010 (Luna integrador)

- Backup fresco e restore isolado passaram: `/backups/pilot-20260912T215347930Z-operational` e `/backups/dispatch-restore-isolated-20260912T215347930Z`, ambos com 11.743 arquivos e volumes canônicos preservados.
- Dispatch serializado usando os `http_payload` exatos criou seis propostas T010 (`201`, `state=proposed`) — registros 1, 5, 6, 7, 8 e 14 — todos confirmados por GET sem `version_id`/`result`. T010-b04/registro 15 retornou HTTP 422; o gate parou sem retry. Registro 16 e todos os T011 não foram enviados.
- Checkpoint pós-gate permaneceu `publications=34`, `versions=81`, `notifications=80`, `alerts=1`, `favorites=0`; logs não mostram approve/apply. Evidência: `docs/execucao/evidencias-dispatch-T010-T011-2026-09-12.md`. Próximo passo exige diagnóstico e revisão independente do 422; não retomar dispatch/aprovar/aplicar antes disso.

## 2026-09-12 19:07:47 - correção do recibo de dispatch (Luna integrador)

- Correção documental: foram seis propostas HTTP 201 confirmadas (registros T010 1, 5, 6, 7, 8 e 14) e uma tentativa HTTP 422 (registro 15), não sete propostas criadas. Logs read-only preservam timestamp `2026-09-12T21:59:02.993973923Z`, peer `172.20.0.1:55144` e status 422, mas não body/detail nem request-id; não houve retry.

## 2026-09-12 19:15 - aplicação idempotente T010 (Luna integrador)

- Os seis T010 aceitos foram pré-validados por GET (`proposed`, hash/diff sem drift) e passaram pelo fluxo normal de autorização/aplicação, ambos HTTP 200. Todos retornaram `no_change` e GET final confirmou `version_id=null`; classificação: seis SKIPPED idempotentes, zero APPLIED.
- Contagens antes/depois permaneceram `publications=34`, `versions=81`, `outbox=81`, `notifications=80`; health 200. T010 registro 15 continua devolvido 422; registro 16 e T011 não foram tocados. Evidência consolidada em `docs/execucao/evidencias-dispatch-T010-T011-2026-09-12.md`.

## 2026-09-12 19:18 - revisão do registro 15 e retomada de criação (Luna integrador)

- T010 registro 15 fica `do_not_dispatch`: a revisão aceita identifica dependência de artefato/entidade compatível para Edital 010/2025, enquanto o alvo 15 é 005/2025. O HTTP 422 não será repetido.
- Retomada limitada a criação normal de T010 registro 16 e oito registros T011, na ordem dos manifestos r2 e com as chaves idempotentes documentais. Nenhuma autorização/aplicação é permitida neste gate; qualquer erro ou drift interrompe a sequência.

## 2026-09-12 19:18 - interrupção no conflito de T010/16 (Luna integrador)

- A pré-checagem dos seis T010 anteriores confirmou `no_change`, `result.diff={}` e `version_id=null`. O primeiro novo POST, T010 registro 16, retornou HTTP 409; nenhuma proposta nova foi criada e T011 não foi iniciado.
- Consulta read-only encontrou o mesmo `run_id` já ligado a `tpp-9ea32737dd8f9112a06ced5bb707a36c`, `state=applied`, `version_id=24`. Não houve retry, autorização, aplicação ou alteração de contagens. Evidência consolidada em `docs/execucao/evidencias-dispatch-T010-T011-2026-09-12.md`.

## 2026-09-12 19:21 - aceite T010 e criação controlada T011 (Luna integrador)

- T010 aceito pós-gate: registros 1,5,6,7,8,14 seguem `no_change` sem versão; registro 16 está coberto pela proposta idempotente já aplicada `tpp-9ea32737dd8f9112a06ced5bb707a36c`, versão 24; registro 15 permanece `do_not_dispatch`.
- T011 liberado somente para criação serial das oito propostas normais (17,18,20,21,22,23,24,25), usando `http_payload`/chaves dos manifestos r2. Nenhuma autorização/aplicação será feita neste gate; parar no primeiro erro ou drift.

## 2026-09-12 19:22:15 - criação T011 interrompida (Luna integrador)

- T011 sublotes 01–03 (concursos 17,18,20) criaram propostas `proposed` e tiveram GET 200: `tpp-02c29e4baa1b036eab1d02de59a65c74`, `tpp-e592fd8efd3baebe12b3b76a696a04f3`, `tpp-49afc9246a42a37353b05df1bf11650a`.
- O sublote 04/concurso 21 retornou HTTP 409 sem proposal_id; o gate parou sem retry. T011 22/23/24/25 não foram enviados, e nenhum dos três criados foi autorizado/aplicado. Contagens permaneceram 34 publicações, 81 versões e 80 notificações. Evidência: `docs/execucao/evidencias-dispatch-T010-T011-2026-09-12.md`.

## 2026-09-12 19:30:35 - aplicação idempotente T011 17/18/20 (Luna integrador)

- Os três T011 aceitos foram pré-validados por GET sem drift e passaram por autorização/aplicação HTTP 200. Todos retornaram `no_change`, com GET final `version_id=null`: três SKIPPED, zero APPLIED/FAIL.
- Contagens permaneceram `publications=34`, `versions=81`, `outbox=81`, `notifications=80`; registros 21–25 não foram tocados. Evidência: `docs/execucao/evidencias-dispatch-T010-T011-2026-09-12.md`.

## 2026-09-12 19:32 - T011/21 DO_NOT_RETRY e criação 22–25 (Luna integrador)

- T011/21 fica `DO_NOT_RETRY`, aceite pela revisão diagnóstica `docs/execucao/evidencias/revisao-diagnostico-T011-21-Luna-20260912.json`; dependência explícita: conferir quatro retificações (`EDITAL DE RETIFICAÇÃO Nº01/2026` a `Nº04/2026`), revalidar identidade/revisão e preparar novo run/proposta.
- Liberada somente a criação serial de T011 22, 23, 24 e 25 pelo manifesto corrigido/aceito, com payloads/chaves exatos. Nenhuma autorização/aplicação neste gate; parar no primeiro 409/422/drift.

## 2026-09-12 19:33:02 - criação T011 22–25 concluída (Luna integrador)

- T011 22/23/24/25 criaram propostas `proposed` com GET 200: `tpp-89d123b46f995642fae59e48e0c2ea25`, `tpp-23904639452716008c2fe67f1af38f63`, `tpp-4e99e2ad1f2d8d8bf41150a564e958ca`, `tpp-988abe18c6d18f774bb4688c7656ea86`.
- Não houve approve/apply; contagens permaneceram 34 publicações, 81 versões, 81 outbox e 80 notificações. T011/21 segue `DO_NOT_RETRY` pelas quatro retificações; revisão independente deve decidir autorização/aplicação dos sete pendentes.

## 2026-09-12 19:38:09 - aplicação gate-final T011 22–25 (Luna integrador)

- Os quatro T011 finais foram pré-validados sem drift e passaram por autorização/aplicação HTTP 200. Todos retornaram `no_change`, com GET final `version_id=null`: quatro SKIPPED, zero APPLIED/FAIL.
- Contagens permaneceram `publications=34`, `versions=81`, `outbox=81`, `notifications=80`; health 200. T011/21 continua `DO_NOT_RETRY`, dependente das quatro retificações.

## 2026-09-12 19:45:19 - devolução UI de T010/T011 (Luna integrador)

- As aplicações `no_change` não encerram conteúdo. A validação UI das 14 rotas T010/T011 falhou: todas exibiram CARGO “Pendente de conferência” e os campos `checked` não ficaram visíveis.
- T010 e T011 ficam `DEVOLVIDAS/EM_CORREÇÃO` de pipeline, aguardando diagnóstico de dados/backend. Propostas, IDs e recibos anteriores permanecem preservados como histórico, sem nova publicação ou retry.
- T010/15 permanece `do_not_dispatch`; T011/21 permanece `DO_NOT_RETRY`, dependente das quatro retificações já registradas. Nenhum serviço ou dado foi alterado nesta atualização.

## 2026-09-12 19:51:09 - próximo gate exclusivo T010/ID 1 (Luna integrador)

- T007/T008 permanecem aceitas e T010/T011 permanecem `DEVOLVIDAS/EM_CORREÇÃO`.
- O próximo e único caminho autorizado é: `reviewed_run` persistido com valores novos → proposta com diff material → revisão independente → `apply` → checkpoint/tela → repetição idempotente.
- Não disparar outros registros e não aplicar T010/ID 1 antes da revisão independente do `reviewed_run` persistido e do diff real. Aguardar os artefatos dos executores; sem serviços, banco ou novas mutações neste gate.

## 2026-09-12 20:21:09 - proposta T010/ID 1 aguardando revisão (Luna integrador)

- Smoke dirigido passou 32/32; backup fresco verificado em `/backups/pilot-20260912T231649719Z` (PostgreSQL e operational, 12.343 arquivos). O envelope e o PDF foram importados pelo fluxo padrão: dry-run `validated`; `--apply` executado uma vez, `imported`.
- Run persistido `tp-reviewed-e35d8a7669ed82e4d74b61e97c663ddb` confirma owner 1, `access_open`, external `183`, SHA do artefato íntegro e somente `cargos` com os valores esperados. Proposta `tpp-32d777ecadaaad5a790f95d7d4dd0e05` foi criada HTTP 201, GET confirmado `state=proposed`, `eligible_fields=[cargos]`, diff material, `approved_at=null`, `version_id=null`.
- Health 200 e checkpoint permaneceram `publications=34`, `versions=81`, `notifications=80`, `alerts=1`, `favorites=0`, `concursos=33`. Não houve approve/apply. Próximo gate exclusivo: revisão independente real do run persistido e do diff; depois, somente se aceita, autorização/aplicação serial de ID 1. T010/T011 seguem DEVOLVIDAS/EM_CORREÇÃO; nenhum outro registro pode ser disparado.
- Evidência reproduzível: `docs/execucao/evidencias/T010/evidencia-gate-id1-reviewed-run-proposta-20260912.json`.

## 2026-09-12 20:26:58 - aplicação única do piloto T010/ID 1 (Luna integrador)

- Revalidação final confirmou hash `85093932c509a665b879f5a0b08f7e51b06977011d59692b1290bef727f8bbb2`, `state=proposed`, baseline `cargos=null` e proposta exata. Approve HTTP 200 com `fields=[cargos]`, usuário 1; apply único HTTP 200.
- GET final confirmou `state=applied`, `version_id=82`, diff material `cargos`: `old=null` → Professor Auxiliar, 10 vagas (9 ampla/1 PCD), R$30,53/hora-aula, até 40h. Consulta read-only confirmou exatamente um `ConcursoVersion` e um outbox para a proposta; outbox `delivered`, totais 82/82.
- Health 200; concurso 1 mostra o cargo esperado; checkpoint: 34 publicações, 82 versões, 81 notificações, 1 alerta, 0 favoritos, 33 concursos. Não executar segunda repetição idempotente ainda. Próximo gate: validação UI/tela e, depois, somente a repetição idempotente do ID1; nenhum outro registro.

## 2026-09-12 20:46:44 - replay idempotente T010/ID1 concluído (Luna integrador)

- A API foi reconstruída/reimplantada somente para `observador-pilot-api-1`, com volumes preservados; health 200 e smoke de replay 2/2 PASS.
- Apply único da segunda proposta `tpp-273377777279a608bb4ce91107fae9bc` retornou HTTP 200 com `idempotent_replay=true`, `original_proposal_id=tpp-32d777ecadaaad5a790f95d7d4dd0e05`, `requested_proposal_id` correto e `version_id=82`. Nenhuma nova versão/outbox/notificação/publicação foi criada.
- Checkpoint/DB final: 34 publicações, 82 versões, 82 outbox, 81 notificações, health 200; concurso 1 mantém exatamente um cargo. Subgate T010/ID1 completo. Liberada somente triagem read-only do próximo lote pequeno; não executar novo import/proposal/apply. T010/15 permanece `do_not_dispatch`; T011/21 `DO_NOT_RETRY`.

## 2026-09-12 20:53:54 - aceite independente final T003 (Luna integrador)

- T003 passa a CONCLUIDA/ACEITA após a revisão `docs/execucao/tarefas/revisao-independente-T003-final-ui-20260912-01.md`: suíte dirigida 16/16 e `tsc` passaram; UI real confirmou `/busca` com 33 Seleções e `/concurso/33` após reload.
- A home `CONCURSOS LISTADOS` permanece um resumo distinto e não deve ser tratada como defeito. Nenhum serviço, dado ou gate T010/T011 foi alterado.

## HISTÓRICO SUPERSEDIDO — 2026-09-12 20:56:47 - aceite independente final T006 no escopo executável (Luna integrador)

- T006 passa a CONCLUIDA/ACEITA no escopo executável: persistência, backup+restore isolado, recorrência e offline/T008, conforme `docs/execucao/tarefas/revisao-independente-T006-operacao-Luna-2026-09-12.md` e `docs/execucao/evidencias/T006-recorrencia-2026-09-12.md`.
- Push nativo não é mascarado por dispositivo/emulador externo; backend/API, fixture e deploy internos foram posteriormente aceitos, restando somente dependência EXTERNA de device/emulador e habilitação explícita. Nenhum serviço, dado ou gate T010/T011 foi alterado neste checkpoint.

## 2026-09-12 21:47:15 - gate T009 PostgreSQL/API e proposta T010/ID6 (Luna integrador)

- Fixture PostgreSQL descartável passou schema fresh e legado, upgrade duas vezes, com `token`/`token_fingerprint` nullable. Smoke autenticado A/B passou GET/POST/DELETE: B não herdou token ativo de A; DELETE limpou token/fingerprint e preservou `revoked_at`/`user_revoked`. Push ficou disabled e não houve drain/rede externa.
- API e web foram construídas/reimplantadas somente no piloto; health/web 200, 23 rotas estáticas, volumes preservados e colunas de push nullable. Evidência consolidada em `docs/execucao/evidencias/T010/gate-operacional-ID6-T009-20260912.json`.
- ID6 conferiu envelope SHA `23D7A5AC0E005DEF90FD45C19AF3E6663BB012A7E3F49436907EBD16C329F80C`, owner 1 e artefato pinado. Importação única retornou `imported`; proposta normal única `tpp-b47411064f1b447b5a6f519c5b925f42` retornou HTTP 201/GET 200, `proposed`, hash `8655bd498afcfa7d51e2c3f0e930f3178420d8446edbf7e919eddcfd593114a9`, 11 cargos e baseline nulo. Não aprovar/aplicar; aguardar revisão independente.

## 2026-09-12 22:04:19 - reconciliação pós-apply T010/ID6 e estado T008/T009 (Luna integrador)

- T010/ID6 está ACEITO: aplicação única da proposta `tpp-b47411064f1b447b5a6f519c5b925f42` gerou versão 83, outbox 83 entregue, notificação 82 e 11 microáreas; replay da proposta e reimportação do run foram idempotentes, sem duplicatas. A UI do coordenador em `localhost` permaneceu estável após reload. Evidências: `docs/execucao/evidencias/T010/revisao-pos-apply-ID6-Luna-20260912.json` e `docs/execucao/evidencias/T010/gate-pos-apply-ID6-20260912.json`.
- Snapshot histórico anterior (supersedido pelo aceite ID7 e pela matriz r3): 33 seleções, 32 fontes, 124 cargos, 34 publicações, 83 versões e 82 notificações; naquele ponto ID7 entrava em preparação. Não há limitação geral de “triagem sem importação” no estado atual.
- T009 está aceito em código, fixture PostgreSQL fresh/legado e deploy interno; push permanece disabled/sem envio e a validação nativa externa continua pendente.
- T008 conserva o aceite de sync/favoritos/alertas, mas abre suplemento `EM_CORREÇÃO` para bootstrap SQLite/OPFS no origin `127.0.0.1`, reproduzido pós-deploy; `localhost` passa. Evidência: `docs/execucao/evidencias/evidencia-piloto-T010-ID6-gate-2026-09-13.json`. Não declarar solução antes da nova revisão.

## 2026-09-12 22:17:43 - aceite operacional T008 OPFS/web r5 (Luna integrador)

- O suplemento T008 OPFS/SQLite foi CONCLUÍDO/ACEITO após revisão independente operacional: smoke em duas abas, erro acessível, recuperação por retry sem limpeza e reload estável. O build `BA7C7308…A6143B` foi implantado somente no web/mobile; API, PostgreSQL e Redis não foram reiniciados. Evidências: `docs/execucao/tarefas/revisao-independente-T008-opfs-r5-operacional-20260912-01.md` e `docs/execucao/evidencias/T008-web-redeploy-20260912-221204.json`.
- O handle externo invisível que mantém `127.0.0.1` preso é condição ambiental reproduzida, não defeito interno reaberto. Origin canônico recomendado para o piloto: `http://localhost:13000`; não limpar OPFS/IndexedDB para contornar a condição.

## 2026-09-12 22:50:28 - reconciliação T010/ID7 e T011/ID17 (Luna integrador)

- T010/ID7 foi aplicado/aceito pelo fluxo normal: proposta `tpp-8157df41c8907a5f39cea3aa357c05dc`, versão 84, outbox 84 entregue em uma tentativa e notificação `version_update_84` id 83. GET concurso 7 confirmou o cargo Técnico Legislativo e benefícios após reload; replay da proposta e reimportação do run permaneceram idempotentes. Evidência: `docs/execucao/evidencias/T010/gate-pos-apply-ID7-20260912.json`.
- T010 fica reconciliada com IDs 1, 6 e 7 concluídos/aceitos; IDs 5, 8, 14 e 16 permanecem insuficientes/no_change, sem inferir conteúdo; ID15 continua `do_not_dispatch` por mismatch documental. Snapshot: 33 seleções, 32 fontes, 124 cargos, 34 publicações, 84 versões e 83 notificações.
- T011/ID17 permanece DEVOLVIDO: o PDF primário foi localizado no volume e copiado intacto, SHA `6caf7901...f7e1f`, 1.094.969 bytes e 50 páginas, mas quotas/AC-PcD-CR e rerun independente ainda faltam. Baseline concurso 17 consultado read-only: source 34, external `concursos-em-andamento/prefeitura-municipal-de-cubati-pb`, cargos nulos. Evidências: `docs/execucao/evidencias/T011/T011-ID17-artifact-local-20260912.json` e `docs/execucao/evidencias/T011/revisao-independente-ID17-Luna-20260912.json`.
- Demais classificações do parecer T011 são preservadas: 18/20/22–25 permanecem no_change/insuficientes; 21 permanece `DO_NOT_RETRY` pelo conflito semântico e quatro retificações pendentes. Nenhum novo import/proposal/apply foi executado para T011.

## 2026-09-12 23:12:40 - aceite da matriz de fontes r3 (Luna integrador)

- A matriz r3 foi ACEITA pelo parecer independente: CSV/JSON equivalentes, 99 linhas/números/fontes únicos e enums consistentes. Apontamentos canônicos: `docs/execucao/evidencias/matriz-fontes-99-reconciliada-r3-20260912.csv` e `docs/execucao/evidencias/matriz-fontes-99-reconciliada-r3-20260912.json`; parecer `docs/execucao/tarefas/revisao-independente-matriz-fontes-r3-final-20260912-01.md`.
- Snapshot atual reconciliado: 33 concursos, 32 fontes, 124 cargos, 34 publicações, 84 versões, 84 outbox, 83 notificações e 86 propostas. Overlays confirmados: fonte 19→concurso 1/v82, 17→6/v83, 22→7/v84; fonte 34→17 DEVOLVIDO r2; T010 5/8/14/16 insuficientes e 15 mismatch; T011 17 não parser-ready, 18/20/22–25 insuficientes e 21 `DO_NOT_RETRY`.
- `docs/entrega-fontes-atual.csv` e `docs/tenderproof-product-status.json` permanecem baselines históricos preservados, não estado atual. A matriz r3 continua `authoritative:false`, os overlays não promovem integração source-wide e T007 `reference_only` permanece delimitado.

## 2026-09-12 18:05 - gate de código T008 (Luna integrador)

- A correção da corrida A→B/owner de T008 foi ACEITA pela revisão independente no gate de código/testes: `revisao-independente-T008-user-isolation-20260912-02.md`, `tsc PASS`, 8/8.
- O gate operacional permanece aberto: falta build implantado e corrida real offline→sync cobrindo UI, servidor, favorito e reabertura. Não executar build, restart ou piloto nesta etapa.

## 2026-09-12 18:19 - resultado da integração T007 (Luna integrador)

- Após testes, backup/restauração isolada e deploy, a proposta `tpr-2abf0ea8e7646be2a47aed6318c682f2` foi aprovada/aplicada pelo fluxo normal aos 32 IDs: `applied`, `skipped=[]`, versões 50–81. Evidência consolidada em `docs/execucao/evidencias-integracao-t007-t008-2026-09-12.md`.
- Não marcar T007 como concluída: o GET autenticado da proposta retorna 500 (`KeyError: 'run'`) e as linhas fallback existentes não mostram `provenance.reference_only=true` na leitura, apesar do recibo de aplicação registrar `reference_only=true`. Reparo adicional requer diagnóstico/correção versionada; SQL ad hoc é proibido.

## 2026-09-12 18:31 - resultado real T008 e gate T007 r2 (Luna integrador)

- T008: corrida real DEVOLVIDA. O cliente preservou localmente `VAL-20260912-REAL-01-alert-182522` com `active=false` e o favorito do concurso 33 após API offline/online e reload, mas as consultas read-only ao servidor não localizaram nenhum dos dois até 18:30:15; evidência em `docs/execucao/evidencias-T008-offline-window-2026-09-12.md`. Drenagem de outbox permanece em andamento.
- T007: r2 aceito em código, 18/18; aguardar a correção de T008 antes de novo deploy para evitar conflito. Não publicar T010/T011.

## 2026-09-12 18:37 - redeploy T007 r2/T008 r3 (Luna integrador)

- T007 r2 e T008 r3 passaram os gates independentes e foram reconstruídos/reimplantados serialmente. O contrato T007 no piloto agora responde GET da proposta HTTP 200 e publica `reference_only=true` para os 30 fallbacks; 32 versões e 32 outbox distintos correspondem aos 32 concursos, sem duplicata.
- Health/assets: API HTTP 200, web `/inicio` HTTP 200 com bundle novo, PostgreSQL/Redis saudáveis. Nenhuma publicação T010/T011 foi executada.
- Próximo gate: nova validação real T008 offline→sync/UI/servidor/favorito/reabertura.

## 2026-09-12 18:39 - aceite operacional T008 (Luna integrador)

- PASS read-only após redeploy/reload: alerta id `6` (`VAL-20260912-REAL-01-alert-182522`) está `active=false` no servidor; favorito id `8` para concurso `33` está presente. Checkpoint retornou 2 alertas e 1 favorito; logs API sem erros, com operações 2xx.
- T007 e T008 ficam ACEITAS no quadro operacional. T010/T011 continuam sem publicação.

## 2026-09-12 18:08 - integração interrompida no gate de testes (Luna integrador)

- Reprodução: `C:\Users\gabri\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe -m pytest backend/tests/test_publication_fallback.py backend/tests/test_tenderproof_publication_post.py backend/tests/test_tenderproof_publication_postgres.py` falhou imediatamente com `No module named pytest`.
- Conforme a sequência operacional, nenhum backup fresco, build/deploy, restart, reparo T007 ou publicação foi executado. Retomar somente após disponibilizar `pytest` nesse runtime ou instrução operacional equivalente, preservando o Python solicitado.
