# BATCH 06 — fontes 66–77

Pesquisa externa realizada em 30/08/2026. Contagens abaixo são apenas as que aparecem de forma explícita em páginas oficiais; quando a listagem mistura fases, anos ou tipos de edital, mantive `UNKNOWN`. Em FAPs/fundações, “edital” de bolsa, fomento, compra, chamada científica ou apoio a projeto não foi contado como concurso/seleção de pessoal.

## 66 — FAPES (ES)

Identificador técnico: `fapes_selection`  
URL fornecida: https://fapes.es.gov.br/editais  
URL oficial confirmada: https://fapes.es.gov.br/editais (domínio oficial Governo ES; links de categorias levam a `/edital-aberto-formação-científica`, `/editais-abertos-pesquisa-4`, `/Editais/Encerrados`, `/Editais/Resultados`).  
Portal ativo: SIM. URL mudou: NÃO.

### Navegação
Homepage: https://fapes.es.gov.br/  
Abertos: categorias “Carreira Científica”, “Pesquisa”, “Difusão do Conhecimento”, “Extensão”, “Inovação” e “Chamadas Internacionais” no menu; exemplo https://fapes.es.gov.br/edital-aberto-forma%C3%A7%C3%A3o-cient%C3%ADfica  
Em andamento/em julgamento: menu “Em Julgamento”, por categoria.  
Encerrados: https://fapes.es.gov.br/Editais/Encerrados  
Resultados: https://fapes.es.gov.br/Editais/Resultados  
Detalhe/documentos: cada linha de edital tem título, descrição, data, formato PDF e “Baixar”; o conteúdo do edital é PDF.

### Universo observado
Observed: 3 itens na categoria de Carreira Científica aberta (PIC Jr 2027, Pós-Doutorado Sênior, PROFIX-CB) e muitos itens nas demais categorias; total do portal `UNKNOWN`.  
Relevant: 0 atuais confirmados como contratação/emprego. Os itens observados são seleção de propostas, bolsas, pesquisa, inovação ou auxílio.  
Active: 0 seleções de pessoal confirmadas; há editais ativos de fomento.  
Closed: UNKNOWN.  
Out of scope: bolsas (PIC Jr, pós-doc, Nossa Bolsa), apoio à pesquisa/eventos, chamadas internacionais e seleção de projetos/empresas.

### Listagem
Estrutura: HTML server-rendered com cabeçalho de categoria e linhas/tabela de conteúdo; texto observável: `Conteúdo | Atualização | Formato | Tamanho`, seguida de descrição e link “Baixar”.  
Selector/container: não foi exposto seletor CSS confiável na inspeção textual; não inventar.  
Título/link/status: título do item é link para página ou PDF; status vem da categoria (Abertos, Em Julgamento, Encerrados, Resultados), não de atributo de cada linha.  
ID: não observado.

### Paginação
Método: não observada na categoria aberta consultada; use todas as categorias e não assuma que `/editais` é uma lista única.  
Parâmetros: desconhecidos.

### Exemplo real
Título: EDITAL FAPES Nº 19/2026 — Programa de Iniciação Científica Júnior (PIC Jr 2027).  
Órgão: FAPES/SEDU.  
Status: aberto, seleção de propostas/bolsas (fora do escopo de emprego).  
URL: https://fapes.es.gov.br/edital-aberto-forma%C3%A7%C3%A3o-cient%C3%ADfica  
Edital: PDF acessível pelo link “Baixar” na linha do edital.

### Campos
titulo: HTML (título/link).  
orgao: HTML (FAPES e parceiros, quando descritos).  
modalidade: HTML/PDF (categoria e texto do edital).  
cargo, area, cidade, uf, vagas, salario_min/max, escolaridade, taxa, prova_data: NÃO DISPONÍVEL para seleção de pessoal; quando existem, estão somente no PDF do edital de fomento.  
status: HTML (categoria da página).  
edital_numero/data, inscricao_inicio/fim: HTML/PDF conforme edital.  
link_edital: HTML (link “Baixar”, PDF).  
link_inscricao: PDF/HTML; em editais de proposta normalmente SigFAPES, não inscrição de candidato a emprego.

### Publicações
Estrutura: páginas separadas de Abertos, Em Julgamento, Encerrados e Resultados; resultados/retificações aparecem como linhas PDF.  
Tipos: edital, alteração/retificação, resultado preliminar/final, chamada internacional.  
Selector/API: HTML/PDF; nenhum endpoint público confirmado.  
Deduplicação sugerida: chave normalizada (número + ano + título + tipo de publicação), preservando retificações como documentos do mesmo edital.  
Ruídos: menu institucional, licitações, transparência, Nossa Bolsa, cookies e iframes sociais.

### API/XHR
Endpoint/método/parâmetros/paginação/JSON path: UNKNOWN; não há evidência de API pública no HTML pesquisado.  
Autenticação: não para páginas/PDFs; submissões podem exigir SigFAPES.  
Observações: o site informa “seu navegador não tem suporte a JavaScript”, mas o conteúdo da categoria é entregue em HTML. Footer identifica PRODEST e software Orchard.

### Tecnologia
Tipo: SERVER_RENDERED, OTHER (Orchard/PRODEST).  
HTTP funciona: SIM para listagem/PDF.  
JS necessário: NÃO para leitura.  
Playwright necessário: NÃO.

### Bloqueios
HTTP: nenhum bloqueio observado via página indexada. Browser: não necessário. WAF/Cloudflare/CAPTCHA: não observado. Alternativa: categorias oficiais e PDFs.

### Quality gate
ACEITAR SE: título/texto disser contratação, cargo, emprego, estágio, seleção simplificada de pessoa ou servidor temporário.  
REJEITAR SE: bolsa, auxílio, fomento, proposta/projeto, chamada científica/internacional, premiação, evento, startup ou Nossa Bolsa de estudante.

### Empty evidence
`EMPTY_EXPLICIT` para o universo de seleção de pessoal atual não é declarado literalmente. Evidência é observacional: as categorias abertas consultadas exibem somente fomento/bolsas/propostas; portanto `OUT_OF_SCOPE`/`UNKNOWN_EMPTY`, não zero global de editais.

### Estratégia recomendada
`CONFIGURABLE_HTML` + `INSTITUTIONAL_FILTER_REQUIRED` + `KEEP_EMPTY`.

### Instruções para Codex
1. Usar as categorias oficiais e seguir links de “Baixar” para PDFs; não usar apenas `/editais` como se fosse uma lista plana.  
2. Classificar por título/descrição e descartar bolsas, auxílio, pesquisa, inovação, eventos, chamadas internacionais e seleção de propostas.  
3. Preservar PDF e data da linha; não gerar `active=0` para um item desconhecido.  
4. Fazer teste live com PIC Jr 2027 garantindo exclusão por fora do escopo e com eventual edital futuro explicitamente de contratação.

### Confidence
HIGH — páginas oficiais, categorias e tecnologia Orchard visíveis; não há evidência de seleção de pessoal corrente.

### Evidências
https://fapes.es.gov.br/editais  
https://fapes.es.gov.br/edital-aberto-forma%C3%A7%C3%A3o-cient%C3%ADfica  
https://fapes.es.gov.br/Editais/Encerrados  
https://fapes.es.gov.br/Editais/Resultados

## 67 — FAPESQ (PB)

Identificador técnico: `fapesq_selection`  
URL fornecida: https://fapesq.rpp.br/editais/  
URL oficial confirmada: https://fapesq.rpp.br/editais/editais-2026 (a página raiz apresenta erro/cache miss em algumas requisições; a coleção anual é acessível).  
Portal ativo: SIM/PARCIAL. URL mudou: NÃO.

### Navegação
Homepage: https://fapesq.rpp.br/  
Abertos/anos: https://fapesq.rpp.br/editais/editais-2026 e links de anos anteriores.  
Em andamento: a própria coleção 2026 mistura edital inicial, retificação, homologação e resultados; não há página global confiável separando somente ativos.  
Encerrados: não confirmada uma URL dedicada; estados aparecem no título da publicação.  
Detalhe: https://fapesq.rpp.br/editais/2026/edital-no-58-2026-2013-processo-seletivo-para-contratacao-de-coordenadores-audiovisuais-equipe-tecnica-e-cadastro-de-reserva-cr-dos-nucleos-de-inovacao-estadual-da-paraiba-nie-pb  
Documentos: páginas de item com iframe/arquivo PDF e URLs `@@download/file/...`.

### Universo observado
Observed: coleção 2026 paginada por `?b_start:int=N`; várias páginas, total global `UNKNOWN`.  
Relevant: pelo menos os editais explicitamente de equipe/pessoal observados: 58 (coordenadores/equipe técnica), 57 (oficineiros/avaliadores), 55 (equipe técnica), 51 (professores), 48 (pesquisadores bolsistas), 47 (apoio técnico/extensionistas), 10/11 (pesquisadores); total `UNKNOWN`.  
Active: `UNKNOWN`: páginas recentes têm homologações/classificações e não permitem afirmar quantos processos ainda aceitam inscrição.  
Closed: UNKNOWN.  
Out of scope: concessão de bolsas sem seleção de função, fomento, mobilidade, eventos, prêmio, propostas e bolsas de permanência; seleção de estudantes deve ser separada de contratação.

