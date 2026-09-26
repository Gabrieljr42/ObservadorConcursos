# Matriz de fontes r5 — relatório (13/09/2026)

Status: READY_FOR_MATRIX_REVIEW_R5. `authoritative=false`; sem rede, Docker, piloto, importação, proposta aplicada ou mutação live.

A r5 deriva da r4 e preserva integralmente os accepted overlays v82–v91. O snapshot 33/32/180/34/91/91/90/95 é explicitamente o último snapshot live verificado antes da indisponibilidade do Docker; não foi revalidado nesta rodada.

Concurso 5 foi removido de `insufficient_contests` e separado como `LOCAL_REVIEWED_READY_FOR_IMPORT_PROPOSAL`, source #38 `institutoconsulplan_open`, parser `/5`, run `tp-reviewed-40120e7a2b6662b131075dc416d2cb18`, suplemento de prova `tp-reviewed-1edc6badadc7a40c9fa6a0b2b220bf3a`; não aplicado.

Concursos 18/20/22–25 permanecem blockers específicos; concurso 15 mantém mismatch; concurso 21 permanece `DO_NOT_RETRY`. Garibaldi é concurso 33/source #49, manifest offline de 4 documentos `accepted_with_blocker`, sem certificação estruturada/live.

A matriz mantém 99 rows/números/fontes únicos. A inventory r3 foi incorporada: runtime factory ausente=0; oito `adapter_current=null` históricos têm factory, mas integração não certificada. Nenhum claim source-wide e nenhuma mutação live.

JSON SHA-256: 712c4f6f0f7a9f85bd70245ad96bd242e4842dfcf19a94954c26942b235c366e
CSV SHA-256: 1baf4863afa01b4a4a3c3f3702f3fcd2284cacc16418a818e95d13edc1cb6bb8


R5 R2 namespace correction: matrix row numero=5 is restored exactly to baseline `ibam_open`; concurso ID 5 is represented only by matrix source #38 `institutoconsulplan_open`. Row #38 is `LOCAL_REVIEWED_READY_FOR_IMPORT_PROPOSAL` with explicit T010 run, receipts, supplement, and completeness review pointers; no glob or T004 pointer is used.

JSON SHA-256: 1fd4946d9191eb76138db5cf6ddaed770311eb64719446006fe532e7810d2e86
CSV SHA-256: ae313153cec371adc62452fc2ce0da5cad2d6f7f14a52a3e3e1f56668c5008d4
