# Revisão independente R3 — `prepare-preserved` ID16

**Veredito: ACCEPT_ARCH_R3.**

Os bloqueios R1 foram corrigidos. O endpoint continua owner/operator-scoped e sem rede; vincula run, source, mode, candidate, revisão e pending canônico único. Exige MIME PDF, URL requested/final iguais ao pending e host permitido, blob local íntegro (SHA/bytes), limites, extração completa e contagem física exata. Revalida SHA/bytes, extração e identidade do edital principal. Para retificação/prorrogação exige marcador textual e corroboração do candidato/número de edital, rejeitando PDF válido de outro certame no mesmo host.

`METHOD_VERSION` e `expected_page_count` agora entram no digest/case ID; após `INSERT OR IGNORE`, o payload persistido é comparado canonicamente e colisão divergente falha 409. O caso permanece `approved_at=null` e só `document_effect_cases` é escrito. Suíte documental: **26 passed**; subset bootstrap: **2 passed**; `compileall`: PASS. Nenhuma mutação de piloto/catálogo/proposta/versão/outbox/notificação.

Nota não bloqueante: replay do mesmo caso retorna antes de recalcular a contagem solicitada; o artefato já foi validado integralmente e a chave inclui a contagem para novas operações.
