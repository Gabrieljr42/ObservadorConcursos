# Revisão independente Luna — ID16 run `tp-reviewed-01c65` (r2)

**Veredito: ACCEPT_DATA_ID16_RERUN_R2**

Escopo somente leitura; nenhum piloto, catálogo, proposta ou serviço foi mutado.

- Conferi diretamente `id16-regenerated-envelope-01c65-20260913.json`, recibo e determinismo. O artefato é `art-0a483f2ba1`, SHA `3503bf2995deba3d836da647369fd7a83ef2b220de10179900eafa4667841deb`, 396219 bytes, PDF de 23 páginas, URL preservada e `reference_only=true`.
- Reprodução própria com `extract_pages_isolated → extract_fields`: 23 páginas processadas sem erro; `cargos` supported (18 cargos, 18 evidências) e `prova_data=2025-01-12` (página 22, 1 evidência). Os 19 snippets, páginas, SHA, URL, método e versão coincidiram exatamente com o envelope persistido.
- Comparação contra `id16-generated-run490.json` confirmou igualdade dos valores, contagens e identidade (source/external_id/concurso/title/detail_url/reference_only); a diferença observada é somente o snippet determinístico da camada isolada, corrigindo o bloqueio de revalidação do `1f9`.
- `derivations_equal=true`, run ID estável nas duas derivações, `eligible_fields` esperado `cargos+prova_data`; não há evidência de relaxamento fail-closed. A grafia fonte `Médio Ginecologista` foi preservada.
- Testes: `pytest tests/test_omni_osvaldo_cruz_integration.py -q` (3 passed); `pytest tests/test_reviewed_run_import.py tests/test_tenderproof_publication.py -q` (34 passed).

`tpp-bdb86b21341b923ed50b5346fcc3ddb6` permanece explicitamente `superseded_never_approve`; qualquer proposta deve ser nova e derivada exclusivamente do run `01c65`.
