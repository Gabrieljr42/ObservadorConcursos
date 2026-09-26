# Revisão independente final T010/ID16 — OMNI/246

Data: 2026-09-13. Read-only; sem deploy/importação real/aplicação.

## Gate — LIBERA deploy + import/proposta

O parser `omni_osvaldo_cruz_jobs.py` e o roteamento `fields.py` estão exclusivos para `omni_open`/`246`, com SHA `3503bf…41deb`, 396219 bytes, 23 páginas, preflight estrito, U+FFFD/SHA/estrutura fail-closed e literal `Médio Ginecologista` preservado. Extração direta reproduz 18 cargos, 10 vagas imediatas, 8 CR, jornadas 10/20/40h, remunerações/taxas/requisitos e `prova_data=2025-01-12`; duas derivações conferem semanticamente (`04892df4…e07872e7`), evidências estão SHA-bound. `extract_fields` com basename fiel sob `artifact_dir` retorna `cargos` e `prova_data` supported, preservando órgão/edital/inscrições; receipt confirma store descartável e eligible exatamente `[cargos, prova_data]`.

Testes ID16/T005/ID17/import/publication: **47 passed**. A tentativa adicional com ID8 teve 18 pass e 2 falhas por fixture ausente `docs/execucao/evidencias/T010/id8.pdf`, não por ID16. LIBERA apenas deploy serial e import/proposta; approve/apply permanecem fora deste gate.
