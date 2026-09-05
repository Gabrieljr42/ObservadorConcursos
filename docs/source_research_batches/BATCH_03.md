# Observador de Concursos — BATCH 03 (fontes 27–39)

Pesquisa externa realizada em 30/08/2026. Foram acessadas as páginas oficiais indexadas/visíveis; quando a página não expôs o HTML completo, o campo permanece UNKNOWN. Contagens são somente do conteúdo que a página declarou/mostrou e não são expectativas do crawler.

## 27 — Instituto Águia

Identificador técnico: `aguia_open`  
URL fornecida: https://portal.institutoaguia.org.br/edital  
URL oficial confirmada: https://portal.institutoaguia.org.br/edital/index/abertos  
Portal ativo: SIM  
URL mudou: NÃO (a rota fornecida é uma raiz válida; a listagem operacional é `/edital/index/abertos`).

### Navegação
Homepage: https://portal.institutoaguia.org.br/  
Abertos: `/edital/index/abertos` (seção “Em inscrição”)  
Em andamento: a mesma página, seção “Em andamento”  
Encerrados: a mesma página, seção “Finalizados”  
Detalhe: `/edital/ver/{id}` (exemplos `/edital/ver/43`, `/edital/ver/40`, `/edital/ver/42`)  
Documentos: links “DOWNLOAD” dentro do detalhe, normalmente PDF; URL final deve ser extraída do `href`.

### Universo observado
Observed: 8 cards visíveis no resultado indexado (4 em andamento e 4 finalizados; a página pode conter mais itens).  
Relevant: os cards são “Concurso Público” ou “Processo Seletivo”; os textos institucionais também citam vestibular/recrutamento, que devem ser excluídos se aparecerem. Número total: UNKNOWN.  
Active: 4 itens na seção “Em andamento”; a seção “Em inscrição” apareceu sem cards na captura.  
Closed: pelo menos 2 itens visíveis em “Finalizados”; total UNKNOWN.  
Out of scope: vestibulares, avaliações de desempenho e recrutamentos sem seleção de pessoal.

### Listagem
Estrutura: HTML server-rendered, cards com imagem/logotipo, tipo (“Concurso Público”/“Processo Seletivo”), órgão, número/ano e link “Mais detalhes”.  
Selector/container: UNKNOWN (não inventar CSS; localizar links cuja URL contenha `/edital/ver/` e subir ao card).  
Título: texto do card e título no detalhe (HTML).  
Link/ID: link de detalhe `/edital/ver/{id}`; o número é um ID numérico observável na URL.  
Status: agrupamento textual “Em inscrição”, “Em andamento”, “Finalizados”, “Futuros”, “Suspensos” (HTML).

### Paginação
Método: não evidenciada na página indexada; a captura mostra listas por status e não informa paginação.  
Parâmetros: UNKNOWN; seguir todos os links de status e todos os links de detalhe encontrados, sem assumir limite.

### Exemplo real
Título: Concurso Público 01/2025 — Câmara Municipal de Aguaí  
Órgão: Câmara Municipal de Aguaí  
Status: detalhe finalizado (inscrições 09/07/2025–31/07/2025)  
URL: https://portal.institutoaguia.org.br/edital/ver/42  
Edital: “EDITAL DE ABERTURA”, documento PDF no detalhe.

### Campos

| Campo | Fonte/evidência |
|---|---|
| titulo, orgao, modalidade, status, cidade, UF | HTML no card/detalhe; modalidade aparece como “Concurso Público” ou “Processo Seletivo”; cidade/UF aparecem no detalhe quando presentes |
| cargo, salario_min/max | HTML no detalhe; exemplo `/ver/42` mostra “Controlador Interno” e remuneração 4.922,39 |
| vagas, escolaridade, taxa, prova_data, edital_numero/data, inscrição_inicio/fim | PDF/HTML de detalhe; não todos presentes no card, parser deve aceitar UNKNOWN |
| link_edital, link_inscricao | HTML `href` dos links “DOWNLOAD”/“Inscreva-se”; extrair, não montar |

### Publicações
Estrutura: lista cronológica no detalhe com data, título (“EDITAL…”, “RETIFICAÇÃO”, “GABARITO”, “CONVOCAÇÃO”, “RESULTADO”, “HOMOLOGAÇÃO”) e “DOWNLOAD”.  
Selector/API: UNKNOWN; usar âncoras do bloco de publicações e validar `href` PDF.  
Deduplicação sugerida: chave `(detalhe_id, href_normalizado, data, título)`; há títulos duplicados (ex.: duas retificações idênticas em `/ver/43`).  
Ruídos: menus, logo, “Sobre a empresa”, contato, área do candidato e links de acessibilidade.

### API/XHR
Endpoint/método/parâmetros/paginação/JSON path: UNKNOWN. A página indexada entrega conteúdo sem evidência de endpoint público; não afirmar API.  
Autenticação: não necessária para listagem/detalhes públicos; área do candidato é separada.

### Tecnologia
Tipo: SERVER_RENDERED / OTHER (framework não identificado).  
HTTP funciona: PARCIAL (página é indexada como HTML; teste HTTP direto no ambiente de pesquisa retornou bloqueio de rede, portanto não é prova de 403 do site).  
JS necessário: UNKNOWN.  
Playwright necessário: NÃO demonstrado para listagem; manter fallback se HTML recebido sem cards.

### Bloqueios
HTTP: tentativa local não permitida pelo ambiente; status real UNKNOWN.  
Browser/WAF/CAPTCHA: nenhuma evidência reproduzível de Cloudflare/CAPTCHA na página indexada.  
Alternativa: usar rota oficial `/edital/index/abertos` e detalhes indexados.

### Quality gate
ACEITAR: card/detalhe com “Concurso Público” ou “Processo Seletivo” e órgão/cargo/documento.  
REJEITAR: vestibular, avaliação de desempenho, recrutamento genérico e conteúdo da área do candidato.

### Empty evidence
UNKNOWN_EMPTY: “Em inscrição” aparece sem cards na captura, mas “Em andamento” possui cards; não declarar fonte vazia.

### Estratégia recomendada
`CONFIGURABLE_HTML` com fallback `HTTP_HTML`; seguir `/edital/index/abertos` e `/edital/ver/{id}`; não depender somente de “Em inscrição”.

### Instruções para Codex
1. Buscar links de detalhe `/edital/ver/{id}` na página de abertos e nas demais seções de status. 2. No detalhe, capturar órgão, título, tipo, localização, período de inscrição, cargos/remuneração e todos os links “DOWNLOAD”. 3. Classificar publicações por título e data, deduplicando hrefs repetidos. 4. Testar `/ver/42` e `/ver/43` como fixtures, inclusive duplicata de retificação e PDF de abertura.

### Confidence
MEDIUM — estrutura, rotas e exemplos são reproduzíveis, mas CSS/API e contagem total não foram expostos.

### Evidências
https://portal.institutoaguia.org.br/; https://portal.institutoaguia.org.br/edital/index/abertos; https://portal.institutoaguia.org.br/edital/ver/42; https://portal.institutoaguia.org.br/edital/ver/43

## 28 — IUDS

Identificador técnico: `iuds_open`  
URL fornecida: https://www.iuds.org.br  
URL oficial confirmada: domínio institucional continua citado como `www.iuds.org.br`; portal operacional histórico confirmado em https://portal.iuds.org.br/  
Portal ativo: PARCIAL  
URL mudou: SIM/PARCIAL — editais indexados usam `portal.iuds.org.br` e CDN `cdn.iuds.org.br`; a página pública atual não retornou listagem verificável.

### Navegação
Homepage: https://www.iuds.org.br/ (conteúdo atual não reproduzido)  
Abertos/em andamento: rota histórica `/edital/index/andamento` (citada por Prefeitura de Águas de Lindóia) e `/edital/index/abertos` (não confirmada como atual).  
Encerrados: `/edital/ver/{id}` para detalhes históricos.  
Detalhe: https://portal.iuds.org.br/edital/ver/77  
Documentos: PDFs em `cdn.iuds.org.br/edital/...` ou links nos detalhes.