### Listagem
Estrutura: página Plone/HTML com breadcrumb, título “Editais 2026”, cada item em heading/título com data de publicação e link “Arquivo”; páginas paginadas usam `b_start:int`.  
Selector/container: não fixar seletor sem inspeção local; usar links de item dentro do conteúdo principal e ignorar menu/breadcrumb.  
Título/link/status: título inclui número, tipo e estágio entre parênteses (Retificado, Homologação, Resultado Preliminar/Final).  
ID: número do edital no título; sem atributo interno confirmado.

### Paginação
Método: offset Plone `?b_start:int=0`, `80`, `160`, `240`, `340`, `420`, `440`, `460` observados nos resultados oficiais.  
Parâmetros: `b_start:int`; avançar até não haver link/itens novos e deduplicar publicações do mesmo edital.

### Exemplo real
Título: EDITAL Nº 58/2026 — Processo seletivo para contratação de coordenadores audiovisuais, equipe técnica e cadastro de reserva dos Núcleos de Inovação Estadual da Paraíba.  
Órgão: FAPESQ/SECTIES/PB.  
Status: publicação de homologação/interposição; processo de pessoal, estágio atual não necessariamente aberto.  
URL: página de detalhe acima.  
Edital: arquivos PDF na própria página (inclui versão inicial, retificação e resultados).

### Campos
titulo: HTML (heading do item/detalhe).  
orgao: HTML/PDF.  
modalidade: HTML/PDF (processo seletivo, equipe, professor etc.).  
area/cargo/vagas/escolaridade/taxa/prova_data: PDF do edital.  
cidade/uf: HTML/PDF quando indicado; não disponível de forma uniforme.  
status: HTML (sufixo do título: homologação, resultado, retificado) + leitura de cronograma PDF.  
edital_numero/data: HTML (título e “publicado”) e PDF.  
inscricao_inicio/fim: PDF; não assumí datas da data de publicação.  
link_edital: HTML (Arquivo/iframe PDF).  
link_inscricao: PDF/SIGFAPESQ quando o edital exigir; autenticação pode ser necessária.

### Publicações
Estrutura: uma página de detalhe pode conter vários arquivos/documentos; coleção anual também replica o mesmo edital como notícia e como resultado.  
Tipos: edital, retificação, homologação, recurso, classificação preliminar/final, resultado.  
Selector/API: links HTML e iframe PDF.  
Deduplicação sugerida: número/ano + slug do edital + tipo de publicação; preservar versões com data.  
Ruídos: chamadas científicas, bolsas, concursos de ideias, menus, links de anos e documentos repetidos.

### API/XHR
Endpoint: nenhum endpoint JSON público confirmado.  
Método/parâmetros: GET HTML; offset `b_start:int`.  
JSON path/autenticação: não aplicável à listagem; SIGFAPESQ pode exigir login para inscrição.  
Observações: convenções `@@download/file`, `b_start:int` e breadcrumbs são compatíveis com Plone; tratar como evidência de plataforma, mas validar no runtime antes de acoplar.

### Tecnologia
Tipo: SERVER_RENDERED, PDF_INDEX, OTHER (Plone-like).  
HTTP funciona: SIM para páginas e PDFs (raiz teve falha/cache miss intermitente).  
JS necessário: NÃO para conteúdo indexado.  
Playwright necessário: NÃO para listagem; pode ser necessário apenas para fluxo autenticado SIGFAPESQ.

### Bloqueios
HTTP: a raiz `/editais/` retornou falha de cache em uma tentativa; páginas anuais funcionam. Browser: conteúdo pesquisável. WAF/Cloudflare/CAPTCHA: não observado. Alternativas: coleções anuais e busca interna oficial.

### Quality gate
ACEITAR SE: edital explicita contratação, equipe técnica, professor/oficineiro/pesquisador em função, apoio técnico/extensionista ou outro vínculo de trabalho/serviço.  
REJEITAR SE: bolsa como benefício sem função, mobilidade estudantil, permanência, auxílio, prêmio, chamada de propostas/projeto, evento ou inovação sem seleção de pessoas.

### Empty evidence
Não vazio: há muitas publicações atuais e evidências de seleção de pessoal. `Active=UNKNOWN` porque a coleção mistura fases e não fornece um contador de processos abertos.

### Estratégia recomendada
`CONFIGURABLE_HTML` com paginação por `b_start:int` e `INSTITUTIONAL_FILTER_REQUIRED`; `HYBRID` para baixar PDFs e ler cronograma.

### Instruções para Codex
1. Percorrer `/editais/editais-2026` e anos anteriores via `b_start:int`, parando quando não houver itens.  
2. Extrair títulos/links de arquivos do conteúdo principal e deduplicar por número/ano/tipo.  
3. Marcar status por texto do título e, quando necessário, cronograma PDF; não inferir ativo somente pela página 2026.  
4. Aplicar filtro de pessoal: aceitar 58, 57, 55, 51, 48, 47, 10/11; descartar bolsas/fomento/mobilidade/prêmios.  
5. Testar paginação, retificação, publicação de resultado e um PDF com datas.

### Confidence
MEDIUM — estrutura e URLs oficiais reproduzíveis; contagem/estado ativo exigem leitura de todos os offsets e cronogramas.

### Evidências
https://fapesq.rpp.br/editais/editais-2026  
https://fapesq.rpp.br/editais/2026/edital-no-58-2026-2013-processo-seletivo-para-contratacao-de-coordenadores-audiovisuais-equipe-tecnica-e-cadastro-de-reserva-cr-dos-nucleos-de-inovacao-estadual-da-paraiba-nie-pb  
https://fapesq.rpp.br/editais/editais-2026/?b_start%3Aint=460

## 68 — Fundação Uniselva

Identificador técnico: `uniselva_selection`  
URL fornecida: https://inscricao.fundacaouniselva.org.br/selecoes  
URL oficial confirmada: https://web.fundacaouniselva.org.br/frmSelecoes.aspx (a URL fornecida abre o Portal de Inscrição, mas a listagem pública reproduzível e os PDFs estão no domínio `web`).  
Portal ativo: SIM/PARCIAL. URL mudou: SIM (interface de inscrição separada da listagem pública).

### Navegação
Homepage institucional: https://www.fundacaouniselva.org.br/  
Listagem: https://web.fundacaouniselva.org.br/frmSelecoes.aspx  
Detalhe: https://web.fundacaouniselva.org.br/frmSelecao.aspx?_id=1261 (exemplo).  
Documentos: `/Editais/<timestamp>_<id>.pdf`.  
Encerrados/histórico: misturados na mesma tabela; não foram confirmadas páginas separadas.

### Universo observado
Observed: tabela pública com dezenas de seleções 2025–2026; total `UNKNOWN`.  
Relevant: múltiplas contratações CLT, autônomos, professores temporários, estágios e funções de projeto; total `UNKNOWN`.  
Active: `UNKNOWN`; os itens mais recentes indexados (017/2026, banco de currículos 001/2026) tinham períodos encerrados em abril/2026, mas o site não apresenta contador de estado atual.  
Closed: `UNKNOWN`.  
Out of scope: chamadas/bolsas sem contratação; separar “contratação de bolsista” conforme texto do edital e regras do projeto.

### Listagem
Estrutura: tabela “Seleção | Área de formação | Período de inscrição | Info” em ASP.NET WebForms; linhas incluem título, área e datas.  
Selector/container: estrutura recorrente de tabela; seletor exato não confirmado.  
Título/link: título/“Info” leva a `frmSelecao.aspx?_id=<id>`.  
ID: parâmetro `_id` no detalhe; documentos têm timestamp e id no nome.  
Status: não há coluna explícita de status; derive somente do período/etapas descritas.

### Paginação
Método: não observada na listagem pública indexada; tabela parece carregar todos ou filtrar por campo “Pesquisar”.  
Parâmetros: pesquisa visual sem endpoint conhecido.

### Exemplo real
Título: EDITAL 017/2026 CONTRATAÇÃO DE ESTAGIÁRIO(A) — Secretariado, Administração ou Comunicação Social.  
Órgão: Fundação Uniselva.  
Status: período publicado 23/02/2026–10/04/2026 (encerrado na data da pesquisa).  
URL: https://web.fundacaouniselva.org.br/frmSelecoes.aspx  
Edital: link “Info”/detalhe e PDF na página.

### Campos
titulo/area/inscricao_inicio/fim: HTML (células da tabela).  
orgao: HTML/PDF.  
modalidade/cargo/escolaridade/vagas/salário/prova_data: PDF do edital/detalhe.  
cidade/uf: PDF (ex.: IFMT/MT).  
status: HTML/PDF por período e cronograma; não há badge uniforme.  
edital_numero/data: HTML/PDF.  
link_edital: HTML, PDF em `/Editais/`.  
link_inscricao: detalhe/formulário da seleção; pode ser e-mail ou formulário eletrônico conforme edital.

