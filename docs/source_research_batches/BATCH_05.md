# BATCH 05 — pesquisa operacional de fontes 53–65

Data da pesquisa: 2026-08-30. Escopo: concursos públicos, processos seletivos e seleções de pessoal. `UNKNOWN` significa que a informação não foi verificável com evidência reproduzível; não é uma inferência.

## Resumo do lote

| Fonte | Resultado operacional | Confiança |
|---|---|---|
| Nosso Rumo | Portal ativo, HTML renderizado; itens em andamento visíveis, contagem total não exposta | MEDIUM |
| Avança SP | Plataforma ProSeleta; 7 cartões em inscrições abertas, 37 em andamento | HIGH |
| Instituto Mais | Portal ativo; 4 abertos e 14 em andamento visíveis | HIGH |
| Publiconsult | Portal ativo, primeira listagem mistura datas/status; status ativo exato UNKNOWN | MEDIUM |
| KLC Concursos | Portal legado; abertos explicitamente vazios, em andamento contém histórico | MEDIUM |
| Sigma Assessoria | Plataforma ProSeleta; 1 processo em andamento | HIGH |
| W2 Auditores | Página direta falhou por decodificação; busca indexada mostra universo de 247 páginas/itens | LOW |
| Fênix Concursos | Portal ativo; página atual sem inscrições, 2 em andamento; snapshot de busca diverge | MEDIUM |
| Oppus Concursos | Domínio fornecido não abre e não há presença oficial atualizável | LOW |
| Instituto Legatus | Portal ativo; concursos públicos com vagas visíveis | HIGH |
| FEPESE | Índice de concursos e subdomínios por projeto; 13 projetos 2026 visíveis | HIGH |
| FUNCERN | Portal institucional; 121 resultados paginados e filtro obrigatório de escopo | HIGH |
| FAPEMIG | Chamadas/ editais são fomento; nenhum processo de contratação de pessoal observado | HIGH |

## 53 — Nosso Rumo (`nossorumo_open`)

### 1. Identidade e URL

- Instituição: Nosso Rumo, organizadora de concursos e processos seletivos.
- URL fornecida: `https://www.nossorumo.org.br`.
- A URL redireciona para `https://nossorumo.org.br/`; ambas devem ser tratadas como a mesma fonte.
- Código: `nossorumo_open`.

### 2. Navegação e mapa

A home apresenta as áreas “Certames em Andamento”, “Próximos Certames”, “Certames Finalizados” e “Tabela de Cargos”, além da busca “Certame ou cargo”. A tabela de cargos está em `/Cargo`. Há área de inscrição/candidato; uma navegação de cartão observada redirecionou para validação de CPF, portanto não é uma rota pública de detalhe confiável.

### 3. `observed`, `relevant`, `active`, `closed`, fora de escopo

- `observed`: vários cartões server-rendered na home, entre eles Mairiporã, Caraguatatuba, São João da Boa Vista, Porangaba, Ariquemes/RO e Olímpia. A home mistura seções e repetições; total exato: `UNKNOWN`.
- `relevant`: concursos públicos e processos seletivos municipais/legislativos, claramente relevantes; quantidade total: `UNKNOWN`.
- `active`: há cartões sob “Certames em Andamento”, inclusive inscrições com datas futuras em relação à captura; contagem total: `UNKNOWN`.
- `closed`: a navegação “Certames Finalizados” existe, mas a rota distinta não foi confirmada; presença de histórico é `observed`, contagem `UNKNOWN`.
- fora de escopo: estatísticas, tabela de cargos isolada, login/validação de CPF e conteúdo institucional não são oportunidades.

### 4. Listagem, item e seletor

- Listagem: cartões de certame na home e tabela em `/Cargo`.
- Item: título, município/UF, modalidade/número, vagas ou CR, período de inscrição, data de prova e término aparecem em texto dos cartões.
- Seletor CSS/XPath/atributo estável: `UNKNOWN`; a extração textual não expôs um seletor reproduzível.
- Detalhe legado localizado em busca: `/Concurso/concurso-selecionado.aspx?IDProcesso={id}`, mas o exemplo testado redirecionou para login; não usar sem validação de ID.

### 5. Paginação

`/Cargo` mostra páginas numeradas 1–4. A paginação dos cartões de certame não foi confirmada. `UNKNOWN` para total e parâmetros de página da listagem principal.

### 6. Exemplo real

“Prefeitura de Mairiporã/SP — Concurso Público 01/2026”, 05 vagas + cadastro reserva, inscrições 06/08/2026–03/09/2026 e prova em 27/09/2026. O cartão foi observado na home; URL de detalhe público atual: `UNKNOWN`.

### 7. Campos observados e tipo de evidência

| Campo | Evidência | Tipo |
|---|---|---|
| organizador/fonte | marca e domínio Nosso Rumo | HTML |
| órgão/município | texto dos cartões | HTML |
| modalidade/número | “Concurso Público 01/2026”, “Processo Seletivo” | HTML |
| vagas/CR | texto do cartão | HTML |
| início/fim de inscrição | datas no cartão | HTML |
| prova | data no cartão | HTML |
| URL de detalhe | rota legada em resultado de busca, não validada para item atual | SEARCH/HTML; parcial |
| publicações, cargos, salários, escolaridade, taxa | não expostos de modo confiável na home | UNKNOWN |

### 8. Publicações

Publicações/edital não foram expostos no cartão de forma reproduzível. Links de PDF e cronograma por certame: `UNKNOWN`.

### 9. API/XHR

Nenhum endpoint API/XHR foi exposto pela navegação acessível. Não inventar endpoint. A tabela de cargos pode usar carregamento adicional, mas isso não foi observado diretamente.

### 10. Tecnologia

Classificação operacional: `SERVER_RENDERED_HTML` com rotas legadas ASP-like e possível componente dinâmico na tabela de cargos. JavaScript necessário: `UNKNOWN`; Playwright não é justificável sem evidência de bloqueio.

### 11. Bloqueios

O domínio com `www` muda para sem `www`; não há evidência de CAPTCHA/WAF. Rotas de inscrição exigem CPF/login. Bloqueio para detalhe público: `PARTIAL`.

### 12. Quality gate

Aceitar somente cartões claramente sob certame/processo seletivo, com órgão e período/vagas. Não contar tabela de cargos, estatísticas, menu, inscrição/CPF ou conteúdo institucional. Se só houver “em andamento” sem datas verificáveis, conservar status `UNKNOWN`.

### 13. Empty evidence

Não é uma fonte vazia: há múltiplos cartões visíveis. Ausência de uma rota separada de finalizados não deve ser interpretada como vazio.

### 14. Diagnóstico técnico

Portal útil para descoberta na home. O recorte por status existe no menu, mas a estrutura interna e os detalhes atuais não são estáveis/confirmados. A tabela `/Cargo` é uma superfície secundária, não substituto de oportunidades.

### 15. Estratégia

`CONFIGURABLE_HTML`/`HTTP_HTML`, com fallback de redirect sem `www`. Extrair cartões sob títulos de status; manter detalhes e contagens como `UNKNOWN` até que uma rota pública seja comprovada.

### 16. Instruções concretas ao Codex

