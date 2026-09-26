# Parecer independente — bloqueio documental ID16

Data: 2026-09-13. Read-only; não aprovei efeitos nem alterei dados.

## Bloqueio reproduzido

O run canônico `tp-reviewed-1f9a51cc55dc7312c5153645b45ab9bc` foi importado no piloto isolado com `fields=[cargos, prova_data]`, mas a criação de proposta retornou HTTP 422. O estado do catálogo mantém os valores anteriores; o `document_review` continua pendente com um único documento novo: **“Edital 002/2024 - Retificação 01”**, URL `https://anexos.cdn.selecao.net.br/uploads/412/concursos/246/anexos/245c22cb-a262-48d9-8091-f198385143f1.pdf`. A decisão registrada é STOP até decisão normal de revisão; não é falha de parser nem autorização de apply.

O artefato-base do run é o PDF SHA `3503bf29…641deb`, 396.219 bytes/23 páginas. O run reproduz 18 cargos (10 imediatos, 8 CR) e `prova_data=2025-01-12`, mas não contém o PDF/texto da retificação. Portanto não há evidência para afirmar se a Retificação 01 altera cargos, vagas, remuneração, jornada, taxa, requisitos ou data/fase da prova; nenhum efeito deve ser inferido.

## Critério de aceite para o caso preparado

1. Materializar a retificação como artefato com URL, SHA/bytes/páginas e evidência literal; fechar `document_review.pending` somente após leitura/reconciliação.
2. Registrar `effects`/decisão por campo: sem efeito comprovado (no-op) ou diff documentado. Conferir explicitamente os 18 cargos e `prova_data`; se houver mudança, nova proposta deve conter apenas campos alterados, com baseline CAS atual.
3. Reexecutar dry-run, `_revalidate → create_proposal` em store descartável e revisão independente; manter identidade/inscrições e valores não afetados intactos. Só então liberar proposta/approve/apply conforme gates normais.

Decisão atual: **BLOQUEADO** por revisão documental pendente; não liberar importação/proposta de produção nem efeitos.
