# Continuação do ObservadorDeCursos — Sol coordena, Lunas executam

## Objetivo e função do coordenador

Continue o trabalho existente até resolver as pendências técnicas executáveis e comprovar os resultados no aplicativo. A execução anterior foi interrompida pelo usuário; isso não significa conclusão nem bloqueio técnico.

Você é o coordenador GPT-5.6 Sol. Quero concentrar aproximadamente 99% da execução nos GPT-5.6 Luna. Sua atuação deve ficar na distribuição, priorização, resolução de conflitos e revisão dos resultados. Essa proporção orienta a delegação; não é uma medição de tokens.

Delegue investigação, leitura extensa, implementação, comandos, extração, testes, integração, navegação no aplicativo e documentação aos Lunas. Um Luna independente revisa cada entrega. Você avalia os resumos, confere evidências essenciais e aceita ou devolve a tarefa. Não refaça a investigação dos agentes nem assuma a implementação por conveniência. Se precisar intervir, decida o problema específico e devolva a execução.

Projeto: `C:\Users\gabri\OneDrive\Documentos\Pessoal\Trabalho pessoal\ObservadorDeCursos`.

Os caminhos seguintes são relativos à raiz desse projeto.

## Retomada, sem reiniciar o trabalho

1. Confira os agentes e trabalhos ainda acessíveis nesta tarefa. Reutilize os Lunas existentes quando possível. Não inicie dois responsáveis para o mesmo arquivo ou operação. Uma interrupção do coordenador não comprova que todo comando ou subagente terminou.
2. Delegue ao integrador uma reconciliação curta entre quadro, arquivos de tarefa, evidências recentes, alterações locais e estado do piloto. O alvo é encontrar exatamente onde continuar, não produzir outra auditoria geral.
3. Leia as instruções AGENTS.md aplicáveis. Preserve alterações locais, inclusive trabalho ainda não revisado. Não use reset, limpeza ampla, descarte de alterações ou remoção de volumes.
4. Não releia os dez chats antigos. Não recrie o board nem renumere tarefas existentes.
5. Modelos de execução: `gpt-5.6-luna`, preferencialmente com esforço `medium`. Para novos agentes com modelo explícito, use `fork_turns="none"` e contexto curto, suficiente para a tarefa. Se o modelo estiver indisponível, informe antes de substituir. Não simule delegação.

Distribuição inicial: um Luna integrador, um revisor, um executor backend/documentos, um executor aplicativo e um responsável pela validação de uso real. Reutilize também os responsáveis pelos dados T010/T011 para terminar o material já iniciado. Amplie até 15 apenas quando houver tarefas independentes prontas e capacidade de revisão. Não crie novas tarefas de usuário na barra lateral.

## Leitura mínima por função

- Integrador: `docs/execucao/QUADRO.md`, `DECISOES.md`, `ENTREGA.md`, T001 e as evidências operacionais mais recentes.
- Backend e revisor: T007, `docs/execucao/evidencias-t007-atomicidade-2026-09-12.md` e as revisões relacionadas.
- Aplicativo e validação: T003, T006, T008 e os recibos recentes de falhas de alerta/favorito.
- Dados: T004, T010, T011, `docs/T004-DISTRIBUICAO-32-20260912.md` e documentos preservados específicos.
- Operação: `docs/OPERACAO-LOCAL.md` e `docs/execucao/evidencias-backup-restore-2026-09-12.md`.
- Cobertura das fontes: `docs/entrega-fontes-atual.csv`, `docs/tenderproof-product-status.json` e matriz candidata da T005.

Consulte `docs/PRODUCT-COMPLETION-AUDIT.md` apenas por assunto. Não mande todos os agentes lerem todos os documentos.

## Estado conhecido na interrupção — confirmar somente o necessário

- Garibaldi foi publicado como seleção 33, com 13 cargos e três retificações vinculadas ao histórico.
- Snapshot após Garibaldi: **33 seleções, 32 fontes, 112 cargos, 49 versões e 48 notificações internas**. São números datados; não os fixe como resultado obrigatório de testes futuros.
- Havia 91 adaptadores, 89 configurações habilitadas e 81 fontes com sucesso histórico de detalhe, em um inventário de 99 fontes. Nenhuma tinha integração integral certificada.
- O aplicativo está em `http://127.0.0.1:13000/inicio`; API em `http://127.0.0.1:18000`.
- Correções de apresentação, coleta e sincronização existem no código; parte passou por revisão, mas o aceite real ainda está pendente.
- Backup operacional e restauração isolada conferiram 11.027 arquivos. A restauração PostgreSQL também passou, mas o snapshot testado ainda tinha 32 seleções. O fechamento precisa considerar os dados posteriores.
- T010 e T011 já têm trabalho documental de 16 registros. O quadro ainda os mostrava como PRONTA. T004 ainda mencionava Garibaldi como proposta pronta, apesar da publicação. Corrija esses estados.
- O antigo bloqueio de armazenamento e a suspeita de 3 registros contra 32 não se reproduziram na última sessão verificada. Não os trate como bloqueios atuais sem nova evidência.

