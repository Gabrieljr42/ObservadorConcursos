# Revisão independente — `prepare-preserved` ID16

**Veredito: REJECT_ARCH.**

O caminho atende autenticação (`_operator` + `_review_run`), owner/run/source/mode/candidate, pending canônico único, URL requested/final e host, blob local sem rede, SHA/bytes, limites, extração completa com contagem física, revalidação de identidade do edital principal, CAS antes do INSERT, `approved_at=null` e ausência de escrita em catálogo/proposta/versão/outbox/notificação. Os testes dirigidos passaram: suíte `test_tenderproof_document_review_gate.py` **26 passed**; subset preservado **2 passed**.

Falha P1: o `case_id` determinístico em `review_cases.py:299-302` não inclui `METHOD_VERSION` (nem `expected_page_count`). Se o método mudar, `current()` deixa de reutilizar o caso antigo, mas `INSERT OR IGNORE` colide no mesmo ID e a função retorna o payload antigo em `:307-313`, violando replay somente para o mesmo método/conteúdo. Incluir método e contagem na chave e, em colisão, comparar payload integral; divergência deve ser 409. Também tornar `content_type` PDF obrigatório, não apenas condicional.
