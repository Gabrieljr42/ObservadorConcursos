# Revisão independente — importador `reviewed_run` T010/ID1

Data: 2026-09-12. **DEVOLVIDA — gate de atomicidade/conflito de artefato.**

Teste dirigido existente: `backend\.venv\Scripts\python.exe -m pytest -q tests/test_reviewed_run_import.py` → 2/2 PASS, cobrindo dry-run, hash/byte_len, pending, repetição e conflito pré-existente. Não há teste PostgreSQL específico; o importador usa `TenderProofStore` SQLite, e a suíte PostgreSQL existente cobre publicação, não este caminho.

Achado P1: `import_reviewed_run` chama `save_artifact_file` antes de `put_run_if_absent`. Em corrida, outro processo pode inserir o mesmo `run_id` após o primeiro `get_run`; o importador sobrescreve o blob pelo mesmo `artifact_id` e só depois detecta `conflito forte durante commit concorrente`. Reprodução read-only em diretório temporário confirmou o run persistido mantendo o SHA antigo enquanto o blob apontava para o SHA novo (`blob_overwrote=True`). Isso quebra atomicidade/proteção de conteúdo. Reservar artifact_id, comparar o blob existente e só gravar após claim transacional; adicionar teste de corrida/rollback.
