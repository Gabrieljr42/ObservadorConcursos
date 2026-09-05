# Overrides autoritativos — fontes 07, 11, 12, 29, 38, 47 e 81

Data da revisão: 30/08/2026, America/Sao_Paulo.

Este arquivo substitui, para os sete identificadores abaixo, as conclusões conflitantes dos batches. As decisões usam somente `SOL_SPOTCHECKS.md`, `LOW_REVIEW.md` e as evidências primárias registradas nos batches. Contagens são snapshots da verificação; `UNKNOWN` significa que a listagem integral não foi observada. Os identificadores 07 e 38 pertencem ao mesmo ecossistema Consulplan e não devem gerar dois crawls nem contagens somadas.

## 07 — Instituto Consulplan (portal www)

Identificador técnico: `consulplan_open`  
URL fornecida: https://www.consulplan.net/  
URL operacional vigente: https://www.institutoconsulplan.org.br/Concursos  
Portal ativo: SIM, no sucessor oficial; o domínio antigo permanece protegido por desafio gerenciado  
URL mudou: SIM, migração operacional confirmada para `institutoconsulplan.org.br`

### Navegação e evidência atual

- `https://www.consulplan.net/` responde com desafio gerenciado Cloudflare (`Just a moment...`, `Enable JavaScript and cookies to continue`, `cType: managed`). O shell antigo não é uma lista vazia.
- `https://www.institutoconsulplan.org.br/` é o novo domínio institucional oficial, com rodapé `© Instituto Consulplan 2026`, Área do Candidato, Sistema de Inscrição e link para os concursos em andamento.
- `https://www.institutoconsulplan.org.br/Concursos` abriu como listagem HTML oficial. No snapshot foram observados blocos de `Inscrições abertas / Novos`, `Em andamento` e `Encerrados`. No bloco aberto/novo foram observados seis cards, dos quais três eram relevantes para seleção de pessoal e três eram acadêmicos/vestibulares; o total corrente completo permanece `UNKNOWN`.
- Na seção de andamento foram observados, entre outros, TJMG, Bálsamo, SAAEB Barretos, Potirendaba, CRESS/RO, Câmara Montanha, TJMS, Santa Maria Jetibá, Vitória, Ji-Paraná, Alagoa, Manaus, Uberlândia, CRA/PR e Eugenópolis. A enumeração não é tratada como total.
- Detalhes oficiais observados incluem `/pases2026`, `/cidennf2026` e `/pref-potirendaba2026`; alguns detalhes isolados retornaram 403, embora a listagem institucional tenha sido reproduzida.
- PDFs recentes no CDN oficial `https://cdnsite.institutoconsulplan.org.br/concursos/...` citam o domínio novo como site oficial, incluindo documentos de Ji-Paraná 2026, Manaus SEMSEG 2026 e CRA/PR 2026.

### Universo observado

Observed: listagem vigente com abertos/novos, em andamento e encerrados; total integral `UNKNOWN`.  
Relevant: pelo menos três cards relevantes no snapshot do bloco aberto/novo, além de itens em andamento; total `UNKNOWN`.  
Active: pelo menos um card relevante aberto/novo; total `UNKNOWN`.  
Closed: seção presente; total `UNKNOWN`.  
Out of scope: vestibulares, PASES e demais seleções acadêmicas sem contratação de pessoal; notícias, serviços, Área do Candidato e documentos institucionais.

### Listagem, paginação e campos

Estrutura: HTML indexável no novo portal, com blocos por estado e âncoras para páginas de detalhe. O seletor/container estável, a paginação e o número total de cards não foram confirmados; registrar como `UNKNOWN` até inspeção DOM/rede. Não presumir API: nenhum endpoint público foi observado.

Campos esperados somente quando presentes no detalhe/PDF: título, órgão, modalidade, cargo/função, cidade/UF, status, vagas, remuneração, escolaridade, taxa, datas, prova, edital, retificações e links documentais. Não preencher campos ausentes a partir do texto do card.

Publicações: seguir links de edital, retificações, cronogramas, resultados e gabaritos no detalhe e no CDN oficial; deduplicar por URL canônica, órgão, edital e documento.

