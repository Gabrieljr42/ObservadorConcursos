# Evidência de dispatch T010/T011 — 2026-09-12

Data/hora do gate: 2026-09-12 18:58:33–18:59:02 -03:00 (API local; recibos UTC nos logs). Correção documental registrada em 2026-09-12 19:04 -03:00. Operador: Luna integrador/T001.

## Pré-condições

- Backup fresco verificado: `/backups/pilot-20260912T215347930Z-operational`, 11.743 arquivos, `canonical_database_included=false`.
- Restore isolado verificado: `/backups/dispatch-restore-isolated-20260912T215347930Z`, 11.743 arquivos; volumes canônicos preservados.
- Health pré/pós-dispatch: HTTP 200, `status=ok`, `env=local-pilot`.
- Payloads enviados sem alteração, exclusivamente o campo `http_payload` dos manifestos r2. Nenhum endpoint de aprovação ou aplicação foi chamado.

## Resultado serializado

T010 foi iniciado na ordem do manifesto. Seis registros (1, 5, 6, 7, 8 e 14) foram criados como `state=proposed` e confirmados por GET 200, sem `version_id` nem `result`:

| Lote/registro | proposal_id | HTTP/estado | diff resumido |
|---|---|---|---|
| T010-b01/1 | `tpp-5867ec21d73ac4fe89418eb466fa0464` | 201 / proposed | Birigui: titulo, orgao, edital_numero |
| T010-b01/5 | `tpp-d5cbe751714efdcd6782b45548d59fca` | 201 / proposed | Unaí: titulo, orgao, edital_numero, inscrições |
| T010-b02/6 | `tpp-69cc831d24aafc69f0aed3b8ba1dc750` | 201 / proposed | Berizal: titulo, orgao, edital_numero, inscrições |
| T010-b02/7 | `tpp-ed6ee1dcd07ee846ba1f24abd4d9201d` | 201 / proposed | Garça: titulo, orgao, edital_numero |
| T010-b03/8 | `tpp-057a831228de8b054c3726529e7038e4` | 201 / proposed | Reriutaba: titulo, orgao, edital_numero, inscrições |
| T010-b03/14 | `tpp-8bbd941a2970275e237e8fbe522783ec` | 201 / proposed | FAPESE/PRONERA: titulo, edital_numero |
| T010-b04/15 | — | **422 / erro** | `Invoke-WebRequest`: Unprocessable Entity; nenhum proposal_id retornado |

O gate parou no primeiro erro: T010 registro 16 e todos os sublotes T011 não foram despachados. Não houve retry, autorização, aplicação, versão, evento ou notificação novos.

## Prova read-only pós-gate

Checkpoint autenticado às 21:59:25Z: `publications=34`, `versions=81`, `notifications=80`, `alerts=1`, `favorites=0`, `concursos=33`. Comparação com o baseline pré-dispatch: sem alteração em versões, publicações aplicadas, eventos/notificações ou favoritos/alertas. Logs API confirmam seis POST 201 + um POST 422, GET 200 dos seis recibos e nenhum POST `/approve` ou `/apply`. Consulta read-only posterior confirmou os seis GETs; não há body/detail nem request-id preservado no log Uvicorn, apenas peer/porta e timestamp `21:59:02.993973923Z` (`172.20.0.1:55144`).

Próximo gate: diagnóstico independente do 422 de T010-b04/registro 15; somente após revisão independente poderá haver retomada controlada. T010/T011 permanecem sem autorização/aplicação.

## Aplicação autorizada T010 — 2026-09-12 19:14–19:15 -03:00

Revisão real: `docs/execucao/evidencias/revisao-real-propostas-T010-Luna-20260912.json`. Antes de mutar, os seis GETs confirmaram `state=proposed`, hashes e diffs inalterados. O fluxo normal foi usado serialmente, com autorização documental já registrada e sem tocar no registro 15/16 ou T011.

