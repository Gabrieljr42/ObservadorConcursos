# TenderProof — etapas 8–10

Objetivo autorizado: mapear as 99 fontes, generalizar o fluxo existente e preparar
coleta contínua. O piloto de dez fontes, a publicação no catálogo real e a
expansão dos adaptadores para as 99 fontes pertencem às etapas seguintes.

## Critérios de aceite

| Etapa | Requisito | Evidência necessária | Estado |
|---|---|---|---|
| 8 | Matriz exata das 99 fontes, famílias, duplicidades, prioridade e pendências | [Inventário JSON](tenderproof-sources-99.json) e [tabela](tenderproof-sources-99.md), preservando 99 IDs | Concluído |
| 8 | Revalidar endereços e observar documentos disponíveis sem escrever no catálogo | 103 listagens e 25 detalhes sondados em 07/09/2026; resultados e limites por URL no inventário | Concluído |
| 9 | Contrato comum: descoberta, identidade, documentos e vazio legítimo | SourceAdapter, registro IBGP/IMESO e testes de contrato/regressão | Concluído |
| 9 | Preservar a experiência de revisão existente e controles de evidência | Regressão da API, aquisição, armazenamento e publicação | Concluído |
| 10 | Percorrer páginas/abas sem apresentar amostra como cobertura completa | URLs observadas, limites, grafos cíclicos e fim/vazio explícito testados; observações reais abaixo | Concluído |
| 10 | Acompanhar concursos conhecidos e preservar progresso | Checkpoints, fencing e recuperação local inclusive na última tentativa; acompanhamento após desaparecer da listagem | Concluído |
| 10 | Agendar, limitar, repetir e isolar falhas por fonte | Celery/Redis reais: 8/8 verificações de reentrega e morte/retomada de worker | Concluído |
| 10 | Execuções e documentos duráveis | SQLite transacional e PDFs com hash; leitura em processo independente, incluindo edital real IMESO | Concluído |
| 10 | Operação observável e reproduzível | [Guia operacional](TENDERPROOF-CONTINUOUS.md), API autenticada e autorização restrita a operadores | Concluído |

## Resultado observado

O catálogo contém **63 bancas e 36 fontes de seleções institucionais**. A sondagem
registrou 87 respostas HTTP de listagem, 7 bloqueios/challenges, 4 falhas TLS,
3 falhas DNS, 1 erro HTTP e 1 resposta acima do limite. São resultados por
endereço, incluindo aliases, e não contagens de bancas homologadas.

Na prova HTTP, duas listagens IMESO produziram **115 candidatos únicos**. O edital
observado do concurso 139 foi baixado: **29 páginas**, identidade válida, cinco
campos sustentados e remuneração desconhecida. Outro processo recuperou o
resultado e conferiu os bytes pelo SHA-256 sem nova aquisição.

O HTML inicial do IBGP não continha a lista renderizada. A prova seguinte executou
**um job real do motor contínuo**, com fallback Solari: **9 candidatos**, **uma
sessão**, encerramento confirmado pelo provedor e **zero pendências no journal**.
A prova durou aproximadamente 13 segundos e pausou a fonte ao terminar. Executou
somente uma listagem; não há alegação de cobertura completa das abas. Detalhes não
foram executados nesse ensaio. Callbacks tardios de liberação de respostas geraram
erros de limpeza após o fechamento; a correção subsequente foi validada offline
em 57 testes focalizados, incluindo nove regressões novas, sem outra sessão paga.

Os artefatos locais ficam em `backend/.tenderproof/expansion-live-20260907` e
`backend/.tenderproof/expansion-browser-20260907`. O resumo sem credenciais é
[tenderproof-expansion-validation.json](tenderproof-expansion-validation.json).
A suíte integrada passou **467 testes**, com 14 testes PostgreSQL opcionais
ignorados e 2 testes live excluídos. As provas reais acima foram executadas
separadamente. O Compose também foi validado sem iniciar serviços.

## Decisões implementadas

- HTTP primeiro; navegador somente com habilitação e reserva explícitas. O SDK
  não repete automaticamente criação de sessão após uma resposta incerta.
- Intenção persistida antes do launch; ID persistido assim que recebido. Falta
  de confirmação de encerramento impede outro browser da fonte, inclusive após
  crash. Reconciliação não presume encerramento por timeout.
- Navegador encerrado antes do processamento local do PDF. Destinos e identidade
  verificados antes de seguir redirects e ao receber o HTML final.
- Contenção adia trabalho sem gastar tentativas. Uma execução já concluída pode
  finalizar sua observação após crash, mesmo com tentativas/prazo esgotados,
  sem abrir rede novamente.
- Atualizações operacionais usam transações para não sobrescrever resultados
  novos. Snapshots JSON antigos continuam legíveis.

## Escopo operacional

O fluxo contínuo produz observações para revisão. A ativação de publicação real,
criação automática de concursos e notificações não faz parte dessas etapas.
As fontes sem adaptador TenderProof ficam explicitamente pendentes; estarem no
inventário não as habilita para aquisição verificada.

A matriz distingue acesso HTTP, qualidade histórica do coletor e homologação
TenderProof. Uma resposta HTTP 200 ou uma lista de links não comprova precisão,
completude nem vigência dos dados de uma banca.

A implantação contínua usa um host e volume local compartilhado por API, worker
e scheduler. O Compose configura `tenderproof_data`; bancos SQLite não devem
operar em NFS/SMB/OneDrive. Os ensaios locais no workspace não substituem essa
configuração de produção. Antes da primeira migração para o volume, parar os
escritores e copiar o diretório operacional inteiro, incluindo bancos, `runs/`
e `artifacts/`; não migrar somente PDFs. Nada foi migrado ou ativado
automaticamente na configuração real do usuário.

O próximo passo é a etapa 11, piloto de dez fontes. Os outros 97 adaptadores
continuam pendentes; estas etapas entregam o inventário e a base para expandi-los.
