# Parecer arquitetural independente — ID16 / revisão documental offline

**Estado: BLOQUEADO até existir um bootstrap preservado; não há autorização para SQL ad hoc, proposta ou publicação.**

## Diagnóstico

`POST /tenderproof/continuous/document-review/{run_id}/prepare` só reusa um `document_effect_case` corrente; se inexistente, abre o detalhe oficial e compara o manifesto vivo. O ID16 tem `current_case=null` e a lista mudou, portanto retorna 409. `select-preserved` também exige um caso já preparado. `import_reviewed_run` persiste apenas `run`/artefato e não cria caso documental.

## Menor contrato seguro

Adicionar função/endpoint autenticado `prepare_preserved` (operador + `_review_run`) que receba a revisão esperada e o item pending exato. Deve:

1. Ler `revision()` no store contínuo e exigir igualdade de owner, source, mode, candidate/external_id, `revision_hash`, manifesto e URL/título/kind do pending.
2. Aceitar somente artefato previamente staged no `TenderProofStore` (ou caminho confinado ao `artifact_dir`), validar URL permitida, SHA-256, `byte_len`, 23 páginas físicas, extração completa sem truncamento/erro e método de extração.
3. Revalidar também o edital principal do run; montar o mesmo payload de `review_cases.prepare` (principal + retificação), sem limpar pending.
4. Persistir somente `document_effect_cases`, com `case_id` determinístico (owner/run/revision/method/SHAs), `INSERT` idempotente e CAS dentro de uma transação; divergência/conflito deve ser 409.
5. Manter `approved_at=null`; nenhuma escrita em `Concursos`, versões, outbox ou notificações. A aprovação posterior continua exigindo decisões literais por página; só depois dela o fluxo normal pode criar proposta.

## Riscos/aceite

Rejeitar URL fora do host/candidato, pending diferente, owner/run cruzado, SHA/bytes/páginas divergentes, método obsoleto, estado applying/approved ou baseline alterada. Testar repetição, concorrência, artefato adulterado, pending removido e confirmação de zero side effects canônicos.

Evidências: `gate-ID16-R2-document-review-blocked-20260913.json`, `ID16-document-review-preserved-replay-20260913.json`, `id16-retificacao-review-draft-20260913.json`.
