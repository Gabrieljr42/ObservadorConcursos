# Revisão independente T007 r2 — GET e `reference_only`

Data: 2026-09-12. **ACEITO — gate de contrato/API e serialização.**

`proposal_view` trata `normalized_link_reference` e `normalized_link_repair` sem tentar validar `payload.run`; o GET de proposta normalizada retorna 200 e preserva `targets`, ação e estado. `ConcursoPublicationOut` expõe `reference_only`; o modelo infere linhas legadas por `provenance.kind=normalized_link_fallback`, enquanto o novo apply persiste o marcador explícito. A suíte em `backend/.venv` passou: `tests/test_publication_fallback.py` + `tests/test_tenderproof_publication_post.py` — 18/18, incluindo GET HTTP e `model_validate` da linha legada.

Gate restante: redeploy/restart serializado e validação no piloto da rota GET e da resposta de publicações; não executei mutação do piloto.
