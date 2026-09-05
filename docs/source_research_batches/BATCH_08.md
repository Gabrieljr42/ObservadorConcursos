# BATCH 08 — fontes 90–99

Pesquisa externa realizada em 2026-08-30, 18:07–18:35 (America/Sao_Paulo, UTC−03:00). A classificação `Relevant` abaixo significa seleção de pessoas para trabalho (concurso, PSS, contratação temporária, emprego, estágio ou função). Bolsas, fomento, premiações, chamadas de projetos e submissão de propostas são mantidos como `Out of scope`.

## 90 — FAPEMAT

### 1. Identidade

- Nome: Fundação de Amparo à Pesquisa do Estado de Mato Grosso (FAPEMAT).
- Identificador técnico: `fapemat_selection`.
- URL inicial fornecida: <https://fapemat.mt.gov.br>.
- URL oficial atual confirmada: <https://www.fapemat.mt.gov.br/pt/editais_1> (a página institucional também aparece em `/web/fapemat/inicio`). O domínio continua oficial, sem migração confirmada.
- Portal ativo: PARCIAL. A página `/pt/editais_1` é indexada, mas a abertura direta pela ferramenta recebeu timeout/Request Rejected; o conteúdo de navegação é recuperável por indexação.
- Tecnologia observada: portal governamental MT com padrões Liferay (`/web/...`, `/documents/...` e parâmetros `com_liferay_asset_publisher...`).

### 2. Mapa do portal

- Homepage: <https://www.fapemat.mt.gov.br/pt/inicio> (URL institucional equivalente encontrada na navegação).
- Editais: <https://www.fapemat.mt.gov.br/pt/editais_1>; separadores visíveis `Abertos`, `Encerrados`, `Resultado` e `Oculto`.
- Submissão: SIGFAPEMAT em <https://sigfap.fapemat.mt.gov.br/index.php>.
- Pessoal: item de menu `Pessoal` existe no portal; não foi localizada uma listagem de vagas/concursos da FAPEMAT.
- Documentos: links PDF em `/documents/363786/...`; exemplo real <https://www.fapemat.mt.gov.br/documents/363786/74177988/Edital%2B012_2025%2B-%2BCentelha%2B3%2B-%2BMT.pdf/ebd83a0c-01d3-097c-1d52-3b18ea90e318>.
- Resultados: ficam em páginas/links do item de edital e, em alguns programas, no Programa Centelha/SIGFAPEMAT.

### 3. Universo atual observado

- Observed: UNKNOWN (os itens dos separadores não foram entregues pelo HTML indexado; somente os nomes dos separadores foram observados).
- Relevant: 0 encontrados nas páginas FAPEMAT consultadas; isso não afirma que o portal inteiro não possa conter publicação histórica não indexada.
- Active: 0 seleções de pessoal confirmadas; não converter em zero do universo total.
- Closed: UNKNOWN.
- Out of scope: editais de pesquisa, premiações, Centelha/subvenção e bolsas; as páginas SECITEC/SEDUC hospedadas no mesmo domínio são de outros órgãos. A página SECITEC indexada mostra PSS de professores e técnicos, mas não deve ser atribuído à FAPEMAT.

### 4. Listagem

- Estrutura: `/pt/editais_1` entrega o cabeçalho e abas, mas os cards/linhas dos itens não foram renderizados no acesso disponível.
- Selector/container, título, link, ID e status: UNKNOWN; não inventar CSS. No portal Liferay, a listagem é plausivelmente um Asset Publisher, mas isso é apenas pista técnica dos parâmetros de URL e requer reteste.
- O conteúdo indexado em páginas de subórgãos aparece como títulos e links de documentos PDF; não usar esses itens como listagem FAPEMAT sem verificar o órgão.

### 5. Paginação

- Aba de editais: UNKNOWN; nenhum controle de paginação foi observável.
- Nas páginas Liferay de outros órgãos, há parâmetros `cur`/`delta` do Asset Publisher; não há evidência de que se apliquem à listagem FAPEMAT.

### 6. Exemplo real

- Título: Edital nº 012/2025 — Programa Centelha 3 (MT), prorrogação de cronograma.
- Órgão: FAPEMAT.
- Status: encerrado por cronograma documental (a fase 2 terminou em 26/03/2026; contratação de projetos prevista para 15/06–17/07/2026).
- URL: PDF oficial acima.
- Edital: PDF; é seleção de projetos/empresas e não contratação de pessoas.

### 7. Campos

Para o exemplo Centelha: `titulo` PDF/HTML (texto do PDF); `orgao` PDF; `modalidade` PDF (subvenção econômica); `cargo`, `cidade`, `uf`, `salario_min`, `salario_max`, `escolaridade`, `taxa`, `prova_data`, `inscricao_inicio`, `inscricao_fim`, `link_inscricao`: NÃO DISPONÍVEL ou fora de escopo; `status`, `edital_numero`, `edital_data`, `link_edital`: PDF/HTML; `vagas`: PDF (até 47 projetos, não vagas de emprego). Não transformar campos ausentes em inferidos.

### 8. Edital e publicações

- O portal disponibiliza PDF do edital, retificações e resultados; o PDF Centelha declara resultados preliminares/finais no portal FAPEMAT e no portal Centelha.
- Ruídos: notícias e páginas de SECITEC, SEDUC e SEDEC compartilham o domínio MT; excluir por órgão antes de classificar como seleção.
- Deduplicação: chave por URL canônica do PDF + número do edital + órgão/programa; não deduplicar apenas pelo título “Edital”.

### 9. API/XHR/backend

- Endpoint público: UNKNOWN. SIGFAPEMAT é sistema separado; a página de perguntas frequentes confirma submissão de propostas via sistema, mas não publica endpoint REST.
- Não foram confirmados `fetch`, XHR, GraphQL, `wp-json` ou JSON embutido.
- Autenticação: o SIGFAPEMAT requer cadastro/login para submissões; não usar essa área como fonte de anúncios.

### 10. Tecnologia, bloqueios e estratégia

- Tipo: `SERVER_RENDERED`/`OTHER` com portal Liferay; PDFs indexados; JS necessário para parte do portal.
- HTTP simples: PARCIAL; a página de editais abriu via indexação, mas o acesso direto retornou timeout/Request Rejected.
- JS: SIM para os componentes dinâmicos; Playwright: provavelmente SIM somente se o HTTP não recuperar as abas.
- WAF/CAPTCHA: Request Rejected/timeout observado; Cloudflare/CAPTCHA não confirmado. Alternativas oficiais: PDF `/documents/...`, SIGFAPEMAT e páginas indexadas.
- Estratégia: `HYBRID` + `KEEP_BLOCKED` quando o acesso direto continuar rejeitado; começar por HTTP/Liferay e PDFs, sem bypass agressivo.

### Quality gate / Empty evidence

- ACEITAR somente publicação explicitamente sobre contratação, cargo, emprego, estágio ou PSS da própria FAPEMAT; separar SECITEC/SEDUC/SEDEC e excluir bolsas/fomento.
- REJEITAR Centelha, pesquisa, premiação, auxílio, bolsa, submissão de projeto e processos de seleção de propostas.
- Situação de vazio: `UNKNOWN_EMPTY` (abas existem, mas os itens não foram renderizados no acesso); não declarar `EMPTY_EXPLICIT`.

### Diagnóstico, recomendação e instruções para Codex

- Diagnóstico: `URL_OUTDATED` (rota inicial é homepage genérica), `PORTAL_MIGRATED` não confirmado, `WAF_BLOCKED`, `INSTITUTIONAL_FILTER_REQUIRED`, `INSUFFICIENT_EVIDENCE`, `CRAWLER_STRATEGY_CLEAR` apenas para PDFs.
- Recomendação: `HYBRID`/`KEEP_BLOCKED` até reteste; não implementar conector de concursos enquanto não houver anúncio de pessoal confirmado.
- Passos: (1) tentar `/pt/editais_1` com HTTP e browser; (2) identificar as abas e o órgão no item; (3) seguir apenas PDFs do namespace FAPEMAT; (4) extrair título/número/data/link do documento; (5) rejeitar `bolsa`, `fomento`, `Centelha`, `pesquisa`, `premiação`, `subvenção`; (6) manter UNKNOWN para contagens e campos que dependem de JS; (7) criar fixture com o PDF Centelha apenas para garantir exclusão.
- Confiança: MEDIUM (domínio/estrutura e exemplos oficiais claros, conteúdo de listagem bloqueado).

### Evidências

<https://www.fapemat.mt.gov.br/pt/editais_1>; <https://www.fapemat.mt.gov.br/documents/363786/74177988/Edital%2B012_2025%2B-%2BCentelha%2B3%2B-%2BMT.pdf/ebd83a0c-01d3-097c-1d52-3b18ea90e318>; <https://www.fapemat.mt.gov.br/pt/perguntas-e-respostas>; <https://sigfap.fapemat.mt.gov.br/index.php>.

## 91 — FAPEG

### 1. Identidade

- Nome: Fundação de Amparo à Pesquisa do Estado de Goiás (FAPEG).
- Identificador técnico: `fapeg_selection`.
- URL inicial fornecida: <https://goias.gov.br/fapeg/categoria/editais/>.
- URL oficial atual confirmada: <https://goias.gov.br/fapeg/editais/>; subpágina operacional <https://goias.gov.br/fapeg/editais/inscricoes-abertas/>. O domínio migrou de páginas antigas `fapeg.go.gov.br` para `goias.gov.br/fapeg`.
- Portal ativo: SIM.

### 2. Mapa do portal

