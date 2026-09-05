# Observador de Concursos — Pesquisa operacional BATCH 07

Fontes 78–89 (FAPs/fundações). Pesquisa externa realizada em 2026-08-30, entre 17:40 e 18:20, America/Sao_Paulo (UTC−03:00). Evidência baseada exclusivamente em páginas oficiais e PDFs oficiais vinculados por elas. Não foi usado crawler local nem qualquer contagem do aplicativo.

**Fechamento do lote:** 12/12 fontes pesquisadas; confiança HIGH 8, MEDIUM 4, LOW 0. Casos para revisão: FAPECE (identidade/domínio), FAPERN (503), FAPESB (portal REDA externo), FACEPE (PSS histórico em meio a chamadas de fomento) e FAPPR (estágios misturados a bolsas).

## 78 — FAPEMA

**Identidade.** Identificador `fapema_selection`; URL fornecida `https://www.fapema.br/inicio/`; URL oficial confirmada `https://www.fapema.br/` e listagem `https://www.fapema.br/editais/` (o domínio `fapema.br` permanece oficial). Portal ativo: SIM. URL mudou: NÃO confirmada.

### Navegação
- Homepage: `https://www.fapema.br/`
- Abertos: `https://www.fapema.br/editais/` e `https://www.fapema.br/category/editais/editais-em-aberto/`
- Em julgamento: a seção é exibida em `/editais/`.
- Encerrados/histórico: `/editais/` e arquivo por categoria/ano; URL específica não foi presumida.
- Detalhe: posts individuais, por exemplo `https://www.fapema.br/edital-fapema-fmrb-n-14-2026/`.
- Documentos: links PDF/DOCX embutidos nos posts, normalmente em `wp-content/uploads/...`.

### Universo observado
Observed: UNKNOWN (a página mostra várias listas, sem total consolidado). Relevant: 0 confirmado no recorte atual. Active: 0 confirmado para seleção de pessoal. Closed: UNKNOWN. Out of scope: múltiplas chamadas de pesquisa, bolsas, apoio e submissão de projetos. O edital FAPEMA/FMRB 14/2026 é explicitamente “Seleção de Agentes da Memória”, mas o próprio conteúdo identifica modalidades Bolsa Aluno e BIQ/FMRB, portanto não é contratação de pessoal.

### Listagem, paginação e exemplo
Estrutura: página WordPress com seções “Editais Abertos”, “Editais em Julgamento” e “Editais Encerrados 2025”, cada item como título/link para post; documentos aparecem no detalhe. Selector/container exato: UNKNOWN (não inventar classe CSS). Título/link/status: HTML; status é inferido da seção editorial, não de campo estruturado. Paginação: links “Ver Todos”/arquivo; parâmetro e número de páginas não confirmados.

Exemplo real: **Edital FAPEMA/FMRB nº 14/2026 — Seleção de Agentes da Memória**, FAPEMA/FMRB, status editorial “Editais Abertos” na página de categoria no momento do registro; detalhe `https://www.fapema.br/edital-fapema-fmrb-n-14-2026/`. A página lista edital, retificação, resultados e chamadas de excedentes, e informa submissão 14–28/05/2026. É seleção de bolsistas, não concurso/emprego.

### Campos
`titulo` HTML; `orgao` HTML (texto do post); `modalidade` PDF/HTML; `cargo` NÃO DISPONÍVEL; `area` PDF/HTML; `cidade` NÃO DISPONÍVEL; `uf` INFERIDO=MA (não usar como campo de cargo); `status` HTML por seção; `vagas` PDF quando o edital informar; `salario_min/max` NÃO DISPONÍVEL; `escolaridade` PDF; `taxa` NÃO DISPONÍVEL; `prova` NÃO DISPONÍVEL; `edital_numero/data` HTML/PDF; `inscricao_inicio/fim` HTML/PDF; `link_edital` HTML; `link_inscricao` NÃO DISPONÍVEL (submissão costuma ser sistema externo). Não converter bolsas em cargo.

### Publicações, API, tecnologia e bloqueios
Publicações: no mesmo post, em ordem cronológica, como edital, retificação, resultado parcial/final, convocação e anexos; deduplicar por URL do documento e título normalizado. Ruído: menus, “Tela Cheia”, links institucionais, cookies e PDFs auxiliares. API/XHR: nenhum endpoint público foi evidenciado; não inventar `/api`. Autenticação: página pública sem autenticação; submissão pode exigir sistema externo. Tecnologia: `WORDPRESS`/`SERVER_RENDERED` (evidência: rotas `/wp-content/uploads/` e categorias/posts). HTTP simples: SIM para índice e detalhe; JS/Playwright: NÃO demonstrado. WAF/Cloudflare/CAPTCHA: não observado nas páginas indexadas; alternativa: categoria oficial.

### Quality gate, vazio, estratégia e instruções
ACEITAR somente item cujo documento oficial evidencie contratação, emprego, cargo, função, estágio ou processo seletivo de pessoal. REJEITAR chamadas de fomento, prêmio, auxílio, bolsa, submissão de projeto ou seleção de proposta. Empty evidence: `OUT_OF_SCOPE` (há chamadas visíveis, mas não de pessoal); não declarar zero de editais sem pessoal como zero de chamadas.

Diagnóstico: `CRAWLER_STRATEGY_CLEAR`, `HTML_SUFFICIENT`, `INSTITUTIONAL_FILTER_REQUIRED`, `OUT_OF_SCOPE`. Estratégia: `CONFIGURABLE_HTML` + `INSTITUTIONAL_FILTER_REQUIRED`; `KEEP_EMPTY` para o universo de pessoal até nova evidência. Instruções Codex: 1) usar `/editais/` e seguir “Ver Todos”; 2) extrair apenas links de posts e documentos no HTML; 3) visitar detalhe para anexos; 4) aplicar filtro lexical/documental de contratação/emprego/estágio; 5) excluir `bolsa`, `fomento`, `auxílio`, `proposta`, `pesquisa` salvo se o edital também comprovar vínculo de pessoal; 6) criar teste de exclusão para FMRB 14/2026; 7) não esperar API nem inventar contagem.

