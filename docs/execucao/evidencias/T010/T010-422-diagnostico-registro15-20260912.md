# T010 — diagnóstico read-only do 422 no registro 15

Data: 2026-09-12. Escopo: `T010-b04`, registro 15, run `tp-tcj-321b30660a7e58fa918a4fb2839e6cd9-1`. Nenhuma chamada ao piloto, retry, alteração de concurso ou aplicação foi feita.

## Reprodução

Foi reconstruído um fixture SQLite isolado usando o PDF preservado `docs/execucao/evidencias/T010/id15.pdf` (SHA do manifesto `5dad1b02870a98e5e85217547f3d0cd57fa7d89b55ce3e5aaa444b5f13163dac`), fonte `ibade_open`, candidato externo `99`, detalhe `https://portal.ibade.selecao.site/edital/ver/99`, artefato oficial S3 do índice e alvo catalogado `concurso_id=15`. O envelope `ProposalIn` já havia passado; a execução direta de `canonical.resolve(..., target_id=15)` reproduziu HTTP 422 em `_revalidate`.

Comando:

```text
cd backend
.venv\Scripts\python.exe -m pytest -q tests/test_t010_record15_diagnosis.py -s
1 passed
```

## Causa

O alvo catalogado no snapshot é `edital_numero=005/2025`, enquanto o PDF preservado identifica explicitamente **Edital 010/2025** (página 1; também aparece como `Edital 010 /2025` nas páginas). O extrator reproduzido não obteve `orgao` nem `edital_numero` suportados (`unknown`), e o PDF não forneceu um identificador externo `99` reconhecível por `document_identity_ids`. A guarda correta falha com:

`TenderProof: vínculo documental forte ausente (código explícito ou órgão e edital correspondentes)`.

Portanto o 422 é incompatibilidade de dados/artefato, não erro do envelope HTTP nem defeito comprovado de backend. Não é seguro afrouxar a guarda para aceitar apenas URL/ID do candidato.

## Ajuste proposto ao pacote (não aplicado)

Devolver o registro para reconciliação documental: confirmar no portal se o alvo 15 deve ser `005/2025` ou `010/2025`; corrigir o binding do pacote/manifesto e gerar novo run/artefato ou nova proposta com SHA correspondente. Manter os campos já `checked`, `reference_only=true` e lacunas (`quantidade`, `taxa`, remuneração/jornada restante) sem promoção. Gate: revisão independente dessa reconciliação antes de qualquer retry.