- Editais: `/editais/`, com links `Inscrições Abertas`, `Em Andamento`, `Encerrados`.
- Abertos: `/editais/inscricoes-abertas/`.
- Em andamento: `/editais/em-andamento/` (timeout intermitente no reteste).
- Encerrados: `/editais/encerrados/`.
- Detalhe: página WordPress/Goiás para cada chamada; anexos e resultados são links PDF/XLSX.
- Submissão: Charles Darwin (APEX) e sistemas específicos; não é inscrição para emprego na listagem de editais.

### 3. Universo atual observado

- Observed: 8 itens na página `Inscrições Abertas` em 30/08/2026 (18/2026 a 12/2026).
- Relevant: 0 ativos na página observada; são chamadas de apoio, pesquisa, mobilidade ou bolsas.
- Active: 0 seleções de pessoal confirmadas na página aberta.
- Closed: pelo menos 1 item relevante histórico: Edital de Convocação 01/2024 do PSS para contratação temporária de Analistas de Ciência e Tecnologia; na página de encerrados aparece entre chamadas fechadas. Não contar essa página como ativo.
- Out of scope: chamadas de bolsistas, propostas, auxílio, mobilidade e projetos.

### 4. Listagem

- A página aberta é tabela HTML: colunas `Nº`, `Tipo`, `Origem`, `Descrição`, `Link`; campos de filtro para número/tipo/origem/descrição/link.
- Título/descrição: célula `Descrição`; link: âncora `ABRIR`/`Abrir`; status deriva da página (abertas/encerrados), não de um campo por linha. Selector exato de CSS não foi exposto pela fonte; usar tabelas e cabeçalhos sem inventar classes.
- Há arquivo XLSX de apoio na própria página, útil como fallback, mas não para contar seleções sem filtrar tipo/órgão.

### 5. Paginação

- Páginas de categoria usam paginação WordPress (`/categoria/editais/page/N/`) para o arquivo histórico; `editais/inscricoes-abertas/` mostrou 8 linhas sem paginação visível.
- Percorrer páginas de categoria e as três listas de status; evitar misturar notícias e chamados de bolsas.

### 6. Exemplo real

- Título: Edital de Convocação nº 01/2024 — Processo Seletivo Simplificado para Contratação Temporária de Analistas de Ciência e Tecnologia – Área I.
- Órgão: FAPEG/SEAD Goiás.
- Status: encerrado/homologado; convocações posteriores em 2026 aparecem como atualizações.
- URL: <https://goias.gov.br/fapeg/wp-content/uploads/sites/5/2024/11/Edital_de_Convocacao_PSS_FAPEG_Edital_009_2024.pdf>.
- Edital: PDF oficial; contratação por tempo determinado.

### 7. Campos

- Para o PSS: `titulo`, `orgao`, `cargo` (Analista de Ciência e Tecnologia – Área I), `modalidade` (PSS/contratação temporária), `status`, `edital_numero`, `link_edital`: PDF/HTML.
- `vagas`, `escolaridade`, `salario_min/max`, `inscricao_inicio/fim`, `prova_data`, `taxa`, `cidade`, `uf`, `link_inscricao`: PDF ou NÃO DISPONÍVEL no edital de convocação; a inscrição original foi em `selecao.go.gov.br`, não na tabela FAPEG.
- Para os itens abertos de 2026, todos os campos de cargo/vagas/taxa/prova são NÃO DISPONÍVEIS ou não aplicáveis; são propostas/bolsas.

### 8. Edital e publicações

- Cada linha abre página de detalhe com edital, retificações, resultados preliminares/finais e eventuais FAQs; links de documentos aparecem como texto datado.
- Publicações de PSS: edital de convocação, resultados, homologação e chamadas; deduplicar pelo número do edital + URL do PDF + tipo de publicação.
- Ruídos: chamadas de bolsa e pesquisa usam palavras `seleção`, `processo seletivo` e `contratação` para projetos; filtro por `contratação temporária`, `cargo`, `função`, `analista` é obrigatório.

### 9. API/XHR/backend

- API pública de dados da lista: UNKNOWN. A estrutura aparenta HTML server-rendered com filtro de tabela; não foi confirmado endpoint XHR/REST.
- Charles Darwin é APEX e exige autenticação para submissão; não usar como endpoint de descoberta pública de vagas.

### 10. Tecnologia, bloqueios e estratégia

- Tipo: `SERVER_RENDERED`/`WORDPRESS` (Goiás), tabelas HTML e PDFs; APEX para submissão.
- HTTP simples: SIM para listas e detalhes; JS não necessário para o HTML principal, embora filtros possam ser JS.
- Playwright: NÃO esperado para listagem; fallback se o portal de status falhar.
- Bloqueios: sem WAF/CAPTCHA observado; `/em-andamento/` teve timeout pontual.
- Estratégia: `CONFIGURABLE_HTML` para as três tabelas, com `HTTP_HTML` + parser de PDF para documentos.

### Quality gate / Empty evidence

- ACEITAR somente PSS/convocação para cargo ou contratação temporária da FAPEG; validar que o texto menciona contratação de pessoa.
- REJEITAR chamadas de bolsistas, apoio financeiro, projetos, mobilidade, eventos e fomento.
- Empty: não vazio; há 8 chamadas abertas, mas `Relevant=0` por filtro institucional.

### Diagnóstico, recomendação e instruções para Codex

- Diagnóstico: `CRAWLER_STRATEGY_CLEAR`, `HTML_SUFFICIENT`, `INSTITUTIONAL_FILTER_REQUIRED`, `PORTAL_MIGRATED` (legado FAPEG para Goiás), `GENERIC_CONNECTOR_SUFFICIENT`.
- Recomendação: `CONFIGURABLE_HTML` para captura e `KEEP_EMPTY` no universo de pessoal atual.
- Passos: (1) usar `/editais/inscricoes-abertas/`, `/editais/em-andamento/` e `/editais/encerrados/`; (2) parsear tabela por cabeçalhos, não CSS inventado; (3) seguir `ABRIR`; (4) extrair links PDF/XLSX e publicações; (5) filtrar termos de contratação de pessoa; (6) classificar chamadas de bolsas/projetos como OUT_OF_SCOPE; (7) fixture do PSS 01/2024 deve ficar Closed; (8) retestar os três endpoints após mudança.
- Confiança: HIGH.

### Evidências

<https://goias.gov.br/fapeg/editais/>; <https://goias.gov.br/fapeg/editais/inscricoes-abertas/>; <https://goias.gov.br/fapeg/editais/encerrados/>; <https://goias.gov.br/fapeg/wp-content/uploads/sites/5/2024/11/Edital_de_Convocacao_PSS_FAPEG_Edital_009_2024.pdf>.

## 92 — FAPDF

### 1. Identidade

- Nome: Fundação de Apoio à Pesquisa do Distrito Federal (FAPDF).
- Identificador técnico: `fapdf_selection`.
- URL inicial fornecida: <https://fap.df.gov.br>.
- URL oficial atual confirmada: <https://www.fap.df.gov.br/>; não houve mudança de domínio confirmada.
- Portal ativo: SIM.

### 2. Mapa do portal

- Homepage: `/` com notícias, cards, Diário Oficial e aplicações aninhadas.
- Editais históricos: páginas anuais como <https://www.fap.df.gov.br/editais-fapdf-2020/>; a carta de serviços aponta também `/editais-fapdf-2024/`.
- Sistema de submissão: <https://sigfapdf.fap.df.gov.br/>; requer login.
- Documentos: PDFs em `/documents/d/fap/...` ou `/documents/10489263/...`.
- Não há uma lista atual explícita de concursos/PSS da FAPDF no homepage; editais exibidos são científicos, bolsas, eventos e fomento.

### 3. Universo atual observado

- Observed: UNKNOWN (homepage sem tabela de editais atual; páginas anuais são arquivos heterogêneos).
- Relevant: 0 seleções de pessoal encontradas nas páginas consultadas.
- Active: 0 confirmados; o site menciona programas de fomento e chamadas, não vagas de emprego.
- Closed: UNKNOWN para o universo completo.
- Out of scope: editais de propostas, bolsas, premiações, credenciamento ad hoc, apoio a eventos e submissão via SIGFAPDF.

### 4. Listagem

- Não existe uma listagem única atual confirmada. Páginas anuais apresentam texto longo com títulos e links de editais/resultados.
- Homepage possui cards de notícias e busca do Diário Oficial; não usar como listagem de concursos.
- Selector/container, ID e status por item: UNKNOWN; não inventar classes.

### 5. Paginação

- Notícias usam paginação WordPress/Liferay-like (`?page=N` observado em categoria); páginas anuais não têm paginação de certames confirmada.
- Para cobertura, percorrer páginas anuais de editais + categoria Notícias, mas sempre aplicar filtro institucional e de pessoal.

### 6. Exemplo real

- Título: Edital nº 09/2025 — Credenciamento de Consultores ad hoc.
- Órgão: FAPDF.
- Status: edital de credenciamento/avaliação de projetos, fora do escopo de contratação; página oficial em PDF.
- URL: <https://www.fap.df.gov.br/documents/d/fap/sei-00193-00000286_2025-33-edital-n-09-2025-credeciamento-consultores-ad-hoc-pdf>.
- Edital: PDF; apesar de usar “candidatos” e seleção, forma banco de consultores ad hoc, não cargo/emprego.

### 7. Campos

- Exemplo ad hoc: `titulo`, `orgao`, `modalidade`, `status`, `edital_numero`, `edital_data`, `link_edital`: HTML/PDF.
- `cargo`, `vagas`, `salario`, `inscricao`, `prova`, `taxa`, `cidade`, `uf`, `link_inscricao`: NÃO DISPONÍVEL/fora de escopo.
- Itens de fomento podem conter valores e cronogramas, mas nunca mapear esses valores como salário ou vagas de pessoal.