### Tecnologia, bloqueios e riscos

O domínio antigo exige JavaScript/cookies e está sob Cloudflare; o sucessor é HTML indexável, mas detalhes isolados podem exigir navegador ou tratamento do 403. Não usar `consulplan.net` como lista operacional nem o CDN como substituto do catálogo. Não inferir que cards acadêmicos sejam concursos de pessoal. O principal risco é falso vazio no host antigo e duplicação entre host antigo, sucessor e o identificador 38.

### Quality gate e empty evidence

ACEITAR somente concurso público, processo seletivo, emprego, cargo ou função com órgão e evidência oficial do edital/detalhe. REJEITAR vestibular, PASES, certificado ou chamada acadêmica sem contratação. Um shell, heading ou desafio sem cards é `UNKNOWN/BLOCKED`, nunca zero. Um card aceito deve ter detalhe ou documento oficial rastreável.

### Estratégia e instruções para o Codex

Estratégia: `HTTP_HTML`/`CONFIGURABLE_HTML` no sucessor para discovery; usar `HYBRID`/navegador apenas como fallback para detalhes que reproduzam o 403. Manter o ID `consulplan_open`, mas apontar a descoberta para `https://www.institutoconsulplan.org.br/Concursos`. Capturar hrefs reais e estado do detalhe; não criar endpoint presumido. Deduplicar por detalhe canônico, órgão/edital e documento. Manter `UNKNOWN` para totais não observados. O ID 38 deve ser tratado como alias legado, conforme a seção própria, sem somar resultados.

### Confidence

`HIGH` para identidade do sucessor e atividade da listagem vigente; `MEDIUM` para extração integral, porque detalhes podem exigir navegador/controle de 403; `LOW` para qualquer contagem além do snapshot explicitamente observado.

### Evidências oficiais

- https://www.consulplan.net/
- https://www.institutoconsulplan.org.br/
- https://www.institutoconsulplan.org.br/Concursos
- https://cdnsite.institutoconsulplan.org.br/concursos/

## 11 — CEBRASPE

Identificador técnico: `cebraspe_open`  
URL fornecida/oficial: https://www.cebraspe.org.br/Concursos/  
Portal ativo: SIM  
Status revisado: `REST_API`

### Navegação e evidência

O portal oficial carrega bundles React (`/concursos/static/js/1.049ae2ab.chunk.js` e `/concursos/static/js/main.68af135b.chunk.js`) que definem a API pública `https://apis.cebraspe.org.br/cebraspe/`. Rotas reproduzidas com 200 e JSON:

- `GET https://apis.cebraspe.org.br/cebraspe/eventos/tipo/concursos/`
- `GET https://apis.cebraspe.org.br/cebraspe/eventos/tipo/concursos/fase/{fase}`
- `GET https://apis.cebraspe.org.br/cebraspe/eventos/{identificador}`
- Documentos sem URL externa própria seguem `https://cdn.cebraspe.org.br/{tipoEvento}/{identificador}/arquivos/{nomeArquivo}` conforme a regra observada no bundle.

A coleção de 30/08/2026 retornou 5 `Novos`, 6 `Inscrições Abertas`, 60 `Em Andamento` e 425 `Encerrados`, total observado de 496 eventos. Esses números são snapshot da API, não promessa de total futuro.

### Universo, exemplo e estado

Observed: 496 no agrupamento da verificação.  
Relevant: `UNKNOWN` sem filtro de escopo aplicado; a API inclui eventos que precisam ser filtrados pelo tipo/natureza.  
Active: usar `isInscricaoAberta` e `periodoInscricao` no detalhe; a fase `Em Andamento` não equivale a inscrição aberta.  
Closed: grupo `encerrado` observado; total do grupo acima é snapshot.  
Exemplo de validação: `CAMARA_MUNICIPAL_PONTAPORA_MS_26` no detalhe retornou `isInscricaoAberta=true` e período de 21/08 a 10/09/2026.

### Campos, detalhe e publicações

