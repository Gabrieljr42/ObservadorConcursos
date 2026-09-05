# Observador de Concursos — BATCH 01 (fontes 01–13)

Pesquisa externa realizada em 30/08/2026 (America/Sao_Paulo). Foram consultadas as URLs fornecidas, páginas internas alcançáveis e busca restrita aos domínios oficiais. Não foram inferidos seletores, endpoints ou totais. `UNKNOWN` significa que a evidência pública disponível não permite concluir.

## 01 — IBFC

Identificador técnico: `ibfc_open`  
URL fornecida: https://concursos.ibfc.org.br/index/abertos/  
URL oficial confirmada: https://concursos.ibfc.org.br/index/abertos/  
Portal ativo: SIM (portal responde; inscrições abertas explicitamente vazias)  
URL mudou: NÃO

### Navegação

Homepage: https://concursos.ibfc.org.br/  
Abertos: https://concursos.ibfc.org.br/index/abertos/  
Em andamento: https://concursos.ibfc.org.br/index/1/  
Encerrados: https://concursos.ibfc.org.br/index/3/  
Detalhe: links internos da listagem; padrão de URL não foi exposto pelo texto acessível  
Documentos: links no detalhe (não há documentos no estado vazio observado)

### Universo observado

Observed: 347 itens nos estados acessíveis (8 em andamento + 339 finalizados; a página finalizada informa “Mostrando 1-20 de 339”).  
Relevant: 347 (concursos, processos seletivos e Jovem Aprendiz; seleção de pessoal).  
Active: 0 inscrições abertas (estado “Inscrições Abertas” diz literalmente “Nenhum item cadastrado”).  
Closed: 339 explicitamente finalizados; 8 em andamento.  
Out of scope: não observado.

### Listagem

Estrutura: página server-rendered com título `Concursos`, abas por status e itens com órgão, edital e período de inscrição. A finalizada é paginada e informa 1–20/339.  
Selector/container: classes CSS não foram expostas no conteúdo textual; não inventar.  
Título: texto do item, HTML.  
Link: link do item, HTML.  
ID: não exposto, UNKNOWN.  
Status: definido pela rota/aba (`abertos`, `1`, `3`), HTML/URL.

### Paginação

Método: paginação HTML na seção finalizada.  
Parâmetros: links numerados 1–6, `Próxima`, `Última`; URL efetiva dos links não foi exposta pela ferramenta. Codex deve seguir os hrefs reais e parar em Última.

### Exemplo real

Título: Instituto Brasileiro de Geografia e Estatística — IBGE, Edital nº 01/2026  
Órgão: IBGE  
Status: Em andamento (período exibido 12/06/2026–09/07/2026)  
URL: https://concursos.ibfc.org.br/index/1/ (item da listagem; detalhe não exposto)  
Edital: não há link acessível no resumo, UNKNOWN.

### Campos

Para o exemplo IBGE, a página acessível fornece: `titulo` HTML (texto do item); `orgao` HTML; `modalidade` UNKNOWN; `cargo` UNKNOWN; `area` UNKNOWN; `cidade` UNKNOWN; `uf` HTML quando aparece no título/órgão, mas não no exemplo; `status` HTML/URL; `vagas` UNKNOWN; `salario_min` UNKNOWN; `salario_max` UNKNOWN; `escolaridade` UNKNOWN; `taxa` UNKNOWN; `prova_data` UNKNOWN; `edital_numero` HTML (“Edital nº 01/2026”); `edital_data` UNKNOWN; `inscricao_inicio` HTML; `inscricao_fim` HTML; `link_edital` UNKNOWN; `link_inscricao` UNKNOWN. Detalhe deve ser seguido antes de preencher UNKNOWN.

### Publicações

Estrutura: não foi exibida no resumo do item; provavelmente no detalhe, UNKNOWN.  
Tipos: edital, retificação, resultado e demais publicações UNKNOWN.  
Selector/API: UNKNOWN.  
Deduplicação sugerida: chave pelo href/ID do concurso + texto e URL do documento.  
Ruídos: menu, abas, placeholder de imagem, cookies e rodapé.

### API/XHR

Endpoint: UNKNOWN; não há endpoint público evidenciado.  
Método/parâmetros/paginação/JSON path/autenticação: UNKNOWN.  
Observações: HTML já contém os itens; não assumir API.

### Tecnologia

Tipo: SERVER_RENDERED/HTML paginado.  
HTTP funciona: SIM (páginas legíveis).  
JS necessário: NÃO para listagem observada.  
Playwright necessário: NÃO indicado.

### Bloqueios

HTTP: página respondeu. Browser: conteúdo acessível. WAF/Cloudflare/CAPTCHA: não observado. Alternativa: usar `/index/1/` e `/index/3/`.

### Quality gate

ACEITAR SE: item estiver na aba de inscrições abertas/em andamento e representar concurso, processo seletivo ou contratação de pessoal; manter edital/documentos quando disponíveis.  
REJEITAR SE: for apenas conteúdo institucional, projeto social, menu ou finalizado quando o crawler estiver coletando ativos.

### Empty evidence

`EMPTY_EXPLICIT`: https://concursos.ibfc.org.br/index/abertos/ mostra “Inscrições Abertas — Nenhum item cadastrado.” Não converter em falha do crawler.

### Estratégia recomendada

`CONFIGURABLE_HTML`; manter `KEEP_EMPTY` para o estado aberto até mudança do portal. Não usar a página finalizada como fonte de ativos. Diagnóstico: `CRAWLER_STRATEGY_CLEAR`, `HTML_SUFFICIENT`, `EMPTY_CORRECT`.

### Instruções para Codex

1. GET `/index/abertos/`, `/index/1/` e `/index/3/`.
2. Parsear itens visíveis e seguir hrefs reais dos cards/linhas; não inventar classe.
3. Percorrer toda a paginação de finalizados apenas para histórico.
4. Usar os textos de status e datas como evidência; não classificar “Em andamento” como inscrição aberta sem data válida.
5. Testar explicitamente o texto empty e paginação 339.

### Confidence

HIGH — páginas oficiais, estados e contagem de finalizados foram observados diretamente; campos de detalhe e API continuam UNKNOWN.

### Evidências

https://concursos.ibfc.org.br/index/abertos/ (empty explícito); https://concursos.ibfc.org.br/index/1/ (8 em andamento); https://concursos.ibfc.org.br/index/3/ (339 finalizados e paginação).

## 02 — IDECAN

Identificador técnico: `idecan_open`  
URL fornecida/oficial: https://portal.concursos.idecan.org.br/edital/index/abertos  
Portal ativo: SIM  
URL mudou: NÃO

### Navegação

Homepage: https://portal.concursos.idecan.org.br/edital/index/abertos  
Abertos: mesma URL  
Em andamento: mesma listagem, seção “EM ANDAMENTO”  
Encerrados: mesma listagem, seção “FINALIZADOS”  
Detalhe: `/edital/ver/{id}` (observados `/edital/ver/24`, `/edital/ver/8`, `/edital/ver/6`)  
Documentos: links “Mais detalhes” e arquivos no detalhe.

### Universo observado

Observed: pelo menos 5 itens (3 em andamento + 2 finalizados visíveis; o restante da página não expôs total).  
Relevant: pelo menos 5, todos concursos/processos seletivos.  
Active: 0 em “EM INSCRIÇÃO” (mensagem explícita).  
Closed: pelo menos 2 na seção finalizados.  
Out of scope: nenhum dos itens observados.

### Listagem

Estrutura: HTML de uma página com seções “FUTUROS, abertos, em andamento, finalizados e suspensos”; cada item tem imagem/logo, modalidade/edital, órgão e link “Mais detalhes”.  
Selector/container: não exposto; não inventar classe.  
Título/órgão/status: HTML.  
ID: presente no href `/edital/ver/24` etc., HTML/URL.  
Datas: HTML no detalhe/listagem quando disponíveis.

### Paginação

Método: não observada no recorte; pode haver todos os itens em uma página.  
Parâmetros: UNKNOWN; Codex deve detectar links de próxima página ou limitar pelo conjunto de seções, sem assumir paginação.

### Exemplo real