### 8. Edital e publicações

- Páginas anuais agrupam edital, retificações, extrato DODF, resultados e relatórios; PDFs oficiais em `documents/d/fap`.
- DODF e SIGFAPDF são fontes complementares indicadas pelo próprio edital; submissões autenticadas não são discovery de pessoal.
- Ruídos: cards de notícias, licitações, contratos, MROSC e bolsas; deduplicar por SEI/edital e URL do PDF.

### 9. API/XHR/backend

- API pública: UNKNOWN. SIGFAPDF é aplicação autenticada; não há endpoint público confirmado.
- Site usa aplicações aninhadas e documentos SEI; não foi confirmado `wp-json`, GraphQL ou XHR de edital.

### 10. Tecnologia, bloqueios e estratégia

- Tipo: `SERVER_RENDERED`/`OTHER`, portal governamental com PDFs e aplicações; homepage entregue por HTTP.
- HTTP simples: SIM para homepage, páginas anuais e PDFs; JS não necessário para documentos.
- Playwright: NÃO para páginas estáticas; pode ser necessário apenas para SIGFAPDF autenticado, que não deve ser usado pelo crawler.
- Bloqueios: nenhum WAF/CAPTCHA observado.
- Estratégia: `HTTP_HTML`/`CONFIGURABLE_HTML` para páginas anuais; `KEEP_EMPTY` para seleção de pessoal.

### Quality gate / Empty evidence

- ACEITAR somente anúncio que diga contratação, cargo, estágio ou PSS de pessoal da FAPDF.
- REJEITAR credenciamento ad hoc, seleção de projetos, bolsas e apoio financeiro.
- Empty: `UNKNOWN_EMPTY` para o universo total; `Relevant=0` por observação das páginas oficiais atuais.

### Diagnóstico, recomendação e instruções para Codex

- Diagnóstico: `INSTITUTIONAL_FILTER_REQUIRED`, `HTML_SUFFICIENT`, `INSUFFICIENT_EVIDENCE`, `GENERIC_CONNECTOR_SUFFICIENT`.
- Recomendação: `KEEP_EMPTY` + `HTTP_HTML` apenas para manter observação periódica; não usar SIGFAPDF login.
- Passos: (1) monitorar homepage e páginas anuais; (2) coletar apenas itens cujo título/descrição contenha contratação/cargo/estágio/PSS; (3) seguir PDF e DODF; (4) ignorar o Edital 09/2025 ad hoc e demais fomento; (5) manter contagens UNKNOWN quando a página anual não expuser universo.
- Confiança: MEDIUM.

### Evidências

<https://www.fap.df.gov.br/>; <https://www.fap.df.gov.br/editais-fapdf-2020/>; <https://www.fap.df.gov.br/documents/d/fap/sei-00193-00000286_2025-33-edital-n-09-2025-credeciamento-consultores-ad-hoc-pdf>; <https://sigfapdf.fap.df.gov.br/>.

## 93 — FAPT

### 1. Identidade

- Nome: Fundação de Amparo à Pesquisa do Estado do Tocantins (FAPT).
- Identificador técnico: `fapt_selection`.
- URL inicial fornecida: <https://fapt.to.gov.br>.
- URL oficial atual: o domínio fornecido continua referenciado em PDFs oficiais, mas abriu timeout no reteste. Evidência governamental atual está em PDFs `central.to.gov.br` e na página CAPES da FAPT.
- Portal ativo: INCERTO/possivelmente desatualizado.
- URL mudou: NÃO CONFIRMADO; não substituir por FAPTO (Fundação de Apoio Científico e Tecnológico do Tocantins), que é entidade diferente.

### 2. Mapa do portal

- Homepage/editais: não recuperados diretamente.
- Documentos oficiais alternativos: <https://central.to.gov.br/download/368536> (Edital FAPT 01/2024 Rosas da Ciência) e <https://www.gov.br/capes/pt-br/acesso-a-informacao/acoes-e-programas/bolsas/programas-estrategicos/outras-informacoes/fundacoes-estaduais-de-amparo-a-pesquisa-faps/fundacao-de-amparo-a-pesquisa-do-estado-do-tocantins-fapt>.
- Submissão: edital Rosas da Ciência orienta envio conforme o edital e divulga resultados na página FAPT; sistema atual não confirmado.

### 3. Universo atual observado

- Observed: UNKNOWN; o portal principal expirou em timeout.
- Relevant: UNKNOWN (nenhuma seleção de pessoal confirmada).
- Active: UNKNOWN.
- Closed: pelo menos 1 edital oficial histórico (Rosas da Ciência 01/2024), de fomento à produção científica, fora do escopo.
- Out of scope: pesquisa/fomento/bolsa, PDPG e chamadas de propostas.

### 4. Listagem e paginação

- Listagem, container, selectors, status e paginação: UNKNOWN devido ao timeout da homepage.
- Não inventar URLs de “abertos” ou “encerrados”. PDFs oficiais são documentos isolados, não listagem.

### 5. Exemplo real

- Título: Edital FAPT nº 01/2024 — Rosas da Ciência — Fomento à Produção Científica a Pesquisadoras no Estado do Tocantins.
- Órgão: FAPT/Secretaria de Estado da Mulher.
- Status: encerrado (cronograma de divulgação final até 18/06/2024).
- URL: <https://central.to.gov.br/download/368536>.
- Edital: PDF, com bolsa e itens de custeio/capital para projeto; não contratação de pessoal.

### 6. Campos

- `titulo`, `orgao`, `modalidade`, `status`, `edital_numero`, `edital_data`, `link_edital`: PDF.
- `cargo`, `vagas`, `salario`, `taxa`, `prova`, `inscricao_inicio/fim`, `link_inscricao`: NÃO DISPONÍVEL/fora de escopo.
- O PDF contém valores de bolsa e orçamento do projeto; não parsear como salário/vagas.

### 7. Edital/publicações e API

- O PDF descreve cronograma, análise de enquadramento/mérito/homologação, recursos e divulgação final; não há página de detalhe web confirmada.
- API/XHR/JSON/SharePoint: UNKNOWN. Não há endpoint público confirmado.
- Autenticação: não determinada; não acessar áreas de submissão sem necessidade.

### 8. Tecnologia, bloqueios e estratégia

- Tipo: `PDF_INDEX`/`OTHER`; portal não acessível na consulta direta.
- HTTP simples: NÃO (timeout no domínio); JS/Playwright: UNKNOWN; WAF/CAPTCHA: não confirmado.
- Alternativa: PDFs `central.to.gov.br`, CAPES e Diário Oficial; não equivalem a feed completo.
- Estratégia: `KEEP_BLOCKED` + `DEPRECATE_REVIEW_REQUIRED` até confirmar URL operacional; monitorar PDFs oficiais indexados apenas como fallback.

### Quality gate / Empty evidence

- ACEITAR somente eventual edital que explicite contratação, cargo, emprego, estágio ou PSS de pessoas pela FAPT.
- REJEITAR Rosas da Ciência, PDPG, bolsas e chamadas de projetos.
- Empty: `UNKNOWN_EMPTY` (portal inacessível; ausência de listagem não prova vazio).

### Diagnóstico, recomendação e instruções para Codex

- Diagnóstico: `SITE_OFFLINE`, `URL_OUTDATED`/`INSUFFICIENT_EVIDENCE`, `INSTITUTIONAL_FILTER_REQUIRED`, `OUT_OF_SCOPE` para os PDFs encontrados.
- Recomendação: `KEEP_BLOCKED` e revisão de depreciação, sem crawler ativo de concursos.
- Passos: (1) retestar `https://fapt.to.gov.br` com HTTP e browser; (2) verificar eventual redirecionamento oficial no portal TO; (3) não confundir FAPT com FAPTO; (4) se não houver feed, manter bloqueada e registrar PDFs como evidência; (5) filtrar bolsas/fomento; (6) criar teste de “site indisponível” que não produza zero ativo falso.
- Confiança: MEDIUM (evidência oficial de identidade e edital, baixa observabilidade do portal).

### Evidências

<https://fapt.to.gov.br>; <https://central.to.gov.br/download/368536>; <https://www.gov.br/capes/pt-br/acesso-a-informacao/acoes-e-programas/bolsas/programas-estrategicos/outras-informacoes/fundacoes-estaduais-de-amparo-a-pesquisa-faps/fundacao-de-amparo-a-pesquisa-do-estado-do-tocantins-fapt>.

## 94 — FAPEAM

### 1. Identidade

- Nome: Fundação de Amparo à Pesquisa do Estado do Amazonas (FAPEAM).
- Identificador técnico: `fapeam_selection`.
- URL inicial fornecida: <https://fapeam.am.gov.br>.
- URL oficial atual confirmada: <https://www.fapeam.am.gov.br/>; o domínio redireciona para `www`.
- Portal ativo: SIM, com restrição eleitoral e componentes dinâmicos.

### 2. Mapa do portal

- Homepage: `/` com serviços essenciais, inclusive `Editais: Vigentes | Fluxo Contínuo | Encerrados | Resultados`.
- Editais: <https://www.fapeam.am.gov.br/editais/>.
- Resultados: <https://www.fapeam.am.gov.br/resultados/>.
- Oportunidades: <https://www.fapeam.am.gov.br/oportunidades/>.
- Documentos: páginas de detalhe em `/editais/.../` com botão/arquivo PDF; resultados e publicações em categorias do WordPress.
- Sistemas de submissão: SIGFAPEAM (login/cadastro); não confundir com inscrição de emprego.

