# BATCH 02 — Reconhecimento operacional (fontes 14–26)

Pesquisa externa realizada em 30/08/2026. As contagens abaixo são somente o que foi observado nas páginas abertas/indexadas durante a pesquisa; `UNKNOWN` significa que o portal não expõe um total verificável naquela página. Não foram inferidos seletores, endpoints ou números.

## 14 — IBGP

Identificador técnico: `ibgp_open`  
URL fornecida: https://novo.ibgpconcursos.com.br/inscricoes_abertas.jsp  
URL oficial confirmada: https://novo.ibgpconcursos.com.br/index.jsp e https://novo.ibgpconcursos.com.br/inscricoes_abertas.jsp  
Portal ativo: PARCIAL. A página de inscrições abertas retornou o cabeçalho sem cards; o índice possui os estados “Em breve”, “Abertos”, “Em andamento” e “Homologados”.

### Navegação
Homepage/índice: `/index.jsp`; abertos: `/inscricoes_abertas.jsp`; em andamento: link “EM ANDAMENTO” no índice (URL não exposta no texto); homologados: link correspondente; detalhe: links `concurso.jsp?cod={id}` foram encontrados em documentos oficiais; documentos: `/rest/concurso/download/edital/{edital_id}/?file=site/anexos/{anexo_id}/{arquivo}`.

### Universo observado
Observed: 0 cards na página de abertos; 4 estados no índice. Relevant: UNKNOWN. Active: UNKNOWN (há PDFs recentes, mas não são prova de card ativo). Closed: UNKNOWN. Out of scope: vestibulares podem aparecer e devem ser filtrados.

### Listagem
Estrutura textual: cabeçalho/abas e campo “PESQUISAR”; nenhum container de item foi exposto pelo HTML textual. Selector/container: UNKNOWN (não inventar). Título/link/ID/status: no detalhe, o ID aparece em `concurso.jsp?cod=662`; no PDF, o ID de edital aparece no caminho REST.

### Paginação
Método/parâmetros: UNKNOWN na listagem de abertos; testar abas e busca do índice. Não assumir que a página vazia representa todo o catálogo.

### Exemplo real
Título: Concurso Público do Município de Lagoa da Prata/MG (documento cronograma). Órgão: Município de Lagoa da Prata/MG. Status: documento de certame em andamento em 2026, não validado como card aberto na captura. URL: https://ftp.novo.ibgpconcursos.com.br/rest/concurso/download/edital/21269/?file=site%2Fanexos%2F657%2FCRONOGRAMA+-+CONCURSO+LAGOA+DA+PRATA-MG.pdf. Edital: PDF no mesmo padrão REST.

### Campos
`titulo` HTML/PDF; `orgao` HTML/PDF; `modalidade` HTML/PDF; `cargo`, `area`, `cidade`, `uf`, `vagas`, `salario`, `escolaridade`, `taxa`, `prova`, `edital_numero`, `edital_data`, `inscricao_inicio`, `inscricao_fim`: PDF (edital/anexos); `status`: HTML quando exposto na aba/detalhe, caso contrário UNKNOWN; `link_edital`: HTML (href REST); `link_inscricao`: HTML (área do candidato); `salario_min/max`: PDF; nenhuma API JSON pública confirmada.

### Publicações
Estrutura: arquivos por concurso, principalmente PDFs. Tipos observados em PDFs indexados: edital, retificações, cronograma, gabarito, resultados, homologação e convocações. Selector/API: UNKNOWN; deduplicar por URL normalizada e nome/data; ruído: PDFs de vestibular, menus e páginas de terceiros que apenas apontam para o IBGP.

### API/XHR
Endpoint de documentos confirmado: `https://novo.ibgpconcursos.com.br/rest/concurso/download/edital/{id}/?file=site/anexos/{tenant}/{arquivo}`; método GET; paginação/JSON path/autenticação: UNKNOWN. É um download público usado pelos próprios sites/órgãos. Não foi confirmada API de listagem.

### Tecnologia
Tipo: SERVER_RENDERED, OTHER (JSP) e PDF_INDEX. HTTP funciona: PARCIAL (web indexou páginas, mas a captura direta teve bloqueio de socket). JS necessário: UNKNOWN. Playwright: provavelmente não para PDFs; possível para abas/busca se HTTP não retornar cards.

### Bloqueios
HTTP: tentativa local falhou por restrição de socket; navegador de pesquisa conseguiu ler índice. Browser: parcial. WAF/Cloudflare/CAPTCHA: não confirmado. Alternativa: FTP/REST de documentos e páginas de órgãos municipais. API alternativa: endpoint de download SIM; XHR de listagem NÃO CONFIRMADO; outra página oficial SIM (`index.jsp`).

### Quality gate
ACEITAR se o item tiver órgão público/entidade, modalidade de seleção de pessoal, datas ou edital e cargo/vagas. REJEITAR vestibular, curso, prova sem seleção de pessoal e documentos sem vínculo com certame.

### Empty evidence
`UNKNOWN_EMPTY`: `/inscricoes_abertas.jsp` mostra literalmente apenas “Inscrições abertas” e rodapé, sem mensagem “nenhum”; abas de índice continuam disponíveis. Não converter em zero global.

### Estratégia recomendada
`HYBRID` + `KEEP_EMPTY` temporário: usar índice/abas HTML; seguir `concurso.jsp?cod=`; baixar documentos pelo endpoint REST; reter UNKNOWN se a listagem continuar sem cards.

### Instruções para Codex
1. Fazer GET em `/index.jsp` e `/inscricoes_abertas.jsp`; preservar os quatro estados e o campo de pesquisa. 2. Descobrir os href reais em runtime, sem fabricar seletores. 3. Seguir `concurso.jsp?cod={id}` quando presente. 4. Para documentos, aceitar somente GET no padrão `/rest/concurso/download/edital/...`; extrair cargos/datas do PDF. 5. Criar teste de página aberta sem cards (não gerar active=0), PDF e vestibular rejeitado. 6. Live retest com edital 21269.

### Confidence
MEDIUM — domínio/estrutura e endpoint de PDF são reproduzíveis, mas a listagem de abertos estava sem itens e a API de catálogo não foi exposta.

### Evidências
https://novo.ibgpconcursos.com.br/index.jsp; https://novo.ibgpconcursos.com.br/inscricoes_abertas.jsp; https://novo.ibgpconcursos.com.br/rest/concurso/download/edital/21269/?file=site%2Fanexos%2F657%2FCRONOGRAMA+-+CONCURSO+LAGOA+DA+PRATA-MG.pdf; https://novo.ibgpconcursos.com.br/concurso.jsp?cod=662.

## 15 — FUNDEP / Gestão de Concursos

Identificador técnico: `fundep_open`  
URL fornecida: https://www.gestaodeconcursos.com.br/site/site/default.aspx  
URL oficial confirmada: https://www.gestaodeconcursos.com.br/site/site/default.aspx (catálogo visual) e https://fundep.selecao.net.br (detalhes)  
Portal ativo: SIM; a homepage alerta que o site de concursos mudou.

### Navegação
Homepage: `/site/site/default.aspx`; estados exibidos: Novos Concursos, Inscrições Abertas, Em Andamento, Homologados; detalhes: `https://fundep.selecao.net.br/informacoes/{id}/`; documentos e inscrição aparecem no detalhe; concursos realizados: link no menu.

### Universo observado
Observed: homepage mostra um card por estado (4 cards na captura, mas cada “Ver todos” abre universo maior). Relevant: UNKNOWN; Active: pelo menos 2 certames de pessoal observados (DMAE `informacoes/63`, EMATER `informacoes/71`), total UNKNOWN; Closed: UNKNOWN; Out of scope: vestibulares e seriados.