Campos observados na listagem: `faseEvento`, `idEvento`, `eventoNomeAbreviado`, `eventoTotalVagas`, `eventoSalarioMaximo`, `strEventoSalarioMaximo`, `eventoURL`, `eventoStatus`, `eventoTipo`, `eventoAno`, `periodoInscricao`, `isInscricaoAberta` e `areaCandidato`. O detalhe deve prevalecer para estado e datas. Preservar arrays `arquivosEdital` e `arquivosGabarito` e resolver CDN somente conforme a regra observada.

### Risco, quality gate e inconsistência

O booleano `isInscricaoAberta` veio `false` nos resumos da coleção, inclusive no grupo aberto, enquanto o detalhe do exemplo retornou `true`. Isso é uma inconsistência real de resumo versus detalhe. O cliente deve usar a fase apenas para discovery e sempre refazer o detalhe antes de classificar estado/datas. Criar testes para agrupamento, cada fase, item aberto, encerrado, detalhe e documentos.

ACEITAR apenas concurso/processo seletivo de pessoal identificado no evento e em seus documentos. REJEITAR vestibular, certificação, curso e evento sem seleção de pessoal. Falha de detalhe ou ausência de um campo não é zero; registrar `UNKNOWN` e retry controlado.

### Estratégia e instruções para o Codex

Usar `REST_API` para discovery, paginação/agrupamento e detalhe. O browser é dispensável para discovery. Para cada identificador, obter o detalhe e prevalecer `isInscricaoAberta`, `periodoInscricao` e documentos. Persistir URL canônica do evento e dos documentos; não confundir `faseEvento` com inscrição aberta.

### Confidence

`HIGH` para API, rotas e campos; `MEDIUM` para classificação final de ativo, devido à inconsistência resumo/detalhe e ao filtro de escopo.

### Evidências oficiais

- https://www.cebraspe.org.br/Concursos/
- https://apis.cebraspe.org.br/cebraspe/eventos/tipo/concursos/
- https://apis.cebraspe.org.br/cebraspe/eventos/FAPEAL_26
- https://cdn.cebraspe.org.br/

## 12 — Fundação Cesgranrio

Identificador técnico: `cesgranrio_open`  
URL institucional: https://www.cesgranrio.org.br/concursos/  
Aplicação oficial: https://concursos.cesgranrio.org.br/  
Portal ativo: SIM  
Status revisado: `REST_API` com catálogo WordPress de fallback

### Catálogo e universo observado

O catálogo institucional WordPress responde 200 em `/concursos/`, `/concursos/page/2`, `/concursos/page/3` e `/concursos/page/4`. Foram observados 10, 10, 10 e 2 links de detalhe, 32 detalhes únicos no snapshot. O padrão de detalhe é `/concurso/{slug}/`.

A categoria oficial `https://www.cesgranrio.org.br/page_category/inscricoes-abertas/` mostrou um item no snapshot: `Transpetro 2026`, em `https://www.cesgranrio.org.br/concurso/transpetro-2026/`. Não usar os números dos parâmetros `ucat=25`, `ucat=26` e `ucat=27` sem seguir os hrefs reais.

Observed: 32 detalhes no snapshot WordPress.  
Relevant: pelo menos um item de seleção de pessoal no snapshot (`Transpetro 2026`); o restante exige filtro integral do tipo de evento.  
Active: `UNKNOWN`; a presença de `Transpetro 2026` na categoria oficial “inscrições abertas” é um sinal de discovery, mas o estado exato deve ser confirmado no cronograma/conteúdo.  
Closed: `UNKNOWN`.  
Out of scope: vestibulares, avaliações acadêmicas e eventos sem seleção de pessoal.

### API/XHR confirmada

O bundle público `https://concursos.cesgranrio.org.br/main.6f687297e0226b96.js` define:

- `GET https://concursos.cesgranrio.org.br/api/PortalEventos`, com `nome`, `status`, `page` base 1 e `pageSize` (10); a homepage usa também `destaque=true` e `pageSize=3`.
- `GET /api/PortalEventos/{id}`.
- `GET /api/PortalEventos/codigo/{guid}`.
- `GET /api/PortalEventoConteudos/publico/{eventId}`.
- `GET /api/PortalGruposProva/todos/{eventId}`.