Título: Concurso Público — EDITAL Nº 09  
Órgão: Corpo de Bombeiros Militar de Minas Gerais (CBMMG)  
Status: Em andamento; inscrições 18/05/2026–17/06/2026  
URL: https://portal.concursos.idecan.org.br/edital/ver/24  
Edital: “Nenhum arquivo postado até o momento”; há “Distribuição do Conteúdo — CFO” para Cadete BM.

### Campos

`titulo` HTML; `orgao` HTML; `modalidade` HTML (“Concurso Público”); `cargo` HTML (“Cadete BM”); `area` HTML/PDF quando em arquivo; `cidade` HTML (“Belo Horizonte - MG”); `uf` HTML; `status` HTML/seção; `vagas` UNKNOWN; `salario_min` HTML (remuneração 7.506,80 no exemplo); `salario_max` HTML; `escolaridade` UNKNOWN; `taxa` UNKNOWN; `prova_data` UNKNOWN; `edital_numero` HTML (“EDITAL Nº 09”); `edital_data` UNKNOWN; `inscricao_inicio` e `inscricao_fim` HTML; `link_edital` UNKNOWN no exemplo (nenhum arquivo); `link_inscricao` UNKNOWN.

### Publicações

Estrutura: arquivos aparecem no detalhe sob “VER EDITAL/INFORMAÇÕES”; no exemplo foi observada ausência explícita de arquivos e um arquivo de distribuição de conteúdo.  
Tipos: edital, distribuição de conteúdo e resultados, conforme títulos publicados; demais UNKNOWN.  
Selector/API: links HTML; endpoint de backend UNKNOWN.  
Deduplicação: `edital_id` do href `/edital/ver/{id}` + URL/título do arquivo.  
Ruídos: logos, menu, texto institucional Gestor Editais, cookies/rodapé.

### API/XHR

Endpoint: UNKNOWN; não há API pública evidenciada. Método, parâmetros, JSON path e autenticação UNKNOWN. A aplicação identifica-se como “Desenvolvido por Gestor Editais © 2012–2026”, evidência de plataforma, não de endpoint.

### Tecnologia

Tipo: SERVER_RENDERED/HTML, plataforma Gestor Editais.  
HTTP funciona: SIM. JS necessário: NÃO para conteúdo acessível. Playwright necessário: NÃO indicado.

### Bloqueios

HTTP/browser responderam; WAF/Cloudflare/CAPTCHA não observado. Alternativa: detalhes `/edital/ver/{id}`.

### Quality gate

ACEITAR SE: seção “EM INSCRIÇÃO”/“EM ANDAMENTO” e modalidade de seleção de pessoal; usar período e órgão do detalhe.  
REJEITAR SE: “FUTUROS” sem edital/inscrição ou publicações institucionais sem seleção.

### Empty evidence

`EMPTY_EXPLICIT` para inscrições: “NENHUM CONCURSO PÚBLICO OU PROCESSO SELETIVO ENCONTRADO”. Não equivale a portal vazio, pois há 3 em andamento e finalizados.

### Estratégia recomendada

`CONFIGURABLE_HTML`; possível conector compartilhado com IBADE (`Gestor Editais`), mas validar diferenças de tenant. Diagnóstico: `HTML_SUFFICIENT`, `API_AVAILABLE` não confirmado, `EMPTY_CORRECT` para abertos.

### Instruções para Codex

1. GET a listagem e separar as cinco seções por headings.
2. Extrair cada href real “Mais detalhes”; o ID é o segmento após `/edital/ver/`.
3. No detalhe, coletar título, órgão, modalidade, cidade/UF, período, cargo e links de arquivos.
4. Preservar “Nenhum arquivo postado até o momento” como empty de publicações.
5. Não deduzir vagas, taxa ou salário ausentes; testar `/ver/24`, `/ver/8` e `/ver/6`.

### Confidence

HIGH para estrutura/status; MEDIUM para universo total (não exposto) e API.

### Evidências

https://portal.concursos.idecan.org.br/edital/index/abertos; https://portal.concursos.idecan.org.br/edital/ver/24; https://portal.concursos.idecan.org.br/edital/ver/8; https://portal.concursos.idecan.org.br/edital/ver/6.

## 03 — Instituto AOCP

Identificador técnico: `aocp_open`  
URL fornecida/oficial: https://www.institutoaocp.org.br/  
Portal ativo: SIM, porém listagens são dinâmicas  
URL mudou: NÃO (rotas atuais incluem `/concursos/status/inscricoes-abertas`, `/concursos/status/em-andamento`)

### Navegação

Homepage: https://www.institutoaocp.org.br/  
Abertos: https://www.institutoaocp.org.br/concursos/status/inscricoes-abertas  
Em andamento: https://www.institutoaocp.org.br/concursos/status/em-andamento  
Encerrados: `/concursos/status/finalizados` (link do menu; href completo não exposto)  
Detalhe: `/concursos/{id}`; exemplos oficiais `/concursos/685` e `/concursos/686` em notícia do AOCP  
Documentos: detalhe do concurso.

### Universo observado

Observed: pelo menos 2 concursos na busca/indexação oficial (CESAMA e SAEB) e exemplos `/685` e `/686`; total UNKNOWN por conteúdo dinâmico.  
Relevant: pelo menos 2, todos concursos/seleções de pessoal.  
Active: ≥1 confirmado pela página “Concursos com Inscrições Abertas” (SAEB); homepage indexada mostra CESAMA como aberto; total UNKNOWN.  
Closed: UNKNOWN.  
Out of scope: projetos sociais, cursos livres, notícias e certificados.

### Listagem

Estrutura: menu com quatro estados; rota de abertos retornou apenas título, busca e rodapé no fetch textual, enquanto a indexação oficial encontrou itens (conteúdo client-side).  
Selector/container: UNKNOWN; não inventar.  
Título, órgão, status e links: HTML após renderização/possível JSON interno, origem exata UNKNOWN.  
ID: exemplificado no URL `/concursos/685`/`686` (HTML/URL).

### Paginação

Método/parâmetros: UNKNOWN. A página diz “Veja Mais Concursos com Inscrições Abertas”, mas não expôs href/paginação no HTML textual. Codex deve inspecionar DOM após renderização.

### Exemplo real

Título: Concurso Público do IFCE 2026 — Edital 01/2026 (Docentes) e Edital 02/2026 (Técnicos Administrativos)  
Órgão: Instituto Federal do Ceará  
Status: inscrições foram anunciadas como abertas; página oficial de detalhe 685/686  
URL: https://www.institutoaocp.org.br/concursos/685 e https://www.institutoaocp.org.br/concursos/686  
Edital: links/documentos no detalhe; URL do PDF não exposta pela fonte textual.

### Campos

`titulo`, `orgao`, `modalidade`, `status`, `link_inscricao`: HTML após renderização, conforme páginas/notícia oficial; `cargo`, `area`, `vagas`, `salario_min`, `salario_max`, `escolaridade`, `taxa`, `prova_data`, `edital_numero`, `edital_data`, `inscricao_inicio`, `inscricao_fim`, `link_edital`: PDF/HTML do detalhe (notícia confirma 276 vagas e períodos, mas não substitui o detalhe). `cidade`, `uf`: HTML/PDF. Campos ausentes no fetch: UNKNOWN.

### Publicações

Estrutura: página de detalhe por concurso, com arquivos e fases; títulos/links não apareceram no fetch da rota 685.  
Tipos: edital, retificação, resultado, gabarito e comunicados (a organização anuncia essas fases; estrutura exata UNKNOWN).  
Selector/API: UNKNOWN.  
Deduplicação: URL do documento + título/data.  
Ruídos: projetos sociais, cursos, notícias, certificados, banners e rodapé.

### API/XHR

Endpoint: UNKNOWN; rotas de status retornam shell sem cards no fetch textual, indicando JS/possível XHR, mas não foi possível reproduzir endpoint. Método, parâmetros, JSON path e autenticação UNKNOWN.

### Tecnologia

Tipo: REACT_SPA ou outra aplicação client-side não confirmada; classificar operacionalmente como `BROWSER_REQUIRED` até inspeção.  
HTTP funciona: PARCIAL (shell/SEO, sem itens).  
JS necessário: SIM para cards observados.  
Playwright necessário: PROVAVELMENTE SIM.

