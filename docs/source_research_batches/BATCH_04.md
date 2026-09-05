# BATCH 04 — pesquisa operacional de fontes 40–52

Data da pesquisa: 30/08/2026 (America/Sao_Paulo). O lote cobre exclusivamente as fontes 40–52. A contagem `observed` é o que foi visível na página consultada; `relevant` é o subconjunto que atende ao escopo de concursos/processos seletivos para trabalho; `active` é a situação indicada pelo próprio portal (não uma inferência feita apenas pela data). Quando a aplicação é dinâmica ou o total não foi exposto, o valor é `UNKNOWN`.

## 40 — UFU / DIRPS

Identificador técnico: `ufu_selection`

### Identidade e URL

- URL fornecida: https://www.portalselecao.ufu.br/servicos/Edital/listar/concursos
- URL oficial confirmada: https://www.portalselecao.ufu.br/servicos/Edital/listar/concursos
- Alternativa oficial de categorização: https://www.portalselecao.ufu.br/servicos/edital/listar
- Portal: Portal de Seleção DIRPS/UFU, Universidade Federal de Uberlândia.

### Navegação e evidência

A página de concursos entrega HTML server-rendered com uma lista longa e histórica. No topo da consulta foram observados os editais INFIS 144/2026, IFILO 143/2026, IQUFU 142/2026, INFIS 141/2026, ICENP 140/2026, FAMED 139/2026, FAMED 137/2026, ICIAG 136/2026, FACES 135/2026, ICIAG 133/2026 e FACES 132/2026. Os primeiros registros observados têm inscrição até 03/09/2026 14:59. O mesmo portal também exibe categorias que não são vagas de trabalho (cursos, vestibular, aplicação de provas, declaração RSC e outros DIRPS).

Exemplo real: https://www.portalselecao.ufu.br/servicos/Edital/cronograma/1843 — “Processo Seletivo Simplificado Visitante INFIS – Edital nº 144/2026”. A página mostra situação aberta, órgão/unidade, e-mail de inscrição, janela 19/08/2026 15:00–03/09/2026 14:59, edital geral/específico, projeto e retificação. Salário, requisitos completos, vagas e taxa normalmente exigem o edital/PDF; não devem ser inventados a partir do card.

### Contagens independentes

- `observed`: `UNKNOWN` (lista histórica extensa, sem total explícito; 11 registros atuais de pessoal visíveis no topo).
- `relevant`: pelo menos 11 atuais, além de muitos registros históricos relevantes; total `UNKNOWN`.
- `active`: 11 registros atuais de pessoal observados na página `/concursos`. A categoria “Técnico Administrativo e Docente” em `/edital/listar` exibia 4 no recorte consultado; é uma visão categorizada e não deve ser somada à lista principal.
- `closed`: `UNKNOWN`; a página contém muitos registros com “Inscrições Encerradas”.
- Fora do escopo: cursos, vestibular, aplicações de prova, RSC, credenciamento e outros serviços DIRPS sem provimento/seleção de pessoal.

### API/XHR, paginação e tecnologia

- Nenhum endpoint REST/XHR foi observado. Não presumir uma API.
- Não há paginação exposta no HTML consultado; a lista histórica parece ser entregue em uma página longa.
- Tecnologia observada: `SERVER_RENDERED / HTTP_HTML`; os cards e a página de cronograma são legíveis sem depender de interação JavaScript.
- Links de detalhe observados no padrão `/servicos/Edital/cronograma/{id}`. O padrão é evidência de navegação, não autorização para inventar seletores CSS.

### Empty evidence e bloqueios

Não é uma fonte vazia: há editais atuais e histórico. Nenhum bloqueio de acesso foi observado. O principal risco é mistura de produtos DIRPS, exigindo filtro semântico por tipo de edital e finalidade.

### Quality gate

Aceitar Concurso Público, Processo Seletivo Simplificado, professor, técnico-administrativo e visitante quando houver vaga/contratação. Rejeitar curso, vestibular, prova/serviço administrativo, RSC e páginas que apenas anunciem avaliação acadêmica. Para um edital aceito, exigir título, órgão, datas e pelo menos um link de edital/publicação; marcar detalhes ausentes como `UNKNOWN`.

### Estratégia e instruções concretas ao Codex

Usar `CONFIGURABLE_HTML` se o coletor comportar páginas UFU; caso contrário, um conector dedicado de HTML é mais seguro que tentar XHR. Percorrer a lista oficial e os cronogramas dos links observados, preservando texto/URL/data de captura. Não juntar a categoria “Técnico Administrativo e Docente” com `/concursos` sem deduplicação por identificador. Baixar/registrar PDFs de edital apenas quando o link estiver presente; não extrair salário/vagas por inferência. Se futuramente aparecer paginação ou uma lista carregada por JS, registrar o mecanismo primeiro e só depois parametrizar.

### Confiança

`HIGH` para existência, HTML e exemplos; `MEDIUM` para a contagem total, pois a página não fornece total canônico.

### Evidências

- https://www.portalselecao.ufu.br/servicos/Edital/listar/concursos
- https://www.portalselecao.ufu.br/servicos/edital/listar
- https://www.portalselecao.ufu.br/servicos/Edital/cronograma/1843
- https://www.portalselecao.ufu.br/sisarq/Processos/listarProcessosRecentes

## 41 — IDGRAN

Identificador técnico: `idgran_open`

### Identidade e URL

- URL fornecida: https://idgran.com.br
- URL oficial confirmada: `UNKNOWN`; a URL fornecida retornou erro interno na consulta web.
- Não foi possível confirmar domínio alternativo oficial. Variações `www`, `.org.br`, `.com.br`, `.com` e `.org` também não produziram portal verificável.

### Navegação e evidência

Nenhuma página de concursos, edital ou candidato foi recuperada. A busca pelo nome e domínio não encontrou um resultado oficial atual que possa ser usado como prova reproduzível.

### Contagens independentes

- `observed`: `UNKNOWN`.
- `relevant`: `UNKNOWN`.
- `active`: `UNKNOWN`.
- `closed`: `UNKNOWN`.
- Fora do escopo: `UNKNOWN`.

### API/XHR, paginação e tecnologia

- API/XHR: `UNKNOWN`; nenhum endpoint deve ser inventado.
- Paginação: `UNKNOWN`.
- Tecnologia: `UNKNOWN`.

### Empty evidence e bloqueios