### Universo observado
Observed: não determinável no portal atual; página de detalhe 77 (Barra Bonita 001/2022) é observável.  
Relevant: concursos públicos/processos seletivos para cargos, conforme editais oficiais.  
Active: UNKNOWN; pesquisa reproduzível encontrou “nenhum concurso aberto… em andamento” em índice secundário, não usar como prova de vazio.  
Closed: pelo menos Barra Bonita 001/2022 e históricos Mogi Guaçu, CREFITO-2 etc.  
Out of scope: parcerias/consultoria sem seleção.

### Listagem
Estrutura observada no detalhe histórico: HTML com órgão, tipo/número, período de inscrição, cidade/UF, bloco de cargos por escolaridade e lista cronológica de documentos com “DOWNLOAD”.  
Selector/container: UNKNOWN.  
Título/link/ID: detalhe `/edital/ver/{id}`, ID numérico.  
Status: rota de listagem histórica e texto do detalhe; não confiar no índice atual sem validação.

### Paginação
Método/parâmetros: UNKNOWN; a rota de listagem histórica deve ser descoberta em browser/HTML antes de implementar.

### Exemplo real
Título: Concurso Público 001/2022 — Prefeitura da Estância Turística de Barra Bonita  
Órgão: Prefeitura da Estância Turística de Barra Bonita/SP  
Status: encerrado (inscrições 15/10/2022–27/11/2022)  
URL: https://portal.iuds.org.br/edital/ver/77  
Edital: PDF de abertura em `cdn.iuds.org.br`.

### Campos

| Campo | Fonte |
|---|---|
| titulo, orgao, modalidade, cidade, UF, status, cargo | HTML do detalhe histórico e PDF de abertura |
| vagas, salário, escolaridade, prova, taxa, edital_numero/data, inscrições | PDF de abertura; o detalhe mostra período e cargos, mas não garante todos os campos |
| links de edital/publicações | HTML “DOWNLOAD” → CDN PDF |
| link_inscricao | HTML/área do candidato; UNKNOWN em certames encerrados |

### Publicações
Detalhes listam abertura, retificações, listas de inscritos, gabaritos e resultados com data e download. Deduplicar por URL/hash; PDFs podem ser a única fonte de dados. Ruído: área do candidato, login, rodapé institucional.

### API/XHR
Endpoint, método, JSON path, paginação e autenticação: UNKNOWN. CDN é armazenamento de PDF, não API de listagem. Não inventar `/api`.

### Tecnologia
Tipo: SERVER_RENDERED + PDF_INDEX; HTTP/JS: UNKNOWN (indexação demonstra HTML histórico, mas acesso atual não foi validado); Playwright: provavelmente necessário para localizar listagem atual se conteúdo for dinâmico.

### Bloqueios
O ambiente não permitiu teste HTTP direto; WAF/CAPTCHA/status real UNKNOWN. Existe alternativa oficial: `portal.iuds.org.br` e CDN. Não fazer bypass.

### Quality gate
ACEITAR somente concursos/processos seletivos de pessoal com órgão/cargo/edital. REJEITAR cursos, consultoria, doações e materiais sem seleção.

### Empty evidence
`UNKNOWN_EMPTY`: nenhuma listagem atual confirmada; não converter em EMPTY_EXPLICIT.

### Estratégia recomendada
`DEPRECATE_REVIEW_REQUIRED` + `KEEP_EMPTY` somente até validação; depois `PLAYWRIGHT`/`HYBRID` se o portal voltar a expor listagem. Usar PDFs CDN como documentos, nunca como evidência de ativos sem status atual.

### Instruções para Codex
1. Fazer health-check de `www.iuds.org.br`, `portal.iuds.org.br` e `/edital/index/andamento`. 2. Se houver cards, extrair href `/edital/ver/{id}`; se não houver, registrar blocked/unknown. 3. No detalhe, seguir todos os downloads e guardar CDN URL. 4. Fixture histórico: `/edital/ver/77`; testar que encerrado não vira ativo. 5. Não marcar vazio nem remover fonte sem nova validação.

### Confidence
LOW — portal atual não forneceu listagem reproduzível; rotas e detalhe histórico são confirmados.

### Evidências
https://portal.iuds.org.br/edital/ver/77; https://cdn.iuds.org.br/edital/1/77/ed36da0a042da04cd321e4e7d2d94500.pdf; https://www.aguasdelindoia.sp.gov.br/noticia/print-noticia/2150/prefeitura-publica-edital-de-convocacao-para-provas-para-processo-seletivo/

## 29 — Reis & Reis

Identificador técnico: `reisesreis_open`  
URL fornecida/confirmada: https://novo.reisauditores.com.br/concursos-em-andamento  
Portal ativo: PARCIAL  
URL mudou: SIM — o domínio `novo.reisauditores.com.br` é o atual portal; a própria página exibe o menu e a área do candidato em `reis.candidato.gestaoselecoes.com.br`.

### Navegação
Homepage: https://novo.reisauditores.com.br/  
Em andamento: `/concursos-em-andamento`  
Encerrados: `/concursos-concluidos` (link no menu; href deve ser extraído)  
Detalhe: UNKNOWN no HTML inicial; página mostra “Carregando concursos…”.  
Documentos: UNKNOWN.

### Universo observado
Observed/Relevant/Active/Closed: UNKNOWN — nenhuma unidade foi renderizada no HTML capturado.  
Out of scope: serviços de auditoria/contabilidade e área de candidato.

### Listagem e paginação
Container, título, link, ID, status e paginação: UNKNOWN; HTML inicial tem apenas marcador “Carregando concursos…”. Requer observação de XHR/browser.

### Exemplo real
Não foi possível obter exemplo atual. Exemplo histórico reproduzível: Processo Seletivo e Eletivo de Conselheiros Tutelares, detalhe legado https://www.reisauditores.com.br/concurso/20/detalhes (2019, encerrado).

### Campos
Todos os campos de item atual: UNKNOWN. No detalhe legado, títulos/publicações e datas são HTML; cargos/vagas/salários dependem do edital PDF.

### Publicações
UNKNOWN para o portal novo. A página de detalhe legado possui linha do tempo de editais, erratas, gabarito e resultados; deduplicar por URL/data/título.

### API/XHR
Endpoint, método, parâmetros e JSON path: UNKNOWN; “Carregando concursos…” é forte indicação de chamada XHR/JS. Inspecionar Network (fetch/XHR) com browser e reproduzir endpoint público, se existir. Não inventar endpoint.

### Tecnologia
REACT_SPA ou outro frontend dinâmico: UNKNOWN (JS necessário: SIM para conteúdo observado; Playwright: SIM/alternativa de descobrir XHR). HTTP simples só obtém shell.

### Bloqueios
Sem evidência de WAF/CAPTCHA; shell HTML acessível por indexação. API alternativa: UNKNOWN.

### Quality gate
Aceitar somente cards retornados pelo frontend com concurso/processo seletivo e órgão; rejeitar serviços institucionais e área autenticada.

### Empty evidence
`UNKNOWN_EMPTY`, não `EMPTY_EXPLICIT`: “Carregando concursos…” não significa lista vazia.

### Estratégia recomendada
`HYBRID` (descobrir XHR; Playwright como fallback), `DEPRECATE_REVIEW_REQUIRED` apenas se a API antiga estiver definitivamente indisponível.

### Instruções para Codex
1. Abrir a rota com browser e registrar requests fetch/XHR disparados após carregamento. 2. Repetir a chamada sem browser se pública; documentar JSON path e paginação. 3. Se não houver API, usar Playwright e aguardar o container de concursos. 4. Criar teste de “shell Carregando…” para impedir falso vazio. 5. Validar detalhe legado `/concurso/20/detalhes` apenas como fixture histórica.

### Confidence
LOW — shell dinâmico reproduzível, mas endpoint/lista atual não expostos.

### Evidências
https://novo.reisauditores.com.br/concursos-em-andamento; https://novo.reisauditores.com.br/; https://www.reisauditores.com.br/concurso/20/detalhes

## 30 — MS Concursos

Identificador técnico: `msconcursos_open`  
URL fornecida/confirmada: https://www.msconcursos.com.br (redireciona/é apresentado também como https://msconcursos.com.br/)  
Portal ativo: SIM  
URL mudou: PARCIAL — versão sem `www` é indexada como página principal; confirmar canonical em runtime.