### 3. Universo atual observado

- Observed: UNKNOWN na página `/editais/`: HTML exibiu placeholders Vue (`{{ tab.label }}`, `Carregando...`) e mensagem template `Não existem ...`; itens concretos não foram renderizados no acesso textual.
- Relevant: UNKNOWN (nenhum anúncio de contratação de pessoal confirmado no feed; editais concretos localizados são pesquisa, bolsas, auxílio e pré-seleção de propostas).
- Active: UNKNOWN; não converter placeholders em zero.
- Closed: UNKNOWN.
- Out of scope: chamadas FAPEAM de propostas, bolsas, auxílios, premiações e contratação de projetos.

### 4. Listagem e paginação

- A página de editais usa abas dinâmicas por status e período de vigência; os itens são preenchidos após JavaScript.
- Container/selector, título/link/status e paginação: UNKNOWN; não inventar seletores.
- Resultados têm busca e filtros `Ano`/tags na página `/resultados/`; não é lista de vagas.

### 5. Exemplo real

- Título: Edital nº 015/2026 — Pré-seleção de Redes Estratégicas de Pesquisa e Pós-Graduação da Amazônia Legal (PDPG).
- Órgão: FAPEAM/CAPES.
- Status: chamada de propostas, fora do escopo de pessoal.
- URL: <https://www.fapeam.am.gov.br/editais/edital-n-o-015-2026-edital-fapeam-de-pre-selecao-de-redes-estrategicas-de-pesquisa-e-pos-graduacao-da-amazonia-legal-programa-de-desenvolvimento-da-pos-graduacao-pdpg-parcerias-estrate/>.
- Edital: página de detalhe com PDF oficial.

### 6. Campos

- Para o exemplo: `titulo`, `orgao`, `modalidade` (pré-seleção de propostas), `status`, `edital_numero`, `edital_data`, `link_edital`: HTML/PDF.
- `cargo`, `vagas`, `salario`, `taxa`, `prova`, `inscricao_inicio/fim`, `link_inscricao`: NÃO DISPONÍVEL ou fora de escopo.
- Os detalhes usam cronograma de submissão/contratação de projetos; não mapear “contratação” de projeto para cargo.

### 7. Edital/publicações e API

- Detalhes de edital contêm edital, resoluções, retificações e resultados; páginas de resultados usam busca por ano/tag.
- A página `/editais/` claramente requer JS para popular abas, mas endpoint XHR não foi exposto pelo acesso textual. `fetch`/REST/GraphQL/`wp-json`: UNKNOWN.
- SIGFAPEAM exige autenticação; não usar login como discovery.

### 8. Tecnologia, bloqueios e estratégia

- Tipo: `WORDPRESS` + `REACT_SPA`/componente Vue não confirmado; placeholders indicam frontend dinâmico.
- HTTP simples: PARCIAL (homepage, detalhes e resultados; listagem de editais sem itens); JS: SIM para abas; Playwright: provavelmente SIM se endpoint não for descoberto.
- Bloqueios: nenhum WAF/CAPTCHA; restrição eleitoral explícita no homepage.
- Estratégia: `HYBRID`/`PLAYWRIGHT` para o feed, com fallback de páginas de detalhe e resultados; `INSTITUTIONAL_FILTER_REQUIRED`.

### Quality gate / Empty evidence

- ACEITAR apenas anúncio de emprego, estágio, cargo, função ou PSS de pessoal da FAPEAM.
- REJEITAR bolsas, auxílio, pré-seleção de redes, projetos, chamadas científicas e “contratação” de propostas.
- Empty: `UNKNOWN_EMPTY`, pois o feed dinâmico não carregou seus itens; não usar a mensagem template como `EMPTY_EXPLICIT`.

### Diagnóstico, recomendação e instruções para Codex

- Diagnóstico: `BROWSER_REQUIRED`, `API_AVAILABLE` não confirmado, `INSTITUTIONAL_FILTER_REQUIRED`, `INSUFFICIENT_EVIDENCE`, `GENERIC_CONNECTOR_SUFFICIENT`.
- Recomendação: `HYBRID` (HTTP + Playwright somente para a lista) e `KEEP_EMPTY`/UNKNOWN para pessoal.
- Passos: (1) abrir `/editais/` em navegador e capturar chamada XHR responsável por `vigentes/fluxo contínuo/encerrados/resultados`; (2) preferir endpoint público se existir; (3) seguir detalhe e PDFs; (4) filtrar cargo/emprego/estágio/PSS; (5) rejeitar bolsas/fomento; (6) fixture PDPG deve testar exclusão; (7) não transformar placeholder em lista vazia.
- Confiança: MEDIUM.

### Evidências

<https://www.fapeam.am.gov.br/>; <https://www.fapeam.am.gov.br/editais/>; <https://www.fapeam.am.gov.br/resultados/>; <https://www.fapeam.am.gov.br/editais/edital-n-o-015-2026-edital-fapeam-de-pre-selecao-de-redes-estrategicas-de-pesquisa-e-pos-graduacao-da-amazonia-legal-programa-de-desenvolvimento-da-pos-graduacao-pdpg-parcerias-estrate/>.

## 95 — FAPESPA

### 1. Identidade

- Nome: Fundação Amazônia de Amparo a Estudos e Pesquisas (FAPESPA).
- Identificador técnico: `fapespa_selection`.
- URL inicial fornecida: <https://fapespa.pa.gov.br>.
- URL oficial atual confirmada: <https://www.fapespa.pa.gov.br/> (redireciona de sem `www`).
- Portal ativo: SIM.

### 2. Mapa do portal

- Homepage: `/`.
- Chamadas: <https://www.fapespa.pa.gov.br/chamadas/>.
- Publicações: <https://www.fapespa.pa.gov.br/publicacoes/> (menu `PUBLICAÇÕES`).
- Recursos humanos: <https://www.fapespa.pa.gov.br/recursos-humanos/>.
- Detalhe/documentos: páginas WordPress e PDFs em `/wp-content/uploads/...`.
- Inscrição para PSS: plataforma externa SIPROS, <https://www.sipros.pa.gov.br>.

### 3. Universo atual observado

- Observed: 4 blocos de chamadas na página `/chamadas/` (012/2025, 011/2025, 010/2025 e PSS 001/2025).
- Relevant: 1 (PSS 001/2025 para contratação temporária de nível superior).
- Active: 0; o cronograma de inscrição foi 01–02/07/2025 e resultado final 17/07/2025.
- Closed: 1 relevante (PSS 001/2025) + chamadas de bolsas/projetos fechadas ou sem status; não somar blocos sem estado explícito.
- Out of scope: chamadas 010/012 de bolsas e Connect Amazônia/propostas de pesquisadores.

### 4. Listagem

- `/chamadas/` é HTML WordPress com blocos de título/descrição e links sucessivos para edital, inscrição, resultado preliminar/final e retificações.
- Não há tabela nem paginação visível na página observada; container/selector CSS exato não foi confirmado. Use hierarquia de headings, links e texto do bloco sem inventar classes.
- Status deriva do cronograma/documento; a página não fornece um campo status por card.

### 5. Paginação

- `/chamadas/` não mostrou paginação na captura; histórico pode estar em páginas WordPress/arquivos de publicação.
- Percorrer links de cada bloco e `/recursos-humanos/`; seguir SIPROS para etapas do PSS.

### 6. Exemplo real

- Título: Edital nº 001/2025 PSS/FAPESPA — Processo Seletivo Simplificado para Contratação Temporária — Nível Superior.
- Órgão: FAPESPA.
- Status: encerrado; resultado final e agendamento de apresentação publicados em julho/2025.
- URL edital: <https://www.fapespa.pa.gov.br/wp-content/uploads/2025/07/EDITAL-001-2025-VIGENTE.pdf>.
- Resultado: <https://www.fapespa.pa.gov.br/wp-content/uploads/2025/07/11.-RESULTADO-FINAL-PSS-001.2025-FAPESPA-1.pdf>.
- Vagas: 8 (2 Administração, 3 Economia, 3 Estatística), conforme Anexo I do PDF.

### 7. Campos

- `titulo`, `orgao`, `modalidade`, `cargo`, `area`, `status`, `vagas`, `salario_min/max`, `escolaridade`, `prova_data`, `edital_numero`, `edital_data`, `inscricao_inicio/fim`, `link_edital`: PDF do edital.
- `link_inscricao`: SIPROS; o edital informa inscrição 01–02/07/2025. `cidade`/`uf`: FAPESPA/Belém-PA; `taxa`: não indicada (não presumir isenção).
- O Anexo II traz funções, requisitos, jornada de 30h e remuneração; o parser deve ler tabelas PDF e manter texto original.

### 8. Edital e publicações

- Fases: inscrição, análise documental/curricular, entrevista; página lista resultado preliminar, cronograma atualizado, resultado final e convocação para entrevista.
- Resultados e convocações aparecem em PDF no site e no SIPROS/DOE; deduplicar por número PSS + tipo de ato + URL.
- Ruídos: chamadas de bolsas de pesquisa e Connect Amazônia; exigir `contratação temporária`, cargo/função e Anexo de vagas.

### 9. API/XHR/backend

- Site WordPress server-rendered; endpoint REST/`wp-json` não confirmado.
- SIPROS é sistema externo de inscrição/acompanhamento; autenticação e endpoint interno desconhecidos. Não automatizar login para discovery.

### 10. Tecnologia, bloqueios e estratégia