### Bloqueios

HTTP: shell sem listagem. Browser: busca/indexação mostra dados. WAF/Cloudflare/CAPTCHA: não observado. API alternativa: UNKNOWN; endpoint XHR: UNKNOWN; outra página oficial: notícias AOCP e rotas `/concursos/{id}`.

### Quality gate

ACEITAR SE: card estiver em rota “inscrições abertas/em andamento” e detalhe confirmar concurso/processo seletivo de pessoal.  
REJEITAR SE: notícia sem link de concurso, projeto social, curso ou certificado.

### Empty evidence

Não marcar vazio: o shell parece vazio, mas a busca oficial encontrou SAEB e a homepage indexada encontrou CESAMA. Situação: `UNKNOWN_EMPTY`/falso vazio provável.

### Estratégia recomendada

`PLAYWRIGHT` ou `HYBRID` (HTTP para detalhe quando possível + browser para carregar cards). Diagnóstico: `BROWSER_REQUIRED`, `INSUFFICIENT_EVIDENCE`, `DEDICATED_CONNECTOR_RECOMMENDED`.

### Instruções para Codex

1. Abrir `/concursos/status/inscricoes-abertas`, `/em-andamento`, `/finalizados` com browser.
2. Capturar DOM após cards carregarem; registrar href real e ID numérico.
3. Testar detalhes `/concursos/685` e `/concursos/686` e localizar documentos no DOM/rede.
4. Em cada card, extrair órgão, título, edital, status e link; buscar datas/vagas no detalhe/PDF.
5. Não aceitar shell sem cards como empty; criar teste de falso vazio e live retest de SAEB/CESAMA.

### Confidence

MEDIUM — existência de rotas e concursos foi confirmada por páginas oficiais/indexação; API, seletor e universo total não foram expostos.

### Evidências

https://www.institutoaocp.org.br/concursos/status/inscricoes-abertas; https://www.institutoaocp.org.br/concursos/status/em-andamento; https://www.institutoaocp.org.br/concursos/685; https://www.institutoaocp.org.br/concursos/686; https://noticias.institutoaocp.org.br/blog/comecam-as-inscricoes-dos-novos-concursos-do-ifce-com-276-vagas/.

## 04 — CONSULPAM

Identificador técnico: `consulpam_open`  
URL fornecida/oficial: https://www.consulpam.com.br/index.php?menu=concursos  
Portal ativo: SIM  
URL mudou: NÃO

### Navegação

Homepage: https://www.consulpam.com.br/  
Concursos/em andamento: URL fornecida  
Realizados: link “Concursos Realizados” no menu (href não exposto)  
Detalhes: links por concurso, vários apontam para `consulpam.selecao.net.br`  
Documentos/inscrição: abas/link dentro do item e portais de seleção.

### Universo observado

Observed: pelo menos 60 itens na listagem textual (links numerados 14–73) e seções de status.  
Relevant: pelo menos 60, todos concursos/processos seletivos de pessoal.  
Active: 9 itens com ícone “Inscrições Abertas” (Groaíras 003/2026, 002/2026; Câmara Massapê; Beberibe 002/2026; Beberibe 001/2026; Groaíras 001/2026; Moreilândia 002/2026; Moreilândia 001/2026; Sobral 001/2026).  
Closed: pelo menos 2 exibidos como encerrados no início, e muitos adicionais.  
Out of scope: nenhum item da listagem observado.

### Listagem

Estrutura: HTML com “Legenda de Status” por imagem/ícone e seção “Concursos Em Andamento”; cada item é link com órgão + edital/modalidade.  
Selector/container: classes não confirmadas; não inventar.  
Título/link/status: HTML e imagem alt/texto.  
ID: não exposto no resumo; UNKNOWN.

### Paginação

Método: não observada no recorte; listagem longa em uma página.  
Parâmetros: UNKNOWN; percorrer links reais e verificar se há paginação ao final.

### Exemplo real

Título: PREFEITURA MUNICIPAL DE GROAÍRAS-CE (003/2026-ACS E ACE — Concurso Público)  
Órgão: Prefeitura Municipal de Groaíras/CE  
Status: Inscrições abertas  
URL: link 14 da listagem, href não exposto pela ferramenta  
Edital: no detalhe/documentos; URL UNKNOWN.

### Campos

No item de exemplo: `titulo` HTML; `orgao` HTML; `modalidade` HTML (“CONCURSO PÚBLICO”); `cargo` HTML parcial (“ACS E ACE”); `area` UNKNOWN; `cidade` HTML (Groaíras); `uf` HTML (CE); `status` HTML/ícone; `vagas`, `salario_min`, `salario_max`, `escolaridade`, `taxa`, `prova_data`, `edital_data` UNKNOWN no resumo; `edital_numero` HTML (003/2026); `inscricao_inicio`, `inscricao_fim`, `link_edital`, `link_inscricao` UNKNOWN até detalhe.

### Publicações

Estrutura: detalhe do concurso e portal `consulpam.selecao.net.br` em alguns itens.  
Tipos: edital, retificação, resultados, gabaritos e comunicados; estrutura/selector UNKNOWN.  
Deduplicação: href/título do documento + concurso.  
Ruídos: legendas de ícones, menu, redes sociais, cookies, rodapé.

### API/XHR

Endpoint: UNKNOWN; conteúdo HTML já lista itens. Não assumir API. Método/parâmetros/auth UNKNOWN.

### Tecnologia

Tipo: SERVER_RENDERED/HTML. HTTP funciona: SIM. JS necessário: NÃO para listagem observada. Playwright: NÃO indicado.

### Bloqueios

HTTP/browser responderam; WAF/Cloudflare/CAPTCHA não observado. Alternativa: links `consulpam.selecao.net.br` para alguns detalhes.

### Quality gate

ACEITAR SE: ícone/texto “Inscrições Abertas” e modalidade concurso/processo seletivo; confirmar detalhe.  
REJEITAR SE: ícone realizado/encerrado ou link de serviço sem seleção.

### Empty evidence

Não vazio: 9 itens explicitamente abertos.

### Estratégia recomendada

`CONFIGURABLE_HTML`; conector secundário para links `consulpam.selecao.net.br`. Diagnóstico: `HTML_SUFFICIENT`, `CRAWLER_STRATEGY_CLEAR`.

### Instruções para Codex

1. GET URL fornecida e identificar a seção “Concursos Em Andamento”.
2. Usar o texto do item e o ícone de status; não tratar todos como abertos.
3. Seguir href real para detalhe; quando tenant `consulpam.selecao.net.br`, conservar o ID/href.
4. No detalhe, extrair documentos e campos ausentes da listagem.
5. Fixture: Groaíras 003/2026; testes para aberto, encerrado e links externos.

### Confidence

HIGH para estados e nove itens abertos; MEDIUM para total, seletores e documentos.

### Evidências

https://www.consulpam.com.br/index.php?menu=concursos (legenda e itens); https://www.consulpam.selecao.net.br/ (tenant citado nos links; detalhe exato deve ser seguido do href real).

## 05 — IBAM

Identificador técnico: `ibam_open`  
URL fornecida/oficial: https://www.ibam-concursos.org.br/  
Portal ativo: SIM; o próprio site alerta que este é o único domínio oficial  
URL mudou: NÃO

### Navegação

Homepage/listagem: https://www.ibam-concursos.org.br/  
Abertos/em andamento: mesma página, links “Edital disponível / Inscrições abertas” e “Concursos em andamento”  
Encerrados: link “Concursos encerrados” (href não exposto)  
Detalhe/inscrição: https://www.ibam-concursos.org.br/inscricao.asp?car=1769&cod=374&task=novo (formulário de Concordia)  
Documentos: links “DOCUMENTOS”/“Edital disponível”.

### Universo observado

Observed: pelo menos 5 certames na página inicial (Lages, Concordia, Arraial do Cabo, Caruaru, Nova Erechim), cada um com tabelas de cargos; total da página não exposto.  
Relevant: pelo menos 5.  
Active: 4 com inscrições abertas/período vigente na data da pesquisa (Concordia, Arraial do Cabo, Caruaru, Nova Erechim); Lages está suspenso e “inscrições em breve”.  
Closed: UNKNOWN.  
Out of scope: alerta antifraude, área do candidato, legislação e rodapé.