**Confidence: HIGH** para identidade e filtro de escopo; MEDIUM para paginação/tecnologia CMS. Evidências: `https://www.fapema.br/editais/`; `https://www.fapema.br/category/editais/`; `https://www.fapema.br/edital-fapema-fmrb-n-14-2026/`.

## 79 — FAPECE

**Identidade.** Identificador `fapece_selection`; URL fornecida `https://fapece.ce.gov.br`; essa URL não resolveu no teste (DNS/host desconhecido). A entidade encontrada em domínio oficial pesquisável é **FAPECE — Fundação Assistencial e Previdenciária da EMATERCE**, em `https://fapece.com.br/`, não uma fundação estadual de amparo à pesquisa. Portal ativo para a fonte pretendida: INCERTO/IDENTIDADE INCOMPATÍVEL. URL mudou: NÃO comprovada; há provável erro de entidade na lista.

### Navegação e universo
Homepage alternativa: `https://fapece.com.br/`; notícia oficial da entidade: `https://fapece.com.br/noticias/`. Não há listagem oficial confirmada de concursos públicos ou seleções de pessoal no domínio fornecido. A página de notícias menciona “Processo Seletivo Diretor de Seguridade”, mas trata de governança de entidade previdenciária, não de contratação pública. Observed/Relevant/Active/Closed: UNKNOWN/UNKNOWN/UNKNOWN/UNKNOWN. Out of scope: previdência, eleições internas, seleção de dirigentes e documentação atuarial.

### Listagem, exemplo, campos e publicações
Listagem de concursos: NÃO CONFIRMADA. Selector, paginação, detalhe e documentos de concurso: UNKNOWN. Exemplo real relevante: nenhum confirmado. Campos (título, órgão, modalidade, cargo, área, cidade, UF, status, vagas, salário, escolaridade, taxa, prova, edital, datas, links): NÃO DISPONÍVEIS para o universo pretendido; eventual notícia/edital interno deve ser tratado como HTML/PDF sem mapear para concurso.

Publicações da entidade são notícias e documentos previdenciários; deduplicar por URL e data, descartando menus/login/relatórios. API/XHR: UNKNOWN. Tecnologia: o PDF oficial observado usa `/wp-content/uploads/`, sugerindo WordPress no domínio alternativo, mas não se deve aplicar isso ao host `fapece.ce.gov.br`. HTTP/JS/Playwright: UNKNOWN no host fornecido. Bloqueio: host não resolveu; browser não validado; não há API alternativa de concursos confirmada.

### Quality gate, vazio, estratégia e instruções
ACEITAR somente se nova evidência oficial demonstrar vaga de emprego, cargo/função contratual, estágio ou processo seletivo de pessoal. REJEITAR previdência, eleições de diretoria/conselho, bolsas e documentos de plano previdenciário. Empty evidence: `UNKNOWN_EMPTY` combinado com `URL_OUTDATED`/`INSUFFICIENT_EVIDENCE`; não marcar como vazio legítimo até confirmar a identidade com o responsável do projeto.

Diagnóstico: `URL_OUTDATED`, `DISCOVERY_COMPLEX`, `INSUFFICIENT_EVIDENCE`, `DEPRECATED_REVIEW_REQUIRED` (equivalente operacional de `DEPRECATE_REVIEW_REQUIRED`). Estratégia: `DEPRECATE_REVIEW_REQUIRED` antes de implementar. Instruções Codex: 1) não criar crawler para `fapece.ce.gov.br` sem confirmação da entidade; 2) validar com fonte oficial se o identificador deveria ser FUNCAP/CE ou outra agência; 3) só depois mapear o domínio correto; 4) manter a entrada pendente para evitar atribuir seleções da FAPECE previdenciária ao Observador.

**Confidence: HIGH** quanto à falha do host e incompatibilidade de identidade; LOW para qualquer conclusão sobre o portal pretendido. Evidências: `https://fapece.com.br/noticias/`; `https://fapece.com.br/wp-content/uploads/2026/05/Fapece_RMCF_2sem2025_VFAprovada.pdf`; tentativa do host fornecido `https://fapece.ce.gov.br` sem resolução.

## 80 — FAPERN

**Identidade.** Identificador `fapern_selection`; URL fornecida `https://fapern.rn.gov.br`; a abertura retornou 503 no teste. A entidade é a Fundação de Amparo e Promoção da Ciência, Tecnologia e Inovação do RN. Portal ativo: PARCIAL/INDETERMINADO. URL oficial alternativa confirmada: `https://www.gov.br/capes/pt-br/acesso-a-informacao/acoes-e-programas/bolsas/programas-estrategicos/outras-informacoes/fundacoes-estaduais-de-amparo-a-pesquisa-faps/fundacao-de-apoio-a-pesquisa-do-rio-grande-do-norte-fapern` (página institucional CAPES); documentos também aparecem no Diário Oficial RN.

### Navegação e universo
Homepage/listagem atual: não confirmada por indisponibilidade do host. Histórico/documento oficial: D.O. RN e páginas institucionais parceiras. A evidência de 2025 mostra edital para seleção de propostas/bolsistas com inscrição por e-mail e divulgação no site FAPERN, não contratação de servidor. Observed: UNKNOWN; Relevant: 0 confirmado; Active: UNKNOWN; Closed: 1 processo de bolsa/proposta conhecido; Out of scope: bolsas, propostas de pesquisa e comunicação científica.

### Listagem, exemplo e campos
Container/selector/paginação: UNKNOWN por 503. Exemplo oficial: **Edital FAPERN de seleção de propostas/bolsistas (D.O. RN, outubro de 2025)**; inscrição por e-mail, arquivos PDF e resultados no site FAPERN; status encerrado conforme cronograma do edital. URL de evidência: `https://webdisk.diariooficial.rn.gov.br/Jornal/12025-10-17.pdf`.

Campos de uma seleção de pessoal: nenhum confirmado. No documento de bolsa: título/edital/data/inscrição = PDF; órgão = PDF; modalidade = bolsa; cargos, salário, prova e taxa = NÃO DISPONÍVEIS; link de inscrição = e-mail no PDF. Publicações: resultados por etapa e convocação de bolsistas; não tratar como emprego.

