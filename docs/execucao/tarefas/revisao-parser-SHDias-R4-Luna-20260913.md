# Revisão independente — parser SHDias R4 (Luna)

Data: 2026-09-13  
Escopo: somente leitura; sem fields/API/DB, rede ou mutação.

## Decisão

**SHDIAS_PARSER_R4_ACCEPT_FOR_INTEGRATION**.

## Verificações

- `shdias_hortolandia.py` fixa `source=shdias_open`, `source_id=51`, `external_id=MTEw/MzA4`, `process_id=00308`, URLs observadas, SHA-256 `F7DE...A750C7`, 697.485 bytes e exatamente 44 páginas.
- `preflight` rejeita identidade divergente, bytes/SHA divergentes, PDF ilegível, contagem de páginas alterada, página vazia e U+FFFD. `parse` exige literalmente título/órgão, edital 001/2026, taxa, prova, remuneração e os dois cargos.
- Resultado reproduz Hortolândia, CPMH 001/2026, cargos 301/302, 12+28=40 vagas, remuneração `3971.37`, taxa `63.25` e prova `2026-09-27`, com evidência por página/SHA.
- O parser é offline/reference-only e não altera o dispatcher genérico. É compatível com a identidade forte do `SHDIASAdapter` (processo derivado do external_id e URL de documento validada); integração deve permanecer explicitamente controlada.

## Execução

`backend/.venv/Scripts/python.exe -m pytest -q backend/tests/test_shdias_hortolandia_r4.py`: **8 passed**.  
`$env:PYTHONPATH='backend'; backend/.venv/Scripts/python.exe -m pytest -q docs/execucao/evidencias/T012/shdias_open/test_proposal_fail_closed.py`: **4 passed** (strong adapter/fallback identity and reference-only envelope).  
`backend/.venv/Scripts/python.exe -m compileall -q backend/app/tenderproof/shdias_hortolandia.py`: **passou**.

Evidência conferida: `docs/execucao/evidencias/T012/shdias_open/parser-r4.json` e artefato PDF local correspondente. Nenhuma rede, API, banco ou catálogo foi tocado.