Isto não é evidência de portal vazio. A URL retornou erro interno/inacessibilidade e o domínio alternativo não foi confirmado. Bloqueio classificado como `UNVERIFIED_DOMAIN / HTTP_INTERNAL_ERROR`; pode ser domínio descontinuado, DNS/TLS ou bloqueio do runtime.

### Quality gate

Não aceitar nenhum item até a identidade do portal e uma página oficial de edital serem confirmadas. Não marcar como “sem concursos”.

### Estratégia e instruções concretas ao Codex

Manter em `KEEP_BLOCKED`/`REVIEW_REQUIRED`. Repetir futuramente DNS, TLS e HTTP a partir do runtime de coleta; verificar apenas resultados cujo domínio possa ser comprovado como IDGRAN. Quando houver domínio confirmado, registrar uma página de listagem e um detalhe antes de criar seletor, endpoint ou regra de contagem. Não preencher `active=0` com base neste bloqueio.

### Confiança

`HIGH` para inacessibilidade da URL fornecida; `LOW` para qualquer afirmação sobre o universo de editais.

### Evidências

- https://idgran.com.br
- Consultas nominais por “IDGRAN concurso” e pelo domínio não retornaram fonte oficial confirmável; nenhum URL alternativo é promovido neste relatório.

## 42 — Quadrix

Identificador técnico: `quadrix_open`

### Identidade e URL

- URL fornecida: https://quadrix.org.br/index/abertos/
- URL oficial confirmada: https://quadrix.org.br/index/abertos/
- Portal de concurso da Quadrix; usa a plataforma compartilhada `selecao.net.br` para anexos/recursos.

### Navegação e evidência

`/index/abertos/` mostrou 2 concursos com inscrição aberta: CREF-SE, edital 01/2026, 17/08–21/09/2026, 170 vagas; e Prefeitura de Cristalina-GO, edital 01/2026, 07/08–10/09/2026, 1.136 vagas. A categoria “Em andamento” (`/index/1/`) mostrou “Mostrando 1–10 de 30”. A categoria “Encerrados” (`/index/3/`) mostrou “1–10 de 752”.

Exemplo real: https://quadrix.org.br/informacoes/3070/ — CREF-SE, Concurso Público, edital 01/2026, situação “Em andamento”, inscrição 17/08 10:00–21/09 23:00, tabela com 200 Assistente Administrativo (nível médio, taxa R$60), 400 Advogado, 401 Agente de Fiscalização e 402 Contador (nível superior, taxa R$63). A página de publicação do edital e PDF confirma órgão, cronograma, localização e dados do certame. PDFs observados em `https://anexos-r2.selecao.net.br/uploads/861/concursos/3070/anexos/...pdf`.

### Contagens independentes

- `observed`: 2 em “Abertos”; 30 em “Em andamento”; 752 em “Encerrados” (contagens próprias de cada categoria, não somar como universo deduplicado).
- `relevant`: 2 abertos + 30 em andamento, sujeitos a excluir itens identificados como exame/certificação sem vaga.
- `active`: 30 na categoria “Em andamento”; os 2 “Abertos” são o subconjunto com janela de inscrição aberta observado.
- `closed`: 752 na categoria “Encerrados”.
- Fora do escopo: exames de suficiência/certificações ou outros eventos sem provimento de cargo.

### API/XHR, paginação e tecnologia

- Nenhum endpoint de API/XHR foi observado.
- Paginação reproduzível: `https://quadrix.org.br/index/1/?dir=&ord=&pg=2&pp=10&q=` mostra 11–20 de 30; a categoria encerrada usa o mesmo formato (`pg`, `pp=10`, `q`, `dir`, `ord`).
- Tecnologia: HTML server-rendered; a lista e detalhes ficam visíveis por HTTP. Imagens e documentos usam a infraestrutura compartilhada `selecao.net.br`.
- Detalhes observados em `/informacoes/{id}/`; não assumir seletores CSS não verificados.

### Empty evidence e bloqueios

Não vazio. Sem CAPTCHA/WAF bloqueando a consulta web. A quantidade e o texto mudam por categoria, portanto o coletor deve preservar a categoria de origem.

### Quality gate

Aceitar Concurso Público, Processo Seletivo e seleção para cargo/emprego, extraindo órgão, edital, situação, inscrições, cargos, vagas, remuneração, taxa e publicações quando presentes. Rejeitar exame de suficiência ou certificação que não seja seleção de pessoal.

### Estratégia e instruções concretas ao Codex

Implementar como `CONFIGURABLE_HTML` da família `selecao.net.br`: base do tenant, `/index/abertos/`, `/index/1/`, `/index/3/`, paginação com `pg`/`pp`, e detalhes `/informacoes/{id}/`. Capturar documentos sob `anexos-r2.selecao.net.br` apenas pelos hrefs efetivamente encontrados. Deduplicar um mesmo ID visto em “Abertos” e “Em andamento”; manter status/categoria separados. Não tratar o total 752 como número de vagas.

### Confiança

`HIGH`.

### Evidências

- https://quadrix.org.br/index/abertos/
- https://quadrix.org.br/index/1/
- https://quadrix.org.br/index/3/
- https://quadrix.org.br/index/1/?dir=&ord=&pg=2&pp=10&q=
- https://quadrix.org.br/informacoes/3070/

## 43 — Gualimp

Identificador técnico: `gualimp_open`

### Identidade e URL

- URL fornecida: https://www.gualimp.com.br
- URL oficial confirmada: https://www.gualimp.com.br/concursos/
- Plataforma de processos ligada também a https://gualimpconsultoria.com.br/processos_de_selecao/ps.html?detail=134 e ao domínio histórico `gualimpconsultoria.com.br`.

### Navegação e evidência

A página principal e `/concursos/` são HTML e exibem “Concursos em andamento — Atualizado em 31 de Julho de 2024” e, de forma explícita, “Nenhum concurso em andamento até o momento!”. Abaixo permanecem muitos cartões históricos, incluindo Prefeitura de Porciúncula 002/2019, Alfredo Chaves 001/2023, Muqui PSS 001/2023, Bom Jardim 001/2022 e Divino 001/2022. Os links apontam para `gualimpconsultoria.com.br` com `?detail={id}`.

