# Observador de Concursos
## Source Site Research & Codex Implementation Runbook

Pesquisa externa concluída em 30/08/2026 (America/Sao_Paulo). Este runbook é autossuficiente e cobre exatamente as 99 fontes cadastradas. As contagens abaixo são snapshots de superfícies oficiais; `UNKNOWN` significa que a evidência não permite afirmar um número. Bolsas, fomento, premiações, projetos, vestibulares e outros processos sem contratação de pessoal permanecem fora do escopo.

### 1. Executive Summary

Total pesquisado: 99

HTML simples: 61  
API encontrada: 5  
XHR/API interna: 4  
SharePoint: 1  
Browser necessário: 14  
WAF/Cloudflare: 1  
Offline: 7  
URL desatualizada: 11  
Empty legítimo: 12  
Com ativos detectados: 24

| Métrica | Total | Regra aplicada |
|---|---:|---|
| HTML simples | **61** | Discovery primário por HTML server-rendered/configurável, ainda que o detalhe use PDF; exclui API como origem primária, shell dinâmico, SharePoint e fontes sem operação confirmada. |
| API encontrada | **5** | Fontes 11, 12, 29, 47 e 81; a 81 reutiliza a API CEBRASPE, portanto são quatro integrações próprias e uma origem operacional compartilhada. |
| XHR/API interna | **4** | APIs públicas confirmadas por bundle/rede nas fontes 11, 12, 29 e 47. |
| SharePoint | **1** | Fonte 16; `/_api` só deve ser usado se a chamada for confirmada no reteste. |
| Browser necessário | **14** | Primário ou fallback controlado nas fontes 03, 07, 08, 14, 23, 28, 43, 44, 48, 51, 70, 90, 94 e 97. |
| WAF/Cloudflare | **1** | Fonte 07 no domínio antigo; o sucessor oficial é HTML acessível. |
| Offline/sem operação confirmada | **7** | Fontes 25, 28, 34, 38, 41, 61 e 79; bloqueio/indisponibilidade não é vazio. |
| URL desatualizada ou migração com substituta confirmada | **11** | Fontes 07, 26, 31, 32, 38, 46, 47, 68, 69, 73 e 96. |
| Empty legítimo / atual fora do escopo | **12** | Fontes P7: 52, 57, 65, 66, 77, 78, 84, 85, 87, 92, 98 e 99. |
| Com ativos detectados | **24** | Fontes 03, 04, 05, 07, 10, 13, 15, 18, 19, 20, 22, 24, 26, 30, 31, 32, 39, 47, 54, 55, 62, 64, 72 e 73; inclui período futuro explicitamente publicado, mas não simples “em andamento” com inscrição fechada. |