### Listagem
Estrutura: seções de homepage com título de órgão, título de certame, data e “Saiba Mais/Ver Todos”; detalhe textual expõe `##`, “Informações Gerais”, “Publicações” e tabela “Vaga | Qtde.” Selector/container: UNKNOWN no texto; link de detalhe `/informacoes/{id}/`; ID numérico no path; status em “Situação”.

### Paginação
Homepage não é universo completo; usar “Ver Todos” e páginas de estado. Parâmetros/endpoint de paginação: UNKNOWN. Percorrer todos os hrefs obtidos de cada estado, deduplicando IDs.

### Exemplo real
Título: Concurso Público DMAE — 01/2026. Órgão: Departamento Municipal de Água e Esgoto de Uberlândia. Status: Em andamento; inscrições 11/08/2026–11/09/2026. URL: https://fundep.selecao.net.br/informacoes/63/. Edital: publicação “EDITAL DO CONCURSO PÚBLICO Nº 01/2026...” no detalhe.

### Campos
`titulo`, `orgao`, `modalidade`, `status`, `inscricao_inicio`, `inscricao_fim`, `edital_numero`, `edital_data`, `link_edital`, `link_inscricao`: HTML; `cargo`, `vagas`, `escolaridade`, `taxa`: HTML no quadro de vagas/detalhe; `salario_min/max`, `area`, `cidade`, `uf`, `prova`: PDF/UNKNOWN dependendo do edital; `publicações`: HTML com links PDF. Não foi confirmada API JSON.

### Publicações
Detalhe organiza edital/retificações, isenção, resultados, gabaritos, recursos e convocações em lista “Publicações”; links apontam para `anexos.cdn.selecao.net.br`/`anexos-r2.selecao.net.br`. Deduplicar por href e título/data. Ruído: vestibular/seriado e login de candidato.

### API/XHR
Não confirmado endpoint de catálogo ou XHR. IDs públicos em `/informacoes/{id}/`; documentos em CDN via GET; autenticação só para área do candidato. Não inventar REST.

### Tecnologia
SERVER_RENDERED, HTML, PDF_INDEX; footer identifica “Sistema de Gerenciamento de Concursos” e ProSeleta. HTTP funciona: SIM para detalhes; JS: NÃO aparente; Playwright: NÃO para listagem/detalhe.

### Bloqueios
Sem 403/429/CAPTCHA observado na pesquisa web; tentativa HTTP local foi limitada pelo ambiente. API alternativa: não confirmada; XHR: não confirmado; página oficial alternativa: `fundep.selecao.net.br`.

### Quality gate
ACEITAR concurso/processo seletivo para emprego/cargo com órgão e edital. REJEITAR vestibular, seriado, exame de título acadêmico e demais seleções educacionais não laborais.

### Empty evidence
Não há evidência de vazio; homepage contém cards. Contagem total permanece UNKNOWN.

### Estratégia recomendada
`CONFIGURABLE_HTML` compartilhável com ProSeleta; filtro institucional obrigatório; `PDF` para salário/prova/cargos.

### Instruções para Codex
1. Usar os estados e “Ver Todos” da homepage; não usar somente os cards destacados. 2. Extrair hrefs `/informacoes/{id}/`. 3. No detalhe, ler “Situação”, datas e tabela “Vaga | Qtde.”. 4. Seguir links CDN de Publicações; priorizar edital consolidado. 5. Filtrar vestibular/seriado. 6. Testar paginação/universo, DMAE ativo e vestibular rejeitado; live retest `/informacoes/63/` e `/informacoes/71/`.

### Confidence
HIGH para estrutura/detalhe; MEDIUM para total do universo, pois a homepage é resumida.

### Evidências
https://www.gestaodeconcursos.com.br/site/site/default.aspx; https://fundep.selecao.net.br/informacoes/63/; https://fundep.selecao.net.br/informacoes/71/.

## 16 — FUMARC

Identificador técnico: `fumarc_open`  
URL fornecida/oficial: https://www.fumarc.com.br/SitePages/Home.aspx e https://www.fumarc.com.br/conheca-a-fumarc  
Portal ativo: PARCIAL. A organização confirma sistema próprio e páginas dedicadas, porém o conteúdo operacional é majoritariamente biblioteca de documentos.

### Navegação
Homepage institucional; concursos/detalhes: páginas dedicadas por órgão; documentos: `https://www.fumarc.com.br/Documentos%20Compartilhados/...`; listagem SharePoint: `.../Forms/AllItems.aspx?FolderCTID=...&RootFolder=...`; inscrição é indicada no edital/portal do certame; resultados/gabaritos em PDFs/SharePoint.

### Universo observado
Observed: pelo menos 1 processo seletivo real (Ubá 08/2025) e documentos de Iturama 01/2025; total UNKNOWN. Relevant: pelo menos 2; Active: UNKNOWN; Closed: UNKNOWN; Out of scope: conteúdo institucional.

### Listagem
Estrutura: não foi encontrada listagem global reproduzível; páginas de documentos SharePoint usam biblioteca e pastas. Selector/container/título/status/ID: UNKNOWN. Links de arquivo possuem nomes legíveis e pasta do órgão.

### Paginação
SharePoint pode paginar biblioteca, mas parâmetro não confirmado. Percorrer pasta `RootFolder` e links “AllItems”; não assumir apenas primeira página.

### Exemplo real
Título: Processo Seletivo Simplificado — Edital nº 08/2025, Rede Municipal de Ensino de Ubá. Órgão: Prefeitura Municipal de Ubá/MG. Status: seleção para contratação temporária; edital PDF. URL: https://www.fumarc.com.br/Documentos%20Compartilhados/Prefeitura%20Municipal%20de%20Ub%C3%A1/Edital%20Publicado.pdf. Edital: PDF confirmado.

### Campos
`titulo`, `orgao`, `modalidade`, `cargo`, `area`, `cidade`, `uf`, `vagas`, `salario`, `escolaridade`, `taxa`, `prova`, `edital_numero`, `edital_data`, `inscricao_inicio`, `inscricao_fim`: PDF; `link_edital`/publicações: HTML SharePoint; `status`: PDF ou UNKNOWN; `link_inscricao`: PDF/UNKNOWN. Não foi confirmada API JSON.

### Publicações
Biblioteca/pastas de documentos; edital, retificações, gabaritos, resultados, convocações e homologação em arquivos PDF. Deduplicar por URL canônica e título/data; ignorar imagens, navegação, avisos de cookies e documentos institucionais.

### API/XHR
SharePoint `Forms/AllItems.aspx` foi confirmado por URL oficial, mas `_api` não foi testado/confirmado. Método GET para HTML/PDF; autenticação não exigida para os PDFs observados. Não inventar `_api` ou JSON path.

### Tecnologia
SHAREPOINT_API (biblioteca SharePoint), PDF_INDEX, SERVER_RENDERED. HTTP funciona: PARCIAL (PDF sim; biblioteca pode exigir JS); JS: PARCIAL; Playwright: possível para navegação de biblioteca, não para PDF.

### Bloqueios
Uma página SharePoint informa que o navegador precisa habilitar scripts; não é CAPTCHA. WAF/Cloudflare: não confirmado. Alternativa: URLs diretas de PDF e páginas de órgãos. API alternativa: `_api` UNKNOWN.

### Quality gate
ACEITAR concurso, processo seletivo público/simplificado ou contratação temporária com cargos. REJEITAR material institucional, cursos, notícias sem edital de pessoal e bolsas/fomento.

### Empty evidence
`UNKNOWN_EMPTY`: não existe índice global verificável; ausência de listagem não prova ausência de certame.

### Estratégia recomendada
`SHAREPOINT_API` somente após validar `_api`; fallback `CONFIGURABLE_HTML`/PDF e `KEEP_BLOCKED` se biblioteca exigir interação.