Exemplo real: https://gualimpconsultoria.com.br/processos_de_selecao/ps.html?detail=134 — Concurso Público 001/2023 da Prefeitura Municipal de Alfredo Chaves/ES. O HTML inicial mostra “Carregando...” para processos/publicações/avisos; a indexação oficial registra edital, isenção, homologação, resultados, retificações e convocações. É uma evidência de detalhe histórico, não de inscrição atual.

### Contagens independentes

- `observed`: `UNKNOWN` (muitos cartões, sem total canônico).
- `relevant`: `UNKNOWN`; os cartões observados são majoritariamente concursos/PSS e históricos.
- `active`: 0 explicitamente na página principal, que afirma não haver concurso em andamento.
- `closed`: muitos históricos, total `UNKNOWN`.
- Fora do escopo: itens de serviços/notícias que não sejam processo seletivo.

### API/XHR, paginação e tecnologia

- Nenhum endpoint XHR foi localizado. O detalhe retorna placeholders “Carregando...”, sinal de dados montados por JavaScript, mas o endpoint não foi confirmado.
- Paginação: `UNKNOWN`; não há paginação claramente exposta na listagem consultada.
- Tecnologia: listagem principal `SERVER_RENDERED / HTTP_HTML`; detalhe do domínio consultoria é `DYNAMIC_JS`/possível XHR.

### Empty evidence e bloqueios

Há `EMPTY_EXPLICIT` somente para a categoria atual da página principal, mas não para o acervo histórico. A atualização declarada é antiga e há divergência entre o status do site principal e a plataforma consultoria; classificar como fonte potencialmente stale, não como descontinuada.

### Quality gate

Aceitar concurso público, PSS e convocações/retificações ligadas a cargos. Exigir prova de órgão, número do edital e publicação. Não converter o cartão histórico em `active` sem data/status atual confirmados; excluir serviços e notícias institucionais.

### Estratégia e instruções concretas ao Codex

Usar `HYBRID / PLAYWRIGHT`: obter a listagem HTML no domínio principal e abrir a página dinâmica da consultoria em navegador real. Preservar `active=0` para a frase explícita da página principal, porém manter o acervo histórico. Não inventar endpoint para substituir “Carregando...”; se o navegador permitir observar XHR em runtime, registrar URL/método/resposta antes de automatizar. Tratar `gualimpconsultoria.com.br` como domínio oficial alternativo somente quando o link vier do site Gualimp.

### Confiança

`MEDIUM-HIGH` para lista e vazio atual; `MEDIUM` para atualização/status por ser stale.

### Evidências

- https://www.gualimp.com.br/concursos/
- https://www.gualimp.com.br
- https://gualimpconsultoria.com.br/processos_de_selecao/ps.html?detail=134
- https://www.gualimpconsultoria.com.br/

## 44 — Instituto Verbena / UFG

Identificador técnico: `verbena_selection`

### Identidade e URL

- URL fornecida: https://institutoverbena.ufg.br
- URL oficial confirmada: https://institutoverbena.ufg.br
- Portais relacionados: https://sistemas.institutoverbena.ufg.br/portal/login, https://sistemas.institutoverbena.ufg.br/cms/home e https://sistemas.ufg.br/CONCURSOS_WEB/ (este último é SISCONCURSO UFG e não deve ser mesclado automaticamente).

### Navegação e evidência

A homepage é um portal de notícias UFG com paginação de notícias (páginas 1–5). No recorte atual foram observadas notícias sobre Educação Intercultural 2027, Minaçu, trainee Sebrae GO, Câmara de Mutunópolis e Prefeitura de Carmo do Rio Verde, além de notícias de treinamento/localização.

Exemplos reais:

- https://institutoverbena.ufg.br/n/203922-instituto-verbena-ufg-divulga-cronograma-b-do-concurso-de-minacu — Cronograma B e inscrições de concurso de Minaçu, com cargos médicos; seleção de pessoal.
- https://institutoverbena.ufg.br/n/203903-inscricoes-abertas-para-o-processo-seletivo-do-programa-trainee-sebrae-goias — 6 vagas de trainee em Goiânia, CLT por prazo determinado, R$5.521,88, 26/08–09/09/2026, taxa R$100.
- https://institutoverbena.ufg.br/n/203739-camara-municipal-de-mutunopolis-abre-concurso-publico-com-sete-vagas — 7 vagas imediatas + 21 CR, cargos e salários R$1.630–5.000, inscrição 18/09–08/10/2026.
- https://institutoverbena.ufg.br/n/203730-prefeitura-de-carmo-do-rio-verde-abre-concurso-publico — 6 vagas imediatas + 18 CR para Professor P-III, R$3.847,97, inscrição 25/09–26/10/2026.

O item https://institutoverbena.ufg.br/n/203998-instituto-verbena-ufg-publica-edital-do-processo-seletivo-educacao-intercultural-2027 é admissão/educação para licenciatura indígena (40 vagas), não contratação; deve ser rejeitado pelo filtro.

### Contagens independentes

- `observed`: 8 notícias visíveis no recorte da homepage; não é total de concursos.
- `relevant`: pelo menos 4 notícias de seleções de pessoal (Minaçu, trainee Sebrae, Mutunópolis e Carmo); total de processos `UNKNOWN`.
- `active`: `UNKNOWN`. Há inscrições abertas ou futuras nas notícias, mas notícia não é uma lista canônica de status e não se deve converter “publicado” automaticamente em ativo.
- `closed`: `UNKNOWN`.
- Fora do escopo: admissão acadêmica (Educação Intercultural), treinamentos, localização e notícias sem vaga/seleção de trabalho.

### API/XHR, paginação e tecnologia

- O portal de notícias tem links de paginação HTML; o CMS/sistemas usa formulários/seletores de ano e tipo e não expôs endpoint API verificável.
- API/XHR: `UNKNOWN`; não inventar URL de consulta.
- Tecnologia: homepage `SERVER_RENDERED / UFG portal`; CMS/candidato potencialmente `DYNAMIC_JS`.

### Empty evidence e bloqueios

Não vazio, mas não existe uma listagem simples de “todos os concursos atuais” confirmada no portal de notícias. O login do candidato e o CMS podem exigir navegador. O SISCONCURSO UFG é uma fonte oficial relacionada, porém com universo possivelmente diferente.

### Quality gate

Aceitar concurso público/PSS/trainee quando o texto provar cargo, emprego, bolsa contratual ou contratação. Exigir edital, órgão, janela, vagas/cargos e link de detalhes quando disponível. Rejeitar vestibular, licenciatura/admissão estudantil, treinamento e notícia institucional sem seleção.