### Listagem

Estrutura: HTML server-rendered com cabeçalho do município, modalidade, texto de status, datas, tabela de escolaridade/cargo/prova/vagas/taxa e links de inscrição/documentos.  
Selector/container: sem classes confirmadas; usar headings/tabelas sem inventar seletor.  
Título/órgão/status: HTML.  
ID: href de inscrição carrega `car` e `cod` (HTML/URL); esses valores são internos, não generalizar.

### Paginação

Método: não observada; página inicial longa.  
Parâmetros: UNKNOWN; buscar todos os headings e verificar link de “Concursos encerrados/em andamento”.

### Exemplo real

Título: Município de Caruaru/PE — 01/2026  
Órgão: Prefeitura Municipal de Caruaru/PE  
Status: Inscrições abertas até 08/10/2026  
URL: https://www.ibam-concursos.org.br/ (seção do certame; href específico não exposto)  
Edital: “Edital de Abertura do Concurso Público 01/2026” e retificação 01, links HTML/PDF.

### Campos

`titulo`, `orgao`, `modalidade`, `cargo`, `cidade`, `uf`, `status`, `vagas`, `escolaridade`, `taxa`, `prova_data`, `edital_numero`, `inscricao_fim`, `link_edital`, `link_inscricao`: HTML (cargos/vagas/taxa/prova aparecem em tabelas; edital/documentos em links). `area` HTML quando cargo especializado; `salario_min`/`salario_max` PDF/HTML (o texto cita vencimentos no anexo, não resumo); `edital_data`, `inscricao_inicio`: HTML/PDF/UNKNOWN conforme item. Não copiar valores de outro município.

### Publicações

Estrutura: seção “DOCUMENTOS” por concurso e links de anexos.  
Tipos observados: edital de abertura, retificação/errata, anexos de cargos/provas/conteúdo, resultado de isenção, homologação e admissão.  
Selector/API: links HTML/PDF; API UNKNOWN.  
Deduplicação: URL absoluta do documento + texto/data.  
Ruídos: botão “INSCREVA-SE”, legislação, área do candidato, cookies, alerta antifraude.

### API/XHR

Endpoint: UNKNOWN; HTML contém dados. O formulário de inscrição usa query `car`, `cod`, `task` na URL de exemplo; isso é navegação, não API REST.

### Tecnologia

Tipo: SERVER_RENDERED/HTML + PDFs. HTTP funciona: SIM. JS necessário: NÃO para listagem. Playwright: NÃO indicado (não submeter formulários).

### Bloqueios

HTTP/browser responderam. WAF/Cloudflare/CAPTCHA não observado. Alternativa: somente domínio oficial alertado no site.

### Quality gate

ACEITAR SE: bloco declarar concurso/processo seletivo para quadro de pessoal e tiver cargo/vaga/período.  
REJEITAR SE: alerta antifraude, legislação ou área autenticada; não enviar formulário de inscrição.

### Empty evidence

Não vazio: quatro certames com período e tabelas de cargos; Lages explicitamente suspenso.

### Estratégia recomendada

`DEDICATED_CONNECTOR` (estrutura rica e tabelas, mas estável); HTTP_HTML pode ser base. Diagnóstico: `HTML_SUFFICIENT`, `DEDICATED_CONNECTOR_RECOMMENDED`.

### Instruções para Codex

1. GET homepage oficial e localizar headings de municípios, não confiar em posição fixa.
2. Parsear bloco até o próximo heading; extrair status, período e tabelas por cabeçalhos sem inventar CSS.
3. Seguir links de documentos e converter PDF para campos detalhados; manter link de inscrição separado.
4. Não marcar Lages como ativo enquanto estiver “suspenso”/“inscrições em breve”.
5. Fixture Caruaru e teste de errata/documentos.

### Confidence

HIGH para estrutura e exemplos; MEDIUM para total geral e URLs de detalhes.

### Evidências

https://www.ibam-concursos.org.br/; https://www.ibam-concursos.org.br/inscricao.asp?car=1769&cod=374&task=novo; https://www.ibam-concursos.org.br/?status=2.

## 06 — IBADE

Identificador técnico: `ibade_open`  
URL fornecida/oficial: https://portal.ibade.selecao.site/edital  
Portal ativo: SIM  
URL mudou: NÃO

### Navegação

Listagem: https://portal.ibade.selecao.site/edital  
Detalhe observado: https://portal.ibade.selecao.site/edital/ver/126  
Abertos: seção “EM INSCRIÇÃO” na listagem  
Em andamento: seção “EM ANDAMENTO”  
Finalizados: seção “FINALIZADOS”  
Documentos: “Arquivos Disponíveis” no detalhe.

### Universo observado

Observed: pelo menos 6 em andamento + vários finalizados; total não exposto.  
Relevant: pelo menos 6, todos concursos/processos/seleções de pessoal.  
Active: 0 em “EM INSCRIÇÃO” (mensagem explícita).  
Closed: vários na seção finalizados; total UNKNOWN.  
Out of scope: menus, rodapé, texto institucional Gestor Editais.

### Listagem

Estrutura: página HTML por seções; item contém logo, modalidade/edital, órgão e “Mais detalhes”.  
Selector/container: UNKNOWN; não inventar.  
Título/órgão/status: HTML. ID: href `/edital/ver/126` (HTML/URL).

### Paginação

Método: não observada no recorte; verificar links adicionais. Parâmetros: UNKNOWN.

### Exemplo real

Título: Concurso Público 001/2026  
Órgão: Prefeitura Municipal de Itarana/ES  
Status: Em andamento; comunicados atualizados em 25/08/2026  
URL: https://portal.ibade.selecao.site/edital/ver/126  
Edital: link “Edital de Abertura” em Arquivos Disponíveis.

### Campos

`titulo`, `orgao`, `modalidade`, `status`, `edital_numero`, `link_edital`: HTML (detalhe/links); `cargo`, `area`, `escolaridade`: HTML no detalhe e/ou PDF; o exemplo lista códigos S01–S12 e requisitos; `cidade`, `uf`: HTML (Itarana/ES); `vagas`, `salario_min`, `salario_max`, `taxa`, `prova_data`, `inscricao_inicio`, `inscricao_fim`, `edital_data`, `link_inscricao`: PDF/HTML/UNKNOWN (não presentes no recorte). `publicações`: HTML com data/título/link DOWNLOAD.

### Publicações

Estrutura: no detalhe, lista cronológica “Arquivos Disponíveis” com data, título e link DOWNLOAD.  
Tipos observados: convocação para prova, quantitativo de inscritos, homologação, resultados PcD/atendimento/isenção, respostas a recursos, cronograma, quadro de vagas, edital e histórico de comunicados.  
Selector/API: links HTML; endpoint UNKNOWN.  
Deduplicação: concurso ID + data + título + URL.  
Ruídos: imagens/logo, requisitos de cargo, rodapé e login.

### API/XHR

Endpoint: UNKNOWN. Plataforma identificada como Gestor Editais pelo rodapé; não assumir API comum sem teste.

### Tecnologia

Tipo: SERVER_RENDERED/HTML, Gestor Editais. HTTP funciona: SIM. JS necessário: NÃO para conteúdo observado. Playwright: NÃO indicado.

### Bloqueios

HTTP/browser responderam; WAF/CAPTCHA não observado. Alternativa: detalhe `/edital/ver/{id}`.

### Quality gate

ACEITAR SE: modalidade concurso/processo/seleção e bloco em andamento tiver cargo/edital.  
REJEITAR SE: vestibular, conteúdo institucional ou publicação sem relação com seleção de pessoal.

### Empty evidence

`EMPTY_EXPLICIT` para “EM INSCRIÇÃO”: “NENHUM CONCURSO PÚBLICO OU PROCESSO SELETIVO ENCONTRADO”; não tratar em andamento como vazio.

### Estratégia recomendada

`CONFIGURABLE_HTML`; avaliar conector compartilhado Gestor Editais com IDECAN, mantendo tenants separados. Diagnóstico: `HTML_SUFFICIENT`, `EMPTY_CORRECT` para abertos.

