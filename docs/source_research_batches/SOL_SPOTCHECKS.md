# Revisões do coordenador (Sol)

Data da verificação: 30/08/2026, America/Sao_Paulo.

Este arquivo registra somente segundas investigações de casos LOW, contraditórios ou arquiteturalmente relevantes. Ele prevalece sobre conclusões conflitantes dos batches na consolidação final. As chamadas abaixo foram leituras públicas, sem autenticação, sem submissão de dados e sem contagens provenientes do crawler do projeto.

## Fontes 07 e 38 — Consulplan

### Evidência atual

- `https://www.consulplan.net/` responde ao HTTP direto com desafio gerenciado do Cloudflare: `Just a moment...`, `Enable JavaScript and cookies to continue`, `cType: managed`. Portanto, HTTP simples não é suficiente no estado observado.
- `https://institutoconsulplan.azurewebsites.net/Concursos` responde atualmente `403` com a página Azure `Error 403 - This web app is stopped` / `Web App - Unavailable`.
- A indexação de busca ainda mostra cards antigos do host Azure, mas essa cópia foi rastreada meses antes e não prova disponibilidade atual.
- PDFs oficiais continuam hospedados em `https://cdnsite.consulplan.net/concursos/...` e citam `www.consulplan.net`, o que confirma o mesmo ecossistema documental, mas não prova equivalência integral de IDs/listagens.
- `https://www.institutoconsulplan.org.br/Concursos` é o sucessor oficial atual e respondeu `200` com HTML server-rendered completo na verificação de 30/08/2026. A página e o rodapé identificam o Instituto Consulplan, com copyright 2026, e seus documentos usam o host oficial `cdnsite.institutoconsulplan.org.br`.
- No recorte `Novos/Abertos` desse portal atual foram observados seis cards: três seleções de pessoal relevantes (CIDENNF, Câmara Municipal de Unaí e Município de Belo Vale) e três processos acadêmicos fora do escopo (PASES, vestibular UNIFACIG e vestibular de Itaúna). Essa contagem é apenas o snapshot dessa categoria e não deve ser somada ao arquivo legado.

### Conclusão

- Fonte 07 (`consulplan_open`): migrar a URL operacional para `https://www.institutoconsulplan.org.br/Concursos` e usar `HTTP_HTML`/`CONFIGURABLE_HTML`; manter filtro explícito para vestibular/PASES e reteste rápido do HTML. O domínio antigo `consulplan.net` permanece uma evidência de WAF, não a superfície preferida.
- Fonte 38 (`institutoconsulplan_open`): o host Azure é `SITE_OFFLINE` e deve ser tratado como alias legado do mesmo universo, com `DEPRECATE_REVIEW_REQUIRED`; não é uma segunda origem operacional.
- Não manter dois crawls independentes nem somar as contagens de 07 e 38. Conservar o identificador 38 apenas por compatibilidade até a depreciação, fazer discovery somente pelo portal atual associado à fonte 07 e deduplicar por documento/órgão/edital.

## Fonte 11 — CEBRASPE

### Tecnologia e endpoints confirmados

O HTML de `https://www.cebraspe.org.br/Concursos/` carrega os bundles React:

- `/concursos/static/js/1.049ae2ab.chunk.js`
- `/concursos/static/js/main.68af135b.chunk.js`

O bundle define explicitamente:

- base da API: `https://apis.cebraspe.org.br/cebraspe/`
- listagem geral: `GET https://apis.cebraspe.org.br/cebraspe/eventos/tipo/concursos/`
- listagem por fase: `GET https://apis.cebraspe.org.br/cebraspe/eventos/tipo/concursos/fase/{fase}`
- detalhe: `GET https://apis.cebraspe.org.br/cebraspe/eventos/{identificador}`
- documentos: `https://cdn.cebraspe.org.br/{tipoEvento}/{identificador}/arquivos/{nomeArquivo}` quando o item não fornece URL externa própria.

Rotas reproduzidas com `200 application/json`:

- `/eventos/tipo/concursos/` — resposta agrupada por `faseEvento`.
- `/eventos/tipo/concursos/fase/em-andamento`.
- `/eventos/tipo/concursos/fase/encerrado`.

