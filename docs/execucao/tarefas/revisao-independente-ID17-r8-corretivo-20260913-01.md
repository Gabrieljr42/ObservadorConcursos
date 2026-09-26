# Revisão independente T011/ID17 r8 corretivo

Data: 2026-09-13

## Gate import/proposta — ACEITA CONDICIONAL

Envelope `60afc4ad…2174` e run determinístico `tp-reviewed-b64ff5228138c8157f8c5e4960046c79` conferem receipt/preflight, `owner_user_id=1`, `reference_only=true`, campos `titulo/orgao/edital_numero/cargos`, 27 evidências SHA-bound nas páginas 19–20 e units BRL/40h/vagas. Extração independente do PDF real e `pytest` (`tests/test_contemax_cubati_jobs.py` + `tests/test_tenderproof_publication.py`) passaram 36 testes. Os 27 `cargos[].requisitos` estão não vazios, sem U+FFFD, `T er`, `atuar r`, `inicia l` ou `ini cial`; somente códigos 10–15 mudam pelo mapa fechado. Nomes, vagas, totais, remunerações, jornada e CR não mudam. As seis ocorrências permanecem apenas nos snippets literais da evidência do PDF, corretamente preservados como proveniência.

## Baseline/escopo — ACEITA

O baseline versão 85/legado preserva a corrupção observada; o r8 é novo e não reutiliza o run/proposta antigos. **Liberar somente uma importação do run r8 e uma proposta corretiva de `cargos`; não autorizar approve/apply.**