### Instruções para Codex

1. Parsear seções `EM INSCRIÇÃO`, `EM ANDAMENTO`, `FINALIZADOS`.
2. Extrair href e ID de cada “Mais detalhes”.
3. No detalhe, coletar a lista cronológica de DOWNLOADs (data, título, URL) e cargos/requisitos.
4. Preservar aviso “nenhum encontrado” apenas para a seção correspondente.
5. Fixture Itarana `/edital/ver/126`; testar deduplicação e histórico de comunicados.

### Confidence

HIGH para estrutura e exemplo; MEDIUM para totais e API.

### Evidências

https://portal.ibade.selecao.site/edital; https://portal.ibade.selecao.site/edital/ver/126.

## 07 — Instituto Consulplan (portal www)

Identificador técnico: `consulplan_open`  
URL fornecida/oficial: https://www.consulplan.net/  
Portal ativo: SIM, interface pública responde  
URL mudou: NÃO; há portal legado separado documentado abaixo

### Navegação

Homepage/listagem: https://www.consulplan.net/  
Abertos: link “Concursos Abertos” (href não exposto)  
Em andamento: link correspondente no menu  
Próximos/novos/encerrados: headings visíveis na página  
Detalhe/documentos: cards não foram renderizados no fetch textual; UNKNOWN.

### Universo observado

Observed: headings “Inscrições abertas”, “Em andamento”, “Próximos concursos”, “Novos Concursos” e “Encerrados”, mas nenhum card textual no fetch; total UNKNOWN.  
Relevant/Active/Closed: UNKNOWN.  
Out of scope: empresa, serviços, certificados, clientes, cookies.

### Listagem

Estrutura: página com campo “Pesquisar por...” e carrosséis/áreas de status; conteúdo provavelmente carregado por JS.  
Selector/container, título, link, ID, status: UNKNOWN (não inventar).

### Paginação

Método: visualmente há links “Anterior/Próximo” no HTML, mas sem href útil no conteúdo textual. Tratar como UNKNOWN e verificar DOM/rede.

### Exemplo real

Título/órgão/status/URL: UNKNOWN na interface www devido ausência de cards.  
Fixture externo somente para investigação de migração: https://institutoconsulplan.azurewebsites.net/Concursos (portal oficial da mesma marca, fonte 38); não usar como fixture da fonte 07 sem decisão do Sol.

### Campos

Todos os campos do exemplo (`titulo`, `orgao`, `modalidade`, `cargo`, `area`, `cidade`, `uf`, `status`, `vagas`, salários, escolaridade, taxa, prova, edital, datas e links): UNKNOWN na interface acessível. PDFs no domínio `cdnsite.consulplan.net` são evidência de que documentos existem no ecossistema, mas não devem ser atribuídos ao card www sem href.

### Publicações

Estrutura/tipos/selector/API: UNKNOWN na interface www. Não confundir links de política, clientes e certificados com publicações.

### API/XHR

Endpoint/método/parâmetros/JSON path/auth: UNKNOWN. A ausência de cards no HTML sugere JS/XHR, mas não comprova endpoint.

### Tecnologia

Tipo: REACT_SPA/VUE/OTHER UNKNOWN; operacionalmente conteúdo dinâmico. HTTP funciona: PARCIAL. JS necessário: PROVAVELMENTE SIM. Playwright: PROVAVELMENTE SIM.

### Bloqueios

HTTP: shell responde. Browser: cards não confirmados pela ferramenta. WAF/Cloudflare: não observado. Alternativa: portal Azure oficial da mesma marca (fonte 38), tratado como origem separada até revisão.

### Quality gate

ACEITAR SE: card renderizado confirmar concurso/processo seletivo e detalhe/documento oficial.  
REJEITAR SE: apenas heading vazio, notícias, serviços ou vestibular sem seleção de pessoal.

### Empty evidence

`UNKNOWN_EMPTY`: headings existem, mas não há evidência de que as listas estejam realmente vazias; pode ser conteúdo JS não renderizado.

### Estratégia recomendada

`PLAYWRIGHT`/`HYBRID`; `DEPRECATE_REVIEW_REQUIRED` somente se o Sol confirmar que www foi substituído pelo Azure. Diagnóstico: `BROWSER_REQUIRED`, `PORTAL_MIGRATED` (suspeita não confirmada), `INSUFFICIENT_EVIDENCE`.

### Instruções para Codex

1. Abrir a interface www com browser e aguardar cards.
2. Inspecionar rede/DOM para obter hrefs reais, paginação Anterior/Próximo e detalhes.
3. Validar se cards coincidem com `institutoconsulplan.azurewebsites.net/Concursos` antes de unir universos.
4. Não retornar zero quando somente headings forem capturados.
5. Criar teste de falso vazio e registrar decisão de alias separadamente da fonte 38.

### Confidence

LOW — interface responde, mas listagem, exemplo, API e contagens não foram observáveis; requer revisão do Sol.

### Evidências

https://www.consulplan.net/; https://institutoconsulplan.azurewebsites.net/Concursos (403 no fetch direto, mas indexado oficialmente com cards e categorias); https://cdnsite.consulplan.net/concursos/1777%20/%201_531136.pdf (edital oficial indexado citando www.consulplan.net).

## 08 — SEPROD

Identificador técnico: `seprod_open`  
URL fornecida: https://www.seprod.com.br/concursos/?utm_refererencia=em_andamento  
URL fornecida/oficial: https://www.seprod.com.br/concursos/  
Portal ativo: PARCIAL (domínio e página existem; listagem não foi reproduzida diretamente)  
URL mudou: NÃO confirmada

### Navegação

Homepage: https://www.seprod.com.br/  
Concursos: https://www.seprod.com.br/concursos/  
Em andamento/próximos/finalizados: opções visíveis na página, hrefs não expostos.  
Detalhe/documentos: PDFs sob `/concursos/{id}/...pdf` aparecem indexados; detalhe HTML UNKNOWN.

### Universo observado

Observed: página de concursos encontrada na busca oficial, com categorias “Em andamento”, “Próximos concursos”, “Concursos finalizados”; cards/total não acessíveis.  
Relevant/Active/Closed: UNKNOWN.  
Out of scope: login/CPF, 2ª via, pagamentos, isenções e notícias antigas.

### Listagem

Estrutura: página inclui área de candidato e menu de estados; conteúdo de concursos possivelmente carregado após sessão/JS. Selector/container, título, link, ID, status: UNKNOWN.

### Paginação

UNKNOWN; verificar DOM após browser e links de cada categoria.

### Exemplo real

Título: Prefeitura Municipal de Capim Grosso — Processo Seletivo Público 01/2022 (documento oficial indexado)  
Órgão: Prefeitura Municipal de Capim Grosso/BA  
Status: encerrado/histórico (publicação de 2022)  
URL: https://www.seprod.com.br/ (notícia indexada) e documentos sob `/concursos/`  
Edital: PDFs históricos indexados; não usar como ativo.

### Campos

No portal atual: todos os campos de seleção UNKNOWN. Em PDFs históricos, `titulo`, `orgao`, `modalidade`, `cargo`, `vagas`, `salario`, `escolaridade`: PDF; demais datas/status/links: PDF/UNKNOWN. Não usar PDF histórico como contagem atual.

### Publicações

Estrutura: PDFs por diretórios numéricos (exemplos indexados `/concursos/0060/...pdf`, `/0118/...pdf`), contendo resultados/atas/editais. Tipos e mapeamento por ID: PDF; selector/API UNKNOWN. Deduplicar por URL/hash. Ruídos: login, cookies, notícias, comprovantes.

### API/XHR

Endpoint: UNKNOWN; página retorna erro interno na ferramenta. Não inferir API a partir dos diretórios PDF.

### Tecnologia

Tipo: OTHER/portal com área autenticada e PDFs. HTTP funciona: UNKNOWN/PARCIAL. JS necessário: UNKNOWN. Playwright: PROVAVELMENTE para conteúdo público carregado.

### Bloqueios

