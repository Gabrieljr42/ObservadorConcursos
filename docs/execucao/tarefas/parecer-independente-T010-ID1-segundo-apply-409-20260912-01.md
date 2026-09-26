# Parecer independente — segundo apply T010/ID1

Status: DEVOLVIDO para correção de contrato de idempotência (sem dano de dados).

O 409 é causado por `publication.py:496`: o `operation` é hash de `run_id + concurso_id`; a primeira proposta aplicada já ocupa `PublicationProposal.applied_observation` (coluna `unique`), então uma segunda proposta distinta para o mesmo run encontra `previous` e lança `HTTPException(409)`. O guard é seguro: a proposta secundária permanece `approved`, não há nova versão/outbox/notificação e ownership/hash já foram validados por `_owned`/`_check_hash`. Também preserva concorrência: antes de existir vencedor, o CAS/unique continua podendo devolver 409.

Isso, porém, não satisfaz o contrato operacional documentado (repetição idempotente/no_change): o teste existente cobre apenas repetir a mesma proposta, que retorna 200 após `applied`; não cobre proposta distinta com o mesmo `run_id`. O erro não devolve referência ao `previous`.

Correção mínima: quando `previous` pertence ao mesmo usuário e tem o mesmo `run_id`, `concurso_id` e operação, retornar 200 com `proposal_view(previous)` (ou resposta `no_change` explicitamente contendo `original_proposal_id`/`version_id`), sem alterar a proposta atual nem criar efeitos. Para owner diferente, manter 409/404; não revelar a proposta. Adicionar teste de segunda proposta aprovada, repetição e concorrência, verificando uma versão/outbox e zero notificações adicionais.