## Prioridade imediata: fechar T007 e T008

### T007 — inconsistência de aplicação, histórico e eventos

Estado observado: 32 referências `normalized_link_fallback` persistiram em `concurso_publications`, enquanto a proposta `tpr-4391918df249356b748f6b97691e0756` respondeu `no_change/skipped`, sem as versões `document_added` e os eventos esperados. Determine a causa pelo código e pelas evidências; não atribua a gravação a um processo sem comprovação.

A rota `/concursos/{id}/publications` retorna essas referências. `publications:null` no detalhe base não comprova um bug, pois pode não ser o contrato dessa rota. Confira o contrato efetivo de API, checkpoint e aplicativo.

Antes de outra aplicação documental:
- Reproduza a inconsistência em PostgreSQL isolado, com configuração relevante equivalente à do piloto.
- Corrija a consistência entre persistência, resultado da proposta, versões e eventos.
- Teste aplicação inicial, repetição idempotente, estado parcial preexistente, falha com rollback e concorrência relevante.
- Verifique que um documento novo ou uma retificação na mesma URL não seja descartado por deduplicação indevida.
- Prepare uma reconciliação auditável para as 32 referências existentes. Preserve dados e recibos anteriores; registre a reparação com seu momento e motivo reais. Não invente eventos ou aprovações retroativos.
- Faça revisão independente antes da execução serializada no piloto.
- Confira o resultado no banco, API, checkpoint e interface. Referência de link não é documento integralmente lido: mantenha explícita a proveniência e `reference_only` quando aplicável.

Não use SQL ad hoc para fazer a contagem parecer correta. Se precisar de migração/reparo, entregue procedimento versionado, limitado, revisado e idempotente, com backup antes da mutação.

### T008 — favoritos e alertas online/offline

Já foram observados: alerta criado e desligado offline chegando ativo ao servidor; dificuldade na primeira abertura de Salvos; falha na remoção de favorito. Há correções propostas e revisadas, mas isso não substitui a prova da versão implantada.

- Teste criar alerta offline, desligá-lo antes do primeiro envio, reconectar e comprovar `active=false` na interface e no servidor.
- Teste salvar e remover favorito, recarregar e reconectar; ele não pode reaparecer nem ficar preso na fila.
- Teste leitura local vazia transitória e exclusão legítima no servidor. Não preserve indefinidamente itens fantasmas nem dados de outro usuário.
- Teste estado acessível do controle, falhas de escrita e reabertura.
- Preserve as preferências reais existentes. Use casos identificáveis e remova somente dados criados para teste pelo fluxo normal.
- Execute a prova no build implantado e registre os recibos. Se o teste falhar, devolva a tarefa com reprodução específica.

Enquanto essas prioridades estiverem abertas, mantenha novas publicações documentais suspensas. Dados e outras frentes independentes podem avançar dentro dos lotes já abertos.

## Evitar acúmulo de pesquisas e tarefas sem fechamento

Não abra T012 nem novo lote de fontes enquanto T007/T008 não tiverem aceite real e os trabalhos T003–T006 já entregues não estiverem corretamente classificados. T009 pode permanecer esperando a dependência demonstrada.

T010/T011 devem concluir somente os casos já atribuídos. Não iniciem outra pesquisa ampla, extração ou download sem necessidade concreta. Separem campos conferidos dos ainda pendentes e deixem propostas prontas para revisão quando o fluxo puder recebê-las.

Depois do fechamento técnico imediato, publique e valide primeiro o material já preparado em T010/T011. Divida em sublotes pequenos por registro: um caso pronto pode avançar sem esperar todos os 16. Não encerre a tarefa de um registro apenas com um relatório de extração.

Cada entrega de conteúdo deve chegar a:
**evidência → extração → conferência independente → proposta → aplicação autorizada → sincronização → aplicativo**.

Só depois distribua novas fontes usando a matriz existente. Priorize registros úteis e atuais sem apagar o histórico; preserve corretamente seleções antigas e tipos distintos de contratação ou bolsa. Não confunda salário mensal com hora-aula, prestação de serviço, benefício ou taxa.

## Quadro persistente e responsabilidades

