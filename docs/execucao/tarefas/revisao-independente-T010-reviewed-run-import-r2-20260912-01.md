# Revisão independente r2 — importador `reviewed_run`

Data: 2026-09-12. **DEVOLVIDA — gate de integração TenderProof.**

Suíte: `backend\.venv\Scripts\python.exe -m pytest -q tests/test_reviewed_run_import.py` → 3/3 PASS. Owner obrigatório, `units` preservado em `ExtractedField`, CLI dry-run, hash/bytes, idempotência e conflito de `artifact_id` estão cobertos; `commit_run_artifact` evita o overwrite concorrente do P1 anterior e deixa apenas arquivo órfão possível.

Achado P1: o caminho não é compatível com o contrato de aplicação que afirma alimentar. `_revalidate` exige que o extrator corrente reproduza exatamente valor, trecho, página, URL e SHA de cada `Evidence`; o importador marca todos os campos manualmente revisados como `SUPPORTED/VALID`, mas não executa essa revalidação. Para T010/ID1, cargos/valores estruturados manualmente e URLs `preserved://` não constituem prova de que `access_open` conseguirá reproduzi-los; a proposta pode ser armazenada, porém o endpoint normal recusará o apply. Deve haver teste de integração com `reviewed_run`→proposal/revalidate, ou o contrato deve declarar preservação não aplicável à publicação.
