# Rascunho de consolidação — fontes 01–89

Documento de apoio tabular para a consolidação do Sol. Foi produzido a partir dos dois anexos de auditoria, dos lotes `BATCH_01.md`–`BATCH_07.md` e de `SOL_SPOTCHECKS.md`. `UNKNOWN` é preservado quando a evidência não permite concluir. As correções do SOL prevalecem sobre os lotes, inclusive 07, 11, 12, 25, 29, 38, 47 e 81.

## Critérios de leitura

- `observed` é o universo visível/confirmado na pesquisa; `relevant` é o subconjunto de seleção de pessoal; `active` exige evidência de inscrição/estado atual. “Em andamento” sozinho não é inscrição aberta.
- Bolsas, fomento, auxílio, prêmio, pesquisa, proposta e vestibular ficam fora do escopo salvo prova explícita de vínculo de pessoal. Categorias podem se sobrepor (não somar sem deduplicação).
- Estratégias e prioridades são recomendações de implementação. P0/P1 preservam fixtures e oportunidades/contradições críticas; P2 cobre conectores claros/ativos; P3/P4 cobrem lacunas operacionais; P5/P6 cobrem bloqueio/identidade; P7 é vazio/out-of-scope legítimo.
- A fonte 81 é a exceção corrigida pelo Sol: o evento CEBRASPE `FAPEAL_26` (ID 3342) comprova pelo menos um item relevante em andamento, com inscrições fechadas; não é empty.

## Matriz de fontes (01–89)

