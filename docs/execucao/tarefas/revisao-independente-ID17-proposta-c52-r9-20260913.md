# Revisão independente — T011/ID17 proposta corretiva r9

Data: 2026-09-13

## Gate proposta — ACEITA (sem liberar apply)

O registro `gate-ID17-r8-import-proposta-20260913.json` identifica a proposta canônica `tpp-c52d279519f1596ed57ab9a1976775b8`, hash `17748a23…c006d2`, estado `proposed`, `concurso_id=17` e baseline versão 85. A comparação independente do envelope/run `60afc4ad…2174` com o PDF e o suplemento de requisitos confirma mudança somente no campo `requisitos` dos cargos 10–15: seis ocorrências, nas quatro correções fechadas `T er→Ter`, `inicia l→inicial`, `atua r→atuar` e `ini cial→inicial`. Códigos, cargos, vagas (79; AC74/PcD5), cotas, remuneração, jornada, demais campos e evidências/proveniência SHA-bound permanecem iguais; os tokens continuam apenas nos snippets literais da fonte. `pytest` direcionado: 36 passed.

## Contagem/controle — ACEITA

Evidência do piloto registra antes/depois `proposals 87→89`, `versions 85→85`, `outbox 85→85`, `notifications 84→84`; logo não houve publicação, fila ou notificação. O endpoint live exigiu autenticação (401), portanto a confirmação operacional é a evidência registrada, não uma mutação/consulta autenticada adicional. Estado final permanece `proposed`; aprovar/aplicar continua bloqueado até o gate próprio.