Campos observados na listagem: `faseEvento`, `idEvento`, `eventoNomeAbreviado`, `eventoTotalVagas`, `eventoSalarioMaximo`, `strEventoSalarioMaximo`, `eventoURL`, `eventoStatus`, `eventoTipo`, `eventoAno`, `periodoInscricao`, `isInscricaoAberta`, `areaCandidato`.

### Conclusão e instrução

- Reclassificar de `PLAYWRIGHT` para `REST_API`.
- O browser é dispensável para discovery; usar o agrupamento/fase da API e `eventoURL` como identificador do detalhe.
- `eventoStatus == em-andamento` não equivale automaticamente a inscrição aberta; usar `isInscricaoAberta` e `periodoInscricao`.
- Na revalidação de 30/08/2026, a coleção agrupada retornou 5 `Novos`, 6 em `Inscrições Abertas`, 60 `Em Andamento` e 425 `Encerrados` (496 eventos observados). O booleano `isInscricaoAberta` veio `false` nos resumos da coleção, inclusive no grupo aberto, mas o detalhe de `CAMARA_MUNICIPAL_PONTAPORA_MS_26` retornou `isInscricaoAberta=true` e período de 21/08 a 10/09/2026. Portanto, usar a fase para discovery e sempre prevalecer os campos do detalhe para estado/datas; criar teste explícito para essa inconsistência entre resumo e detalhe.
- Preservar arrays de `arquivosEdital` e `arquivosGabarito` do detalhe e montar URL CDN somente segundo a regra observada no bundle.
- Criar testes para agrupamento, fase, item aberto, encerrado, detalhe e documentos CDN.

## Fonte 12 — CESGRANRIO

### Catálogo WordPress confirmado

As duas URLs respondem atualmente `200`:

- `https://www.cesgranrio.org.br/concursos/` — HTML WordPress, cerca de 92 KB na verificação.
- `https://concursos.cesgranrio.org.br/` — aplicação Angular.

O catálogo institucional possui quatro páginas reproduzíveis:

- `/concursos/`
- `/concursos/page/2`
- `/concursos/page/3`
- `/concursos/page/4`

Foram observados 10, 10, 10 e 2 links de detalhe respectivamente, totalizando 32 detalhes únicos no snapshot. O padrão é `/concurso/{slug}/`.

A categoria oficial `https://www.cesgranrio.org.br/page_category/inscricoes-abertas/` mostrou exatamente um item no snapshot: `Transpetro 2026`, detalhe `https://www.cesgranrio.org.br/concurso/transpetro-2026/`. Categorias adicionais da página incluem parâmetros `ucat=25`, `ucat=26` e `ucat=27`; seguir os hrefs reais em vez de presumir significado numérico.

### API Angular confirmada

O bundle público `https://concursos.cesgranrio.org.br/main.6f687297e0226b96.js` define:

- `GET https://concursos.cesgranrio.org.br/api/PortalEventos`
- parâmetros usados pelo frontend: `nome`, `status`, `page` (base 1) e `pageSize` (10); homepage usa também `destaque=true` e `pageSize=3`.
- `GET /api/PortalEventos/{id}`.
- `GET /api/PortalEventos/codigo/{guid}`.
- `GET /api/PortalEventoConteudos/publico/{eventoId}`.
- `GET /api/PortalGruposProva/todos/{eventoId}`.

Para o evento 22 (`TRANSPETRO 2026`), as três rotas públicas retornaram `200`. O detalhe contém `id`, `codigo`, `dataInicio`, `dataFim`, `nome`, cliente/razão social, descrição, tipo e publicação. `PortalEventoConteudos/publico/22` retorna seções HTML, inclusive `ACESSO AOS EDITAIS` e resultados. `PortalGruposProva/todos/22` retorna grupos, cargos, requisitos, salários e `taxaInscricao`.

### Conclusão e instrução