| # | fonte | ID técnico | URL inicial | URL correta | tecnologia | observed | relevant | active | estratégia | confiança | prioridade |
|---:|---|---|---|---|---|---|---|---|---|---|:---:|
| 1 | IBFC | `ibfc_open` | https://concursos.ibfc.org.br/index/abertos/ | https://concursos.ibfc.org.br/index/abertos/ | SERVER_RENDERED/HTML | 347 (8 andamento + 339 finalizados) | 347 | 0 abertas (empty explícito) | CONFIGURABLE_HTML + KEEP_EMPTY | HIGH | P2 |
| 2 | IDECAN | `idecan_open` | https://portal.concursos.idecan.org.br/edital/index/abertos | https://portal.concursos.idecan.org.br/edital/index/abertos | SERVER_RENDERED/Gestor Editais | ≥5 | ≥5 | 0 em inscrição (empty explícito) | CONFIGURABLE_HTML; validar tenant com IBADE | HIGH/MEDIUM | P2 |
| 3 | Instituto AOCP | `aocp_open` | https://www.institutoaocp.org.br/ | https://www.institutoaocp.org.br/concursos/status/inscricoes-abertas | BROWSER_REQUIRED/SPA provável | ≥2 | ≥2 | ≥1 confirmado, total UNKNOWN | PLAYWRIGHT ou HYBRID | MEDIUM | P2 |
| 4 | CONSULPAM | `consulpam_open` | https://www.consulpam.com.br/index.php?menu=concursos | https://www.consulpam.com.br/index.php?menu=concursos | SERVER_RENDERED/HTML | ≥60 | ≥60 | 9 abertas | CONFIGURABLE_HTML + tenant `consulpam.selecao.net.br` | HIGH/MEDIUM | P2 |
| 5 | IBAM | `ibam_open` | https://www.ibam-concursos.org.br/ | https://www.ibam-concursos.org.br/ | SERVER_RENDERED/HTML+PDF | ≥5 | ≥5 | 4 com período aberto; 1 suspenso/em breve | DEDICATED_CONNECTOR + HTTP_HTML | HIGH/MEDIUM | P2 |
| 6 | IBADE | `ibade_open` | https://portal.ibade.selecao.site/edital | https://portal.ibade.selecao.site/edital | SERVER_RENDERED/Gestor Editais | ≥6 andamento | ≥6 | 0 em inscrição (empty explícito) | CONFIGURABLE_HTML; avaliar compartilhamento com IDECAN | HIGH/MEDIUM | P2 |
| 7 | Instituto Consulplan | `consulplan_open` | https://www.consulplan.net/ | https://www.consulplan.net/ | WAF/Cloudflare; conteúdo dinâmico | headings sem cards; total UNKNOWN | UNKNOWN | UNKNOWN | PLAYWRIGHT/HYBRID; não transformar desafio em vazio | LOW; Sol: WAF_BLOCKED | P5 |
| 8 | SEPROD | `seprod_open` | https://www.seprod.com.br/concursos/ | https://www.seprod.com.br/concursos/ | OTHER; TLS/área autenticada | categorias indexadas, cards UNKNOWN | UNKNOWN | UNKNOWN | KEEP_BLOCKED + PLAYWRIGHT/HYBRID após health-check | LOW | P5 |
| 9 | FCC | `fcc_open` | https://www.concursosfcc.com.br/concursoAndamento.html | https://www.concursosfcc.com.br/concursoAndamento.html | SERVER_RENDERED/HTML+PDF | 30 em andamento | maioria, com ruído acadêmico | UNKNOWN | DEDICATED_CONNECTOR ou CONFIGURABLE_HTML + filtro | HIGH/MEDIUM | P3 |
| 10 | FGV | `fgv_open` | https://conhecimento.fgv.br/concursos | https://conhecimento.fgv.br/concursos | SERVER_RENDERED/HTML+PDF | ≥44 links | maioria; filtrar exames/certificações | ≥1 (CPNU2), total UNKNOWN | CONFIGURABLE_HTML + filtro institucional | HIGH/MEDIUM | P3 |
| 11 | CEBRASPE | `cebraspe_open` | https://www.cebraspe.org.br/concursos/ | https://www.cebraspe.org.br/Concursos/ | REST_API/React | 496 (5 novos, 6 abertos, 60 andamento, 425 encerrados) | UNKNOWN por item; grupo de concursos | detalhe prevalece; Pontaporã aberto; resumo pode falsear `isInscricaoAberta` | REST_API; detalhe `/eventos/{id}` e CDN | HIGH (Sol) | P0 |
| 12 | CESGRANRIO | `cesgranrio_open` | https://www.cesgranrio.org.br/concursos/ | https://www.cesgranrio.org.br/concursos/ + Angular API | WORDPRESS + REST_API/Angular | 32 detalhes (10+10+10+2); 1 em categoria aberta | filtrar vestibular/avaliação | Transpetro 2026 na categoria aberta; status por conteúdo | REST_API `PortalEventos` + WP fallback | HIGH (Sol) | P0 |
| 13 | IDCAP | `idcap_open` | https://www.idcap.org.br/ | https://www.idcap.org.br/ | SERVER_RENDERED/HTML | 22 em andamento | 22 | ≥2 com período futuro/aberto; total UNKNOWN | CONFIGURABLE_HTML + filtro | HIGH/MEDIUM | P2 |
| 14 | IBGP | `ibgp_open` | https://novo.ibgpconcursos.com.br/inscricoes_abertas.jsp | https://novo.ibgpconcursos.com.br/index.jsp + /inscricoes_abertas.jsp | JSP/PDF_INDEX | 0 cards abertos; 4 estados | UNKNOWN | UNKNOWN | HYBRID + KEEP_EMPTY temporário; seguir `concurso.jsp?cod=` e download REST | MEDIUM | P3 |
| 15 | FUNDEP/Gestão | `fundep_open` | https://www.gestaodeconcursos.com.br/site/site/default.aspx | https://www.gestaodeconcursos.com.br/site/site/default.aspx + https://fundep.selecao.net.br | SERVER_RENDERED/ProSeleta | 4 cards resumidos | ≥2 de pessoal | ≥2 observados; total UNKNOWN | CONFIGURABLE_HTML + PDF/filtro | HIGH/MEDIUM | P2 |
| 16 | FUMARC | `fumarc_open` | https://www.fumarc.com.br/SitePages/Home.aspx | https://www.fumarc.com.br/SitePages/Home.aspx + /conheca-a-fumarc | SHAREPOINT/PDF | ≥2 processos/documentos | ≥2 | UNKNOWN | SHAREPOINT_API somente se `_api` for confirmado; fallback HTML/PDF | MEDIUM | P4 |
| 17 | IMESO | `imeso_open` | https://portal.imeso.com.br/edital | https://portal.imeso.com.br/edital | HTML+PDF | 4 detalhes + IDs indexados | 4 | UNKNOWN | CONFIGURABLE_HTML + PDF | HIGH/MEDIUM | P2 |
| 18 | OMNI | `omni_open` | https://portal.omniconcursospublicos.com.br | https://portal.omniconcursospublicos.com.br/ + https://institutoomni.selecao.net.br/ | ProSeleta/HTML | 6 (2 antigo + 4 novo) | 6 | ≥2 futuras | CONFIGURABLE_HTML; dois tenants, dedup por documento | MEDIUM | P2 |
| 19 | Instituto ACCESS | `access_open` | https://access.selecao.net.br/index/abertos/ | https://access.selecao.net.br/index/abertos/ | ProSeleta/HTML | 15 | ≥14 pessoal | ≥2 futuras; total UNKNOWN | CONFIGURABLE_HTML + filtro institucional | HIGH | P2 |
| 20 | EXAME Auditores | `exame_open` | https://concursos.exameconsultores.com.br/index/1/ | https://concursos.exameconsultores.com.br/ | HTML/ProSeleta | 158 no catálogo; 6 andamento | 6/6 amostrados | 1 futura | CONFIGURABLE_HTML + paginação por estado | HIGH | P2 |
| 21 | EPL | `epl_open` | https://www.eplconcursos.com.br | https://www.eplconcursos.com.br | HTML legado | 0 abertos; históricos em andamento | seleções de pessoal históricas | 0 abertos; andamento UNKNOWN | KEEP_EMPTY abertos + CONFIGURABLE_HTML histórico; revisar depreciação | HIGH/MEDIUM | P6 |
| 22 | ABCP | `abcp_open` | https://abcp.selecao.net.br/index/abertos/ | https://abcp.selecao.net.br/ | ProSeleta/HTML | 10 | 10 | ≥4 abertas | CONFIGURABLE_HTML | HIGH | P2 |
| 23 | UNIFIL | `unifil_open` | https://main.institutounifil.com.br | https://main.institutounifil.com.br/concurso/{id} + https://unifil.br/editais-regulamentos/editais/ | HTML+PDF | ≥13 (2026) | ≥12 | UNKNOWN | DEDICATED/HYBRID; índice/detalhe/PDF | MEDIUM | P3 |
| 24 | OBJETIVA | `objetiva_open` | https://concursos.objetivas.com.br | https://concursos.objetivas.com.br/ | ProSeleta/HTML | 12 | 12 | ≥5 futuras | CONFIGURABLE_HTML | HIGH | P2 |
| 25 | Leandro Ferreira Consultoria | `leandroferreira_open` | https://www.leandroferreira.com.br | UNKNOWN | DNS_INACTIVE/IDENTITY_UNCONFIRMED | UNKNOWN | UNKNOWN | UNKNOWN | DEPRECATE_REVIEW_REQUIRED; não substituir pelo município homônimo | HIGH (Sol) | P6 |
| 26 | COTEC/FADENOR | `cotec_open` | https://www.cotec.fadenor.com.br/index/abertos/ | https://cotec-fadenor.selecao.net.br/index/abertos/ | ProSeleta/HTML | 3 abertos + histórico | 2 dos 3 abertos | 2 abertas | CONFIGURABLE_HTML + filtro; seguir `/informacoes/{id}/` | HIGH/MEDIUM | P2 |
| 27 | Instituto Águia | `aguia_open` | https://portal.institutoaguia.org.br/edital | https://portal.institutoaguia.org.br/edital/index/abertos | SERVER_RENDERED | 8 cards (4 andamento + 4 finalizados) | concursos/PSS; total UNKNOWN | 4 andamento; aberto sem cards | CONFIGURABLE_HTML + `/edital/ver/{id}` | MEDIUM | P3 |
| 28 | IUDS | `iuds_open` | https://www.iuds.org.br | https://portal.iuds.org.br/ (histórico) | HTML/PDF; TLS inconclusivo | detalhe histórico 77; universo atual UNKNOWN | cargos conforme editais | UNKNOWN | DEPRECATE_REVIEW_REQUIRED + KEEP_EMPTY só após validação; browser se voltar | LOW (Sol) | P5 |
| 29 | Reis & Reis | `reisesreis_open` | https://novo.reisauditores.com.br/concursos-em-andamento | https://novo.reisauditores.com.br/concursos-em-andamento | Astro + REST_API | item ID 70; paginação API | 1 | inscrição fechada; `situacaoEdital=PUBLICADO` não basta | REST_API Gestão Seleções; header `X-TenantID: reisauditores` | HIGH (Sol) | P0 |
| 30 | MS Concursos | `msconcursos_open` | https://www.msconcursos.com.br | https://www.msconcursos.com.br | UNKNOWN | 9 snapshot (2 abertas + 7 andamento) | 9 | 2 abertas | HTTP_HTML/CONFIGURABLE_HTML; href real em runtime | MEDIUM | P3 |
| 31 | FACET | `facet_open` | https://www.facetconcursos.com.br | https://concursos.facetconcursos.com.br/index/abertos/ | HTML/ProSeleta | 30 totais em 2 páginas | ≥30 | 1 aberta | CONFIGURABLE_HTML + paginação/detalhe | HIGH/MEDIUM | P2 |
| 32 | EDUCA PB | `educapb_open` | https://www.educapb.com.br | https://educapb.selecao.net.br/index/1/ | ProSeleta/HTML | 5 | 5 | 1 aberta | CONFIGURABLE_HTML | HIGH/MEDIUM | P2 |
| 33 | ADM&TEC | `admtec_open` | UNKNOWN | https://admtec.org.br/ | HTML/detalhe codificado | UNKNOWN | concursos/PSS | UNKNOWN | CONFIGURABLE_HTML/DEDICATED; confirmar índice antes do crawl | MEDIUM | P4 |
| 34 | CONTEMAX | `contemax_open` | https://www.contemaxconsultoria.com.br | UNKNOWN | UNKNOWN; health-check falho | UNKNOWN | UNKNOWN | UNKNOWN | KEEP_BLOCKED + DEPRECATE_REVIEW_REQUIRED; sem parser especulativo | LOW (Sol) | P5 |
| 35 | CPCon/UEPB | `cpcon_open` | UNKNOWN | https://cpcon.uepb.edu.br | HTML/WordPress legado | muitos por ano; total UNKNOWN | concursos/PSS | UNKNOWN | CONFIGURABLE/DEDICATED; legado + WP; filtro | MEDIUM | P4 |
| 36 | FUNVAPI | `funvapi_open` | UNKNOWN | https://www.funvapi.com.br/ | WordPress/PDF | ≥5 blocos | concursos e seleção de educação | UNKNOWN | CONFIGURABLE_HTML + archives/PDF; REST só após confirmação | MEDIUM | P3 |
| 37 | CONSEP | `consep_open` | UNKNOWN | https://www.consep-pi.com.br/concursos | HTML/PDF | 1 andamento + 8 encerrados; abertos empty | testes/PSS/concurso | 1 em andamento | CONFIGURABLE_HTML por status + detalhe/PDF | HIGH | P3 |
| 38 | Instituto Consulplan (Azure legado) | `institutoconsulplan_open` | https://institutoconsulplan.azurewebsites.net/Concursos | UNKNOWN/host offline | Azure parado/alias legado | 403 Web App stopped; cards indexados antigos não valem | UNKNOWN | UNKNOWN | DEPRECATE_REVIEW_REQUIRED; alias bloqueado, dedup com 07 | HIGH (Sol) | P6 |
| 39 | Instituto Avalia | `avalia_open` | https://www2.avalia.org.br/concursos.jsp | https://www2.avalia.org.br/concursos.jsp | HTML/detalhe | dezenas; total UNKNOWN | concursos/empregos/estágio; filtrar acadêmico | ≥2 abertas observadas | DEDICATED/CONFIGURABLE + `concurso.jsp?id=` | HIGH/MEDIUM | P2 |
| 40 | UFU/DIRPS | `ufu_selection` | https://www.portalselecao.ufu.br/servicos/Edital/listar/concursos | https://www.portalselecao.ufu.br/servicos/Edital/listar/concursos | SERVER_RENDERED/HTML | ≥11 atuais; total UNKNOWN | ≥11 atuais + histórico | 11 atuais; não somar categoria | CONFIGURABLE/DEDICATED HTML + filtro DIRPS + cronograma | HIGH | P0 |
| 41 | IDGRAN | `idgran_open` | https://idgran.com.br | UNKNOWN | UNKNOWN/erro interno | UNKNOWN | UNKNOWN | UNKNOWN | KEEP_BLOCKED + DEPRECATE_REVIEW_REQUIRED | LOW | P5 |
| 42 | Quadrix | `quadrix_open` | https://quadrix.org.br/index/abertos/ | https://quadrix.org.br/index/abertos/ | HTML/HTTP | UNKNOWN | UNKNOWN | UNKNOWN | CONFIGURABLE_HTML + detalhes/CDN `selecao.net.br` | MEDIUM | P3 |
| 43 | Gualimp | `gualimp_open` | https://www.gualimp.com.br | https://www.gualimp.com.br/concursos/ | HTML + detalhe dynamic JS | UNKNOWN | UNKNOWN | UNKNOWN | CONFIGURABLE_HTML; browser/XHR só após observar | MEDIUM | P3 |
| 44 | Verbena/UFG | `verbena_selection` | https://institutoverbena.ufg.br | https://institutoverbena.ufg.br | UFG HTML + possível JS | UNKNOWN | UNKNOWN | UNKNOWN | CONFIGURABLE/DEDICATED após mapear CMS/candidato | MEDIUM | P3 |
| 45 | IDIB | `idib_open` | https://idib.org.br | https://idib.org.br + https://concurso.idib.org.br/SITE/Concursos.aspx | ASP.NET WebForms/HTML | UNKNOWN | UNKNOWN | UNKNOWN | CONFIGURABLE_HTML; preservar aviso JS | MEDIUM | P2 |
| 46 | JCM | `jcm_open` | https://eventos.concursosjcm.com.br | https://concursosjcm.com.br/ | HTML/ProSeleta | UNKNOWN | UNKNOWN | UNKNOWN | CONFIGURABLE_HTML; usar links reais/CDN | MEDIUM | P2 |
| 47 | Elo Assessoria | `elo_open` | https://eloassessoriaeservicos.com.br/concursos | https://novo.eloassessoriaeservicos.com.br/concursos | Astro + REST_API | 7 correntes; 3 abertas, 3 em breve, 1 encerrado; próximo 3; concluído 123 | 7 correntes após filtro | 3 `inscricoesAbertas=true` | REST_API Gestão Seleções; header `X-TenantID: eloassessoria`; cargos/anexos | HIGH (Sol) | P0 |
| 48 | Apta | `apta_open` | https://www.aptaconcursos.com.br | https://www.aptaconcursos.com.br | DYNAMIC_JS/browser compatibility | UNKNOWN | UNKNOWN | UNKNOWN | KEEP_BLOCKED; browser real para validar listagem | LOW/MEDIUM | P5 |
| 49 | Legalle | `legalle_open` | https://portal.editais.legalleconcursos.com.br/edital | https://portal.editais.legalleconcursos.com.br/edital | HTML/S3 PDF | UNKNOWN | UNKNOWN | UNKNOWN | CONFIGURABLE_HTML + `/edital/ver/{id}` | MEDIUM | P2 |
| 50 | RBO | `rbo_open` | https://rboconcursos.selecao.net.br/index/abertos/ | https://rboconcursos.selecao.net.br/index/abertos/ | ProSeleta/HTML | UNKNOWN | UNKNOWN | UNKNOWN | CONFIGURABLE_HTML tenant + `/informacoes/{id}/` | MEDIUM | P2 |
| 51 | SHDias | `shdias_open` | https://www.shdias.com.br/concursos/ | https://www.shdias.com.br/concurso | DYNAMIC_JS/browser compatibility | UNKNOWN; indexação mostra cards | UNKNOWN | UNKNOWN | KEEP_BLOCKED + navegador real/live retest | LOW/MEDIUM | P5 |
| 52 | Zambini | `zambini_open` | https://www.zambini.org.br/portal/concursos | https://www.zambini.org.br/portal/concursos | STATIC_HTML | vazio atual + detalhe histórico | UNKNOWN | 0 atual no recorte | CONFIGURABLE_HTML + KEEP_EMPTY | MEDIUM | P7 |
| 53 | Nosso Rumo | `nossorumo_open` | https://www.nossorumo.org.br | https://nossorumo.org.br/ | SERVER_RENDERED_HTML/legado | vários cartões; total UNKNOWN | concursos/PSS | andamento com datas futuras; total UNKNOWN | CONFIGURABLE_HTML/HTTP_HTML; redirect sem www | MEDIUM | P3 |
| 54 | Avança SP | `avancasp_open` | https://avancasp.selecao.net.br/index/abertos/ | https://avancasp.selecao.net.br/index/abertos/ | ProSeleta/HTML | 7 abertos; 37 andamento | 6/7 abertos | 6 de pessoal abertas | CONFIGURABLE_HTML compartilhado ProSeleta; detalhe/anexos | HIGH | P0 |
| 55 | Instituto Mais | `institutomais_open` | https://www.institutomais.org.br/Concursos/ConcursosAbertos | https://www.institutomais.org.br/Concursos/ConcursosAbertos | HTML/PDF | 4 abertos + 14 andamento | relevante | 4 abertas | CONFIGURABLE_HTML; seguir detalhe/PDF | HIGH | P0 |
| 56 | Publiconsult | `publiconsult_open` | https://publiconsult.com.br/Concurso/Index | https://publiconsult.com.br/Concurso/Index | HTML | ≥17 cards | concursos/PSS; total UNKNOWN | UNKNOWN | CONFIGURABLE_HTML; status por legenda/datas, preservar UNKNOWN | MEDIUM | P3 |
| 57 | KLC | `klc_open` | https://www.klcconcursos.com.br | https://www.klcconcursos.com.br | HTML legado | abertos empty; >100 históricos em andamento | concursos/PSS | UNKNOWN | HTTP_HTML/CONFIGURABLE_HTML; KEEP_EMPTY sem promover históricos | MEDIUM | P7 |
| 58 | Sigma | `sigma_open` | https://concursos.sigmaassessoria.com.br | https://concursos.sigmaassessoria.com.br | ProSeleta/HTML | 1 | 1 contratação | em andamento, prazo já encerrado | CONFIGURABLE_HTML tenant; fixture fechado | HIGH | P1 |
| 59 | W2 | `w2_open` | https://www.w2consultores.com.br/index/todos/ | https://www.w2consultores.com.br/index/todos/ | provável HTML legado/charset | 247 páginas indexadas | processos/concursos; total filtrado UNKNOWN | UNKNOWN | CONFIGURABLE_HTML + charset fallback; KEEP_BLOCKED se falhar | LOW | P5 |
| 60 | Fênix | `fenix_open` | https://portal.fenix.selecao.site/edital | https://portal.fenix.selecao.site/edital | Gestor Editais/HTML | aberto empty; 2 andamento; snapshot diverge | 2 relevantes | estado conflitante; active UNKNOWN | CONFIGURABLE_HTML; registrar timestamp e conflito, não inferir | MEDIUM | P5 |
| 61 | Oppus | `oppus_open` | https://www.oppusconcursos.com.br | UNKNOWN | domínio indisponível | nenhum atual; PDFs antigos | histórico relevante, atual UNKNOWN | UNKNOWN | KEEP_BLOCKED + DEPRECATE_REVIEW_REQUIRED | LOW | P6 |
| 62 | Instituto Legatus | `legatus_open` | https://www.legatus.org.br | https://www.legatus.org.br | HTML/PDF | ≥10 cards | concursos municipais | há períodos correntes/futuros; total UNKNOWN | CONFIGURABLE_HTML + detalhes/tabelas | HIGH | P0 |
| 63 | FEPESE | `fepese_open` | https://fepese.org.br/concursos/ | https://fepese.org.br/concursos/ | HTML + tenants | 13 projetos 2026 | 13 pessoal | status individual UNKNOWN | HYBRID/CONFIGURABLE_HTML por tenant + publicações | HIGH | P3 |
| 64 | FUNCERN | `funcern_selection` | https://funcern.br/concursos/ | https://funcern.br/concursos/ | WordPress-like HTML/PDF | 3 abertos + 2 andamento + 121 resultados | ≥2 abertos de pessoal; filtrar bolsas | ≥2 abertos | CONFIGURABLE_HTML `?page=N` + filtro institucional/PDF | HIGH | P0 |
| 65 | FAPEMIG | `fapemig_selection` | https://fapemig.br/pt/editais/ | https://fapemig.br/oportunidades/chamadas-e-editais | CMS dinâmico/HTML | 190 chamadas (4 abertas etc.) | 0 pessoal observado | 0 pessoal; fomento ativo | CONFIGURABLE_HTML + KEEP_EMPTY; filtro de fomento | HIGH/MEDIUM | P7 |
| 66 | FAPES (ES) | `fapes_selection` | https://fapes.es.gov.br/editais | https://fapes.es.gov.br/editais | SERVER_RENDERED/Orchard | 3 carreira científica + demais | 0 emprego confirmado | 0 pessoal | CONFIGURABLE_HTML + filtro institucional + KEEP_EMPTY | HIGH | P7 |
| 67 | FAPESQ (PB) | `fapesq_selection` | https://fapesq.rpp.br/editais/ | https://fapesq.rpp.br/editais/editais-2026 | SERVER_RENDERED/Plone-like/PDF | coleção 2026 paginada | vários editais de equipe/pessoal; total UNKNOWN | UNKNOWN | CONFIGURABLE_HTML `b_start:int` + HYBRID/PDF + filtro | MEDIUM | P3 |
| 68 | Fundação Uniselva | `uniselva_selection` | https://inscricao.fundacaouniselva.org.br/selecoes | https://web.fundacaouniselva.org.br/frmSelecoes.aspx | ASP.NET WebForms | dezenas 2025–26 | múltiplas contratações/estágios | UNKNOWN | CONFIGURABLE_HTML no domínio web; browser só se interface necessária | MEDIUM | P3 |
| 69 | Fundação FAFIPA | `fafipa_open` | https://concursos.fundacaofafipa.org.br/ | https://fafipa.selecao.net.br/ | ProSeleta/HTML | 42 em andamento | 42 | 42 em andamento (inscrição individual deve ser verificada) | CONFIGURABLE_HTML compartilhado `selecao.net.br` | HIGH | P2 |
| 70 | IESES | `ieses_open` | https://ieses.org/projetos | https://www.concursos.ieses.org/ | SPA/load-more/tenants | ≥12 projetos | concursos/PSS; total UNKNOWN | UNKNOWN | PLAYWRIGHT/HYBRID; observar XHR antes de usar API | MEDIUM | P3 |
| 71 | FUNPEC | `funpec_selection` | https://funpec.br/processos-seletivos/ | https://funpec.br/processos-seletivos/ | HTML/PDF | 3 novos + 6 andamento + 77 encerrados | pessoal | 6 andamento; 3 novos potencialmente ativos | CONFIGURABLE_HTML + estados/paginação + filtro | HIGH | P0 |
| 72 | FADE-UFPE | `fade_selection` | https://fade.org.br | https://fade.org.br/category/editais/ | WordPress/HTML/PDF | ≥67 páginas; 10 por página | estágio/empregos; excluir bolsa pura | UNKNOWN; vários abertos/andamento | CONFIGURABLE_HTML; WordPress API somente se confirmada | HIGH | P0 |
| 73 | FAPEX | `fapex_selection` | https://master.fapex.org.br/portalrh/ | https://fapex.org.br/Fapex/Site/Principal/Edital/index + https://fapex.pandape.infojobs.com.br/ | HTML + plataforma externa | editais históricos + 50 vagas Pandapé | contratação/estágio + vagas | 50 vagas Pandapé | HYBRID/DEDICATED; portalrh KEEP_BLOCKED (login) | MEDIUM | P0 |
| 74 | FATEC Santa Maria | `fatec_selection` | https://www.fatecsm.org.br/processos-seletivos/ | https://www.fatecsm.org.br/processos-seletivos/ | WordPress/HTML/PDF | 10 (3 andamento + 7 encerrados) | 10 | 3 | CONFIGURABLE_HTML + PDF | HIGH | P0 |
| 75 | FAPED | `faped_selection` | https://faped.org.br | https://faped.org.br/editais | HTML/PDF | muitos editais; 1 filtro celetista | 1 Analista em Sanidade Vegetal | 0; encerrado | CONFIGURABLE_HTML + KEEP_EMPTY + filtro | MEDIUM | P1 |
| 76 | FAPESE | `fapese_selection` | https://fapese.org.br | https://www.fapese.org.br/programa-primeiro-emprego/ | WordPress/HTML/PDF | 16 publicações | professores/instrutores; excluir beneficiários | 0 confirmados | CONFIGURABLE_HTML + filtro + KEEP_EMPTY | HIGH | P1 |
| 77 | FAPEPI | `fapepi_selection` | https://www.fapepi.pi.gov.br/editais-fapepi/ | https://www.fapepi.pi.gov.br/editais-fapepi/ | WordPress/HTML/PDF | ≥9 editais 2026 | 0 pessoal confirmado | 0 | CONFIGURABLE_HTML + KEEP_EMPTY + filtro | HIGH | P7 |
| 78 | FAPEMA | `fapema_selection` | https://www.fapema.br/inicio/ | https://www.fapema.br/editais/ | WordPress/HTML/PDF | UNKNOWN | 0 pessoal atual; bolsas/fomento | 0 pessoal | CONFIGURABLE_HTML + filtro + KEEP_EMPTY | HIGH/MEDIUM | P7 |
| 79 | FAPECE | `fapece_selection` | https://fapece.ce.gov.br | UNKNOWN | identidade incompatível; host não resolve | UNKNOWN | UNKNOWN | UNKNOWN | DEPRECATE_REVIEW_REQUIRED; confirmar entidade antes de crawler | HIGH para conflito/LOW para alvo | P6 |
| 80 | FAPERN | `fapern_selection` | https://fapern.rn.gov.br | https://fapern.rn.gov.br | 503/bloqueado | UNKNOWN | 0 confirmado; bolsa conhecida fora | UNKNOWN | KEEP_BLOCKED/HYBRID após retorno; sem bypass | MEDIUM/LOW | P5 |
| 81 | FAPEAL / evento CEBRASPE | `fapeal_selection` | https://fapeal.br | https://www.fapeal.br/ + https://www.cebraspe.org.br/concursos/FAPEAL_26 | CEBRASPE REST_API + portal FAPEAL | ≥1 (`FAPEAL_26`, ID 3342; 10 vagas; 23 edital/22 gabarito) | ≥1 seleção de pessoal | 0 inscrições abertas; processo em andamento com prazo fechado | P0 false-empty: discovery CEBRASPE/API; detalhe e CDN, não só arquivo FAPEAL | HIGH (Sol) | P0 |
| 82 | FACEPE | `facepe_selection` | https://www.facepe.br | https://www.facepe.br/ + /editais/todos/ | WordPress/HTML/PDF | muitos; total UNKNOWN | ≥1 PSS contratação temporária histórico | 0 atual | HYBRID HTML+PDF + KEEP_EMPTY; fixture seleção simplificada | HIGH/MEDIUM | P1 |
| 83 | FAPESB | `fapesb_selection` | https://www.fapesb.ba.gov.br/category/edital/ | https://www.fapesb.ba.gov.br/category/edital/ + https://selecao.ba.gov.br/ | WordPress + portal REDA | UNKNOWN | 1 REDA 001/2026, 22 vagas | 0 em 30/08; fechado | HYBRID índice/PDF/portal; fixture REDA; não autenticar | HIGH | P1 |
| 84 | FAPERJ | `faperj_selection` | https://faperj.br | https://faperj.br/?id=28.5.7 | HTML/CMS legado | dezenas chamadas; total UNKNOWN | 0 atual; bolsas/auxílios | 0 contratação | CONFIGURABLE_HTML + KEEP_EMPTY; HYBRID só se pessoal em PDF | MEDIUM | P7 |
| 85 | FAPESP | `fapesp_selection` | https://fapesp.br/oportunidades/ | https://fapesp.br/oportunidades/ | SERVER_RENDERED/HTML | 109 oportunidades | 0 emprego/concurso (bolsas) | 0 escopo | KEEP_EMPTY/DEPRECATE_REVIEW_REQUIRED; não contar 109 como concurso | HIGH | P7 |
| 86 | FAPPR/Araucária | `fappr_selection` | https://fappr.pr.gov.br/Pagina/Processos-Seletivos | https://www.fappr.pr.gov.br/Pagina/Processos-Seletivos | HTML/CMS/PDF | UNKNOWN; PS 01–04/2026 | ≥4 estágios + CLT fixture | 0 em 30/08; prazos passados | HYBRID HTML+atos/PDF; fixtures estágio/CLT; excluir NAPI/bolsa | HIGH/MEDIUM | P1 |
| 87 | FAPESC | `fapesc_selection` | https://fapesc.sc.gov.br | https://fapesc.sc.gov.br/chamadas-abertas/ | WordPress/HTML/PDF | UNKNOWN chamadas 2026 | 0 emprego; bolsas fora | 0 escopo | CONFIGURABLE_HTML + KEEP_EMPTY + filtro; sem plataforma para discovery | HIGH/MEDIUM | P7 |
| 88 | FAPERGS | `fapergs_selection` | https://fapergs.rs.gov.br/selecao-2025 | https://fapergs.rs.gov.br/selecao-2025 | PROCERGS/HTML/PDF | 1 PSS pessoal | 1 | 0; encerrado | HYBRID detalhe+anexos; fixture 5 agentes e status ENCERRADO | HIGH | P1 |
| 89 | FUNDECT | `fundect_selection` | https://www.fundect.ms.gov.br/informativos/consultas/ | https://www.fundect.ms.gov.br/informativos/consultas/ | WordPress/HTML/PDF/DOE | tabela 2024–26; total UNKNOWN | 1 Diretor-Presidente | 0; nomeação 16/12/2025 | HYBRID tabela+detalhe/PDF/DOE; excluir chamadas de projeto/bolsa | HIGH/MEDIUM | P1 |