Usar `https://nossorumo.org.br/` como entrada; seguir somente links de “Certames em Andamento”, “Próximos” e “Finalizados” quando resultarem em HTML público; deduplicar por órgão + modalidade + número; aceitar campos visíveis dos cartões; não usar a rota legada de detalhe sem confirmar resposta pública; registrar redirect e ausência de endpoint como evidência.

### 17. Confiança e URLs

Confiança geral MEDIUM. Evidências: [home](https://nossorumo.org.br/), [tabela de cargos](https://nossorumo.org.br/Cargo), [rota de concurso legada](https://nossorumo.org.br/Concurso/concurso-selecionado.aspx?IDProcesso=148).

## 54 — Avança SP (`avancasp_open`)

### 1. Identidade e URL

Avança SP, plataforma de concursos/processos seletivos. URL: `https://avancasp.selecao.net.br/index/abertos/`. Código `avancasp_open`.

### 2. Navegação e mapa

Status públicos: `/index/abertos/`, `/index/1/` (Em andamento), `/index/2/` (Homologado), `/index/3/` (Finalizado), `/index/4/` (Suspenso), `/index/5/` (Cancelado). Detalhes usam `/informacoes/{id}/`. Rodapé identifica “Desenvolvido por ProSeleta - Gestão de Processos Seletivos Online”.

### 3. Estados

- `observed`: 7 cartões em `/index/abertos/`.
- `relevant`: 6 desses 7 são concursos/processos de pessoal; “Vestibular Processo Seletivo 10/2026 UNIREGISTRAL” é admissão acadêmica e fora do escopo.
- `active`: 7 cartões exibidos como abertos pela própria página; ativos de pessoal observados: 6.
- `closed`: a categoria Finalizado existe, mas a página testada declarou “Nenhum item cadastrado”; Homologado tem “1–10 de 205”.
- `out_of_scope`: vestibular/admissão acadêmica.

### 4. Listagem, item e seletor

Cartões de órgão, modalidade/número, vagas, datas e link de detalhe. Seletor exato: `UNKNOWN`. Detalhe usa `/informacoes/{id}/`.

### 5. Paginação

Em andamento: “Mostrando 1–10 de 37”, páginas 1–4, rota `/index/{n}/`. Homologado: “1–10 de 205”, páginas até 35. A página aberta não exibe contagem de todos os abertos além dos 7 cartões atuais.

### 6. Exemplo real

CRECI/SP — Concurso Público 01/2026, detalhe [informacoes/251](https://avancasp.selecao.net.br/informacoes/251/): inscrições 21/08/2026–21/09/2026, prova 29/11/2026, 34 vagas. A página traz local de prova, publicações e tabela de vagas/salário/taxa.

### 7. Campos e evidência

| Campo | Tipo |
|---|---|
| órgão, modalidade, número, vagas, início/fim | HTML |
| status e prova | HTML no detalhe |
| cargo, escolaridade, salário, carga horária, taxa, código | HTML/tabela no detalhe |
| edital/retificações | links HTML para PDFs em `anexos-r2.selecao.net.br` |
| API/IDs | rota HTML `/informacoes/{id}/`; API `UNKNOWN` |

### 8. Publicações

No CRECI/SP foram observados edital/retificações e impugnações, com links de anexos em `anexos-r2.selecao.net.br`; datas de publicação aparecem no HTML.

### 9. API/XHR

Nenhum endpoint API/XHR foi exposto. Não inventar. O HTML contém toda a informação necessária na navegação observada.

### 10. Tecnologia

`SERVER_RENDERED_HTML`, plataforma ProSeleta compartilhada com Sigma. JavaScript/Playwright: não requerido pela evidência disponível.

### 11. Bloqueios

Sem CAPTCHA/WAF observado. Links de anexos são domínio separado, mas públicos.

### 12. Quality gate

Aceitar concurso/processo seletivo de contratação. Excluir vestibular e admissão estudantil. Usar o status da própria rota, não inferir status apenas pela data.

### 13. Empty evidence

Finalizado (`/index/3/`) exibiu explicitamente “Nenhum item cadastrado”. Isso é vazio real daquela categoria, não da fonte. A categoria aberta não está vazia.

### 14. Diagnóstico técnico

A plataforma tem rotas de status previsíveis e detalhe rico, com paginação explícita. A contagem de “em andamento” inclui histórico da categoria e não deve ser somada à contagem de abertos.

### 15. Estratégia

`CONFIGURABLE_HTML`, idealmente conector compartilhado ProSeleta; obter `/index/abertos/` e detalhes `/informacoes/{id}/`; seguir anexos somente para publicações.

### 16. Instruções ao Codex

Capturar os 7 cartões de `/index/abertos/`; descartar o vestibular; seguir cada `/informacoes/{id}/`; extrair tabela de cargos e publicações; guardar status e datas exatamente como HTML; não converter 37/205 em ativos abertos.

### 17. Confiança e URLs

HIGH. Evidências: [abertos](https://avancasp.selecao.net.br/index/abertos/), [em andamento](https://avancasp.selecao.net.br/index/1/), [homologados](https://avancasp.selecao.net.br/index/2/), [finalizados/vazio](https://avancasp.selecao.net.br/index/3/), [CRECI detalhe](https://avancasp.selecao.net.br/informacoes/251/).

## 55 — Instituto Mais (`institutomais_open`)

### 1. Identidade e URL

Instituto Mais. URL `https://www.institutomais.org.br/Concursos/ConcursosAbertos`; código `institutomais_open`.

### 2. Navegação e mapa

Página “Concursos Abertos” separa “Próximos Concursos”, “Inscrições Abertas”, “Concursos em andamento” e link de encerrados em `/Concursos/ConcursosEncerrados`. Detalhes usam `/Concursos/Detalhe/{id}`.

### 3. Estados

- `observed`: 4 itens em inscrições abertas e 14 itens em andamento (lista visível).
- `relevant`: concursos/processos de prefeituras, autarquias e fundações são relevantes.
- `active`: os 4 abertos são explicitamente ativos; quantidade total além da página: `UNKNOWN`.
- `closed`: encerrados possuem 50 itens por página e ao menos 11 páginas observadas na navegação.
- fora de escopo/triagem: residência médica e outros processos acadêmicos devem ser classificados separadamente; não tratar como concurso público de cargos efetivos sem indicação de vínculo.

### 4. Listagem, item e seletor

Listagem textual com órgão, modalidade e número; detalhe `/Concursos/Detalhe/{id}`. Seletor estável: `UNKNOWN`.

### 5. Paginação

Encerrados: `/Concursos/ConcursosEncerrados/2`, `/7` etc.; 50 itens por página e 11 páginas. Abertos/em andamento não exibiram paginação distinta.

### 6. Exemplo real

[São Sebastião PREV CP Edital 01/2026](https://www.institutomais.org.br/Concursos/Detalhe/10645): inscrições 17/08/2026–08/10/2026; quatro cargos, cada um com 1 vaga (Agente Administrativo Previdenciário, Técnico de Contabilidade, Assistente Financeiro e Contador).

### 7. Campos e evidência

| Campo | Tipo |
|---|---|
| órgão/modalidade/número/status/período | HTML |
| cargo, pré-requisito, vagas | HTML/tabela |
| edital/comunicados | HTML + PDFs no CKFinder |
| salário/taxa/carga horária | geralmente no edital; não sempre na página | UNKNOWN quando ausente |

### 8. Publicações

São Sebastião PREV expõe edital e comunicados; o edital foi observado em `ckfinder/userfiles/files/EDITAL%20001-2026%20-%20%20ATUALIZADO.pdf`. Diadema CP 04/2026 e CP 03/2026 também exibem publicações, inclusive quando inscrições encerraram.

### 9. API/XHR

Nenhum endpoint API/XHR exposto; PDFs são links HTML para armazenamento CKFinder.

### 10. Tecnologia

`SERVER_RENDERED_HTML` com rotas convencionais e documentos CKFinder; JavaScript não necessário para o conteúdo observado.

### 11. Bloqueios

Nenhum CAPTCHA/WAF observado. Links de edital podem exigir URL-encoding, mas são públicos.

### 12. Quality gate

Aceitar cargos e processos de contratação. Excluir páginas de conteúdo institucional e vestibular; marcar residência/estágio conforme o produto decidir, sem promovê-los automaticamente a concurso de cargo efetivo.

### 13. Empty evidence

Não vazio: 4 abertos e 14 em andamento aparecem explicitamente.

### 14. Diagnóstico técnico

Boa fonte HTML para descoberta e detalhe. O status é mais confiável no detalhe do que pelo nome da seção; “encerrados” é histórico paginado.

### 15. Estratégia

`CONFIGURABLE_HTML`; coletar base, seguir `/Concursos/Detalhe/{id}`, baixar PDFs de publicações e paginar somente encerrados.

### 16. Instruções ao Codex

Extrair os quatro itens da seção aberta; seguir todos os IDs; preservar tabela de cargos e pré-requisitos; tratar residência/estágio com filtro de vínculo; usar encerrados somente para histórico, sem marcar como ativos.

### 17. Confiança e URLs

HIGH. Evidências: [abertos](https://www.institutomais.org.br/Concursos/ConcursosAbertos), [São Sebastião PREV](https://www.institutomais.org.br/Concursos/Detalhe/10645), [encerrados](https://www.institutomais.org.br/Concursos/ConcursosEncerrados), [edital PDF](https://www.institutomais.org.br/ckfinder/userfiles/files/EDITAL%20001-2026%20-%20%20ATUALIZADO.pdf).

## 56 — Publiconsult (`publiconsult_open`)

### 1. Identidade e URL

Publiconsult; URL `https://publiconsult.com.br/Concurso/Index`; código `publiconsult_open`.

### 2. Navegação e mapa

Menu: Concursos, Inscrições Abertas, Em Andamento, Homologados, Suspensos, painel do candidato e “Visualizar todos”. Detalhes usam `/Concurso/Detail/{id}?origem=H`.

### 3. Estados

- `observed`: pelo menos 17 cartões na primeira página da listagem.
- `relevant`: itens nomeados como concurso/processo seletivo municipal são relevantes; total filtrado `UNKNOWN`.
- `active`: `UNKNOWN`: a listagem principal mostra datas, mas não um status individual consistente; várias datas já transcorreram na data da pesquisa.
- `closed`: homologados têm listagem própria (`IndexTodosHomologados`) com muitos registros.
- fora de escopo: treinamentos, notícias, artigos e “avaliação funcional” não são oportunidades de contratação.

### 4. Listagem, item e seletor

Cartões com órgão, modalidade e datas; detalhe numérico. Seletor exato: `UNKNOWN`.

### 5. Paginação

A página inicial não expôs paginação reproduzível no texto. “Visualizar todos” abre `IndexTodosHomologados`; paginação interna: `UNKNOWN`.

### 6. Exemplo real

[Sarapuí Concurso Público 04/2026](https://publiconsult.com.br/Concurso/Detail/676?origem=H): inscrições 30/06/2026–07/08/2026; página exibe retificação e edital consolidado e cargos de Professor de Educação Básica II/Inglês e Professor de Apoio Educacional Especializado, valor 31,64.

### 7. Campos e evidência

| Campo | Tipo |
|---|---|
| órgão, modalidade, período | HTML |
| status legendado 1=Andamento, 2=Homologado, 3=Suspenso, 4=Cancelado | HTML no detalhe |
| código, cargo, valor | HTML/tabela |
| publicações | HTML/tabela, links quando disponíveis |
| vagas, escolaridade, carga, taxa | não observados de modo completo | UNKNOWN |

### 8. Publicações

O detalhe de Sarapuí expõe “Retificação 1” e “Edital de Abertura Consolidado”; a coluna de link apareceu vazia no texto capturado, portanto URL de arquivo é `UNKNOWN`.

### 9. API/XHR

Nenhum endpoint exposto. Não assumir API por o rodapé mencionar Gsist/cloud.

### 10. Tecnologia

`SERVER_RENDERED_HTML`, com imagens/ativos em bucket S3 da Gsist. JavaScript não necessário no conteúdo textual observado.

### 11. Bloqueios

Sem CAPTCHA/WAF observado; ausência de status explícito na listagem é risco de classificação, não bloqueio.

### 12. Quality gate

Exigir tipo concurso/processo seletivo e órgão; usar status do detalhe/legenda, nunca só data. Rejeitar avaliação funcional, treinamentos e conteúdo editorial.

### 13. Empty evidence

Não há evidência de lista vazia: muitos cartões e listagem de homologados.

### 14. Diagnóstico técnico

A fonte mistura status e histórico na experiência de listagem. O detalhe é a unidade confiável para status/publicações; contagem da primeira página não deve ser tratada como total.

### 15. Estratégia

`CONFIGURABLE_HTML` com fallback para o detalhe; classificar status pela legenda e conservar `UNKNOWN` quando o cartão não trouxer status.

### 16. Instruções ao Codex

Abrir `/Concurso/Index`; coletar cartões e IDs; seguir `/Concurso/Detail/{id}?origem=H`; extrair legenda, cargos e publicações; não inferir ativo por datas; paginar apenas quando a página fornecer controle explícito.

### 17. Confiança e URLs

MEDIUM. Evidências: [índice](https://publiconsult.com.br/Concurso/Index), [detalhe Sarapuí](https://publiconsult.com.br/Concurso/Detail/676?origem=H), [homologados](https://publiconsult.com.br/Concurso/IndexTodosHomologados).

## 57 — KLC Concursos (`klc_open`)

### 1. Identidade e URL

KLC Concursos; URL `https://www.klcconcursos.com.br`; código `klc_open`.

### 2. Navegação e mapa

Portal legado com menu candidato, estados e abas codificadas por `?pag=&sub=`: `sub=1` Concursos Abertos, `sub=2` Em andamento, `sub=3` Encerrados e `sub=0` Próximos. Detalhe usa `?id={id}&pag=mco`.

### 3. Estados

- `observed`: “Concursos Abertos” declarou explicitamente “Nenhum concurso”. Em andamento mostrou muitos registros históricos (mais de 100 linhas/items).
- `relevant`: concursos e processos seletivos municipais são relevantes; total `UNKNOWN`.
- `active`: `UNKNOWN`; a seção “Em andamento” contém datas antigas e não prova vigência atual.
- `closed`: quatro itens visíveis em `sub=3` e link “Veja mais”.
- fora de escopo: “teste seletivo” deve ser preservado como processo seletivo somente quando houver contratação explícita.

### 4. Listagem, item e seletor

Listas HTML por query `sub`; detalhe `id` + `pag=mco`. Seletor CSS estável: `UNKNOWN`.

### 5. Paginação

“Veja mais...” aparece em encerrados; parâmetros exatos de paginação além de `pag`/`sub`: `UNKNOWN`.

### 6. Exemplo real

[PSS 002/2025 Teodoro Sampaio/SP](https://www.klcconcursos.com.br/?id=628&pag=mco): inscrições 25/09/2025–13/10/2025; detalhe lista edital, retificações, isenção, gabaritos e resultados. É histórico/encerrado, não ativo atual.

### 7. Campos e evidência

| Campo | Tipo |
|---|---|
| órgão, modalidade/número, datas | HTML |
| publicações e tipo de documento | HTML/link |
| cargo, vagas, salário, taxa | não completos na amostra | UNKNOWN |
| status | seção/cronologia; ativo atual UNKNOWN |

### 8. Publicações

Detalhe Teodoro Sampaio expõe abertura, retificações, isenção, prorrogação, homologação, gabaritos e resultados. Links de arquivo estão no HTML, mas não foram todos resolvidos.

### 9. API/XHR

Nenhuma API/XHR observada. Não inventar endpoints.

### 10. Tecnologia

`LEGACY_SERVER_RENDERED_HTML`, com query strings curtas e sem dependência evidente de JavaScript.

### 11. Bloqueios

Sem CAPTCHA/WAF observado. A nomenclatura “Em andamento” não garante atividade atual.

### 12. Quality gate

Aceitar somente processos com contratação e órgão identificados. Manter a seção “abertos” vazia como evidência; não promover itens históricos de “em andamento” a ativos sem datas/status atual.

### 13. Empty evidence

`?pag=&sub=1` declarou “Nenhum concurso”: vazio explícito de concursos abertos no momento da captura.

### 14. Diagnóstico técnico

Portal legada e navegável por query parameters. O problema principal é semântico: status de seção não acompanha necessariamente datas atuais.

### 15. Estratégia

`HTTP_HTML`/`CONFIGURABLE_HTML`; consultar todos os `sub`, parsear detalhes por `id`, manter status atual como `UNKNOWN` quando datas forem históricas.

### 16. Instruções ao Codex

Consultar `sub=1`, `2`, `3`, `0`; registrar vazio explícito de `sub=1`; seguir detalhes `?id={id}&pag=mco`; extrair publicações; não contar “Em andamento” histórico como ativo sem confirmação.

### 17. Confiança e URLs

MEDIUM. Evidências: [home/abertos](https://www.klcconcursos.com.br/?pag=&sub=1), [em andamento](https://www.klcconcursos.com.br/?pag=&sub=2), [encerrados](https://www.klcconcursos.com.br/?pag=&sub=3), [detalhe](https://www.klcconcursos.com.br/?id=628&pag=mco).

## 58 — Sigma Assessoria (`sigma_open`)

### 1. Identidade e URL

Sigma Assessoria; URL `https://concursos.sigmaassessoria.com.br`; código `sigma_open`.

### 2. Navegação e mapa

Plataforma ProSeleta, com status Inscrições Abertas, Em andamento, Homologado, Finalizado, Suspenso e Cancelado. Detalhe em `/informacoes/{id}/`.

### 3. Estados

- `observed`: 1 item em andamento — PSS simplificado 001.2026, Prefeitura de Itaju.
- `relevant`: 1, processo seletivo para contratação.
- `active`: 1 observado como Em andamento; inscrições 13/08/2026–27/08/2026.
- `closed`: categorias existem; total `UNKNOWN`.
- fora de escopo: nenhum item fora de escopo foi observado na página-alvo.

### 4. Listagem, item e seletor

Cartão ProSeleta com título e datas; detalhe `/informacoes/264/`. Seletor exato: `UNKNOWN`.

### 5. Paginação

Não observada na página com um item. `UNKNOWN`.

### 6. Exemplo real

[Prefeitura Municipal de Itaju — PSS 001.2026](https://concursos.sigmaassessoria.com.br/informacoes/264/): processo seletivo, inscrições 13/08/2026–27/08/2026, professor de educação especial em cadastro reserva.

### 7. Campos e evidência

| Campo | Tipo |
|---|---|
| órgão, modalidade, número, período, status | HTML |
| cargo/vaga/quantidade | HTML/tabela |
| edital completo | link HTML para PDF em `anexos-r2.selecao.net.br` |
| salário, escolaridade, taxa, carga | não observados no detalhe | UNKNOWN |

### 8. Publicações

Edital completo datado de 06/08/2026, linkado no anexo compartilhado ProSeleta.

### 9. API/XHR

Nenhum endpoint API/XHR exposto.

### 10. Tecnologia

`SERVER_RENDERED_HTML`, ProSeleta compartilhada com Avança SP.

### 11. Bloqueios

Sem CAPTCHA/WAF observado; anexos em domínio separado.

### 12. Quality gate

Aceitar a linha de processo seletivo e a vaga; não criar item separado para o PDF.

### 13. Empty evidence

Não vazio: um item em andamento é exibido.

### 14. Diagnóstico técnico

Estrutura praticamente idêntica à Avança SP, mas domínio de organizadora diferente. Conector compartilhado é viável, desde que o domínio seja parâmetro.

### 15. Estratégia

`CONFIGURABLE_HTML` usando o mesmo parser ProSeleta, com domínio e status configuráveis.

### 16. Instruções ao Codex

Abrir a raiz; coletar cartões por status; seguir `/informacoes/{id}/`; extrair status, vagas e links de anexos; não assumir que todos os hosts ProSeleta têm a mesma contagem.

### 17. Confiança e URLs

HIGH. Evidências: [raiz](https://concursos.sigmaassessoria.com.br), [detalhe](https://concursos.sigmaassessoria.com.br/informacoes/264/).

## 59 — W2 Auditores (`w2_open`)

### 1. Identidade e URL

W2 Auditores/Consultores; URL fornecida `https://www.w2consultores.com.br/index/todos/`; código `w2_open`.

### 2. Navegação e mapa

Resultados indexados mostram “Processos Seletivos - Todos” e parâmetros `dir`, `ord`, `pg`, `pp`, `q`; busca também aparece como `busca`. Há rotas de status (Inscrições Abertas, Em andamento, Homologado, Finalizado, Suspenso, Cancelado) e detalhe `/informacoes/{id}/`.

### 3. Estados

- `observed`: busca indexada mostra página 7 de 247, 10 itens por página.
- `relevant`: títulos são processos/concursos municipais; quantidade filtrada `UNKNOWN`.
- `active`: `UNKNOWN`; páginas indexadas são antigas, embora edital oficial externo confirme atividade W2 em 2026.
- `closed`: há muitos registros históricos e detalhes homologados.
- fora de escopo: nenhum item fora de escopo confirmado.

### 4. Listagem, item e seletor

Parâmetros reproduzíveis pela busca: `?dir=&ord=&pg=7&pp=10&q=`; alternativa `?busca=CONQUISTA+`. Seletor exato: `UNKNOWN`. Detalhe de exemplo indexado: `/informacoes/82/`.

### 5. Paginação

Evidência indexada: página 7 de 247, 10 por página; controles Primeira/Anterior/Próxima/Última. Parâmetros `pg` e `pp` confirmados por resultado de busca.

### 6. Exemplo real

O índice de busca mostra o detalhe [informacoes/82](https://www.w2consultores.com.br/informacoes/82/) como Concurso Público — Prefeitura de Santo Afonso/MT, Edital 001/2015, homologado. Para atividade mais recente, edital oficial da AMM-MT cita PSS W2 002/2026 de Lambari D’Oeste, mas a URL do detalhe no portal é `UNKNOWN`.

### 7. Campos e evidência

| Campo | Tipo |
|---|---|
| título, órgão, número, período, situação | SEARCH snippet/HTML indexado |
| vagas/salário | SEARCH snippet de detalhe/HTML parcial |
| publicações | detalhe, mas não recuperado integralmente |
| contagem 247/página 7/10 itens | SEARCH snippet reproduzível |

### 8. Publicações

Não foi possível validar anexos diretamente; URL e lista de publicações de item atual: `UNKNOWN`.

### 9. API/XHR

Nenhum endpoint exposto. Não confundir parâmetros de listagem com API.

### 10. Tecnologia

Provável HTML server-rendered legado; a ferramenta de navegação falhou ao decodificar a página direta, portanto tecnologia final: `UNKNOWN` com indício `SERVER_RENDERED_HTML`.

### 11. Bloqueios

Bloqueio observado na pesquisa: falha de decodificação Unicode ao abrir as páginas diretas; não há evidência de WAF/CAPTCHA. Recomenda-se fallback de charset Windows-1252/ISO-8859-1 antes de concluir indisponibilidade.

### 12. Quality gate

Exigir órgão, modalidade e situação verificáveis; não usar só resultados de busca para marcar ativo. A situação de um edital oficial externo não substitui o registro no portal.

### 13. Empty evidence

Não há evidência de vazio; há resultado indexado de 247 páginas.

### 14. Diagnóstico técnico

Fonte tecnicamente recuperável por busca, mas não validada pelo navegador devido a encoding. Contagens e parâmetros têm boa evidência indexada; status atual e campos completos não.

### 15. Estratégia

`CONFIGURABLE_HTML` com fallback de charset; se o parser não suportar a resposta, `KEEP_BLOCKED` temporário e revisão manual. Usar `pg`, `pp`, `q`/`busca` e seguir `/informacoes/{id}/`.

### 16. Instruções ao Codex

Tentar resposta com UTF-8 e Windows-1252/Latin-1; testar `/index/todos/?dir=&ord=&pg=1&pp=10&q=`; validar paginação e detalhes; preservar `active=UNKNOWN` até observar status no portal; não inventar IDs para Lambari.

### 17. Confiança e URLs

LOW. Evidências: [índice fornecido](https://www.w2consultores.com.br/index/todos/), [busca página 7](https://www.w2consultores.com.br/index/todos/?dir=&ord=&pg=7&pp=10&q=), [busca por Conquista](https://www.w2consultores.com.br/index/todos/?busca=CONQUISTA+), [detalhe indexado](https://www.w2consultores.com.br/informacoes/82/).

## 60 — Fênix Concursos (`fenix_open`)

### 1. Identidade e URL

Fênix Concursos, portal `https://portal.fenix.selecao.site/edital`; código `fenix_open`.

### 2. Navegação e mapa

Seções: Futuros, Inscrições Abertas, Em andamento, Finalizados, Suspensos e Cancelados. Detalhes usam `/edital/ver/{id}`. Rodapé “Desenvolvido por Gestor Editais © 2012–2026”; aviso de cookies ACT SISTEMAS.

### 3. Estados

- `observed`: página atual mostra “NENHUM CONCURSO PÚBLICO OU PROCESSO SELETIVO ENCONTRADO” em inscrições abertas; 2 em andamento (Severínia PSS 01/2026 e Tabapuã CP 01/2026); futuros e suspensos explicitamente sem itens.
- `relevant`: os 2 processos/concursos são relevantes.
- `active`: aberto atual = 0 explicitamente, mas resultado de busca rastreado 2 dias antes mostra Pedrinhas Paulista CP 01/2026 com inscrições 21/08–04/09/2026. Estado atual conflitante: `UNKNOWN` para ativos.
- `closed`: muitos finalizados.
- fora de escopo: “Capacitação – PALESTRA...” observado na listagem; excluir.

### 4. Listagem, item e seletor

HTML agrupado por status; detalhe `/edital/ver/{id}`. Seletor exato: `UNKNOWN`.

### 5. Paginação

Não observada; a página reúne histórico extenso. `UNKNOWN`.

### 6. Exemplo real

[Prefeitura de Tabapuã — Concurso Público 01/2026](https://portal.fenix.selecao.site/edital/ver/125): inscrições 04/05/2026–15/05/2026; detalhe apresenta edital, retificações, gabaritos, recursos, resultados e homologação.

### 7. Campos e evidência

| Campo | Tipo |
|---|---|
| órgão, modalidade/número, datas, cidade | HTML |
| cargo/escolaridade | HTML/tabela no detalhe |
| publicações | HTML + downloads `cdn-fenix.selecao.site` |
| status | HTML por seção; conflito entre snapshot atual e busca |

### 8. Publicações

Severínia e Tabapuã mostram edital, retificações, homologação, gabarito e resultados; arquivos são servidos em `cdn-fenix.selecao.site`.

### 9. API/XHR

Nenhum endpoint exposto; não inventar API.

### 10. Tecnologia

`SERVER_RENDERED_HTML`/Gestor Editais; JavaScript não necessário para as listas observadas.

### 11. Bloqueios

Sem CAPTCHA/WAF; há aviso de cookies ACT SISTEMAS. Divergência entre cache de busca e página atual é risco de frescor, não bloqueio.

### 12. Quality gate

Aceitar somente CP/PSS de contratação. Excluir capacitação/palestra; não marcar ativo pela busca sem confirmar na página atual.

### 13. Empty evidence

Inscrições Abertas, Futuros e Suspensos têm mensagens explícitas de vazio na captura atual; não declarar fonte vazia porque “Em andamento” e Finalizados têm itens.

### 14. Diagnóstico técnico

Portal legível, mas status pode mudar/cachar rapidamente. A página de detalhe é a unidade para publicações e cargos; a seção de status é evidência de snapshot.

### 15. Estratégia

`CONFIGURABLE_HTML`; coletar cada seção, deduplicar por `/edital/ver/{id}`, registrar timestamp/status textual e tratar conflito de snapshots como `UNKNOWN`.

### 16. Instruções ao Codex

Abrir `/edital`; armazenar os vazios explícitos; seguir IDs 125/126 como exemplos; filtrar capacitação; comparar o status de detalhe e seção; não importar o item Pedrinhas da busca sem revalidar HTML atual.

### 17. Confiança e URLs

MEDIUM. Evidências: [índice](https://portal.fenix.selecao.site/edital), [Tabapuã](https://portal.fenix.selecao.site/edital/ver/125), [Severínia](https://portal.fenix.selecao.site/edital/ver/126).

## 61 — Oppus Concursos (`oppus_open`)

### 1. Identidade e URL

Oppus Concursos Públicos Ltda; URL fornecida `https://www.oppusconcursos.com.br`; código `oppus_open`.

### 2. Navegação e mapa

Não foi possível abrir a URL fornecida em HTTP/HTTPS: o navegador marcou-a como URL não segura/indisponível. Buscas retornam apenas PDFs municipais antigos e páginas de terceiros; não há mapa atual navegável.

### 3. Estados

- `observed`: nenhum item no portal atual, por falha de acesso; não confundir com vazio.
- `relevant`: histórico de concursos públicos Oppus aparece em editais antigos; quantidade atual `UNKNOWN`.
- `active`: `UNKNOWN`.
- `closed`: histórico documental antigo, não uma listagem atual.
- fora de escopo: nenhum julgamento sobre PDFs antigos além da relevância histórica.

### 4. Listagem, item e seletor

Listagem/seletor/detalhe atuais: `UNKNOWN`. PDFs antigos mencionam site, cartão, prova, gabarito e área de recursos.

### 5. Paginação

`UNKNOWN`.

### 6. Exemplo real

Editais antigos de Condor/RS (2015), CREFITO-4 (2016) e Itirapina (2017) mencionam Oppus e seu domínio; não há URL de detalhe atual validada. Não usar esses documentos para marcar oportunidade ativa.

### 7. Campos e evidência

Somente existência histórica da organizadora, modalidades e documentos em PDFs de terceiros; campos atuais, status, vagas e datas: `UNKNOWN`.

### 8. Publicações

Publicações históricas existem em PDFs municipais, mas não foram atribuídas a um endpoint atual da fonte.

### 9. API/XHR

`UNKNOWN`; não foi possível acessar a página.

### 10. Tecnologia

`UNKNOWN`.

### 11. Bloqueios

Bloqueio de acesso/segurança da URL no navegador; não há evidência suficiente para chamar de WAF ou CAPTCHA.

### 12. Quality gate

Não ingerir qualquer registro atual até a fonte fornecer domínio funcional ou uma URL oficial verificável. PDFs antigos podem ficar apenas como evidência histórica.

### 13. Empty evidence

`UNKNOWN_EMPTY`: falha de acesso não é mensagem de lista vazia.

### 14. Diagnóstico técnico

Domínio provavelmente descontinuado ou URL desatualizada, mas isso não pode ser afirmado como fato definitivo sem confirmação do operador. Requer revisão manual.

### 15. Estratégia

`KEEP_BLOCKED` + `DEPRECATE_REVIEW_REQUIRED`; não remover silenciosamente a fonte, nem criar parser especulativo.

### 16. Instruções ao Codex

Manter a fonte em quarentena; revalidar DNS/HTTPS em ambiente com acesso e procurar comunicação oficial contemporânea; somente depois cadastrar listagem, seletor ou endpoint.

### 17. Confiança e URLs

LOW para conteúdo atual, HIGH para a falha do domínio fornecido. Evidências históricas: [Condor 2015 (busca)](https://www.google.com/search?q=site%3Aoppusconcursos.com.br+Condor+2015), [CREFITO-4 2016 (busca)](https://www.google.com/search?q=site%3Aoppusconcursos.com.br+CREFITO-4+2016), [Itirapina 2017 (busca)](https://www.google.com/search?q=site%3Aoppusconcursos.com.br+Itirapina+2017).

## 62 — Instituto Legatus (`legatus_open`)

### 1. Identidade e URL

Instituto Legatus; URL `https://www.legatus.org.br`; código `legatus_open`.

### 2. Navegação e mapa

Menu: Inscrições Abertas, Próximos, Em andamento, Encerrados, Concurso e área do candidato. Home mostra cartões e detalhes usam `/concursos/{id}/{slug}/`.

### 3. Estados

- `observed`: pelo menos 10 cartões na home, incluindo Tanque do Piauí, Caxingó, São Mateus/MA, Hugo Napoleão, Croatá/CE, Caxias, Turilândia e Codó.
- `relevant`: concursos públicos municipais com vagas/CR são relevantes.
- `active`: há concursos com período de inscrição corrente/futuro; contagem exata `UNKNOWN`.
- `closed`: rota existe; total `UNKNOWN`.
- fora de escopo: institucional/FAQ e área do candidato; não criar itens.

### 4. Listagem, item e seletor

Cards de concurso na home; detalhe slugificado. Seletor exato: `UNKNOWN`.

### 5. Paginação

Páginas de status existem (`/concursos/abertos/`, `/andamento/`, `/proximos-concursos/`, provável `/encerrados/`), mas paginação numérica não foi confirmada.

### 6. Exemplo real

[Município de Tanque do Piauí/PI](https://www.legatus.org.br/concursos/160/municipio-de-tanque-do-piaui-pi/): Concurso Público, inscrições 25/06/2026–03/08/2026, Edital 01/2026, 50 vagas + cadastro reserva. A tabela tem código, cargo, escolaridade, geral, PCD e taxa.

### 7. Campos e evidência

| Campo | Tipo |
|---|---|
| órgão, modalidade, número, período, vagas/CR | HTML |
| cargos, escolaridade, vagas gerais/PCD, taxa | HTML/tabela |
| publicações e inscrições | HTML/links |
| salário | não exposto no detalhe | UNKNOWN |

### 8. Publicações

Tanque do Piauí lista edital, retificação, resultados de isenção e publicação PCD; links públicos na página.

### 9. API/XHR

Nenhum endpoint exposto.

### 10. Tecnologia

`SERVER_RENDERED_HTML` com rotas slugificadas; JavaScript não necessário no conteúdo observado.

### 11. Bloqueios

Sem CAPTCHA/WAF. FAQ cita `www.institutolegatus.com.br` para área do candidato; isso é domínio auxiliar, não deve ser tratado como migração sem evidência.

### 12. Quality gate

Aceitar apenas Concurso/Processo Seletivo de pessoal; ignorar links de candidato, FAQ e institucional.

### 13. Empty evidence

Não vazio: diversos cartões e detalhe com 50 vagas.

### 14. Diagnóstico técnico

Fonte rica em tabela de vagas e publicações; home e status são superfícies de descoberta. A contagem real depende das páginas de status e não foi exposta.

### 15. Estratégia

`CONFIGURABLE_HTML`; coletar home/status, seguir detalhes slugificados, preservar tabela geral/PCD/taxa.

### 16. Instruções ao Codex

Consultar `/concursos/abertos/`, `/andamento/` e `/proximos-concursos/`; deduplicar por ID; extrair tabela do detalhe; não seguir `institutolegatus.com.br` como listagem sem confirmar que é área de candidato.

### 17. Confiança e URLs

HIGH. Evidências: [home](https://www.legatus.org.br), [Tanque do Piauí](https://www.legatus.org.br/concursos/160/municipio-de-tanque-do-piaui-pi/), [abertos](https://www.legatus.org.br/concursos/abertos/), [em andamento](https://www.legatus.org.br/concursos/andamento/), [próximos](https://www.legatus.org.br/concursos/proximos-concursos/).

## 63 — FEPESE (`fepese_open`)

### 1. Identidade e URL

FEPESE; URL `https://fepese.org.br/concursos/`; código `fepese_open`.

### 2. Navegação e mapa

Índice “Concursos Públicos” e links por projeto em subdomínios próprios. O índice também tem “Seleções Públicas”, que é contratação de fornecedores/projetos sob Decreto 8.241/2014, não seleção de pessoal.

### 3. Estados

- `observed`: 13 subdomínios/projetos 2026 na seção “Concursos mais acessados”.
- `relevant`: os 13 são processos seletivos/concursos de pessoal (magistério, saúde, guarda, administração etc.).
- `active`: projetos apresentam notícias/cronogramas 2026; status individual completo `UNKNOWN`.
- `closed`: histórico agregado “mais de 450 concursos realizados” é métrica institucional, não contagem ativa.
- fora de escopo: `/selecoespublicas/` (compras/serviços) e conteúdo institucional/capacitação.

### 4. Listagem, item e seletor

Índice de cards/link para subdomínio; cada tenant tem navegação Principal, Edital, Perguntas, Legislação, Cronograma, Inscrição e Contato. Seletor exato: `UNKNOWN`.

### 5. Paginação

Índice mostra carrossel “Anterior/Próximo”, não universo paginado completo. Paginação de tenants: `UNKNOWN`.

### 6. Exemplo real

[Processo Seletivo Magistério São José — Edital 005/2026/SME](https://2026pseducasj.fepese.org.br/): seleção para contratos temporários de professores/auxiliares, cadastro reserva; notícia datada 24/08/2026 e navegação pública de edital/cronograma.

### 7. Campos e evidência

| Campo | Tipo |
|---|---|
| projeto, órgão, modalidade/número | HTML do índice/tenant |
| finalidade e status/notícias | HTML tenant |
| cronograma, edital, perguntas | links HTML; arquivo exato pode exigir navegação interna |
| vagas, salário, taxa, escolaridade | tenant/edital; não completos na home | UNKNOWN quando ausente |

### 8. Publicações

Tenant apresenta seção “PUBLICAÇÕES” e link de candidato em `ssl.fepese.org.br`; edital/PDF específico do exemplo não teve URL estável exposta na captura, portanto `UNKNOWN`.

### 9. API/XHR

Nenhum endpoint API/XHR exposto; tenant parece HTML estático/server-rendered.

### 10. Tecnologia

`MULTI_TENANT_HTML`: índice institucional + subdomínio por concurso. JavaScript não necessário no conteúdo textual observado.

### 11. Bloqueios

Sem CAPTCHA/WAF no índice; candidato/inscrição usa host SSL separado.

### 12. Quality gate

Aceitar somente subdomínios cujo texto indique contratação, concurso ou processo seletivo. Rejeitar rigorosamente “Seleções Públicas” de aquisição/serviços e métricas institucionais.

### 13. Empty evidence

Índice não vazio; 13 projetos destacados. “Mais de 450” não é evidência de ativos.

### 14. Diagnóstico técnico

A descoberta exige seguir subdomínios; um parser de página única não alcança publicações. Separar tenant e índice é essencial.

### 15. Estratégia

`HYBRID`/`CONFIGURABLE_HTML`: extrair links do índice, visitar cada tenant, coletar publicações e cronograma; manter status individual `UNKNOWN` sem evidência.

### 16. Instruções ao Codex

Abrir `/concursos/`; enumerar os 13 links de 2026; descartar `/selecoespublicas/`; visitar tenant e seções Edital/Cronograma/Publicações; não transformar “mais acessados” ou “450 realizados” em contagens de ativos.

### 17. Confiança e URLs

HIGH. Evidências: [índice](https://fepese.org.br/concursos/), [tenant São José](https://2026pseducasj.fepese.org.br/), [seleções públicas fora de escopo](https://fepese.org.br/selecoespublicas/).

## 64 — FUNCERN (`funcern_selection`)

### 1. Identidade e URL

FUNCERN/NUPS; URL `https://funcern.br/concursos/`; código `funcern_selection`.

### 2. Navegação e mapa

Página “Processos Seletivos e Concursos executados pela FUNCERN”. Seções Inscrições abertas, Em andamento e Outros processos seletivos. Paginação por `?page={n}`; inscrições podem apontar para `inscricoes.funcern.org`.

### 3. Estados

- `observed`: 3 itens abertos, 2 em andamento e lista “outros” de 121 resultados.
- `relevant`: Lagoa de Pedras CP 01/2026 e Equador CP 002/2026 são concursos de cargos efetivos; há itens de estágio/fiscal que podem ser relevantes como seleção de pessoal. Total filtrado `UNKNOWN`.
- `active`: pelo menos 2 concursos públicos abertos; os 2 “em andamento” são Bolsa de Pesquisa SEMURB e ProITEC IFRN, ambos fora de escopo de emprego.
- `closed`: outros processos paginados contêm históricos e seleções de pessoal encerradas.
- fora de escopo: IFRN Integrado/ProITEC (admissão estudantil), bolsas de pesquisa e bolsistas.

### 4. Listagem, item e seletor

Cards/links com título e descrição; detalhes slugificados, por exemplo `/concursos/concurso-lagoa-de-pedras-2026/`. Seletor exato: `UNKNOWN`.

### 5. Paginação

“Exibindo 1 a 10 de 121 resultados”; página 2 em `?page=2`, portanto ao menos 13 páginas de 10. Paginar até a ausência de próxima página.

### 6. Exemplo real

[Concurso Público Lagoa de Pedras/RN — Edital 01/2026](https://funcern.br/concursos/concurso-lagoa-de-pedras-2026/): inscrições abertas, cargos efetivos, edital retificado e resultados de isenção; inscrição em `inscricoes.funcern.org`.

### 7. Campos e evidência

| Campo | Tipo |
|---|---|
| título, órgão, modalidade/número, estado | HTML |
| status/seção, edital, retificações | HTML/links |
| vagas/cargos/salários | detalhe ou edital; ausentes na página Lagoa | UNKNOWN quando ausente |
| contagem 121/página | HTML |

### 8. Publicações

Lagoa expõe Edital 01/2026, edital retificado e resultados de isenção; documentos complementares podem estar no host de inscrição.

### 9. API/XHR

Nenhum endpoint exposto; links externos de inscrição são HTML.

### 10. Tecnologia

`WORDPRESS_LIKE_SERVER_RENDERED_HTML`, com slugs e query `?page=N`; JavaScript não necessário para a listagem observada.

### 11. Bloqueios

Sem CAPTCHA/WAF no portal; inscrição externa é separada e deve ser tratada apenas como link.

### 12. Quality gate

Aceitar concurso/processo seletivo com contratação, estágio ou função temporária explicitamente descritos. Rejeitar bolsa/pesquisa, bolsas de projeto, seleção de estudantes, vestibular e cursos. Não tratar “PSS Bolsa de Pesquisa SEMURB” como vaga.

### 13. Empty evidence

Não vazio: 3 abertos, 2 em andamento e 121 outros resultados.

### 14. Diagnóstico técnico

Fonte tem boa paginação e mistura emprego, estágio, bolsa e admissão estudantil; filtro semântico institucional é obrigatório antes de contar ativos.

### 15. Estratégia

`CONFIGURABLE_HTML` com paginação `?page=N` e `INSTITUTIONAL_FILTER_REQUIRED`; detalhe e edital são fontes de confirmação.

### 16. Instruções ao Codex

Coletar abertos/andamento; filtrar títulos/descrições por contratação; paginar 121 resultados; excluir explicitamente IFRN/ProITEC/bolsas; seguir slugs e manter URL externa de inscrição separada do detalhe.

### 17. Confiança e URLs

HIGH. Evidências: [índice](https://funcern.br/concursos/), [página 2](https://funcern.br/concursos/?page=2), [Lagoa de Pedras](https://funcern.br/concursos/concurso-lagoa-de-pedras-2026/), [IFRN fora de escopo](https://funcern.br/concursos/ifrn-integrado-2027/).

## 65 — FAPEMIG (`fapemig_selection`)

### 1. Identidade e URL

FAPEMIG — Fundação de Amparo à Pesquisa do Estado de Minas Gerais; URL fornecida `https://fapemig.br/pt/editais/`; código `fapemig_selection`.

### 2. Navegação e mapa

A URL legada `/pt/editais/` e a antiga `/pt/chamadas_abertas_oportunidades_fapemig/` redirecionam para a home. A superfície moderna é `/oportunidades/chamadas-e-editais`, com filtros Todas, Abertas, Fluxo Contínuo, Em Análise, Resultados e Encerradas. Há login/fluxo Everest para submissão.

### 3. Estados e distinção de escopo

- `observed`: página moderna indexada mostra 190 chamadas: 4 abertas, 5 fluxo contínuo, 11 em análise, 34 resultados e 136 encerradas (contagens podem variar entre snapshots dinâmicos).
- `relevant`: 0 seleções de pessoal observadas.
- `active`: 0 oportunidades de pessoal observadas; as 4 abertas são chamadas de fomento.
- `closed`: arquivos/ chamadas de fomento encerradas, não concursos de contratação.
- fora de escopo: todas as chamadas encontradas — auxílios, bolsas, pesquisa, inovação, eventos e financiamento.

### 4. Listagem, item e seletor

Lista dinâmica de “Chamadas e Editais”; item é chamada de fomento com público-alvo, valor, documentos e submissão. Seletor/endpoints: `UNKNOWN`; não confundir “Pesquisador na Empresa” com contratação: é financiamento a empresas/pesquisadores, com bolsas BDCTI.

### 5. Paginação

Resultado indexado informa 12 entradas por página; parâmetros de paginação não foram expostos de forma confiável. `UNKNOWN`.

### 6. Exemplo real

[Chamada FAPEMIG-SEDE 013/2026 — Pesquisador na Empresa](https://fapemig.br/oportunidades/chamadas-e-editais/chamada-fapemig-sede-013-2026-pesquisador-na-empresa): fomento à inovação para empresas/startups/cooperativas e pesquisadores, R$5 milhões, com bolsas/documentos. Não é processo seletivo de empregados.

### 7. Campos e evidência

| Campo | Tipo |
|---|---|
| número/título da chamada, status, datas | HTML/indexação dinâmica |
| público-alvo, valor, modalidade de fomento | HTML/detalhe |
| edital, retificação, submissão | links HTML/PDF/DOCX |
| cargo, salário, vagas, órgão empregador | inexistentes nas chamadas observadas |

### 8. Publicações

Chamadas exibem edital, retificações e documentos de fomento. Isso não deve ser convertido em “publicação de concurso”.

### 9. API/XHR

A listagem é dinâmica e apresentou erro ao carregar quando filtrada por público-alvo; nenhum endpoint foi exposto. Não inventar REST, GraphQL ou `wp-json`.

### 10. Tecnologia

`DYNAMIC_HTML/SPA_OR_SERVER_COMPONENT_UNKNOWN`; filtros dependem de carregamento adicional. A página de filtro retornou “Erro ao carregar chamadas” em uma captura.

### 11. Bloqueios

Não há evidência de CAPTCHA/WAF; o problema é carregamento dinâmico/erro de filtro e redirect das rotas legadas.

### 12. Quality gate

Regra obrigatória: rejeitar qualquer item com chamada de fomento, auxílio, bolsa, pesquisa, inovação, evento ou submissão de projeto. Só aceitar se uma página declarar explicitamente cargo, contratação, emprego, estágio ou seleção de pessoal por órgão. Nenhum caso aceitável foi encontrado.

### 13. Empty evidence

Para o escopo de pessoal, estado correto é `EMPTY_CORRECT`/`OUT_OF_SCOPE`: há centenas de chamadas institucionais, mas zero oportunidades de contratação observadas. Não interpretar o erro de carregamento como vazio técnico.

### 14. Diagnóstico técnico

Esta fonte não deve alimentar o mesmo índice de concursos. A semelhança lexical de “edital” e “seleção” é perigosa; FAPEMIG publica fomento. O portal moderno exige carregamento dinâmico e tem contagens variáveis.

### 15. Estratégia

`INSTITUTIONAL_FILTER_REQUIRED` + `KEEP_EMPTY` para seleção de pessoal; opcionalmente manter parser de arquivo de fomento separado, fora do produto de concursos. Não cadastrar chamadas como vagas.

### 16. Instruções ao Codex

Abrir a superfície moderna somente para confirmar o filtro; classificar todas as chamadas observadas como fomento; rejeitar “Pesquisador na Empresa” e bolsas; não usar contagens 190/4 como concursos; registrar vazio correto de pessoal e erro dinâmico separadamente.

### 17. Confiança e URLs

HIGH para a conclusão de escopo; MEDIUM para tecnologia/contagens dinâmicas. Evidências: [URL fornecida/redirect](https://fapemig.br/pt/editais/), [chamadas modernas](https://fapemig.br/oportunidades/chamadas-e-editais), [Pesquisador na Empresa](https://fapemig.br/oportunidades/chamadas-e-editais/chamada-fapemig-sede-013-2026-pesquisador-na-empresa), [dados abertos](https://fapemig.br/dados-abertos/).

## Observações transversais do lote

1. Avança SP e Sigma são claramente a mesma família ProSeleta: mesmos estados, rota `/informacoes/{id}/`, anexos `anexos-r2.selecao.net.br` e rodapé ProSeleta. Um conector parametrizado é plausível, mas contagens e domínios devem permanecer independentes.
2. Fênix usa `selecao.site` no host, porém o rodapé é Gestor Editais/ACT SISTEMAS; não deve ser agrupado automaticamente com ProSeleta.
3. Publiconsult e W2 exibem padrões de organizadoras cloud/legadas, mas não há evidência de API. Não inventar endpoints.
4. FEPESE exige descoberta multi-tenant por subdomínio; FUNCERN exige filtro institucional; FAPEMIG deve ficar fora do índice de pessoal.
5. Oppus e W2 são os casos que mais precisam de revisão manual por indisponibilidade/decodificação; Fênix precisa de reconciliação de snapshots de status.