### Instruções para Codex
1. Descobrir páginas dedicadas e pastas oficiais por links do site. 2. Tentar biblioteca SharePoint em modo leitura; só usar `_api` se o próprio tenant responder. 3. Baixar PDFs diretos e extrair texto com pypdf. 4. Parsear título, órgão, cargos, vagas e cronograma do edital. 5. Filtrar documentos não laborais. 6. Criar teste para SharePoint com JS indisponível, PDF de Ubá e ausência de índice. Live retest na URL do edital de Ubá.

### Confidence
MEDIUM — PDF e SharePoint confirmados; catálogo global/endpoint de listagem não confirmado.

### Evidências
https://www.fumarc.com.br/conheca-a-fumarc; https://www.fumarc.com.br/Documentos%20Compartilhados/Prefeitura%20Municipal%20de%20Ub%C3%A1/Edital%20Publicado.pdf; https://www.fumarc.com.br/Documentos%20Compartilhados/Forms/AllItems.aspx?FolderCTID=0x0120001FB7EC7FA4BA094D92983EA76483352E&RootFolder=%2FDocumentos+Compartilhados%2FPrefeitura+Municipal+de+Betim%2FProcesso+Seletivo+Simplificado%2FEdital+e+Anexos.

## 17 — IMESO

Identificador técnico: `imeso_open`  
URL fornecida/oficial: https://portal.imeso.com.br/edital  
Portal ativo: SIM (portal de editais e detalhes).

### Navegação
Listagem: `/edital`; detalhe: `/edital/ver/{id}`; documentos: links “DOWNLOAD” para `s3.us-east-1.amazonaws.com/cdn.imeso.com.br/edital/...`; categorias/listagem de editais e fases estão no detalhe; inscrição é indicada no edital/detalhe.

### Universo observado
Observed: 4 detalhes amostrados (IDs 122, 124, 127, 135) e vários IDs indexados; total UNKNOWN. Relevant: 4; Active: UNKNOWN (páginas exibem cronogramas/status de fases, alguns prazos já passados); Closed: UNKNOWN; Out of scope: não observado.

### Listagem
Detalhe server-rendered com título, órgão, município/UF, período de inscrição, data e lista cronológica de publicações. Selector/container: UNKNOWN; link de detalhe `/edital/ver/{id}`; ID numérico; status/etapa aparece no conteúdo, não há atributo estruturado confirmado.

### Paginação
Parâmetros da listagem `/edital`: UNKNOWN. Usar todos os hrefs de `/edital/ver/` e seguir paginação/busca somente se encontrada no HTML.

### Exemplo real
Título: Concurso Público 001/2026. Órgão: Prefeitura Municipal de Augusto de Lima/MG. Status: página de certame com inscrições 26/05/2026–26/06/2026 e publicações posteriores. URL: https://portal.imeso.com.br/edital/ver/127. Edital: link “EDITAL CONFORME ERRATA...” em download S3.

### Campos
`titulo`, `orgao`, `modalidade`, `cidade`, `uf`, `status`, `inscricao_inicio`, `inscricao_fim`: HTML; `cargo`, `vagas`, `salario`, `escolaridade`: HTML quando quadro de cargos está na página (ex.: ID 122), caso contrário PDF; `taxa`, `prova`, `edital_numero`, `edital_data`: PDF/HTML; `link_edital` e publicações: HTML href S3; `link_inscricao`: HTML/UNKNOWN; `area`: UNKNOWN.

### Publicações
Lista cronológica com editais, erratas, formulários, isenção, homologações, mapas de candidatos, gabaritos, resultados e convocações. Links S3; deduplicar por href + texto/data e preservar retificações. Ruído: “Sobre a IMESO”, contato, navegação e imagens.

### API/XHR
Nenhum endpoint JSON/XHR confirmado. Download S3 é público por GET; autenticação não observada. Não inventar API.

### Tecnologia
SERVER_RENDERED, PDF_INDEX, OTHER (Gestor Editais, identificado no rodapé). HTTP funciona: SIM nas páginas indexadas; JS: NÃO aparente; Playwright: NÃO provável.

### Bloqueios
Nenhum 403/429/CAPTCHA confirmado na pesquisa web; HTTP local foi limitado pelo ambiente. Alternativa: links S3/PDF. API/XHR: não confirmado.

### Quality gate
ACEITAR concurso/PS para cargo, função ou contratação pública. REJEITAR cursos, chamadas acadêmicas e documentos sem seleção de pessoal.

### Empty evidence
`UNKNOWN_EMPTY`: não foi observado texto explícito de ausência; detalhes existem. Não usar zero de `/edital` sem varrer todos os links.

### Estratégia recomendada
`CONFIGURABLE_HTML` + PDF; conector dedicado somente se a listagem exigir descoberta não documentada.

### Instruções para Codex
1. GET `/edital`, coletar todos hrefs `/edital/ver/{id}` e páginas seguintes se existirem. 2. No detalhe extrair título/órgão/período/status e todos os links “DOWNLOAD”. 3. Classificar publicações por texto/data; baixar edital/retificações. 4. Extrair cargos/vagas/salários da tabela HTML ou PDF. 5. Testar ID 122 (quadro de vagas) e ID 127 (muitas publicações), deduplicação e estado sem inscrições.

### Confidence
HIGH para detalhe e documentos; MEDIUM para contagem total/paginação.

### Evidências
https://portal.imeso.com.br/edital/ver/127; https://portal.imeso.com.br/edital/ver/122; https://portal.imeso.com.br/edital/ver/135.

## 18 — OMNI Concursos

Identificador técnico: `omni_open`  
URL fornecida: https://portal.omniconcursospublicos.com.br  
URL oficial confirmada: https://portal.omniconcursospublicos.com.br/ e também https://institutoomni.selecao.net.br/ (mesma marca/ProSeleta; ambos acessíveis).  
Portal ativo: SIM. URL mudou: NÃO comprovado como substituição; documentar os dois tenants/domínios.

### Navegação
Portal fornecido possui estados Inscrições Abertas, Em andamento, Homologado, Finalizado, Suspenso, Cancelado; novo domínio possui a mesma navegação. Detalhes no padrão `/informacoes/{id}/`; documentos em `cdn.omniconcursospublicos.com.br/edital/...pdf` ou links de anexos.

### Universo observado
Observed: 2 cards no portal fornecido (Papanduva/Holambra históricos) e 4 cards no novo domínio (Saltinho, Tapejara, CISAMUSEP, Catanduvas). Relevant: 6 observados; Active: pelo menos 2 com inscrições futuras na captura (Saltinho e Tapejara); total UNKNOWN. Closed: UNKNOWN. Out of scope: nenhum nos exemplos.

### Listagem
Estrutura ProSeleta: item com tipo, `h3` textual/título, edital, datas, “Inscrições Abertas!”, vagas e “Mais Informações”; selector CSS exato não exposto (UNKNOWN). Link de detalhe `/informacoes/{id}/`, ID numérico, status por estado/texto.

### Paginação
Não observada na página principal; estados separados. Percorrer `/index/abertos/`, `/index/todos/` se disponíveis e todos os hrefs de detalhes. Parâmetros: UNKNOWN.

### Exemplo real
Título: Concurso Público 001/2026 — Câmara Municipal de Saltinho/SC. Órgão: Câmara Municipal de Saltinho/SC. Status: inscrições abertas, 20/08/2026–15/09/2026. URL: https://institutoomni.selecao.net.br/ (card; detalhe esperado `/informacoes/44/`, cache não abriu). Edital: publicação no detalhe, URL exata não confirmada no cache.