### Publicações
Estrutura: detalhe/PDF concentra edital, cronograma, resultados preliminar/final, recursos e convocação; listagem não separa publicações.  
Tipos: edital, retificação, resultado, convocação, anexos.  
Deduplicação sugerida: `_id` do detalhe + nome/tipo do PDF.  
Ruídos: login, sistemas (transparência, compras, licitação), menu, imagens “Aguarde”.

### API/XHR
Endpoint: não confirmado.  
Método: GET HTML/WebForms; parâmetros conhecidos `_id` no detalhe.  
Paginação/JSON path: UNKNOWN.  
Autenticação: listagem e PDFs públicos; envio pode exigir formulário/e-mail.  
Observações: a URL fornecida exibe portal de inscrição/iframe sem a tabela na resposta textual; usar `web.fundacaouniselva.org.br/frmSelecoes.aspx` como discovery.

### Tecnologia
Tipo: SERVER_RENDERED, OTHER (ASP.NET WebForms; `frmSelecoes.aspx`, `frmSelecao.aspx`).  
HTTP funciona: PARCIAL (domínio `web`); URL `inscricao` exige renderização/iframe para o portal.  
JS necessário: NÃO para tabela pública `web`; SIM/PARCIAL para portal de inscrição.  
Playwright necessário: provável apenas para a interface `inscricao`, não para discovery.

### Bloqueios
HTTP: nenhuma resposta 403/429 confirmada; `inscricao` não expôs a listagem na captura textual. Browser: portal de inscrição pode exigir. WAF/CAPTCHA: não observado. Alternativa: domínio `web` e PDFs públicos.

### Quality gate
ACEITAR SE: título/PDF indicar contratação CLT, celetista, autônomo, estágio, professor temporário, analista, técnico, cargo/função e cronograma de candidatura.  
REJEITAR SE: somente bolsa de pesquisa/auxílio sem função contratual ou edital de projeto sem seleção de pessoa.

### Empty evidence
`UNKNOWN_EMPTY`: há listagem pública e numerosos itens, mas não há marcador consistente de ativos; não declarar vazio.

### Estratégia recomendada
`CONFIGURABLE_HTML` no domínio `web` + `HYBRID`/`PLAYWRIGHT` somente se a interface de inscrição for necessária.

### Instruções para Codex
1. Descobrir na tabela de `frmSelecoes.aspx`, capturando título, área, período e link `frmSelecao.aspx?_id=...`.  
2. Abrir detalhe e PDFs `/Editais/` para cargos, vagas, remuneração e documentos.  
3. Determinar ativo pelas datas e cronograma, não pela existência da linha.  
4. Usar `inscricao.fundacaouniselva.org.br/selecoes` somente como alternativa para links/formulários.  
5. Testar uma seleção CLT, uma de estágio e uma bolsa para garantir exclusão correta.

### Confidence
MEDIUM — migração/interface alternativa e ASP.NET são reproduzíveis; estado atual e paginação não estão explícitos.

### Evidências
https://web.fundacaouniselva.org.br/frmSelecoes.aspx  
https://web.fundacaouniselva.org.br/frmSelecao.aspx?_id=1261  
https://inscricao.fundacaouniselva.org.br/selecoes

## 69 — Fundação FAFIPA

Identificador técnico: `fafipa_open`  
URL fornecida: https://concursos.fundacaofafipa.org.br/  
URL oficial confirmada: https://fafipa.selecao.net.br/ (a URL fornecida e `fundacaofafipa.org.br` são interfaces/domínios antigos; a listagem corrente indexa `fafipa.selecao.net.br`).  
Portal ativo: SIM. URL mudou: SIM.

### Navegação
Homepage/listagem atual: https://fafipa.selecao.net.br/  
Em andamento: `/index/1/?pg=1&pp=20` e páginas seguintes.  
Inscrições abertas: link de menu, mesma família `/index/1`.  
Homologado: `/index/3/` (parâmetro `pg`).  
Finalizado/suspenso/cancelado: estados de menu em interfaces legadas; não misturar com em andamento.  
Detalhe: link do título de cada concurso.  
Documentos: detalhe do certame, atos oficiais e editais.

### Universo observado
Observed: a consulta oficial mostra “Mostrando 1–18 de 42” em Em andamento.  
Relevant: 42 processos/concurso em andamento na listagem; todos são seleções de pessoal público/emprego.  
Active: 42 em andamento no portal; isso não significa que todos ainda aceitem inscrição (datas devem ser verificadas).  
Closed: outros estados/páginas, total `UNKNOWN`.  
Out of scope: menu institucional, atos gerais e licitações; não há bolsa científica no universo da organizadora.

### Listagem
Estrutura: cards/blocos HTML server-rendered; cada item exibe tipo (“Concurso Público”/“Processo Seletivo”), título, órgão, edital, datas de inscrição/isencão e data de prova.  
Selector/container: seletor CSS não confirmado; usar os blocos de conteúdo principal e links dos títulos.  
Título/link: heading do item é link para detalhe.  
ID: não exposto no texto; edital e slug formam identificador estável.  
Status: seção/rota (`index/1`, `index/3`) e rótulo “Inscrições Abertas!” quando presente.

### Paginação
Método: parâmetros `pg` (página) e `pp` (itens por página); exemplo `https://fafipa.selecao.net.br/index/1/?pg=1&pp=20`, consulta oficial mostra `pg=2`.  
Parâmetros: `pg`, `pp`, e busca `q`/`dir`/`ord` vistos em URLs indexadas; percorrer até o contador “Mostrando … de 42”.

### Exemplo real
Título: Concurso para Emprego Público do Município de Água Comprida – MG.  
Órgão: Município de Água Comprida/MG.  
Status: Em andamento; inscrições 28/07/2026–27/08/2026; prova 27/09/2026; Edital 001/2026.  
URL: https://fafipa.selecao.net.br/ (link do título no card).  
Edital: link/documentos dentro do detalhe.

### Campos
titulo/orgao/status/inscricao_inicio/fim/prova_data/edital_numero: HTML do card.  
modalidade: HTML (“Concurso Público”/“Processo Seletivo”).  
cargo/area/vagas/salário/escolaridade/taxa: detalhe/PDF.  
cidade/uf: HTML no título/órgão e detalhe.  
edital_data: detalhe/PDF.  
link_edital: detalhe/documentos; link_inscricao: detalhe/portal de candidato.  
Classificação: HTML para resumo; PDF para campos não resumidos.

### Publicações
Estrutura: detalhe e menu “Atos Oficiais”; editais, retificações, gabaritos/resultados e convocações podem ser documentos.  
Tipos: edital, retificação, prova, gabarito, resultado, homologação, convocação.  
Selector/API: links HTML; endpoint JSON não confirmado.  
Deduplicação: chave por órgão + edital + tipo/documento; evitar duplicar cards de modalidades do mesmo órgão.  
Ruídos: login/Área do Candidato, SAC, busca, chamadas internas e menus.

### API/XHR
Endpoint: nenhum confirmado.  
Método: GET HTML com `pg`/`pp`.  
Paginação: `pg`, `pp`; JSON path/auth: não aplicável.  
Observações: infraestrutura é `selecao.net.br`, potencial cluster com ACCESS/ABCP/RBO/Avança SP; validar diferenças de tenant antes de compartilhar parser.

### Tecnologia
Tipo: SERVER_RENDERED, OTHER (plataforma white-label `selecao.net.br`).  
HTTP funciona: SIM.  
JS necessário: NÃO para cards.  
Playwright necessário: NÃO.

### Bloqueios
HTTP/browser: sem bloqueio observado nas páginas indexadas. WAF/Cloudflare/CAPTCHA: não observado. Alternativa: domínios `fafipa.selecao.net.br` e legados `fundacaofafipa.org.br`.

### Quality gate
ACEITAR SE: bloco é Concurso Público/Processo Seletivo/Emprego Público e tem órgão, edital ou datas de candidato.  
REJEITAR SE: links institucionais, atos não relacionados ao certame, licitações ou chamadas internas.

### Empty evidence
Não vazio: “Em andamento” com 42 itens e contador explícito; não declarar empty mesmo que inscrições de parte estejam encerradas.

### Estratégia recomendada
`CONFIGURABLE_HTML` (com possibilidade de conector compartilhado `selecao.net.br`).

### Instruções para Codex
1. Migrar discovery para `https://fafipa.selecao.net.br/index/1/`.  
2. Percorrer `pg` até o contador; manter `pp` fixo e deduplicar.  
3. Extrair tipo/título/órgão/edital/datas do card e abrir detalhe para PDFs e cargos.  
4. Não considerar “Em andamento” como inscrição aberta sem conferir período.  
5. Criar teste com página 1 e 2, item de Processo Seletivo e item com “Inscrições Abertas!”.

### Confidence
HIGH — migração, paginação e contador reproduzidos no portal oficial.