### Navegação
Homepage: https://msconcursos.com.br/  
Inscrições abertas: seção “INSCRIÇÕES ABERTAS” na home  
Em andamento: seção “CONCURSOS EM ANDAMENTO” na home  
Encerrados/histórico/detalhe: links “Saiba mais” de cada card; hrefs não expostos na captura.  
Documentos: dentro dos detalhes, links do edital e publicações; URL UNKNOWN.

### Universo observado
Observed: 9 itens visíveis no snapshot: 2 em “Inscrições abertas” e 7 em “Em andamento”.  
Relevant: 9, todos rotulados Concurso Público ou Processo Seletivo e ligados a órgãos/cargos.  
Active: 2 com inscrição aberta (Santana de Parnaíba editais 05/2026 médico e 06/2026 agente de trânsito).  
Closed: UNKNOWN (não foi aberta página histórica).  
Out of scope: vestibulares/cursos se aparecerem.

### Listagem
Estrutura HTML: headings de seção, card com tipo, título longo, período de inscrição, data de prova e links “Saiba mais”/“Inscreva-se”. Selector/container: UNKNOWN; selecionar links pelos textos e subir ao card. Status: heading/etiqueta do card.

### Paginação
Não evidenciada na home; seguir todos os links de detalhe e procurar página “concursos” no menu. Parâmetros UNKNOWN.

### Exemplo real
Título: Concurso Público para Médico e Médico Plantonista — Prefeitura de Santana de Parnaíba, SP — Edital 05/2026  
Órgão: Prefeitura de Santana de Parnaíba/SP  
Status: inscrições abertas, 19/08/2026–13/09/2026; prova 27/09/2026  
URL: link “Saiba mais” da home (href não exposto; extrair em runtime)  
Edital: link no detalhe, UNKNOWN.

### Campos
titulo/orgao/modalidade/status/inscrição_inicio/fim/prova_data: HTML do card (texto reproduzível).  
cargo: HTML do título em exemplo.  
vagas/salário/escolaridade/taxa/edital_numero/data/link_edital/link_inscricao/publicações: UNKNOWN no snapshot; obter no detalhe/PDF.

### Publicações
UNKNOWN na home; prever edital, retificações, gabarito, resultados e convocações no detalhe. Deduplicar por href e título/data.

### API/XHR
UNKNOWN; conteúdo principal aparece no HTML indexado, sem endpoint identificado. Não inventar API.

### Tecnologia
SERVER_RENDERED/OTHER; HTTP simples: provável SIM (conteúdo indexado), JS: UNKNOWN, Playwright: NÃO demonstrado.

### Bloqueios
Nenhuma evidência de WAF/CAPTCHA na fonte indexada; status HTTP direto não testável neste ambiente. Alternativa: domínio sem `www`.

### Quality gate
Aceitar Concurso Público/Processo Seletivo com período e órgão; rejeitar cards de notícias/serviços.

### Empty evidence
Não vazio: há 2 inscrições abertas e 7 em andamento declarados.

### Estratégia recomendada
`HTTP_HTML`/`CONFIGURABLE_HTML`; extrair detalhes dos hrefs reais e aceitar status por seção/período.

### Instruções para Codex
1. GET home e identificar headings “INSCRIÇÕES ABERTAS” e “CONCURSOS EM ANDAMENTO”. 2. Extrair cada card e href “Saiba mais”/“Inscreva-se”. 3. Parsear datas e prova do texto; no detalhe extrair PDFs/publicações. 4. Fixture: Santana de Parnaíba médico 05/2026. 5. Não usar contagem 9 como expected permanente; é observação da captura.

### Confidence
MEDIUM — status e campos de card claros, hrefs e detalhes não expostos.

### Evidências
https://msconcursos.com.br/; https://www.msconcursos.com.br/

## 31 — FACET Concursos

Identificador técnico: `facet_open`  
URL fornecida: https://www.facetconcursos.com.br  
URL oficial confirmada: https://concursos.facetconcursos.com.br/index/abertos/  
Portal ativo: SIM  
URL mudou: SIM — a operação de concursos está no subdomínio `concursos.facetconcursos.com.br`; o domínio institucional `facetconcursos.com.br` também exibe portfólio.

### Navegação
Aberto: `/index/abertos/`  
Em andamento: homepage do subdomínio  
Todos/histórico: `/index/todos/`  
Detalhe: `/informacoes/{id}/` (fixture `/informacoes/44/`)  
Documentos: publicação no detalhe; PDFs usam links próprios, inclusive `anexos.cdn.selecao.net.br` em exemplos indexados.

### Universo observado
Observed: `/index/todos/` declara “Mostrando 1–15 de 30”, com 30 total e paginação em duas páginas.  
Relevant: cards rotulados Concurso Público/Processo Seletivo; pelo menos 30 no universo.  
Active: 1 em `/index/abertos/` (Prefeitura de Floresta/PE 2026).  
Closed: demais itens do universo podem estar em andamento/homologados/finalizados/suspensos; total por estado UNKNOWN.  
Out of scope: notícias “CERTIFICADO”, contatos e área do candidato.

### Listagem/paginação
Cards HTML com tipo, título, edital, datas, “Quantidade de Vagas” e “Mais Informações”. Selector/container: UNKNOWN; localizar anchors dos cards e subir ao item. Paginação HTML com links 1, 2, Próxima, Última; seguir os hrefs reais (não presumir parâmetro).

### Exemplo real
Título: Concurso Público Prefeitura de Floresta/PE – 2026, Edital nº 01/2026  
Órgão: Prefeitura de Floresta/PE  
Status: Em andamento / inscrições abertas 24/08/2026–01/10/2026; 431 vagas declaradas  
URL: https://concursos.facetconcursos.com.br/informacoes/44/  
Edital: publicação “EDITAL - CONCURSO PÚBLICO…” em 24/08/2026.

### Campos
titulo, orgao, modalidade, status, vagas, inscrição_inicio/fim: HTML da listagem/detalhe.  
edital_numero/data, prova_data, taxa, link_edital, link_inscricao: HTML do detalhe e PDFs.  
cargo, salário, escolaridade, cidade/UF: HTML da tabela de vagas/detalhe; exemplo de processo seletivo 42 expõe tabela com cargo, escolaridade, salário, quantidade, taxa.  
area/salário_min/max: PDF/HTML, não garantidos; marcar UNKNOWN quando ausentes.

### Publicações
Detalhe tem seção “Publicações” com título/data/link; cronograma e tabela “Vagas”. Deduplicar por href, título e data; excluir menus, cookies, “Site 100% Seguro” e footer.

### API/XHR
UNKNOWN; HTML completo é indexado, sem API pública identificada. PDFs CDN são documentos, não endpoint de listagem.

### Tecnologia
SERVER_RENDERED / CONFIGURABLE_HTML; HTTP: SIM pela indexação; JS: UNKNOWN; Playwright: NÃO demonstrado.

### Bloqueios
Sem Cloudflare/CAPTCHA observado. O teste HTTP direto foi impedido pelo ambiente, não atribuir 403 ao portal.

### Quality gate
Aceitar tipos Concurso Público/Processo Seletivo e campos de órgão/cargo. Rejeitar certificados, notícias e vestibular.

### Empty evidence
Não vazio; rota aberta declara um item e todos declara 30.

### Estratégia recomendada
`CONFIGURABLE_HTML` com paginação pelos links reais e detalhe `/informacoes/{id}/`.

### Instruções para Codex
1. Crawl `/index/abertos/`; seguir `/index/todos/` e paginação até “Última”. 2. Para cada card, extrair tipo, título, edital, datas, vagas e href do detalhe. 3. No detalhe `/informacoes/44/`, extrair situação, cronograma, publicações e tabela de vagas. 4. Validar fixture Floresta; testar segunda página e duplicatas de PDFs. 5. Não confundir “todos=30” com ativos=30.

### Confidence
HIGH para rotas, paginação e exemplo; MEDIUM para selectors/API (não expostos).

### Evidências
https://concursos.facetconcursos.com.br/index/abertos/; https://concursos.facetconcursos.com.br/index/todos/; https://concursos.facetconcursos.com.br/informacoes/44/; https://facetconcursos.com.br/