HTTP direto: erro interno na pesquisa; Browser: página oficial indexada e resultado textual parcial; WAF/Cloudflare/CAPTCHA: não comprovado. API alternativa: UNKNOWN; PDFs oficiais são alternativa de histórico, não de listagem ativa.

### Quality gate

ACEITAR SE: card/documento atual confirmar processo seletivo ou concurso de pessoal e status/datas.  
REJEITAR SE: área de candidato autenticada, notícia antiga, resultado sem certame atual ou menu.

### Empty evidence

`UNKNOWN_EMPTY`: categorias existem, mas ausência de cards não permite afirmar vazio.

### Estratégia recomendada

`KEEP_BLOCKED` + `PLAYWRIGHT`/`HYBRID` após validação; não marcar `KEEP_EMPTY`. Diagnóstico: `INSUFFICIENT_EVIDENCE`, `BROWSER_REQUIRED` provável.

### Instruções para Codex

1. Validar URL com browser e capturar as três categorias sem login.
2. Se cards exigirem JS, registrar requisições de rede; só usar endpoint se observado.
3. Seguir links de documentos atuais e manter PDFs históricos fora do universo ativo.
4. Nunca retornar zero baseado apenas no shell/erro.
5. Fixture futura deve ser um certame atual confirmado pelo site; caso continue inacessível, manter bloqueado e abrir revisão Sol.

### Confidence

LOW — acesso direto falhou e não há listagem atual reproduzível; requer revisão do Sol.

### Evidências

https://www.seprod.com.br/concursos/; https://www.seprod.com.br/; https://www.seprod.com.br/concursos/EDITAL_CONCURSO_S%C3%83O_FRANCISCO.pdf (PDF histórico indexado).

## 09 — FCC

Identificador técnico: `fcc_open`  
URL fornecida/oficial: https://www.concursosfcc.com.br/concursoAndamento.html  
Portal ativo: SIM  
URL mudou: NÃO

### Navegação

Listagem: URL fornecida, com seções “Próximos concursos” e “Em andamento”.  
Detalhe: padrão `/concursos/{slug}/index.html`, exemplo https://www.concursosfcc.com.br/concursos/abgfg126/index.html.  
Documentos/publicações: links e arquivos no detalhe; portal do candidato separado.

### Universo observado

Observed: 30 certames listados em “Em andamento” no recorte (ABGF, ARTESP, assembleias, defensorias, FDSBC, fundações, governos, MPs, polícias, tribunais etc.).  
Relevant: maioria concursos/empregos; inclui vestibulares/certificações que devem ser filtrados.  
Active: UNKNOWN — “Em andamento” não equivale necessariamente a inscrições abertas.  
Closed: UNKNOWN (não é a página de encerrados).  
Out of scope observado: vestibulares (UNASP, FDSBC), certificações CFP/EQT e concursos internos, conforme título.

### Listagem

Estrutura: HTML com duas colunas/links de órgão e cargo; detalhe é slug HTML. Selector/container não exposto; título/órgão/modalidade HTML. ID: slug no href.

### Paginação

Não observada; listagem única no recorte. Parâmetros UNKNOWN.

### Exemplo real

Título: ABGF — Agência Brasileira Gestora de Fundos Garantidores e Garantia  
Órgão: ABGF  
Status: Em andamento; página atualizada 25/08/2026  
URL: https://www.concursosfcc.com.br/concursos/abgfg126/index.html  
Edital: Edital 01/2026 de abertura, retificações 02/03/04 e documentos de vagas/resultados.

### Campos

`titulo`, `orgao`, `modalidade`, `cargo`, `salario_min/max`, `escolaridade`, `status`, `taxa`, `inscricao_inicio/fim`, `link_edital`, `link_inscricao`: HTML no detalhe; ABGF informa cargos, salários, taxa R$145 e períodos. `area`: HTML (Analistas/TI etc.); `cidade`, `uf`, `vagas`, `prova_data`, `edital_numero/data`: HTML/PDF conforme edital; alguns UNKNOWN no resumo.

### Publicações

Estrutura: detalhe com “Links e Arquivos” e “Publicações”.  
Tipos observados: edital abertura, retificações/prorrogação/reabertura, comunicados, listas/isenções, vagas reservadas, provas, gabaritos, resultados, homologação e convocação.  
Selector/API: links HTML para PDF/portal.  
Deduplicação: título + data + URL absoluta.  
Ruídos: Acrobat Reader, portal do candidato, banners e aviso de cookies.

### API/XHR

Endpoint: UNKNOWN; HTML server-rendered suficiente. Método/auth UNKNOWN.

### Tecnologia

Tipo: SERVER_RENDERED/HTML + PDF. HTTP funciona: SIM. JS necessário: NÃO para detalhe observado. Playwright: NÃO indicado.

### Bloqueios

HTTP/browser responderam; WAF/CAPTCHA não observado.

### Quality gate

ACEITAR SE: título indicar concurso/seleção para cargo/emprego e detalhe tiver edital/período.  
REJEITAR SE: vestibular, certificação, exame profissional ou concurso interno quando o escopo exigir seleção pública externa.

### Empty evidence

Não vazio: 30 itens em andamento observados; active operacional deve ser calculado por datas, não pelo heading.

### Estratégia recomendada

`DEDICATED_CONNECTOR` (listagem por slug + detalhe rico) ou `CONFIGURABLE_HTML`. Diagnóstico: `HTML_SUFFICIENT`, `INSTITUTIONAL_FILTER_REQUIRED`.

### Instruções para Codex

1. GET `concursoAndamento.html` e coletar pares órgão/cargo e hrefs.
2. Derivar slug somente do href real; abrir cada `/concursos/{slug}/index.html`.
3. Extrair “Links e Arquivos” e “Publicações”, preservando data/título/URL.
4. Aplicar filtro: excluir vestibular, certificação e concurso interno quando não forem seleção de pessoal.
5. Fixture ABGF (`abgfg126`) e teste de reabertura/retificação.

### Confidence

HIGH para estrutura e fixture; MEDIUM para active e filtro de modalidades.

### Evidências

https://www.concursosfcc.com.br/concursoAndamento.html; https://www.concursosfcc.com.br/concursos/abgfg126/index.html; https://www.concursosfcc.com.br/concursos/unica124/index.html.

## 10 — FGV

Identificador técnico: `fgv_open`  
URL fornecida/oficial: https://conhecimento.fgv.br/concursos  
Portal ativo: SIM  
URL mudou: NÃO

### Navegação

Listagem: https://conhecimento.fgv.br/concursos  
Detalhe exemplo: https://conhecimento.fgv.br/cpnu2  
Documentos: seção “Arquivos do concurso” no detalhe.  
Busca: campo “Qual concurso você está procurando?”.

### Universo observado

Observed: pelo menos 44 links de concursos no recorte da listagem (inclui a segunda sequência), sem total explícito.  
Relevant: maioria concursos/processos seletivos; também exames de cartórios, magistratura, CFC/EQT e certificações — filtrar.  
Active: pelo menos 1 explicitamente “Em Andamento” (CPNU2); total UNKNOWN.  
Closed: itens históricos misturados (ex.: BANESTES 2022); status por detalhe.  
Out of scope: exames/certificações e vestibulares, conforme título.

### Listagem

Estrutura: HTML com campo de busca e links de título; não há status na listagem textual. Selector/container UNKNOWN; hrefs HTML. ID: slug no href (`/cpnu2`).

### Paginação

Não observada; lista longa em uma página. Busca pode filtrar por texto, mas parâmetros/XHR UNKNOWN.

### Exemplo real

Título: Concurso Público Nacional Unificado 2  
Órgão: concurso federal (órgão/edital especificados no detalhe)  
Status: Em Andamento  
URL: https://conhecimento.fgv.br/cpnu2  
Edital: arquivos listados em “Arquivos do concurso”; exemplo edital Enap nº 233/2026 e outros.

### Campos

`titulo`, `status`, `link_edital`, `edital_numero/data`, `publicações`: HTML no detalhe; `orgao`, `modalidade`, `cargo`, `area`, `cidade`, `uf`, `vagas`, salários, escolaridade, taxa, prova e datas: HTML/PDF no detalhe/edital, alguns não presentes no recorte; `link_inscricao`: HTML (há links externos “Página de Acompanhamento”).