Reutilize `docs/execucao/QUADRO.md`, `DECISOES.md`, `ENTREGA.md` e `tarefas/Txxx.md`.

- Somente o integrador edita o quadro geral; cada executor mantém seu arquivo de tarefa.
- Reconcilie os estados na retomada e depois de cada entrega, bloqueio, transferência ou aceite. Use data/hora real de atualização.
- Cada tarefa registra resultado esperado, responsável, arquivos reservados, estado, evidências, revisão, próximo passo e bloqueio preciso.
- Diferencie código implementado, revisão aprovada, build implantado e comportamento comprovado. CONCLUIDA exige o aceite aplicável, não apenas código pronto.
- Corrija a lista de pendências em ENTREGA.md conforme as provas novas. Preserve evidências anteriores como histórico, sem apresentá-las como situação corrente.
- O quadro deve ser breve e permitir retomada sem releitura de chats. Não crie uma segunda estrutura de gestão.

Os agentes compartilham arquivos e serviços. Um proprietário por arquivo; delimite faixas quando necessário. Integração, builds, reinícios, migrações e publicações no piloto são serializados pelo integrador. A sessão de navegador usada para testes também tem um responsável por vez.

## Autonomia, preservação e orçamento

Há autorização para corrigir o projeto e publicar no piloto os campos documentalmente conferidos pelo fluxo normal de proposta, autorização e aplicação. Registre revisão automatizada como automatizada; nunca como leitura humana.

Preserve catálogo, histórico, credenciais, volumes, alterações locais e serviços Docker de outros projetos. Não amplie publicação para hospedagem externa nem envie mensagens a terceiros. Não contorne autenticação, desafios ou validação TLS.

Solari: limite acumulado autorizado de US$20; última reserva conhecida de US$5,26, com cobrança efetiva não conciliada. Consulte o controle persistido antes de gastar. Não reinicie o orçamento nem repita tentativas pagas sem alternativa concreta. Registre e encerre as sessões utilizadas.

Ausência de adaptador é trabalho interno. Só classifique como externo um impedimento específico comprovado. Push pode ter implementação interna pendente além de credenciais/dispositivo: separe essas duas coisas e conclua a parte executável.

## Economia e revisão

- Contexto curto por agente; arquivos completos e logs extensos ficam no repositório.
- Mensagens ao Sol: tarefa, resultado, evidência, teste, bloqueio e próximo passo, preferencialmente em até 150 palavras.
- Não encaminhe todos os comandos, PDFs ou transcrições ao coordenador.
- Use espera por conclusão; evite consultas e mensagens repetidas sem mudança.
- Testes direcionados durante o desenvolvimento; integração proporcional ao lote. Não repita suítes aprovadas sem mudança ou preocupação concreta.
- Revisão independente por Luna antes do aceite. O Sol examina os pontos essenciais e decide; não executa outra revisão completa em paralelo.
- Se houver duas devoluções pelo mesmo defeito, pare a repetição e produza uma reprodução mínima com diagnóstico. Reatribua o problema se necessário.
- Ao usuário, reporte mudanças verificadas e bloqueios relevantes. Não apresente intenção, pesquisa ou criação de tarefa como entrega.

## Encerramento

Continue além de T007/T008: conclua o material preparado, as pendências internas do quadro e os próximos lotes viáveis das fontes. Não declare integração completa das 99 com base em amostras.

Antes de encerrar:
- Quadro e relatório reconciliados; nenhuma tarefa interna executável esquecida.
- Aplicações, histórico, eventos e sincronização coerentes, sem duplicação.
- Aplicativo validado com as alterações implantadas, inclusive fluxo offline.
- Dados tratados e documentos corretamente visíveis; campos restantes classificados com evidência.
- Backup atualizado após as aplicações finais, com recuperação verificada proporcionalmente às mudanças.
- Matriz das 99 fontes consolidada, distinguindo cobertura parcial de integração comprovada.
- Dependências externas especificadas com impacto e condição de retomada; trabalho interno restante permanece explicitamente pendente.

Não espere indefinidamente por sites indisponíveis ou recursos que o usuário não forneceu. Conclua o trabalho independente e informe esses limites, sem afirmar cumprimento de critérios que ficaram bloqueados.

Entrega final curta: antes/depois, correções aceitas, testes reais, estado operacional, pendências externas e links para aplicativo, quadro e evidências. Não prometa percentual de economia de tokens sem medição confiável.

**Comece delegando a reconciliação do quadro e a retomada de T007/T008. Preserve as entregas anteriores, feche os defeitos atuais e transforme os dados já preparados em resultados no aplicativo.**
