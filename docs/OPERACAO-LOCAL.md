# Observador: operação local iniciada em 08/09/2026

## Entrega atualizada em 09/09/2026

O catálogo contém **32 registros de 31 fontes e 99 cargos estruturados**, incluindo as retificações de Pedrinhas e Barra Longa, a chamada FAPESE para prestadores de serviço e a certificação ocupacional de Lagoa da Prata. Estado corrente: [ENTREGA-ATUAL-OPERACAO.md](ENTREGA-ATUAL-OPERACAO.md); matriz das 99 fontes: [entrega-fontes-atual.csv](entrega-fontes-atual.csv). A entrega anterior e o texto do piloto inicial abaixo são históricos: há 91 adaptadores, 89 configurações habilitadas e 81 fontes com sucesso histórico de detalhe. Nenhum desses números certifica cobertura integral.

Endereço verificado nesta entrega: **http://127.0.0.1:13000/inicio**. Usa o mesmo backend de `localhost`, com cache local independente. Se aparecer “Dados salvos indisponíveis”, outra instância pode manter o arquivo local aberto; feche sua outra aba e tente novamente. Não apague o armazenamento. Ações offline ainda não sincronizadas pertencem ao endereço em que foram feitas.

O detalhe mostra aviso quando há documento novo pendente. **Pedrinhas recebeu a retificação na versão 15**: inscrições de 09/09 às 10h até 11/09 às 10h, Brasília; prova em 27/09. Período original e eventos foram preservados. Ibiúna continua com três listas pendentes por conflito de numeração 001/2026 versus edital-base 002/2026; ver [pacote de conflito](ENTREGA-IBIUNA-CONFLITO.md).

Na execução corrente, login, sessão, detalhes, retificação e os cargos foram verificados pela API e pelo checkpoint real. A verificação visual/offline ainda depende de liberar o handle OPFS de outra instância. A existência de build web e testes aprovados não substitui esse aceite.

Nenhuma fonte tem integração integral certificada. Salários, vagas, cargos e outros campos sem prova permanecem pendentes. Novas publicações continuam passando por proposta, autorização e aplicação auditada; a coleta não publica automaticamente.

Aplicativo: http://localhost:13000. Revisão: http://localhost:13000/tenderproof.

Para consultar novamente um concurso já coletado, abra sua conferência e use **Solicitar nova coleta**. A fonte precisa estar habilitada e o usuário deve ter acesso de operação. O pedido fica na fila e seu andamento reaparece ao reabrir a mesma coleta. Repetir o pedido não duplica o trabalho. Ao terminar, use **Abrir nova coleta para conferência**; o histórico anterior continua preservado. A renovação de um concurso não comprova a cobertura de toda a fonte e não publica automaticamente.
Backend: http://localhost:18000. Conta e senha estão no arquivo privado
`backend/.tenderproof/local-pilot/ACESSO-LOCAL.md`; não publicar nem commitar.

## O que está ligado

- Projeto Docker `observador-pilot`, separado dos outros projetos, com API,
  aplicativo web, trabalhador, agendador, PostgreSQL 17 e Redis.
- ACCESS, ABCP e Fênix: coleta real por HTTP, a cada hora. O primeiro ciclo
  encontrou três candidatos por fonte. O limite de uma listagem, três candidatos
  e três documentos mantém a cobertura parcial explícita.
- Nove observações iniciais: cinco com documento válido e quatro exigindo revisão
  documental. Validade documental não garante todos os campos nem cadastro.
- Três concursos publicados após revisão de título, órgão e número do edital:
  Birigui (ACCESS), Ibiúna (ABCP) e Pedrinhas Paulista (Fênix).
- Datas, salários, vagas e localização não comprovados permanecem desconhecidos.
- Alerta interno `Concursos revisados do piloto`, sem filtro de inscrições abertas,
  pois não há datas comprovadas. Eventos são entregues a cada 30 segundos, sem
  duplicação. Isso não envia push, e-mail nem mensagens externas.