### API, tecnologia e bloqueios
API/XHR: UNKNOWN. Tecnologia do site não verificável. HTTP simples: NÃO CONFIRMADO (503); browser: não testado com sucesso; WAF/CAPTCHA: não distinguível de indisponibilidade; endpoint alternativo de seleção: NÃO confirmado. A página CAPES é HTML institucional e não substitui o portal operacional.

### Quality gate, vazio, estratégia e instruções
ACEITAR apenas edital com contratação/emprego/cargo/função/estágio explicitamente descrito. REJEITAR “seleção de propostas”, bolsa, auxílio, comunicação científica e submissão de projeto. Empty evidence: `UNKNOWN_EMPTY` + `SITE_OFFLINE`/`KEEP_BLOCKED`; não converter 503 em zero.

Diagnóstico: `SITE_OFFLINE`, `INSUFFICIENT_EVIDENCE`, `WAF_BLOCKED` não comprovado. Estratégia: `KEEP_BLOCKED` ou `HYBRID` somente após o host voltar; não implementar bypass. Instruções Codex: 1) registrar 503 e não relaxar filtros; 2) revalidar `fapern.rn.gov.br` e o Diário Oficial em live retest; 3) procurar somente páginas oficiais “processo seletivo/contratação/estágio”; 4) manter chamadas de bolsas fora do universo; 5) se o domínio permanecer indisponível, manter fonte bloqueada com evidência.

**Confidence: MEDIUM** para escopo e bloqueio; LOW para estrutura técnica. Evidências: `https://www.gov.br/capes/pt-br/acesso-a-informacao/acoes-e-programas/bolsas/programas-estrategicos/outras-informacoes/fundacoes-estaduais-de-amparo-a-pesquisa-faps/fundacao-de-apoio-a-pesquisa-do-rio-grande-do-norte-fapern`; D.O. `https://webdisk.diariooficial.rn.gov.br/Jornal/12025-10-17.pdf`; URL fornecida com resposta 503.

## 81 — FAPEAL

**Identidade.** Identificador `fapeal_selection`; URL fornecida `https://fapeal.br`; URL oficial confirmada `https://www.fapeal.br/`. Portal ativo: SIM. URL mudou: SIM (redirecionamento/uso de `www` observado; manter `www.fapeal.br`).

### Navegação, universo e exemplo
Homepage/pesquisador: `https://www.fapeal.br/pesquisador/`; editais: `https://www.fapeal.br/pesquisador/editais/`; categoria: `https://www.fapeal.br/category/editais/`; chamadas abertas: `/category/editais/chamadas-abertas/`; plataforma de submissão: eFAP (link na área do pesquisador). Observed: UNKNOWN (a página agrupa anos/categorias sem total confiável). Relevant: 0 atual confirmado; Active: 0 de pessoal confirmado; Closed: UNKNOWN; Out of scope: bolsas, publicação de teses, Centelha, mobilidade e fomento.

Exemplo: **Edital Fapeal nº 05/2026 — Bolsas de Iniciação Científica Júnior**, `https://www.fapeal.br/2026/06/pibic-jr-2026/`; contém edital retificado, resultados, homologações e anexos, mas é bolsa/projeto. Não aceitar como concurso.

### Listagem, campos e documentos
Estrutura: WordPress por posts/categorias; títulos e links em HTML; filtros por ano/categoria; detalhe com blocos de links PDF. Selector/container exato: UNKNOWN. Paginação: arquivo WordPress, parâmetro não confirmado. Campos: `titulo`, `orgao`, `modalidade`, `status`, `edital_numero/data`, `inscricao_inicio/fim`, `link_edital` = HTML/PDF quando presentes; `cargo`, `salário`, `prova`, `taxa`, cidade e inscrição = NÃO DISPONÍVEIS ou eFAP externo; vagas = PDF quando aplicável; não mapear bolsas para cargo.

Publicações: edital, retificações, homologação, resultado parcial/final, anexos; deduplicar por título+URL e manter a publicação mais recente. Ruído: comentários, menus, categorias, eFAP, banners e páginas de prestação de contas. API/XHR: nenhum endpoint público confirmado. Tecnologia: `WORDPRESS`/`SERVER_RENDERED`; HTTP simples SIM; JS/Playwright NÃO demonstrado; WAF/CAPTCHA não observado.

### Quality gate, vazio, estratégia e instruções
ACEITAR somente contratação, emprego, cargo/função, estágio ou seleção de pessoal explicitamente descritos no post/PDF. REJEITAR concessão de bolsas, auxílio, chamada de projetos e publicação acadêmica. Empty evidence: `OUT_OF_SCOPE` para as chamadas visíveis; não usar a quantidade de posts como active count.

Diagnóstico: `HTML_SUFFICIENT`, `GENERIC_CONNECTOR_SUFFICIENT`, `INSTITUTIONAL_FILTER_REQUIRED`, `OUT_OF_SCOPE`. Estratégia: `CONFIGURABLE_HTML` + `KEEP_EMPTY`. Instruções Codex: 1) iniciar em `/pesquisador/editais/` e categorias; 2) seguir links dos posts e PDFs; 3) capturar título/data/status editorial; 4) excluir palavras/modalidades de fomento; 5) tratar eFAP somente como link de submissão, sem autenticação; 6) teste de exclusão para PIBIC Jr e teste de empty legítimo.

**Confidence: HIGH** para URL, WordPress e escopo; MEDIUM para paginação. Evidências: `https://www.fapeal.br/pesquisador/editais/`; `https://www.fapeal.br/category/editais/chamadas-abertas/`; `https://www.fapeal.br/2026/06/pibic-jr-2026/`.

## 82 — FACEPE

**Identidade.** Identificador `facepe_selection`; URL fornecida `https://www.facepe.br`; URL oficial confirmada `https://www.facepe.br/`. Portal ativo: SIM. Editais: `/editais/todos/`, `/editais/abertos/`, `/editais/em-julgamento/`, `/editais/resultados/`, `/editais/encerrados/` (links exibidos no menu).

### Universo e exemplo
Observed: muitos itens no arquivo, total exato UNKNOWN. Relevant: pelo menos 1 seleção pública de contratação temporária histórica, comprovada no PDF `https://www.facepe.br/pub_files/EDITAL_Facepe_selecaosimplificada.pdf`; Active: 0 confirmado no recorte atual; Closed: pelo menos 1 seleção simplificada histórica; Out of scope: a maioria dos itens atuais (bolsas, auxílios, projetos, prêmios e eleições acadêmicas).