- Tipo: `WORDPRESS` + `PDF_INDEX`; HTTP simples: SIM; JS: NÃO para listagem; Playwright: NÃO esperado.
- Bloqueios: nenhum WAF/CAPTCHA observado; alguns PDFs antigos podem retornar 404, usar URL vigente.
- Estratégia: `CONFIGURABLE_HTML` + parser PDF; `DEDICATED_CONNECTOR` opcional para SIPROS apenas se acesso público de resultados for comprovado.

### Quality gate / Empty evidence

- ACEITAR PSS e atos com contratação temporária/cargo/função e vagas.
- REJEITAR bolsas de pesquisa, chamadas de projetos e Connect Amazônia.
- Empty: não vazio historicamente; `Active=0`, `Closed=1` para a seleção relevante observada.

### Diagnóstico, recomendação e instruções para Codex

- Diagnóstico: `CRAWLER_STRATEGY_CLEAR`, `HTML_SUFFICIENT`, `DEDICATED_CONNECTOR_RECOMMENDED`, `INSTITUTIONAL_FILTER_REQUIRED`, `GENERIC_CONNECTOR_SUFFICIENT`.
- Recomendação: `HYBRID` (HTML/PDF + SIPROS somente se público), com PSS em estado Closed.
- Passos: (1) usar `/chamadas/` e `/recursos-humanos/`; (2) identificar o bloco PSS pelo título; (3) seguir PDF vigente, resultados e convocações; (4) extrair Anexos I/II para cargo, vagas, requisitos e remuneração; (5) tratar SIPROS como inscrição externa; (6) rejeitar bolsas/projetos; (7) testar fixture PSS 001/2025 e estado encerrado.
- Confiança: HIGH.

### Evidências

<https://www.fapespa.pa.gov.br/>; <https://www.fapespa.pa.gov.br/chamadas/>; <https://www.fapespa.pa.gov.br/wp-content/uploads/2025/07/EDITAL-001-2025-VIGENTE.pdf>; <https://www.fapespa.pa.gov.br/wp-content/uploads/2025/07/11.-RESULTADO-FINAL-PSS-001.2025-FAPESPA-1.pdf>.

## 96 — FAPEAP

### 1. Identidade

- Nome: Fundação de Amparo à Pesquisa do Estado do Amapá (FAPEAP).
- Identificador técnico: `fapeap_selection`.
- URL inicial fornecida: <https://fapeap.ap.gov.br>.
- URL oficial atual confirmada: <https://fapeap.portal.ap.gov.br/>; a URL inicial hoje aponta para portal estadual genérico e a fundação tem subdomínio `portal.ap.gov.br` ativo.
- Portal ativo: SIM no novo domínio; URL mudou: SIM (migração confirmada pelo portal oficial atual e pelo antigo domínio genérico).

### 2. Mapa do portal

- Homepage: <https://fapeap.portal.ap.gov.br/>.
- Notícias: link `Notícias` (rota não exposta na captura).
- Publicações: link `Ver publicações`; homepage lista os últimos 7 arquivos.
- Programas: Centelha, Rede de Pesquisa, PPSUS, NexBio, Tecnova, PROFIX, Bolsa Produtividade e Desafio Startup.
- Submissão: SIG FAPEAP em <https://sigfapeap.portal.ap.gov.br>.
- Documentos: links `Baixar` hospedados em `matrix.amapa.gov.br`.

### 3. Universo atual observado

- Observed: 7 publicações na homepage (21/08/2026 a 11/08/2026) e 9 programas institucionais visíveis.
- Relevant: 0 anúncios de emprego/PSS encontrados; publicações são retificações, resultados e chamadas de projetos/bolsas.
- Active: UNKNOWN para chamadas por status formal; nenhuma seleção de pessoal ativa confirmada.
- Closed: UNKNOWN; resultados publicados não equivalem a encerramento de todos os programas.
- Out of scope: Centelha, PDPG, PROFIX, Startup, bolsas, PPSUS e submissões de projetos.

### 4. Listagem

- Homepage apresenta cards de notícias e tabela HTML de publicações com colunas `Data`, `Descrição`, `Arquivo`; cada registro tem link `Baixar` para `matrix.amapa.gov.br`.
- Não há coluna de status de concurso, cargo ou vagas. Selector CSS exato não foi exposto; usar cabeçalhos/links e validar o domínio do arquivo.

### 5. Paginação

- Homepage mostra sete registros recentes e link `Ver publicações`; paginação da página completa não foi recuperada (UNKNOWN).
- Programas e notícias são menus independentes; percorrer publicações e páginas de programa quando necessário.

### 6. Exemplo real

- Título: Edital nº 003/2026 — Programa de Desenvolvimento da Pós-Graduação (PDPG) – Parcerias Estratégicas nos Estados V / Rede de Pesquisa e Desenvolvimento da Amazônia Legal.
- Órgão: FAPEAP/CAPES.
- Status: chamada de propostas/resultados, fora do escopo de pessoal.
- URL: homepage e publicação datada 06/08/2026; arquivo `Baixar` em `matrix.amapa.gov.br`.
- Outro exemplo atual: Programa Prêmio Desafio Startup Amapá 2026, publicação 20/07/2026; é premiação/projeto, não emprego.

### 7. Campos

- Para os itens atuais: `titulo`, `orgao`, `status` e `edital_data`: HTML da publicação; `link_edital`: URL de download `matrix.amapa.gov.br`; `modalidade`: PDF/HTML (PDPG, bolsa ou fomento).
- `cargo`, `vagas`, `salario`, `taxa`, `prova`, `cidade`, `uf`, `inscricao_inicio/fim`, `link_inscricao`: NÃO DISPONÍVEL/fora de escopo.

### 8. Edital e publicações

- Tipos observados: edital, portaria, retificação, resultado preliminar/final e declarações. Links de download são externos ao subdomínio, mas oficiais do Governo do Amapá.
- Deduplicar por data + descrição normalizada + URL de arquivo; separar resultados e retificações do edital-base.
- Ruídos: notícias de programas, SIGFAPEAP e conteúdo geral de Governo do Amapá.

### 9. API/XHR/backend

- Endpoint JSON/XHR: UNKNOWN; tabela é server-rendered no acesso textual.
- SIG FAPEAP é sistema separado e possivelmente autenticado; não há API pública confirmada.

### 10. Tecnologia, bloqueios e estratégia

- Tipo: `SERVER_RENDERED`/`OTHER` no portal estadual Amapá; HTTP simples: SIM para homepage; JS: NÃO aparente para cards/tabela; Playwright: NÃO esperado.
- Bloqueios: nenhum WAF/CAPTCHA; rotas internas retornaram 502 pontual, mas homepage funciona.
- Estratégia: `CONFIGURABLE_HTML` + PDF/arquivo oficial; manter `KEEP_EMPTY` para pessoal.

### Quality gate / Empty evidence

- ACEITAR somente publicação que explicite contratação, cargo, emprego, estágio ou PSS de pessoal da FAPEAP.
- REJEITAR editais de pesquisa, bolsas, premiações, startups e propostas.
- Empty: `UNKNOWN_EMPTY` para o universo de pessoal; `Relevant=0` por observação das publicações atuais.

### Diagnóstico, recomendação e instruções para Codex

- Diagnóstico: `PORTAL_MIGRATED`, `CRAWLER_STRATEGY_CLEAR`, `HTML_SUFFICIENT`, `INSTITUTIONAL_FILTER_REQUIRED`, `GENERIC_CONNECTOR_SUFFICIENT`.
- Recomendação: `CONFIGURABLE_HTML` no domínio novo + `KEEP_EMPTY` para seleção de pessoal.
- Passos: (1) trocar URL da fonte para `https://fapeap.portal.ap.gov.br/`; (2) buscar tabela de publicações e links `matrix.amapa.gov.br`; (3) seguir PDFs e retificações; (4) filtrar apenas contratação/cargo/estágio/PSS; (5) não atribuir status Active a resultados de projetos; (6) manter SIGFAPEAP fora de discovery; (7) criar teste de migração do domínio antigo para o novo.
- Confiança: HIGH para migração e estrutura; MEDIUM para ausência de seleção de pessoal.

### Evidências

<https://fapeap.ap.gov.br/>; <https://fapeap.portal.ap.gov.br/>; <https://sigfapeap.portal.ap.gov.br>; <https://diofe.portal.ap.gov.br/portal/edicoes/visualizar_pdf/9934/>.

## 97 — FAPERR (Fundação de Amparo à Pesquisa do Estado de Roraima)

Identificador técnico: `faperr_selection`

URL fornecida: `https://faperr.rr.gov.br/`

URL oficial confirmada: `https://faperr.rr.gov.br/` (homepage); arquivos oficiais no mesmo domínio.

Portal ativo: `PARCIAL` — a página pública observada entrega `Welcome`/`Loading...`.

### Navegação

Homepage: `https://faperr.rr.gov.br/`

Abertos: `UNKNOWN`

Em andamento: `UNKNOWN`

Encerrados: `UNKNOWN`

Detalhe: `UNKNOWN` — nenhum detalhe público navegável confirmado.

Documentos: PDFs em `https://faperr.rr.gov.br/wp-content/uploads/...`.

### Universo observado

Observed: `UNKNOWN`; Relevant: `UNKNOWN` (nenhum item de contratação confirmado); Active: `UNKNOWN`; Closed: `UNKNOWN`; Out of scope: PPSUS, pesquisa, bolsas, premiações e contratação de projetos.

### Listagem

Estrutura: shell de aplicação; não há lista pública confirmada.

Selector/container: `UNKNOWN`

Título: `UNKNOWN` na homepage; disponível em PDF quando acessível.

Link: `UNKNOWN` para a listagem; links de PDF conhecidos.