- Material sintético e navegador pago desativados. Novas publicações continuam
  exigindo preparação, aprovação e aplicação; a coleta não publica sozinha.

Isso é um piloto persistente com dados reais, acessível somente neste computador.
Não é hospedagem pública nem integração completa das 99 fontes. As outras fontes
permanecem no inventário, sem habilitação neste piloto.

## Usar

1. Abrir o aplicativo e entrar com os dados do arquivo privado.
2. O início mostra os concursos sincronizados; o sino mostra notificações.
3. Em Notificações, `Sincronizar tudo` busca os dados mais recentes.
4. Em `/tenderproof`, `Atualizar fontes e observações` mostra o progresso e as
   pendências. Abrir uma observação para revisar seus campos e documentos.
5. Campos sem prova ou com pendência documental não devem ser liberados.

## Ligar, parar e fazer backup

Na raiz do projeto, em PowerShell:

```powershell
./scripts/observador-pilot.ps1 -Action Status
./scripts/observador-pilot.ps1 -Action Start
./scripts/observador-pilot.ps1 -Action Stop
./scripts/observador-pilot.ps1 -Action Backup
```

Start reutiliza os dados persistentes. Stop preserva os volumes. Backup pausa
os escritores, gera um dump PostgreSQL e copia/verifica o volume operacional
completo; depois religa os serviços. Nenhum comando remove volumes. Cada backup
recebe um nome novo dentro do volume Docker `observador-pilot_pilot_backups`.
A senha do banco e a chave de autenticação ficam em `backend/.env.pilot`, ignorado
pelo Git. Preserve esse arquivo junto dos backups em armazenamento privado.

Docker precisa estar ligado e o computador acordado para as coletas ocorrerem.
Os containers têm reinício automático quando o Docker volta. A configuração não
liga o Docker nem o computador por conta própria.

## Manutenção

- O piloto usa a imagem `backend-api:latest` já instalada, com o código atual
  montado por leitura. Para outra máquina, construir a imagem a partir de
  `backend/Dockerfile` e instalar as dependências mobile antes da primeira execução.
- `./scripts/observador-pilot.ps1 -Action BuildWeb` reconstrói a interface com
  `/api`, sem herdar o endereço antigo do `.env` mobile ou do cache do Expo.
- O servidor web encaminha `/api` ao backend do piloto, no mesmo endereço da
  página. SQLite web recebe os cabeçalhos de isolamento necessários.
- A rotina horária antiga usa `LEGACY_CRAWLER_ENABLED=false` por padrão.
  As chamadas manuais antigas retornam 409 quando desativado; tarefas antigas
  em fila e chamadas diretas ao serviço também recusam execução. O bloqueio
  impede publicação por fora da revisão, inclusive após reiniciar o trabalhador.
- O banco operacional usa volume Docker local, não o OneDrive. O código-fonte
  continua no workspace original.

## Verificações realizadas

- 50 testes de publicação, coleta contínua e operação do piloto passaram.
- 12 testes de operação/resiliência passaram em outra execução (há sobreposição).
- Depois do ajuste de tentativas de notificações, os quatro testes focais passaram.
- Três testes da transação mobile passaram, incluindo rollback e caminho Android.
- TypeScript sem erros e exportação web com 23 rotas.
- Cadastro e aplicação repetida de Birigui/Ibiúna mantiveram IDs e versões.
- Login, sincronização, listagem e notificações verificados no navegador.
- Backup PostgreSQL restaurado em banco separado: dois concursos, duas versões
  e duas notificações no momento daquele backup. A cópia de teste foi removida.
- Backup operacional: 33 arquivos verificados e restaurados em diretório separado,
  sem substituir os originais. Um backup posterior inclui a publicação da Fênix.

Relatórios privados da execução estão em `backend/.tenderproof/local-pilot/`.
O estado desses relatórios é uma fotografia da verificação, não um monitor ao vivo.