## 32 — EDUCA PB

Identificador técnico: `educapb_open`  
URL fornecida: https://www.educapb.com.br  
URL oficial confirmada: https://educapb.selecao.net.br/index/1/  
Portal ativo: SIM  
URL mudou: SIM — o portal operacional mudou para `educapb.selecao.net.br`; footer identifica “ProSeleta - Gestão de Processos Seletivos Online”.

### Navegação
Listagem em andamento: `https://educapb.selecao.net.br/index/1/`  
Inscrições abertas: link “Inscrições Abertas” na própria página (href deve ser extraído).  
Em andamento/homologado/finalizado/suspenso/cancelado: links de menu visíveis.  
Detalhe: `/informacoes/{id}/` (fixture `/informacoes/6/`)  
Documentos: links `anexos-r2.selecao.net.br` no detalhe; inscrição online em link separado.

### Universo observado
Observed: 5 cards em andamento visíveis na página `/index/1/`.  
Relevant: 5 concursos públicos municipais; todos seleção de pessoal.  
Active: 1 com “Inscrições Abertas!” — Cuité de Mamanguape 01/2026.  
Closed: não há closed nessa rota; demais estados separados.  
Out of scope: login da área do candidato e footer ProSeleta.

### Listagem/paginação
HTML cards com tipo, título, edital, datas, isenção, vagas e href do detalhe. Selector/container: UNKNOWN; procurar anchors de `/informacoes/`. Paginação: não evidenciada para 5 itens; seguir links de navegação e estados.

### Exemplo real
Título: Concurso Público 01/2026 — Prefeitura Municipal de Cuité de Mamanguape/PB  
Órgão: Prefeitura Municipal de Cuité de Mamanguape  
Status: em andamento; inscrições 14/08/2026–13/09/2026; 117 vagas declaradas  
URL: https://educapb.selecao.net.br/informacoes/6/  
Edital: “Edital Normativo nº 01/2026 - Abertura de Inscrições”, link PDF em `anexos-r2.selecao.net.br`.

### Campos
HTML no detalhe: título, modalidade, órgão, situação, inscrição início/fim, isenção, publicações, cargos, escolaridade, salário, carga horária, quantidade, taxa. Exemplo mostra tabela de vagas com códigos 1–30 e esses campos.  
PDF: edital/atribuições/conteúdo programático e eventuais prova/cargos adicionais.  
link_edital/link_inscricao: HTML href; não montar URLs.  
area/cidade/UF/salário_min/max/edital_data: HTML/PDF quando explicitamente presentes; caso contrário UNKNOWN.

### Publicações
Seção “Publicações” no detalhe, com título, data e link PDF; inclui atribuições, conteúdo, edital, avisos e formulário. Deduplicar href/título/data. Ruído: menus de status, busca, área do candidato, cookie, footer ProSeleta.

### API/XHR
Nenhum endpoint público foi identificado; a própria página entrega HTML. Plataforma ProSeleta é evidenciada apenas no footer; não assumir API comum.

### Tecnologia
SERVER_RENDERED / white-label ProSeleta; HTTP: SIM pela indexação; JS: UNKNOWN; Playwright: NÃO demonstrado.

### Bloqueios
Sem WAF/CAPTCHA visível; teste HTTP direto não permitido no ambiente. Alternativa oficial é o subdomínio selecao.net.br.

### Quality gate
Aceitar Concurso Público/Processo Seletivo com órgão e cargo; rejeitar login, notícias, vestibular e links genéricos.

### Empty evidence
Não vazio: cinco itens, um com inscrição aberta.

### Estratégia recomendada
`CONFIGURABLE_HTML` e possível conector compartilhado com outras páginas `*.selecao.net.br` somente após confirmar estrutura; não presumir API.

### Instruções para Codex
1. Usar `/index/1/` como discovery. 2. Seguir links de menu (abertas, andamento, homologado, finalizado, suspenso, cancelado). 3. Extrair cards e abrir `/informacoes/{id}/`. 4. No detalhe, parsear tabela “Vagas” e publicações, preservando PDF URLs `anexos-r2.selecao.net.br`. 5. Fixture `/informacoes/6/`; testar classificação aberta versus em andamento.

### Confidence
HIGH para migração, rotas, campos e exemplo; MEDIUM para engine/API.

### Evidências
https://educapb.selecao.net.br/index/1/; https://educapb.selecao.net.br/informacoes/6/; https://educapb.com.br/

## 33 — ADM&TEC

Identificador técnico: `admtec_open`  
URL fornecida/confirmada: https://admtec.org.br/ (também `www.admtec.org.br`)  
Portal ativo: SIM  
URL mudou: NÃO/PARCIAL (ambas as variantes são indexadas).

### Navegação
Homepage: https://www.admtec.org.br/  
Concursos/detalhe: `/concursos/publicacoes/{slug-ou-id}/{id}`; exemplos `/concursos/publicacoes/MTA1/MTEz` (Iguaracy), `/MTEz/MTIx` (Piranhas).  
Categorias de status/histórico: links “Concursos” e páginas de publicação; URL de índice não confirmada.  
Documentos: links em seções “Edital e alterações”, “Publicações oficiais”, “Publicações”, “Resultados”.

### Universo observado
Observed total: UNKNOWN; páginas individuais têm vários itens e a busca/indexação não expõe índice completo.  
Relevant: páginas identificadas são concursos públicos e processos seletivos para cargos.  
Active: UNKNOWN global; exemplos recentes têm eventos 2026, mas não usar datas futuras isoladas como contagem ativa.  
Closed: UNKNOWN.  
Out of scope: formação institucional e área autenticada.

### Listagem
A melhor unidade observável é a página de detalhe com título do órgão, tipo, período de inscrição, blocos de documentos e cargos. Selector/container: UNKNOWN; links e headings sem CSS reproduzível. IDs/rotas codificados em dois segmentos no path.

### Paginação
Índice e parâmetros UNKNOWN; implementar discovery por links “Concursos”/sitemap apenas depois de observar HTML atual. Não assumir que slug Base64 seja ID decodificável.

### Exemplo real
Título: Concurso Público — Prefeitura Municipal de Piranhas/AL — Guarda Municipal 01/2026  
Órgão: Prefeitura Municipal de Piranhas/AL  
Status: página oficial mostra inscrições 10/04/2026–11/05/2026 e comunicações de devolução; certame em fase posterior/encerrada  
URL: https://www.admtec.org.br/concursos/publicacoes/MTEz/MTIx  
Edital: “Edital do Concurso (Retificado em 22/04/2026)” no bloco “Edital e alterações”.

### Campos
HTML: título, órgão, modalidade, período de inscrições, publicações, cargo (“Guarda Municipal”) e taxa R$125 no exemplo.  
PDF: edital, vagas, salário, escolaridade, cargos detalhados, prova e datas completas.  
links: href de cada item de publicação; API/JSON: UNKNOWN.

### Publicações
Blocos titulados “Edital e alterações”, “Publicações oficiais”, “Publicações”, “Resultados preliminares/finais”, “Gabarito”. Itens possuem data e link. Deduplicar `(concurso path, data, título, href)`; excluir “Sobre”, redes sociais e área do candidato.

### API/XHR
UNKNOWN; não foi encontrado endpoint declarado. A URL amigável contém dois segmentos codificados e a página é indexável como HTML.

### Tecnologia
SERVER_RENDERED / OTHER; HTTP: SIM pela indexação; JS: UNKNOWN; Playwright: NÃO demonstrado.

### Bloqueios
Sem WAF/CAPTCHA evidenciado; teste HTTP direto não permitido pelo ambiente.

### Quality gate
Aceitar concurso/processo seletivo que indique provimento de cargos/empregos; rejeitar página de formação, notícia institucional, login e “edital em desenvolvimento” sem processo aberto.

### Empty evidence
`UNKNOWN_EMPTY`; não há índice global/estado completo reproduzido.

### Estratégia recomendada
`CONFIGURABLE_HTML`/`DEDICATED_CONNECTOR_RECOMMENDED` (detalhe com vários blocos e rota codificada). Buscar índice oficial antes de crawl profundo.

