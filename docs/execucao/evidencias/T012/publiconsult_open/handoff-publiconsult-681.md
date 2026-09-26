# T012 handoff — `publiconsult_open` / fonte 56

**Estado:** `PROPOSTA_PRONTA` para revisão e integração; não aprovada/aplicada.

Foi reutilizado um único run/documento preservado, sem rede, API, Docker, SQL ad hoc, piloto ou escrita compartilhada. O `PubliconsultAdapter` confirmou o candidato `external_id=681`, rota oficial de detalhe, título/identidade e 15 documentos; escolheu unicamente **Edital de Abertura de Inscrições** (Votuporanga, Processo Seletivo 1/2026). O edital comprova contratação temporária sob Regime Administrativo Especial, duas funções, 20 + CR cada, remunerações, jornadas, requisitos, taxas e data prevista de prova. Não é bolsa/financiamento.

Artefatos: `reviewed-envelope-publiconsult-681.json`, `receipt-publiconsult-681.json`, `provenance-publiconsult-681.json`, `fail-closed-tests-publiconsult-681.json`. Os seis testes do `PubliconsultAdapter` passaram; guards rejeitam identidade, documento, vazio e ambiguidade inválidos.

**Handoff canônico ao integrador:** `concurso_id=null` é intencional neste artefato pré-alocação; `source_number=56` permanece somente na proveniência/recibo. Alocar o ID local pela rota normal e injetá-lo no envelope antes de `ReviewedRun.model_validate` e do dry-run. A validação parcial passou (JSON, 7 `ReviewedField` e evidências em listas); a validação integral fica bloqueada apenas pelo ID nulo. `external_id=681` é a identidade Publiconsult, não ID local. `reference_only=true`; nenhuma mutação foi feita.