### Campos
`titulo`, `orgao`, `modalidade`, `status`, `inscricao_inicio`, `inscricao_fim`: HTML; `edital_numero`, `vagas`: HTML quando exibidos; `cargo`, `salario`, `escolaridade`, `taxa`, `prova`, `edital_data`: PDF/HTML do detalhe; `link_edital`, `link_inscricao`: HTML; `area`, `cidade`, `uf`: HTML/PDF. API JSON/XHR: UNKNOWN.

### Publicações
Detalhes ProSeleta agrupam edital, retificações, isenção, inscrições, convocação, gabarito, resultados e homologação; PDFs CDN. Deduplicar URL/título/data. Ruído: login, cookies, navegação e links de contato.

### API/XHR
Não confirmado endpoint público; footer confirma ProSeleta. Método GET para páginas/PDF; autenticação apenas área do candidato. Não inventar API.

### Tecnologia
SERVER_RENDERED, PDF_INDEX, OTHER (ProSeleta). HTTP funciona: SIM; JS: NÃO aparente; Playwright: NÃO para conteúdo público.

### Bloqueios
Portal e novo domínio foram lidos; sem WAF/CAPTCHA confirmado. O domínio `www.omniconcursospublicos.com.br` retornou 403 na pesquisa, mas não é o URL fornecido. Alternativa: `portal...` e `institutoomni...`; API: não confirmada.

### Quality gate
ACEITAR concurso, processo seletivo ou seleção competitiva para emprego/cargo. REJEITAR cursos, material não oficial e páginas de terceiros; conferir cancelados/suspensos.

### Empty evidence
Não vazio; há cards. Total UNKNOWN.

### Estratégia recomendada
`CONFIGURABLE_HTML` compartilhável com ProSeleta; manter os dois domínios configuráveis e `KEEP_BLOCKED` apenas para `www` 403.

### Instruções para Codex
1. Configurar ambos os hosts oficiais e não substituir o portal fornecido sem teste de equivalência. 2. Percorrer estados e extrair links `/informacoes/{id}/`. 3. Parsear tipo, edital, datas, status e vagas. 4. Coletar PDFs CDN do detalhe. 5. Testar um item de cada host, suspensão/cancelamento e deduplicação por órgão+edital; live retest portal e institutoomni.

### Confidence
MEDIUM — engine e estrutura fortes, mas os dois domínios apresentam universos aparentemente diferentes e um detalhe atual não abriu no cache.

### Evidências
https://portal.omniconcursospublicos.com.br/; https://institutoomni.selecao.net.br/; https://www.omniconcursospublicos.com.br/informacoes/85/; https://cdn.omniconcursospublicos.com.br/edital/1/5/90818e73ab3c7b22aac5bc235c07e1e1.pdf.

## 19 — Instituto ACCESS

Identificador técnico: `access_open`  
URL fornecida/oficial: https://access.selecao.net.br/index/abertos/ e homepage https://access.selecao.net.br/  
Portal ativo: SIM.

### Navegação
Estados: `/index/abertos/`, `/index/todos/`, “Em andamento”, homologado, finalizado, suspenso e cancelado; detalhe `/informacoes/{id}/`; inscrição online e publicações no detalhe; PDFs em `anexos.cdn.selecao.net.br`/`anexos-r2.selecao.net.br`.

### Universo observado
Observed: homepage exibiu 15 cards em andamento (inclui UFAC especialização). Relevant: pelo menos 14 de pessoal entre os cards; Active: pelo menos 2 com prazo futuro na captura (Guapimirim e Engenheiro Paulo de Frontin); Closed: vários cards com prazos passados, total UNKNOWN. Out of scope: UFAC “processo seletivo para curso de especialização”.

### Listagem
ProSeleta: tipo, título (`h3` textual), edital, datas, etiqueta “Inscrições Abertas!”, vagas e href “Mais Informações”; selector CSS exato UNKNOWN; detalhe `/informacoes/{id}/`; ID numérico/status em texto.

### Paginação
Estados separados; `/index/todos/?busca=1` observado. Parâmetros de paginação não confirmados; varrer hrefs de todas as páginas/estados.

### Exemplo real
Título: Prefeitura Municipal de Navegantes/SC — Concurso Público Edital 062/2026. Órgão: Prefeitura de Navegantes/SC. Status: Em andamento (período 14/04/2026–28/05/2026). URL: https://access.selecao.net.br/informacoes/161/. Edital: “EDITAL Nº 062/2026 – EDITAL DE ABERTURA CONSOLIDADO” e retificação, links CDN.

### Campos
`titulo`, `orgao`, `modalidade`, `inscricao_inicio`, `inscricao_fim`, `status`, `edital_numero`, `edital_data`, `link_edital`, `link_inscricao`: HTML; `cargo`, `vagas`, `escolaridade`, `salario`, `taxa`, `prova`: HTML/PDF (quadro de vagas/edital); `area`, `cidade`, `uf`: HTML/PDF; API JSON/XHR: UNKNOWN.

### Publicações
Categorias no detalhe: Edital, Anexos, Provas e Gabaritos, Resultados, Comunicados, retificações e recursos. Links CDN; deduplicar por href e título/data. Ruído: login, cookies, contato, breadcrumb.

### API/XHR
Nenhum endpoint confirmado; ProSeleta no footer. GET público para HTML/PDF; autenticação somente área do candidato.

### Tecnologia
SERVER_RENDERED, PDF_INDEX, OTHER (ProSeleta). HTTP funciona: SIM; JS: NÃO aparente; Playwright: NÃO provável.

### Bloqueios
Sem 403/429/CAPTCHA confirmado; PDFs CDN acessíveis. Alternativa: domínio `concursos.access.org.br` aparece para consulta de local de prova. API/XHR não confirmado.

### Quality gate
ACEITAR concurso/processo seletivo/emprego público. REJEITAR curso de especialização, vestibular e demais seleções acadêmicas.

### Empty evidence
Não vazio. Total exato de `/index/abertos/` não confirmado; manter UNKNOWN para universo.

### Estratégia recomendada
`CONFIGURABLE_HTML` compartilhável ProSeleta + filtro institucional.

### Instruções para Codex
1. Usar `/index/abertos/` e `/index/todos/?busca=1`, sem depender da homepage resumida. 2. Extrair `/informacoes/{id}/`. 3. Parsear datas/status/vagas e categorias de publicações; baixar PDFs CDN. 4. Excluir curso de especialização/vestibular. 5. Testar Navegantes (ID 161), item ativo e item encerrado; validar que Guapimirim/Frontin continuam capturados.

### Confidence
HIGH — páginas, campos, IDs, status e engine reproduzíveis.

### Evidências
https://access.selecao.net.br/; https://access.selecao.net.br/informacoes/161/; https://access.selecao.net.br/index/todos/?busca=1.

## 20 — EXAME Auditores

Identificador técnico: `exame_open`  
URL fornecida: https://concursos.exameconsultores.com.br/index/1/  
URL oficial confirmada: https://concursos.exameconsultores.com.br/ (também há host `exame.selecao.net.br`)  
Portal ativo: SIM.

### Navegação
Estados: Inscrições Abertas, Em andamento, Homologados, Encerrados, Cancelados, Previstos e Suspensos. Detalhe `/informacoes/{id}/`; página fornecida `/index/1/`; paginação `/index/2/?dir=&ord=&pg=2&pp=15&q=` observada; documentos no detalhe.

### Universo observado
Observed: 6 cards em andamento na homepage e 15 por página em homologados; catálogo informa 158 itens em uma captura paginada. Relevant: 6/6 amostrados são seleções de pessoal. Active: 1 com prazo futuro (Santana de Pirapama 12/10–10/11/2026) na captura; demais observados tinham prazos passados. Closed: pelo menos 1 detalhe encerrado (Lagoa Dourada); total por estado UNKNOWN.