As três rotas públicas testadas para o evento 22 (`TRANSPETRO 2026`) retornaram 200. O detalhe contém id, código, datas, nome, cliente/razão social, descrição, tipo e publicação. O conteúdo público contém seções HTML, inclusive `ACESSO AOS EDITAIS`; grupos de prova retornam cargos, requisitos, salários e `taxaInscricao`.

### Campos, documentos e riscos

Usar o endpoint paginado como fonte de discovery e abrir detalhe, conteúdos e grupos. `dataFim` do evento não é sinônimo de inscrições abertas: usar categoria, cronograma e conteúdo oficial. URLs de mídia podem conter tokens SAS com expiração; nunca persistir a query assinada como identidade, somente o caminho estável/documento e a forma de renovação.

Quality gate: aceitar concurso/processo seletivo de pessoal com órgão, evento e documentos; rejeitar vestibular e avaliação acadêmica. Falha da categoria WordPress não implica vazio quando a API está disponível. Não somar categorias e páginas duplicadas.

### Estratégia e instruções para o Codex

Preferir `REST_API`; manter o WordPress para discovery, validação de categoria e fallback. Paginar em base 1 até o fim, abrir os quatro recursos por evento quando aplicável, extrair grupos/cargos e documentos. Criar fixture do evento 22 e testes de paginação, conteúdo público, cargos, filtros de escopo e URL assinada. Registrar `UNKNOWN` quando a API não informar estado suficiente.

### Confidence

`HIGH` para catálogo, API, paginação base 1 e fixture 22; `MEDIUM` para status de inscrições, que depende do cronograma/conteúdo e não apenas de `dataFim`.

### Evidências oficiais

- https://www.cesgranrio.org.br/concursos/
- https://www.cesgranrio.org.br/page_category/inscricoes-abertas/
- https://www.cesgranrio.org.br/concurso/transpetro-2026/
- https://concursos.cesgranrio.org.br/
- https://concursos.cesgranrio.org.br/api/PortalEventos

## 29 — Reis & Reis

Identificador técnico: `reisesreis_open`  
URL oficial atual: https://novo.reisauditores.com.br/concursos-em-andamento  
API operacional: https://api.gestaoselecoes.com.br  
Portal ativo: SIM  
Status revisado: `REST_API` para discovery + `HTTP_HTML` para detalhe

### Navegação e universo

O portal novo é Astro. A página de andamento embute `/_astro/ConcursosPagination.DxmG8JD1.js` com situações `PUBLICADO,INSCRICAO_ABERTA,ANDAMENTO`; a página encerrada usa `CONCLUIDO`.

No snapshot, a chamada de andamento retornou um item, ID 70, Prefeitura Municipal de Itabirinha, Concurso Público 1/2025, `situacaoEdital=PUBLICADO`, mas `situacaoInscricao=ENCERRADAS` e `inscricoesAbertas=false`. Portanto, a aba “em andamento” não é contagem de inscrições abertas.

Observed: `UNKNOWN` como total até paginar todo o resultado.  
Relevant: pelo menos o item 70; total `UNKNOWN`.  
Active: o item 70 estava com inscrição encerrada; total de inscrições abertas `UNKNOWN`.  
Closed: usar situação `CONCLUIDO`; total `UNKNOWN`.  
Out of scope: itens que não sejam concurso/processo seletivo de pessoal.

### API e detalhe

O módulo público define base `https://api.gestaoselecoes.com.br` e `GET /api/editais?page={page}&size=9&situacao={lista}&order=DESC`, com header obrigatório `X-TenantID: reisauditores`. A paginação é base 0 e a resposta Spring Page contém `content`, `totalPages`, `totalElements`, `number`, `last` e `empty`.

O card aponta para `/editais/{id}`. `https://novo.reisauditores.com.br/editais/70` respondeu 200 e embutiu objetos completos de `edital`, `cargos` e `anexos` nos props de `TabsEdital`. Foram observados órgão, tipo, número/ano, situação, datas, totais, isenções, cargos, requisitos, taxa, vagas, URLs S3 e metadados de publicações.

