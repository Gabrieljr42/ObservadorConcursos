# Evidência T010/ID6 — validação pós-apply

## Observação UI complementar — coordenador CUA

Esta seção é explicitamente `coordinator_cua_observation`, não uma captura independente desta sessão. No build implantado, o coordenador abriu `http://localhost:13000/concurso/6`: exibiu as 11 microáreas e todos os valores aprovados (1 vaga + CR, AC1/PcD0, R$3.242/mês, 40h, requisito e taxa R$120), publicação 001/2026, prova pendente e histórico legível da versão 83. O reload permaneceu estável, sem JSON bruto/`undefined`.

Smoke OPFS: aba B falhou enquanto A segurava o handle; após fechar A, aguardar 2 s e clicar retry, B abriu ID6 completo sem limpar dados; reload permaneceu estável. `127.0.0.1` continua apenas lock transitório de handle externo.

Em `/notificacoes`, a versão 83 apareceu e “Ativar push” ficou disponível. No web, a ação não criou diálogo visível; não há prova de POST. Isso permanece comportamento web não conclusivo, separado de push nativo/T009.

## Conferência API/checkpoint somente leitura

Login e GETs autenticados retornaram HTTP 200. `GET /concursos/6` confirma título `Processo Seletivo Público - 001/2026 Prefeitura Municipal de Berizal/MG`, edital `001/2026`, 11 cargos; os 11 coincidem com: 1 vaga imediata + cadastro de reserva, AC 1, PcD 0, R$ 3.242,00 por mês, 40h semanais, taxa R$ 120,00 e requisito de residência na área + Ensino Médio Completo. `prova_data=null` (pendente), como esperado. `GET /concursos/6/publications` retorna publicação `001/2026`.

Versão mais recente: id 83, capturada em `13/09/2026 00:53:14`, resumo `Vagas, remuneração, jornada e requisitos por cargo foram atualizados.`

## Parecer

**ACEITA COMPLEMENTARMENTE no escopo ID6**, com a ressalva de que a UI é observação do coordenador, não prova independente. Vinculado a `docs/execucao/tarefas/revisao-independente-T008-opfs-r5-operacional-20260912-01.md`.