### Estratégia e instruções concretas ao Codex

Usar `HYBRID`: rastrear notícias oficiais para descoberta e seguir o link do edital/CMS para detalhes; usar Playwright somente se o CMS deixar campos vazios até a execução de JavaScript. Manter `observed`, `relevant` e `active` independentes da contagem de notícias. Não mesclar automaticamente o SISCONCURSO UFG com Verbena; registrar origem distinta e deduplicar só com identificador/título comprovado.

### Confiança

`MEDIUM`: notícia, cargos, datas e valores têm evidência direta, mas a descoberta/status global é incompleta.

### Evidências

- https://institutoverbena.ufg.br
- https://sistemas.institutoverbena.ufg.br/portal/login
- https://sistemas.institutoverbena.ufg.br/cms/home
- https://institutoverbena.ufg.br/p/42688-processos-seletivos-e-concursos-anteriores
- https://institutoverbena.ufg.br/n/203922-instituto-verbena-ufg-divulga-cronograma-b-do-concurso-de-minacu
- https://institutoverbena.ufg.br/n/203903-inscricoes-abertas-para-o-processo-seletivo-do-programa-trainee-sebrae-goias
- https://institutoverbena.ufg.br/n/203739-camara-municipal-de-mutunopolis-abre-concurso-publico-com-sete-vagas
- https://institutoverbena.ufg.br/n/203730-prefeitura-de-carmo-do-rio-verde-abre-concurso-publico

## 45 — IDIB

Identificador técnico: `idib_open`

### Identidade e URL

- URL fornecida: https://idib.org.br
- URL oficial confirmada: https://idib.org.br e https://concurso.idib.org.br/SITE/Concursos.aspx
- Portal canônico de concursos: `concurso.idib.org.br`.

### Navegação e evidência

A homepage oficial encaminha ao portal de concursos. A listagem server-rendered mostra “Inscrições abertas” para Uruburetama, edital 01/2026, até 08/09/2026, seguida de itens “Em andamento”.

Exemplo principal: https://concurso.idib.org.br/Concurso.aspx?ID=354 — Uruburetama, inscrição 07/07–08/09/2026, 278 vagas imediatas + cadastro reserva. A tabela mostra cargo, localidade, remuneração, vagas, requisitos e taxa; o total apresentado no resumo inclui 278 imediatas, 78? campos de tabela e 452 no detalhamento de categorias, portanto o coletor deve guardar os valores por campo e não recompor um número único sem entender o esquema. Publicações e edital aparecem na mesma página. Outro fixture: `https://concurso.idib.org.br/Concurso.aspx?ID=355` (Marco/CE, 238 imediatas, janela 15/07–24/08/2026).

### Contagens independentes

- `observed`: homepage exibiu 6 cards correntes; a listagem canônica mostra muitos itens “Em andamento”; total `UNKNOWN`.
- `relevant`: `UNKNOWN`, com predominância de concursos/PSS de prefeituras.
- `active`: pelo menos 1 (Uruburetama, inscrições abertas); não inferir que todos os itens “Em andamento” ainda aceitam inscrição.
- `closed`: `UNKNOWN`.
- Fora do escopo: cursos/capacitações ou conteúdo institucional que não seja cargo/emprego.

### API/XHR, paginação e tecnologia

- Nenhum endpoint API/XHR foi observado.
- Paginação: não exposta na consulta canônica; `UNKNOWN`.
- Tecnologia: `ASP.NET WEBFORMS / SERVER_RENDERED HTML`. A página exibe aviso “Javascript desativado”, mas conteúdo, tabelas e links ficam acessíveis no HTML.
- Detalhe observado no padrão `https://concurso.idib.org.br/Concurso.aspx?ID={id}`. Downloads seguem `ConcursoDownloadArquivo.aspx?ID=<token>&ID2=1` e há arquivos em `idibstorage.s3.amazonaws.com`; usar somente hrefs encontrados.

### Empty evidence e bloqueios

Não vazio. Não foi observado CAPTCHA/WAF impedindo listagem. Login do candidato é separado. A mistura de status (“abertas”/“em andamento”) requer preservação da origem da categoria.

### Quality gate

Aceitar Concurso Público, PSS e seleções para cargos, com órgão e edital. Extrair cargos/vagas/salário/taxa apenas quando estiverem na tabela ou documento. Rejeitar capacitação e páginas de candidato sem informações do certame.

### Estratégia e instruções concretas ao Codex

Usar `CONFIGURABLE_HTML` ou conector dedicado IDIB. Rastrear `/SITE/Concursos.aspx`, extrair links `Concurso.aspx?ID=...`, e capturar o bloco de inscrição, tabelas e publicações. Não depender de XHR nem de JavaScript. Armazenar cada contador de vagas na coluna/contexto original; não somar números de resumo de semântica desconhecida. Verificar a data de captura antes de declarar ativo.

### Confiança

`HIGH`.

### Evidências

- https://idib.org.br
- https://concurso.idib.org.br/SITE/Concursos.aspx
- https://concurso.idib.org.br/Concurso.aspx?ID=354
- https://concurso.idib.org.br/Concurso.aspx?ID=355
- https://concurso.idib.org.br/ConcursoDownloadArquivo.aspx?ID=<token>&ID2=1 (padrão observado em hrefs; token não deve ser inventado)

## 46 — JCM Consultoria

Identificador técnico: `jcm_open`

### Identidade e URL

- URL fornecida: https://eventos.concursosjcm.com.br
- URL oficial atual confirmada: https://concursosjcm.com.br/
- Também responde: https://concursos.concursosjcm.com.br/
- A URL `eventos` apresenta “Eventos – Em andamento — Nenhum item cadastrado”; é uma URL antiga/migrada.

### Navegação e evidência

O domínio atual lista 7 processos em andamento: Paiva-MG CP 001/2026 (13 vagas, futuro), Pedro Teixeira-MG CP 001/2026 (125, futuro), Prudente de Morais-MG CP 001/2026 (3, futuro), Conceição da Barra de Minas-MG CP 001/2026 (30, 19/08–18/09), Conceição da Barra de Minas-MG PSS 001/2026 (4, 19/08–18/09), Ingaí-MG CP 001/2026 (1, 12/08–11/09) e Carrancas-MG PSS 001/2026 (3, janela encerrada em 28/08, mas ainda em andamento no card).