### Evidências
https://fafipa.selecao.net.br/  
https://fafipa.selecao.net.br/index/1/?pg=1&pp=20  
https://fafipa.selecao.net.br/index/1/?pg=2&pp=22  
https://concursos.fundacaofafipa.org.br/

## 70 — IESES

Identificador técnico: `ieses_open`  
URL fornecida: https://ieses.org/projetos  
URL oficial confirmada: https://www.concursos.ieses.org/ (a URL institucional `ieses.org/projetos` é o portal-base; projetos também são publicados em tenants `*.ieses.org`, como `https://ibhases.ieses.org/`).  
Portal ativo: SIM/PARCIAL. URL mudou: SIM (subdomínios por projeto/entidade).

### Navegação
Homepage: https://ieses.org/  
Projetos: https://www.concursos.ieses.org/ e https://ieses.org/projetos  
Exemplos tenant: https://ibhases.ieses.org/; `https://msgas2025.ieses.org/projetos`; `https://gaspar.ieses.org/projetos`.  
Detalhe: botão “Ver detalhes” dos cards do projeto; rota exata varia por tenant.  
Documentos/resultados: página do tenant/projeto, normalmente links de edital e comunicados.

### Universo observado
Observed: base retorna shell com “Últimos Projetos”, busca e botão “Carregar mais”; tenants indexados mostram pelo menos 12 projetos.  
Relevant: projetos explicitamente Concurso Público/Processo Seletivo (CRMVSC, IBHASES, SCGAS, TJPA, MSGÁS, CRC-SC etc.); total `UNKNOWN`.  
Active: `UNKNOWN`; a lista não mostra status uniforme.  
Closed: UNKNOWN.  
Out of scope: notícias, cursos e páginas não relacionadas ao processo do projeto.

### Listagem
Estrutura: cards com logo da entidade, nome, tipo/número do edital, “Ver detalhes” e botão “Carregar mais projetos”; busca por projeto/entidade.  
Selector/container: não confirmado porque resposta HTTP textual do portal-base expõe apenas shell.  
Título/link/status: card/título e detalhe; status não uniforme no card.  
ID: não observado.

### Paginação
Método: botão “Carregar mais projetos” (infinite/load-more provável), sem parâmetro público confirmado.  
Parâmetros/API: UNKNOWN; não inventar endpoint.

### Exemplo real
Título: PROCESSO SELETIVO PÚBLICO – EDITAL 001/2026 (IBHASES).  
Órgão: Instituto Beneficente de Habitação, Assistência Social, Educação e Saúde.  
Status: projeto publicado; estado deve ser conferido na página do tenant.  
URL: https://ibhases.ieses.org/  
Edital: página do projeto/tenant.

### Campos
titulo/orgao/modalidade: HTML após renderização do card/tenant.  
status: detalhe/HTML; não uniforme.  
cargo/area/cidade/UF/vagas/salário/escolaridade/taxa/prova_data/inscricao_inicio/fim: detalhe e PDF (quando disponíveis).  
edital_numero: HTML (ex.: 001/2026).  
link_edital/link_inscricao: detalhe/tenant; tipo PDF ou formulário externo.

### Publicações
Estrutura: por projeto/tenant, com editais e atos específicos; resultados/gabaritos tendem a ficar no detalhe.  
Tipos: edital, retificação, resultados, gabarito, convocação.  
Selector/API: desconhecido; exige inspeção de rede.  
Deduplicação: tenant + entidade + edital + tipo.  
Ruídos: logo, notícias, busca, menu e projetos antigos.

### API/XHR
Endpoint: UNKNOWN.  
Método/paginação/JSON path: UNKNOWN; botão “Carregar mais” indica chamada dinâmica, mas não se deve presumir URL.  
Auth: não aparente para listagem; candidatura pode ter portal próprio.  
Observação: HTTP simples devolve headings/input/button sem cards; conteúdo completo aparece em resultados indexados/tenant, indicando JS.

### Tecnologia
Tipo: REACT_SPA/OTHER provável (não confirmado; shell + load-more).  
HTTP funciona: PARCIAL.  
JS necessário: SIM.  
Playwright necessário: SIM/PROVÁVEL para discovery, salvo endpoint descoberto em runtime.

### Bloqueios
HTTP: shell vazio na resposta textual. Browser: necessário para cards. WAF/Cloudflare/CAPTCHA: não observado. Alternativa: tenants `*.ieses.org` e subdomínio `www.concursos.ieses.org`.

### Quality gate
ACEITAR SE: projeto/tenant explicitar concurso público ou processo seletivo de pessoal, com edital e órgão.  
REJEITAR SE: curso, notícia, projeto sem seleção de candidatos ou conteúdo não relacionado.

### Empty evidence
`UNKNOWN_EMPTY`: shell vazio não prova vazio; não usar como empty.

### Estratégia recomendada
`PLAYWRIGHT` ou `HYBRID`; preferir XHR/API somente após observar a chamada real do botão.

### Instruções para Codex
1. Abrir o portal-base com browser e registrar a chamada gerada por busca/carregar mais.  
2. Percorrer todos os cards até o botão desaparecer; guardar tenant, entidade e link de detalhe.  
3. Abrir tenant/detalhe e extrair edital/documentos; não derivar endpoint.  
4. Testar `ibhases.ieses.org`, CRMVSC e SCGAS para diferenças de tenant.  
5. Adicionar fixture para shell HTTP e para cards renderizados.

### Confidence
MEDIUM — existência de SPA/load-more e tenants é reproduzida; endpoint e status ativo continuam desconhecidos.

### Evidências
https://ieses.org/projetos  
https://www.concursos.ieses.org/  
https://ibhases.ieses.org/  
https://msgas2025.ieses.org/projetos

## 71 — FUNPEC

Identificador técnico: `funpec_selection`  
URL fornecida: https://funpec.br/processos-seletivos/  
URL oficial confirmada: https://funpec.br/processos-seletivos/  
Portal ativo: SIM. URL mudou: NÃO.

### Navegação
Homepage: https://funpec.br/  
Novos: https://funpec.br/processos-seletivos/novos/  
Em andamento: https://funpec.br/processos-seletivos/em-andamento/  
Encerrados: https://funpec.br/processos-seletivos/encerrados/  
Bolsistas (separado): link “Bolsistas” no menu.  
Detalhe: `/processo-seletivo/<slug>/`.  
Seleções públicas de fornecedores/compras: https://funpec.br/selecoes-publicas/ — fora do escopo.

### Universo observado
Observed: 3 itens em “Novos”, 6 em “Em andamento” e página de encerrados com 77 itens (contador/resultado oficial indexado); a página geral tem paginação.  
Relevant: processos de pessoal nos 3 novos + 6 em andamento; encerrados também são processos de pessoal.  
Active: 6 em andamento; 3 novos têm edital aberto e devem ser tratados como potencialmente ativos após validar cronograma.  
Closed: 77 exibidos pela página de encerrados.  
Out of scope: `/bolsistas/` (bolsas de pesquisa) e `/selecoes-publicas/` (compras/serviços).

### Listagem
Estrutura: lista de links/títulos em HTML, com páginas numeradas; categoria fornece semântica de estado.  
Selector/container: seletor CSS não confirmado; usar links no conteúdo principal.  
Título/link: slug de detalhe.  
ID: número no título (ex.: 12/2026).  
Status: rota Novo/Em andamento/Encerrados.

### Paginação
Método: paginação numerada; página geral mostra 1–9, encerrados 1–8.  
Parâmetros: links de páginas; valores exatos não reproduzidos, seguir hrefs em vez de inventar query.

### Exemplo real
Título: PROCESSO SELETIVO 12/2026 — CUIDADOR EM SAÚDE – NEI (CADASTRO DE RESERVA).  
Órgão: FUNPEC/UFRN/projeto NEI.  
Status: novo (edital aberto; categoria “Novos”).  
URL: https://funpec.br/processo-seletivo/processo-seletivo-12-2026-cuidador-em-saude-nei-cadastro-de-reserva/  
Edital: link `EDITAL 13/2026` na página de detalhe.

### Campos
titulo/status: HTML (lista/rota e detalhe).  
orgao/modalidade/cargo/área/vagas/salário/escolaridade/taxa/prova_data/inscrições: detalhe/PDF do edital.  
cidade/UF: PDF/projeto.  
edital_numero: HTML e PDF.  
link_edital: HTML (link de PDF).  
link_inscricao: PDF/detalhe; não há formulário universal exposto na lista.

### Publicações
Estrutura: detalhe lista edital e documentos; resultados/retificações podem ser PDFs anexos.  
Tipos: edital, retificação, convocação, resultado, recursos.  
Selector/API: HTML/PDF; sem endpoint público confirmado.  
Deduplicação: número/ano + cargo + projeto + tipo.  
Ruídos: Bolsistas, Compras, Licitações, Serviços Nacionais/Internacionais, cookies, WhatsApp e menus.

### API/XHR
Endpoint: não confirmado.  
Método: GET HTML; paginação via links.  
Autenticação: não para páginas/PDFs; área do coordenador é separada.  
Observações: WordPress não foi formalmente confirmado no texto; trate como HTML server-rendered até validar headers/fonte.