### Quality gate, riscos e estratégia

ACEITAR somente quando o detalhe/documento confirmar contratação, concurso ou processo seletivo e o órgão. Não classificar como aberto apenas por `situacaoEdital=PUBLICADO`; exigir `situacaoInscricao` e `inscricoesAbertas`. Deduplicar anexos por id/URL e preservar tipo. O risco principal é misturar “andamento” com “aberto” e perder itens por header tenant ausente.

Usar `REST_API`, enviar `X-TenantID: reisauditores`, paginar até `last=true`, usar `CONCLUIDO` para encerrados e abrir o HTML do detalhe. Fixture: ID 70, incluindo inscrição encerrada, cargos e anexos. Não inferir URL ou endpoint adicional.

### Empty evidence

Uma resposta vazia de uma situação, falha de header ou página não acessada é `UNKNOWN`, não `EMPTY`. Só aceitar vazio após paginação válida de todas as situações relevantes e confirmação do tenant.

### Confidence

`HIGH` para API, tenant, paginação e detalhe ID 70; `MEDIUM` para totais e status agregado enquanto a paginação completa não for observada.

### Evidências oficiais

- https://novo.reisauditores.com.br/concursos-em-andamento
- https://novo.reisauditores.com.br/editais/70
- https://api.gestaoselecoes.com.br/api/editais

## 38 — Instituto Consulplan Azure (legado)

Identificador técnico: `institutoconsulplan_open`  
URL fornecida: https://institutoconsulplan.azurewebsites.net/Concursos  
URL sucessora oficial: https://www.institutoconsulplan.org.br/Concursos  
Estado: `SITE_OFFLINE` + `PORTAL_MIGRATED`  
Decisão: alias legado; deprecar crawl independente

### Evidência e comparação

- O host Azure responde 403 com `Error 403 - This web app is stopped / Web App - Unavailable`. Isso é indisponibilidade de plataforma, não uma lista vazia.
- Resultados indexados antigos mostravam uma fotografia anterior com cinco itens abertos/novos e cerca de 14 em andamento. Essa fotografia é obsoleta e não deve ser contada.
- O novo portal oficial `https://www.institutoconsulplan.org.br/Concursos` contém a listagem corrente de abertos/novos, em andamento e encerrados descrita no override #07.
- PDFs atuais em `https://cdnsite.institutoconsulplan.org.br/concursos/...` citam o domínio novo como site oficial, reforçando a migração.

### Universo e deduplicação

Observed/Relevant/Active/Closed no Azure atual: `UNKNOWN`; não usar o snapshot indexado. O universo corrente é o do sucessor oficial e não deve ser somado ao #07 nem ao próprio sucessor. Manter o identificador por compatibilidade histórica, mas apontar o conector funcional ao #07/novo portal e deduplicar por URL de detalhe, órgão/edital/documento.

### Quality gate, risco e estratégia

Nunca converter 403 `web app stopped` em `[]`. Não tentar reconstruir os números antigos. Aceitar itens somente por meio da origem sucessora, com o mesmo filtro de contratação de pessoal usado no #07. Marcar `DEPRECATE_REVIEW_REQUIRED` para eventual remoção futura do alias depois de preservar compatibilidade e referências históricas.

Estratégia: nenhum crawl operacional no Azure; registrar o estado de migração e redirecionar discovery para `https://www.institutoconsulplan.org.br/Concursos`. Não somar contagens. Se o host voltar, tratar qualquer conteúdo como validação histórica e deduplicar antes de considerar um item.

### Confidence

`HIGH` para indisponibilidade do Azure, migração e regra de não soma; `LOW` para qualquer universo atual próprio do Azure.

### Evidências oficiais

- https://institutoconsulplan.azurewebsites.net/Concursos
- https://www.institutoconsulplan.org.br/Concursos
- https://cdnsite.institutoconsulplan.org.br/concursos/

## 47 — Elo Assessoria