ID: `UNKNOWN`

Status: `UNKNOWN`

### Paginação

Método: `UNKNOWN`

Parâmetros: `UNKNOWN`

### Exemplo real

Título: Edital FAPERR nº 004/2025 — Chamada Pública PPSUS 8ª Edição.

Órgão: FAPERR/órgãos parceiros do PPSUS.

Status: chamada/seleção de projetos; fora de escopo de pessoal.

URL: `https://faperr.rr.gov.br/wp-content/uploads/2025/04/Edital_004_-_Chamada_Publica_PPSUS_8_Edicao_assinado.pdf`

### Campos

titulo: PDF/UNKNOWN; orgao: PDF; modalidade: PDF (chamada de projeto); cargo: UNKNOWN/fora de escopo; area: PDF; cidade: UNKNOWN; uf: PDF/RO-RR conforme item; status: PDF/UNKNOWN; vagas: UNKNOWN/fora de escopo; salario: UNKNOWN/fora de escopo; escolaridade: PDF quando aplicável; taxa: UNKNOWN; prova: UNKNOWN; edital: PDF; inscricao_inicio: PDF quando aplicável; inscricao_fim: PDF quando aplicável; link_edital: PDF/HTML; link_inscricao: UNKNOWN. Campos indicados como PDF são documentais, não campos de emprego.

### Publicações

Estrutura: `UNKNOWN` — arquivos PDF isolados observáveis.

Tipos: chamadas de pesquisa, bolsas, manuais, resultados/projetos.

Selector/API: `UNKNOWN`

Deduplicação sugerida: título normalizado + URL + versão/retificação.

Ruídos: SISC&T, legislação, PPSUS, contratação de projeto e bolsas.

### API/XHR

Endpoint: `UNKNOWN`; Método: `UNKNOWN`; Parâmetros: `UNKNOWN`; Paginação: `UNKNOWN`; JSON path: `UNKNOWN`; Autenticação: SISC&T exige login; Observações: não usar sistema de projetos como discovery de pessoal.

### Tecnologia

Tipo: `OTHER`/shell de aplicação; HTTP funciona: parcial; JS necessário: provável para conteúdo, não confirmado; Playwright necessário: reteste recomendado.

### Bloqueios

HTTP: corpo textual incompleto; Browser: não testado para conteúdo pós-carregamento; WAF: não confirmado; Alternativa: PDFs oficiais e reteste Playwright.

### Estratégia recomendada

`KEEP_BLOCKED` + `PLAYWRIGHT` em reteste controlado; não criar `REST_API`/`XHR_API` sem evidência.

### 1. Identidade, URL canônica e data da observação

- URL fornecida: `https://faperr.rr.gov.br/`.
- A URL é institucional, porém o acesso textual atual entrega somente `Welcome`/`Loading...`; não foi confirmada uma migração para outro domínio. Data/hora da observação: 30/08/2026, America/Sao_Paulo.
- Sistema relacionado encontrado em documentação oficial: SISC&T/SIGFAPERR, com login em `https://aplicacoes.segad.rr.gov.br/sigfaperr/login.xhtml`. É um sistema de submissão/gestão de projetos e não uma listagem pública de empregos.

### 2. Mapa de superfícies públicas

- Homepage: `https://faperr.rr.gov.br/`.
- Documento institucional do sistema: `https://faperr.rr.gov.br/wp-content/uploads/2025/05/Manual-SISCTT-Pesquisador_compressed.pdf`.
- Exemplo de edital oficial: `https://faperr.rr.gov.br/wp-content/uploads/2025/04/Edital_004_-_Chamada_Publica_PPSUS_8_Edicao_assinado.pdf`.
- Não foi localizada uma página pública estável de listagem de editais nem uma rota de resultados de concursos da Fundação.

### 3. Universo observado e classificação

- Observed: `UNKNOWN` (a página pública é um shell de carregamento; os PDFs encontrados não constituem uma listagem completa).
- Relevant: `UNKNOWN` para o universo total; nenhum processo seletivo de contratação de pessoal foi confirmado na amostra observável.
- Active: `UNKNOWN`; Closed: `UNKNOWN`.
- Out of scope confirmado: PPSUS, chamadas de pesquisa, bolsas, premiações e contratação de projetos. O menu “Contratação” no manual do SISC&T refere-se a projetos contratados/financiados, não à contratação de servidores ou empregados.
- A Lei Estadual nº 1.641/2022, disponível no portal oficial, prevê ingresso de servidores efetivos por concurso público; isso não é um edital atual da FAPERR e não deve ser contado como oportunidade observada.

### 4. Listagem, paginação e estado

- Listagem, filtros, ordenação, paginação e seletores: `UNKNOWN`; não inventar seletores a partir do shell `Loading...`.
- Não há evidência suficiente para afirmar que o portal fornece uma tabela server-rendered, API pública ou paginação de editais.

### 5. Exemplo de item e natureza

- Edital FAPERR nº 004/2025 — Chamada Pública PPSUS 8ª Edição: chamada de pesquisa/propostas, com bolsas e serviços de projeto; não cria vaga de emprego nem vínculo funcional. Estado documental: chamada/seleção de projetos, fora do universo do Observador.
- O manual SISC&T também documenta submissão, acompanhamento e contratação de projetos; “contratação” aqui não equivale a PSS ou concurso de pessoal.

### 6. Campos disponíveis

- Nos PDFs: título, programa, órgão, datas, público-alvo, modalidade, anexos e links de submissão.
- Campos de pessoal (`cargo`, `vagas`, `salário`, `taxa`, `prova`, `cidade`, `inscrição_inicio/fim`) não foram encontrados em item relevante confirmado.

### 7. Editais e publicações

- Superfície identificada: arquivos PDF em `wp-content/uploads`; não foi confirmado índice público navegável.
- Não atribuir status Active/Closed apenas pelo nome do arquivo. Deduplicar edital, retificação, resultado e manual pela URL e título normalizado quando a listagem voltar a estar disponível.

### 8. API/XHR/backend

- Endpoint JSON/XHR: `UNKNOWN`.
- O corpo público observado não prova backend, tecnologia ou endpoint. O SISC&T exige login e não deve ser tratado como API de discovery sem evidência pública.

### 9. Tecnologia e bloqueios

- Classificação operacional: `OTHER`/SPA ou shell de aplicação; requer reteste visual/Playwright somente para descobrir se há conteúdo carregado após JavaScript.
- Bloqueios confirmados: conteúdo não exposto no carregamento textual (`Loading...`). Não foi confirmado WAF, CAPTCHA ou endpoint alternativo.

### Quality gate

- ACEITAR somente edital com contratação explícita de pessoas, cargo/emprego, PSS, estágio ou concurso da própria FAPERR.
- REJEITAR PPSUS, chamadas de projetos, bolsas e “contratação” de projetos.

### Empty evidence

- `UNKNOWN_EMPTY`/`KEEP_BLOCKED`; não converter a tela de carregamento em `Relevant=0` definitivo.

### Estratégia recomendada

- Diagnóstico: `PORTAL_PARTIAL`, `LOW_OBSERVABILITY`, `INSTITUTIONAL_FILTER_REQUIRED`, `NO_PUBLIC_LIST_CONFIRMED`.
- Recomendação: `KEEP_BLOCKED` com reteste Playwright; manter arquivos oficiais como evidência out-of-scope e não criar adaptador de API sem confirmação.

### Instruções para Codex

- Passos: (1) retestar homepage em navegador; (2) procurar menu/listagem carregada e seus requests; (3) se houver PDF público, extrair somente chamadas de contratação de pessoal; (4) manter SISC&T como sistema de projetos; (5) separar legislação sobre concurso de edital observado.
- Diagnóstico e recomendação permanecem condicionados ao reteste da superfície dinâmica.

### Confidence

MEDIUM para a classificação dos documentos; LOW-MEDIUM para ausência de edital de pessoal, pois a superfície pública estava incompleta.

### Evidências

<https://faperr.rr.gov.br/>; <https://faperr.rr.gov.br/wp-content/uploads/2025/05/Manual-SISCTT-Pesquisador_compressed.pdf>; <https://faperr.rr.gov.br/wp-content/uploads/2025/04/Edital_004_-_Chamada_Publica_PPSUS_8_Edicao_assinado.pdf>; <https://faperr.rr.gov.br/wp-content/uploads/2025/03/Lei-Ordinaria-1641-2022-de-Roraima-RR-FAPERR.pdf>; <https://aplicacoes.segad.rr.gov.br/sigfaperr/login.xhtml>.

## 98 — FAPERO (Fundação de Amparo à Pesquisa do Estado de Rondônia)

Identificador técnico: `fapero_selection`

URL fornecida: `https://rondonia.ro.gov.br/fapero/publicacoes/`

URL oficial confirmada: `https://rondonia.ro.gov.br/fapero/publicacoes/` e `https://rondonia.ro.gov.br/fapero/`.

Portal ativo: `SIM` — arquivo de publicações e páginas anuais acessíveis.

### Navegação

Homepage: `https://rondonia.ro.gov.br/fapero/`

Abertos: `UNKNOWN` (a publicação não tem marcador universal de aberto).

Em andamento: `UNKNOWN`

Encerrados: arquivo anual/resultado, sem filtro universal confirmado.

Detalhe: páginas individuais/arquivo anual e PDF.

Documentos: PDFs em `https://rondonia.ro.gov.br/wp-content/uploads/...`.

### Universo observado

Observed: pelo menos três blocos programáticos em 2026; Relevant: `0` confirmado na amostra; Active: `0` relevante confirmado; Closed: `UNKNOWN`; Out of scope: bolsas, projetos, premiações e chamadas de pesquisa/inovação.