### Publicações

Estrutura: “Arquivos do concurso” em ordem de data com título e link; detalhe CPNU2 mostra editais Enap e links de fases. Tipos: editais, retificações, comunicados, resultados, fases. Selector/API UNKNOWN. Deduplicar data+título+URL. Ruídos: contatos, cookies, certificados e links externos.

### API/XHR

Endpoint: UNKNOWN; listagem e detalhe são HTML legíveis. Não inventar API.

### Tecnologia

Tipo: SERVER_RENDERED/HTML + PDFs; possível busca JS, não confirmada. HTTP funciona: SIM. JS necessário: NÃO para conteúdo observado. Playwright: NÃO indicado.

### Bloqueios

Sem WAF/CAPTCHA; HTTP/browser responderam.

### Quality gate

ACEITAR SE: detalhe tiver status e cargo/emprego/processo seletivo de pessoal.  
REJEITAR SE: exame de certificação, cartório, vestibular ou conteúdo sem provimento/seleção de pessoal.

### Empty evidence

Não vazio: CPNU2 “Em Andamento” e dezenas de links.

### Estratégia recomendada

`CONFIGURABLE_HTML` + filtro institucional. Diagnóstico: `HTML_SUFFICIENT`, `INSTITUTIONAL_FILTER_REQUIRED`.

### Instruções para Codex

1. GET listagem e coletar todos os hrefs reais, inclusive sequência além da primeira tela.
2. Abrir cada slug, extrair status, órgão/modalidade e “Arquivos do concurso”.
3. Seguir links externos de inscrição/acompanhamento apenas como `link_inscricao`.
4. Excluir exames, certificações e vestibulares por modalidade/título.
5. Fixture CPNU2; teste de arquivo datado e filtro de exame.

### Confidence

HIGH para listagem/detalhe; MEDIUM para total e classificação de active.

### Evidências

https://conhecimento.fgv.br/concursos; https://conhecimento.fgv.br/cpnu2.

## 11 — CEBRASPE

Identificador técnico: `cebraspe_open`  
URL fornecida: https://www.cebraspe.org.br/concursos/  
URL oficial confirmada: https://www.cebraspe.org.br/Concursos/ (variação de capitalização indexada)  
Portal ativo: PARCIAL (shell exige JavaScript)  
URL mudou: NÃO; apenas capitalização/redirect observados

### Navegação

Homepage: https://www.cebraspe.org.br/  
Concursos: https://www.cebraspe.org.br/Concursos/  
Em andamento/encerrados: abas visíveis no portal, href/API UNKNOWN  
Detalhe: `/concursos/{slug}`, exemplos oficiais `/concursos/anac_23`, `/concursos/pref_porto_alegre_rs_26`  
Documentos: páginas de detalhe + CDN `cdn.cebraspe.org.br/concursos/{slug}/arquivos/...`.

### Universo observado

Observed: categorias “Concursos encerrados” e “Concursos em andamento”, mas cards não foram carregados no fetch; exemplos oficiais indexados incluem ANAC, Porto Alegre, Agepar, Câmara dos Deputados etc.  
Relevant/Active/Closed: UNKNOWN sem renderização da listagem.  
Out of scope: notícias e materiais não ligados a seleção.

### Listagem

Estrutura: SPA/shell com aviso “É necessário habilitar o javascript para ver esta página corretamente”; cards e status não acessíveis sem browser. Selector/container, API e IDs da listagem UNKNOWN. Detalhes usam slug explícito no URL.

### Paginação

UNKNOWN; verificar carregamento JS/JSON e abas. Não supor paginação.

### Exemplo real

Título: Concurso Público para Agência Nacional de Aviação Civil — ANAC  
Órgão: Agência Nacional de Aviação Civil  
Status: página de detalhe em fase final/encerrada (resultado final publicado em 18/02/2026)  
URL: https://www.cebraspe.org.br/concursos/anac_23  
Edital: lista de comunicados/editais na página e arquivos CDN.

### Campos

No detalhe ANAC: `titulo`, `orgao`, `cargo/area`, `status`, publicações e links: HTML; `vagas`, salários, escolaridade, taxa, prova, inscrição, edital: HTML/PDF conforme edital. `link_edital` é CDN/HTML; `link_inscricao` pode ser consulta individual. Campos ausentes: UNKNOWN.

### Publicações

Estrutura: detalhe por slug com data, hora/título de “Editais, comunicados e informações” e links; arquivos CDN em PDF/HTML. Tipos observados: edital, comunicado, gabarito, resultado, convocação e curso de formação. Deduplicar slug+data+título+URL. Ruídos: VLibras, consultas individuais, cabeçalhos e rodapé.

### API/XHR

Endpoint: UNKNOWN; shell exige JS, mas não foi possível observar rede. Não inventar endpoint.

### Tecnologia

Tipo: REACT_SPA/OTHER UNKNOWN; operacionalmente BROWSER_REQUIRED. HTTP funciona: PARCIAL (shell). JS necessário: SIM. Playwright: PROVAVELMENTE SIM.

### Bloqueios

HTTP: shell/aviso JS; browser: não validado nesta pesquisa. WAF/Cloudflare/CAPTCHA: não observado. Alternativa: páginas de detalhe e CDN oficiais indexadas.

### Quality gate

ACEITAR SE: detalhe oficial indicar provimento/seleção de cargos/empregos e publicações correspondentes.  
REJEITAR SE: notícia institucional, consulta individual ou documento sem vínculo ao certame.

### Empty evidence

`UNKNOWN_EMPTY`; ausência de cards é explicada pelo requisito de JavaScript, não por vazio.

### Estratégia recomendada

`PLAYWRIGHT`/`HYBRID`; manter CDN/HTML de detalhes como fallback. Diagnóstico: `BROWSER_REQUIRED`, `INSUFFICIENT_EVIDENCE`.

### Instruções para Codex

1. Abrir `/Concursos/` com browser e aguardar JS; capturar abas e cards.
2. Registrar hrefs/slugs reais e status; não usar shell vazio como empty.
3. Para cada slug, extrair publicações datadas e URLs CDN; parsear PDFs/HTML.
4. Fixture ANAC e `pref_porto_alegre_rs_26`; teste de falso vazio e documento CDN.

### Confidence

MEDIUM para estrutura de detalhe; LOW para listagem/API/contagens, requer revisão do Sol.

### Evidências

https://www.cebraspe.org.br/Concursos/; https://www.cebraspe.org.br/concursos/anac_23; https://www.cebraspe.org.br/concursos/pref_porto_alegre_rs_26; https://cdn.cebraspe.org.br/concursos/.

## 12 — CESGRANRIO

Identificador técnico: `cesgranrio_open`  
URL fornecida: https://www.cesgranrio.org.br/concursos/  
URL oficial alternativa confirmada: https://concursos.cesgranrio.org.br/  
Portal ativo: INCERTO/PARCIAL  
URL mudou: POSSÍVEL migração para subdomínio `concursos.cesgranrio.org.br`

### Navegação

URL fornecida: retorna erro interno na pesquisa.  
Portal de concursos alternativo: https://concursos.cesgranrio.org.br/ (responde sem conteúdo textual).  
Detalhes/documentos: arquivos indexados sob `concursos.cesgranrio.org.br/media/gpoweb-prd-hibrido3/eventos/...` e subportais por evento; estrutura atual UNKNOWN.

### Universo observado

Observed/Relevant/Active/Closed: UNKNOWN; nenhuma listagem atual reproduzível.  
Evidência institucional: a Fundação realiza concursos públicos e vestibulares, mas isso não é contagem do portal.  
Out of scope: revistas, ANBIMA e portais de certificação quando não concurso público.

### Listagem

Estrutura/selector/container/título/link/ID/status: UNKNOWN por erro interno e portal alternativo sem texto.

### Paginação

UNKNOWN.

### Exemplo real

Título: BANESE 01/2025 (documento/resultado indexado no domínio de concursos)  
Órgão: Banco do Estado de Sergipe — BANESE  
Status: histórico/encerrado (publicação 2025)  
URL: arquivo indexado em `https://concursos.cesgranrio.org.br/media/...pdf`  
Edital: PDF/documento oficial; não usar como ativo.