- Estratégia preferida: `REST_API`, mantendo o catálogo WordPress como discovery/validação de categorias e fallback.
- Usar `PortalEventos` paginado; abrir detalhes, conteúdos públicos e grupos de prova.
- Não usar `dataFim` do evento como sinônimo de inscrições abertas; a categoria WordPress e o cronograma/conteúdo devem determinar o estado.
- URLs de mídia possuem tokens SAS com expiração; nunca persistir a query assinada como identidade. Persistir o caminho estável/documento e renovar pelo endpoint.
- Filtrar vestibulares e avaliações acadêmicas. Criar fixture do evento 22 e testes de paginação, conteúdo público, cargos e URL assinada.

## Fonte 29 — Reis & Reis

### Frontend e API confirmados

O portal novo é Astro. A página `https://novo.reisauditores.com.br/concursos-em-andamento` embute o componente:

- `/_astro/ConcursosPagination.DxmG8JD1.js`
- props de situação: `PUBLICADO,INSCRICAO_ABERTA,ANDAMENTO`.

A página encerrada embute `CONCLUIDO`.

O módulo público define:

- base: `https://api.gestaoselecoes.com.br`
- `GET /api/editais?page={page}&size=9&situacao={lista}&order=DESC`
- header obrigatório: `X-TenantID: reisauditores`
- paginação base 0; resposta Spring Page com `content`, `totalPages`, `totalElements`, `number`, `last` e `empty`.

A chamada da página em andamento retornou um item no snapshot, ID 70, Prefeitura Municipal de Itabirinha, Concurso Público 1/2025, `situacaoEdital=PUBLICADO`, porém `situacaoInscricao=ENCERRADAS` e `inscricoesAbertas=false`.

O card aponta para `/editais/{id}`. `https://novo.reisauditores.com.br/editais/70` respondeu `200` e embutiu, nos props do componente `TabsEdital`, objetos completos de `edital`, `cargos` e `anexos`. Campos observados: órgão, tipo, número/ano, situação, datas, totais, isenções, cargos, requisitos, taxa, vagas, URLs S3, título/data/tipo de cada publicação.

### Conclusão e instrução

- Reclassificar de `HYBRID/PLAYWRIGHT` para `REST_API` no discovery + `HTTP_HTML` no detalhe.
- Não considerar todo item retornado pela página “em andamento” como inscrição aberta; usar `situacaoInscricao` e `inscricoesAbertas`.
- Paginar até `last=true`; usar `CONCLUIDO` para encerrados.
- Deduplicar anexos por `id`/URL e preservar `tipo`.
- Fixture ID 70; testes do header tenant, paginação, inscrição encerrada, cargos e anexos.

## Health-checks ainda inconclusivos

- Fonte 08 SEPROD: `https://www.seprod.com.br/concursos/` falhou na negociação TLS no cliente direto. Não é evidência de empty; testar browser/TLS legado e manter `KEEP_BLOCKED` se persistir.
- Fonte 28 IUDS: domínio principal e `portal.iuds.org.br` falharam na negociação TLS no cliente direto. Detalhes históricos/CDN existem; não declarar portal ativo nem vazio sem browser.
- Fonte 34 CONTEMAX: a homepage não produziu resposta HTTP reproduzível no cliente direto; manter `SITE_OFFLINE/UNKNOWN_EMPTY`, sem deprecar definitivamente apenas por essa tentativa.

## Fonte 25 — Leandro Ferreira Consultoria: correção de identidade

### Evidência direta

- A identidade cadastrada no projeto é `Leandro Ferreira & Consultoria`, ID técnico `leandroferreira_open`, URL `https://www.leandroferreira.com.br`.
- Em consulta DNS direta de 30/08/2026, `www.leandroferreira.com.br` não existia; o domínio raiz retornou somente o SOA da zona, sem endereço A utilizável.
- Busca restrita ao domínio e ao nome da fonte não revelou portal sucessor atribuível à consultoria.
- `https://www.leandroferreira.mg.gov.br/` é o portal oficial do município de Leandro Ferreira/MG. A coincidência de nome não comprova sucessão nem vínculo com a consultoria cadastrada.

### Conclusão corrigida