Exemplo real: https://concursosjcm.com.br/informacoes/261/ — Conceição da Barra de Minas CP 001/2026, inscrição 19/08 08:00–18/09 16:00, 30 vagas, cargos detalhados e publicações. PDFs ficam em `anexos-r2.selecao.net.br/uploads/17/concursos/261/anexos/...pdf`. Também foi verificado `/informacoes/262/` (PSS, 4 vagas) e `/informacoes/266/` (Paiva, 13, futura).

### Contagens independentes

- `observed`: 7 cards na lista “Em andamento”.
- `relevant`: 7 (CP/PSS de municípios).
- `active`: 7 com status “Em andamento”; 3 têm janela futura e 4 têm janela aberta ou recém-encerrada na data da pesquisa. Não converter automaticamente a janela em ativo sem confirmação no card/detalhe.
- `closed`: `UNKNOWN`.
- Fora do escopo: eventos sem seleção de pessoal.

### API/XHR, paginação e tecnologia

- Nenhum endpoint REST/XHR observado.
- Paginação: não visível no recorte de 7 cards; `UNKNOWN` para conjuntos maiores.
- Tecnologia: HTML server-rendered, plataforma ProSeleta compartilhada; imagens em `static-cdn.selecao.net.br`, anexos em `anexos-r2.selecao.net.br`.
- Detalhes no padrão `/informacoes/{id}/`; categorias `/index/abertos/`, `/index/1/` e `/index/3/` são compatíveis com a plataforma compartilhada.

### Empty evidence e bloqueios

Não vazio no domínio atual. A URL fornecida `eventos` é vazia e deve ser tratada como migração, não como evidência de ausência de concursos.

### Quality gate

Aceitar CP e PSS municipais com edital, órgão, cargos e janela. Preservar “futuro”, “em andamento” e prazo de inscrição separadamente. Rejeitar evento/serviço sem vaga.

### Estratégia e instruções concretas ao Codex

Usar o mesmo `CONFIGURABLE_HTML` da família ProSeleta/selecao.net.br, com base `concursosjcm.com.br`; não apontar o coletor para `eventos` como fonte principal. Percorrer categorias e detalhes por ID, capturar publicações e PDFs pelos hrefs reais e deduplicar o mesmo edital entre categorias. Não presumir paginação até ela aparecer.

### Confiança

`HIGH` para migração, cards, detalhes e plataforma.

### Evidências

- https://eventos.concursosjcm.com.br
- https://concursosjcm.com.br/
- https://concursos.concursosjcm.com.br/
- https://concursosjcm.com.br/informacoes/261/
- https://concursosjcm.com.br/informacoes/262/
- https://concursosjcm.com.br/informacoes/266/

## 47 — Elo Assessoria

### Identidade e URL

- URL fornecida: https://eloassessoriaeservicos.com.br/concursos
- URL oficial atual confirmada: https://novo.eloassessoriaeservicos.com.br/concursos
- Portal de candidato externo: https://elo.candidato.gestaoselecoes.com.br

### Navegação e evidência

O domínio antigo falhou na consulta; o domínio `novo` é o site oficial migrado. A listagem `/concursos` contém abas “Andamento”, “Próximos” e “Encerrados”, porém o HTML retornou “Carregando concursos...”, sem total ou cards no primeiro carregamento.

Exemplos reais indexados no próprio domínio novo:

- https://novo.eloassessoriaeservicos.com.br/concurso/134 — São Geraldo do Baixio 1/2026, “Inscrições Abertas”, 19/08–17/09/2026, Processo Seletivo Público, 3 cargos e 10 vagas (ACS 4+4, ACE 2), taxa R$80 e edital datado de 12/06/2026.
- https://novo.eloassessoriaeservicos.com.br/concurso/137 — CIMAG 1/2026, publicado, janela futura 24/10–23/11/2026, CP, 2 cargos.
- https://novo.eloassessoriaeservicos.com.br/concurso/125 — Monte Carmelo 1/2025, encerrado, 7 cargos e 12 documentos.

### Contagens independentes

- `observed`: `UNKNOWN` na lista dinâmica; não converter resultados de busca em total.
- `relevant`: pelo menos 1 (São Geraldo do Baixio), mais futuros/publicados; total `UNKNOWN`.
- `active`: pelo menos 1 com inscrições abertas (São Geraldo do Baixio).
- `closed`: `UNKNOWN`.
- Fora do escopo: vestibular/educação sem contratação; conta de candidato sem edital.

### API/XHR, paginação e tecnologia

- Nenhum endpoint de API/XHR foi confirmado; o placeholder indica que a aba precisa de JavaScript para descobrir os itens.
- Paginação: `UNKNOWN`.
- Tecnologia: listagem `DYNAMIC_JS`; detalhes por `/concurso/{id}` foram indexados e podem ser lidos como HTML.

### Empty evidence e bloqueios

Não é fonte vazia. O placeholder “Carregando concursos...” é bloqueio funcional para HTTP simples; o domínio antigo também falhou. Não afirmar que a lista tem zero.

### Quality gate

Aceitar CP/PSS com órgão, cargo, vagas, período e edital. Exigir confirmação de situação no detalhe. Rejeitar itens acadêmicos ou sem seleção de pessoal.

### Estratégia e instruções concretas ao Codex

Usar `HYBRID / PLAYWRIGHT`: navegador real para abrir as abas e descobrir os IDs; HTTP para detalhes `/concurso/{id}` quando retornarem conteúdo estável. Registrar o request/response observado para a aba antes de criar um cliente de dados; não inventar API. Manter `UNKNOWN` para totais enquanto o endpoint/lista dinâmica não for capturado.

### Confiança

`MEDIUM`: domínio migrado e fixtures têm evidência forte, mas a descoberta atual depende de JavaScript.

### Evidências

- https://eloassessoriaeservicos.com.br/concursos
- https://novo.eloassessoriaeservicos.com.br/concursos
- https://novo.eloassessoriaeservicos.com.br/concurso/134
- https://novo.eloassessoriaeservicos.com.br/concurso/137
- https://novo.eloassessoriaeservicos.com.br/concurso/125
- https://elo.candidato.gestaoselecoes.com.br

## 48 — Apta Assessoria

Identificador técnico: `apta_open`

### Identidade e URL

