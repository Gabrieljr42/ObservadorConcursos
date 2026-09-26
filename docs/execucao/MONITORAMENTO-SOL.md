# Monitoramento periódico do Sol

- Automação: acompanhar-execu-o-do-sol, a cada duas horas; permanece ativa.
- Tarefa: Continuar entregas do ObservadorDeCu, 01a09765-5865-7fe3-bbd5-ebff0e32366d, host local.
- Última inspeção: 2026-09-13 17:08 UTC / 14:08 Brasília.
- Cursor Sol: 2d04ec42-5988-4100-a642-a6f50a06fe4c:7. Snapshot principal ativo e sem mensagens recentes expostas; arquivos e tarefas dos Lunas demonstram atividade.
- Cursor integrador: 783791b1-3299-4d63-ae7b-a3825cf98811:6 (thread 01a09767-294e-7da1-b0e2-6dd1da4db2ae).
- Cursor revisor de dados: 5716d9c6-0ed7-4092-8a8f-8e2775c53c27:6 (thread 01a0976a-b65c-7bd1-acae-d5cbc8ad29f7).

## Prioridade vigente

T012 amplia fontes distintas com seleções reais publicadas: base 32, primeiro marco 40. Não contar adapters, preparação local ou cargos adicionais de fontes existentes como novas fontes. Sol coordena; Lunas executam; integrador publica sequencialmente sem esperar o lote inteiro. Os conflitos documentais dos concursos 15/21 permanecem preservados.

O quadro registra dez executores de fontes, dois revisores, um responsável operacional e um integrador; atribuição não significa dez executores ativos continuamente. Nesta inspeção o integrador estava ativo na preparação documental KLC R7, e o revisor de dados havia concluído a revisão Publiconsult R14. Não foi criado outro coordenador.

## Estado verificado

Checkpoint autenticado em 17:08:31 UTC: 35 seleções, 34 fontes, 188 cargos, 34 publicações, 93 versões, 92 notificações, zero favoritos e um alerta. Progresso desde 15:08: +1 seleção, +1 fonte e +6 cargos. T012 soma duas fontes novas publicadas (SHDias/source51 e CPCON/source35); faltam seis fontes para o primeiro marco de 40.

CPCON concurso35 foi aplicado às 16:34 UTC com seis cargos, versão/outbox93 e notificação92. Evidência UI R13 confirma início/busca/detalhe, reload e segunda sessão, identidade e seis cargos com R$3.768,36, sem inventar datas ausentes. Arquivos lidos: T012/cpcon_open/ui-validation-r13-20260913.md e referência live-apply-receipt-r13-20260913.json. SHDias concurso34 mantém os dois cargos e aceite UI R8 anterior; não repetir a validação sem regressão. O monitor verificou API/checkpoint, sem operar navegador ou serviços.

Publiconsult R14 repetiu HTTP422 às 17:01 UTC, apesar do aceite local; document-review fechado e nenhuma proposta persistida. Há diagnóstico novo R15 às 17:05: os valores, artefato e páginas coincidem, mas os três snippets persistidos diferem da saída do parser ativo. A comparação exata em _reproduced_evidence bloqueia título/órgão/edital. O diagnóstico reproduziu essa diferença (1 teste + 7 de regressão registrados), delimitou a correção de geração/persistência das evidências e a encaminhou ao bundle R17. Isso ainda é diagnóstico local, sem correção implantada ou nova fonte. Evidências lidas: T012/publiconsult_open/diagnostico-evidence-reproduction-r15.json e -receipt.json. UFU R10 também permaneceu bloqueada em422; a mesma causa não está comprovada para UFU.

FAFIPA R11 produziu proposta com zero cargos, embora o envelope previsse14; foi corretamente bloqueada e rejeitada no R12, sem publicação incompleta. O bundle R17 registra parser com14 evidências de cargos, sete campos e testes locais19+83, pronto para revisão independente, ainda sem deploy/live. Arquivo lido: T012/fafipa_open/fafipa-backend-bundle-r17-20260913.json. A reconciliação antiga196/182 já estava resolvida; não abrir nova auditoria por ela.

KLC mudou de bloqueio geral409 para diagnóstico concreto: o documento pending é uma retificação, distinta do edital principal. Pacote R7 e revisãoR8 existem; integrador executando a preparação exata, ainda sem aprovação/proposta/publicação comprovada. APTA e Avança SP têm correções documentais no fluxo local; não assumir deploy ou aceite live. Avalia/EPL seguem com bloqueios documentais; W2 permanece histórico excluído. Outras candidatas aceitas localmente continuam pendentes de publicação verificável.

Docker foi recuperado às10:35 UTC por pedido explícito do usuário; login/checkpoint estão funcionando nesta inspeção. A recuperação não certificou o restore PostgreSQL final. WSL configurado com1CPU/2GB; operações pesadas permanecem serializadas. Unaí/ID5, certificação documental Garibaldi, restore e push nativo mantêm pendências próprias sem reter toda a expansão. Aceites anteriores T007/T008 permanecem delimitados;34 publicações não significam34 PDFs preservados.

## Orientação e decisão nesta inspeção

Entre as inspeções, ao responder ao usuário sobre outra tarefa Sol, foi enviada orientação para reutilizar um Luna no caminho real de criação/revalidação que falhava em UFU/Publiconsult, verificar antes de generalizar a causa e avançar fontes independentes. Não repetir essa orientação agora: o diagnóstico R15 responde ao pedido, CPCON foi publicada e KLC segue em execução independente.

Nenhuma mensagem ao Sol nesta rodada. Quadro e entrega registram os bloqueios recentes e a publicação CPCON com evidências; não há conclusão falsa nova identificada. O monitor alterou somente este registro, sem implementação, testes próprios, reinício ou edição do quadro do integrador. Não há ação indispensável do usuário nem motivo para alerta nesta rodada.

## Próxima inspeção

Verificar se a correção Publiconsult reproduz exatamente a evidência pelo caminho ativo antes de outra proposta; acompanhar FAFIPA com os14 cargos preservados, desfecho KLC e avanço de fontes independentes. Distinguir bundle/revisão local de deploy/proposta/aplicação/API/UI. Evitar orientações ou revisões repetidas sem diagnóstico novo. Manter a automação até entrega comprovada e pendências residuais honestamente classificadas; permanecer silencioso quando não houver mudança que exija atenção do usuário.