### Tecnologia
Tipo: SERVER_RENDERED, PDF_INDEX, OTHER.  
HTTP funciona: SIM.  
JS necessário: NÃO.  
Playwright necessário: NÃO.

### Bloqueios
Sem 403/429/WAF/CAPTCHA observados. API alternativa: não encontrada. Página de Bolsistas e Seleções Públicas são alternativas institucionais, mas não devem ser misturadas.

### Quality gate
ACEITAR SE: rota/categoria de Processo Seletivo e título indicar cargo/função/contratação/estágio ou cadastro de reserva.  
REJEITAR SE: Bolsistas, bolsa de pesquisa, compra de equipamentos, fornecedor, cotação ou serviço.

### Empty evidence
Não vazio: 6 em andamento e 3 novos. Encerrados têm 77 na página oficial.

### Estratégia recomendada
`CONFIGURABLE_HTML` com rotas de estado e paginação; filtro institucional obrigatório.

### Instruções para Codex
1. Consultar separadamente `/novos/`, `/em-andamento/` e `/encerrados/`; seguir paginação completa.  
2. Abrir cada slug e baixar link `EDITAL`; extrair cargos/datas do PDF.  
3. Excluir `/bolsistas/` e `/selecoes-publicas/` do conector.  
4. Não contar 3 “Novos” como ativos sem checar cronograma.  
5. Testar 12/2026, um encerrado 07/2026 e um item rejeitado de Bolsistas.

### Confidence
HIGH — rotas, categorias, itens e separação de bolsistas/compras confirmados oficialmente.

### Evidências
https://funpec.br/processos-seletivos/  
https://funpec.br/processos-seletivos/novos/  
https://funpec.br/processos-seletivos/em-andamento/  
https://funpec.br/processos-seletivos/encerrados/  
https://funpec.br/processo-seletivo/processo-seletivo-12-2026-cuidador-em-saude-nei-cadastro-de-reserva/

## 72 — FADE-UFPE

Identificador técnico: `fade_selection`  
URL fornecida: https://fade.org.br  
URL oficial confirmada: https://fade.org.br/category/editais/  
Portal ativo: SIM. URL mudou: NÃO.

### Navegação
Homepage: https://fade.org.br/  
Editais: https://fade.org.br/category/editais/  
Em andamento: link de categoria na página; posts são marcados “Em andamento”.  
Inscrições abertas: link de categoria “Inscrições Abertas”.  
Finalizados: categoria “Finalizados”.  
Fornecedores/seleção pública: `sistemas.fade.org.br` (fora do escopo de pessoal).  
Detalhe: post WordPress individual; PDFs em `wp-content/uploads`.

### Universo observado
Observed: categoria de Editais com paginação de pelo menos 67 páginas, 10 posts na primeira e 10 na segunda página.  
Relevant: posts para estágio, auxiliar, analista, engenheiro, professor, prestador e bolsista; excluir bolsas puramente científicas conforme regra.  
Active: `UNKNOWN` no total; primeira página mostra vários posts marcados Em andamento/Inscrições Abertas, incluindo 089/2026 bolsista, 088/2026 estágio, 087/2026 DevOps, 085/2026 engenheiro e 084/2026 estágio.  
Closed: `UNKNOWN` (categoria Finalizados).  
Out of scope: fornecedores, seleção pública de compras, exames, projetos sem seleção de pessoa e bolsas de pesquisa quando não forem contratação/função.

### Listagem
Estrutura: WordPress archive com posts; cada item mostra autor/data, título `h2`, resumo, categorias (Editais/Em andamento/Finalizados/Inscrições Abertas) e “Read More”.  
Selector/container: estrutura WordPress/ColorMag; usar links dos posts e categorias, não inventar classe.  
Título/link/status: HTML do post e categoria.  
ID: slug/permalink WordPress.

### Paginação
Método: `/category/editais/page/2/` e link Anterior/Próximo; resultado indica 67 páginas.  
Parâmetros: número no caminho `/page/N/`.

### Exemplo real
Título: Estágio em Análise de Processos – Rotinas Financeiras | Cadastro Reserva | Edital 088/2026.  
Órgão: Fade-UFPE.  
Status: Em andamento/Inscrições Abertas (categoria da primeira página).  
URL: https://fade.org.br/category/editais/ (link do post).  
Edital: post individual e PDF/anexos.

### Campos
titulo/status: HTML do archive/post/categorias.  
orgao: HTML/resumo.  
modalidade/cargo/área/cidade/UF/vagas/salário/escolaridade/taxa/prova: post e PDF.  
edital_numero/data: título/post/PDF.  
inscricao_inicio/fim: resumo ou PDF.  
link_edital: post/PDF em `wp-content/uploads`.  
link_inscricao: post, formulário ou instrução do PDF.

### Publicações
Estrutura: post individual com edital, anexos, convocações e resultados; categorias de estado e tags.  
Tipos: edital, retificação, resultado, cancelamento, convocação, anexos.  
Selector/API: WordPress HTML; REST API não confirmada.  
Deduplicação: permalink/slug + número do edital; preservar atualizações do post e PDFs.  
Ruídos: projetos/notícias, fornecedores, exames, autores, comentários e menus.

### API/XHR
Endpoint: nenhum `wp-json` confirmado.  
Método/paginação: GET archive `/category/editais/page/N/`.  
JSON/auth: não aplicável para conteúdo público.

### Tecnologia
Tipo: WORDPRESS, SERVER_RENDERED, PDF_INDEX. Footer confirma tema ColorMag e WordPress.  
HTTP funciona: SIM.  
JS necessário: NÃO.  
Playwright necessário: NÃO.

### Bloqueios
HTTP/browser: sem bloqueios observados. WAF/Cloudflare/CAPTCHA: não observado. Alternativa: sistema `sistemas.fade.org.br` apenas para fornecedores.

### Quality gate
ACEITAR SE: post/categoria indicar contratação, emprego, estágio, cargo, prestação de serviço pessoal ou processo seletivo de pessoa.  
REJEITAR SE: seleção pública de fornecedor, compra, exame, evento ou bolsa de pesquisa sem vínculo/função.

### Empty evidence
Não vazio: páginas 1–2 têm posts atuais; não usar categoria Finalizados como prova de vazio geral.

### Estratégia recomendada
`WORDPRESS_API` se API pública for confirmada no runtime; caso contrário `CONFIGURABLE_HTML` com archive pagination.

### Instruções para Codex
1. Percorrer `/category/editais/` e `/page/N/` até o fim; também consultar categorias Em andamento/Inscrições Abertas.  
2. Extrair categorias e permalink; abrir post e PDFs.  
3. Excluir fornecedores/seleções públicas em `sistemas.fade.org.br` e bolsas sem função.  
4. Testar 088/2026, 087/2026 e um Finalizado; validar datas no PDF.

### Confidence
HIGH — WordPress, paginação, categorias e exemplos atuais confirmados; contagem de ativos permanece desconhecida.

### Evidências
https://fade.org.br/category/editais/  
https://fade.org.br/category/editais/page/2/  
https://fade.org.br/wp-content/uploads/2026/04/Edital-042_2026.pdf

## 73 — FAPEX

Identificador técnico: `fapex_selection`  
URL fornecida: https://master.fapex.org.br/portalrh/  
URL oficial confirmada: https://fapex.org.br/Fapex/Site/Principal/Edital/index (editais públicos); para vagas correntes, https://fapex.pandape.infojobs.com.br/ é o “Trabalhe Conosco” oficial. `portalrh` fornecido é login de empregado, não discovery público.  
Portal ativo: SIM/PARCIAL. URL mudou: SIM (portal RH não é a listagem pública).

### Navegação
Portal RH fornecido: login CPF/senha, cadastro e recuperação; não há vagas públicas.  
Editais: https://fapex.org.br/Fapex/Site/Principal/Edital/index  
Trabalhe conosco: https://fapex.pandape.infojobs.com.br/  
Detalhe: link “DETALHE” nos editais ou vaga no Pandapé.  
Documentos: PDFs em `fapex.org.br/Fapex/Harp/sys/web/pub/arquivos/pdf/...`.

### Universo observado
Observed: portal RH fornece somente autenticação; arquivo público de Editais lista seleções de estagiários, monitores, professores, tutores e prestadores (muitos anos; total `UNKNOWN`); Pandapé informa “50 vagas de emprego”.  
Relevant: editais de contratação/estágio/monitoria/prestação de pessoa + 50 vagas Pandapé; total global `UNKNOWN`.  
Active: 50 vagas no Pandapé na data observada; estado dos editais históricos não é uniforme.  
Closed: UNKNOWN.  
Out of scope: licitações/Seleção Pública Eletrônica de fornecedores, Portal RH autenticado, bolsas de pesquisa sem função.

### Listagem
Editais: archive server-rendered com título, descrição, “DETALHE/EDITAR” e “Lançamento/Inscrições”.  
Pandapé: cards de vaga com cargo, cidade, regime, posições, remuneração e data.  
Selector/container: não confirmado; usar links textuais e estrutura de cada sistema.  
ID: slug/ID no detalhe; PDFs têm identificador temporário.