## Executive Summary preliminar

Critério: contar fontes/linhas, não itens individuais, e contar somente quando a própria linha da matriz traz evidência explícita. As categorias se sobrepõem; portanto não somar entre si. “Ativa” abaixo significa inscrição aberta ou estado atual compatível com oportunidade, enquanto “em andamento” pode ter inscrição fechada.

| categoria | preliminar | regra de contagem |
|---|---:|---|
| fontes com estratégia definida (não `UNKNOWN`) | 89 | toda linha recebeu estratégia de suporte; `UNKNOWN` permanece em campos de evidência, não é convertido em falha |
| fontes com pelo menos uma seleção de pessoal relevante observada | 49 | `relevant` explícito ou ≥/pelo menos; inclui históricos e fontes com active UNKNOWN |
| fontes com inscrição aberta/ativa confirmada | 23 | `active` explicitamente positivo ou detalhe/API indicando inscrição aberta; não inclui apenas “em andamento” |
| fontes com relevant histórico/fechado e fixture útil | 19 | processo de pessoal explicitamente encerrado ou com prazo passado, preservado para regressão |
| fontes com empty/out-of-scope legítimo | 9 | 0 de pessoal confirmado e evidência de fomento/bolsa/empty; não contar shell bloqueado como vazio |
| fontes bloqueadas, offline ou identidade incerta | 13 | WAF/TLS/503/indisponibilidade/identidade sem origem confiável; inclui aliases legados |
| fontes que exigem filtro institucional/acadêmico | 30 | batch ou spot-check exige separar concurso/emprego de bolsa, fomento, vestibular, certificação ou projeto |
| fontes com API/endpoint confirmado no spot-check | 4 | CEBRASPE, CESGRANRIO, Reis & Reis e Elo; FAPEAL usa o endpoint CEBRASPE como discovery alternativo |
| itens/API explicitamente observados em destaque | 4 | CEBRASPE: 496 eventos; CESGRANRIO: 32 detalhes + 1 categoria aberta; Elo: 7 correntes/123 concluídos; FAPEAL: ID 3342 |