Exemplo relevante encerrado: **Edital FACEPE Seleção Simplificada**, contratação temporária de gestores, analistas, assistentes, programadores e técnico de suporte; detalhe/PDF acima. O PDF informa contratação temporária e etapas, portanto é pessoal. Exemplo atual fora do escopo: Edital 10/2026/11/2026 de bolsas/projetos na listagem de todos.

### Listagem, paginação, campos e publicações
Estrutura: índice HTML WordPress com itens em sequência; cada item tem número/título, resumo e links “Download”; parâmetro de categoria `?c=todos` também é usado. Container/selector exato: UNKNOWN. Paginação: página longa e possíveis parâmetros WordPress; modo completo de paginação não confirmado. No detalhe/PDF: título, modalidade, cargo, área, requisitos, remuneração, datas e etapas = PDF; órgão = PDF; link do edital = HTML/PDF; inscrição = PDF ou organizadora externa; cidade/UF/taxa/prova/vagas = PDF quando presentes; não inferir campos ausentes.

Publicações: lançamento, errata, enquadramento, resultados e listas de espera; deduplicar pelo número do edital + tipo de publicação + URL. Ruído: “Download”, menus, AgilFAP, categorias, links de bolsas. API/XHR: nenhum endpoint público evidenciado; AgilFAP é sistema de submissão/acompanhamento, não API de listagem. Tecnologia: `WORDPRESS`/`SERVER_RENDERED`; HTTP SIM; JS/Playwright NÃO demonstrado; bloqueios não observados.

### Quality gate, vazio, estratégia e instruções
ACEITAR somente PDFs/posts com contratação/emprego/cargo/função/estágio/processo seletivo de pessoal. REJEITAR bolsas, auxílios, submissão de propostas, prêmios, eleições de conselho e chamadas de pesquisa. Empty evidence: `EMPTY_BY_OBSERVATION` para pessoal atual somente se o live retest confirmar que `/editais/abertos/` não contém seleção de pessoal; caso contrário `UNKNOWN_EMPTY`.

Diagnóstico: `HTML_SUFFICIENT`, `INSTITUTIONAL_FILTER_REQUIRED`, `DEDICATED_CONNECTOR_RECOMMENDED` para PDFs de seleção. Estratégia: `HYBRID` (HTML + PDF), com `KEEP_EMPTY` quando não houver seleção aberta. Instruções Codex: 1) percorrer `/editais/todos/` e filtros de status; 2) seguir links de detalhe/download; 3) extrair campos de seleção de pessoal do PDF; 4) classificar bolsa/fomento fora do escopo; 5) usar como fixture o PDF da seleção simplificada; 6) testar páginas todos/abertos/encerrados e deduplicação.

**Confidence: HIGH** para URL, taxonomia e exemplo de contratação; MEDIUM para tecnologia/paginação. Evidências: `https://www.facepe.br/`; `https://www.facepe.br/editais/todos/`; `https://www.facepe.br/pub_files/EDITAL_Facepe_selecaosimplificada.pdf`.

## 83 — FAPESB

**Identidade.** Identificador `fapesb_selection`; URL fornecida `https://www.fapesb.ba.gov.br/category/edital/`; URL oficial confirmada e ativa. Portal ativo: SIM. A página contém anos 2008–2026 e filtros “Abertos”, “Fechados”, “Resultados”.

### Universo e exemplo
Observed: UNKNOWN (listagem editorial extensa). Relevant: 1 processo de pessoal confirmado — **Processo Seletivo Simplificado REDA 001/2026**, 22 vagas; Active: 0 no registro de 30/08/2026, pois inscrição oficial foi 30/04–07/05/2026; Closed: 1 confirmado; Out of scope: chamadas de projetos, bolsas, subvenção e pesquisa.

Exemplo real: **FAPESB abre 22 vagas REDA**, funções temporárias, Salvador/BA, inscrição pelo portal `https://selecao.ba.gov.br/`; comunicado no próprio site FAPESB e PDF oficial `https://www.fapesb.ba.gov.br/wp-content/uploads/2019/08/EDITAL_DEFINITIVO_REDA_2026.pdf`. O PDF explicita processo seletivo simplificado para contratação temporária e avaliação curricular.

### Listagem, paginação, campos e documentos
Estrutura: página WordPress por posts, com filtros de ano e estado e links de “Continue lendo”; o comunicado REDA aponta para o portal externo de inscrição. Selector exato: UNKNOWN. Paginação: não confirmada; percorrer links de arquivo/ano. Título, órgão, modalidade, status editorial, data e link = HTML; cargos, vagas, requisitos, remuneração, município, etapas e datas = PDF; taxa/prova = PDF se houver; `link_inscricao` = portal externo quando apontado.

Publicações: edital, erratas, resultados e comunicados; PDFs em `/wp-content/uploads/`; deduplicar por número/tipo/data. Ruído: menus, SIGA, categorias e notícias repetidas. API/XHR: nenhum endpoint público confirmado; SIGA é cadastro/submissão, e `selecao.ba.gov.br` é portal de inscrição com `<select>` de processos, sem endpoint público observado. Tecnologia: `WORDPRESS` no índice, `SERVER_RENDERED` no portal; HTTP SIM para páginas; JS/Playwright não necessário para o índice, mas pode ser necessário para o formulário; WAF/CAPTCHA não observado.

### Quality gate, vazio, estratégia e instruções
ACEITAR REDA/contratação temporária, cargos e funções com edital oficial. REJEITAR “seleção pública” de propostas/subvenção, bolsas e projetos. Empty evidence: `EMPTY_BY_OBSERVATION` para processos abertos em 30/08/2026, mas manter histórico fechado REDA para monitoramento de resultados/convocações.

Diagnóstico: `HTML_SUFFICIENT`, `INSTITUTIONAL_FILTER_REQUIRED`, `DEDICATED_CONNECTOR_RECOMMENDED`, `PORTAL_MIGRATED` (índice e inscrição são domínios distintos). Estratégia: `HYBRID` (índice WordPress + PDFs + portal de inscrição), sem autenticação para descoberta. Instruções Codex: 1) ler `/category/edital/` com filtros de ano/status; 2) detectar posts que contenham contratação/REDA/cargo/função; 3) abrir PDF e extrair vagas, cargo, remuneração e datas; 4) seguir `selecao.ba.gov.br` apenas como link de inscrição, sem submeter; 5) guardar resultados/convocações como publicações; 6) usar REDA 001/2026 como fixture fechado; 7) não contar chamadas de pesquisa.