### Paginação
Editais: paginação não determinada.  
Pandapé: página mostra 20 por bloco e informa 50 encontradas; seguir controles do próprio portal/browser.  
Parâmetros: UNKNOWN.

### Exemplo real
Título: Coordenador de Enfermagem — FAPEX.  
Órgão: FAPEX, Salvador/BA.  
Status: vaga efetiva CLT; 1 posição; remuneração R$ 10.000–11.000 (Pandapé).  
URL: https://fapex.pandape.infojobs.com.br/  (link da vaga).  
Edital: vagas Pandapé não usam edital PDF; editais de estágio ficam no archive FAPEX.

### Campos
Pandapé: titulo, cidade/UF, modalidade (presencial), jornada, vagas/posições, regime, salário e data em HTML; descrição/detalhes no link da vaga.  
Editais FAPEX: titulo/orgao/status/datas HTML; cargo/área/vagas/escolaridade/taxa/prova e edital PDF; link_edital HTML/PDF; link_inscricao no texto do edital (frequentemente e-mail/formulário).  
salário/prova/cidade em archive: NÃO DISPONÍVEL uniformemente.

### Publicações
Archive FAPEX reúne edital de abertura, retificações, resultados e convocações como itens/arquivos; Pandapé reúne vaga atual, sem histórico de edital.  
Deduplicação: ID/slug da vaga ou título+data; para PDF, projeto+edital+número+tipo.  
Ruídos: login Portal RH, licitação/fornecedor, transparência, links de editar e menus.

### API/XHR
Endpoint: não confirmado para archive FAPEX/Pandapé.  
Método: GET público para archive e página Pandapé; Portal RH exige sessão.  
JSON/paginação/auth: desconhecidos; não inventar API InfoJobs.

### Tecnologia
Tipo: OTHER/SERVER_RENDERED no archive FAPEX; portalrh é aplicação autenticada; Pandapé é plataforma externa de recrutamento.  
HTTP funciona: SIM para archive/Pandapé; NÃO para dados internos do Portal RH sem login.  
JS necessário: NÃO para archive; Pandapé pode renderizar controles em JS.  
Playwright necessário: NÃO para archive; provável para paginação Pandapé se HTTP não trouxer cards.

### Bloqueios
Portal RH: login é bloqueio legítimo; não contornar. Archive/Pandapé: sem WAF/CAPTCHA observado. Alternativa pública: archive e Pandapé.

### Quality gate
ACEITAR SE: vaga/editais indicarem emprego CLT, temporário, estágio, monitor, tutor, professor ou prestador de serviço pessoal.  
REJEITAR SE: fornecedor/licitação, compra, cotação, licitação eletrônica, bolsa de pesquisa sem função e conteúdo autenticado do empregado.

### Empty evidence
Não vazio: Pandapé declara 50 vagas e archive apresenta editais de seleção. Portal RH isolado seria `BLOCKED/UNKNOWN`, não vazio.

### Estratégia recomendada
`HYBRID`/`DEDICATED_CONNECTOR`: archive FAPEX para editais de projeto + Pandapé para vagas correntes; `KEEP_BLOCKED` somente para Portal RH.

### Instruções para Codex
1. Não usar `/portalrh/` como discovery; tratar como login.  
2. Implementar discovery no archive `/Fapex/Site/Principal/Edital/index` e, separadamente, Pandapé.  
3. Extrair detalhes/PDFs de seleção de pessoas; excluir licitações e fornecedor.  
4. Não inferir active dos editais históricos; para Pandapé usar cards/estado da vaga.  
5. Testar Coordenador de Enfermagem, um edital de estágio 2026 e bloqueio do Portal RH sem login.

### Confidence
MEDIUM — fontes públicas e migração são claras; API/paginação dos sistemas externos não confirmadas.

### Evidências
https://master.fapex.org.br/portalrh/  
https://fapex.org.br/Fapex/Site/Principal/Edital/index  
https://fapex.pandape.infojobs.com.br/  
https://www.fapex.org.br/Fapex/Harp/sys/web/pub/faq/index.html

## 74 — FATEC (Santa Maria)

Identificador técnico: `fatec_selection`  
URL fornecida: https://www.fatecsm.org.br/processos-seletivos/  
URL oficial confirmada: https://www.fatecsm.org.br/processos-seletivos/  
Portal ativo: SIM. URL mudou: NÃO.

### Navegação
Homepage: https://www.fatecsm.org.br/  
Processos seletivos: `/processos-seletivos/`  
Detalhe: não há páginas de detalhe separadas; cada linha da tabela já traz os links de arquivos.  
Documentos: links rotulados EDITAL, ANEXO, RESULTADO, AVISO, ERRATA, CLASSIFICAÇÃO, ENTREVISTAS, CRONOGRAMA, ATA DE JULGAMENTO.

### Universo observado
Observed: 3 itens “EM ANDAMENTO” e 7 itens “ENCERRADO” visíveis na página (10 entradas observadas).  
Relevant: 10 — todos são seleção/contratação, estágio, tutor, técnico ou cargo de projeto.  
Active: 3.  
Closed: 7 observados.  
Out of scope: compras/licitações e menus institucionais.

### Listagem
Estrutura: tabela HTML com colunas DATA, NÚMERO, PERÍODO INSCRIÇÕES, DESCRIÇÃO, ARQUIVOS.  
Selector/container: tabela principal; seletor CSS exato não confirmado.  
Título: descrição textual; link: cada rótulo de arquivo.  
ID: coluna NÚMERO (ex.: 2026/3010088-01).  
Status: texto `(EM ANDAMENTO)` ou `(ENCERRADO)` na coluna DATA.

### Paginação
Método: nenhuma paginação observada; página apresenta histórico diretamente.  
Parâmetros: nenhum.

### Exemplo real
Título: CONTRATAÇÃO CLT: ANALISTA DE PROJETOS E AÇÕES EM GÊNERO, DIREITOS HUMANOS E ENFRENTAMENTO ÀS VIOLÊNCIAS — Psicologia e Direito.  
Órgão: FATEC/UFSM, projeto 2026/3010088-01.  
Status: EM ANDAMENTO; inscrições 10/07/2026–24/07/2026.  
URL: https://www.fatecsm.org.br/processos-seletivos/  
Edital: primeiro link EDITAL da linha; anexos/resultados na mesma linha.

### Campos
data/status/ID/período/título: HTML da tabela.  
orgao: HTML/PDF.  
modalidade/cargo/área/vagas/salário/escolaridade/taxa/prova_data: PDF EDITAL.  
cidade/UF: PDF (Santa Maria/RS ou local do projeto).  
edital_numero/data e link_edital: HTML/PDF.  
link_inscricao: edital/aviso; não há coluna própria.

### Publicações
Muitos documentos por linha, rotulados por tipo; retificações, resultados parciais, classificação, entrevistas, cronograma e ata aparecem como links separados.  
Deduplicação: ID da linha + rótulo + URL; não descartar dois anexos com mesmo rótulo.  
Ruídos: links de compras/licitações no menu e rodapé.

### API/XHR
Endpoint/API: não encontrado; GET HTML suficiente.  
Paginação/auth: não aplicável; documentos públicos.

### Tecnologia
Tipo: SERVER_RENDERED, WORDPRESS (tema GeneratePress visível no rodapé), PDF_INDEX.  
HTTP funciona: SIM.  
JS necessário: NÃO.  
Playwright necessário: NÃO.

### Bloqueios
Sem 403/429/WAF/CAPTCHA observado.

### Quality gate
ACEITAR SE: status EM ANDAMENTO/ENCERRADO e descrição indicar contratação, cargo, estágio, tutor, técnico ou seleção de profissional.  
REJEITAR SE: item de compra/licitação ou arquivo genérico sem processo de pessoal.

### Empty evidence
Não vazio: três linhas em andamento e sete encerradas explicitamente.

### Estratégia recomendada
`CONFIGURABLE_HTML`.

### Instruções para Codex
1. Ler a tabela principal e separar status do campo DATA.  
2. Usar a coluna NÚMERO como ID; conservar todos os links de arquivos por rótulo.  
3. Abrir EDITAL para campos de cargo/vagas/remuneração e PDF para datas.  
4. Testar a linha 2026/3010088-01 e uma encerrada 2025/3030061-01.

### Confidence
HIGH — tabela, status, contagens observadas e documentos são explícitos.

### Evidências
https://www.fatecsm.org.br/processos-seletivos/  
https://www.fatecsm.org.br/doc.licitacoes/edital_280125105402-fatec.pdf

## 75 — FAPED

Identificador técnico: `faped_selection`  
URL fornecida: https://faped.org.br  
URL oficial confirmada: https://faped.org.br/editais  
Portal ativo: SIM. URL mudou: NÃO.