Essas contagens são preliminares e não substituem o recorte do crawler: linhas com “≥”, “pelo menos”, snapshots ou categorias sobrepostas não autorizam extrapolar totais de itens. A mudança da fonte 81 deve ser contabilizada como correção de falso empty, não como nova fonte.

## Shared Platform Opportunities

| oportunidade | fontes | limite/decisão |
|---|---|---|
| Cliente REST Gestão Seleções com paginação Spring e header por tenant | 29 Reis & Reis; 47 Elo | compartilhar paginação/serialização; manter `X-TenantID` e regras por tenant; usar `situacaoInscricao`/`inscricoesAbertas` |
| Cliente ProSeleta/`selecao.net.br` configurável | 15, 18, 19, 22, 24, 26, 31, 32, 46, 50, 54, 69 | compartilhar parser de cards/detalhes/PDF, mas separar tenants, URLs e filtros; não presumir API comum |
| Gestor Editais HTML | 2 IDECAN; 6 IBADE; 60 Fênix | conector HTML comum possível; validar diferenças de tenant e preservar empty explícito |
| WordPress/editorial + PDF | 36, 65–66, 72, 75–78, 81–85, 87, 89 | HTML para título/status/link; PDF para cargo/vagas/remuneração; filtro institucional obrigatório; não inventar REST |
| CEBRASPE REST/API + CDN | 11 e discovery alternativo de 81 | usar endpoints confirmados; detalhe prevalece ao resumo; FAPEAL não deve ficar presa ao arquivo de fomento |
| Catálogo WP + API Angular | 12 CESGRANRIO | API é primária; WordPress valida categorias/fallback; tokens SAS não são identidade |
| HTML server-rendered + PDF | 1, 4, 5, 9, 10, 13, 17, 20, 27, 30, 33, 35, 37, 39–45, 49, 53, 56, 62–64, 68, 70, 71, 74, 76, 86, 88 | usar configuração por fonte; estado só por texto/data oficial; seguir hrefs reais |
| Sistema externo de inscrição/submissão | 15, 22, 26, 47, 65, 67, 68, 73, 76, 81–84, 89 | armazenar link, não autenticar nem usar para discovery; não contar submissão como vaga |

