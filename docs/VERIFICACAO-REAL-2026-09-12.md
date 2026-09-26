# Verificação real — 12/09/2026

Verificação do piloto existente após iniciar seus seis serviços com Docker Compose, preservando volumes. Não houve nova publicação de catálogo nem alteração de código nesta verificação.

## Ambiente e dados

- API, web, worker e scheduler ativos; PostgreSQL e Redis saudáveis.
- Login, renovação de sessão, checkpoint, 32 detalhes e revisões passaram pela API via proxy web.
- 32 seleções de 31 fontes, 99 cargos, 48 versões e 47 notificações únicas.
- Um alerta existente e nenhum favorito; ações preservadas entre checkpoints.
- Oito seleções classificadas com inscrições abertas na data da verificação.
- 91 adaptadores, 89 configurações habilitadas e 81 fontes com sucesso histórico de detalhe. Esses indicadores não certificam cobertura integral.
- Solari: US$20 autorizados, US$5,26 reservados, oito sessões registradas e nenhuma pendente de encerramento; cobrança efetiva desconhecida.

Evidências: `backend/.tenderproof/product-completion/delivery-api-current-20260912T195115192916Z.json` e `backend/.tenderproof/product-completion/delivery-current-20260912T195125613173Z.json`.

## Interface observada no navegador

Em `http://127.0.0.1:13000/inicio`, o aplicativo abriu autenticado e sincronizou os 32 registros. O bloqueio de armazenamento anteriormente registrado não se reproduziu nesta sessão.

A busca mostrou 32 resultados; o filtro Abertas reduziu para oito e a pesquisa Caruaru retornou uma seleção. O detalhe exibiu seis cargos, remunerações, requisitos e horários de prova. As telas de alertas e salvos abriram; o alerta existente aparece desligado e salvos mostra zero itens. Não foram criados, removidos ou alternados alertas/favoritos para este diagnóstico.

Problemas visíveis:

- Localização N/I, inclusive em Caruaru e outros cartões inspecionados.
- Seção de publicações estruturadas vazia no detalhe de Caruaru; o checkpoint contém zero publicações.
- Cronograma de Caruaru apresentado em UTC (até 09/10 às 02:59 UTC), equivalente a 08/10 às 23:59 de Brasília, mas pouco claro ao usuário.
- Resumo de alteração de prazo repete as mesmas datas e omite a mudança de precisão/horário.
- Histórico de cargos apresenta JSON bruto e nomes internos de campos.
- Busca rotula a contagem de seleções como “Vagas”.

## Coleta atual

Worker e scheduler retomaram processamento real. Foram observadas listagens bem-sucedidas em FAPESP, FAPERGS, FAPESC e ADMTEC. Também existem novas tentativas por ValueError em FAFIPA e FAPESB, espera por aquisição ocupada e detalhes adiados por limite de tempo do ciclo. As causas dos ValueError não foram investigadas nesta verificação.

O coletor legado está desabilitado (`legacy_crawler_enabled=False`). O disparo periódico de sua tarefa não significa publicação pelo fluxo antigo.

## Limites deste diagnóstico

Não certifica as 99 fontes, nem atualização documental integral nas fontes oficiais. Não foram testados modo offline com rede indisponível, criação/alteração de favoritos e alertas, push, dispositivos nativos ou restauração de backup. Serviços deixados ativos para uso local.