**Confidence: HIGH**. Evidências: `https://www.fapesb.ba.gov.br/category/edital/`; `https://www.fapesb.ba.gov.br/fapesb-lanca-edital-com-22-vagas-em-regime-reda-para-nivel-superior/`; `https://www.fapesb.ba.gov.br/wp-content/uploads/2019/08/EDITAL_DEFINITIVO_REDA_2026.pdf`; `https://selecao.ba.gov.br/`.

## 84 — FAPERJ

**Identidade.** Identificador `faperj_selection`; URL fornecida `https://faperj.br`; URL oficial confirmada `https://faperj.br/`. Portal ativo: SIM. Lista de editais: `https://faperj.br/?id=28.5.7`; o site também expõe SISFAPERJ.

### Universo e exemplo
Observed: UNKNOWN; a lista de 2026 contém dezenas de editais/chamadas. Relevant: 0 atual confirmado; Active: 0 de contratação confirmado; Closed: UNKNOWN; Out of scope: bolsas, auxílios, prêmios, apoio a projetos e submissão de propostas. O item TCT 2025/2026 é bolsa de treinamento, não vínculo empregatício.

Exemplo real fora do escopo: **Edital FAPERJ nº 14/2026 — Treinamento e Capacitação Técnica (TCT)**, submissões e bolsa; aparece em notícias/lista de editais. Exemplo de histórico de pessoal não suficiente para active: o site antigo possui portaria de contratação, mas não é listagem atual confirmada.

### Listagem, campos, publicações, API e bloqueios
Estrutura: HTML server-rendered legado, com sumário “Lista de Editais/Chamadas (2026)”, links de detalhes e cronogramas; query `?id=28.5.7`. Selector/container exato: UNKNOWN. Paginação: links de anos no rodapé; não confirmada. Campos de chamadas: título/número/data/status/cronograma = HTML; documentos = PDF; cargo/vagas/salário/taxa/prova = NÃO DISPONÍVEIS salvo PDF; `link_inscricao` = SisFAPERJ quando edital indicar. Publicações incluem erratas, resultados preliminares/finais e termos de outorga; deduplicar número+tipo+data. API/XHR: nenhum endpoint público evidenciado. Tecnologia: `SERVER_RENDERED`/CMS legado; HTTP SIM; JS/Playwright NÃO demonstrado; WAF/CAPTCHA não observado.

### Quality gate, vazio, estratégia e instruções
ACEITAR apenas contratação, emprego, cargo, função ou estágio explícito. REJEITAR bolsas TCT/PV/PVE, auxílios, prêmios, editais de projetos e termos de outorga. Empty evidence: `OUT_OF_SCOPE` para as chamadas correntes; não afirmar empty de todo o portal sem verificar eventual seção “Servidores”.

Diagnóstico: `HTML_SUFFICIENT`, `INSTITUTIONAL_FILTER_REQUIRED`, `OUT_OF_SCOPE`. Estratégia: `CONFIGURABLE_HTML` + `KEEP_EMPTY`; usar `HYBRID` apenas quando houver edital de pessoal em PDF. Instruções Codex: 1) usar `?id=28.5.7` como índice de chamadas; 2) seguir links e PDFs; 3) filtrar por contratação/emprego/estágio/cargo; 4) excluir bolsas e submissão de propostas; 5) manter SisFAPERJ como link externo, sem login; 6) revisar a seção de servidores em live retest antes de concluir vazio.

**Confidence: MEDIUM** (portal e escopo claros; ausência de seleção atual requer reteste). Evidências: `https://faperj.br/`; `https://faperj.br/?id=28.5.7`; `https://sisfaperj.faperj.br/`.

## 85 — FAPESP

**Identidade.** Identificador `fapesp_selection`; URL fornecida/oficial `https://fapesp.br/oportunidades/`. Portal ativo: SIM. A página é explicitamente “Oportunidades de Bolsas”, não a lista institucional de concursos.

### Universo observado e exemplo
Observed: **109 oportunidades abertas**, contador visível na página oficial em 30/08/2026. Relevant para o Observador: 0 de emprego/concurso; Active: 0 no escopo; Closed: consultar `/oportunidades/encerradas/`; Out of scope: 109 bolsas/fellowships. A própria página informa que não contém editais institucionais da FAPESP e que contém anúncios de processos seletivos relacionados a auxílios e bolsas.

Exemplo: **Bolsa de TT-III em Genética Animal**, nº 9739, 1 posição, CAUNESP/Jaboticabal, prazo 11/09/2026, detalhe `https://fapesp.br/oportunidades/inovacoes-em-genomica-e-fenomica-no-melhoramento-genetico-de-tilapia/9739/`; campos título, área, processo FAPESP, quantidade, instituição, prazo e e-mail estão no HTML. É bolsa, não contratação; não aceitar.

### Listagem, paginação e campos
Estrutura: lista HTML com filtros de modalidade/cidade/área e links numéricos `/oportunidades/.../{id}/`; contador e categorias são HTML. Selector exato: UNKNOWN. Paginação: não confirmada; usar navegação da própria lista/filtros, sem presumir `page=N`. Campos do exemplo: `titulo`, `area`, `id`, `vagas`, `orgao`, `cidade`, `inscricao_fim`, `link` = HTML; `modalidade` = HTML (“TT-III”); cargo/salário/taxa/prova/escolaridade = texto da oportunidade ou NÃO DISPONÍVEL; edital PDF geralmente inexistente; inscrição = e-mail/formulário externo; status = lista aberta/encerrada.

Publicações/detalhes: descrição, requisitos, atividades, como se candidatar; não há cadeia de retificações institucional. Deduplicar por número da oportunidade/URL; ruído inclui versão bilíngue duplicada, menus e filtros. API/XHR: nenhum endpoint público confirmado. Tecnologia: `SERVER_RENDERED`/HTML; HTTP SIM; JS/Playwright NÃO demonstrado; bloqueios não observados.