As categorias se sobrepõem e contam **fontes**, não certames. `Active` no restante do documento mantém separados o estado do processo e o estado da inscrição. A descoberta mais crítica foi o falso vazio da FAPEAL (#81): o concurso `FAPEAL_26` está em andamento no CEBRASPE, embora as inscrições estejam encerradas e o arquivo editorial da Fundação seja dominado por fomento.

### 2. Matriz das 99 fontes

| # | Fonte | URL fornecida | URL correta | Tecnologia | Observed | Relevant | Active | Estratégia recomendada | Confiança |
|---:|---|---|---|---|---|---|---|---|---|
| 01 | IBFC | https://concursos.ibfc.org.br/index/abertos/ | https://concursos.ibfc.org.br/index/abertos/ | SERVER_RENDERED/HTML | 347 (8 andamento + 339 finalizados) | 347 | 0 abertas (empty explícito) | CONFIGURABLE_HTML + KEEP_EMPTY | HIGH |
| 02 | IDECAN | https://portal.concursos.idecan.org.br/edital/index/abertos | https://portal.concursos.idecan.org.br/edital/index/abertos | SERVER_RENDERED/Gestor Editais | ≥5 | ≥5 | 0 em inscrição (empty explícito) | CONFIGURABLE_HTML; validar tenant com IBADE | HIGH/MEDIUM |
| 03 | Instituto AOCP | https://www.institutoaocp.org.br/ | https://www.institutoaocp.org.br/concursos/status/inscricoes-abertas | BROWSER_REQUIRED/SPA provável | ≥2 | ≥2 | ≥1 confirmado, total UNKNOWN | PLAYWRIGHT ou HYBRID | MEDIUM |
| 04 | CONSULPAM | https://www.consulpam.com.br/index.php?menu=concursos | https://www.consulpam.com.br/index.php?menu=concursos | SERVER_RENDERED/HTML | ≥60 | ≥60 | 9 abertas | CONFIGURABLE_HTML + tenant `consulpam.selecao.net.br` | HIGH/MEDIUM |
| 05 | IBAM | https://www.ibam-concursos.org.br/ | https://www.ibam-concursos.org.br/ | SERVER_RENDERED/HTML+PDF | ≥5 | ≥5 | 4 com período aberto; 1 suspenso/em breve | DEDICATED_CONNECTOR + HTTP_HTML | HIGH/MEDIUM |
| 06 | IBADE | https://portal.ibade.selecao.site/edital | https://portal.ibade.selecao.site/edital | SERVER_RENDERED/Gestor Editais | ≥6 andamento | ≥6 | 0 em inscrição (empty explícito) | CONFIGURABLE_HTML; avaliar compartilhamento com IDECAN | HIGH/MEDIUM |
| 07 | Instituto Consulplan | https://www.consulplan.net/ | https://www.institutoconsulplan.org.br/Concursos | HTML server-rendered; domínio antigo sob Cloudflare | 6 no bloco aberto/novo; demais seções presentes; total UNKNOWN | 3 relevantes no bloco aberto/novo; total UNKNOWN | 3 abertas/novas relevantes no snapshot | HTTP_HTML/CONFIGURABLE_HTML; navegador só como fallback de detalhes 403 | HIGH para sucessor; MEDIUM para extração integral |
| 08 | SEPROD | https://www.seprod.com.br/concursos/?utm_refererencia=em_andamento | https://www.seprod.com.br/concursos/ | OTHER; TLS/área autenticada | categorias indexadas, cards UNKNOWN | UNKNOWN | UNKNOWN | KEEP_BLOCKED + PLAYWRIGHT/HYBRID após health-check | LOW |
| 09 | FCC | https://www.concursosfcc.com.br/concursoAndamento.html | https://www.concursosfcc.com.br/concursoAndamento.html | SERVER_RENDERED/HTML+PDF | 30 em andamento | maioria, com ruído acadêmico | UNKNOWN | DEDICATED_CONNECTOR ou CONFIGURABLE_HTML + filtro | HIGH/MEDIUM |
| 10 | FGV | https://conhecimento.fgv.br/concursos | https://conhecimento.fgv.br/concursos | SERVER_RENDERED/HTML+PDF | ≥44 links | maioria; filtrar exames/certificações | ≥1 (CPNU2), total UNKNOWN | CONFIGURABLE_HTML + filtro institucional | HIGH/MEDIUM |
| 11 | CEBRASPE | https://www.cebraspe.org.br/concursos/ | https://www.cebraspe.org.br/Concursos/ | REST_API/React | 496 (5 novos, 6 abertos, 60 andamento, 425 encerrados) | UNKNOWN por item; grupo de concursos | detalhe prevalece; Pontaporã aberto; resumo pode falsear `isInscricaoAberta` | REST_API; detalhe `/eventos/{id}` e CDN | HIGH (Sol) |
| 12 | CESGRANRIO | https://www.cesgranrio.org.br/concursos/ | https://www.cesgranrio.org.br/concursos/ + Angular API | WORDPRESS + REST_API/Angular | 32 detalhes (10+10+10+2); 1 em categoria aberta | ≥1 relevante; filtrar vestibular/avaliação | UNKNOWN; Transpetro 2026 aparece na categoria aberta, mas o estado exato depende do conteúdo/cronograma | REST_API `PortalEventos` + WP fallback | HIGH (Sol) |
| 13 | IDCAP | https://www.idcap.org.br/ | https://www.idcap.org.br/ | SERVER_RENDERED/HTML | 22 em andamento | 22 | ≥2 com período futuro/aberto; total UNKNOWN | CONFIGURABLE_HTML + filtro | HIGH/MEDIUM |
| 14 | IBGP | https://novo.ibgpconcursos.com.br/inscricoes_abertas.jsp | https://novo.ibgpconcursos.com.br/index.jsp + /inscricoes_abertas.jsp | JSP/PDF_INDEX | 0 cards abertos; 4 estados | UNKNOWN | UNKNOWN | HYBRID + KEEP_EMPTY temporário; seguir `concurso.jsp?cod=` e download REST | MEDIUM |
| 15 | FUNDEP/Gestão | https://www.gestaodeconcursos.com.br/site/site/default.aspx | https://www.gestaodeconcursos.com.br/site/site/default.aspx + https://fundep.selecao.net.br | SERVER_RENDERED/ProSeleta | 4 cards resumidos | ≥2 de pessoal | ≥2 observados; total UNKNOWN | CONFIGURABLE_HTML + PDF/filtro | HIGH/MEDIUM |
| 16 | FUMARC | https://www.fumarc.com.br/SitePages/Home.aspx | https://www.fumarc.com.br/SitePages/Home.aspx + /conheca-a-fumarc | SHAREPOINT/PDF | ≥2 processos/documentos | ≥2 | UNKNOWN | SHAREPOINT_API somente se `_api` for confirmado; fallback HTML/PDF | MEDIUM |
| 17 | IMESO | https://portal.imeso.com.br/edital | https://portal.imeso.com.br/edital | HTML+PDF | 4 detalhes + IDs indexados | 4 | UNKNOWN | CONFIGURABLE_HTML + PDF | HIGH/MEDIUM |
| 18 | OMNI | https://portal.omniconcursospublicos.com.br | https://portal.omniconcursospublicos.com.br/ + https://institutoomni.selecao.net.br/ | ProSeleta/HTML | 6 (2 antigo + 4 novo) | 6 | ≥2 futuras | CONFIGURABLE_HTML; dois tenants, dedup por documento | MEDIUM |
| 19 | Instituto ACCESS | https://access.selecao.net.br/index/abertos/ | https://access.selecao.net.br/index/abertos/ | ProSeleta/HTML | 15 | ≥14 pessoal | ≥2 futuras; total UNKNOWN | CONFIGURABLE_HTML + filtro institucional | HIGH |
| 20 | EXAME Auditores | https://concursos.exameconsultores.com.br/index/1/ | https://concursos.exameconsultores.com.br/ | HTML/ProSeleta | 158 no catálogo; 6 andamento | 6/6 amostrados | 1 futura | CONFIGURABLE_HTML + paginação por estado | HIGH |
| 21 | EPL | https://www.eplconcursos.com.br | https://www.eplconcursos.com.br | HTML legado | 0 abertos; históricos em andamento | seleções de pessoal históricas | 0 abertos; andamento UNKNOWN | KEEP_EMPTY abertos + CONFIGURABLE_HTML histórico; revisar depreciação | HIGH/MEDIUM |
| 22 | ABCP | https://abcp.selecao.net.br/index/abertos/ | https://abcp.selecao.net.br/ | ProSeleta/HTML | 10 | 10 | ≥4 abertas | CONFIGURABLE_HTML | HIGH |
| 23 | UNIFIL | https://main.institutounifil.com.br | https://main.institutounifil.com.br/concurso/{id} + https://unifil.br/editais-regulamentos/editais/ | HTML+PDF | ≥13 (2026) | ≥12 | UNKNOWN | DEDICATED/HYBRID; índice/detalhe/PDF | MEDIUM |
| 24 | OBJETIVA | https://concursos.objetivas.com.br | https://concursos.objetivas.com.br/ | ProSeleta/HTML | 12 | 12 | ≥5 futuras | CONFIGURABLE_HTML | HIGH |
| 25 | Leandro Ferreira Consultoria | https://www.leandroferreira.com.br | UNKNOWN | DNS_INACTIVE/IDENTITY_UNCONFIRMED | UNKNOWN | UNKNOWN | UNKNOWN | DEPRECATE_REVIEW_REQUIRED; não substituir pelo município homônimo | HIGH (Sol) |
| 26 | COTEC/FADENOR | https://www.cotec.fadenor.com.br/index/abertos/ | https://cotec-fadenor.selecao.net.br/index/abertos/ | ProSeleta/HTML | 3 abertos + histórico | 2 dos 3 abertos | 2 abertas | CONFIGURABLE_HTML + filtro; seguir `/informacoes/{id}/` | HIGH/MEDIUM |
| 27 | Instituto Águia | https://portal.institutoaguia.org.br/edital | https://portal.institutoaguia.org.br/edital/index/abertos | SERVER_RENDERED | 8 cards (4 andamento + 4 finalizados) | concursos/PSS; total UNKNOWN | 4 andamento; aberto sem cards | CONFIGURABLE_HTML + `/edital/ver/{id}` | MEDIUM |
| 28 | IUDS | https://www.iuds.org.br | https://portal.iuds.org.br/ (histórico) | HTML/PDF; TLS inconclusivo | detalhe histórico 77; universo atual UNKNOWN | cargos conforme editais | UNKNOWN | DEPRECATE_REVIEW_REQUIRED + KEEP_EMPTY só após validação; browser se voltar | LOW (Sol) |
| 29 | Reis & Reis | https://novo.reisauditores.com.br/concursos-em-andamento | https://novo.reisauditores.com.br/concursos-em-andamento | Astro + REST_API | item ID 70; paginação API | 1 | inscrição fechada; `situacaoEdital=PUBLICADO` não basta | REST_API Gestão Seleções; header `X-TenantID: reisauditores` | HIGH (Sol) |
| 30 | MS Concursos | https://www.msconcursos.com.br | https://www.msconcursos.com.br | UNKNOWN | 9 snapshot (2 abertas + 7 andamento) | 9 | 2 abertas | HTTP_HTML/CONFIGURABLE_HTML; href real em runtime | MEDIUM |
| 31 | FACET | https://www.facetconcursos.com.br | https://concursos.facetconcursos.com.br/index/abertos/ | HTML/ProSeleta | 30 totais em 2 páginas | ≥30 | 1 aberta | CONFIGURABLE_HTML + paginação/detalhe | HIGH/MEDIUM |
| 32 | EDUCA PB | https://www.educapb.com.br | https://educapb.selecao.net.br/index/1/ | ProSeleta/HTML | 5 | 5 | 1 aberta | CONFIGURABLE_HTML | HIGH/MEDIUM |
| 33 | ADM&TEC | https://admtec.org.br/ | https://admtec.org.br/ | HTML/detalhe codificado | UNKNOWN | concursos/PSS | UNKNOWN | CONFIGURABLE_HTML/DEDICATED; confirmar índice antes do crawl | MEDIUM |
| 34 | CONTEMAX | https://www.contemaxconsultoria.com.br | UNKNOWN | UNKNOWN; health-check falho | UNKNOWN | UNKNOWN | UNKNOWN | KEEP_BLOCKED + DEPRECATE_REVIEW_REQUIRED; sem parser especulativo | LOW (Sol) |
| 35 | CPCon/UEPB | https://cpcon.uepb.edu.br | https://cpcon.uepb.edu.br | HTML/WordPress legado | muitos por ano; total UNKNOWN | concursos/PSS | UNKNOWN | CONFIGURABLE/DEDICATED; legado + WP; filtro | MEDIUM |
| 36 | FUNVAPI | https://www.funvapi.com.br | https://www.funvapi.com.br/ | WordPress/PDF | ≥5 blocos | concursos e seleção de educação | UNKNOWN | CONFIGURABLE_HTML + archives/PDF; REST só após confirmação | MEDIUM |
| 37 | CONSEP | https://www.consep-pi.com.br | https://www.consep-pi.com.br/concursos | HTML/PDF | 1 andamento + 8 encerrados; abertos empty | testes/PSS/concurso | 1 em andamento | CONFIGURABLE_HTML por status + detalhe/PDF | HIGH |
| 38 | Instituto Consulplan (Azure legado) | https://institutoconsulplan.azurewebsites.net/Concursos | https://www.institutoconsulplan.org.br/Concursos (via fonte 07) | Azure Web App parado; alias legado | 403 `Web App stopped`; universo próprio não aplicável | UNKNOWN; não somar ao sucessor | UNKNOWN; sem crawl independente | DEPRECATE_REVIEW_REQUIRED; preservar alias e deduplicar com 07 | HIGH para migração/não soma |
| 39 | Instituto Avalia | https://www2.avalia.org.br/concursos.jsp | https://www2.avalia.org.br/concursos.jsp | HTML/detalhe | dezenas; total UNKNOWN | concursos/empregos/estágio; filtrar acadêmico | ≥2 abertas observadas | DEDICATED/CONFIGURABLE + `concurso.jsp?id=` | HIGH/MEDIUM |
| 40 | UFU/DIRPS | https://www.portalselecao.ufu.br/servicos/Edital/listar/concursos | https://www.portalselecao.ufu.br/servicos/Edital/listar/concursos | SERVER_RENDERED/HTML | ≥11 atuais; total UNKNOWN | ≥11 atuais + histórico | 11 atuais; não somar categoria | CONFIGURABLE/DEDICATED HTML + filtro DIRPS + cronograma | HIGH |
| 41 | IDGRAN | https://idgran.com.br | UNKNOWN | UNKNOWN/erro interno | UNKNOWN | UNKNOWN | UNKNOWN | KEEP_BLOCKED + DEPRECATE_REVIEW_REQUIRED | LOW |
| 42 | Quadrix | https://quadrix.org.br/index/abertos/ | https://quadrix.org.br/index/abertos/ | HTML/HTTP | UNKNOWN | UNKNOWN | UNKNOWN | CONFIGURABLE_HTML + detalhes/CDN `selecao.net.br` | MEDIUM |
| 43 | Gualimp | https://www.gualimp.com.br | https://www.gualimp.com.br/concursos/ | HTML + detalhe dynamic JS | UNKNOWN | UNKNOWN | UNKNOWN | CONFIGURABLE_HTML; browser/XHR só após observar | MEDIUM |
| 44 | Verbena/UFG | https://institutoverbena.ufg.br | https://institutoverbena.ufg.br | UFG HTML + possível JS | UNKNOWN | UNKNOWN | UNKNOWN | CONFIGURABLE/DEDICATED após mapear CMS/candidato | MEDIUM |
| 45 | IDIB | https://idib.org.br | https://idib.org.br + https://concurso.idib.org.br/SITE/Concursos.aspx | ASP.NET WebForms/HTML | UNKNOWN | UNKNOWN | UNKNOWN | CONFIGURABLE_HTML; preservar aviso JS | MEDIUM |
| 46 | JCM | https://eventos.concursosjcm.com.br | https://concursosjcm.com.br/ | HTML/ProSeleta | UNKNOWN | UNKNOWN | UNKNOWN | CONFIGURABLE_HTML; usar links reais/CDN | MEDIUM |
| 47 | Elo Assessoria | https://eloassessoriaeservicos.com.br/concursos | https://novo.eloassessoriaeservicos.com.br/concursos | Astro + REST_API | 7 correntes; 3 abertas, 3 em breve, 1 encerrado; próximo 3; concluído 123 | 7 correntes após filtro | 3 `inscricoesAbertas=true` | REST_API Gestão Seleções; header `X-TenantID: eloassessoria`; cargos/anexos | HIGH (Sol) |
| 48 | Apta | https://www.aptaconcursos.com.br | https://www.aptaconcursos.com.br | DYNAMIC_JS/browser compatibility | UNKNOWN | UNKNOWN | UNKNOWN | KEEP_BLOCKED; browser real para validar listagem | LOW/MEDIUM |
| 49 | Legalle | https://portal.editais.legalleconcursos.com.br/edital | https://portal.editais.legalleconcursos.com.br/edital | HTML/S3 PDF | UNKNOWN | UNKNOWN | UNKNOWN | CONFIGURABLE_HTML + `/edital/ver/{id}` | MEDIUM |
| 50 | RBO | https://rboconcursos.selecao.net.br/index/abertos/ | https://rboconcursos.selecao.net.br/index/abertos/ | ProSeleta/HTML | UNKNOWN | UNKNOWN | UNKNOWN | CONFIGURABLE_HTML tenant + `/informacoes/{id}/` | MEDIUM |
| 51 | SHDias | https://www.shdias.com.br/concursos/ | https://www.shdias.com.br/concurso | DYNAMIC_JS/browser compatibility | UNKNOWN; indexação mostra cards | UNKNOWN | UNKNOWN | KEEP_BLOCKED + navegador real/live retest | LOW/MEDIUM |
| 52 | Zambini | https://www.zambini.org.br/portal/concursos | https://www.zambini.org.br/portal/concursos | STATIC_HTML | vazio atual + detalhe histórico | UNKNOWN | 0 atual no recorte | CONFIGURABLE_HTML + KEEP_EMPTY | MEDIUM |
| 53 | Nosso Rumo | https://www.nossorumo.org.br | https://nossorumo.org.br/ | SERVER_RENDERED_HTML/legado | vários cartões; total UNKNOWN | concursos/PSS | andamento com datas futuras; total UNKNOWN | CONFIGURABLE_HTML/HTTP_HTML; redirect sem www | MEDIUM |
| 54 | Avança SP | https://avancasp.selecao.net.br/index/abertos/ | https://avancasp.selecao.net.br/index/abertos/ | ProSeleta/HTML | 7 abertos; 37 andamento | 6/7 abertos | 6 de pessoal abertas | CONFIGURABLE_HTML compartilhado ProSeleta; detalhe/anexos | HIGH |
| 55 | Instituto Mais | https://www.institutomais.org.br/Concursos/ConcursosAbertos | https://www.institutomais.org.br/Concursos/ConcursosAbertos | HTML/PDF | 4 abertos + 14 andamento | relevante | 4 abertas | CONFIGURABLE_HTML; seguir detalhe/PDF | HIGH |
| 56 | Publiconsult | https://publiconsult.com.br/Concurso/Index | https://publiconsult.com.br/Concurso/Index | HTML | ≥17 cards | concursos/PSS; total UNKNOWN | UNKNOWN | CONFIGURABLE_HTML; status por legenda/datas, preservar UNKNOWN | MEDIUM |
| 57 | KLC | https://www.klcconcursos.com.br | https://www.klcconcursos.com.br | HTML legado | abertos empty; >100 históricos em andamento | concursos/PSS | UNKNOWN | HTTP_HTML/CONFIGURABLE_HTML; KEEP_EMPTY sem promover históricos | MEDIUM |
| 58 | Sigma | https://concursos.sigmaassessoria.com.br | https://concursos.sigmaassessoria.com.br | ProSeleta/HTML | 1 | 1 contratação | em andamento, prazo já encerrado | CONFIGURABLE_HTML tenant; fixture fechado | HIGH |
| 59 | W2 | https://www.w2consultores.com.br/index/todos/ | https://www.w2consultores.com.br/index/todos/ | provável HTML legado/charset | 247 páginas indexadas | processos/concursos; total filtrado UNKNOWN | UNKNOWN | CONFIGURABLE_HTML + charset fallback; KEEP_BLOCKED se falhar | LOW |
| 60 | Fênix | https://portal.fenix.selecao.site/edital | https://portal.fenix.selecao.site/edital | Gestor Editais/HTML | aberto empty; 2 andamento; snapshot diverge | 2 relevantes | estado conflitante; active UNKNOWN | CONFIGURABLE_HTML; registrar timestamp e conflito, não inferir | MEDIUM |
| 61 | Oppus | https://www.oppusconcursos.com.br | UNKNOWN | domínio indisponível | nenhum atual; PDFs antigos | histórico relevante, atual UNKNOWN | UNKNOWN | KEEP_BLOCKED + DEPRECATE_REVIEW_REQUIRED | LOW |
| 62 | Instituto Legatus | https://www.legatus.org.br | https://www.legatus.org.br | HTML/PDF | ≥10 cards | concursos municipais | há períodos correntes/futuros; total UNKNOWN | CONFIGURABLE_HTML + detalhes/tabelas | HIGH |
| 63 | FEPESE | https://fepese.org.br/concursos/ | https://fepese.org.br/concursos/ | HTML + tenants | 13 projetos 2026 | 13 pessoal | status individual UNKNOWN | HYBRID/CONFIGURABLE_HTML por tenant + publicações | HIGH |
| 64 | FUNCERN | https://funcern.br/concursos/ | https://funcern.br/concursos/ | WordPress-like HTML/PDF | 3 abertos + 2 andamento + 121 resultados | ≥2 abertos de pessoal; filtrar bolsas | ≥2 abertos | CONFIGURABLE_HTML `?page=N` + filtro institucional/PDF | HIGH |
| 65 | FAPEMIG | https://fapemig.br/pt/editais/ | https://fapemig.br/oportunidades/chamadas-e-editais | CMS dinâmico/HTML | 190 chamadas (4 abertas etc.) | 0 pessoal observado | 0 pessoal; fomento ativo | CONFIGURABLE_HTML + KEEP_EMPTY; filtro de fomento | HIGH/MEDIUM |
| 66 | FAPES (ES) | https://fapes.es.gov.br/editais | https://fapes.es.gov.br/editais | SERVER_RENDERED/Orchard | 3 carreira científica + demais | 0 emprego confirmado | 0 pessoal | CONFIGURABLE_HTML + filtro institucional + KEEP_EMPTY | HIGH |
| 67 | FAPESQ (PB) | https://fapesq.rpp.br/editais/ | https://fapesq.rpp.br/editais/editais-2026 | SERVER_RENDERED/Plone-like/PDF | coleção 2026 paginada | vários editais de equipe/pessoal; total UNKNOWN | UNKNOWN | CONFIGURABLE_HTML `b_start:int` + HYBRID/PDF + filtro | MEDIUM |
| 68 | Fundação Uniselva | https://inscricao.fundacaouniselva.org.br/selecoes | https://web.fundacaouniselva.org.br/frmSelecoes.aspx | ASP.NET WebForms | dezenas 2025–26 | múltiplas contratações/estágios | UNKNOWN | CONFIGURABLE_HTML no domínio web; browser só se interface necessária | MEDIUM |
| 69 | Fundação FAFIPA | https://concursos.fundacaofafipa.org.br/ | https://fafipa.selecao.net.br/ | ProSeleta/HTML | 42 em andamento | 42 | 42 em andamento (inscrição individual deve ser verificada) | CONFIGURABLE_HTML compartilhado `selecao.net.br` | HIGH |
| 70 | IESES | https://ieses.org/projetos | https://www.concursos.ieses.org/ | SPA/load-more/tenants | ≥12 projetos | concursos/PSS; total UNKNOWN | UNKNOWN | PLAYWRIGHT/HYBRID; observar XHR antes de usar API | MEDIUM |
| 71 | FUNPEC | https://funpec.br/processos-seletivos/ | https://funpec.br/processos-seletivos/ | HTML/PDF | 3 novos + 6 andamento + 77 encerrados | pessoal | 6 andamento; 3 novos potencialmente ativos | CONFIGURABLE_HTML + estados/paginação + filtro | HIGH |
| 72 | FADE-UFPE | https://fade.org.br | https://fade.org.br/category/editais/ | WordPress/HTML/PDF | ≥67 páginas; 10 por página | estágio/empregos; excluir bolsa pura | UNKNOWN; vários abertos/andamento | CONFIGURABLE_HTML; WordPress API somente se confirmada | HIGH |
| 73 | FAPEX | https://master.fapex.org.br/portalrh/ | https://fapex.org.br/Fapex/Site/Principal/Edital/index + https://fapex.pandape.infojobs.com.br/ | HTML + plataforma externa | editais históricos + 50 vagas Pandapé | contratação/estágio + vagas | 50 vagas Pandapé | HYBRID/DEDICATED; portalrh KEEP_BLOCKED (login) | MEDIUM |
| 74 | FATEC Santa Maria | https://www.fatecsm.org.br/processos-seletivos/ | https://www.fatecsm.org.br/processos-seletivos/ | WordPress/HTML/PDF | 10 (3 andamento + 7 encerrados) | 10 | 3 | CONFIGURABLE_HTML + PDF | HIGH |
| 75 | FAPED | https://faped.org.br | https://faped.org.br/editais | HTML/PDF | muitos editais; 1 filtro celetista | 1 Analista em Sanidade Vegetal | 0; encerrado | CONFIGURABLE_HTML + KEEP_EMPTY + filtro | MEDIUM |
| 76 | FAPESE | https://fapese.org.br | https://www.fapese.org.br/programa-primeiro-emprego/ | WordPress/HTML/PDF | 16 publicações | professores/instrutores; excluir beneficiários | 0 confirmados | CONFIGURABLE_HTML + filtro + KEEP_EMPTY | HIGH |
| 77 | FAPEPI | https://www.fapepi.pi.gov.br/editais-fapepi/ | https://www.fapepi.pi.gov.br/editais-fapepi/ | WordPress/HTML/PDF | ≥9 editais 2026 | 0 pessoal confirmado | 0 | CONFIGURABLE_HTML + KEEP_EMPTY + filtro | HIGH |
| 78 | FAPEMA | https://www.fapema.br/inicio/ | https://www.fapema.br/editais/ | WordPress/HTML/PDF | UNKNOWN | 0 pessoal atual; bolsas/fomento | 0 pessoal | CONFIGURABLE_HTML + filtro + KEEP_EMPTY | HIGH/MEDIUM |
| 79 | FAPECE | https://fapece.ce.gov.br | UNKNOWN | identidade incompatível; host não resolve | UNKNOWN | UNKNOWN | UNKNOWN | DEPRECATE_REVIEW_REQUIRED; confirmar entidade antes de crawler | HIGH para conflito/LOW para alvo |
| 80 | FAPERN | https://fapern.rn.gov.br | https://fapern.rn.gov.br | 503/bloqueado | UNKNOWN | 0 confirmado; bolsa conhecida fora | UNKNOWN | KEEP_BLOCKED/HYBRID após retorno; sem bypass | MEDIUM/LOW |
| 81 | FAPEAL / evento CEBRASPE | https://fapeal.br | https://www.fapeal.br/ + https://www.cebraspe.org.br/concursos/FAPEAL_26 | CEBRASPE REST_API + portal FAPEAL | ≥1 (`FAPEAL_26`, ID 3342; 10 vagas; 23 edital/22 gabarito) | ≥1 seleção de pessoal | 0 inscrições abertas; processo em andamento com prazo fechado | P0 false-empty: discovery CEBRASPE/API; detalhe e CDN, não só arquivo FAPEAL | HIGH (Sol) |
| 82 | FACEPE | https://www.facepe.br | https://www.facepe.br/ + /editais/todos/ | WordPress/HTML/PDF | muitos; total UNKNOWN | ≥1 PSS contratação temporária histórico | 0 atual | HYBRID HTML+PDF + KEEP_EMPTY; fixture seleção simplificada | HIGH/MEDIUM |
| 83 | FAPESB | https://www.fapesb.ba.gov.br/category/edital/ | https://www.fapesb.ba.gov.br/category/edital/ + https://selecao.ba.gov.br/ | WordPress + portal REDA | UNKNOWN | 1 REDA 001/2026, 22 vagas | 0 em 30/08; fechado | HYBRID índice/PDF/portal; fixture REDA; não autenticar | HIGH |
| 84 | FAPERJ | https://faperj.br | https://faperj.br/?id=28.5.7 | HTML/CMS legado | dezenas chamadas; total UNKNOWN | 0 atual; bolsas/auxílios | 0 contratação | CONFIGURABLE_HTML + KEEP_EMPTY; HYBRID só se pessoal em PDF | MEDIUM |
| 85 | FAPESP | https://fapesp.br/oportunidades/ | https://fapesp.br/oportunidades/ | SERVER_RENDERED/HTML | 109 oportunidades | 0 emprego/concurso (bolsas) | 0 escopo | KEEP_EMPTY/DEPRECATE_REVIEW_REQUIRED; não contar 109 como concurso | HIGH |
| 86 | FAPPR/Araucária | https://fappr.pr.gov.br/Pagina/Processos-Seletivos | https://www.fappr.pr.gov.br/Pagina/Processos-Seletivos | HTML/CMS/PDF | UNKNOWN; PS 01–04/2026 | ≥4 estágios + CLT fixture | 0 em 30/08; prazos passados | HYBRID HTML+atos/PDF; fixtures estágio/CLT; excluir NAPI/bolsa | HIGH/MEDIUM |
| 87 | FAPESC | https://fapesc.sc.gov.br | https://fapesc.sc.gov.br/chamadas-abertas/ | WordPress/HTML/PDF | UNKNOWN chamadas 2026 | 0 emprego; bolsas fora | 0 escopo | CONFIGURABLE_HTML + KEEP_EMPTY + filtro; sem plataforma para discovery | HIGH/MEDIUM |
| 88 | FAPERGS | https://fapergs.rs.gov.br/selecao-2025 | https://fapergs.rs.gov.br/selecao-2025 | PROCERGS/HTML/PDF | 1 PSS pessoal | 1 | 0; encerrado | HYBRID detalhe+anexos; fixture 5 agentes e status ENCERRADO | HIGH |
| 89 | FUNDECT | https://www.fundect.ms.gov.br/informativos/consultas/ | https://www.fundect.ms.gov.br/informativos/consultas/ | WordPress/HTML/PDF/DOE | tabela 2024–26; total UNKNOWN | 1 Diretor-Presidente | 0; nomeação 16/12/2025 | HYBRID tabela+detalhe/PDF/DOE; excluir chamadas de projeto/bolsa | HIGH/MEDIUM |
| 90 | FAPEMAT | https://fapemat.mt.gov.br | https://www.fapemat.mt.gov.br/pt/editais_1 | Liferay/server-rendered com componentes dinâmicos e PDFs | UNKNOWN (abas observadas; itens não renderizados) | 0 na amostra; universo total UNKNOWN | 0 confirmadas; universo total UNKNOWN | HYBRID + KEEP_BLOCKED; retestar a rota Liferay e seguir PDFs oficiais | MEDIUM |
| 91 | FAPEG | https://goias.gov.br/fapeg/categoria/editais/ | https://goias.gov.br/fapeg/editais/inscricoes-abertas/ | WordPress/Goiás, tabela HTML + PDF/XLSX | 8 itens abertos observados | 0 na lista aberta; 1 histórico relevante fechado | 0 | CONFIGURABLE_HTML + PDF; filtrar PSS/contratação de pessoa | HIGH |
| 92 | FAPDF | https://fap.df.gov.br | https://www.fap.df.gov.br/ | Portal governamental server-rendered + páginas anuais/PDF | UNKNOWN (arquivo heterogêneo, sem lista atual única) | 0 nas páginas consultadas; universo total UNKNOWN | 0 confirmadas; universo total UNKNOWN | HTTP_HTML/CONFIGURABLE_HTML + KEEP_EMPTY; monitorar arquivos sem usar SIGFAPDF autenticado | MEDIUM |
| 93 | FAPT | https://fapt.to.gov.br | https://fapt.to.gov.br (operacionalidade não confirmada) | PDF_INDEX/OTHER; domínio com timeout | UNKNOWN | UNKNOWN; nenhum item de pessoal confirmado | UNKNOWN | KEEP_BLOCKED + DEPRECATE_REVIEW_REQUIRED; manter PDFs `central.to.gov.br` como fallback | MEDIUM |
| 94 | FAPEAM | https://fapeam.am.gov.br | https://www.fapeam.am.gov.br/editais/ | WordPress com componente Vue/dinâmico; PDFs | UNKNOWN (placeholders `Carregando...`/template) | UNKNOWN; nenhum anúncio de pessoal confirmado | UNKNOWN | HYBRID/PLAYWRIGHT para descobrir a lista; não tratar placeholder como vazio | MEDIUM |
| 95 | FAPESPA | https://fapespa.pa.gov.br | https://www.fapespa.pa.gov.br/chamadas/ | WordPress + PDF; inscrição externa SIPROS | 4 blocos de chamadas observados | 1 PSS relevante (8 vagas), fechado | 0 | CONFIGURABLE_HTML + PDF; SIPROS somente como inscrição/resultado público comprovado | HIGH |
| 96 | FAPEAP | https://fapeap.ap.gov.br | https://fapeap.portal.ap.gov.br/ | Portal estadual Amapá server-rendered + arquivos `matrix.amapa.gov.br` | 7 publicações recentes | 0 confirmadas; amostra de projetos/bolsas | UNKNOWN; nenhuma seleção ativa confirmada | CONFIGURABLE_HTML no domínio novo + PDF; manter SIG FAPEAP separado | HIGH/MEDIUM |
| 97 | FAPERR | https://faperr.rr.gov.br/ | https://faperr.rr.gov.br/ | Shell de aplicação/OTHER; conteúdo `Loading...` | UNKNOWN | UNKNOWN; nenhum item de pessoal confirmado | UNKNOWN | KEEP_BLOCKED + reteste PLAYWRIGHT; não criar API sem evidência | MEDIUM/LOW-MEDIUM |
| 98 | FAPERO | https://rondonia.ro.gov.br/fapero/publicacoes/ | https://rondonia.ro.gov.br/fapero/publicacoes/ | WordPress governamental, HTML + arquivos anuais/PDF | pelo menos 3 blocos programáticos em 2026 | 0 confirmadas na amostra; histórico total UNKNOWN | 0 relevante confirmada | HTTP_HTML + CONFIGURABLE_HTML + PDF + KEEP_EMPTY; filtrar vínculo de pessoal | HIGH/MEDIUM |
| 99 | FAPAC | https://fapac.ac.gov.br/ | https://fapac.ac.gov.br/98-2/ | WordPress/HTML + PDFs e possível iframe/feed | pelo menos 7 publicações/blocos | 0 confirmadas; amostra fora de pessoal | UNKNOWN; universo completo UNKNOWN | CONFIGURABLE_HTML + PDF + KEEP_EMPTY; manter SIGFAPAC fora do discovery | HIGH/MEDIUM |

### 3. Pesquisa individual

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
URL fornecida: `https://www.leandroferreira.com.br`  
URL oficial correta: `UNKNOWN`  
Verificação: 30/08/2026, aproximadamente 18:05, `America/Sao_Paulo` (UTC−03:00).

### Navegação

Homepage, abertos, em andamento, encerrados, detalhe e documentos: `UNKNOWN`. A URL fornecida não possui endereço web resolvível. Nenhum sucessor oficial atribuível à consultoria foi encontrado. O portal `leandroferreira.mg.gov.br` pertence ao município homônimo e **não** é sucessor comprovado desta fonte.

### Universo observado

Observed: `UNKNOWN`. Relevant: `UNKNOWN`. Active: `UNKNOWN`. Closed: `UNKNOWN`. Out of scope: qualquer conteúdo do município de Leandro Ferreira/MG quando usado como substituto desta identidade. A falha DNS não permite concluir zero.

### Listagem

Container, item, título, link, ID e status: `UNKNOWN`; nenhuma listagem oficial atual foi recuperada.

### Paginação

Método e parâmetros: `UNKNOWN`.

### Exemplo real

Nenhum exemplo atual e atribuível à consultoria foi confirmado. Não usar PSS municipal homônimo como fixture.

### Campos

`titulo`, `orgao`, `modalidade`, `cargo`, `area`, `cidade`, `uf`, `status`, `vagas`, `salario_min`, `salario_max`, `escolaridade`, `taxa`, `prova_data`, `edital_numero`, `edital_data`, `inscricao_inicio`, `inscricao_fim`, `link_edital` e `link_inscricao`: `NÃO DISPONÍVEL/UNKNOWN`.

### Publicações

Estrutura, tipos, seletor, API e regras de deduplicação: `UNKNOWN`. Não anexar documentos de terceiros ou do município homônimo à fonte.

### API/XHR

Endpoint, método, parâmetros, paginação, JSON path e autenticação: `UNKNOWN`. Não inventar API nem enumerar IDs.

### Tecnologia

Tipo: `DNS_INACTIVE / UNKNOWN`. A consulta DNS direta encontrou `www.leandroferreira.com.br` inexistente; o domínio raiz retornou apenas o SOA da zona, sem endereço A utilizável. HTTP, JavaScript e Playwright não chegam à aplicação porque não há host web confirmado.

### Bloqueios

Bloqueio atual: `ERR_NAME_NOT_RESOLVED`/DNS. Isso é falha externa de identidade/transporte, não `EMPTY_EXPLICIT`. Não há alternativa oficial confirmada.

### Quality gate

ACEITAR somente após uma comunicação ou página de primeira parte comprovar o sucessor da mesma consultoria e oferecer processo seletivo de pessoal. REJEITAR coincidência nominal, portal municipal, agregadores e documentos históricos sem vínculo verificável com a fonte.

### Empty evidence

`UNKNOWN_EMPTY`. Nunca transformar a falha DNS em `active=0` ou “sem concursos”.

### Estratégia recomendada

`DEPRECATE_REVIEW_REQUIRED` + `KEEP_BLOCKED`. Preservar o identificador técnico por compatibilidade até decisão explícita; não criar parser especulativo e não substituir silenciosamente a URL.

### Instruções para Codex

1. Manter `leandroferreira_open` bloqueado e registrar a falha DNS.
2. Não apontar a fonte para `leandroferreira.mg.gov.br`.
3. Antes de qualquer alteração, exigir um domínio de primeira parte que prove continuidade da consultoria.
4. Se um sucessor for comprovado, refazer apenas a investigação dessa fonte e criar fixture/listagem/detalhe reais.
5. Testar que DNS indisponível resulta em `BLOCKED/UNKNOWN`, nunca em empty legítimo.

### Confidence

HIGH para a indisponibilidade e para a rejeição do portal municipal homônimo; LOW para a existência de sucessor, que permanece `UNKNOWN`.

### Evidências

- `https://www.leandroferreira.com.br` — host não resolvido na consulta de 30/08/2026.
- DNS direto de `www.leandroferreira.com.br` e `leandroferreira.com.br` — nenhum endereço web utilizável.

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



### 4. Cross-source findings

#### 4.1 Regras transversais de evidência

- **Observed não é Relevant e Relevant não é Active.** `Observed` mede o que a superfície oficial mostrou; `Relevant` exige seleção de pessoas para trabalho; `Active` exige estado/prazo oficial. Um processo “em andamento” pode estar com inscrições encerradas.
- **`UNKNOWN` é um resultado válido.** Timeout, desafio, 403, shell `Loading...`, placeholder `Carregando...`, aba sem cards ou índice parcial nunca autorizam zero.
- **Empty exige prova positiva.** Aceitar vazio somente quando a categoria correta foi carregada integralmente, a semântica do status é conhecida e nenhuma evidência contraditória existe em detalhe/documento/origem executora.
- **Detalhe prevalece ao resumo.** Isso é obrigatório no CEBRASPE (#11/#81), onde `isInscricaoAberta` pode divergir entre coleção e detalhe, e nas engines Gestão Seleções (#29/#47), onde “publicado/em andamento” não equivale a inscrição aberta.
- **Contagens são snapshots datados.** Não somar abas sobrepostas, cards repetidos, edital/retificação/resultado, portal institucional e portal executor.

#### 4.2 Fundações de pesquisa: filtro institucional obrigatório

Nas fontes 65–99, “edital”, “seleção”, “vagas”, “beneficiário” ou “contratação” frequentemente descrevem fomento, bolsas, projetos, premiações, pesquisadores apoiados, OSCs ou contratação de **projetos**. Só entra no Observador um item que comprove concurso, PSS, emprego, estágio, cargo ou função de pessoal. Valor de bolsa não é salário; quantidade de projetos não é vaga.

Fixtures negativas devem cobrir Centelha, PPSUS, PDPG, bolsas, credenciamento ad hoc, premiações e chamadas de propostas. Fixtures positivas devem cobrir, entre outras, FAPESPA PSS 001/2025 (#95), FAPESB REDA 001/2026 (#83), FAPERGS PSS 2025 (#88) e FAPEAL 26 (#81). A fonte #81 demonstra por que o arquivo institucional de fomento não pode ser a única origem de discovery.

#### 4.3 Canonicalização, documentos e deduplicação

- Canonicalizar URL após redirects, removendo tokens efêmeros de download e preservando o caminho estável. Na CESGRANRIO, queries SAS expiram e não podem ser identidade.
- Modelar edital-base, retificação, resultado, gabarito, convocação e homologação como publicações derivadas, não como certames distintos.
- Chave preferida: identificador oficial estável; depois órgão + número/ano do edital + URL canônica. Título isolado é insuficiente.
- Preservar origem institucional e origem executora. FAPEAL (#81) usa CEBRASPE sem perder a identidade da Fundação; Consulplan #38 é alias legado de #07 e não gera segundo universo.
- Não autenticar em Área do Candidato, SIGs, SIPROS, PortalRH ou sistemas de submissão. Guardar o link público e usar somente endpoints/documentos públicos confirmados.

#### 4.4 Correções arquiteturais que prevalecem

1. **Consulplan #07/#38:** discovery no sucessor oficial `institutoconsulplan.org.br/Concursos`; o Azure está parado e não deve ser rastreado nem somado.
2. **CEBRASPE #11:** REST público por fase/detalhe/CDN; browser dispensável para discovery; detalhe prevalece ao resumo.
3. **CESGRANRIO #12:** API Angular paginada como origem primária e WordPress como validação/fallback.
4. **Leandro Ferreira #25:** identidade sem host resolvível; o município homônimo não é substituto.
5. **Reis & Reis #29 e Elo #47:** mesma engine Gestão Seleções, cliente REST compartilhável, tenants e regras separados.
6. **FAPEAL #81:** P0 de falso vazio; `FAPEAL_26` tem 10 vagas, processo em andamento e inscrição encerrada.

#### 4.5 Observabilidade mínima

Cada execução deve registrar URL/endpoint, instante em `America/Sao_Paulo`, status HTTP, estratégia usada, número de páginas/itens observados, filtros aplicados, motivo de rejeição e se o estado veio de resumo, detalhe ou PDF. Mudança súbita para zero deve gerar diagnóstico, não exclusão silenciosa.

## Shared Platform Opportunities

| Plataforma | Fontes | Estrutura comum | API comum? | Pode compartilhar conector? |
|---|---|---|---|---|
| Gestão Seleções | 29 Reis & Reis; 47 Elo | Astro + Spring Page base 0; `/api/editais`, detalhe, cargos e anexos; header `X-TenantID` | **Sim**, base `api.gestaoselecoes.com.br` confirmada | **Sim.** Um cliente REST, com tenant, filtros e fixtures por fonte. |
| ProSeleta / `selecao.net.br` | 15, 18, 19, 22, 24, 26, 31, 32, 46, 50, 54, 58, 59 e 69; integração parcial em 04/42 | Cards por estado, detalhes `/informacoes/{id}/` ou variante, anexos/PDF e tenants white-label | **Não confirmada** como API pública comum | **Sim, configurável por HTML**, sem presumir endpoint, status ou seletor idêntico. |
| Gestor Editais / `selecao.site` | 02 IDECAN, 06 IBADE, 17 IMESO, 27 Águia, 49 Legalle e 60 Fênix | Seções de estado, páginas `/edital/ver/{id}`, documentos e cards semelhantes | **Não confirmada** | **Provavelmente.** Compartilhar parser somente após fixtures DOM por tenant. |
| CEBRASPE REST + CDN | 11 CEBRASPE; 81 FAPEAL como origem executora | Coleção por fase, detalhe por identificador, arrays documentais e CDN oficial | **Sim**, endpoints confirmados | **Sim.** A #81 reutiliza o conector #11 com filtro/identidade FAPEAL. |
| CESGRANRIO WordPress + Angular | 12 | Catálogo editorial paginado + `PortalEventos`, conteúdos públicos e grupos de prova | **Sim**, exclusiva desta plataforma | **Sim**, conector dedicado com WP de fallback. |
| HTML/PDF de fundações e portais governamentais | 65–99, com variações documentadas | Título/data/link no HTML; cargos, vagas, requisitos, remuneração e cronograma em PDF | **Não**; nomes SIG não provam backend comum | **Parcialmente.** Reusar componentes de HTML/PDF e quality gate, não um endpoint universal. |
| WordPress editorial + PDF | 36, 64–66, 72, 75–78, 82–85, 87, 89, 91, 95, 98 e 99 | Archives/categorias, posts, anexos, resultados e retificações | `wp-json` somente quando observado; não presumir | **Sim** para primitivas de archive/PDF, com configuração e filtro por fonte. |
| SharePoint documental | 16 FUMARC | Bibliotecas/páginas e PDFs | `/_api` ainda não confirmado | **Não ainda.** Manter HTML/PDF; promover à API só após chamada reproduzida. |
| Sistemas externos de inscrição/submissão | FUNDEP, ProSeleta, Gestão Seleções, SIGs, SIPROS, Pandapé e portais de candidato | Login/cadastro, acompanhamento ou submissão fora do catálogo institucional | Variável e frequentemente autenticada | **Não para discovery autenticado.** Apenas links públicos e resultados comprovados. |

### 5. Execution Order for Codex

A prioridade é de **implementação**, não um selo de qualidade da instituição. Dentro de cada nível, a sequência abaixo já considera risco de perda, clareza da evidência e potencial de reuso.

| Prioridade | Fontes | Objetivo operacional |
|---|---|---|
| **P0 — perda de concurso / false empty** | **15:** 81, 07, 11, 12, 29, 47, 54, 55, 62, 64, 71, 72, 73, 74, 40 | Corrigir primeiro falso vazio, migração, estado incorreto e fontes com oportunidades atuais que a estratégia existente tende a perder. |
| **P1 — endpoint/fixture claro, baixo risco** | **8:** 58, 75, 76, 82, 83, 86, 88, 89 | Incorporar casos fechados/claros e filtros positivos/negativos com alto valor de regressão. |
| **P2 — HTML com estrutura clara** | **25:** 01, 02, 03, 04, 05, 06, 13, 15, 17, 18, 19, 20, 22, 24, 26, 31, 32, 39, 45, 46, 49, 50, 69, 91, 95 | Ajustes diretos em listagem, paginação, detalhe e PDF, preservando tenants e semântica de status. |
| **P3 — conector dedicado** | **19:** 09, 10, 14, 23, 27, 30, 36, 37, 42, 43, 44, 53, 56, 63, 67, 68, 70, 94, 96 | Resolver portais com múltiplas superfícies, estado especial, multi-tenant, PDF ou discovery incompleto. |
| **P4 — browser/estrutura especial** | **3:** 16, 33, 35 | Fazer engenharia controlada de SharePoint/índice legado/CMS antes de definir implementação. |
| **P5 — bloqueado ou instável, com reteste/alternativa** | **12:** 08, 28, 34, 41, 48, 51, 59, 60, 80, 90, 93, 97 | Priorizar fallback oficial, health-check e diagnóstico; não tentar bypass nem emitir empty. |
| **P6 — bloqueado/identidade sem origem operacional** | **5:** 21, 25, 38, 61, 79 | Preservar compatibilidade e evidência; deprecar somente após decisão explícita ou sucessor comprovado. |
| **P7 — empty legítimo / atual fora do escopo** | **12:** 52, 57, 65, 66, 77, 78, 84, 85, 87, 92, 98, 99 | Manter barato e estável; regressões negativas devem impedir que fomento/bolsa/histórico virem ativo. |

A soma é **99/99**. Em P0, a ordem recomendada começa por #81 e #07 porque são falsos vazios comprovados; em seguida vêm as APIs reutilizáveis (#11, #12, #29 e #47), depois as fontes HTML/externas com oportunidades correntes. Uma fonte só desce para P7 quando o vazio/out-of-scope foi observado na superfície correta; qualquer bloqueio permanece P5/P6 ou `UNKNOWN`.

### 6. Matriz de implementação

| Prioridade | Fonte | Problema | Estratégia | URL/Endpoint | O que Codex deve alterar | Testes | Live retest |
|---|---|---|---|---|---|---|---|
| P0 | #81 FAPEAL / evento CEBRASPE | arquivo de fomento gera falso vazio apesar de concurso CEBRASPE em andamento | REST_API/P0 | `https://apis.cebraspe.org.br/cebraspe/eventos/FAPEAL_26` | ingerir ID 3342; manter processo em andamento e inscrição encerrada como estados distintos | 10 vagas; R$ 5.767,15; 23/22 documentos; fomento negativo | API detalhe/fase + página CEBRASPE + documento |
| P0 | #07 Instituto Consulplan | domínio antigo sob Cloudflare causaria false empty; sucessor oficial tem três relevantes abertas/novas | HTTP_HTML/CONFIGURABLE_HTML; browser só em detalhe 403 | `https://www.institutoconsulplan.org.br/Concursos` | migrar discovery da fonte 07; filtrar vestibular/PASES; deduplicar totalmente com 38 | 6 cards abertos/novos: 3 positivos e 3 acadêmicos negativos | lista atual + um detalhe + CDN oficial |
| P0 | #11 CEBRASPE | resumo API contradiz detalhe | REST_API | `apis.cebraspe.org.br/cebraspe/eventos/...` | API por fase; detalhe prevalece | 496, Pontaporã, CDN | 200 e flags |
| P0 | #12 CESGRANRIO | WP e Angular paralelos | REST_API | `/api/PortalEventos`, `/api/PortalEventos/{id}` | API paginada + grupos/conteúdos; WP fallback | evento 22 + SAS | paginação/estado |
| P0 | #29 Reis & Reis | engine REST confirmada | REST_API | `api.gestaoselecoes.com.br/api/editais` | header tenant + flags de inscrição | ID 70/paginação | API 200 |
| P0 | #47 Elo Assessoria | REST tenant Elo | REST_API | `/api/editais`, `/cargos`, `/anexos` | cliente comum com Reis; flags de inscrição | ID 134 + futuro/encerrado | API 200 |
| P0 | #54 Avança SP | 7 abertos, 1 vestibular | CONFIGURABLE_HTML | `/index/abertos/`, `/informacoes/251/` | excluir UNIREGISTRAL; 6 pessoais | CRECI | período |
| P0 | #55 Instituto Mais | 4 abertos + andamento | CONFIGURABLE_HTML | `/Concursos/ConcursosAbertos` | seguir detalhes/PDF | 4 abertas | retestar |
| P0 | #62 Instituto Legatus | detalhe rich/tabelas | CONFIGURABLE_HTML | `/concursos/160/...` | extrair vagas/PCD/taxa | Tanque do Piauí | período |
| P0 | #64 FUNCERN | 121 resultados + bolsas | CONFIGURABLE_HTML | `funcern.br/concursos/` | paginar; excluir SEMURB/ProITEC | 2 abertos | páginas |
| P0 | #71 FUNPEC | 3 novos + 6 andamento + 77 fechado | CONFIGURABLE_HTML | `/processos-seletivos/` | separar estados e filtro pessoal | cuidador 12/2026 | cronograma |
| P0 | #72 FADE-UFPE | 67 páginas, bolsas misturadas | CONFIGURABLE_HTML | `/category/editais/` | paginar; excluir bolsa pura | estágio/DevOps | páginas 1–2 |
| P0 | #73 FAPEX | portal RH exige login | HYBRID/DEDICATED | arquivo FAPEX + Pandapé | não usar `portalrh` para discovery | 50 vagas | URL pública |
| P0 | #74 FATEC Santa Maria | 3 andamento/7 encerrado | CONFIGURABLE_HTML | `/processos-seletivos/` | extrair PDF/status | 10 entradas | reteste |
| P0 | #40 UFU/DIRPS | mistura produtos DIRPS | HTML + filtro | `/servicos/Edital/cronograma/{id}` | aceitar só pessoal; não somar visões | 11 atuais | 144/2026 |
| P1 | #58 Sigma | processo já expirado | CONFIGURABLE_HTML | `sigmaassessoria.com.br` | fixture fechado; não active | Itaju 001.2026 | status |
| P1 | #75 FAPED | compras/oferta vs celetista | CONFIGURABLE + filtro | `/editais` | usar filtro celetista; manter fechado | Analista 001/2025 | filtro |
| P1 | #76 FAPESE | emprego/função vs curso beneficiário | CONFIGURABLE + filtro | `/programa-primeiro-emprego/` | aceitar docentes; excluir beneficiário | Editais 02/06 | status |
| P1 | #82 FACEPE | seleção histórica em portal de bolsas | HYBRID + KEEP_EMPTY | `/editais/todos/`, PDF seleção | fixture PSS; excluir maioria fomento | PDF simplificada | filtros |
| P1 | #83 FAPESB | REDA em portal externo | HYBRID | categoria + `selecao.ba.gov.br` | fixture 22 vagas; link sem autenticar | REDA 001/2026 | status |
| P1 | #86 FAPPR/Araucária | estágio misturado com bolsas | HYBRID | `/Pagina/Processos-Seletivos` | fixtures PS 01–04 e CLT; excluir NAPI | status/atos | prazos |
| P1 | #88 FAPERGS | PSS encerrado com anexos | HYBRID | `/selecao-2025` | fixture 5 agentes; anexos não são itens | ENCERRADO | links |
| P1 | #89 FUNDECT | Diretor-Presidente fechado | HYBRID + filtro | `/informativos/consultas/` | separar cargo de chamadas de projeto | nomeação 16/12/2025 | anos/categorias |
| P2 | #01 IBFC | aberto empty explícito | CONFIGURABLE_HTML | `/index/abertos/` | manter empty e separar andamento/finalizados | empty + paginação 339 | confirmar texto e contagem |
| P2 | #02 IDECAN | estado em seções Gestor Editais | CONFIGURABLE_HTML | `/edital/index/abertos`, `/edital/ver/{id}` | parser por seção e detalhe | `/ver/24`, arquivo ausente | repetir estados |
| P2 | #03 Instituto AOCP | shell sem cards | PLAYWRIGHT/HYBRID | `/concursos/status/inscricoes-abertas` | browser para cards; não false-empty | SAEB/CESAMA | verificar cards |
| P2 | #04 CONSULPAM | HTML com ícones de status | CONFIGURABLE_HTML | `index.php?menu=concursos` | mapear alt/texto e tenant externo | 9 abertas + detalhe | repetir legenda |
| P2 | #05 IBAM | tabelas/PDF e suspensão | DEDICATED_CONNECTOR | `ibam-concursos.org.br` | extrair tabela e PDFs; respeitar suspensão | 4 abertas + Lages | datas/status |
| P2 | #06 IBADE | empty de inscrição, histórico | CONFIGURABLE_HTML | `/edital`, `/edital/ver/{id}` | separar EM INSCRIÇÃO de andamento | empty + `/ver/126` | verificar item |
| P2 | #13 IDCAP | cards e estados incompletos | CONFIGURABLE_HTML | `idcap.org.br` | seguir cards/detalhe e filtrar | 22 + ≥2 abertos | recontar |
| P2 | #15 FUNDEP/Gestão | catálogo resumido e tenant | CONFIGURABLE_HTML | `fundep.selecao.net.br/informacoes/{id}` | seguir “Ver todos”; PDF para campos | DMAE 63/EMATER 71 | datas |
| P2 | #17 IMESO | total/paginação não expostos | CONFIGURABLE_HTML + PDF | `/edital/ver/{id}` | seguir IDs e anexos | IDs 122/124/127/135 | repetir |
| P2 | #18 OMNI | dois domínios/universos | CONFIGURABLE_HTML | dois tenants ProSeleta | configurar ambos e deduplicar | Saltinho/Tapejara | comparar IDs |
| P2 | #19 Instituto ACCESS | uma especialização fora do escopo | CONFIGURABLE_HTML + filtro | `access.selecao.net.br` | excluir UFAC acadêmico | 14 pessoais + UFAC | status |
| P2 | #20 EXAME Auditores | catálogo paginado | CONFIGURABLE_HTML | `exameconsultores.../index/1/` | percorrer estados e query params | catálogo 158 + Santana | prazo |
| P2 | #22 ABCP | redirect e ProSeleta | CONFIGURABLE_HTML | `/informacoes/2867/` | canonicalizar homepage; seguir detalhe | Ibiúna 33 vagas | período |
| P2 | #24 OBJETIVA | ProSeleta com PSS | CONFIGURABLE_HTML | `/informacoes/2602/` | extrair detalhe/CDN | 5 futuras | período |
| P2 | #26 COTEC/FADENOR | domínio migrado ProSeleta | CONFIGURABLE_HTML + filtro | `/informacoes/28/` | usar URL atual confirmada | 2 pessoais + vestibular | datas |
| P2 | #31 FACET | duas páginas e detalhe | CONFIGURABLE_HTML | `/index/todos/`, `/informacoes/{id}/` | seguir paginação real | 30 total/Floresta | páginas 1–2 |
| P2 | #32 EDUCA PB | canonical ProSeleta | CONFIGURABLE_HTML | `/index/1/`, `/informacoes/6/` | mapear “Inscrições Abertas” | Cuité | status |
| P2 | #39 Instituto Avalia | filtro acadêmico | DEDICATED/CONFIGURABLE | `concurso.jsp?id=597` | usar detalhe para publicações | EPAGRI/UESB | inscrições |
| P2 | #45 IDIB | WebForms | CONFIGURABLE_HTML | `concurso.idib.org.br/SITE/Concursos.aspx` | parsear tabelas apesar de aviso JS | links/estado | HTTP |
| P2 | #46 JCM | host/ProSeleta migrado | CONFIGURABLE_HTML | `concursosjcm.com.br` | usar domínio atual e anexos reais | href/CDN | HTTP |
| P2 | #49 Legalle | links S3/detalhe | CONFIGURABLE_HTML | `/edital/ver/{id}` | seguir hrefs, não assumir consulta única | anexos | HTTP |
| P2 | #50 RBO | tenant ProSeleta | CONFIGURABLE_HTML | `/informacoes/{id}/` | parser configurável | item/detail | HTTP |
| P2 | #69 Fundação FAFIPA | 42 em andamento não necessariamente abertos | CONFIGURABLE_HTML | `fafipa.selecao.net.br` | validar período item a item | 42 | datas |
| P2 | #91 FAPEG | 8 chamadas abertas de fomento; PSS relevante apenas histórico | CONFIGURABLE_HTML + PDF | `/editais/inscricoes-abertas/` e `/encerrados/` | parsear tabela por cabeçalho; aceitar contratação de pessoa e rejeitar bolsas/projetos | 8 itens negativos + PSS 001/2024 fechado | três listas de estado + PDF PSS |
| P2 | #95 FAPESPA | PSS de 8 vagas misturado a chamadas de bolsas/projetos | CONFIGURABLE_HTML + PDF | `https://www.fapespa.pa.gov.br/chamadas/` | extrair bloco PSS, anexos I/II e publicações; SIPROS só como link público | PSS 001/2025 positivo; Connect Amazônia negativo | lista + edital vigente + resultado final |
| P3 | #09 FCC | andamento mistura modalidades | DEDICATED/CONFIGURABLE | `concursoAndamento.html` | filtro institucional; status por detalhe | vestibular/certificação | comparar 30 |
| P3 | #10 FGV | lista mistura exames | CONFIGURABLE_HTML | `/concursos` | filtro de concurso/emprego | CPNU2 + ruídos | validar item |
| P3 | #14 IBGP | JSP sem cards | HYBRID + KEEP_EMPTY | `index.jsp`, download REST | não promover PDF recente a ativo | PDF 21269 + abas | HTTP/browser |
| P3 | #23 UNIFIL | índice ausente/status por PDF | DEDICATED/HYBRID | `/concurso/{id}` | discovery por links; excluir ID 195 | Sarandi 182 | detalhe |
| P3 | #27 Instituto Águia | “em andamento” não é aberto | CONFIGURABLE_HTML | `/edital/ver/{id}` | separar seção e status | 42 finalizado | recontagem |
| P3 | #30 MS Concursos | snapshot sem href | HTTP_HTML | `msconcursos.com.br` | coletar href em runtime | 2 abertas/7 andamento | links |
| P3 | #36 FUNVAPI | posts podem usar REST, não confirmado | CONFIGURABLE_HTML | `/category/concursos/` | archives + PDFs | 5 blocos | status |
| P3 | #37 CONSEP | aberto empty + andamento | CONFIGURABLE_HTML | `/concursos`, detalhe | manter 1 andamento distinto | edital 002/2026 | status |
| P3 | #42 Quadrix | total unknown/ProSeleta CDN | CONFIGURABLE_HTML | `/index/abertos/` | parser por href e detalhe | empty/itens | HTTP |
| P3 | #43 Gualimp | detalhe JS/XHR | CONFIGURABLE + browser | `/concursos/` | observar chamada antes de API | card/detalhe | DOM |
| P3 | #44 Verbena/UFG | portal UFG/CMS | DEDICATED/CONFIGURABLE | `institutoverbena.ufg.br` | mapear candidato/lista | rotas oficiais | browser |
| P3 | #53 Nosso Rumo | cartões sem detalhe público | CONFIGURABLE_HTML | `nossorumo.org.br/` | usar home/status; não rota CPF | Mairiporã | redirect |
| P3 | #56 Publiconsult | datas/status misturados | CONFIGURABLE_HTML | `/Concurso/Index` | manter active UNKNOWN sem status | Sarapuí | revalidar |
| P3 | #63 FEPESE | tenants por projeto | HYBRID | `fepese.org.br/concursos/` | visitar cada tenant; status UNKNOWN | 13 projetos | reteste |
| P3 | #67 FAPESQ (PB) | itens de equipe/pessoal, estado incerto | HYBRID + PDF | `/editais/editais-2026?b_start:int=N` | paginar offsets; status por cronograma | editais 58/57/55 | todos offsets |
| P3 | #68 Fundação Uniselva | listagem web separada da inscrição | CONFIGURABLE_HTML | `web.../frmSelecoes.aspx` | usar web para discovery; não login | 017/2026 | tabela |
| P3 | #70 IESES | SPA/load-more | PLAYWRIGHT/HYBRID | `www.concursos.ieses.org` | observar XHR; não inventar API | 12 tenants | botão |
| P3 | #94 FAPEAM | abas Vue entregam placeholders, sem itens no HTML textual | PLAYWRIGHT/HYBRID | `https://www.fapeam.am.gov.br/editais/` | observar XHR em navegador; preferir endpoint somente se reproduzido; seguir detalhes/PDF e filtrar fomento | `Carregando...` não é empty; PDPG negativo | browser + rede + detalhe 015/2026 |
| P3 | #96 FAPEAP | domínio fornecido migrou; publicações atuais são fomento | CONFIGURABLE_HTML + PDF | `https://fapeap.portal.ap.gov.br/` | atualizar canonical; ler tabela e downloads `matrix.amapa.gov.br`; filtrar instituição/pessoal | redirect/migração; PDPG e Startup negativos | homepage + sete publicações + download |
| P4 | #16 FUMARC | SharePoint/biblioteca | HTML/PDF; `_api` só observado | `fumarc.com.br/Documentos...` | parser de biblioteca; sem endpoint inventado | Ubá 08/2025 | PDF acessível |
| P4 | #33 ADM&TEC | índice/ID codificado | CONFIGURABLE/DEDICATED | `admtec.org.br` | confirmar discovery antes de crawl | rota MTEz/MTIx | hrefs |
| P4 | #35 CPCon/UEPB | legado + novo WP | CONFIGURABLE/DEDICATED | `cpcon.uepb.edu.br` | unir só com dedup e filtro | ano 2020/21 | catálogo |
| P5 | #08 SEPROD | TLS/acesso não reproduzível | KEEP_BLOCKED | `/concursos/` | health-check antes de parser | TLS/browser | repetir acesso |
| P5 | #28 IUDS | TLS/portal histórico | KEEP_BLOCKED | `portal.iuds.org.br` | não concluir vazio | detalhe 77/browser | retestar |
| P5 | #34 CONTEMAX | health-check falho | KEEP_BLOCKED | `contemaxconsultoria.com.br` | sem parser especulativo | HTTP/HTTPS | retestar |
| P5 | #41 IDGRAN | erro interno | KEEP_BLOCKED | `idgran.com.br` | não fabricar URL correta | HTTP/browser | health-check |
| P5 | #48 Apta | tela incompatibilidade | KEEP_BLOCKED | `aptaconcursos.com.br` | browser real somente após validação | compatibilidade | live browser |
| P5 | #51 SHDias | incompatibilidade JS | KEEP_BLOCKED | `/concurso` | usar indexação só como pista | browser real | live |
| P5 | #59 W2 | charset/decoding | CONFIGURABLE + charset | `/index/todos/` | testar UTF-8/Windows-1252; não inventar Lambari | page 7/247 | HTTP |
| P5 | #60 Fênix | snapshots conflitantes | CONFIGURABLE_HTML | `/edital` | timestamp/status textual; active UNKNOWN | 2 andamento + empty | comparar |
| P5 | #80 FAPERN | 503 | KEEP_BLOCKED | `fapern.rn.gov.br` | registrar bloqueio; não bypass | HTTP 503 | DOE/portal |
| P5 | #90 FAPEMAT | abas Liferay não renderizadas; `Request Rejected`; risco de misturar outros órgãos MT | HYBRID + KEEP_BLOCKED | `https://www.fapemat.mt.gov.br/pt/editais_1` | usar rota atual; capturar abas/lista só após confirmação; filtrar órgão e seguir PDFs; manter UNKNOWN | Centelha negativo; SECITEC excluída; placeholder não é empty | HTTP/browser das abas + um PDF FAPEMAT |
| P5 | #93 FAPT | domínio FAPT com timeout; nenhuma migração confirmada | KEEP_BLOCKED + fallback PDF | `https://fapt.to.gov.br` + `central.to.gov.br` | preservar identidade FAPT; nunca substituir por FAPTO; PDF isolado não vira catálogo | Rosas da Ciência negativo; FAPT ≠ FAPTO | health-check do domínio + PDF oficial |
| P5 | #97 FAPERR | homepage pública permanece em shell `Loading...` | KEEP_BLOCKED + PLAYWRIGHT retest | `https://faperr.rr.gov.br/` | descobrir lista/request somente em navegador; manter SISC&T fora do discovery | shell não é empty; PPSUS negativo; sem API inventada | browser + PDF PPSUS + health-check |
| P6 | #21 EPL | “andamento” legado | KEEP_EMPTY + histórico | `/concursos/andamento` | não marcar ativo sem data | abertos empty/CFS | health-check |
| P6 | #25 Leandro Ferreira Consultoria | identidade errada no batch | DEPRECATE_REVIEW_REQUIRED | `UNKNOWN` | não substituir pela Prefeitura; preservar ID | DNS/SOA sem A | confirmar sucessor primário |
| P6 | #38 Instituto Consulplan (Azure legado) | Azure `Web App stopped`; alias duplicaria a fonte 07 | DEPRECATE_REVIEW_REQUIRED | Azure legado → sucessor da #07 | desativar crawl independente sem apagar compatibilidade; nunca somar contagens | 403 vira BLOCKED/alias, não `[]`; dedup 07/38 | Azure health-check + portal sucessor |
| P6 | #61 Oppus | domínio indisponível | KEEP_BLOCKED | `oppusconcursos.com.br` | somente evidência histórica | no current item | health-check |
| P6 | #79 FAPECE | identidade FAPECE incompatível | DEPRECATE_REVIEW_REQUIRED | `fapece.ce.gov.br` | confirmar entidade; sem crawler | DNS + fapece.com.br | revisão Sol |
| P7 | #52 Zambini | vazio atual/histórico | KEEP_EMPTY | `/portal/concursos` | não promover histórico | empty + detalhe | confirmar |
| P7 | #57 KLC | abertos empty, históricos | KEEP_EMPTY + HTML | `klcconcursos.com.br` | separar histórico; não usar datas antigas | empty | reteste |
| P7 | #65 FAPEMIG | FAPEMIG é fomento | KEEP_EMPTY + filtro | `/oportunidades/chamadas-e-editais` | não converter 4 abertas em emprego | 190/4/0 | reteste |
| P7 | #66 FAPES (ES) | FAPES só bolsas/fomento | KEEP_EMPTY + filtro | `/editais` | preservar 0 pessoal | 3 carreira científica | categorias |
| P7 | #77 FAPEPI | fomento/bolsas | KEEP_EMPTY + filtro | `/editais-fapepi/` | preservar 0 de pessoal | 9 editais | categorias |
| P7 | #78 FAPEMA | FMRB bolsa não é emprego | KEEP_EMPTY + filtro | `/editais/` | teste negativo FMRB 14/2026 | posts/PDF | reteste |
| P7 | #84 FAPERJ | chamadas/bolsas | KEEP_EMPTY + filtro | `?id=28.5.7` | só promover pessoal com PDF | TCT negativo | categorias |
| P7 | #85 FAPESP | 109 bolsas | KEEP_EMPTY | `/oportunidades/` | não contar 109 como concursos | oportunidade 9739 | reteste |
| P7 | #87 FAPESC | bolsas/chamadas abertas | KEEP_EMPTY + filtro | `/chamadas-abertas/` | não converter bolsas em vagas | FAPESC 49/2026/Ciasc 22/2026 | categorias |
| P7 | #92 FAPDF | arquivos anuais heterogêneos, sem índice atual único de pessoal | HTTP_HTML + KEEP_EMPTY | `https://www.fap.df.gov.br/` e páginas anuais | monitorar arquivos públicos; não usar SIGFAPDF autenticado nem credenciamento como emprego | Edital 09/2025 ad hoc negativo; UNKNOWN global | homepage + arquivo anual + PDF |
| P7 | #98 FAPERO | arquivo WordPress atual contém bolsas/projetos, não emprego | CONFIGURABLE_HTML + PDF + KEEP_EMPTY | `/fapero/publicacoes/` e arquivos anuais | monitorar HTML/PDF; exigir vínculo/cargo antes de Relevant | TIC/CTI e CAFIX negativos; paginação anual | 2026 + `/pg/2/` + PDF |
| P7 | #99 FAPAC | página de editais contém bolsas, PPSUS, Centelha e OSC | CONFIGURABLE_HTML + PDF + KEEP_EMPTY | `https://fapac.ac.gov.br/98-2/` | monitorar somente superfície pública; manter SIGFAPAC fora do discovery | Mentes Azuis/PPSUS/Centelha/OSC negativos | página de editais + um documento |

# INSTRUCTIONS TO THE CODEX IMPLEMENTATION AGENT

Este documento foi produzido após pesquisa externa das **99 fontes**. O código do projeto será disponibilizado separadamente a este agente; a pesquisa aqui registrada é a base técnica e deve ser tratada como evidência datada de 30/08/2026, não como autorização para inventar comportamento.

1. Mapeie cada **identificador técnico** das seções individuais para o `SourceDefinition`, configuração ou conector existente no código.
2. Não refaça do zero toda a pesquisa dos sites.
3. Antes de alterar uma fonte, faça somente uma validação rápida da URL/endpoint, do estado e de uma fixture oficial para confirmar que a evidência continua atual.
4. Execute estritamente na ordem **P0 → P7** da matriz de implementação; dentro de P0, comece por #81, #07 e pelas APIs compartilháveis.
5. Prefira API estável e pública ao scraping visual quando este runbook confirmou uma API.
6. Aproveite as plataformas compartilhadas, especialmente Gestão Seleções, ProSeleta/Gestor Editais e CEBRASPE.
7. Não duplique conectores quando diversas bancas usam a mesma engine; mantenha tenant, URL, filtro e fixtures específicos em configuração.
8. Cada alteração deve ganhar regression tests de listagem, paginação, detalhe, documentos, status, deduplicação e filtros aplicáveis.
9. Cada grupo de alterações deve receber live targeted test nas fontes afetadas, com timestamp em `America/Sao_Paulo`.
10. Não relaxe filtros apenas para aumentar a quantidade de concursos.
11. Não transforme `UNKNOWN` em zero, string vazia, URL presumida, selector inventado ou contagem estimada.
12. Não transforme uma fonte em `VERIFIED` sem evidência reproduzida de listagem/detalhe e fixture oficial.
13. Empty legítimo deve permanecer vazio e possuir teste negativo.
14. Blocked legítimo pode permanecer bloqueado; registre motivo, tentativa, fallback e próxima condição de reteste.
15. Mantenha separados estado do processo e estado da inscrição. “Em andamento” não significa “inscrição aberta”.
16. Em FAPs/fundações, rejeite bolsas, fomento, premiações, propostas, OSCs e contratação de projetos, salvo prova explícita de vínculo de pessoal.
17. Não altere o aplicativo mobile.
18. Não apague PostgreSQL para “resolver” inconsistência.
19. Não remova unique constraints nem contorne deduplicação; corrija canonicalização/chaves com migração segura quando realmente necessário.
20. Depois das correções, execute **um único ciclo completo** e produza um BEFORE/AFTER auditável.

Fluxo recomendado por fonte:

- Capture o estado anterior e a razão do problema.
- Revalide a evidência mínima indicada na linha da matriz.
- Implemente a menor mudança compatível com o conector compartilhado.
- Rode fixtures positivas e negativas; para FAPs, ambas são obrigatórias.
- Rode o live targeted test e registre itens observados, relevantes, ativos e rejeitados.
- Só então avance para a próxima fonte/prioridade.

O BEFORE/AFTER final deve listar, por fonte: URL canônica, estratégia, estado operacional, contagens com origem, itens adicionados/removidos, motivo das rejeições, testes executados e qualquer `UNKNOWN/BLOCKED` remanescente. Não use o output anterior do crawler como expected; expected vem das fixtures e evidências oficiais deste runbook, atualizadas pelo reteste rápido.
