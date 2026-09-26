# Revisão independente — replay T010/ID1 r2

Status: ACEITA.

- `tests/test_tenderproof_publication.py::test_distinct_semantic_replay_returns_original_without_second_version`: PASS. A chave continua sendo hash de `run_id + target` (`concurso_id` em update); o retorno é 200 sem nova `ConcursoVersion`/outbox e contém `idempotent_replay`, `original_proposal_id` e `requested_proposal_id`.
- `test_semantic_replay_divergent_fields_or_stale_baseline_remains_409`: PASS. A implementação exige owner, run, target, estado terminal (`applied`/`no_change`), campos aprovados e valores propostos equivalentes; executa `_assert_baseline` antes de devolver replay.
- Suítes `test_tenderproof_publication.py`, `test_reviewed_run_import.py` e `test_access_birigui_jobs.py` passaram (execução direcionada sem falhas).
- `_owned`/`_check_hash` precedem o replay; colisão de outro owner/target, `applying`/`rolled_back` e divergências permanecem 409 genérico, sem vazamento. O caminho de replay só lê e devolve a proposta original.

Gate: ACEITA. A cobertura específica prova a ausência de nova versão/outbox; notificações não são criadas no replay porque nenhuma mutação nem outbox ocorre.