Não há evidência de API REST/XHR pública estável comum a todos os tenants ProSeleta ou aos portais de FAPs. Qualquer promoção de `WORDPRESS_API`, `_api`, XHR ou endpoint deve depender de chamada observada em runtime.

## Tabela de implementação (89 linhas)

| # | problema | estratégia | URL/endpoint | mudança recomendada | testes | live retest |
|---:|---|---|---|---|---|---|
| 1 | aberto empty explícito | CONFIGURABLE_HTML | `/index/abertos/` | manter empty e separar andamento/finalizados | empty + paginação 339 | confirmar texto e contagem |
| 2 | estado em seções Gestor Editais | CONFIGURABLE_HTML | `/edital/index/abertos`, `/edital/ver/{id}` | parser por seção e detalhe | `/ver/24`, arquivo ausente | repetir estados |
| 3 | shell sem cards | PLAYWRIGHT/HYBRID | `/concursos/status/inscricoes-abertas` | browser para cards; não false-empty | SAEB/CESAMA | verificar cards |
| 4 | HTML com ícones de status | CONFIGURABLE_HTML | `index.php?menu=concursos` | mapear alt/texto e tenant externo | 9 abertas + detalhe | repetir legenda |
| 5 | tabelas/PDF e suspensão | DEDICATED_CONNECTOR | `ibam-concursos.org.br` | extrair tabela e PDFs; respeitar suspensão | 4 abertas + Lages | datas/status |
| 6 | empty de inscrição, histórico | CONFIGURABLE_HTML | `/edital`, `/edital/ver/{id}` | separar EM INSCRIÇÃO de andamento | empty + `/ver/126` | verificar item |
| 7 | Cloudflare WAF | PLAYWRIGHT/HYBRID | `consulplan.net` | não ingerir shell como empty | desafio/WAF | browser real |
| 8 | TLS/acesso não reproduzível | KEEP_BLOCKED | `/concursos/` | health-check antes de parser | TLS/browser | repetir acesso |
| 9 | andamento mistura modalidades | DEDICATED/CONFIGURABLE | `concursoAndamento.html` | filtro institucional; status por detalhe | vestibular/certificação | comparar 30 |
| 10 | lista mistura exames | CONFIGURABLE_HTML | `/concursos` | filtro de concurso/emprego | CPNU2 + ruídos | validar item |
| 11 | resumo API contradiz detalhe | REST_API | `apis.cebraspe.org.br/cebraspe/eventos/...` | API por fase; detalhe prevalece | 496, Pontaporã, CDN | 200 e flags |
| 12 | WP e Angular paralelos | REST_API | `/api/PortalEventos`, `/api/PortalEventos/{id}` | API paginada + grupos/conteúdos; WP fallback | evento 22 + SAS | paginação/estado |
| 13 | cards e estados incompletos | CONFIGURABLE_HTML | `idcap.org.br` | seguir cards/detalhe e filtrar | 22 + ≥2 abertos | recontar |
| 14 | JSP sem cards | HYBRID + KEEP_EMPTY | `index.jsp`, download REST | não promover PDF recente a ativo | PDF 21269 + abas | HTTP/browser |
| 15 | catálogo resumido e tenant | CONFIGURABLE_HTML | `fundep.selecao.net.br/informacoes/{id}` | seguir “Ver todos”; PDF para campos | DMAE 63/EMATER 71 | datas |
| 16 | SharePoint/biblioteca | HTML/PDF; `_api` só observado | `fumarc.com.br/Documentos...` | parser de biblioteca; sem endpoint inventado | Ubá 08/2025 | PDF acessível |
| 17 | total/paginação não expostos | CONFIGURABLE_HTML + PDF | `/edital/ver/{id}` | seguir IDs e anexos | IDs 122/124/127/135 | repetir |
| 18 | dois domínios/universos | CONFIGURABLE_HTML | dois tenants ProSeleta | configurar ambos e deduplicar | Saltinho/Tapejara | comparar IDs |
| 19 | uma especialização fora do escopo | CONFIGURABLE_HTML + filtro | `access.selecao.net.br` | excluir UFAC acadêmico | 14 pessoais + UFAC | status |
| 20 | catálogo paginado | CONFIGURABLE_HTML | `exameconsultores.../index/1/` | percorrer estados e query params | catálogo 158 + Santana | prazo |
| 21 | “andamento” legado | KEEP_EMPTY + histórico | `/concursos/andamento` | não marcar ativo sem data | abertos empty/CFS | health-check |
| 22 | redirect e ProSeleta | CONFIGURABLE_HTML | `/informacoes/2867/` | canonicalizar homepage; seguir detalhe | Ibiúna 33 vagas | período |
| 23 | índice ausente/status por PDF | DEDICATED/HYBRID | `/concurso/{id}` | discovery por links; excluir ID 195 | Sarandi 182 | detalhe |
| 24 | ProSeleta com PSS | CONFIGURABLE_HTML | `/informacoes/2602/` | extrair detalhe/CDN | 5 futuras | período |
| 25 | identidade errada no batch | DEPRECATE_REVIEW_REQUIRED | `UNKNOWN` | não substituir pela Prefeitura; preservar ID | DNS/SOA sem A | confirmar sucessor primário |
| 26 | domínio migrado ProSeleta | CONFIGURABLE_HTML + filtro | `/informacoes/28/` | usar URL atual confirmada | 2 pessoais + vestibular | datas |
| 27 | “em andamento” não é aberto | CONFIGURABLE_HTML | `/edital/ver/{id}` | separar seção e status | 42 finalizado | recontagem |
| 28 | TLS/portal histórico | KEEP_BLOCKED | `portal.iuds.org.br` | não concluir vazio | detalhe 77/browser | retestar |
| 29 | engine REST confirmada | REST_API | `api.gestaoselecoes.com.br/api/editais` | header tenant + flags de inscrição | ID 70/paginação | API 200 |
| 30 | snapshot sem href | HTTP_HTML | `msconcursos.com.br` | coletar href em runtime | 2 abertas/7 andamento | links |
| 31 | duas páginas e detalhe | CONFIGURABLE_HTML | `/index/todos/`, `/informacoes/{id}/` | seguir paginação real | 30 total/Floresta | páginas 1–2 |
| 32 | canonical ProSeleta | CONFIGURABLE_HTML | `/index/1/`, `/informacoes/6/` | mapear “Inscrições Abertas” | Cuité | status |
| 33 | índice/ID codificado | CONFIGURABLE/DEDICATED | `admtec.org.br` | confirmar discovery antes de crawl | rota MTEz/MTIx | hrefs |
| 34 | health-check falho | KEEP_BLOCKED | `contemaxconsultoria.com.br` | sem parser especulativo | HTTP/HTTPS | retestar |
| 35 | legado + novo WP | CONFIGURABLE/DEDICATED | `cpcon.uepb.edu.br` | unir só com dedup e filtro | ano 2020/21 | catálogo |
| 36 | posts podem usar REST, não confirmado | CONFIGURABLE_HTML | `/category/concursos/` | archives + PDFs | 5 blocos | status |
| 37 | aberto empty + andamento | CONFIGURABLE_HTML | `/concursos`, detalhe | manter 1 andamento distinto | edital 002/2026 | status |
| 38 | Azure parado/alias | DEPRECATE_REVIEW_REQUIRED | Azure `/Concursos` | tratar como legado bloqueado; dedup com 07 | 403 stopped | browser principal |
| 39 | filtro acadêmico | DEDICATED/CONFIGURABLE | `concurso.jsp?id=597` | usar detalhe para publicações | EPAGRI/UESB | inscrições |
| 40 | mistura produtos DIRPS | HTML + filtro | `/servicos/Edital/cronograma/{id}` | aceitar só pessoal; não somar visões | 11 atuais | 144/2026 |
| 41 | erro interno | KEEP_BLOCKED | `idgran.com.br` | não fabricar URL correta | HTTP/browser | health-check |
| 42 | total unknown/ProSeleta CDN | CONFIGURABLE_HTML | `/index/abertos/` | parser por href e detalhe | empty/itens | HTTP |
| 43 | detalhe JS/XHR | CONFIGURABLE + browser | `/concursos/` | observar chamada antes de API | card/detalhe | DOM |
| 44 | portal UFG/CMS | DEDICATED/CONFIGURABLE | `institutoverbena.ufg.br` | mapear candidato/lista | rotas oficiais | browser |
| 45 | WebForms | CONFIGURABLE_HTML | `concurso.idib.org.br/SITE/Concursos.aspx` | parsear tabelas apesar de aviso JS | links/estado | HTTP |
| 46 | host/ProSeleta migrado | CONFIGURABLE_HTML | `concursosjcm.com.br` | usar domínio atual e anexos reais | href/CDN | HTTP |
| 47 | REST tenant Elo | REST_API | `/api/editais`, `/cargos`, `/anexos` | cliente comum com Reis; flags de inscrição | ID 134 + futuro/encerrado | API 200 |
| 48 | tela incompatibilidade | KEEP_BLOCKED | `aptaconcursos.com.br` | browser real somente após validação | compatibilidade | live browser |
| 49 | links S3/detalhe | CONFIGURABLE_HTML | `/edital/ver/{id}` | seguir hrefs, não assumir consulta única | anexos | HTTP |
| 50 | tenant ProSeleta | CONFIGURABLE_HTML | `/informacoes/{id}/` | parser configurável | item/detail | HTTP |
| 51 | incompatibilidade JS | KEEP_BLOCKED | `/concurso` | usar indexação só como pista | browser real | live |
| 52 | vazio atual/histórico | KEEP_EMPTY | `/portal/concursos` | não promover histórico | empty + detalhe | confirmar |
| 53 | cartões sem detalhe público | CONFIGURABLE_HTML | `nossorumo.org.br/` | usar home/status; não rota CPF | Mairiporã | redirect |
| 54 | 7 abertos, 1 vestibular | CONFIGURABLE_HTML | `/index/abertos/`, `/informacoes/251/` | excluir UNIREGISTRAL; 6 pessoais | CRECI | período |
| 55 | 4 abertos + andamento | CONFIGURABLE_HTML | `/Concursos/ConcursosAbertos` | seguir detalhes/PDF | 4 abertas | retestar |
| 56 | datas/status misturados | CONFIGURABLE_HTML | `/Concurso/Index` | manter active UNKNOWN sem status | Sarapuí | revalidar |
| 57 | abertos empty, históricos | KEEP_EMPTY + HTML | `klcconcursos.com.br` | separar histórico; não usar datas antigas | empty | reteste |
| 58 | processo já expirado | CONFIGURABLE_HTML | `sigmaassessoria.com.br` | fixture fechado; não active | Itaju 001.2026 | status |
| 59 | charset/decoding | CONFIGURABLE + charset | `/index/todos/` | testar UTF-8/Windows-1252; não inventar Lambari | page 7/247 | HTTP |
| 60 | snapshots conflitantes | CONFIGURABLE_HTML | `/edital` | timestamp/status textual; active UNKNOWN | 2 andamento + empty | comparar |
| 61 | domínio indisponível | KEEP_BLOCKED | `oppusconcursos.com.br` | somente evidência histórica | no current item | health-check |
| 62 | detalhe rich/tabelas | CONFIGURABLE_HTML | `/concursos/160/...` | extrair vagas/PCD/taxa | Tanque do Piauí | período |
| 63 | tenants por projeto | HYBRID | `fepese.org.br/concursos/` | visitar cada tenant; status UNKNOWN | 13 projetos | reteste |
| 64 | 121 resultados + bolsas | CONFIGURABLE_HTML | `funcern.br/concursos/` | paginar; excluir SEMURB/ProITEC | 2 abertos | páginas |
| 65 | FAPEMIG é fomento | KEEP_EMPTY + filtro | `/oportunidades/chamadas-e-editais` | não converter 4 abertas em emprego | 190/4/0 | reteste |
| 66 | FAPES só bolsas/fomento | KEEP_EMPTY + filtro | `/editais` | preservar 0 pessoal | 3 carreira científica | categorias |
| 67 | itens de equipe/pessoal, estado incerto | HYBRID + PDF | `/editais/editais-2026?b_start:int=N` | paginar offsets; status por cronograma | editais 58/57/55 | todos offsets |
| 68 | listagem web separada da inscrição | CONFIGURABLE_HTML | `web.../frmSelecoes.aspx` | usar web para discovery; não login | 017/2026 | tabela |
| 69 | 42 em andamento não necessariamente abertos | CONFIGURABLE_HTML | `fafipa.selecao.net.br` | validar período item a item | 42 | datas |
| 70 | SPA/load-more | PLAYWRIGHT/HYBRID | `www.concursos.ieses.org` | observar XHR; não inventar API | 12 tenants | botão |
| 71 | 3 novos + 6 andamento + 77 fechado | CONFIGURABLE_HTML | `/processos-seletivos/` | separar estados e filtro pessoal | cuidador 12/2026 | cronograma |
| 72 | 67 páginas, bolsas misturadas | CONFIGURABLE_HTML | `/category/editais/` | paginar; excluir bolsa pura | estágio/DevOps | páginas 1–2 |
| 73 | portal RH exige login | HYBRID/DEDICATED | arquivo FAPEX + Pandapé | não usar `portalrh` para discovery | 50 vagas | URL pública |
| 74 | 3 andamento/7 encerrado | CONFIGURABLE_HTML | `/processos-seletivos/` | extrair PDF/status | 10 entradas | reteste |
| 75 | compras/oferta vs celetista | CONFIGURABLE + filtro | `/editais` | usar filtro celetista; manter fechado | Analista 001/2025 | filtro |
| 76 | emprego/função vs curso beneficiário | CONFIGURABLE + filtro | `/programa-primeiro-emprego/` | aceitar docentes; excluir beneficiário | Editais 02/06 | status |
| 77 | fomento/bolsas | KEEP_EMPTY + filtro | `/editais-fapepi/` | preservar 0 de pessoal | 9 editais | categorias |
| 78 | FMRB bolsa não é emprego | KEEP_EMPTY + filtro | `/editais/` | teste negativo FMRB 14/2026 | posts/PDF | reteste |
| 79 | identidade FAPECE incompatível | DEPRECATE_REVIEW_REQUIRED | `fapece.ce.gov.br` | confirmar entidade; sem crawler | DNS + fapece.com.br | revisão Sol |
| 80 | 503 | KEEP_BLOCKED | `fapern.rn.gov.br` | registrar bloqueio; não bypass | HTTP 503 | DOE/portal |
| 81 | falso empty corrigido | REST_API/P0 | `apis.cebraspe.org.br/cebraspe/eventos/FAPEAL_26` | ingerir ID 3342 como relevante fechado; discovery CEBRASPE | 10 vagas, flags, 23/22 docs | API + portal |
| 82 | seleção histórica em portal de bolsas | HYBRID + KEEP_EMPTY | `/editais/todos/`, PDF seleção | fixture PSS; excluir maioria fomento | PDF simplificada | filtros |
| 83 | REDA em portal externo | HYBRID | categoria + `selecao.ba.gov.br` | fixture 22 vagas; link sem autenticar | REDA 001/2026 | status |
| 84 | chamadas/bolsas | KEEP_EMPTY + filtro | `?id=28.5.7` | só promover pessoal com PDF | TCT negativo | categorias |
| 85 | 109 bolsas | KEEP_EMPTY | `/oportunidades/` | não contar 109 como concursos | oportunidade 9739 | reteste |
| 86 | estágio misturado com bolsas | HYBRID | `/Pagina/Processos-Seletivos` | fixtures PS 01–04 e CLT; excluir NAPI | status/atos | prazos |
| 87 | bolsas/chamadas abertas | KEEP_EMPTY + filtro | `/chamadas-abertas/` | não converter bolsas em vagas | FAPESC 49/2026/Ciasc 22/2026 | categorias |
| 88 | PSS encerrado com anexos | HYBRID | `/selecao-2025` | fixture 5 agentes; anexos não são itens | ENCERRADO | links |
| 89 | Diretor-Presidente fechado | HYBRID + filtro | `/informativos/consultas/` | separar cargo de chamadas de projeto | nomeação 16/12/2025 | anos/categorias |