Identificador técnico: `elo_open`  
URL fornecida: https://eloassessoriaeservicos.com.br/concursos  
URL operacional: https://novo.eloassessoriaeservicos.com.br/concursos  
Portal de candidato: https://elo.candidato.gestaoselecoes.com.br  
API: https://api.gestaoselecoes.com.br  
Portal ativo: SIM, migrado; status revisado `REST_API`

### API e universo observado

O módulo público `https://novo.eloassessoriaeservicos.com.br/_astro/ConcursosSection.DhIge_VT.js` usa a API Gestão Seleções com header `X-TenantID: eloassessoria`. A chamada é `GET /api/editais?page={page}&size={size}&situacao={lista}&order=DESC`, paginação base 0 e resposta Spring Page com `content`, `totalElements`, `totalPages`, `last` e `empty`. Situações observadas: `PUBLICADO,INSCRICAO_ABERTA,ANDAMENTO`, `PROXIMO` e `CONCLUIDO`.

No snapshot de 30/08/2026, o grupo corrente retornou sete registros: três com `inscricoesAbertas=true` (IDs 134, 133 e 129), três com `situacaoInscricao=EM_BREVE` e um com inscrições encerradas. `PROXIMO` retornou três e `CONCLUIDO` informou 123. As categorias se sobrepõem semanticamente; não somar esses números como universo deduplicado.

### Rotas e fixtures

Foram reproduzidos com 200 JSON:

- `GET https://api.gestaoselecoes.com.br/api/editais/134`
- `GET https://api.gestaoselecoes.com.br/api/editais/134/cargos`
- `GET https://api.gestaoselecoes.com.br/api/editais/134/anexos`

O fixture ID 134 é São Geraldo do Baixio 1/2026, Processo Seletivo Público, com três cargos e dois anexos. O grupo também permite validar item futuro e item encerrado.

Observed: sete no grupo corrente, três próximos e 123 concluídos no snapshot; não somar.  
Relevant: pelo menos os itens de seleção de pessoal; total deduplicado `UNKNOWN`.  
Active: pelo menos três com `inscricoesAbertas=true`; total corrente deduplicado `UNKNOWN`.  
Closed: 123 na situação `CONCLUIDO` no snapshot, sem somar com outras categorias.  
Out of scope: vestibular, educação sem contratação e conta de candidato.

### Quality gate, riscos e estratégia

ACEITAR somente CP/PSS com órgão, cargo/função, vagas, período e edital/documento. Exigir `inscricoesAbertas`/`situacaoInscricao` para estado de inscrição; `situacaoEdital=PUBLICADO` sozinho não é suficiente. Deduplicar entre abas por id/URL/órgão/edital. O risco principal é misturar tenants ou tratar a mesma engine como uma segunda fonte; manter header Elo e identidade própria.

Reclassificar de browser/hybrid para `REST_API`; não abrir navegador para discovery/detalhe quando os endpoints responderem. Paginar até `last=true`, buscar detalhe, cargos e anexos. Manter a página nova como URL operacional; o domínio antigo é referência de migração. Não inventar parâmetros fora do módulo observado.

### Empty evidence

O placeholder `Carregando concursos...` do HTML não é lista vazia. Uma resposta vazia sem paginação válida, header tenant ou detalhe de situação é `UNKNOWN`; não emitir zero.

### Confidence

`HIGH` para API, tenant, rotas e snapshot; `MEDIUM` para o total deduplicado e estado final, por sobreposição das categorias e necessidade de filtro de escopo.

### Evidências oficiais

- https://novo.eloassessoriaeservicos.com.br/concursos
- https://novo.eloassessoriaeservicos.com.br/concurso/134
- https://api.gestaoselecoes.com.br/api/editais/134
- https://api.gestaoselecoes.com.br/api/editais/134/cargos
- https://api.gestaoselecoes.com.br/api/editais/134/anexos
- https://elo.candidato.gestaoselecoes.com.br

## 81 — FAPEAL

