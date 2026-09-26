# Parecer independente — replay preservado ID16

Data: 2026-09-13. Revisão read-only; nenhum piloto, serviço, rede ou catálogo foi alterado.

## Veredito: REJECT

O patch em `backend/app/tenderproof/review_cases.py` faz `prepare()` consultar primeiro o caso aberto do mesmo `owner/run`, exige revisão e método atuais, URL do documento igual a `artifact.url_requested/final`, host limitado ao detalhe/cópia principal e bytes não vazios com `byte_len`/SHA válidos. O caso é devolvido sem download; o `approve()` usa CAS da revisão, mantém `field_changes` pendente e o no-op só limpa `document_review_state`, sem criar publicação.

Checks executados: `backend\\.venv\\Scripts\\python.exe -m pytest -q backend/tests/test_tenderproof_document_review_gate.py backend/tests/test_tenderproof_review_cases.py backend/tests/test_tenderproof_document_selection.py backend/tests/test_tenderproof_review_drafts.py` — **59 passed**; `compileall` do módulo — PASS. A evidência `docs/execucao/evidencias/T010/ID16-document-review-preserved-replay-20260913.json` confirma 22 testes do gate e ausência de mutação.

Bloqueio: o replay retornado por `current()` não verifica `payload.identity == identity(run)` nem que cada `document`/URL/identidade/owner/source/candidate seja exatamente o item do `revision.pending` do mesmo run. Verifica somente `owner/run`, igualdade do objeto `revision` e método; portanto um caso persistido com revisão válida, mas payload documental divergente (inclusive documento+artefato em URL alternativa do mesmo host), poderia ser reapresentado como revisão legítima. Os testes atuais cobrem host/URL divergentes apenas fazendo o caminho normal falhar; não provam rejeição fechada de payload cruzado nem no-op sem contagens de versão/outbox/notificação.

Reparo mínimo: antes de retornar o caso, validar identidade do payload e do documento contra `identity(run)` e `revision.pending`/manifest do mesmo run, URL exata permitida e vínculo do artefato; adicionar testes cross-user/source/candidate, URL alternativa e aprovação no-op com contagens inalteradas. Até então, não liberar `ACCEPT_DEPLOY_AND_OPERATE`.