- URL fornecida: https://www.aptaconcursos.com.br
- URL oficial confirmada: https://www.aptaconcursos.com.br
- Padrão de detalhe histórico observado: `https://aptaconcursos.com.br/concursos/publicacoes/{órgão-url-encoded}/{id}`.

### Navegação e evidência

O site abriu uma tela “Navegador incompatível com o sistema”, recomendando Firefox/Chrome/Opera/Safari. O conteúdo oficial indexado confirma a aplicação “Concursos Públicos/Processos Seletivos” e cards atuais, incluindo Câmara Municipal de Aragarças-GO CP 01/2026 e Prefeitura de Nova Ponte-MG CP 01/2026; o primeiro exibia “INSCREVER-ME”, “DOCUMENTOS” e “2ª VIA DO BOLETO”. Há acervo de 2024–2019.

Exemplos históricos reais: `https://aptaconcursos.com.br/concursos/publicacoes/PREFEITURA%20MUNICIPAL%20DE%20SANTA%20CRUZ%20DO%20RIO%20PARDO/652` e `.../IBITINGA/282`. PDFs de arquivo usam `https://arquivos.aptaconcursos.com.br/arquivos/{id}/{arquivo}.pdf`, padrão observado em resultados oficiais.

### Contagens independentes

- `observed`: `UNKNOWN` (aplicação completa não renderizada; índice mostra muitos cards).
- `relevant`: pelo menos 2 cards atuais; total `UNKNOWN`.
- `active`: pelo menos 1 card com inscrição (“INSCREVER-ME”), mas a aplicação incompatível impede confirmar o conjunto e a data.
- `closed`: muitos históricos, total `UNKNOWN`.
- Fora do escopo: vestibular, residência/curso, estágio ou processo interno que não seja contratação pública no escopo definido.

### API/XHR, paginação e tecnologia

- API/XHR: `UNKNOWN`; nenhum endpoint foi recuperado e não deve ser inventado.
- Paginação: `UNKNOWN`.
- Tecnologia: aplicação legada `DYNAMIC_JS / BROWSER_COMPATIBILITY`; HTTP simples serve a tela de incompatibilidade. Playwright/navegador real é necessário para testar a listagem.

### Empty evidence e bloqueios

Não vazio: o índice oficial e a busca exibem cards atuais. O bloqueio é de compatibilidade/browser, não `EMPTY_EXPLICIT`. Não definir active=0.

### Quality gate

Aceitar CP/PSS de prefeitura/câmara com cargo, vagas e edital. Rejeitar curso, residência, vestibular, estágio e seleção interna se não houver contratação pública do escopo. Validar “inscrever-me” com data/edital antes de marcar ativo.

### Estratégia e instruções concretas ao Codex

Usar `PLAYWRIGHT`/`HYBRID` em navegador real. Primeiro capturar screenshot/HTML após o sistema passar a tela de compatibilidade; depois registrar os requests reais da listagem e detalhes. Enquanto isso, usar apenas URLs indexadas como fixtures, sem extrapolar IDs ou total. Persistir `UNKNOWN` para API, paginação e contagens totais.

### Confiança

`MEDIUM-LOW`: existência e cards são confirmados, mas a interface atual não foi renderizada no runtime de consulta.

### Evidências

- https://www.aptaconcursos.com.br
- https://www.aptaconcursos.com.br/servicos
- https://www.aptaconcursos.com.br/sobre
- https://aptaconcursos.com.br/concursos/publicacoes/PREFEITURA%20MUNICIPAL%20DE%20SANTA%20CRUZ%20DO%20RIO%20PARDO/652
- https://arquivos.aptaconcursos.com.br/arquivos/{id}/{arquivo}.pdf (padrão observado; não inventar valores)

## 49 — Legalle Concursos

Identificador técnico: `legalle_open`

### Identidade e URL

- URL fornecida: https://portal.editais.legalleconcursos.com.br/edital
- URL oficial confirmada: https://portal.editais.legalleconcursos.com.br/edital
- Alternativa observada: https://portal.editais.legalleconcursos.com.br/edital/index/abertos

### Navegação e evidência

A lista exibe as seções “EM INSCRIÇÃO”, “EM ANDAMENTO” e “FINALIZADOS”. Foram observados quatro itens em inscrição: Relvado CP 01/2026 (14/08–13/09/2026), Francisco Alves CP 001/2026 (03/08–01/09), Canudos do Vale CP/PSS 01/2026 (30/07–02/09) e Câmara de Capão do Leão CP 01/2026 (17/08–15/09). “Em andamento” também exibe Silveira Martins, Morro Redondo, Sério e Credenciamento Médico IPE Saúde; este último não é seleção de cargo e deve ser filtrado.

Exemplo real: https://portal.editais.legalleconcursos.com.br/edital/ver/2531 — Concurso Público 01/2026 de São Lourenço do Sul/RS. O detalhe contém publicações, retificações, homologação, resultados, provas/gabaritos, cargos, requisitos, salários e links de download em S3; é uma fixture robusta mesmo sendo processo encerrado.

### Contagens independentes

- `observed`: pelo menos 4 em inscrição; pelo menos 4 em andamento (incluindo o credenciamento); finalizados muitos, total `UNKNOWN`.
- `relevant`: 4 em inscrição + pelo menos 3 em andamento após excluir credenciamento médico; total finalizado `UNKNOWN`.
- `active`: 4 com janela de inscrição exibida.
- `closed`: `UNKNOWN`.
- Fora do escopo: “Credenciamento Médico” e outros credenciamentos sem concurso/seleção para cargo.

### API/XHR, paginação e tecnologia

- Nenhuma API/XHR foi observada.
- Paginação: não visível no recorte consultado; `UNKNOWN`.
- Tecnologia: HTML server-rendered com links de detalhe `/edital/ver/{id}` e anexos em S3. Não presumir que a página inteira seja uma única consulta se a implementação mudar.

### Empty evidence e bloqueios

Não vazio. O volume de finalizados é grande; ausência de um contador explícito não é evidência de ausência.

### Quality gate

Aceitar CP/PSS com órgão, edital, cargos, datas, vagas e publicações. Excluir credenciamento/serviço médico, quando não houver provimento de cargo. Preferir o status da seção + datas do detalhe; não inferir status só pelo título.

### Estratégia e instruções concretas ao Codex