- Não substituir a fonte 25 pelo portal municipal.
- Classificar a fonte como `DNS_INACTIVE` / `IDENTITY_UNCONFIRMED`; discovery, totais, exemplos, seletores e URL substituta permanecem `UNKNOWN`.
- Recomendação: `DEPRECATE_REVIEW_REQUIRED`, preservando o ID técnico apenas por compatibilidade até que um sucessor primário seja comprovado.
- O material de PSS do município pode ser uma fonte independente válida em outro inventário, mas está fora do escopo desta identidade entre as 99 fontes.

## Fonte 47 — Elo Assessoria: API Gestão Seleções confirmada

### Frontend e chamadas reproduzidas

O módulo público `https://novo.eloassessoriaeservicos.com.br/_astro/ConcursosSection.DhIge_VT.js` usa explicitamente:

- base `https://api.gestaoselecoes.com.br`;
- `GET /api/editais?page={page}&size={size}&situacao={lista}&order=DESC`;
- header `X-TenantID: eloassessoria`;
- páginas base 0 e resposta Spring Page (`content`, `totalElements`, `totalPages`, `last`, `empty`);
- grupos `PUBLICADO,INSCRICAO_ABERTA,ANDAMENTO`, `PROXIMO` e `CONCLUIDO`.

Também foram reproduzidos com `200 application/json`:

- `GET /api/editais/134`;
- `GET /api/editais/134/cargos`;
- `GET /api/editais/134/anexos`.

No snapshot de 30/08/2026, o grupo corrente devolveu 7 registros: 3 com `inscricoesAbertas=true` (IDs 134, 133 e 129), 3 em `situacaoInscricao=EM_BREVE` e 1 com inscrições encerradas. `PROXIMO` devolveu 3 e `CONCLUIDO` informou 123. Essas categorias se sobrepõem semanticamente e não devem ser somadas como universo deduplicado.

### Conclusão e instrução

- Reclassificar de `PLAYWRIGHT/HYBRID` para `REST_API`; browser não é necessário para discovery ou detalhe.
- Tratar Elo e Reis & Reis como tenants da mesma engine Gestão Seleções, compartilhando cliente/paginação, mas mantendo header e regras por tenant.
- Usar `inscricoesAbertas` e `situacaoInscricao`, nunca apenas `situacaoEdital=PUBLICADO`, para o estado de inscrição.
- Fixture recomendada: ID 134, com detalhe, 3 cargos e 2 anexos; testar também item futuro e item encerrado dentro do grupo corrente.

## Fonte 81 — FAPEAL: concurso de pessoal corrente encontrado fora do arquivo de fomento

### Evidência oficial

O endpoint público do CEBRASPE confirmou o concurso `FAPEAL_26`:

- `GET https://apis.cebraspe.org.br/cebraspe/eventos/FAPEAL_26` — `200 application/json`;
- ID 3342, nome `FAPE AL 26`, 10 vagas, remuneração máxima `R$ 5.767,15`;
- inscrições de 15/05/2026 a 19/06/2026, atualmente fechadas;
- 23 arquivos de edital e 22 de gabarito no detalhe;
- presente na fase oficial `Em Andamento` da coleção CEBRASPE.

O edital de abertura oficial (`Edital nº 1 — FAPEAL, de 7 de maio de 2026`) declara concurso público para provimento e cadastro de reserva no cargo de Gestor Especializado em Ciência e Tecnologia, executado pelo CEBRASPE. Página operacional: `https://www.cebraspe.org.br/concursos/FAPEAL_26`; documentos: `https://cdn.cebraspe.org.br/concursos/FAPEAL_26/arquivos/...`.

### Conclusão e instrução

- Corrigir a conclusão do BATCH 07: a fonte 81 não está vazia para pessoal.
- `Observed >= 1`, `Relevant >= 1`; processo em andamento, inscrições fechadas na data da pesquisa.
- Prioridade `P0` porque limitar discovery às categorias de editais científicos da homepage FAPEAL produziria false empty.
- Usar a API CEBRASPE como origem operacional do concurso e o portal FAPEAL como origem institucional complementar; deduplicar pelo identificador `FAPEAL_26`/edital 1/2026.
- Testar que fomento continua excluído e que o concurso de Gestor permanece incluído mesmo fora do arquivo editorial de chamadas da fundação.