### Listagem
ProSeleta: item com tipo, órgão/título, edital, inscrição, vagas e “Mais Informações”; selector exato UNKNOWN; href `/informacoes/{id}/`; status por seção. Busca/paginação usa `dir`, `ord`, `pg`, `pp`, `q` (confirmado por URL).

### Paginação
Server-side, 15 itens por página: `pg=2&pp=15`; navegar “Próxima/Última” e incrementar `pg`, preservando `dir`, `ord`, `q`; parar quando não houver itens.

### Exemplo real
Título: P.M. de Santana de Pirapama — Concurso Público. Órgão: Prefeitura Municipal de Santana de Pirapama/MG. Status: Em andamento; inscrições 12/10/2026–10/11/2026; 79 vagas. URL: https://concursos.exameconsultores.com.br/ (card; href de detalhe não exposto no resultado). Edital: detalhe deve conter publicação Edital nº 01/2026.

### Campos
`titulo`, `orgao`, `modalidade`, `status`, `vagas`, `edital_numero`, `inscricao_inicio`, `inscricao_fim`: HTML; `cargo`, `area`, `cidade`, `uf`, `salario`, `escolaridade`, `taxa`, `prova`, `edital_data`: HTML/PDF; `link_edital`, `link_inscricao`: HTML. Publicações e status confirmados em detalhe; API JSON não confirmada.

### Publicações
Detalhe agrupa Edital, Normas/Legislação, Publicações/Outros Arquivos, Resultados e cronograma; itens incluem mapa estatístico, candidatos, gabaritos, locais, resultados, homologação, portarias. Deduplicar título+data+href. Ruído: login, área restrita e cursos/apostilas.

### API/XHR
Nenhuma API JSON confirmada. Paginação HTML explícita por query string; GET público. Área do candidato requer CPF/senha, não usar para discovery.

### Tecnologia
SERVER_RENDERED, DATATABLES-like pagination (sem prova de DataTables JS), PDF_INDEX, ProSeleta. HTTP funciona: SIM; JS: NÃO aparente; Playwright: NÃO.

### Bloqueios
Sem WAF/CAPTCHA confirmado. `exame.selecao.net.br` é host alternativo oficial. 403/429 não observado.

### Quality gate
ACEITAR concurso/processo seletivo/seleção interna que preencha função/cargo. REJEITAR certificação sem provimento, curso, material de terceiros e cancelados como ativos.

### Empty evidence
Não vazio. `/index/5/` exibiu “Nenhum item cadastrado” para Cancelados; isso é EMPTY_EXPLICIT somente daquela categoria.

### Estratégia recomendada
`CONFIGURABLE_HTML` com paginação query-string; filtro de status por categoria.

### Instruções para Codex
1. Implementar estados e `/index/{estado}/`. 2. Para cada estado, percorrer `pg=1..N`, `pp=15`, mantendo parâmetros. 3. Extrair href `/informacoes/{id}/`; parsear detalhe, cronograma e publicações. 4. Não considerar área do candidato. 5. Testar `pg=2`, detalhe 539 (encerrado) e item futuro de Santana; live retest com `/index/2/?dir=&ord=&pg=2&pp=15&q=`.

### Confidence
HIGH — paginação, estados, detalhe e universo paginado reproduzidos.

### Evidências
https://concursos.exameconsultores.com.br/; https://concursos.exameconsultores.com.br/index/2/?dir=&ord=&pg=2&pp=15&q=; https://concursos.exameconsultores.com.br/informacoes/539/; https://concursos.exameconsultores.com.br/index/5/.

## 21 — EPL Concursos

Identificador técnico: `epl_open`  
URL fornecida/oficial: https://www.eplconcursos.com.br (também responde em https://eplconcursos.com.br)  
Portal ativo: PARCIAL/LEGADO.

### Navegação
Homepage `/index`; estados `/concursos/abertos`, `/concursos/andamento`, `/concursos/finalizados`, além de notícias. O índice atual mostra “Inscrições Abertas” vazio; em andamento lista certames de 2022/2023; finalizados lista histórico.

### Universo observado
Observed: 0 abertos, vários em andamento legados (ex.: Fundação Hospitalar Santa Terezinha, PM Bahia CFS/2023, Santa Cruz de Monte Castelo, Santa Rita, Curitiba). Relevant: itens em andamento são seleção de pessoal; Active: 0 visível em “abertos”, UNKNOWN em “andamento” porque são antigos; Closed: muitos históricos; Out of scope: nenhum, embora “serviços/treinamentos” não sejam certames.

### Listagem
Cards com imagem, órgão e título; selector/container exato UNKNOWN; hrefs não expostos no texto. Índice informa “NENHUM REGISTRO CADASTRADO NESSA SEÇÃO”.

### Paginação
Não observada nas categorias; seguir todos os cards/links. Parâmetros: UNKNOWN.

### Exemplo real
Título: Processo Seletivo Interno para Curso de Formação de Sargentos da Polícia Militar (CFS PM/2023). Órgão: Polícia Militar da Bahia. Status: Em andamento legado; URL: https://eplconcursos.com.br/concursos/andamento. Edital: documentos de concurso no próprio portal/arquivo legado.

### Campos
Cards fornecem `titulo`, `orgao`, `modalidade`, `status`: HTML; demais (`cargo`, `vagas`, `salario`, `escolaridade`, `taxa`, datas, edital) PDF/HTML de detalhe; selectors, API e links de inscrição UNKNOWN.

### Publicações
Seções antigas com editais, recursos, resultados e avisos; PDFs em hosts de arquivo. Deduplicar URL/título; ruído: imagens e serviços/treinamentos.

### API/XHR
Não confirmada. Site atual é HTML legado/MH Informática; host antigo exibe erros PHP e mensagem “Nenhum concurso com inscrição aberta”.

### Tecnologia
STATIC_HTML/SERVER_RENDERED, OTHER legado. HTTP funciona: SIM nas páginas indexadas; JS: NÃO; Playwright: NÃO.

### Bloqueios
Nenhum WAF/CAPTCHA; host antigo expõe warnings PHP, indicando manutenção/legado, não tentar bypass. Alternativa: páginas `/concursos/andamento` e `/finalizados`.

### Quality gate
ACEITAR seleção de pessoal com edital oficial. REJEITAR treinamentos, assessoria, notícias e cursos sem cargo.

### Empty evidence
`EMPTY_EXPLICIT` em Inscrições Abertas: a página diz “NENHUM REGISTRO CADASTRADO NESSA SEÇÃO...”. Não marcar todo o portal vazio: Em andamento/Finalizados possuem cards.

### Estratégia recomendada
`KEEP_EMPTY` para abertos + `CONFIGURABLE_HTML` para histórico; `DEPRECATE_REVIEW_REQUIRED` se objetivo for apenas ativos e não houver atualização.

### Instruções para Codex
1. Manter `/concursos/abertos` como empty explícito. 2. Não usar “andamento” legado como active sem validar datas atuais. 3. Extrair cards de `/concursos/andamento` e detalhes se encontrados. 4. Ignorar host antigo com warnings PHP. 5. Testar empty explícito e um card legado; reportar active UNKNOWN, não zero global.

### Confidence
HIGH para estado vazio/legado; MEDIUM para completude do histórico.

### Evidências
https://www.eplconcursos.com.br/index; https://eplconcursos.com.br/concursos/andamento; https://eplconcursos.com.br/concursos/finalizados; https://antigo-correto.eplconcursos.com.br/controle/arquivos/sistema/controle/arquivos/img/fundoBusca.png.

## 22 — ABCP

Identificador técnico: `abcp_open`  
URL fornecida: https://abcp.selecao.net.br/index/abertos/  
URL oficial confirmada: https://abcp.selecao.net.br/ (homepage redireciona menu “Início” para `abconcursospublicos.org`)  
Portal ativo: SIM.

