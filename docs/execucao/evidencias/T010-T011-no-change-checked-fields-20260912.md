# Evidência exclusiva — T010 id1 / T011 id17: `no_change` e campos checked

Data: 2026-09-12  
Escopo: diagnóstico local, somente leitura; nenhum POST, criação de proposta, mutação de banco/piloto ou retry.

## Causa comprovada

Os pacotes documentais carregam campos revisados fora do contrato de proposta. T010 id1 lista `location, role, requirements, workload, remuneration, vacancies, fee, registration_deadline`, mas seu `http_payload` contém apenas `run_id`, `concurso_id`, `source_id` e `authorization` (`docs/execucao/evidencias/T010/T010-manifesto-propostas-offline.json`). T011 id17 repete o padrão: `checked_fields` inclui `cargos, vagas, carga_horaria, remuneracao...`, enquanto o payload contém somente `run_id` e `concurso_id` (`docs/execucao/evidencias/T011/manifesto-propostas-offline.json`).

O runtime confirmou `ProposalIn.model_fields == [run_id, concurso_id, source_id, authorization]`. `create_proposal` busca o `run_id` persistido e `canonical.resolve/_revalidate` deriva `eligible` exclusivamente de `run.fields` e do artefato preservado; metadados `checked_fields` não são lidos. O `runs` SQLite local não contém esses dois IDs (`rows 0`), portanto não há transferência implícita a demonstrar. A aplicação/versionamento só difere `VERSIONED_FIELDS`, onde `cargos` é o quadro estruturado; `role`, `workload`, `remuneration` e nomes do pacote não viram `cargos` por convenção.

## Conclusão e fluxo correto

Não há defeito no endpoint normal: `no_change` é consequência de um run sem observações estruturadas correspondentes. Para publicar os 14 detalhes, é necessário preparar um novo run revisado a partir do artefato preservado, materializando somente campos comprovados (incluindo `cargos` no formato canônico e evidência/hash), então submeter nova proposta normal e seguir aprovação/aplicação. Não promover pending nem inferir unidade temporal de remuneração. O fluxo de retificação continua sendo o módulo de amendment, não `ProposalIn`.

## Testes/recibo

Ambiente: `backend/.venv/Scripts/python.exe` (projeto ObservadorDeCursos).  
`python -c "from app.tenderproof.publication_router import ProposalIn; ..."` → contrato confirmado; `python -m pytest -q backend/tests/test_tenderproof_dispatch.py` (a partir da raiz) → **10 passed**.
