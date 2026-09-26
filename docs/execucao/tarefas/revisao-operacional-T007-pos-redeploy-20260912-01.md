# Revisão operacional T007 pós-redeploy

Data: 2026-09-12. **ACEITO — gate operacional pós-redeploy.**

Evidência serializada confirma proposta `tpr-2abf0ea8e7646be2a47aed6318c682f2` GET 200/applied, 32 versões `document_added`, 32 outbox/concursos distintos e zero duplicatas. API/checkpoint reportam 34 publicações; leitura read-only das rotas `/concursos/{id}/publications` reproduziu 34 linhas, 30 `normalized_link_fallback` e 30 `reference_only=true`. As quatro restantes são documentos preservados de `raw_data.tenderproof.amendments`, nos concursos 3 e 32 (duas linhas cada), portanto explicam a diferença: duas referências iniciais foram enriquecidas/substituídas por quatro documentos integrais, sem perder histórico.

`/health` respondeu 200. As 30 referências têm proveniência `normalized_link_fallback`/`link_edital`; as quatro linhas não-reference têm origem `raw_data.tenderproof.amendments`. Nenhuma mutação foi feita.