### Navegação
Estados: `/index/abertos/`, em andamento, homologado, finalizado, suspenso, cancelado; detalhes `/informacoes/{id}/`; publicações e inscrição no detalhe.

### Universo observado
Observed: 10 cards na homepage em andamento; Relevant: 10 (incluem concursos e processos de pessoal); Active: pelo menos 4 com etiqueta de inscrições abertas e datas futuras na captura (Ibiúna, São Roque, Jaborandi, Valinhos); Closed: demais observados com prazos passados; total UNKNOWN.

### Listagem
ProSeleta: tipo, título, edital, período, etiqueta de inscrição, quantidade de vagas e “Mais Informações”; selector exato UNKNOWN; href `/informacoes/{id}/` e ID numérico.

### Paginação
Estados separados; paginação de cada estado não confirmada. Seguir todos links e “próxima/última” se presente.

### Exemplo real
Título: Processo Seletivo Simplificado 002/2026 — Prefeitura de Ibiúna/SP. Órgão: Prefeitura da Estância Turística de Ibiúna/SP. Status: Em andamento/inscrições abertas 25/08–08/09/2026, 33 vagas. URL: https://abcp.selecao.net.br/informacoes/2867/. Edital: “EDITAL DE ABERTURA” PDF CDN.

### Campos
`titulo`, `orgao`, `modalidade`, `inscricao_inicio`, `inscricao_fim`, `status`, `edital_numero`, `edital_data`, `link_edital`, `link_inscricao`: HTML; `cargo`, `escolaridade`, `salario`, `taxa`, `vagas`: HTML no detalhe; `area`, `cidade`, `uf`, `prova`: PDF/HTML. API JSON/XHR UNKNOWN.

### Publicações
Detalhe tem Edital e demais documentos, links CDN; em páginas maiores haverá resultados/gabaritos/retificações. Deduplicar por URL/título/data; ruído login/cookies/breadcrumb.

### API/XHR
Não confirmado; ProSeleta no footer; GET HTML/PDF público.

### Tecnologia
SERVER_RENDERED, PDF_INDEX, OTHER (ProSeleta). HTTP SIM; JS NÃO aparente; Playwright NÃO provável.

### Bloqueios
Sem WAF/CAPTCHA; menu “Início” aponta para domínio institucional `abconcursospublicos.org`, mas o catálogo `/abcp.selecao.net.br` é a origem operacional. API alternativa não confirmada.

### Quality gate
ACEITAR concurso, processo seletivo simplificado/público e emprego/cargo. REJEITAR apenas vestibular/curso ou cancelado/suspenso como ativo.

### Empty evidence
Não vazio; total de abertos UNKNOWN.

### Estratégia recomendada
`CONFIGURABLE_HTML` ProSeleta compartilhado com ACCESS/OMNI/EXAME/OBJETIVA/COTEC.

### Instruções para Codex
1. Percorrer os estados, coletar `/informacoes/{id}/`. 2. Extrair tipo, edital, datas, status, tabela de vagas e publicações CDN. 3. Manter `abconcursospublicos.org` apenas como link institucional, não como origem de dados sem validação. 4. Testar ID 2867, itens abertos e finalizados.

### Confidence
HIGH.

### Evidências
https://abcp.selecao.net.br/; https://abcp.selecao.net.br/informacoes/2867/.

## 23 — UNIFIL

Identificador técnico: `unifil_open`  
URL fornecida: https://main.institutounifil.com.br  
URL oficial confirmada: https://main.institutounifil.com.br/concurso/{id} e https://unifil.br/editais-regulamentos/editais/  
Portal ativo: SIM; portal próprio com vários certames 2026.

### Navegação
Detalhe por ID `/concurso/180`, `/181` etc.; área restrita, consulta de inscrição e downloads de editais no detalhe; página institucional e regulamentos em `unifil.br`.

### Universo observado
Observed: pelo menos 13 páginas de concursos 2026 indexadas (IDs 173, 180, 182, 186–191, 193–195); Relevant: pelo menos 12 (municípios/emprego público/PSS); Active: UNKNOWN por falta de cronograma/status textual na página de detalhe; Closed: UNKNOWN; Out of scope: ID 195 “Concurso Oportunidade”/bolsa acadêmica deve ser excluído.

### Listagem
Não foi encontrada listagem global; cada detalhe usa `/concurso/{id}` com título “Município de ...”, links de área do candidato/consulta de inscrição e imagens numeradas de documentos. Selector/container/atributos: UNKNOWN; ID é numérico no path.

### Paginação
Não confirmada. Discovery precisa de índice/sitemap ou IDs encontrados nos links; não enumerar IDs cegamente em produção.

### Exemplo real
Título: PSS 001/2026 — Município de Sarandi. Órgão: Município de Sarandi/PR. Status: processo seletivo (página com edital, retificação, deferimento, homologação, classificação e homologação final). URL: https://main.institutounifil.com.br/concurso/182. Edital: “Edital de Abertura – Processo Seletivo” (imagem/link de download).

### Campos
`titulo`, `orgao`, `modalidade`, `cargo`, `vagas`, `edital`, `publicações`, `link_edital`: HTML + links/imagens; `status`, datas de inscrição/prova, salário, escolaridade, taxa, cidade/UF, área: PDF/UNKNOWN conforme edital; `link_inscricao`: HTML; API/XHR não confirmada.

### Publicações
Imagens/documentos enumerados (“Image106”, “Image111”, etc.) com edital, retificações, isenção, inscrições, gabaritos, resultados, classificação e homologação; links de S3/arquivos podem ser revelados no HTML. Deduplicar por href e rótulo; excluir concurso de bolsa/vestibular.

### API/XHR
Nenhuma API pública confirmada. Detalhes e downloads são GET; área restrita exige credenciais.

### Tecnologia
SERVER_RENDERED, PDF_INDEX, OTHER (portal próprio). HTTP funciona: PARCIAL (pesquisa web indexa detalhes; host raiz retornou 403); JS: UNKNOWN; Playwright: possível se downloads forem montados por JS.

### Bloqueios
Host raiz `main...` retornou 403 na pesquisa, mas páginas `/concurso/{id}` foram indexadas; sem CAPTCHA confirmado. Alternativa: `institutounifil.com.br` institucional e páginas de órgãos com links da banca. API: não confirmada.

### Quality gate
ACEITAR concurso público, emprego público e PSS para cargos. REJEITAR “Concurso Oportunidade”/bolsas, vestibular e processos acadêmicos.

### Empty evidence
Não vazio; ausência de listagem global é `UNKNOWN_EMPTY`, não zero.

### Estratégia recomendada
`DEDICATED_CONNECTOR`/`HYBRID` (discovery por links/índice + detalhe `/concurso/{id}` + PDFs); `KEEP_BLOCKED` para host raiz 403 se persistir.

### Instruções para Codex
1. Descobrir IDs por sitemap/homepage e links de prefeituras, sem varredura ilimitada. 2. GET cada `/concurso/{id}`. 3. Extrair links/imagens de edital e publicações; baixar PDFs. 4. Parsear cargos/datas no PDF. 5. Excluir ID 195 e termos de bolsa/vestibular. 6. Testar 180/182/191 e um processo encerrado; validar 403 do host raiz.

### Confidence
MEDIUM — muitos detalhes reais e padrão estável, mas ausência de índice/paginação e host raiz 403 dificultam contagem.

### Evidências
https://main.institutounifil.com.br/concurso/180; https://main.institutounifil.com.br/concurso/182; https://main.institutounifil.com.br/concurso/191; https://main.institutounifil.com.br/concurso/195; https://unifil.br/editais-regulamentos/editais/.

