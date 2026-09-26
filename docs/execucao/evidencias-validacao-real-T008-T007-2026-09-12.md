# Reconciliação e prontidão — validação real T008/T007

Data da checagem: 2026-09-12 (America/Sao_Paulo). Responsável: Luna validação real.

## Escopo e gate

- Leitura integral de `docs/CONTINUACAO-SOL-LUNA-2026-09-12.md`, `docs/execucao/tarefas/T003.md`, `T006.md` e `T008.md`.
- Não existe `AGENTS.md` no projeto nem em caminho listado por `rg --files`; não há instrução adicional aplicável.
- Sem navegador, mutação, alteração de preferência, limpeza de fila/dados, reinício, SQL, publicação, edição do quadro ou código.
- Gate atual: **AGUARDANDO_LIBERAÇÃO_DO_INTEGRADOR** para assumir a sessão de navegador e executar a prova implantada.

## Estado operacional somente leitura

- `GET http://127.0.0.1:18000/health`: HTTP 200, `status=ok`, `env=local-pilot`.
- `GET http://127.0.0.1:13000/inicio`: HTTP 200; web acessível.
- Quadro: T007 `EM_EXECUCAO`; T008 `EM_REVISAO`; T003/T006 `EM_REVISAO`.
- T007: `evidencias-t007-atomicidade-2026-09-12.md` mantém 32 `normalized_link_fallback` sem `document_added`/outbox coerente; propostas `no_change`/`skipped`. Não validar como resolvido.
- Recibos recentes: `alert-roundtrip-review-20260912T203446668Z.json` falha por cartão desaparecer após toggle; `alert-roundtrip-real-20260912T202832217Z.json` falha `true !== false`; `favorite-roundtrip-real-1789245134655.json` salva/reabre, mas falha aguardando resposta na remoção. `favorite-cleanup-20260912T202000.json` restaurou favorito 0, sem tocar alerta.
- Portanto, código/build existente não equivale a aceite real; a prova implantada ainda está pendente.

## Identificadores isolados preparados

Prefixo único desta corrida: `VAL-20260912-REAL-01`.

- Alerta: nome `VAL-20260912-REAL-01-alert-<epoch>`; usar somente o alerta criado nesta corrida e guardar seu ID/estado inicial.
- Favorito: concurso alvo `33` (Garibaldi), chave de correlação `VAL-20260912-REAL-01-fav-<epoch>`; confirmar previamente ausência no servidor e remover somente o registro criado.
- Vazio transitório/exclusão: `VAL-20260912-REAL-01-empty-<epoch>`; sem reutilizar dados de outros usuários.
- T007 correlação: capturar `proposal_id`, `hash`, `publication_id`, `checkpoint` e timestamp reais retornados pelo fluxo; não inventar evento ou versão retroativa.

## Roteiro após liberação

1. **Alerta offline:** criar com o nome isolado, desligar antes do primeiro envio, reconectar; conferir na UI `aria-checked=false`/ativo=false, fila sem item preso e servidor `active=false` pelo endpoint autenticado.
2. **Favorito:** salvar offline, reconectar e confirmar POST/estado no servidor; recarregar e reabrir; remover pelo controle acessível; confirmar DELETE, ausência após recarga/reconexão e fila limpa.
3. **Vazio/exclusão:** observar leitura local vazia transitória sem apagar criação pendente; após exclusão legítima sem outbox, confirmar que não reaparece e não mostra dados de outro usuário.
4. **Acessibilidade/falha/reabertura:** conferir role/aria/tab-stop do switch e remoção; induzir falha de escrita reversível; confirmar rollback/erro visível e recuperação ao reabrir.
5. **T007:** em read-only, conferir banco (versões/eventos/publicações), API (`/concursos/{id}/publications`), checkpoint autenticado e interface; registrar proveniência `reference_only` quando aplicável.
6. Preservar preferências baseline, anexar recibos novos e remover apenas os IDs isolados criados pelo fluxo normal.

## Prontidão

**Pronto para executar assim que o integrador liberar a sessão/build. Bloqueado agora somente pelo gate de integração; não há autorização para iniciar a prova mutante nesta etapa.**

## Tentativa após liberação — bloqueio de ambiente

Em 2026-09-12, após a liberação explícita do integrador, a sessão CUA foi inspecionada: `apps=[]`, `browsers=[]`. A tentativa de abrir `http://127.0.0.1:13000/inicio` falhou imediatamente com `No browser is available`. Nenhuma ação UI, login, criação, alteração ou limpeza foi executada; preferências e dados permanecem intactos. A prova T008 não foi realizada e não pode ser marcada como aceite operacional até que um navegador seja disponibilizado nesta sessão.

Nova tentativa após handoff do integrador: `getState()` nesta sessão continua retornando `apps=[]`, `browsers=[]`; a aba IAB local não atravessa para este agente. Não foi possível acessar o estado “Dados salvos indisponíveis”, nem executar qualquer ação UI ou mutação.

## Recibos posteriores — classificação

Os recibos `evidencias-T008-offline-window-2026-09-12.md`, `evidencias-redeploy-t007-r2-t008-r3-2026-09-12.md` e o quadro foram reconciliados. O IAB ficou acessível somente ao integrador: `127.0.0.1` falhou por OPFS Access Handle; `localhost` abriu com 33 concursos. Na janela offline, `VAL-20260912-REAL-01-alert-182522` foi criado localmente ativo e desligado (`Value:0`), e Garibaldi/33 ficou SALVO. O primeiro retorno não drenou (reprodução); após r3/reload, drenou: servidor alerta id 6 `active=false`, favorito id 8/concurso 33, checkpoint `alerts=2`, `favorites=1`, GET 200 sem erros. UI mostrou “Salvos 1” e botão acessível `Remover Município de Garibaldi dos salvos`.

**Classificação: ACEITE PARCIAL.** Gate restante, exatamente: (1) executar o clique de remover favorito; (2) recarregar e reconectar; (3) provar no servidor a ausência do favorito e fila drenada; (4) provar leitura vazia transitória versus exclusão legítima. T007 não é reavaliada nesta evidência.

## Revisão operacional final — Luna

Novos recibos fecham o gate residual: o favorito id 8 foi removido pela UI (Salvos 1→0), reload manteve vazio legítimo, servidor confirmou ausência, checkpoint `favorites=0`, `DELETE 204` e `GET 200`. O alerta de teste id 6 foi excluído pela UI; reload preservou somente o alerta original id 1 ativo; servidor confirmou ausência, checkpoint `alerts=1/favorites=0`, `DELETE 204` e `GET 200`.

Cobertura reconciliada: criação offline + toggle false; retry após API recuperada; reload/reopen; isolamento/owner em código; salvar/remover favorito; vazio transitório e exclusão legítima; acessibilidade; preservação de preferência real. **Decisão: ACEITO operacionalmente T008.**