### Quality gate, estratégia e instruções
ACEITAR somente se evidência mudar de fellowship para contratação/emprego/estágio formal; a publicação “processo seletivo” não basta quando o vínculo é bolsa. REJEITAR todas as modalidades Bolsa, PD, TT, IC, mestrado/doutorado e seleção vinculada a projeto. Empty evidence: `OUT_OF_SCOPE` com 109 itens observados; não classificar como fonte quebrada.

Diagnóstico: `HTML_SUFFICIENT`, `INSTITUTIONAL_FILTER_REQUIRED`, `OUT_OF_SCOPE`, `EMPTY_CORRECT`. Estratégia: `KEEP_EMPTY`/`DEPRECATE_REVIEW_REQUIRED` se o produto não deseja bolsas; não criar crawler de concurso para esta URL. Instruções Codex: 1) manter a fonte apenas como explicitamente fora do escopo; 2) se houver necessidade futura de bolsas, usar `/oportunidades/` e detalhe numérico como conector separado; 3) testar exclusão com a oportunidade 9739; 4) não interpretar o contador 109 como concursos ativos.

**Confidence: HIGH**. Evidências: `https://fapesp.br/oportunidades/`; `https://fapesp.br/oportunidades/encerradas/`; `https://fapesp.br/oportunidades/inovacoes-em-genomica-e-fenomica-no-melhoramento-genetico-de-tilapia/9739/`.

## 86 — FAPPR / Fundação Araucária

**Identidade.** Identificador `fappr_selection`; URL fornecida `https://fappr.pr.gov.br/Pagina/Processos-Seletivos`; URL oficial confirmada e ativa. Portal ativo: SIM; domínio também se identifica como Fundação Araucária.

### Universo e exemplos
Observed: UNKNOWN (página histórica por anos). Relevant: pelo menos 4 seleções de estágio de 2026, conforme PS 01/2026–PS 04/2026; Active: 0 confirmado em 30/08/2026 porque prazos de fevereiro/março passaram; Closed: pelo menos 4; Out of scope: bolsas de pesquisa, chamadas públicas, eleições internas. Estágio é relevante pelo escopo, mesmo quando há bolsa-auxílio.

Exemplo relevante: **PS 04/2026 — Estágio no Setor dos NAPIs (Pós-Graduação)**, 1 vaga, 30h, bolsa R$2.000 + VR/VT, inscrição até 24/03/2026 por e-mail; página e resultado no mesmo índice. Exemplo de emprego: edital 01.001/2025 para concurso de emprego público CLT, publicado em PDF oficial `https://www.fappr.pr.gov.br/sites/fundacao-araucaria/arquivos_restritos/files/documento/2025-06/1_edital_de_abertura_no_010012025_-_fundacao_a_250625_101122.pdf`.

### Listagem, campos, publicações e tecnologia
Estrutura: página institucional HTML longa, agrupada por “Processos Seletivos 2026”, 2025, 2023 etc.; cada item contém texto de vagas/áreas/bolsa/prazo e links de edital/ato/resultado. Selector/container exato: UNKNOWN. Paginação: sem paginação visível no conteúdo; percorra todo o HTML e links. Campos título, área, vagas, prazo, bolsa/valor, setor e inscrição = HTML; edital/etapas/requisitos = PDF; cidade/UF = texto ou PDF; salário/prova/taxa = PDF quando houver; status = ano + existência de resultado, não assumir ativo somente por título.

Publicações: edital, retificação, comissão, resultado preliminar/final, convocação; deduplicar por PS + tipo de ato. Ruídos: programas e chamadas de fomento no menu, eleições e seleção de bolsistas. API/XHR: nenhum endpoint público observado. Tecnologia: `SERVER_RENDERED`/CMS estadual; HTTP SIM; JS/Playwright NÃO demonstrado; WAF/CAPTCHA não observado.

### Quality gate, vazio, estratégia e instruções
ACEITAR estágio, emprego CLT, cargo ou seleção de pessoal. REJEITAR bolsas NAPI sem vínculo, chamadas de projetos e eleições. Empty evidence: `EMPTY_BY_OBSERVATION` para processos abertos em 30/08/2026 (live retest deve confirmar); histórico relevante fechado deve permanecer indexável.

Diagnóstico: `HTML_SUFFICIENT`, `INSTITUTIONAL_FILTER_REQUIRED`, `DEDICATED_CONNECTOR_RECOMMENDED`. Estratégia: `HYBRID` (HTML índice + PDF/atos). Instruções Codex: 1) usar `/Pagina/Processos-Seletivos`; 2) extrair cada bloco PS e links de edital/resultado; 3) identificar prazo e resultado para status; 4) incluir PS 01–04/2026 como fixtures de estágio encerrado; 5) incluir concurso CLT 01.001/2025 como fixture de emprego; 6) excluir NAPI/bolsas sem contrato; 7) testar deduplicação de atos.

**Confidence: HIGH** para estrutura e exemplos; MEDIUM para active=0, dependente do reteste temporal. Evidências: `https://www.fappr.pr.gov.br/Pagina/Processos-Seletivos`; `https://www.fappr.pr.gov.br/Pagina/Atos-Notas-e-Comunicados`; PDF do concurso CLT acima.

## 87 — FAPESC

**Identidade.** Identificador `fapesc_selection`; URL fornecida `https://fapesc.sc.gov.br`; URL oficial confirmada `https://fapesc.sc.gov.br/`. Portal ativo: SIM. Listagem confirmada: `https://fapesc.sc.gov.br/chamadas-abertas/`; há também chamadas em andamento, encerradas, resultados e comunicados.

### Universo e exemplo
Observed: UNKNOWN; a página lista várias chamadas públicas de 2026. Relevant: 0 de contratação/emprego confirmado; Active: 0 no escopo de pessoal; Closed: UNKNOWN; Out of scope: chamadas de pesquisa, inovação, bolsas e submissão de propostas. Exemplo atual: **Edital FAPESC nº 49/2026 — bolsas de produção científica e tecnológica**, listado como chamada aberta; rejeitar. Exemplo de oportunidade com profissionais: chamada Ciasc nº 22/2026, até 16 bolsas, seleção de bolsistas — também fora do escopo de emprego.