### Instruções para Codex
1. Descobrir links da navegação “Concursos” no HTML atual. 2. Para cada detalhe `/concursos/publicacoes/{a}/{b}`, capturar headings e links de documentos. 3. Classificar bloco e data; parsear PDF quando HTML não trouxer campos. 4. Fixture Piranhas `/MTEz/MTIx` e Iguaracy `/MTA1/MTEz`; testar suspensão/anulação sem marcar ativo. 5. Não usar números codificados como Base64 sem evidência.

### Confidence
MEDIUM — detalhe, blocos e campos são claros; índice, paginação e API não.

### Evidências
https://www.admtec.org.br/concursos/publicacoes/MTEz/MTIx; https://www.admtec.org.br/concursos/publicacoes/MTA1/MTEz; https://admtec.org.br/

## 34 — CONTEMAX

Identificador técnico: `contemax_open`  
URL fornecida: https://www.contemaxconsultoria.com.br  
URL oficial atual: domínio fornecido continua citado em editais; rotas históricas confirmadas em `.../site/concursos-em-andamento/...` e `.../site/concursosrealizados/...`.  
Portal ativo: INCERTO/PARCIAL  
URL mudou: PARCIAL — não foi possível reproduzir índice atual; editais de 2024 ainda referenciam o domínio.

### Navegação
Homepage: https://www.contemaxconsultoria.com.br/  
Em andamento (histórica): `/site/concursos-em-andamento/{slug}`  
Realizados: `/site/concursosrealizados/{slug}`  
Detalhe: exemplos históricos em links oficiais de contratos: `/site/concursosrealizados/prefeitura-municipal-de-bayeux`, etc.  
Documentos: links de edital/resultados; URLs atuais UNKNOWN.

### Universo observado
Observed/Relevant/Active/Closed: UNKNOWN no índice atual. Editais oficiais/contratos comprovam portfólio de concursos e processos seletivos.  
Out of scope: serviços de RH sem certame e páginas de capacidade técnica.

### Listagem
A estrutura histórica é por slugs de órgão, com página de concurso e documentos; selector/container, título, status e ID: UNKNOWN.

### Paginação
UNKNOWN; não inventar parâmetros.

### Exemplo real
Título: Concurso Público — Prefeitura Municipal de Cubati/PB (2024)  
Órgão: Prefeitura Municipal de Cubati/PB  
Status: encerrado/histórico; inscrições e provas em 2024  
URL histórica: https://www.contemaxconsultoria.com.br/site/concursos-em-andamento/prefeitura-municipal-de-cubati-pb  
Edital: PDF do manual/edital; não há href atual reproduzível na captura.

### Campos
HTML atual: UNKNOWN.  
PDF/manual de edital: cronograma, cargos, vagas, salários, escolaridade, taxa, prova e documentos. Editais de 2024 exibem cronograma detalhado; usar PDF como fonte para campos ausentes.

### Publicações
Em páginas históricas, esperar edital, retificações, gabaritos, resultados e convocações; links e datas UNKNOWN. Deduplicar por href/hash e texto.

### API/XHR
UNKNOWN; nenhuma API pública identificada.

### Tecnologia/Bloqueios
Tipo UNKNOWN; conteúdo atual não confirmado. WAF/HTTP/CAPTCHA UNKNOWN. Não fazer bypass; buscar páginas do órgão/edital oficial como alternativa documental.

### Quality gate
Aceitar somente concursos/processos seletivos de pessoal; rejeitar portfólio, contratos e notícias sem vaga.

### Empty evidence
`UNKNOWN_EMPTY`; ausência de índice atual não prova vazio.

### Estratégia recomendada
`DEPRECATE_REVIEW_REQUIRED` + `KEEP_BLOCKED` até health-check do domínio. Se rotas históricas voltarem, `CONFIGURABLE_HTML` dedicado para slugs.

### Instruções para Codex
1. Testar homepage, `/site/concursos-em-andamento/` e `/site/concursosrealizados/`. 2. Seguir apenas links oficiais retornados; não gerar slugs. 3. Se página não existir, registrar URL_OUTDATED/SITE_OFFLINE e usar edital oficial do órgão somente como evidência de closed. 4. Fixture histórica Cubati; não marcar ativo sem página atual e período vigente.

### Confidence
LOW — domínio e rotas históricas documentados, índice atual/API não confirmados.

### Evidências
https://www.contemaxconsultoria.com.br/; https://www.contemaxconsultoria.com.br/site/concursos-em-andamento/prefeitura-municipal-de-cubati-pb; https://www.contemaxconsultoria.com.br/site/concursosrealizados/prefeitura-municipal-de-bayeux

## 35 — CPCon / UEPB

Identificador técnico: `cpcon_open`  
URL fornecida/confirmada: https://cpcon.uepb.edu.br  
Portal ativo: PARCIAL (portal novo e arquivo histórico coexistem)  
URL mudou: SIM/PARCIAL — páginas novas em `cpcon.uepb.edu.br`; acervo legado em `arquivo.cpcon.uepb.edu.br` e sistema do candidato em `sistemas.cpcon.uepb.edu.br`.

### Navegação
Homepage: https://cpcon.uepb.edu.br/  
Índice legado: https://arquivo.cpcon.uepb.edu.br/concursos.htm (anos/status)  
Detalhes novos: páginas WordPress, ex. https://cpcon.uepb.edu.br/prefeitura-municipal-de-nova-palmeira/  
Documentos: blocos “Documentos Publicados”, “Editais”, “Provas e Gabaritos” com download.  
Inscrições: sistema separado `sistemas.cpcon.uepb.edu.br`/links “Acesso à área do candidato”.

### Universo observado
Observed: índice legado mostra muitos concursos por ano (p.ex. 2020/2021); contagem total UNKNOWN.  
Relevant: concursos públicos e processos seletivos UEPB/municípios.  
Active: UNKNOWN — exemplos pesquisados são 2022/2023/2025 e páginas atuais podem estar encerradas.  
Closed: vários explicitamente “resultado final publicado”.  
Out of scope: vestibulares/transferência e cursos quando não seleção de pessoal; filtro institucional obrigatório.

### Listagem/paginação
Legado: HTML estático agrupado por ano e links de concurso; sem paginação observada. Novo: WordPress posts/páginas com tabela de documentos; selector CSS não confirmado. Seguir links reais e arquivos `arquivo.cpcon...`.

### Exemplo real
Título: Concurso Público da Universidade Estadual da Paraíba — Edital Normativo 001/2023  
Órgão: UEPB  
Status: encerrado (página exibe resultados finais e documentos de 2023)  
URL: https://cpcon.uepb.edu.br/concurso-publico-da-universidade-estadual-da-paraiba/  
Edital: “Edital Normativo (Consolidado)” em bloco Editais.

### Campos
HTML: título, órgão, tipo e lista de publicações/datas.  
PDF: vagas, cargos, escolaridade, salários, taxa, prova, cronograma e edital número/data.  
Inscrição/resultado: links externos a sistema e PDFs. API WordPress: não verificada, não presumir `wp-json`.

### Publicações
Blocos nomeados “Documentos Publicados”, “Editais”, “Provas e Gabaritos”, “Atualizações na área do candidato”; cada item tem título, data e Download. Deduplicar URL+hash; excluir menu/contatos.

### API/XHR
UNKNOWN; apesar de WordPress aparente, endpoint REST não foi confirmado. Sistema SIGEPS é autenticação, não fonte de listagem pública.

### Tecnologia
WORDPRESS (páginas novas; evidência de estrutura de posts), STATIC_HTML legado/PDF_INDEX. HTTP: SIM para páginas indexadas; JS: NÃO demonstrado; Playwright: NÃO para discovery.

### Bloqueios
Sem WAF/CAPTCHA evidenciado. Há múltiplos subdomínios oficiais; usar arquivo se novo não listar histórico.

### Quality gate
Aceitar concurso/processo seletivo de cargos/empregos/temporários. Rejeitar transferência, vestibular, cursos e editais acadêmicos não laborais.

### Empty evidence
`UNKNOWN_EMPTY`; páginas exibem histórico e não fornecem estado global atual.

### Estratégia recomendada
`CONFIGURABLE_HTML`/`DEDICATED_CONNECTOR`; tratar novo WordPress e arquivo legado como duas origens de discovery; `INSTITUTIONAL_FILTER_REQUIRED`.