### Listagem

Estrutura: HTML server-rendered de publicações, arquivo anual e paginação.

Selector/container: `UNKNOWN` (não inventar seletor).

Título: HTML/PDF.

Link: HTML para PDF oficial.

ID: `UNKNOWN`.

Status: texto do título/documento; não uniforme.

### Paginação

Método: arquivo anual e URL de página (`/publicacoes/pg/2/`).

Parâmetros: segmento de caminho; demais parâmetros `UNKNOWN`.

### Exemplo real

Título: Edital nº 5/2024/FAPERO-DC — Chamada Simplificada TIC/CTI.

Órgão: FAPERO/Estado de Rondônia.

Status: seleção para bolsas; sem vínculo empregatício; out-of-scope.

URL: `https://rondonia.ro.gov.br/wp-content/uploads/2024/08/Edital_5_-T-I-Comunicacao.pdf`

### Campos

titulo: HTML/PDF; orgao: HTML/PDF; modalidade: PDF; cargo: UNKNOWN/fora de escopo; area: PDF; cidade: UNKNOWN; uf: PDF/RO; status: HTML/PDF; vagas: UNKNOWN/fora de escopo; salario: UNKNOWN (valor de bolsa não é salário); escolaridade: PDF; taxa: UNKNOWN; prova: UNKNOWN; edital: PDF; inscricao_inicio: PDF; inscricao_fim: PDF; link_edital: HTML/PDF; link_inscricao: PDF/UNKNOWN.

### Publicações

Estrutura: arquivo anual/lista HTML.

Tipos: edital, chamada, resultado, retificação, bolsa e programa.

Selector/API: `UNKNOWN`.

Deduplicação sugerida: título/programa + data + URL; tratar resultado/retificação como derivados.

Ruídos: bolsas, premiações, pesquisa, projetos e notícias de inovação.

### API/XHR

Endpoint: `UNKNOWN`; Método: `UNKNOWN`; Parâmetros: caminho de arquivo/página; Paginação: URL de arquivo/página; JSON path: `UNKNOWN`; Autenticação: não observada; Observações: HTML/PDF é suficiente para cobertura inicial.

### Tecnologia

Tipo: `WORDPRESS`/portal governamental; HTTP funciona: SIM; JS necessário: NÃO aparente; Playwright necessário: NÃO esperado.

### Bloqueios

HTTP: sem bloqueio confirmado; Browser: não necessário; WAF: não confirmado; Alternativa: páginas anuais e PDFs oficiais.

### Estratégia recomendada

`HTTP_HTML` + `CONFIGURABLE_HTML` + PDF + `KEEP_EMPTY` para vagas de pessoal.

### 1. Identidade, URL canônica e data da observação

- URL fornecida/atual: `https://rondonia.ro.gov.br/fapero/publicacoes/`; homepage institucional: `https://rondonia.ro.gov.br/fapero/`.
- Site ativo no domínio oficial do Governo de Rondônia. Data/hora da observação: 30/08/2026, America/Sao_Paulo.

### 2. Mapa de superfícies públicas

- Publicações atuais: `https://rondonia.ro.gov.br/fapero/publicacoes/`.
- Arquivo 2026: `https://rondonia.ro.gov.br/fapero/publicacoes/2026-2/`.
- Arquivo 2025: `https://rondonia.ro.gov.br/fapero/publicacoes/2025-2/`.
- Há páginas de arquivo/paginação no padrão `/publicacoes/pg/2/`, além de PDFs oficiais em `https://rondonia.ro.gov.br/wp-content/uploads/...`.

### 3. Universo observado e classificação

- Observed: pelo menos três blocos programáticos na página 2026 (Tecnova, Centelha 3 e Empreender na Escola), além de itens históricos.
- Relevant: `0` confirmado na amostra atual; Active: `0` relevante confirmado. Closed: `UNKNOWN` para o universo completo.
- Chamadas de projeto, premiação, pesquisa, inovação e bolsas são out-of-scope. Os documentos históricos de TIC/CTI e CAFIX usam bolsa, não relação de emprego.

### 4. Listagem, paginação e estado

- Listagem é HTML server-rendered de publicações, com título/data e links para documentos; arquivos anuais e paginação são navegáveis por URL.
- Seletores CSS específicos não foram registrados por não serem necessários à prova e não devem ser inventados. Status deve ser inferido somente de texto explícito (“resultado”, “retificação”, encerramento) e da data do documento.

### 5. Exemplo de item e natureza

- `EDITAL Nº 5/2024/FAPERO-DC — Chamada Simplificada para desenvolvimento profissional TIC/CTI`: seleciona profissionais para receber bolsas de até 12 meses (incluindo valor mensal indicado no edital), sem vínculo empregatício. É bolsa/formação profissional e, portanto, fora do Observador.
- `EDITAL Nº 1/2023/FAPERO-DC — CAFIX`: também é programa de bolsas, não contratação de pessoal.

### 6. Campos disponíveis

- HTML/PDF: título, programa, área/perfil, datas, requisitos, valor e duração da bolsa, regras de inscrição, resultados e retificações.
- Campos de emprego (`cargo`, `vagas` como posto, salário, taxa, prova e local de lotação) não foram confirmados; valores de bolsa não devem ser mapeados como salário.

### 7. Editais e publicações

- Tipos observados: edital, chamada, resultado, retificação e arquivos anuais.
- Deduplicar por título/programa/URL; manter resultado e retificação como documentos derivados do edital-base.
- PDFs oficiais relevantes à classificação: `https://rondonia.ro.gov.br/wp-content/uploads/2024/08/Edital_5_-T-I-Comunicacao.pdf` e `https://rondonia.ro.gov.br/wp-content/uploads/2023/01/EDITAL-No-1-2023-FAPERO-DC.pdf`.

### 8. API/XHR/backend

- Endpoint público JSON/XHR: `UNKNOWN`; não é necessário para a cobertura observada.
- A página pode ser consumida por HTML e links de PDF; não afirmar existência de `wp-json` sem teste específico.

### 9. Tecnologia e bloqueios

- `WORDPRESS`/site governamental server-rendered; HTTP simples: SIM; JS para a listagem: não necessário; Playwright: NÃO esperado.
- Nenhum WAF/CAPTCHA observado. A paginação e os arquivos anuais devem ser testados respeitando limites e sem contar dados locais como contagem externa.

### Quality gate

- ACEITAR somente convocação, PSS, concurso, estágio ou contratação explícita de pessoas pela FAPERO.
- REJEITAR bolsas, chamadas de projetos, premiações e “desenvolvimento profissional” sem vínculo.

### Empty evidence

- Para a categoria atual: `OUT_OF_SCOPE` (há itens observados, todos fora de pessoal); não declarar que o arquivo histórico inteiro está vazio.

### Estratégia recomendada

- Diagnóstico: `HTML_SUFFICIENT`, `WORDPRESS_ARCHIVE`, `INSTITUTIONAL_FILTER_REQUIRED`, `GENERIC_CONNECTOR_SUFFICIENT`.
- Recomendação: `CONFIGURABLE_HTML` + PDF, seguir páginas anuais/paginação e manter `KEEP_EMPTY` para pessoal.

### Instruções para Codex

- Passos: (1) rastrear somente publicações FAPERO; (2) seguir PDF, resultado e retificação; (3) exigir evidência de vínculo/cargo antes de Relevant; (4) não promover bolsas a Active jobs; (5) deduplicar arquivos anuais e URLs.
- Não contar valor/duração de bolsa como salário/vaga.

### Confidence

HIGH para a classificação dos exemplos e estrutura; MEDIUM para ausência de contratação no universo histórico total.

### Evidências

<https://rondonia.ro.gov.br/fapero/publicacoes/>; <https://rondonia.ro.gov.br/fapero/publicacoes/2026-2/>; <https://rondonia.ro.gov.br/wp-content/uploads/2024/08/Edital_5_-T-I-Comunicacao.pdf>; <https://rondonia.ro.gov.br/wp-content/uploads/2023/01/EDITAL-No-1-2023-FAPERO-DC.pdf>.

## 99 — FAPAC (Fundação de Amparo à Pesquisa do Estado do Acre)

Identificador técnico: `fapac_selection`

URL fornecida: `https://fapac.ac.gov.br/`

URL oficial confirmada: `https://fapac.ac.gov.br/` e página de editais `https://fapac.ac.gov.br/98-2/`.

Portal ativo: `SIM` — homepage e página de editais acessíveis.

### Navegação

Homepage: `https://fapac.ac.gov.br/`

Abertos: `UNKNOWN` (programas aparecem publicados, mas sem filtro universal).

Em andamento: `UNKNOWN`

Encerrados: `UNKNOWN`

Detalhe: blocos na página `/98-2/`, com links HTML/PDF.

Documentos: editais/resultados/retificações na página e links externos oficiais.

### Universo observado

Observed: pelo menos sete blocos/publicações; Relevant: `0` confirmado; Active: `UNKNOWN`; Closed: `UNKNOWN`; Out of scope: bolsas, PPSUS, Centelha, premiações, OSC e propostas de projeto.

### Listagem

Estrutura: HTML/WordPress com blocos de publicações; iframe/feed também referenciado.

Selector/container: `UNKNOWN`.

Título: HTML/PDF.

Link: HTML para arquivo/resultado.

ID: `UNKNOWN`.

Status: `UNKNOWN` sem marcador universal.

### Paginação

Método: não confirmada; página única observada.

Parâmetros: `UNKNOWN`.

### Exemplo real

Título: Edital 003/2026 — Mentes Azuis.