## 24 — OBJETIVA Concursos

Identificador técnico: `objetiva_open`  
URL fornecida: https://concursos.objetivas.com.br  
URL oficial confirmada: https://concursos.objetivas.com.br/ (menu institucional aponta `www.objetivas.com.br`)  
Portal ativo: SIM.

### Navegação
Estados Inscrições Abertas, Em andamento, Finalizado; detalhes `/informacoes/{id}/`; PDFs CDN; homepage operacional no host `concursos.objetivas.com.br`.

### Universo observado
Observed: 12 cards visíveis em andamento, incluindo concurso e PSS; Relevant: 12; Active: pelo menos 5 com inscrições futuras na captura (Guaporé, Estrela, Cachoeira do Sul, Conceição do Almeida CP/PSP); Closed: demais observados tinham prazo passado ou suspensão. Total UNKNOWN.

### Listagem
ProSeleta: tipo, título em caixa alta, órgão/município, datas, etiqueta de inscrição, vagas quando presentes e “Mais Informações”; selector exato UNKNOWN; href `/informacoes/{id}/` e ID numérico.

### Paginação
Não confirmada na homepage; estados e eventuais links “mais”. Percorrer todos hrefs e páginas se presentes.

### Exemplo real
Título: Conceição do Almeida/BA — Município — Concurso Público 01/2026. Órgão: Município de Conceição do Almeida/BA. Status: Em andamento; inscrições 10/08–10/09/2026. URL: https://concursos.objetivas.com.br/informacoes/2602/. Edital: “Edital nº 01/2026 – Edital de Abertura das Inscrições” CDN.

### Campos
`titulo`, `orgao`, `modalidade`, `inscricao_inicio`, `inscricao_fim`, `status`, `edital_numero`, `link_edital`, `link_inscricao`: HTML; `cargo`, `vagas`, `escolaridade`, `taxa`: HTML no detalhe; `salario`, `prova`, `edital_data`, `area`, `cidade`, `uf`: PDF/HTML; API/XHR UNKNOWN.

### Publicações
Publicações no detalhe com edital, isenção, retificações, resultados, gabaritos e cronograma; PDFs `anexos-r2.selecao.net.br`. Deduplicar href+título/data; ruído login/cookies.

### API/XHR
Não confirmada; ProSeleta no footer; GET HTML/PDF público.

### Tecnologia
SERVER_RENDERED, PDF_INDEX, OTHER (ProSeleta). HTTP SIM; JS NÃO aparente; Playwright NÃO.

### Bloqueios
Sem WAF/CAPTCHA confirmado. Host institucional `www.objetivas.com.br` é alternativa de contato, não substituir catálogo.

### Quality gate
ACEITAR concurso, processo seletivo público/emprego e cargos. REJEITAR item suspenso/cancelado como ativo e conteúdo não laboral.

### Empty evidence
Não vazio; total UNKNOWN.

### Estratégia recomendada
`CONFIGURABLE_HTML` ProSeleta compartilhado.

### Instruções para Codex
1. Usar catálogo no host `concursos.objetivas.com.br`. 2. Seguir estados e hrefs `/informacoes/{id}/`. 3. Parsear detalhe e PDFs CDN. 4. Tratar CP e PSP do mesmo município como certames distintos quando IDs/títulos diferirem. 5. Testar IDs 2602, 2606, 2617; suspenso Arvorezinha não pode ser active.

### Confidence
HIGH.

### Evidências
https://concursos.objetivas.com.br/; https://concursos.objetivas.com.br/informacoes/2602/; https://concursos.objetivas.com.br/informacoes/2606/; https://concursos.objetivas.com.br/informacoes/2617/.

## 25 — Leandro Ferreira Consultoria

Identificador técnico: `leandroferreira_open`  
URL fornecida: https://www.leandroferreira.com.br  
URL oficial confirmada: https://www.leandroferreira.mg.gov.br/ (Prefeitura de Leandro Ferreira; a URL fornecida não resolveu na pesquisa).  
Portal ativo: PARCIAL; a fonte parece ter sido cadastrada como consultoria, mas os processos reais estão no portal oficial municipal.

### Navegação
Homepage municipal; “Concursos Públicos e Processos Seletivos”/“Certames Públicos”; notícias/detalhes `/documento/...` ou `/noticia/...`; PDFs em `sistema.leandroferreira.mg.gov.br/UpFiles/...`; Transparência também possui “Concursos Públicos” e “Processos Seletivos”.

### Universo observado
Observed: homepage lista pelo menos 10 publicações de concursos/processos em 2026; Relevant: pelo menos 7 de pessoal (PSS 001–005/2026 e seleção de diretores); Active: pelo menos 1 publicação recente PSS 005/2026, mas status do certame não exposto; Closed: homologações 001/002; Out of scope: chamamento cultural PNAB e licitações.

### Listagem
Portal municipal usa feed de notícias, título/data e link “ver concurso/processo”; selector exato UNKNOWN. Detalhe contém título, texto integral e tabela de arquivos para download; links de PDF no host `sistema...`.

### Paginação
Homepage tem “veja todos os concursos/processos”; parâmetros não confirmados. Seguir o link e todas as páginas do feed.

### Exemplo real
Título: Edital de Processo Seletivo Simplificado nº 005/2026. Órgão: Município de Leandro Ferreira/MG (Saúde/Educação). Status: seleção para contratação temporária e cadastro de reserva; publicação 09/07/2026. URL: https://www.leandroferreira.mg.gov.br/documento/edital-de-processo-seletivo-simplificado-n-005-2026-663. Edital: “Edital Nº 05/2026” em PDF.

### Campos
`titulo`, `orgao`, `modalidade`, `status` (quando no texto), `edital_numero`, `edital_data`, `link_edital`, publicações: HTML; `cargo`, `vagas`, `salario`, `escolaridade`, `taxa`, `prova`, `inscricao_inicio`, `inscricao_fim`, `cidade`, `uf`, `area`: PDF/HTML do edital; `link_inscricao`: PDF/UNKNOWN.

### Publicações
Detalhe lista classificação preliminar, edital, classificação final/extrato de notas e termo de homologação; outros PSS têm portaria/edital/classificação. Deduplicar por href/título/data. Ruído: PNAB cultural, licitações, diário oficial, menu e transparência.

### API/XHR
Não confirmada. Site municipal parece server-rendered/DEC Soluções Digitais; PDFs em sistema separado. Links Flowdocs são transparência e não seleção.

### Tecnologia
SERVER_RENDERED, PDF_INDEX, OTHER (site municipal DEC). HTTP funciona: SIM na pesquisa; página informa “Não há suporte ao JavaScript” e ainda entrega conteúdo; Playwright NÃO provável.

### Bloqueios
URL fornecida não resolveu (host `www.leandroferreira.com.br`); portal oficial municipal e `sistema...` acessíveis/indexados. WAF/CAPTCHA não confirmado. Alternativa oficial SIM.

### Quality gate
ACEITAR PSS, concurso e seleção de diretores/cargos com contratação. REJEITAR chamamento cultural PNAB, licitações, credenciamentos e incentivo ao atleta.

### Empty evidence
`UNKNOWN_EMPTY` para URL fornecida; não declarar vazio porque domínio não resolveu. Portal municipal contém itens.

### Estratégia recomendada
`DEPRECATE_REVIEW_REQUIRED` para a URL fornecida + `DEDICATED_CONNECTOR` para portal municipal oficial, com filtro de categorias.

### Instruções para Codex
1. Validar se `leandroferreira.com.br` é domínio da consultoria; não seguir como fonte municipal sem confirmação. 2. Configurar `https://www.leandroferreira.mg.gov.br/` e a área “Concursos Públicos e Processos Seletivos”. 3. Extrair links “ver concurso/processo” e PDFs. 4. Filtrar PNAB/licitações. 5. Testar documento 663 e PSS 001/2026; preservar UNKNOWN para inscrições não publicadas.