Usar conector `CONFIGURABLE_HTML` dedicado Legalle. Percorrer as três seções, seguir `/edital/ver/{id}`, registrar publicações e downloads S3 pelos hrefs reais e deduplicar por edital/ID. Manter a seção de origem para que “em inscrição” não se confunda com “em andamento”.

### Confiança

`HIGH`.

### Evidências

- https://portal.editais.legalleconcursos.com.br/edital
- https://portal.editais.legalleconcursos.com.br/edital/index/abertos
- https://portal.editais.legalleconcursos.com.br/edital/ver/2531

## 50 — RBO Assessoria

Identificador técnico: `rbo_open`

### Identidade e URL

- URL fornecida: https://rboconcursos.selecao.net.br/index/abertos/
- URL oficial confirmada: https://rboconcursos.selecao.net.br/index/abertos/
- Plataforma compartilhada ProSeleta/selecao.net.br.

### Navegação e evidência

“Abertos” mostra 2 itens: Prefeitura Estância Turística de Jahu-SP CP 02/2026, 24/08–25/09/2026, 10 vagas; e SEBRAE-SP PSS 036/2026, 28/08–03/09/2026, 1 vaga. “Em andamento” mostra “Mostrando 1–10 de 24” e inclui os PSS SEBRAE 034/033/032 e outros certames.

Exemplo real: https://rboconcursos.selecao.net.br/informacoes/203/ — Jahu CP 02/2026, status “Em andamento”, inscrição 24/08 09:00–25/09 23:59, publicações de abertura retificada/retificação e 10 cargos, um com uma vaga cada. Documentos usam `anexos-r2.selecao.net.br`.

### Contagens independentes

- `observed`: 2 abertos; 24 em andamento; finalizados/cancelados sem total consolidado.
- `relevant`: 2 + 24, sujeitos ao quality gate.
- `active`: 2 com inscrições abertas; 24 são a categoria “Em andamento” e podem incluir processos em fases posteriores.
- `closed`: `UNKNOWN`.
- Fora do escopo: nenhum item claramente fora do escopo no recorte, mas validar PSS/serviços.

### API/XHR, paginação e tecnologia

- Nenhuma API/XHR observada.
- Paginação reproduzível em `/index/1/?dir=&ord=&pg=2&pp=10&q=` e páginas seguintes; primeira página informa 1–10/24.
- Tecnologia: HTML server-rendered, tenant ProSeleta. Detalhe `/informacoes/{id}/`, imagens `static-cdn.selecao.net.br`, PDFs `anexos-r2.selecao.net.br`.

### Empty evidence e bloqueios

Não vazio, sem bloqueio de listagem. Separar categoria e status real do detalhe.

### Quality gate

Aceitar CP/PSS e processos com cargo/emprego, edital e publicação. Filtrar credenciamento, curso ou serviço caso apareça em categoria genérica.

### Estratégia e instruções concretas ao Codex

Reutilizar o conector configurável ProSeleta: tenant base RBO, categorias, parâmetros observados `dir`, `ord`, `pg`, `pp`, `q`, detalhes por ID e anexos por href. Não somar 2+24 como total único sem deduplicação; o mesmo item pode aparecer nas categorias. Registrar data/status da página de detalhe.

### Confiança

`HIGH`.

### Evidências

- https://rboconcursos.selecao.net.br/index/abertos/
- https://rboconcursos.selecao.net.br/index/1/
- https://rboconcursos.selecao.net.br/index/1/?dir=&ord=&pg=2&pp=10&q=
- https://rboconcursos.selecao.net.br/informacoes/203/

## 51 — SHDias

Identificador técnico: `shdias_open`

### Identidade e URL

- URL fornecida: https://www.shdias.com.br/concursos/
- URL oficial confirmada: https://www.shdias.com.br/concurso
- A aplicação também aparece em `https://shdias.com.br/concursos/index/?busca=&status=andamento`.

### Navegação e evidência

A aplicação tem abas “Inscrições abertas”, “Em breve”, “Em andamento” e “Finalizado”. O recorte indexado da aba de abertas mostrou 3 cards, todos com “Inscrições abertas Até 25/08/2026”: Prefeitura de Salto CP 002/2026 (42 vagas, 35 cargos, até R$18.552,60), Prefeitura de Salto PSS 001/2026 ACS/ACE (1 vaga, 9 cargos, até R$3.267) e Hortolândia CP 001/2026 Guarda (36 vagas, 2 cargos, até R$3.971,37).

A consulta de “andamento” mostrou 7 cards (Hortolândia, Salto, PSS Salto, PPIPETS 001/2024, Elias Fausto CPPMEF 001/2023, Paulínia PSPMP 002/2018 e Paulínia CPPMP 001/2018); uma variante `www` mostrou somente 4 cards. Essa divergência de domínio/filtro deve ser preservada e revisada.

Exemplos de detalhes: `https://www.shdias.com.br/concursos/publicacoes/PREFEITURA%2BMUNICIPAL%2BDE%2BELIAS%2BFAUSTO/277` (CP 001/2023, 34 vagas, publicações); `https://www.shdias.com.br/concursos/publicacoes/PREFEITURA%2BDA%2BEST%C3%82NCIA%2BTUR%C3%8DSTICA%2BDE%2BSALTO/276` (PSS encerrado, 4 vagas). PDFs usam `https://arquivo.shdias.com.br/arquivos/...pdf`.

### Contagens independentes

- `observed`: 3 na aba aberta do recorte indexado; 7 em andamento na variante sem `www`, 4 na variante `www`.
- `relevant`: os CP/PSS observados; excluir qualquer curso/serviço sem seleção. Total `UNKNOWN`.
- `active`: site rotulou 3 como abertas, mas a data “até 25/08/2026” já passou na data da pesquisa (30/08); tratar como `UNKNOWN_NEEDS_LIVE_VALIDATION`, não como 0 nem como ativo confirmado.
- `closed`: `UNKNOWN`.
- Fora do escopo: cursos, atendimento e itens não relacionados a cargo.

### API/XHR, paginação e tecnologia

- Nenhum endpoint API/XHR confirmado.
- Paginação: `UNKNOWN`.
- Tecnologia: aplicação legada `DYNAMIC_JS / BROWSER_COMPATIBILITY`; HTTP direto retornou tela de incompatibilidade, enquanto resultados indexados expõem os cards e detalhes.
- Detalhes no padrão `/concursos/publicacoes/{organização-url-encoded}/{id}`; PDFs no host `arquivo.shdias.com.br`.