### Instruções para Codex
1. Crawl homepage e índice legado por ano. 2. Seguir páginas de concurso e extrair os quatro blocos de documentos. 3. Parsear PDF para campos de edital. 4. Excluir vestibular/transferência/professor formador sem contratação compatível. 5. Fixture Nova Palmeira/UEPB 2023; testar páginas arquivo e novo domínio sem duplicar por título+órgão+ano+documento.

### Confidence
MEDIUM — migração, estrutura e filtros claros; índice atual/API e active não.

### Evidências
https://cpcon.uepb.edu.br/; https://arquivo.cpcon.uepb.edu.br/concursos.htm; https://cpcon.uepb.edu.br/concurso-publico-da-universidade-estadual-da-paraiba/; https://sistemas.cpcon.uepb.edu.br/

## 36 — FUNVAPI

Identificador técnico: `funvapi_open`  
URL fornecida/confirmada: https://www.funvapi.com.br/  
Portal ativo: SIM  
URL mudou: NÃO/PARCIAL — WordPress usa também `funvapi.com.br/index.php/category/concursos/`.

### Navegação
Homepage: https://funvapi.com.br/  
Concursos em andamento: link textual “CONCURSOS EM ANDAMENTO” (href deve ser extraído)  
Realizados: `/index.php/category/concursos-realizados/`  
Categoria: `/index.php/category/concursos/`  
Detalhe: posts por concurso (href deve ser extraído).  
Documentos: links PDF WordPress `wp-content/uploads/YYYY/MM/...pdf`.

### Universo observado
Observed: categoria “Concursos” mostra vários posts recentes; pelo menos 5 blocos de municípios na captura (Belo Jardim, Vera Mendes, Princesa Isabel, Cajueiro, Aroeiras, Iati etc.); total UNKNOWN.  
Relevant: posts explicitamente Concurso Público e Processo de Seleção de profissionais da educação.  
Active: UNKNOWN global; posts recentes incluem 2026 e devem ser classificados por datas/status dos documentos.  
Closed: categoria “Concursos Realizados” separada.  
Out of scope: FAQ, notícias administrativas e outras categorias.

### Listagem/paginação
WordPress archive posts com título, data/autor e links; paginação textual “1 2 … 12 Older posts”. Selector CSS: UNKNOWN; seguir anchors do archive e links de “Older posts”.

### Exemplo real
Título: Concurso Público nº 001/2026 — Câmara Municipal de Vera Mendes/PI  
Órgão: Câmara Municipal de Vera Mendes/PI  
Status: página de categoria recente; documentos incluem edital, retificações e isenção; estado ativo exato UNKNOWN  
URL: https://www.funvapi.com.br/index.php/category/concursos/  
Edital: link PDF “EDITAL DE CONCURSO PÚBLICO Nº 001/2026”.

### Campos
HTML do post: órgão/título, lista de documentos e datas do post.  
PDF: número/data, vagas, cargos, salário, escolaridade, taxa, prova e cronograma.  
status/inscrição: HTML/PDF; não inferir active só da data de publicação. link_edital/inscrição: href real do post/PDF.

### Publicações
Cada post lista edital, retificações, isenção, homologados, concorrência, locais de prova, gabarito, resultados e homologação. Deduplicar href/hash; excluir widgets, FAQ, autor e menu.

### API/XHR
WORDPRESS é evidenciado pela estrutura `/index.php/category/` e uploads; REST `wp-json` não verificado. Não assumir endpoint API.

### Tecnologia
WORDPRESS/PDF_INDEX; HTTP: SIM pela indexação; JS: NÃO demonstrado; Playwright: NÃO.

### Bloqueios
Sem WAF/CAPTCHA observado; HTTP direto do ambiente não permitido.

### Quality gate
Aceitar concurso/processo seletivo de pessoal e “seleção de profissionais”. Rejeitar bolsas, fomento e comunicados sem cargo. “Concursos realizados” serve para closed, não active.

### Empty evidence
Não vazio como archive; active global UNKNOWN.

### Estratégia recomendada
`WORDPRESS_API` somente após confirmar REST; por ora `CONFIGURABLE_HTML` com archives + PDFs.

### Instruções para Codex
1. Crawl `/index.php/category/concursos/` e todas as páginas Older posts. 2. Para cada post, extrair todos os links PDF e classificar tipo pelo texto. 3. Separar `/concursos-realizados/` como closed. 4. Derivar status somente de indicação explícita (inscrição, convocação, homologação), não da data do post. 5. Fixture Vera Mendes 001/2026 e Iati; teste de paginação até página 12.

### Confidence
MEDIUM — WordPress/archive/documentos claros; total/active e REST não.

### Evidências
https://funvapi.com.br/; https://www.funvapi.com.br/index.php/category/concursos/; https://www.funvapi.com.br/index.php/category/concursos-realizados/; https://funvapi.com.br/index.php/perguntas-frequentes/

## 37 — CONSEP

Identificador técnico: `consep_open`  
URL fornecida/confirmada: https://www.consep-pi.com.br/concursos  
Portal ativo: SIM  
URL mudou: NÃO.

### Navegação
Todos: `/concursos`  
Aberto: link “Aberto” (href no menu)  
Em andamento: link “Em Andamento”  
Encerrado: link “Encerrado”  
Detalhe: `/concurso/{slug}/{id}` (exemplos `/concurso/.../203`, `/188`)  
Documentos: links de edital/comunicado/divulgação PDF no detalhe.

### Universo observado
Observed: página declara “Abertos — Não há dados para visualização”, “Em Andamento” com 1 item e “Encerrados” com 8 itens visíveis; total de todos UNKNOWN.  
Relevant: teste seletivo/processo seletivo/concurso para municípios.  
Active: 1 — “TESTE SELETIVO EDITAL N 002/2026 - BAIXA GRANDE DO RIBEIRO”.  
Closed: pelo menos 8 listados.  
Out of scope: notícias/comunicados gerais não vinculados a concurso.

### Listagem/paginação
HTML com blocos por status e links de detalhe `/concurso/{slug}/{id}`. Selector/container UNKNOWN. Paginação: não observada; clicar “Veja todos” e links de status.

### Exemplo real
Título: Teste Seletivo Edital N 002/2026 — Baixa Grande do Ribeiro  
Órgão: Prefeitura de Baixa Grande do Ribeiro/PI  
Status: em andamento; inscrições 11/05/2026–15/05/2026; detalhe lista 13 publicações  
URL: https://www.consep-pi.com.br/concurso/TESTE-SELETIV0-EDITAL-N-002-2026-BAIXA-GRANDE-D0-RIBEIR0/203/  
Edital: “BAIXA GRANDE DO RIBEIRO - EDITAL - TESTE SELETIVO 2026” PDF de 11/05/2026.

### Campos
HTML detalhe: título, inscrição início/fim, número de documentos/publicações, status por rota e órgão.  
PDF edital: cargos, vagas, salários, escolaridade, taxa, prova e cronograma.  
links PDFs: anchors do bloco “Acesso a Editais, Comunicados e Divulgações”. Cidade/UF no título/edital; demais UNKNOWN se ausentes.

### Publicações
Bloco cronológico com título, data entre colchetes e PDF; tipos incluem edital, inscrições deferidas, local de provas, gabaritos, resultados e recursos. Publicações gerais aparecem também no detalhe e na página `/concursos`; deduplicar por href+hash.

### API/XHR
UNKNOWN; HTML server-rendered aparente, sem API confirmada.

### Tecnologia
SERVER_RENDERED/PDF_INDEX; HTTP: SIM pela indexação; JS: NÃO demonstrado; Playwright: NÃO.

### Bloqueios
Sem WAF/CAPTCHA; portal informa “conteúdo poderá ser alterado” e atualizações frequentes. Não depender de cache.

### Quality gate
Aceitar Concurso/Processo/Teste Seletivo com órgão/cargos. Rejeitar comunicados avulsos sem certame, menu e informativos genéricos.

### Empty evidence
`EMPTY_EXPLICIT` para categoria “Abertos” (texto literal “Nao há dados para visualizaçao”); fonte não é vazia porque há 1 em andamento.