### Listagem, campos e documentos
Estrutura: página de categoria com cabeçalhos “Chamadas abertas”, “Chamadas em andamento”, “Divulgação de resultados”, “Chamadas encerradas”; cada item título/data/link, anexos PDF no detalhe. Selector exato: UNKNOWN. Paginação: não confirmada. Título, data, link e status editorial = HTML; objetivo, elegibilidade, valores e cronograma = PDF; cargo, salário e prova = NÃO DISPONÍVEIS em chamadas de bolsa; submissão = Plataforma Fapesc externa. Publicações: edital, retificações, resultados, comunicados; deduplicar por número da chamada e tipo. Ruídos: newsletter, notícias, formulário/plataforma, banners.

API/XHR: nenhum endpoint público confirmado. Tecnologia: `WORDPRESS`/`SERVER_RENDERED` (PDFs em `wp-content/uploads` e páginas de categoria); HTTP SIM; JS/Playwright NÃO demonstrado; WAF/CAPTCHA não observado.

### Quality gate, vazio, estratégia e instruções
ACEITAR somente edital explicitamente de emprego/cargo/função/estágio; REJEITAR bolsas mesmo que usem “vagas” e “processo seletivo”. Empty evidence: `OUT_OF_SCOPE` (há chamadas abertas, mas sem pessoal confirmado). Diagnóstico: `HTML_SUFFICIENT`, `INSTITUTIONAL_FILTER_REQUIRED`, `OUT_OF_SCOPE`. Estratégia: `CONFIGURABLE_HTML` + `KEEP_EMPTY`; não usar a Plataforma Fapesc para login/submissão.

Instruções Codex: 1) percorrer `/chamadas-abertas/`, `/chamadas-em-andamento/`, resultados e encerradas; 2) seguir posts e PDFs; 3) filtrar contratação/emprego/estágio; 4) excluir bolsa/projeto/auxílio; 5) fixture negativo FAPESC/EPAGRI 49/2026 e Ciasc 22/2026; 6) não inventar API da Plataforma Fapesc.

**Confidence: HIGH** para escopo e navegação; MEDIUM para classificação CMS/paginação. Evidências: `https://fapesc.sc.gov.br/chamadas-abertas/`; `https://fapesc.sc.gov.br/duvidas-frequentes/`; `https://fapesc.sc.gov.br/edital-de-bolsas-para-o-programa-de-inovacao-do-ciasc-com-inscricoes-prorrogadas/`.

## 88 — FAPERGS

**Identidade.** Identificador `fapergs_selection`; URL fornecida/oficial `https://fapergs.rs.gov.br/selecao-2025`. Portal ativo: SIM como arquivo oficial; processo selecionado: ENCERRADO.

### Universo e exemplo
Observed: 1 página de processo seletivo pessoal; Relevant: 1; Active: 0; Closed: 1; Out of scope: chamadas/bolsas do restante do portal. Exemplo: **Edital nº 01/2025 — Processo Seletivo Simplificado para contratação temporária de cinco Agentes Administrativos, CLT**, status explicitamente “Processo Seletivo ENCERRADO”. A página tem terceira chamada e todos os resultados.

### Listagem, campos, documentos, tecnologia
Não há índice genérico separado para processos; página de detalhe é a listagem oficial do PSS. Container/selector: HTML sem selector confirmado; paginação: não aplicável. Título, status e links de anexos = HTML; cargo, vagas, requisitos, etapas, remuneração e datas = PDF do edital; resultados/listas/convocações = PDFs. `link_edital` e documentos estão em “Arquivos anexos”; inscrição atual não disponível porque encerrado.

Publicações: edital, formulário, retificação, listas de inscritos, notas, entrevistas, resultado final, homologação e convocações DOE (múltiplas chamadas). Deduplicar por nome do anexo/URL; ruído: relatórios de gestão, menu de chamadas/bolsas. API/XHR: nenhum endpoint público evidenciado. Tecnologia: `SERVER_RENDERED`/CMS PROCERGS (rodapé “Desenvolvido pela PROCERGS”); HTTP SIM; JS/Playwright NÃO necessário; WAF/CAPTCHA não observado.

### Quality gate, vazio, estratégia e instruções
ACEITAR porque o título e o PDF explicitam contratação temporária de agentes administrativos. REJEITAR chamadas de fomento/bolsa. Empty evidence: `EMPTY_BY_OBSERVATION` para pessoal ativo, mas preservar o registro histórico fechado para convocações.

Diagnóstico: `CRAWLER_STRATEGY_CLEAR`, `HTML_SUFFICIENT`, `DEDICATED_CONNECTOR_RECOMMENDED`, `EMPTY_CORRECT`. Estratégia: `HYBRID` (detalhe HTML + anexos PDF). Instruções Codex: 1) usar `https://fapergs.rs.gov.br/selecao-2025`; 2) extrair o texto de status “ENCERRADO”; 3) coletar todos os links em “Arquivos anexos”; 4) indexar edital, retificação, listas, resultados, homologação e convocações; 5) criar fixture com cinco agentes administrativos e status fechado; 6) não contar anexos como concursos distintos.

**Confidence: HIGH**. Evidências: `https://fapergs.rs.gov.br/selecao-2025`; edital/anexos vinculados na mesma página; `https://fapergs.rs.gov.br/`.

## 89 — FUNDECT

**Identidade.** Identificador `fundect_selection`; URL fornecida/oficial `https://www.fundect.ms.gov.br/informativos/consultas/`. Portal ativo: SIM. Categorias oficiais: consultas, chamadas abertas/em andamento/encerradas, formulários e SIGFUNDECT.

### Universo e exemplo
Observed: listagem HTML tabular com itens de 2024–2026; total exato UNKNOWN. Relevant: 1 seleção pública de cargo confirmada — Diretor-Presidente (Chamada FUNDECT nº 001/2025/CS); Active: 0; Closed: 1 (nomeação 16/12/2025); Out of scope: chamadas PAE, PICTEC, Water4All, Biodiversa+, ERC, bolsas e projetos.

