# Recuperação do Docker — 13/09/2026

Recuperação executada pela tarefa de acompanhamento após o pedido explícito do usuário: “O docker caiu faça ele voltar”. Concluída e verificada em **2026-09-13 10:35:15 UTC / 07:35 Brasília**.

## Falha observada e ação

O motor não respondia a `docker info`. O reinício oficial encontrou falha de inicialização no socket `dockerInference`: Windows erro 1920, arquivo inacessível. O log do backend confirmou que esse endpoint impedia a inicialização; isso não estabelece a causa original da indisponibilidade anterior.

`docker desktop stop --force --timeout 30` encerrou o Desktop e foi confirmada ausência dos seus processos. A tentativa de renomear somente o socket falhou. A pasta temporária foi então validada: diretório normal, contendo apenas `dockerInference` e `userAnalyticsOtlpHttp.sock`, ambos endpoints de zero bytes. Origem/destino absolutos foram conferidos dentro de `C:\Users\gabri\AppData\Local\Docker`.

Essa pasta foi preservada como `C:\Users\gabri\AppData\Local\Docker\run.stale-20260913T073145`; `run` foi recriada vazia. Nenhum socket foi apagado. A alternativa de preservar a pasta corresponde a relatos do mesmo erro no [rastreador do Docker](https://github.com/docker/desktop-feedback/issues/460); a decisão foi limitada aos dois endpoints observados localmente.

`docker desktop start --timeout 120` passou. Banco/Redis/web voltaram; os containers existentes de API, worker e scheduler estavam parados e foram iniciados por `docker start`, sem rebuild/recriação. Os containers antigos de outros projetos e o verificador temporário de restore permaneceram parados. Volumes, bancos, configurações e imagens não foram removidos ou redefinidos.

## Verificação

- Motor: Docker Engine 28.1.1 respondendo a `docker info` e `docker ps`.
- Seis containers `observador-pilot` em execução: web, API, worker, scheduler, PostgreSQL e Redis. PostgreSQL/Redis com health healthy.
- API com inicialização completa no log; `/inicio` HTTP 200; login autenticado e `/api/sync/checkpoint` HTTP 200.
- Checkpoint de 10:35:15 UTC: **33 seleções, 32 fontes, 180 cargos, 34 publicações, 91 versões, 90 notificações, zero favoritos e um alerta**, coerente com o estado anterior à recuperação.
- Configuração WSL existente: 1 CPU, 2 GB de RAM e 1 GB de swap; não alterada. Consumo observado dos seis containers somava aproximadamente 541 MiB, além do sistema/engine. Essa limitação deve ser considerada ao executar tarefas Docker concorrentes; não foi comprovada como causa da falha.

## Continuação

A recuperação libera o integrador do Sol para retomar os gates operacionais e T012. O restore final PostgreSQL segue pendente de teste próprio; esta verificação não equivale ao aceite do restore. Fontes devem avançar por Luna em paralelo, com operações de publicação/build/restore serializadas conforme os recursos reais.