### Estratégia recomendada
`CONFIGURABLE_HTML`; crawl status “Aberto”, “Em Andamento”, “Encerrado” e detalhe, com PDFs.

### Instruções para Codex
1. GET `/concursos`; seguir hrefs dos três status e “Veja todos”. 2. Extrair cada `/concurso/{slug}/{id}`. 3. Parsear bloco de 13 publicações e PDF do edital. 4. Registrar explicitamente vazio de “Aberto” sem zerar “Em andamento”. 5. Fixture `/203/`; teste de closed `/188/` e deduplicação de publicação geral.

### Confidence
HIGH — status explícitos, rotas, exemplo e publicação reproduzíveis.

### Evidências
https://www.consep-pi.com.br/concursos; https://www.consep-pi.com.br/concurso/TESTE-SELETIV0-EDITAL-N-002-2026-BAIXA-GRANDE-D0-RIBEIR0/203/; https://www.consep-pi.com.br/concurso/C0NCURS0-PUBLIC0-PREFEITURA-MUNICIPAL-DE-0UR0-VELH0-PB/188/

## 38 — Instituto Consulplan (atenção especial; comparar depois com fonte 07)

Identificador técnico: `institutoconsulplan_open`  
URL fornecida/confirmada: https://institutoconsulplan.azurewebsites.net/Concursos  
Portal ativo: SIM  
URL mudou: NÃO (o host Azure é o portal operacional observado; não tratar como domínio abandonado).

### Navegação
Homepage: https://institutoconsulplan.azurewebsites.net/  
Concursos: `/Concursos`  
Detalhe: links “Mais Informações” levam a `concurso.jsp?id={n}` (exemplos confirmados `id=597`, `574`, `599`, `568`).  
Inscrição: links “Inscreva-se” no card/detalhe; acompanhar inscrição no detalhe.  
Documentos/publicações: dentro de `concurso.jsp?id={n}`, lista cronológica de links; PDFs ficam em `cdnsite.consulplan.net/concursos/...` em editais observados.

### Universo observado
Observed: `/Concursos` expõe 5 itens em “Inscrições abertas / Novos”, cerca de 14 em “Em andamento” (incluindo CFBM, Viana, TJMS, Campos, câmaras, TJMG, Manaus, CAU, Ji-Paraná, Vitória, Alagoa, Campos e Venda Nova) e uma lista extensa em “Encerrados”; total exacto UNKNOWN.  
Relevant: concursos públicos, processos seletivos, seleções públicas e emprego/estágio quando ligados a pessoal; vestibulares aparecem em encerrados e devem ser filtrados.  
Active: pelo menos itens nos blocos “Inscrições abertas / Novos” e “Em andamento”; quantidade exacta UNKNOWN.  
Closed: muitos itens explícitos em “Encerrados”, não contar para ativos.  
Out of scope: vestibulares (Universidade de Itaúna/UNIFACIG), exames/certificações e promoções sem contratação.

### Listagem
Estrutura HTML server-rendered: cada card tem imagem, órgão, tipo e “Mais Informações”; cards em três seções de status. Selector/container: UNKNOWN; selecionar anchors para `concurso.jsp?id=` e subir ao card. ID numérico no query string. Status é o título da seção e/ou tipo do detalhe.

### Paginação
Não observada na página `/Concursos`; toda a lista é extensa. Seguir todos os anchors `concurso.jsp?id=` e não limitar a primeira tela. Parâmetros de lista UNKNOWN.

### Exemplo real
Título: Prefeitura Municipal de Potirendaba/SP — Concurso Público  
Órgão: Prefeitura Municipal de Potirendaba/SP  
Status: seção “Inscrições abertas / Novos” na página oficial observada  
URL: https://institutoconsulplan.azurewebsites.net/Concursos (o href do detalhe não foi exposto pela captura; extrair em runtime)  
Edital: link PDF no detalhe; URL exata UNKNOWN no índice.

Observação importante: os exemplos `concurso.jsp?id=597/574/599` pertencem ao Instituto Avalia (fonte 39), não ao Consulplan. Não reutilizar esses IDs no conector 38.

### Campos
HTML do card/detalhe: título, órgão, tipo/modalidade, status por seção, links de inscrição/acompanhamento, publicações e datas.  
PDF: cargos, vagas, salários, escolaridade, taxa, prova, edital número/data e cronograma.  
`link_edital`/publicações: hrefs reais do detalhe, frequentemente CDN; `link_inscricao`: href “Inscreva-se”.  
Cidade/UF: normalmente no nome do órgão; marcar UNKNOWN se ausente, não inferir. API/JSON: UNKNOWN.

### Publicações
Detalhes exibem linha do tempo com editais de abertura/retificações, deferimento, convocação, resultados, gabaritos, homologação e anexos. Deduplicar por href/hash porque editais e anexos pareados podem repetir título/data. Excluir vestibular, newsletter, cookies, menu e “Acompanhamento de Inscrição” autenticado como publicação.

### API/XHR
Endpoint/método/paginação/JSON path: UNKNOWN. A página de concursos é HTML indexável e links `.jsp`/PDF; não afirmar API Azure/REST sem Network.

### Tecnologia
SERVER_RENDERED / OTHER (host Azure); HTTP: SIM pela indexação; JS: NÃO demonstrado para discovery; Playwright: NÃO provável, mas usar fallback se cards faltarem.

### Bloqueios
Sem Cloudflare/CAPTCHA observado. URLs de PDF CDN podem expirar/usar token; extrair href no momento da coleta.

### Quality gate
Aceitar Concurso Público, Processo Seletivo Público, Seleção Pública ou emprego/estágio de pessoal com órgão/cargo. Rejeitar vestibular, residência acadêmica, certificação e promoção sem vaga.

### Empty evidence
Não vazio; seções abertas/andamento possuem cards. Nunca considerar somente “Encerrados”.

### Estratégia recomendada
`DEDICATED_CONNECTOR` + `CONFIGURABLE_HTML`; três seções e filtro institucional. Manter 38 separado de 07 até comparação controlada: 38 usa host Azure e `.jsp?id=`/CDN; referências antigas a `consulplan.net` em editais não provam que os universos sejam iguais. Não pesquisar 07 neste batch.

### Instruções para Codex
1. GET `/Concursos`, extrair todos os cards das três seções e hrefs reais. 2. Classificar status pela seção e abrir o detalhe. 3. Parsear título/órgão/tipo, links de inscrição e publicações; baixar PDFs CDN. 4. Filtrar vestibulares e certificações. 5. Criar fixture de um card aberto e um encerrado; não usar IDs 597 etc. da Avalia. 6. Em comparação futura com fonte 07, comparar URLs, IDs, órgãos, títulos e PDFs por conteúdo antes de aliasar/remover duplicação.

### Confidence
MEDIUM — host, seções, tipos e comportamento são reproduzíveis; hrefs individuais/API e equivalência com 07 ainda não.

### Evidências
https://institutoconsulplan.azurewebsites.net/Concursos; https://institutoconsulplan.azurewebsites.net/; https://cdnsite.consulplan.net/concursos/1776%20/%204_785589.pdf

## 39 — Instituto Avalia

Identificador técnico: `avalia_open`  
URL fornecida/confirmada: https://www2.avalia.org.br/concursos.jsp  
Portal ativo: SIM  
URL mudou: NÃO.

### Navegação
Listagem: `/concursos.jsp`  
Filtros/status: “EM ANDAMENTO”, “INSCRIÇÃO ABERTA”, “PRÓXIMOS”, “COM RESULTADO DISPONÍVEL”, “FINALIZADO” (filtros visíveis).  
Detalhe: `/concurso.jsp?id={n}`; fixtures `id=597` Joinville, `574` Porto Alegre, `599` RN, `568` Itapetininga.  
Documentos/publicações: seção “PUBLICAÇÕES” no detalhe, com data e links; PDFs/hrefs devem ser extraídos.