## Correções/contradições a aplicar no texto individual

1. Fonte 07: substituir qualquer “empty/portal saudável” por WAF_BLOCKED; `www.consulplan.net` exige browser/Cloudflare e não deve ser tratado como lista vazia.
2. Fonte 38: corrigir para Azure parado (`403 Web App stopped`), alias/legado provável; não contar cards indexados antigos nem manter crawl duplicado com 07.
3. Fonte 11: trocar PLAYWRIGHT por REST_API; usar os endpoints CEBRASPE e o detalhe como autoridade de inscrição. Registrar a inconsistência resumo/detalhe de `isInscricaoAberta`.
4. Fonte 12: trocar conclusão de portal quebrado por WP + Angular funcional; usar `PortalEventos` paginado, conteúdos/grupos e fixture Transpetro 2026; não usar `dataFim` isoladamente.
5. Fonte 25: remover completamente a substituição pelo município de Leandro Ferreira; identidade da consultoria está DNS_INACTIVE/IDENTITY_UNCONFIRMED, sem URL sucessora.
6. Fonte 29: trocar HYBRID/Playwright por REST_API com `X-TenantID: reisauditores`; ID 70 está publicado, porém com inscrição encerrada.
7. Fonte 47: trocar PLAYWRIGHT/HYBRID por REST_API Gestão Seleções; usar `X-TenantID: eloassessoria`, cargos/anexos e flags de inscrição; categorias corrente/próximo/concluído se sobrepõem.
8. Fonte 81: corrigir `relevant=0/active=0` para `observed/relevant ≥1` por `FAPEAL_26`/ID 3342; inscrições estão fechadas, não abertas. Registrar P0 false-empty e discovery via CEBRASPE/API.
9. Fontes 02 e 06: não chamar o portal inteiro de vazio porque somente “EM INSCRIÇÃO” está explicitamente vazio; andamento/histórico existem.
10. Fontes 03, 08, 14, 21, 28, 34, 41, 48, 51, 59–61: não promover shell/bloqueio/timeout a empty; manter UNKNOWN ou KEEP_BLOCKED conforme matriz.
11. Fontes 54, 55, 62, 64, 69, 71–74: “em andamento” deve passar por cronograma/inscrição; não somar cards de estados sobrepostos.
12. Fontes 65–78 e 82–87: não converter “edital”, “processo seletivo” ou “vagas” de bolsa/fomento em contratação; preservar exemplos negativos e filtros.
13. Fontes 78, 81 e 83: links/arquivos oficiais podem ser de ecossistemas diferentes; guardar a origem e não substituir identidade sem prova.
14. Em toda fonte: não inventar seletor, endpoint, contagem, URL de detalhe ou paginação; manter `UNKNOWN`, registrar ambiguidade e exigir fixture + live retest em `America/Sao_Paulo`.

## Ambiguidades para revisão do Sol

- O significado operacional de prioridade entre P2/P3/P4 não foi explicitado em um anexo separado; a distribuição acima é uma proposta conservadora, mantendo P0/P1/P5/P6/P7 alinhados às notas do BATCH 07.
- A contagem do Executive Summary é por fonte e usa evidência mínima (“≥” conta a linha); não é soma do crawler de 99 fontes nem contagem de itens deduplicados.
- As fontes 40–65 têm URLs iniciais/canônicas variáveis entre inventário e batches; a matriz prioriza a URL de pesquisa do batch e marca `UNKNOWN` quando não houve confirmação explícita.
- A fonte 81 foi atualizada por correção adicional do Sol após a leitura do snapshot: a evidência CEBRASPE de FAPEAL_26 deve ser mantida como override mesmo antes da atualização física de `SOL_SPOTCHECKS.md`.
