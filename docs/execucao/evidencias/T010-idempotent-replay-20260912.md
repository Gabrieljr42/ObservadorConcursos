# T010 — replay idempotente de aplicação

Diagnóstico/correção local, sem piloto, quadro ou sincronização.

`apply_proposal` mantém a chave de operação existente (`run_id + target`). No
ramo em que já existe `applied_observation`, agora retorna HTTP 200 somente
quando a proposta solicitante e a original têm o mesmo owner, run, concurso,
estado terminal (`applied`/`no_change`), conjunto de `approved_fields` e
valores `proposed`; a baseline solicitante também precisa continuar atual.
Retorna a visão da proposta original com `idempotent_replay`, IDs original e
solicitante. Não cria versão/outbox/notificação nem toca o concurso. Qualquer
divergência, proposta `applying`/`rolled_back`, owner/target diferente ou
baseline stale permanece 409 genérico.

Teste: `backend/.venv/Scripts/python.exe -m pytest -q tests/test_tenderproof_publication.py -k "semantic_replay or concurrent_duplicate"` → **3 passed**.
