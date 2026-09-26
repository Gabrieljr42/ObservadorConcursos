# Relatório de alterações — matriz de fontes r4 R2 (2026-09-13)

Status: READY_FOR_MATRIX_REVIEW_R2.

A matriz mantém a reconciliação da r3 e somente overlays aceitos. Não houve alteração de baselines, documentos centrais ou piloto.

Snapshot: 33 concursos; 32 fontes de catálogo; 99 linhas/fontes configuradas; 180 cargos; 34 publications; 91 versions; 91 outbox; 90 notifications; 95 proposals; push devices/deliveries/attempts 0/0/0.

A reconciliação read-only de catálogo, detalhes e DB confirmou 180 cargos. A regra canônica é SUM(len(cargos)), tratando cargos=null como zero. Os 14 IDs nullable são 31,29,28,26,25,24,23,22,21,20,18,15,5,2. O total 194 foi apenas diagnóstico ingênuo que contou null como uma entrada e não é estado vivo. Evidências: docs/execucao/evidencias/T010/reconciliacao-cargos-180-vs-194-20260913.json e docs/execucao/evidencias/revisao-desvio-cargos-api-194-vs-db180-Luna-20260913.json.

Overlays com gate/UI específico: fonte19->concurso1 v82; fonte17->6 v83; fonte22->7 v84; fonte34->17 v86; fonte45->8 cargo v87/prova v88; Barra Longa fonte47/elo_open->32 v89; fonte76->14 v90; fonte18->16 v91. As demais linhas preservam ponteiros baseline.

Preservações: insuficientes concursos 5,18,20,22,23,24,25; concurso15/fonte6 identity mismatch; concurso21 DO_NOT_RETRY. bdb86 permanece NEVER_APPROVE_NEVER_APPLY como política de proposta. CSV e JSON foram conferidos com 99 linhas, IDs/fontes únicos e colunas da r3.