| registro | proposal_id | authorize | apply | resultado | GET final |
|---:|---|---:|---:|---|---|
| 1 | `tpp-5867ec21d73ac4fe89418eb466fa0464` | 200 | 200 | SKIPPED (`no_change`) | `no_change`, `version_id=null` |
| 5 | `tpp-d5cbe751714efdcd6782b45548d59fca` | 200 | 200 | SKIPPED (`no_change`) | `no_change`, `version_id=null` |
| 6 | `tpp-69cc831d24aafc69f0aed3b8ba1dc750` | 200 | 200 | SKIPPED (`no_change`) | `no_change`, `version_id=null` |
| 7 | `tpp-ed6ee1dcd07ee846ba1f24abd4d9201d` | 200 | 200 | SKIPPED (`no_change`) | `no_change`, `version_id=null` |
| 8 | `tpp-057a831228de8b054c3726529e7038e4` | 200 | 200 | SKIPPED (`no_change`) | `no_change`, `version_id=null` |
| 14 | `tpp-8bbd941a2970275e237e8fbe522783ec` | 200 | 200 | SKIPPED (`no_change`) | `no_change`, `version_id=null` |

Contagens antes/depois (checkpoint/API + PostgreSQL read-only): `publications=34`, `versions=81`, `outbox=81`, `notifications=80` em ambos os lados. Health permaneceu HTTP 200. Nenhuma versão, publicação, evento/outbox ou notificação nova foi gerada; os seis resultados são idempotentemente sem alteração.

## Retomada de criação T010/16→T011 — 2026-09-12 19:17:50 -03:00

- GET read-only dos seis T010 anteriores confirmou `no_change`, `result.diff={}`, `version_id=null`.
- T010 registro 15 permanece `do_not_dispatch`: artefato/entidade compatível para Edital 010/2025 não corresponde ao alvo 15 (005/2025); não houve retry.
- A primeira criação da retomada, T010 registro 16 (`run_id=tp-tcj-59347827080f515f92f18723759a231d-1`, chave `t010-id16-3503bf2995deba3d836da647369fd7a83ef2b220de10179900eafa4667841deb`), retornou HTTP 409 Conflict. Nenhum `proposal_id` novo foi retornado; T011 não foi iniciado.
- Consulta PostgreSQL read-only identificou uma entidade existente para o mesmo `run_id`: `tpp-9ea32737dd8f9112a06ced5bb707a36c`, `state=applied`, `version_id=24`, hash `dae646ddaa05f72f8f05724cbd1981eb0e63830ba4caf95b1bf14e663d7c354c`; portanto não houve retry nem criação duplicada. Logs preservam `2026-09-12T22:17:56.274631809Z`, peer `172.20.0.1:38466`, `409 Conflict`.
- Gate parou no primeiro erro. Nenhuma autorização/aplicação foi feita na retomada; T011 permanece intocada. Health/checkpoint e contagens seguem sem mutação.

## Criação T011 interrompida — 2026-09-12 19:22:15 -03:00

Checkpoint antes/depois: `publications=34`, `versions=81`, `notifications=80`, `alerts=1`, `favorites=0`. Nenhum approve/apply foi chamado.

| sublote/concurso | proposal_id | HTTP/estado | diff resumido | erro |
|---|---|---|---|---|
| T011-01 / 17 | `tpp-02c29e4baa1b036eab1d02de59a65c74` | 201 / proposed; GET 200 | título, edital, inscrições | — |
| T011-02 / 18 | `tpp-e592fd8efd3baebe12b3b76a696a04f3` | 201 / proposed; GET 200 | título, órgão, edital | — |
| T011-03 / 20 | `tpp-49afc9246a42a37353b05df1bf11650a` | 201 / proposed; GET 200 | título, órgão, edital | — |
| T011-04 / 21 | — | 409 Conflict | — | criação recusada; nenhum proposal_id retornado |

O gate parou no primeiro erro/drift. T011 22, 23, 24 e 25 não foram enviados. Os três `proposal_id` permanecem apenas `proposed`; revisão independente real é o próximo gate.

## Diagnóstico read-only do 409 T011-04/21 — 2026-09-12 19:29:11 -03:00