### Navegação
Homepage: https://faped.org.br/  
Editais gerais: https://faped.org.br/editais  
Menu de pessoal: “Processo Seletivo Simplificado-Celetista” aponta para rota filtrada exibida como `https://faped.org.br/editais%26filter%3D2` em resultado indexado.  
Outras categorias: Editais de Compras, Bolsas de Estímulo à Inovação e Oferta Tecnológica.  
Detalhe/documentos: blocos na página e PDFs em `/files/uploads/document/`.

### Universo observado
Observed: `/editais` mostra muitos editais de compras/oferta tecnológica, todos encerrados; filtro de celetista mostra o Edital de Processo Seletivo Simplificado 001/2025.  
Relevant: 1 processo de pessoal confirmado (Analista em Sanidade Vegetal).  
Active: 0 confirmados; o item observado está encerrado.  
Closed: 1 pessoal confirmado; demais contagens são compras/oferta e não devem ser somadas.  
Out of scope: compras, fornecedor, oferta tecnológica, bolsas de estímulo à inovação e projetos.

### Listagem
Estrutura: HTML com blocos “Edital … Encerrado”, “Abertura”, título, descrição e “Documentos”.  
Selector/container: não fixado; usar heading/texto do bloco e links PDF.  
Título/link/status: heading e descrição; status no heading.  
ID: número do edital.

### Paginação
Método: não observada; página extensa com filtro de categoria.  
Parâmetros: `filter=2` aparece codificado na URL do menu; confirmar href real em runtime, sem inventar variação.

### Exemplo real
Título: EDITAL DE PROCESSO SELETIVO SIMPLIFICADO Nº 001/2025 — Analista em Sanidade Vegetal.  
Órgão: FAPED/CPAMT/Better Cotton; atividades Embrapa Agrossilvipastoril, IMAmt e UNEMAT.  
Status: encerrado; abertura 16/09/2025.  
URL: https://faped.org.br/files/uploads/document/aKU2wP4C1758025979489.pdf  
Edital: PDF oficial, 1 vaga CLT, 8h/dia, salário base R$ 8.000.

### Campos
titulo/status/edital_numero/data_abertura: HTML/PDF.  
orgao/modalidade/cargo/área/vagas/salário/escolaridade: PDF (tabela do edital).  
cidade/UF: PDF.  
taxa/prova/inscrições: PDF.  
link_edital: HTML para PDF `/files/uploads/document/`.  
link_inscricao: PDF (instruções do edital); não há formulário universal.

### Publicações
A página de pessoal exibe edital e “Documentos”; convocações/resultados podem ser PDFs separados (exemplo convite para entrevista e resultado da entrevista indexados).  
Deduplicação: número+ano+cargo+tipo, preservando resultado/convocação.  
Ruídos: grandes blocos de compras, licitações, fornecedores, bolsistas e links Conveniar.

### API/XHR
Nenhum endpoint público confirmado; GET HTML/PDF.  
Auth: não para edital/resultados; Conveniar é portal separado.

### Tecnologia
Tipo: SERVER_RENDERED, PDF_INDEX, OTHER (CMS não confirmado).  
HTTP funciona: SIM.  
JS necessário: NÃO.  
Playwright necessário: NÃO.

### Bloqueios
Sem bloqueio HTTP/WAF/CAPTCHA observado; rota filtrada codificada pode dar cache miss, usar menu oficial e validar.

### Quality gate
ACEITAR SE: texto contiver processo seletivo simplificado e contratação de profissional/CLT/cargo, com vaga e requisitos.  
REJEITAR SE: edital de compra/fornecedor, oferta tecnológica, bolsa de inovação ou chamada de projeto.

### Empty evidence
`EMPTY_BY_OBSERVATION` para pessoal: único edital encontrado está encerrado; não afirmar empty global porque compras continuam listadas.

### Estratégia recomendada
`CONFIGURABLE_HTML` + `KEEP_EMPTY` + `INSTITUTIONAL_FILTER_REQUIRED`.

### Instruções para Codex
1. Seguir o link do menu “Processo Seletivo Simplificado-Celetista”; validar URL filtrada antes de configurar.  
2. Extrair somente blocos de pessoal e PDFs; excluir categorias de compras/bolsas/oferta.  
3. Usar o PDF 001/2025 como fixture e confirmar status encerrado.  
4. Implementar estado vazio separado do archive de compras.

### Confidence
MEDIUM — edital de pessoal e filtro estão confirmados, mas a URL codificada do filtro/paginação exige validação rápida.

### Evidências
https://faped.org.br/  
https://faped.org.br/editais  
https://faped.org.br/files/uploads/document/aKU2wP4C1758025979489.pdf

## 76 — FAPESE

Identificador técnico: `fapese_selection`  
URL fornecida: https://fapese.org.br  
URL oficial confirmada: https://www.fapese.org.br/programa-primeiro-emprego/ e https://www.fapese.org.br/ (redireciona/canonicaliza para www).  
Portal ativo: SIM. URL mudou: SIM (canonicalização para `www`).

### Navegação
Homepage: https://www.fapese.org.br/  
Editais: link “Oportunidades > Editais”.  
Programa/seleção: https://www.fapese.org.br/programa-primeiro-emprego/  
Abiertos/Em andamento/Concluídos: abas na página do Programa Primeiro Emprego.  
Documentos: links de PDFs em `/wp-content/uploads/2026/...`; resultados e retificações na mesma página.  
Portal Conveniar/compras: subdomínio separado, fora do escopo de pessoal.

### Universo observado
Observed: página do Programa Primeiro Emprego lista 16 publicações (chamada, retificações, homologações, resultados e classificação).  
Relevant: seleção de professores/instrutores (Edital 02/2026 e complementar 06/2026) é pessoal/função; seleção de jovens para cursos com bolsa-auxílio é beneficiário/qualificação, não emprego.  
Active: 0 confirmados em 30/08/2026; última publicação é classificação consolidada de 03/08/2026.  
Closed: pelo menos o ciclo 2026 do PPE após resultados; total `UNKNOWN`.  
Out of scope: seleção de alunos/beneficiários do PPE, bolsa-auxílio de R$500, editais de apoio a eventos, pesquisa e fomento.

### Listagem
Estrutura: página WordPress com título “Programa Primeiro Emprego”, abas “Abertos Em andamento Concluídos” e lista de links datados.  
Selector/container: seletor exato não confirmado; usar links de publicação e texto da aba.  
Título/link/status: data + título; estado pela aba e pelo tipo (chamada/resultado).  
ID: número do edital no título.

### Paginação
Método: não observada nessa página; lista única com 16 itens.  
Parâmetros: nenhum confirmado.

### Exemplo real
Título: Edital Nº 02/2026 — Chamada Pública para Formação de Banco de Professores/Instrutores do Programa Primeiro Emprego Sergipe.  
Órgão: FAPESE/UFS/SETEEM/MTE.  
Status: concluído/resultado consolidado publicado 03/08/2026.  
URL: https://www.fapese.org.br/programa-primeiro-emprego/  
Edital: link da publicação de 10/03/2026 e retificações/resultado na mesma página.

### Campos
titulo/status/data_publicação: HTML.  
orgao/modalidade/cargo/área/requisitos/vagas/remuneração/inscrição: PDF do edital; página dá apenas resumo.  
cidade/UF: PDF/Programa (SE).  
link_edital: HTML/PDF em `wp-content/uploads`.  
link_inscricao: publicação/edital; formulário externo do PPE.  
Para alunos PPE, bolsa-auxílio não deve ser mapeada como salário.

### Publicações
Estrutura: lista cronológica de chamadas, retificações, homologação, resultado preliminar/final, classificação e recursos.  
Tipos: edital, retificação, homologação, resultado, classificação consolidada.  
Deduplicação: número/ano + título normalizado + tipo + data; preservar cada retificação.  
Ruídos: notícias do programa, bolsa de alunos, apoio a eventos, Conveniar e conteúdo institucional.

### API/XHR
Endpoint: nenhum `wp-json` público confirmado.  
Método: GET HTML + PDFs.  
Auth: não para publicações; formulários podem ser externos.

### Tecnologia
Tipo: WORDPRESS, SERVER_RENDERED, PDF_INDEX (links `wp-content/uploads`).  
HTTP funciona: SIM.  
JS necessário: NÃO para lista.  
Playwright necessário: NÃO.

### Bloqueios
Sem 403/429/WAF/CAPTCHA observado; canonicalização `www` deve ser seguida.

### Quality gate
ACEITAR SE: seleção de professores/instrutores, trabalhador, estágio, cargo/função ou contratação.  
REJEITAR SE: seleção de jovens para curso/benefício/bolsa-auxílio, fomento, apoio a evento ou pesquisa.

### Empty evidence
`EMPTY_BY_OBSERVATION` para seleção de pessoal: ciclo de instrutores tem resultado consolidado e não há chamada aberta. Não declarar vazio da página geral, que contém publicações históricas.

### Estratégia recomendada
`CONFIGURABLE_HTML` + `WORDPRESS_API` somente se API for confirmada; `INSTITUTIONAL_FILTER_REQUIRED` + `KEEP_EMPTY`.

