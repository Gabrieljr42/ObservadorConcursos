# Revisão independente T005 r3 — Barra Longa / concurso 32

Data: 2026-09-13. Read-only; sem deploy, importação real ou mutação.

## Gate deploy — ACEITA

`fields.py` agora resolve `storage_path` relativo por `artifact_dir()/basename`, preserva caminho absoluto e mantém o parser SHA/bytes-pinado fail-closed. O roteamento continua restrito a `elo_open` + externo `129`; não há fallback genérico. Suíte própria: `38 passed` (`test_barra_longa_parser`, `test_tenderproof_publication`, `test_reviewed_run_import`).

## Gate import/proposta — DEVOLVIDA

O run `tp-reviewed-d74dc56d2ed14981d4e2fbee2d913c15` preserva PDF SHA `a5a7ff…ef5a2`, 429261 bytes, 7 microáreas, valores canônicos e 21 evidências únicas (p.18+p.23), com shape compatível. Porém o receipt/proposta registra `eligible_fields=[cargos, inscricao_inicio, inscricao_fim, prova_data, taxa]`, não `cargos` único como exigido pelo gate; não há reprodução independente de `_revalidate→create_proposal` demonstrando baseline null e esse escopo. Regerar receipt/proposta isolada com o store descartável, basename relativo, `cargos` único e baseline null; só então liberar import/proposta. Nenhum approve/apply.