Identificador técnico: `fapeal_selection`  
URL fornecida: https://fapeal.br  
URL institucional: https://www.fapeal.br/  
Origem operacional do concurso: https://www.cebraspe.org.br/concursos/FAPEAL_26  
API operacional: https://apis.cebraspe.org.br/cebraspe/eventos/FAPEAL_26  
Portal institucional ativo: SIM  
Correção: não é vazio para seleção de pessoal

### Evidência oficial do concurso

O detalhe público CEBRASPE `GET https://apis.cebraspe.org.br/cebraspe/eventos/FAPEAL_26` respondeu 200 JSON. O evento tem ID 3342, nome `FAPE AL 26`, 10 vagas, remuneração máxima de R$ 5.767,15, inscrições de 15/05/2026 a 19/06/2026 (fechadas na data da pesquisa), 23 arquivos de edital e 22 de gabarito. O evento está na fase oficial `Em Andamento` do CEBRASPE.

O edital de abertura oficial (`Edital nº 1 — FAPEAL, de 7 de maio de 2026`) declara concurso público para provimento e cadastro de reserva no cargo de Gestor Especializado em Ciência e Tecnologia, executado pelo CEBRASPE. A página operacional é `https://www.cebraspe.org.br/concursos/FAPEAL_26`; os documentos seguem `https://cdn.cebraspe.org.br/concursos/FAPEAL_26/arquivos/...`.

### Universo revisado

Observed: pelo menos um concurso de pessoal confirmado.  
Relevant: pelo menos um (`FAPEAL_26`).  
Active: processo em andamento, com inscrição encerrada; não classificar como inscrição aberta.  
`process_status=Em Andamento`; `registration_status=Encerrada`; `process_closed=0` no snapshot oficial. Estado do processo e estado da inscrição devem permanecer separados.  
Out of scope: bolsas, chamadas de projetos, PIBIC Jr., auxílio, mobilidade, publicação acadêmica e demais fomento.

O arquivo institucional FAPEAL contém chamadas científicas/fomento e pode não expor o concurso no mesmo agrupamento editorial. Limitar discovery à homepage/categoria de editais de fomento produziria `false empty`.

### Campos e documentos

No evento CEBRASPE, preservar identificador `FAPEAL_26`, ID 3342, nome, vagas, remuneração, período de inscrição, fase, status de inscrição e arrays de arquivos de edital/gabarito. No portal FAPEAL, usar a instituição como fonte complementar de identidade e escopo; não substituir o detalhe CEBRASPE por um post de bolsa.

### Quality gate, riscos e estratégia

ACEITAR `FAPEAL_26` porque edital e detalhe descrevem provimento/cadastro de reserva para cargo de pessoal. REJEITAR PIBIC Jr. e chamadas de bolsas/projetos mesmo quando aparecem como “edital” na FAPEAL. O risco P0 é um conector que reporta zero por olhar somente o arquivo de fomento; outro risco é transformar inscrição encerrada em concurso encerrado.

Estratégia: usar a API/listagem CEBRASPE como origem operacional do concurso e `www.fapeal.br` como origem institucional complementar. Pesquisar/filtrar pelo identificador `FAPEAL_26`, cargo e edital 1/2026. Deduplicar pelo identificador do evento, edital e documento. No pipeline, manter campos distintos `process_status` e `registration_status`; o registro é em andamento com inscrições fechadas.

### Empty evidence

`0` para a categoria de fomento não prova `0` para pessoal. O caso só pode ser vazio depois de verificar a origem CEBRASPE e as evidências institucionais relacionadas; a conclusão correta deste snapshot é `Relevant >= 1`, não vazio.

### Confidence

`HIGH` para existência, identidade, 10 vagas, remuneração, datas, fase e documentos do concurso; `MEDIUM` para a exaustividade de todos os processos de pessoal da FAPEAL fora do evento confirmado.

### Evidências oficiais

- https://www.fapeal.br/
- https://www.fapeal.br/pesquisador/editais/
- https://apis.cebraspe.org.br/cebraspe/eventos/FAPEAL_26
- https://www.cebraspe.org.br/concursos/FAPEAL_26
- https://cdn.cebraspe.org.br/concursos/FAPEAL_26/arquivos/