Não existe proposta com o `run_id` do manifesto `tp-tcj-d0d2a0870efb5314aaaf97079b11ced0-1` nem com a chave idempotente `t011-21-tp-tcj-d0d2a0870efb5314aaaf97079b11ced0-1-2a074dea`. Para o alvo `concurso_id=21`, a única entidade existente é `tpp-6e9c6c16a1f534dcd6738bdefa0a7f6d`, owner `1`, `state=applied`, `run_id=tpr-5d6ffb1c73be`, `version_id=32`, `proposal_hash=96622747fc6b84b34d4c85c7b7e0e3e940844cf74f655e0abf3ae6994d5497cb`, `approved_at=2026-09-09 22:17:09.45279`, `applied_at=2026-09-09 22:17:09.588601`, resultado `outbox_pending` e diff nos campos `content_hash, edital_numero, inscricao_fim, inscricao_inicio, link_edital, orgao, prova_data, titulo`. Logs preservam somente `409 Conflict` em `2026-09-12T22:22:20.298790228Z`; não houve retry ou mutação.

## Aplicação T011 17/18/20 — 2026-09-12 19:30:35 -03:00

Revisão real `docs/execucao/evidencias/revisao-real-T011-Luna-20260912.json` confirmou os três estados `proposed`, hashes e diffs sem drift antes da mutação. O fluxo normal foi executado serialmente; nenhum registro 21–25 foi tocado.

| registro | proposal_id | authorize/apply | resultado | GET final |
|---:|---|---|---|---|
| 17 | `tpp-02c29e4baa1b036eab1d02de59a65c74` | 200 / 200 | SKIPPED (`no_change`) | `no_change`, `version_id=null` |
| 18 | `tpp-e592fd8efd3baebe12b3b76a696a04f3` | 200 / 200 | SKIPPED (`no_change`) | `no_change`, `version_id=null` |
| 20 | `tpp-49afc9246a42a37353b05df1bf11650a` | 200 / 200 | SKIPPED (`no_change`) | `no_change`, `version_id=null` |

Contagens antes/depois: `publications=34`, `versions=81`, `outbox=81`, `notifications=80`; health 200. Nenhuma versão, evento/outbox ou notificação foi criada.

## Criação T011 22/23/24/25 — 2026-09-12 19:33:02 -03:00

GET read-only dos T011 17/18/20 confirmou `no_change`, `result.diff={}`, `version_id=null`. As quatro propostas seguintes foram criadas serialmente pelo manifesto aceito, sem approve/apply:

| concurso | proposal_id | HTTP/estado | diff |
|---:|---|---|---|
| 22 | `tpp-89d123b46f995642fae59e48e0c2ea25` | 201 / proposed; GET 200 | título, órgão, edital |
| 23 | `tpp-23904639452716008c2fe67f1af38f63` | 201 / proposed; GET 200 | título, órgão, edital |
| 24 | `tpp-4e99e2ad1f2d8d8bf41150a564e958ca` | 201 / proposed; GET 200 | título, órgão, edital |
| 25 | `tpp-988abe18c6d18f774bb4688c7656ea86` | 201 / proposed; GET 200 | órgão, edital |

Contagens antes/depois: `publications=34`, `versions=81`, `notifications=80`, `alerts=1`, `favorites=0`; health 200. T011/21 continua `DO_NOT_RETRY`; nenhuma autorização/aplicação foi feita em 22–25.

## Aplicação gate-final T011 22–25 — 2026-09-12 19:38:09 -03:00

Revisão `docs/execucao/evidencias/revisao-gate-final-T011-Luna-20260912.json` confirmou state/hash/diff sem drift antes de cada mutação. O fluxo normal foi executado serialmente:

| concurso | proposal_id | authorize/apply | resultado | GET final |
|---:|---|---|---|---|
| 22 | `tpp-89d123b46f995642fae59e48e0c2ea25` | 200 / 200 | SKIPPED (`no_change`) | `no_change`, `version_id=null` |
| 23 | `tpp-23904639452716008c2fe67f1af38f63` | 200 / 200 | SKIPPED (`no_change`) | `no_change`, `version_id=null` |
| 24 | `tpp-4e99e2ad1f2d8d8bf41150a564e958ca` | 200 / 200 | SKIPPED (`no_change`) | `no_change`, `version_id=null` |
| 25 | `tpp-988abe18c6d18f774bb4688c7656ea86` | 200 / 200 | SKIPPED (`no_change`) | `no_change`, `version_id=null` |

Contagens antes/depois: `publications=34`, `versions=81`, `outbox=81`, `notifications=80`; health API 200. Zero novas versões, eventos, outbox ou notificações. T011/21 permanece `DO_NOT_RETRY`.
