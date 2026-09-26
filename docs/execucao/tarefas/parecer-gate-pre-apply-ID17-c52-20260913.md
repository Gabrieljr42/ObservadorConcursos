# Gate final pré-apply — T011/ID17 proposta corretiva

Data: 2026-09-13. Revisão read-only; nenhuma mutação executada.

## Decisão: LIBERA approve + apply

A proposta exata `tpp-c52d279519f1596ed57ab9a1976775b8` está `proposed`, no concurso 17, com baseline versão 85 e `eligible_fields=["cargos"]`. A revisão independente r9 confirma que o diff é restrito a seis strings de `requisitos`, nos cargos/códigos 10–15, usando apenas o mapa fechado de correções (`T er→Ter`, `inicia l→inicial`, `atua r→atuar`, `ini cial→inicial`). Não há alteração de nomes, códigos, vagas, AC/PcD, remuneração, jornada, CR, evidências ou proveniência; o texto corrompido permanece somente nos snippets literais da fonte. O envelope/run e SHA estão vinculados à evidência operacional.

O gate ID17 r8 registra `baseline_version=85`, estado `proposed`, sem approve/apply. Após a criação posterior da proposta ID8, o gate ID8 registra contagens `proposals=90`, `versions=85`, `outbox=85`, `notifications=84`, e declara a proposta ID17 intocada. Portanto, fica liberada uma única operação approve+apply para esta proposta, condicionada a CAS do hash/estado/baseline 85; não aprovar/aplicar qualquer outra proposta nem repetir fora de replay idempotente.

Evidências: `docs/execucao/evidencias/T011/gate-ID17-r8-import-proposta-20260913.json`, `docs/execucao/tarefas/revisao-independente-ID17-proposta-c52-r9-20260913.md` e `docs/execucao/evidencias/T010/gate-ID8-import-proposta-20260913.json`.