### Instruções para Codex
1. Canonicalizar para `www.fapese.org.br` e abrir a página PPE.  
2. Percorrer abas/lista e coletar cada PDF/publicação.  
3. Aceitar Edital 02/2026/Complementar 06/2026 apenas como seleção de instrutores; rejeitar a seleção de jovens/bolsa-auxílio.  
4. Usar resultado de 03/08/2026 para teste de concluído e não contar como ativo.  
5. Testar separação entre categoria “Abertos”, “Em andamento” e “Concluídos”.

### Confidence
HIGH — página oficial e ciclo/resultado são explícitos; regra de escopo exige filtro cuidadoso.

### Evidências
https://www.fapese.org.br/programa-primeiro-emprego/  
https://www.fapese.org.br/ufs-e-fapese-divulgam-selecao-de-instrutores-para-o-programa-primeiro-emprego/  
https://www.fapese.org.br/confira-o-resultado-final-do-programa-primeiro-emprego/

## 77 — FAPEPI

Identificador técnico: `fapepi_selection`  
URL fornecida: https://www.fapepi.pi.gov.br/editais-fapepi/  
URL oficial confirmada: https://www.fapepi.pi.gov.br/editais-fapepi/  
Portal ativo: SIM. URL mudou: NÃO.

### Navegação
Homepage: https://www.fapepi.pi.gov.br/  
Editais: `/editais-fapepi/` e `/editais/` (arquivo WordPress).  
Em andamento: https://www.fapepi.pi.gov.br/situacao-de-edital/em-andamento/  
Detalhe: `/edital/<slug>/`.  
Documentos: página do edital e PDFs `/wp-content/uploads/2026/...`.  
SIGFAPEPI: https://sig.fapepi.pi.gov.br/ (submissões autenticadas).

### Universo observado
Observed: arquivo “Editais Fapepi” mostra pelo menos 9 editais 2026 e histórico extenso; total `UNKNOWN`.  
Relevant: 0 seleções de emprego/pessoal confirmadas.  
Active: 0 relevantes; página Em Andamento contém fomento/eventos/Tecnova/bolsas.  
Closed: UNKNOWN.  
Out of scope: PBIC, PAPG, PDCTR, PROFIX, PAP, Tecnova, prêmios, chamadas de propostas, eventos, auxílio e qualquer seleção de projetos/bolsas.

### Listagem
Estrutura: arquivo HTML WordPress com heading “EDITAIS”, links de título e seção “EDITAIS ENCERRADOS”; itens levam a post detalhado ou PDF.  
Selector/container: seletor CSS não confirmado; usar links do conteúdo principal.  
Título/link/status: HTML; status em categoria/rota ou no texto da publicação.  
ID: número/ano no título.

### Paginação
Método: arquivo alternativo `/editais/?page=1`, `/editais/?page=2` aparece indexado; seguir `page` até fim.  
Parâmetros: `page=N`; a página temática `/editais-fapepi/` é uma lista longa sem paginação visível.

### Exemplo real
Título: EDITAL Nº 006/2026 — Programa de Bolsas de Iniciação Científica da FAPEPI (PBIC).  
Órgão: FAPEPI.  
Status: edital de bolsa/submissão de proposta, fora do escopo; publicado 24/06/2026.  
URL: https://www.fapepi.pi.gov.br/edital/edital-no-006-2026-programa-de-bolsas-de-iniciacao-cientifica-da-fapepi-pbic/  
Edital: PDF/anexos na página.

### Campos
titulo/status/data_publicação: HTML do arquivo/post.  
orgao/modalidade/área/vagas/valores/requisitos/cronograma: HTML/PDF do edital.  
cargo/cidade/UF/salário/taxa/prova: NÃO DISPONÍVEL para seleção de pessoal atual; não inferir de bolsas.  
edital_numero/data/link_edital: HTML/PDF.  
inscricao_inicio/fim/link_inscricao: PDF e SIGFAPEPI (login; submissão de propostas).

### Publicações
Estrutura: post detalhado inclui edital, anexos Word/PDF, resultados de habilitação/mérito e retificações.  
Tipos: edital, anexos, retificação, resultado preliminar/final, recursos.  
Deduplicação: número/ano + slug + tipo; arquivos de chamadas diferentes não são vagas.  
Ruídos: SIGFAPEPI, notícias, prêmios, eventos, auxílio e histórico extenso.

### API/XHR
Endpoint: nenhum `wp-json` confirmado.  
Método: GET HTML/PDF; SIGFAPEPI é sistema autenticado.  
Paginação: `/editais/?page=N`; JSON/auth desconhecidos.

### Tecnologia
Tipo: WORDPRESS, SERVER_RENDERED, PDF_INDEX.  
HTTP funciona: SIM para arquivo/posts; SIGFAPEPI requer login.  
JS necessário: NÃO para arquivo; pode ser necessário no SIGFAPEPI.  
Playwright necessário: NÃO para discovery; não automatizar login.

### Bloqueios
Sem WAF/CAPTCHA observado em páginas públicas. SIGFAPEPI é bloqueio de autenticação legítimo; alternativa é ler edital/post público.

### Quality gate
ACEITAR SE: futura publicação indicar explicitamente contratação, cargo, emprego, estágio ou seleção de pessoa.  
REJEITAR SE: bolsa, auxílio, fomento, evento, prêmio, pesquisa, submissão de proposta, Tecnova ou chamada científica.

### Empty evidence
`OUT_OF_SCOPE`/`EMPTY_BY_OBSERVATION`: arquivo atual contém somente editais de fomento/bolsas/eventos/propostas; não há seleção de pessoal confirmada. Não tratar “Em Andamento” de fomento como concurso ativo.

### Estratégia recomendada
`WORDPRESS_API` apenas se endpoint público for confirmado; de imediato `CONFIGURABLE_HTML` + `KEEP_EMPTY` + `INSTITUTIONAL_FILTER_REQUIRED`.

### Instruções para Codex
1. Percorrer `/editais-fapepi/` e arquivo `/editais/?page=N`, seguindo posts e PDFs.  
2. Classificar semanticamente; excluir PBIC/PAPG/PDCTR/PROFIX/PAP/Tecnova/prêmios/eventos/auxílios.  
3. Não acessar ou automatizar SIGFAPEPI autenticado para discovery.  
4. Manter resultado vazio de pessoal enquanto não houver edital com contratação/emprego/estágio.  
5. Testar PBIC 006/2026 como exclusão e qualquer futuro edital de contratação como inclusão.

### Confidence
HIGH — arquivo oficial, categorias e natureza dos editais são explícitos; nenhuma seleção de pessoal atual foi encontrada.

### Evidências
https://www.fapepi.pi.gov.br/editais-fapepi/  
https://www.fapepi.pi.gov.br/situacao-de-edital/em-andamento/  
https://www.fapepi.pi.gov.br/edital/edital-no-006-2026-programa-de-bolsas-de-iniciacao-cientifica-da-fapepi-pbic/  
https://sig.fapepi.pi.gov.br/

## Cross-source / oportunidades compartilhadas do lote

| Plataforma | Fontes | Estrutura comum | API comum? | Pode compartilhar conector? |
|---|---|---|---|---|
| `selecao.net.br` white-label | FAFIPA (69) e outros lotes podem conter ACCESS/ABCP/RBO/Avança SP | HTML server-rendered com `index/<estado>`, `pg`, `pp`, cards, status e contador | Nenhuma API confirmada neste lote | SIM, com configuração por tenant; validar URLs de detalhe e estados |
| WordPress archive/PDF | FADE (72), FAPESE (76), FAPEPI (77) | arquivos por categoria/post, `/page/N/` ou página temática, PDFs em `wp-content/uploads` | `wp-json` não confirmado | Parcial; conector genérico de archive + filtro institucional |
| FAPs institucionais HTML/PDF | FAPES (66), FAPESQ (67) | páginas de edital/resultado e PDFs; categorias/anos | Nenhuma API confirmada | Não compartilhar parser sem normalização; filtros de escopo são específicos |
| Sistemas de fundação/seleção | Uniselva (68), FUNPEC (71), FATEC (74), FAPED (75), FAPEX (73) | HTML/PDF, detalhes e documentos, porém engines distintas | Nenhuma API confirmada | Conector configurável apenas em nível de campos, não presumir engine comum |

## Casos para revisão do Sol

- FAPESQ (67): MEDIUM; coleção mistura fases e paginação extensa. Revisar definição de `active` após leitura de cronogramas.  
- IESES (70): MEDIUM; shell JS/load-more e endpoints desconhecidos; precisa inspeção de rede/Playwright.  
- FAPEX (73): supplied URL é login Portal RH; decidir se integração Pandapé + archive deve substituir a origem.  
- FAPED (75): filtro de pessoal aparece em URL codificada; confirmar href exato em live retest.  
- FAPESE (76): separar rigorosamente instrutor (pessoal) de aluno PPE (benefício com bolsa-auxílio).  
- FAPES (66) e FAPEPI (77): KEEP_EMPTY/OUT_OF_SCOPE; não remover sem revisar se surgirem editais explícitos de contratação.