### Empty evidence e bloqueios

Não é fonte vazia. O bloqueio de compatibilidade e a divergência entre URLs/status são os riscos principais. A janela de inscrição expirada no texto indexado torna a confirmação em tempo real obrigatória.

### Quality gate

Aceitar CP/PSS para cargo, com órgão, edital, vagas, cargos, salário e datas. Não declarar active com base somente no nome da aba; conferir data/status e detalhe. Excluir conteúdo não seletivo.

### Estratégia e instruções concretas ao Codex

Usar `PLAYWRIGHT / HYBRID`: testar navegador real compatível, capturar a lista após o JavaScript e registrar os requests observados. Consultar tanto `/concurso` quanto a variante `status=andamento`, preservando o domínio/URL de origem até explicar a divergência. Manter os 3 como “rótulo aberto observado” e separar de `active_confirmed`; atualizar com data de captura. Não inventar API/paginação.

### Confiança

`MEDIUM` (cards e detalhes confirmados; aplicação dinâmica e status conflitante).

### Evidências

- https://www.shdias.com.br/concurso
- https://shdias.com.br/concursos/index/?busca=&status=andamento
- https://www.shdias.com.br/concursos/publicacoes/PREFEITURA%2BMUNICIPAL%2BDE%2BELIAS%2BFAUSTO/277
- https://www.shdias.com.br/concursos/publicacoes/PREFEITURA%2BDA%2BEST%C3%82NCIA%2BTUR%C3%8DSTICA%2BDE%2BSALTO/276
- https://arquivo.shdias.com.br/arquivos/...pdf (padrão observado; não inventar caminho final)

## 52 — Zambini

Identificador técnico: `zambini_open`

### Identidade e URL

- URL fornecida: https://www.zambini.org.br/portal/concursos
- URL oficial confirmada: https://www.zambini.org.br/portal/concursos
- Histórico: https://www.zambini.org.br/portal/concursos/encerrados

### Navegação e evidência

A página atual contém o título “CONCURSOS EM ANDAMENTO” e a frase explícita “No momento não temos nenhum concurso em andamento.” O link de encerrados leva a uma lista histórica. Exemplo real de encerrado: https://www.zambini.org.br/portal/concursos/ver/1966 — Concurso 01/2022 da Prefeitura de Cabreúva/SP, 40 vagas + cadastro reserva, cargos administrativos, guarda, professor, enfermagem e vigia, inscrições 04–13/03/2022; o detalhe mostra etapa, homologação, retificações, resultados e convocações.

### Contagens independentes

- `observed`: 0 em andamento (frase explícita); histórico encerrado separado.
- `relevant`: 0 atuais; histórico relevante existe, total `UNKNOWN`.
- `active`: 0 explicitamente no portal atual.
- `closed`: `UNKNOWN`.
- Fora do escopo: cursos para GCM, serviços gráficos/consultoria e links administrativos.

### API/XHR, paginação e tecnologia

- Nenhum endpoint API/XHR observado.
- Paginação: não observada na página atual; `UNKNOWN` no histórico.
- Tecnologia: `STATIC_HTML / HTTP_HTML`; o vazio atual e o detalhe histórico foram legíveis sem interação JavaScript.

### Empty evidence e bloqueios

`EMPTY_EXPLICIT` para concursos em andamento. Isto não significa que a fonte não tenha histórico; preservar o link de encerrados e não eliminar o tenant.

### Quality gate

Aceitar concursos públicos/PSS com cargo/emprego e edital quando surgirem. Rejeitar serviços, cursos GCM e conteúdo sem processo seletivo de pessoal. Marcar ativo somente com sinal explícito de inscrição/status e data.

### Estratégia e instruções concretas ao Codex

Usar `KEEP_EMPTY / HTTP_HTML`: consultar a página atual, registrar a frase vazia e verificar periodicamente a lista de encerrados apenas para histórico. Não criar seletor de API ou inferir próximos concursos. Se a frase mudar, reabrir a investigação da listagem antes de preencher contagens.

### Confiança

`HIGH` para vazio atual e exemplo histórico; `MEDIUM` para total histórico.

### Evidências

- https://www.zambini.org.br/portal/concursos
- https://www.zambini.org.br/portal/concursos/encerrados
- https://www.zambini.org.br/portal/concursos/ver/1966

## Oportunidade de plataforma compartilhada

Quadrix, JCM e RBO foram observados com a mesma família de páginas ProSeleta/`selecao.net.br`: categorias `/index/abertos/`, `/index/1/`, `/index/3/`, detalhes `/informacoes/{id}/`, parâmetros de paginação `dir`, `ord`, `pg`, `pp=10`, `q`, imagens `static-cdn.selecao.net.br` e anexos `anexos-r2.selecao.net.br`. Recomenda-se um conector configurável por tenant/base URL, com quality gate e deduplicação por tenant + ID; não assumir que contagens ou categorias sejam iguais em todos os tenants.

## Quality gate do lote

- Fontes com acesso e evidência suficiente para implementação inicial: UFU/DIRPS, Quadrix, IDIB, JCM, Legalle, RBO e Zambini (com particularidades acima).
- Fontes que exigem navegador/dados dinâmicos antes de automatizar: Gualimp (detalhe), Verbena/CMS, Elo, Apta e SHDias.
- Fonte explicitamente vazia: Zambini atual; Gualimp também declara 0 em andamento, mas conserva histórico e tem atualização stale.
- Fonte bloqueada/não confirmada: IDGRAN.
- Nenhum endpoint API/XHR foi promovido sem observação direta. Totais `UNKNOWN` permanecem assim quando a página não os forneceu.

## Casos para revisão humana do Sol

1. IDGRAN: confirmar se o domínio fornecido está descontinuado ou se existe domínio oficial novo.
2. Gualimp: resolver divergência entre “nenhum em andamento” e a plataforma consultoria dinâmica, além da atualização de julho de 2024.
3. Instituto Verbena/UFG: decidir se notícias de trainee entram no escopo e separar Verbena do SISCONCURSO UFG.
4. Elo: capturar o request que alimenta “Carregando concursos...” no domínio novo.
5. Apta: executar em navegador compatível e confirmar cards atuais, status e endpoint real.
6. SHDias: resolver divergência `www`/sem `www` e validar as 3 inscrições com prazo textual já expirado em 30/08/2026.
