# T012 — Avança SP (`avancasp_open`) — proposta pronta

Estado: **PROPOSTA_PRONTA**, `reference_only=true`, sem escrita no catálogo,
sem POST/pilot e sem coleta de rede nesta etapa.

## Identidade e escopo

O candidato único revisado é o external id `272`, com detalhe oficial
`https://avancasp.selecao.net.br/informacoes/272/` e título
“Concurso Público - 01/2026 - Prefeitura Municipal de Cabreúva”. O fixture de
listagem e o fixture de detalhe são preservados no repositório; os IDs da
listagem são únicos e o `SelecaoNetAdapter` confirmou que o detalhe, o tenant
301 e o documento vinculado pertencem ao mesmo concurso.

O detalhe identifica concurso público municipal em andamento, com 14 cargos,
remuneração, jornada, requisito, taxa e vagas/CR. O caso foi aceito como
contratação de pessoal publicável; não há marca de vestibular, bolsa, auxílio
ou treinamento. A chave de não duplicidade é `avancasp_open:272`.

## Proveniência preservada

- Detalhe HTML: 37.232 bytes, SHA-256
  `8f84661e03be3aaac0022a91f680c2c25e98ef8d1682e90c75be0f60061d59e3`.
- Listagem HTML: 47.635 bytes, SHA-256
  `d04a91da70d0f3dfa40ce1b216e594508ed03f5c8bbfebbc2284035aaa27cbf2`.
- Trechos revisados no envelope comprovam identidade municipal, período de
  inscrição, prova prevista e tabela de cargos.
- O HTML preserva um edital vinculado em
  `https://anexos-r2.selecao.net.br/uploads/301/concursos/272/anexos/aa3e927b-faeb-414e-ae6c-28800427a051.pdf`.
  Como o PDF não está entre os fixtures, nenhum conteúdo ou SHA de PDF foi
  declarado; a proposta usa somente o HTML preservado como artefato revisado.

## Gate e handoff

O envelope `tenderproof.reviewed-run.v1` tem `pending_fields=[]`, exatamente o
campo canônico `cargos`, owner positivo e run determinístico
`tp-reviewed-9edb46567e9d34e12c488cdcefb53f19`. O teste local executa o dry-run
do importador, revalida identidade/documento, rejeita host/tenant/ID
estranhos e rejeita detalhe com identidade divergente: **7 passed**.
O CLI do importador também validou o envelope em modo dry-run e retornou esse
mesmo `run_id`.

Próximo passo do integrador: revisão independente deste envelope e, se aceito,
execução do fluxo normal de importação/proposta. Esta entrega não promove nem
aplica a seleção.

## Strong-binding preflight

Após a revisão inicial, foi adquirido uma única vez o PDF oficial vinculado
ao detalhe, usando `BoundedHTTPDriver` com TLS verificado e allowlist do
adaptador. O artefato preservado é
`avancasp-open-edital-272.pdf`, 742.298 bytes, SHA-256
`b0ba7e154786ce20c7bbe5fd454933c552558c4dfcfc588b60a71eab6a4ca06a`.

O parser fonte-específico `avancasp_parser.py` é estritamente pinado a
`avancasp_open`, external ID `272`, SHA e tamanho acima. Ele comprova no PDF
fresco `orgao=Prefeitura Municipal De Cabreúva`,
`edital_numero=01/2026` e `identity_ids={272}`, além das sete áreas
publicáveis, incluindo os 14 cargos da tabela.

O teste executou o `_revalidate` real contra SQLite efêmero, com ID positivo,
sem piloto e sem catálogo: **PASS**. O único bloqueio restante é a faixa
genérica `remuneracao`, deliberadamente fora do escopo publicável; os campos
de identidade, cronograma e `cargos` foram elegíveis. A suíte source-specific
combinada ficou em **10 passed**.

## Live envelope r1

O pacote de importação live está em
`live-envelope-ready-r1.json`. Ele contém apenas o PDF oficial acima (nunca o
HTML de SHA `8f8466…`), sete campos com evidências literais frescas, owner
positivo e `pending_fields=[]`. O dry-run produziu o run determinístico
`tp-reviewed-99b7976845305f188d176677963fc079`.

O round-trip `ReviewedRun` completo → `_revalidate` foi executado em SQLite
efêmero. Variantes com artefato HTML, external ID stale e SHA alterado foram
rejeitadas. O receipt correspondente é
`live-envelope-receipt-r1.json`; a suíte combinada terminou com **10 passed**.