### Universo observado
Observed: listagem extensa com dezenas de órgãos; total exacto UNKNOWN.  
Relevant: concursos, empregos públicos, processos/seleções de pessoal e estágio; página também inclui vestibulares, residência médica, avaliações e promoções.  
Active: pelo menos “Empresa de Pesquisa Agropecuária e Extensão Rural de Santa Catarina — EPAGRI” e “UESB” aparecem como inscrições abertas; “Secretaria de Educação de Pernambuco — Projeto Ganhe o Mundo Professor” e outros estão em andamento. Número exacto UNKNOWN.  
Closed: muitos com resultado/homologação final.  
Out of scope: vestibular (UIT/UNIFACIG), residência médica, certificação, promoção interna sem contratação, curso/chamada não laboral.

### Listagem/paginação
HTML com headings `####` por órgão e link `concurso.jsp?id={n}`; filtros de status na mesma página. Pagination: não evidenciada; seguir todos os links de detalhe. Selector/container UNKNOWN.

### Exemplo real
Título: Município de Joinville/SC — Concurso Público nº 004/2026  
Órgão: Município de Joinville/SC  
Status: em andamento; detalhe contém publicações de 28/08/2026 (resultado preliminar de títulos etc.)  
URL: https://www2.avalia.org.br/concurso.jsp?id=597  
Edital: publicações e termos de retificação no detalhe; href real deve ser extraído.

### Campos
HTML detalhe: órgão, texto descritivo do concurso, status implícito por publicações, links de acompanhamento e lista cronológica de publicações.  
PDF: edital, cargos, vagas, salários, escolaridade, taxa, prova e cronograma.  
link_edital/publicações: hrefs da seção PUBLICAÇÕES.  
cidade/UF/modalidade: HTML no título/descrição quando explícitos. API/JSON: UNKNOWN.

### Publicações
Detalhe mostra lista extensa com datas, termos de retificação, deferimento, convocações, resultados de provas/títulos, gabaritos, homologação e anexos. Deduplicar por URL/hash e manter anexos distintos. Ruído: “Consultar número e situação da inscrição”, boletins personalizados e links autenticados.

### API/XHR
UNKNOWN; páginas `.jsp?id=` são server-rendered/indexáveis, sem endpoint JSON confirmado.

### Tecnologia
SERVER_RENDERED / PDF_INDEX; HTTP: SIM; JS: NÃO demonstrado; Playwright: NÃO provável.

### Bloqueios
Nenhum WAF/CAPTCHA observado; não depender de links de acompanhamento autenticados para discovery.

### Quality gate
Aceitar concurso/processo/seleção/emprego/estágio que seja seleção de pessoas. Rejeitar vestibular, residência, promoção/certificação e chamadas acadêmicas. Aplicar filtro por título e descrição, não somente palavra “edital”.

### Empty evidence
Não vazio: filtros e órgãos com inscrições abertas/em andamento.

### Estratégia recomendada
`DEDICATED_CONNECTOR`/`CONFIGURABLE_HTML`; discovery por `concurso.jsp?id=`, filtro institucional forte e detalhe para publicações.

### Instruções para Codex
1. GET `/concursos.jsp`, coletar todos os links `concurso.jsp?id=` e o rótulo de seção/filtro. 2. Abrir cada detalhe e extrair descrição, órgão, tipo, publicações e hrefs. 3. Parsear PDFs para campos ausentes. 4. Excluir vestibulares/residências/certificações/promoções. 5. Fixtures `id=597` (Joinville ativo/em andamento), `id=574` (Porto Alegre, resultado/homologação) e `id=568` (Itapetininga, concurso); testar deduplicação de anexos.

### Confidence
HIGH para rotas, filtros, detalhe e exemplos; MEDIUM para selectors/API e contagem total.

### Evidências
https://www2.avalia.org.br/concursos.jsp; https://www2.avalia.org.br/concurso.jsp?id=597; https://www2.avalia.org.br/concurso.jsp?id=574; https://www2.avalia.org.br/concurso.jsp?id=568

## Quality gate transversal do batch

Para todas as bancas, `active` somente pode ser marcado por seção/status explícito ou período de inscrição vigente no próprio portal/detalhe; datas de publicação de PDF não bastam. `UNKNOWN` não deve ser convertido em zero. PDFs são evidência documental de campos e devem ser baixados pelos hrefs observados. Filtros institucionais são obrigatórios para CPCon, Consulplan e Avalia, pois os portais misturam concursos com vestibular, residência, certificação e outras avaliações.

## Casos para revisão do Sol

1. IUDS (28): LOW; portal operacional atual/listagem não foi reproduzível, decidir se manter bloqueado ou fazer segunda verificação.  
2. Reis & Reis (29): LOW; shell “Carregando concursos…” exige descoberta de XHR/Playwright.  
3. CONTEMAX (34): LOW; domínio/índice atual incerto, rotas históricas preservadas.  
4. Consulplan 38 versus fonte 07: ainda não determinar alias/mesmo universo; comparação deve ser feita posteriormente com evidência de URLs, IDs e PDFs.  
5. ADM&TEC (33): índice global e status ativo não confirmados; detalhes são fortes, mas não usar amostra como contagem.

## Matriz explícita dos campos exigidos

Esta matriz torna explícita a classificação HTML/API/PDF/UNKNOWN de cada campo solicitado; quando há mais de uma fonte, o Codex deve preferir HTML estruturado e conservar o PDF como evidência.

| Fonte | titulo | orgao | modalidade | cargo | area | cidade/UF | status | vagas | salario_min/max | escolaridade | taxa | prova_data | edital_numero/data | inscricao_inicio/fim | link_edital | link_inscricao |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 27 Águia | HTML | HTML | HTML | HTML/PDF | UNKNOWN | HTML | HTML | PDF/HTML | HTML/PDF | PDF | PDF | PDF | PDF | HTML | HTML | HTML |
| 28 IUDS | HTML/PDF | HTML/PDF | HTML/PDF | HTML/PDF | UNKNOWN | HTML/PDF | UNKNOWN | PDF | PDF | PDF | PDF | PDF | PDF | HTML/PDF | HTML | HTML/UNKNOWN |
| 29 Reis & Reis | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN |
| 30 MS Concursos | HTML | HTML | HTML | HTML/PDF | UNKNOWN | HTML/PDF | HTML | PDF/detail | PDF/detail | PDF | PDF | HTML/PDF | HTML/PDF | HTML | HTML | HTML |
| 31 FACET | HTML | HTML | HTML | HTML/PDF | UNKNOWN | HTML/PDF | HTML | HTML/PDF | HTML/PDF | HTML/PDF | HTML/PDF | PDF | HTML/PDF | HTML | HTML | HTML |
| 32 EDUCA PB | HTML | HTML | HTML | HTML | UNKNOWN | HTML/PDF | HTML | HTML/PDF | HTML/PDF | HTML/PDF | HTML/PDF | PDF | HTML/PDF | HTML | HTML | HTML |
| 33 ADM&TEC | HTML | HTML | HTML | HTML/PDF | UNKNOWN | HTML/PDF | HTML/PDF | PDF | PDF | PDF | HTML/PDF | PDF | HTML/PDF | HTML/PDF | HTML | HTML |
| 34 CONTEMAX | UNKNOWN | UNKNOWN | UNKNOWN | PDF | UNKNOWN | PDF | UNKNOWN | PDF | PDF | PDF | PDF | PDF | PDF | PDF | UNKNOWN | UNKNOWN |
| 35 CPCon | HTML | HTML | HTML | PDF | UNKNOWN | HTML/PDF | UNKNOWN | PDF | PDF | PDF | PDF | PDF | PDF | PDF | HTML | HTML |
| 36 FUNVAPI | HTML | HTML | HTML/PDF | PDF | UNKNOWN | PDF | UNKNOWN | PDF | PDF | PDF | PDF | PDF | PDF | PDF | HTML | HTML |
| 37 CONSEP | HTML | HTML | HTML | PDF | UNKNOWN | HTML/PDF | HTML | PDF | PDF | PDF | PDF | PDF | PDF | HTML/PDF | HTML | HTML |
| 38 Consulplan | HTML | HTML | HTML | PDF | UNKNOWN | HTML/PDF | HTML | PDF | PDF | PDF | PDF | PDF | PDF | HTML/PDF | HTML | HTML |
| 39 Avalia | HTML | HTML | HTML | PDF | UNKNOWN | HTML/PDF | HTML | PDF | PDF | PDF | PDF | PDF | PDF | HTML/PDF | HTML | HTML |
