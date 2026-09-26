# Revisão independente T005 r5 — Barra Longa / concurso 32

Data: 2026-09-13. Read-only; sem mutação real.

## Gate final — LIBERA deploy + import/proposta

O run `tp-reviewed-511f58b869b35d449311e6184b2d3dea` está consistente: PDF SHA `a5a7ff5a…ef5a2`, 429261 bytes, preflight passed e duas derivações iguais. O envelope contém somente `cargos`, exatamente 7 microáreas, valores 1 vaga ampla/PcD0, R$3242.00, R$162.10, 40h e requisitos preservados; `cargos.evidence` contém 21 IDs únicos (3×7, cargo e p.23 por microárea), não apenas cargo 7. `owner_user_id=1`, `reference_only=true`.

Receipt/dry-run confirmam store descartável com basename, catálogo realista (`cargos=null`, datas iguais, prova/taxa não publicáveis), `eligible_fields=[cargos]`, baseline null, `apply=false` e `catalogue_mutated=false`. O reparo em `fields.py` (`artifact_dir()/stored.name` somente para relativo; absoluto preservado) permanece presente. Testes próprios: parser/rota relativa **2 passed**; suíte dirigida anterior **39 passed**. Liberação não inclui approve/apply nem piloto.