Exemplo relevante: **Seleção Pública de Candidatos para preenchimento do cargo de Diretor-Presidente da FUNDECT, triênio 2026–2028**, detalhe `https://www.fundect.ms.gov.br/selecao-publica-de-candidatos-para-preenchimento-do-cargo-de-diretor-presidente-da-fundect-para-mandatoreferente-ao-trienio-2026-2028/`. A página informa lista tríplice, dedicação exclusiva, remuneração por cargo em comissão e registra análise, homologação, convocação e nomeação.

### Listagem, campos, documentos, API e tecnologia
Estrutura: tabela/lista HTML com colunas Nome, Assunto e Tramitação; links “Leitura”, “Acessar proposta” e observações de DOE/anexos. Filtros por ano 2024/2025/2026 e busca aparecem no HTML. Selector exato: UNKNOWN. Paginação: não confirmada; seguir filtros/links de ano e categoria. Título/assunto/status/data/link = HTML; cargo, dedicação, remuneração e etapas = detalhe/PDF/DOE; vagas = detalhe quando expressas; salário/prova/taxa = PDF ou NÃO DISPONÍVEL; documentos e anexos = links HTML/PDF.

Publicações: edital/chamada, retificações, enquadramento, resultados, homologação, convocação e nomeação; deduplicar por chamada/número + tipo + data. Ruído: links SIGFUNDECT, formulários editáveis, boletins, notícias e tabelas de bolsas. API/XHR: nenhum endpoint público confirmado; SIGFUNDECT é sistema externo e pode exigir autenticação. Tecnologia: `WORDPRESS`/`SERVER_RENDERED` (páginas e uploads); HTTP SIM; JS/Playwright não demonstrado; WAF/CAPTCHA não observado.

### Quality gate, vazio, estratégia e instruções
ACEITAR somente cargos/funções/emprego/estágio com processo de seleção de pessoa. REJEITAR seleção de propostas, financiamento, bolsas e eventos. Empty evidence: `EMPTY_BY_OBSERVATION` para seleção de pessoal ativa; manter o Diretor-Presidente como fechado histórico. Diagnóstico: `HTML_SUFFICIENT`, `INSTITUTIONAL_FILTER_REQUIRED`, `DEDICATED_CONNECTOR_RECOMMENDED`, `EMPTY_CORRECT`. Estratégia: `HYBRID` (tabela HTML + detalhe/PDF/DOE).

Instruções Codex: 1) iniciar em `/informativos/consultas/`; 2) percorrer anos e categorias; 3) usar assunto/tramitação para separar “Em andamento” de “Finalizado”; 4) seguir o detalhe do Diretor-Presidente e documentos DOE; 5) excluir PAE/PICTEC/Water4All e demais chamadas de projeto/bolsa; 6) não contar anexos como itens; 7) testar status fechado e deduplicação de observações/retificações; 8) não acessar SIGFUNDECT autenticado para discovery.

**Confidence: HIGH** para estrutura, exemplo e escopo; MEDIUM para tecnologia CMS/paginação. Evidências: `https://www.fundect.ms.gov.br/informativos/consultas/`; `https://www.fundect.ms.gov.br/selecao-publica-de-candidatos-para-preenchimento-do-cargo-de-diretor-presidente-da-fundect-para-mandatoreferente-ao-trienio-2026-2028/`; `https://www.fundect.ms.gov.br/editais-anteriores/`.

# Síntese operacional do BATCH 07

## Oportunidades de plataforma compartilhada

| Cluster | Fontes | Evidência comum | Conector compartilhado | Confiança |
|---|---|---|---|---|
| WordPress/editorial com posts, categorias, PDFs em uploads | FAPEMA, FAPEAL, FAPESB, FAPESC, FUNDECT (FACEPE também aparenta mesma família de publicação) | rotas de categoria/post e documentos PDF; filtros editoriais | **Possível** conector HTML genérico com configuração por URL e filtro institucional; não presumir API comum | MEDIUM |
| CMS governamental server-rendered | FAPPR, FAPERGS | páginas institucionais com blocos de conteúdo e anexos | Parcialmente compartilhável (HTML + PDF), seletores por tenant | MEDIUM |
| Sistema externo de submissão/inscrição | FACEPE/AgilFAP, FAPESB/SIGA + `selecao.ba.gov.br`, FAPESC Plataforma, FAPEAL/eFAP, FAPERJ/SisFAPERJ, FUNDECT/SIGFUNDECT | links externos explícitos | Não usar para discovery nem autenticação; armazenar apenas link de inscrição | HIGH |

Não foi encontrada evidência de API REST/XHR pública estável que justifique conector API compartilhado. Casos LOW–MEDIUM para revisão do Sol: FAPECE (identificador/domínio aparentemente incorreto), FAPERN (503 e portal não verificável), FAPESB (índice FAPESB + portal REDA externo), FACEPE (seleção simplificada histórica versus maioria de bolsas), FAPPR (estágio relevante misturado com bolsas) e FAPESP (109 oportunidades abertas, todas explicitamente bolsas/out of scope).

## Resumo de estratégia

- **P0/P1:** FAPESB REDA 001/2026, FACEPE seleção simplificada histórica, FAPPR concurso CLT/estágios e FAPERGS PSS — manter fixtures e filtros de pessoal.
- **P2:** FAPEMA, FAPEAL, FAPESC, FUNDECT — conector HTML/PDF configurável com filtro institucional; não transformar chamadas em concursos.
- **P5/P6:** FAPERN — manter bloqueado até o portal retornar; FAPECE — revisão de identidade antes de qualquer crawler.
- **P7:** FAPESP (109 bolsas), FAPEMA/FAPEAL/FAPESC/FAPERJ e demais chamadas de fomento — empty/out-of-scope legítimo para o Observador, preservando evidência.

## Quality gate transversal

1. “Edital”, “seleção” ou “vagas” não bastam: exigir contratação/emprego/cargo/função/estágio ou processo seletivo de pessoal no texto oficial.
2. Bolsas, auxílio, fomento, prêmio, projeto, proposta e chamada científica ficam fora do universo relevante salvo evidência explícita de vínculo de pessoal.
3. Nunca converter UNKNOWN em zero, nem usar contagem de posts/anexos como active count.
4. Documentos PDF são fonte de campos de cargo, vagas, remuneração e cronograma; HTML é fonte de título, status editorial e links.
5. Toda alteração deve ter fixture real, teste de exclusão de bolsa/fomento e live retest no fuso `America/Sao_Paulo`.