### Confidence
MEDIUM — migração/identidade da URL fornecida não confirmada, mas portal municipal e exemplo oficial são fortes.

### Evidências
https://www.leandroferreira.mg.gov.br/; https://www.leandroferreira.mg.gov.br/documento/edital-de-processo-seletivo-simplificado-n-005-2026-663; https://www.leandroferreira.mg.gov.br/mapa-do-site; https://sistema.leandroferreira.mg.gov.br/.

## 26 — COTEC / FADENOR

Identificador técnico: `cotec_open`  
URL fornecida: https://www.cotec.fadenor.com.br/index/abertos/  
URL oficial confirmada: https://cotec-fadenor.selecao.net.br/index/abertos/; domínio fornecido também responde e apresenta o mesmo catálogo ProSeleta.  
Portal ativo: SIM; processos anteriores: https://anteriores.cotec.fadenor.com.br/.

### Navegação
Estados `/index/abertos/`, `/index/1/` (em andamento), `/index/3/` (finalizado), homologado/cancelado; detalhes `/informacoes/{id}/`; anteriores em host separado; publicações e PDFs CDN.

### Universo observado
Observed: 3 cards em inscrições abertas (Ponto Chique, Proficiência em Línguas Estrangeiras, Nova Porteirinha) e muitos em andamento/anteriores; Relevant: 2 de pessoal entre os 3 abertos (Ponto Chique e Nova Porteirinha); Active: 2 com inscrições abertas; Proficiência é seleção acadêmica e out of scope; Closed: vários em `/index/3/`; total UNKNOWN.

### Listagem
ProSeleta: tipo, título/órgão, edital, datas, etiqueta “Inscrições Abertas!”, isenção, vagas e “Mais Informações”; selector CSS exato UNKNOWN; href `/informacoes/{id}/`; ID numérico. `/index/1/` lista em andamento.

### Paginação
Estados usam páginas numéricas (`/index/1/`, `/index/3/`); não assumir que “1” é página e não estado sem validar links. Percorrer todos os hrefs de estados e eventual próxima/última.

### Exemplo real
Título: Concurso Público — Prefeitura Municipal de Ponto Chique/MG, Edital 01/2026. Órgão: Prefeitura Municipal de Ponto Chique/MG. Status: Em andamento/inscrições 23/07–18/09/2026, 63 vagas. URL: https://cotec-fadenor.selecao.net.br/informacoes/28/. Edital: “Edital (Conforme 2ª Retificação)” PDF CDN.

### Campos
`titulo`, `orgao`, `modalidade`, `inscricao_inicio`, `inscricao_fim`, `status`, `edital_numero`, `edital_data`, `link_edital`, `link_inscricao`: HTML; `cargo`, `vagas`, `salario`, `escolaridade`, `taxa`, `prova`, `area`, `cidade`, `uf`: HTML/PDF (Ponto Chique mostra tabela de vagas HTML); publicações: HTML href CDN; API/XHR UNKNOWN.

### Publicações
Categorias Edital, Anexos, Resultados, Gabaritos/Cadernos, Recursos, Comunicados; detalhe `/informacoes/28/` mostra retificações, anexos e resultado de isenção. Host de anteriores tem arquivos por processo e endpoint visual; deduplicar por href+título/data. Ruído: proficiência linguística, login/cookies.

### API/XHR
Nenhuma API JSON confirmada; ProSeleta no footer. GET HTML/PDF público. `anteriores.cotec...` é catálogo separado de processos históricos.

### Tecnologia
SERVER_RENDERED, PDF_INDEX, OTHER (ProSeleta), plataforma `selecao.net.br`. HTTP SIM; JS NÃO aparente; Playwright NÃO.

### Bloqueios
Sem WAF/CAPTCHA confirmado. Domínio fornecido e `cotec-fadenor.selecao.net.br` apresentam o mesmo padrão; usar o segundo como URL atual confirmada. API alternativa não confirmada.

### Quality gate
ACEITAR concurso/PS para cargos/contratação (Ponto Chique/Nova Porteirinha). REJEITAR Proficiência em Línguas Estrangeiras, vestibular e seleção acadêmica; não contar anteriores como ativos.

### Empty evidence
Não vazio; `/index/3/` mostra finalizados. Proficiência é OUT_OF_SCOPE, não empty.

### Estratégia recomendada
`CONFIGURABLE_HTML` ProSeleta compartilhado + `INSTITUTIONAL_FILTER_REQUIRED`; histórico via host anteriores somente quando necessário.

### Instruções para Codex
1. Usar `cotec-fadenor.selecao.net.br/index/abertos/` como catálogo. 2. Seguir estados e `/informacoes/{id}/`; tratar `/index/1/` como “Em andamento” conforme links do menu. 3. Parsear tabela de vagas e publicações CDN. 4. Excluir Proficiência linguística. 5. Manter `anteriores...` como histórico separado. 6. Testar ID 28 (ativo), Ponto Chique, Nova Porteirinha e finalizado; live retest nos dois domínios.

### Confidence
HIGH para engine/estrutura e exemplos; MEDIUM para total/paginação.

### Evidências
https://cotec-fadenor.selecao.net.br/index/abertos/; https://cotec-fadenor.selecao.net.br/informacoes/28/; https://www.cotec.fadenor.com.br/index/abertos/; https://anteriores.cotec.fadenor.com.br/; https://cotec-fadenor.selecao.net.br/index/3/.

## Shared Platform Opportunities (BATCH 02)

| Plataforma | Fontes | Estrutura comum | API comum? | Pode compartilhar conector? |
|---|---|---|---|---|
| ProSeleta / `selecao.net.br` | ACCESS, ABCP, OMNI (novo e portal), EXAME, OBJETIVA, COTEC; FUNDEP usa o mesmo padrão no host `fundep.selecao.net.br` | Estados `/index/...`, detalhe `/informacoes/{id}/`, “Informações Gerais”, “Publicações”, tabela de vagas, CDN `anexos*.selecao.net.br`, footer ProSeleta | API JSON não confirmada; HTML estável comum | SIM; criar parser configurável por tenant e filtros de estados |
| IBGP próprio | IBGP | JSP/índice e `concurso.jsp?cod=`, documentos `/rest/concurso/download/edital/...` | REST de download confirmado; catálogo UNKNOWN | Parcial; conector dedicado para discovery/PDF |
| SharePoint/PDF | FUMARC | `Documentos Compartilhados`, `Forms/AllItems.aspx`, pastas por órgão, PDFs | `_api` não confirmado | Possível conector SharePoint após validação do tenant |
| Portal próprio | UNIFIL | `/concurso/{id}`, imagens/documentos numerados, área restrita | Não confirmada | Conector dedicado |
| Site municipal | Leandro Ferreira | Feed de notícias, `/documento/...`, PDFs em `sistema...` | Não confirmada | Conector municipal/configurável, não ProSeleta |

## Casos para revisão do Sol

1. IBGP: página de inscrições abertas vazia, mas PDFs REST recentes e páginas de concursos existem; confirmar discovery/API e evitar falso empty.  
2. OMNI: portal fornecido e `institutoomni.selecao.net.br` estão ativos, com universos diferentes; decidir alias/dupla origem.  
3. Leandro Ferreira: URL fornecida não resolve; validar depreciação e adoção do portal municipal oficial.  
4. FUMARC: SharePoint sem índice global e `_api` não confirmada; decidir conector/fallback PDF.  
5. UNIFIL: host raiz 403 e ausência de índice; decidir estratégia de discovery sem enumeração cega de IDs.