### Campos

Nos documentos PDF indexados, cargo, localidade, status e resultados são PDF. No portal atual todos os campos de listagem/detalhe: UNKNOWN. Não transformar resultados PDF em concurso ativo.

### Publicações

Estrutura: PDFs em armazenamento `media/gpoweb-prd-hibrido3/eventos/...`; tipos incluem editais/resultados, mas evento e metadados não confirmados. Selector/API UNKNOWN. Deduplicar URL/hash.

### API/XHR

Endpoint: UNKNOWN; não foi possível carregar portal. Não inventar.

### Tecnologia

Tipo: OTHER/portal de eventos UNKNOWN. HTTP funciona: NÃO/PARCIAL (erro interno na URL original; subdomínio sem texto). JS necessário: UNKNOWN. Playwright: PROVAVELMENTE.

### Bloqueios

HTTP original: erro interno; browser: não reproduzido. WAF/Cloudflare/CAPTCHA: não comprovado. Alternativa oficial: subdomínio de concursos e PDFs CDN, apenas para histórico/validação.

### Quality gate

ACEITAR SE: evento atual no portal oficial confirmar concurso/processo seletivo de pessoal com edital.  
REJEITAR SE: certificação ANBIMA, revista, vestibular ou PDF de resultado histórico sem evento atual.

### Empty evidence

`UNKNOWN_EMPTY`/`KEEP_BLOCKED`: não há evidência suficiente para vazio.

### Estratégia recomendada

`KEEP_BLOCKED` + `DEPRECATE_REVIEW_REQUIRED` para avaliar migração do domínio; não remover fonte. Diagnóstico: `SITE_OFFLINE` (URL original na ferramenta), `PORTAL_MIGRATED` possível, `INSUFFICIENT_EVIDENCE`.

### Instruções para Codex

1. Validar em browser URL original e `concursos.cesgranrio.org.br`.
2. Se o subdomínio carregar, mapear eventos/links e observar rede antes de implementar.
3. Manter PDFs `media/...` como documentos, não como itens independentes.
4. Não retornar zero e não tratar ANBIMA/revistas como concurso.
5. Abrir revisão do Sol para decidir alias/migração; fixture BANESE somente histórico.

### Confidence

LOW — portal atual não reproduzível; migração e API precisam de nova investigação.

### Evidências

https://www.cesgranrio.org.br/concursos/; https://concursos.cesgranrio.org.br/; https://concursos.cesgranrio.org.br/media/gpoweb-prd-hibrido3/eventos/ (padrão de arquivos indexados); https://revistas.cesgranrio.org.br/index.php/index/about.

## 13 — IDCAP

Identificador técnico: `idcap_open`  
URL fornecida/oficial: https://www.idcap.org.br/  
Portal ativo: SIM  
URL mudou: NÃO

### Navegação

Homepage/listagem: https://www.idcap.org.br/  
Abertos: link “Inscrições Abertas”  
Em andamento: `/index/1/` (rota observada)  
Finalizados: `/index/3/`  
Cancelados: link “Cancelados”  
Detalhe: links “Saiba mais” (href não exposto no recorte)  
Documentos: detalhe do concurso.

### Universo observado

Observed: 22 itens na listagem em andamento (do TJBA/NUPEMEC até CRCCE) visíveis no recorte; a página não expõe total.  
Relevant: 22 observados, todos concursos/processos seletivos ou seleção privada de trabalhadores; filtrar vestibular se aparecer.  
Active: pelo menos 2 com período futuro/aberto no recorte (TJBA/NUPEMEC sem datas, OGMO Itajaí “Em Breve”); total de inscrições abertas precisa de rota própria, UNKNOWN.  
Closed: itens com datas já passadas na mesma listagem; status de finalizado deve vir de `/index/3/`.  
Out of scope: área do candidato, projetos sociais, treinamento.

### Listagem

Estrutura: HTML com headings “Concursos / Processos Seletivos Em andamento”, abas por status, campo “Busca...” e cards que exibem tipo, título, edital, datas e algumas vagas.  
Selector/container: classes não expostas; não inventar.  
Título/órgão/status/datas/vagas: HTML. ID: href de “Saiba mais”, UNKNOWN no texto.

### Paginação

Método: não observada no recorte; verificar páginas `index/1`, `index/3` e eventual navegação ao final. Parâmetros UNKNOWN.

### Exemplo real

Título: Concurso Público nº 002/2026 — Prefeitura Municipal de Itupeva/SP — GCM  
Órgão: Prefeitura Municipal de Itupeva/SP  
Status: Em andamento/listagem; inscrições 28/07/2026–19/08/2026 (período encerrado em 30/08, embora o bloco esteja em andamento)  
URL: página oficial https://www.idcap.org.br/ (href “Saiba mais” não exposto)  
Edital: Edital nº 002/2026 no card; link do documento UNKNOWN.

### Campos

`titulo`, `orgao`, `modalidade`, `status`, `edital_numero`, `inscricao_inicio`, `inscricao_fim`, `vagas`: HTML no card (ex.: Itupeva GCM, 20 vagas). `cargo/area`: HTML no título (GCM); `cidade`, `uf`: HTML; `salario_min/max`, `escolaridade`, `taxa`, `prova_data`, `edital_data`, `link_edital`, `link_inscricao`: detalhe/PDF/UNKNOWN. Alguns cards têm “Pedidos de Isenção”, também HTML.

### Publicações

Estrutura: não exposta no card; seguir “Saiba mais” para documentos. Tipos esperados/observados no ecossistema: edital, retificação, resultados e comunicados; selector/API UNKNOWN. Deduplicar URL+título/data. Ruídos: área do candidato, busca, abas, links de cancelado.

### API/XHR

Endpoint: UNKNOWN; cards aparecem no HTML acessível, sem API confirmada. Não inventar.

### Tecnologia

Tipo: SERVER_RENDERED/HTML. HTTP funciona: SIM. JS necessário: NÃO para cards observados. Playwright: NÃO indicado.

### Bloqueios

HTTP/browser responderam; WAF/Cloudflare/CAPTCHA não observado. Alternativa: rotas `/index/1/`, `/index/3/` e cancelados.

### Quality gate

ACEITAR SE: card/detalhe confirmar concurso/processo seletivo de pessoal, com órgão e período; seleção privada OGMO pode ser mantida se escopo aceitar contratação.  
REJEITAR SE: vestibular, treinamento, projeto social, cancelado ou apenas área autenticada.

### Empty evidence

Não vazio: 22 itens observados em andamento; active deve ser separado por período, não pelo heading.

### Estratégia recomendada

`CONFIGURABLE_HTML`; possível conector dedicado somente se detalhe divergir. Diagnóstico: `HTML_SUFFICIENT`, `INSTITUTIONAL_FILTER_REQUIRED`.

### Instruções para Codex

1. GET homepage e rotas de status; extrair todos os cards.
2. Guardar tipo, órgão, título, edital, datas e vagas quando presentes.
3. Seguir href real de “Saiba mais” para edital/documentos e inscrição.
4. Calcular active por datas/status; não considerar todo “Em andamento” como aberto.
5. Fixture Itupeva GCM (20 vagas) e teste de período encerrado + rota finalizados.

### Confidence

HIGH para listagem e campos de card; MEDIUM para active total, detalhes e documentos.

### Evidências

https://www.idcap.org.br/; https://www.idcap.org.br/index/1/; https://www.idcap.org.br/index/3/.

## Casos para revisão do Sol

1. Fonte 07 — Consulplan www: cards não renderizados; confirmar se é alias/substituta do portal Azure da fonte 38 antes de implementar.
2. Fonte 08 — SEPROD: acesso direto retornou erro interno; confirmar rota/JS/API atual e decidir `KEEP_BLOCKED`.
3. Fonte 11 — CEBRASPE: listagem exige JavaScript; obter API/XHR ou estratégia Playwright.
4. Fonte 12 — CESGRANRIO: possível migração para `concursos.cesgranrio.org.br`; confirmar portal e universo antes de implementar.
5. Fonte 03 — AOCP: shell vazio, mas indexação oficial mostra ativos; investigar DOM/rede para evitar falso empty.