Órgão: FAPAC/Estado do Acre.

Status: programa de bolsas; out-of-scope.

URL: `https://fapac.ac.gov.br/98-2/`

### Campos

titulo: HTML/PDF; orgao: HTML/PDF; modalidade: PDF (bolsa/fomento); cargo: UNKNOWN/fora de escopo; area: HTML/PDF; cidade: UNKNOWN; uf: PDF/AC; status: HTML/PDF/UNKNOWN; vagas: UNKNOWN/fora de escopo; salario: UNKNOWN (auxílio/bolsa não é salário); escolaridade: PDF; taxa: UNKNOWN; prova: UNKNOWN; edital: PDF/HTML; inscricao_inicio: PDF/UNKNOWN; inscricao_fim: PDF/UNKNOWN; link_edital: HTML/PDF; link_inscricao: PDF/UNKNOWN.

### Publicações

Estrutura: blocos HTML na página de editais.

Tipos: edital, chamada, bolsas, PPSUS, Centelha, resultado, retificação e OSC.

Selector/API: `UNKNOWN`.

Deduplicação sugerida: título + programa + URL; separar edital-base, retificação e resultado.

Ruídos: SIGFAPAC, feed estadual, notícias e chamadas de projeto.

### API/XHR

Endpoint: `UNKNOWN`; Método: `UNKNOWN`; Parâmetros: `UNKNOWN`; Paginação: `UNKNOWN`; JSON path: `UNKNOWN`; Autenticação: SIGFAPAC possivelmente autenticado; Observações: não usar SIGFAPAC para discovery sem evidência pública.

### Tecnologia

Tipo: `WORDPRESS`/HTML estático ou server-rendered; HTTP funciona: SIM; JS necessário: NÃO aparente na lista; Playwright necessário: NÃO, salvo conteúdo do iframe/feed.

### Bloqueios

HTTP: sem bloqueio confirmado; Browser: não necessário; WAF: não confirmado; Alternativa: página `/98-2/` e PDFs/links oficiais.

### Estratégia recomendada

`CONFIGURABLE_HTML` + PDF + `KEEP_EMPTY`; manter SIGFAPAC separado.

### 1. Identidade, URL canônica e data da observação

- URL fornecida/atual: `https://fapac.ac.gov.br/`.
- Site institucional ativo, com menu de Institucional, Programas, Editais e SIGFAPAC. Data/hora da observação: 30/08/2026, America/Sao_Paulo.

### 2. Mapa de superfícies públicas

- Página de editais: `https://fapac.ac.gov.br/98-2/`.
- SIGFAPAC: `https://www.sig.fapac.ac.gov.br`.
- Homepage também referencia `feed.ac.gov.br` em iframe/integração de conteúdo.
- A página de editais contém blocos de chamadas, PDFs, resultados e programas; não foi observada paginação pública específica.

### 3. Universo observado e classificação

- Observed: pelo menos sete blocos/publicações na página de editais.
- Relevant: `0` confirmado; Active: `UNKNOWN`; Closed: `UNKNOWN`.
- Itens atuais incluem Mentes Azuis (Edital 003/2026), Mães da Ciência, PPSUS, Centelha 3, Cadeia Produtiva e outros programas de bolsa/fomento. São propostas, bolsas, premiações ou chamamentos de organizações, não vagas de emprego.

### 4. Listagem, paginação e estado

- Lista em HTML/WordPress com títulos e links; não há paginação comprovada.
- Estado deve ser lido do texto do edital, retificação ou resultado; não inferir Active apenas por aparecer no topo da página.

### 5. Exemplo de item e natureza

- `Edital 003/2026 — Mentes Azuis`: bolsa/programa, não contratação de pessoal.
- PPSUS e Centelha 3: chamadas de pesquisa/inovação e seleção de propostas, também out-of-scope.
- Chamamento de OSC: parceria/execução de programa, não seleção individual para emprego da Fundação.

### 6. Campos disponíveis

- HTML/PDF: título, programa, instituição/público, modalidade, datas, documentos, link de inscrição e resultados.
- `cargo`, `vagas` de emprego, `salário`, `taxa`, `prova`, cidade/lotação: não confirmados; bolsa/auxílio não é salário.

### 7. Editais e publicações

- Tipos observados: edital, chamada, resultado, retificação, bolsas, PPSUS, Centelha e chamamentos.
- Deduplicar por título + programa + URL; separar edital-base, retificação e resultado. Manter SIGFAPAC como sistema de submissão, não como fonte de contratação sem evidência.

### 8. API/XHR/backend

- Endpoint JSON/XHR: `UNKNOWN`; não foi confirmado `wp-json` nem API pública.
- A página de editais pode ser extraída por HTML; o iframe/feed e o SIGFAPAC devem ser tratados como superfícies separadas.

### 9. Tecnologia e bloqueios

- `WORDPRESS`/HTML estático ou server-rendered; HTTP simples: SIM; JS não é requisito evidente para a lista; Playwright: não necessário, salvo para conteúdo do iframe.
- Nenhum WAF/CAPTCHA confirmado; o SIGFAPAC pode requerer autenticação.

### Quality gate

- ACEITAR somente edital explícito de contratação, cargo/emprego, PSS, concurso ou estágio da FAPAC.
- REJEITAR bolsas, pesquisa, inovação, PPSUS, Centelha, premiação, OSC e propostas de projeto.

### Empty evidence

- `OUT_OF_SCOPE` para a amostra atual, com `Active/Closed=UNKNOWN` no universo completo; não transformar UNKNOWN em zero.

### Estratégia recomendada

- Diagnóstico: `HTML_SUFFICIENT`, `INSTITUTIONAL_FILTER_REQUIRED`, `GENERIC_CONNECTOR_SUFFICIENT`, `OUT_OF_SCOPE_CURRENT`.
- Recomendação: `CONFIGURABLE_HTML` + PDF e `KEEP_EMPTY` para seleção de pessoal; não acoplar discovery ao SIGFAPAC.

### Instruções para Codex

- Passos: (1) monitorar a página `/98-2/`; (2) seguir somente novos editais com linguagem de contratação; (3) conservar resultados/retificações como derivados; (4) excluir bolsas e chamadas de projeto; (5) testar o iframe somente se uma futura chamada relevante apontar para ele.
- Não consultar o SIGFAPAC como fonte de vagas sem evidência pública de contratação.

### Confidence

HIGH para a classificação atual; MEDIUM para ausência de processos de pessoal no histórico completo.

### Evidências

<https://fapac.ac.gov.br/>; <https://fapac.ac.gov.br/98-2/>; <https://www.sig.fapac.ac.gov.br>.

## Síntese — oportunidades de plataforma compartilhada

| Cluster potencial | Fontes | Reuso seguro | Limite/evidência |
|---|---|---|---|
| HTML + PDF em portais governamentais/WordPress | FAPEG, FAPEAM, FAPESPA, FAPERO, FAPAC | Extrator genérico de título, data, link, PDF, retificação e resultado, com filtro institucional | Não presumir mesmo tenant ou mesma API; cada domínio precisa de teste próprio |
| Portais estaduais com arquivos e sistemas SIG separados | FAPEMAT, FAPDF, FAPERR, FAPAC, FAPEAP | Componente comum de “portal público + sistema de submissão”, mantendo SIG fora do discovery de emprego | Nomes SIG não provam backend compartilhado nem endpoint comum |
| Portal estadual do Amapá/PRODAP | FAPEAP e possíveis publicações estaduais relacionadas | Reuso de navegação, tabela de publicações e links `matrix.amapa.gov.br` | Confirmar institucionalidade e evitar misturar outras secretarias |
| FAPESPA + SIPROS externo | FAPESPA | Conector de documentos/resultados pode acompanhar SIPROS se houver evidência pública | SIPROS é sistema distinto; não inventar API nem assumir que é fonte de vagas |

### Casos LOW-MEDIUM para revisão

- FAPEMAT — listagem oficial com bloqueio/Request Rejected e múltiplos portais; retestar somente se necessário.
- FAPT — domínio fornecido intermitente/sem confirmação de migração; manter `KEEP_BLOCKED` e não usar FAPTO como substituta.
- FAPEAM — página de editais apresenta placeholders Vue (`Carregando...`, `Não existem...`); investigar XHR/Playwright antes de qualquer `Relevant=0`.
- FAPERR — homepage pública permanece em `Loading...`; descobrir rota real somente com navegador e sem fabricar endpoint.
- FAPEAP — migração do domínio antigo para `portal.ap.gov.br` está fortemente indicada, mas a estrutura interna e status das chamadas ainda exigem teste.

### Fechamento e quality gate do lote

- Lote contém exatamente 10 fontes: 90 FAPEMAT, 91 FAPEG, 92 FAPDF, 93 FAPT, 94 FAPEAM, 95 FAPESPA, 96 FAPEAP, 97 FAPERR, 98 FAPERO e 99 FAPAC.
- Nenhuma contagem foi derivada de dados locais ou apresentada como contagem externa sem observação oficial; `UNKNOWN` foi mantido quando a superfície estava dinâmica, bloqueada ou incompleta.
- Bolsas, fomento, PPSUS, Centelha, projetos, premiações e “contratação” de projetos foram explicitamente separados de concursos/PSS/empregos. Somente contratação de pessoal da própria Fundação pode entrar em `Relevant`.
- Cada fonte registra data/fuso, URLs oficiais, evidências, estado do universo, tecnologia/bloqueio, quality gate, estratégia e confiança. Não foram inventados seletores, endpoints ou contagens.
- Não houve alteração de código; somente este relatório de pesquisa foi atualizado.
