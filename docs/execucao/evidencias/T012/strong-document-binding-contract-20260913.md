# T012 — contrato de vínculo documental forte (diagnóstico offline)

## Resultado

`_revalidate` não considera a existência de PDF, `reference_only=true`, hash,
evidência manual ou importação bem-sucedida como vínculo forte. O vínculo é um
predicado derivado novamente dos bytes preservados e do concurso canônico.

## Predicado efetivo

Antes do vínculo, o run precisa estar concluído, com `document` e `artifact`,
passar `_assert_document_review_clear` (manifest atual sem pending), e casar
exatamente `source`, `candidate.source`, `candidate.external_id` com
`contest.external_id`, e a URL de detalhe do candidato com `contest.link_pagina`.
O adapter então valida detalhe e todas as três URLs documentais (documento,
artifact requested/final). O documento deve ser `edital`/`consolidado`, sem
rótulo de anexo/resultado/retificação, e `document.url_requested` deve ser a
URL do artifact. O store precisa devolver bytes cujo tamanho e SHA coincidam;
extração deve terminar sem erro/truncamento e `validate_identity` deve retornar
`valid`.

O vínculo forte final é exatamente uma destas alternativas:

1. `document_identity_ids(adapter, candidate, pages) == {candidate.external_id}`;
2. não havendo IDs no PDF, `extract_fields` fresco nos mesmos bytes deve gerar
   `orgao` e `edital_numero`, ambos `supported`, e ambos devem ser iguais ao
   `contest.orgao`/`contest.edital_numero` canônicos.

Título, órgão ou número enviados apenas no envelope/review não substituem a
extração fresca. A falha final é a linha 191 de
`backend/app/tenderproof/publication.py`.

## Reprodução local dos dois bloqueios

Com os PDFs já preservados em `.tenderproof/r30new`/`.tenderproof/r60rec`, o
replay do extrator devolveu:

- W2 `105`: `titulo=supported`, `orgao=supported`,
  `edital_numero=conflict(value=None)`, `document_identity_ids=set()`.
- SHDias `MTEw/MzA4`: `titulo=supported`, `orgao=supported`,
  `edital_numero=unknown(value=None)`, `document_identity_ids=set()`.

Assim, os dois não satisfazem nenhuma alternativa. O campo `edital_numero`
manual do W2 e os campos manuais do SHDias não são usados para formar o
predicado; no SHDias o manifesto sequer contém `edital_numero`.

## Transformação segura

Não há bypass nem relaxamento. Para cada fonte: alocar `Source`/`Concurso` pela
rota normal (não converter `source_number` em ID), importar um
`tenderproof.reviewed-run.v1` com candidato/documento/artifact vinculados,
manter o manifest de document-review aprovado quando houver pending, e
implementar apenas parser/normalizador fonte-específico que reproduza nos
mesmos bytes `orgao` + `edital_numero` (ou um ID explícito realmente impresso
no PDF), com testes fail-closed. Depois executar `_revalidate` e somente então
`create_proposal`.

Document-review/dispatch é necessário quando o manifest está pending, mas sua
aprovação sozinha não cria o strong binding; ainda é necessário o predicado
documental acima.

## Referência aceita

`docs/tenderproof-batch30-publication-live.json` mostra o caso `exame_open`
aplicado: `orgao` e `edital_numero=01/2026` estavam `supported`, coincidiram
com o baseline e a proposta foi aplicada em banco descartável.

Escopo: leitura/replay local; nenhum endpoint, rede, Docker, DB de produção,
piloto ou contrato foi alterado.
