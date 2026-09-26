# Revisão independente T010/ID1 — r4 identidade de evidências

Status: ACEITA / ratificação do gate código ID1.

- `backend\\.venv\\Scripts\\python.exe -m pytest -q tests/test_reviewed_run_import.py` → 4/4 PASS.
- `backend\\.venv\\Scripts\\python.exe -m pytest -q tests/test_access_birigui_jobs.py tests/test_tenderproof_publication.py` → 18/18 PASS.
- O teste novo confirma que trocar apenas `evidence_id` mantém `_run_id` e retorna `idempotent`; mudanças em `snippet`, `value` ou `units` alteram a identidade. A normalização recursiva cobre evidências aninhadas; comparação semântica do run também exclui IDs efêmeros/storage path.
- Não houve piloto, quadro ou mutação externa.

Gate: ACEITA; ratifico a aceitação r3. PostgreSQL continua não exercitado neste ambiente sem fixture descartável explícita.
