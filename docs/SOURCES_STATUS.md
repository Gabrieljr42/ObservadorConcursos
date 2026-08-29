# Matriz de Status das Fontes de Concursos (1 a 99)

> **Projeto**: Observador de Concursos  
> **Data de Atualização**: 28/08/2026  
> **Cobertura**: 99 de 99 fontes cadastradas, tipadas, testadas e integradas ao pipeline de diagnóstico.

---

## 1. Resumo Executivo da Arquitetura

1. **Pipeline de 3 Estágios (`BaseConnector`)**:
   - **Estágio 1**: `httpx` de alta performance com headers de browser e timeout configurável.
   - **Estágio 2**: `httpx` permissivo com bypass de SSL legado / fallback de encoding Latin-1 / UTF-8.
   - **Estágio 3**: `Playwright Chromium` headless automático para SPAs e sites protegidos por renderização JavaScript pesada.
2. **Quality Gate Rígido (`_is_valid_certame`)**:
   - Rejeição ativa de lixo de menus, termos genéricos (*"para saber mais informações"*, botões de navegação, termos de privacidade).
   - Rejeição estrita de fomento científico puro / bolsas acadêmicas em fontes institucionais (`FAPs`), capturando exclusivamente editais de **processos seletivos, estágio e contratação de pessoal temporário/efetivo**.
3. **Idempotência & Deduplicação Multinível**:
   - Chaves de deduplicação: `(source_id, external_id)` $\rightarrow$ `(source_id, link_pagina)` $\rightarrow$ `(source_id, orgao, edital_numero)`.
   - Comparação semântica de diff sem criar versões espúrias para carimbos de data/hora ou representações numéricas equivalentes.
4. **Diagnóstico Estruturado (`CrawlRun`)**:
   - Tabela `crawl_runs` rastreando início, fim, duração em ms, status (`success`, `empty_valid`, `degraded`, `blocked`, `failed`), HTTP status, se usou browser, contagem de candidatos encontrados/rejeitados, inseridos, atualizados e inalterados.
   - **Zero falhas silenciosas**: `/crawl-all/sync` isola falhas individuais por transação segura.

---

## 2. Matriz Completa das 99 Fontes

| # | Fonte / Banca | `source_type` | Categoria | URL Oficial | Estratégia | Browser Fallback | Status |
|---|---|---|---|---|---|:---:|:---:|
| 1 | IBFC | `ibfc_open` | `banca` | `https://concursos.ibfc.org.br` | Dedicado (`IBFCOpenConnector`) | Sim | ✅ Implementado |
| 2 | IDECAN | `idecan_open` | `banca` | `https://idecan.org.br` | Dedicado (`IDECANConnector`) | Sim | ✅ Implementado |
| 3 | Instituto AOCP | `aocp_open` | `banca` | `https://www.institutoaocp.org.br` | Dedicado (`AOCPConnector`) | Sim | ✅ Implementado |
| 4 | CONSULPAM | `consulpam_open` | `banca` | `https://www.consulpam.com.br` | Declarativo (`ConfigurableHTMLConnector`) | Sim | ✅ Implementado |
| 5 | IBAM | `ibam_open` | `banca` | `http://www.ibam-concursos.org.br` | Dedicado (`IBAMConnector`) | Sim | ✅ Implementado |
| 6 | IBADE | `ibade_open` | `banca` | `https://www.ibade.org.br` | Dedicado (`IBADEConnector`) | Sim | ✅ Implementado |
| 7 | CONSULPLAN | `consulplan_open` | `banca` | `https://www.consulplan.net` | Dedicado (`ConsulplanConnector` - Canonical) | Sim | ✅ Implementado |
| 8 | SEPROD | `seprod_open` | `banca` | `https://www.seprod.com.br` | Declarativo (`ConfigurableHTMLConnector`) | Sim | ✅ Implementado |
| 9 | FCC | `fcc_open` | `banca` | `https://www.concursosfcc.com.br` | Dedicado (`FCCConnector`) | Sim | ✅ Implementado |
| 10 | FGV Conhecimento | `fgv_open` | `banca` | `https://conhecimento.fgv.br` | Dedicado (`FGVConnector`) | Sim | ✅ Implementado |
| 11 | CEBRASPE | `cebraspe_open` | `banca` | `https://www.cebraspe.org.br` | Dedicado (`CebraspeConnector`) | Sim | ✅ Implementado |
| 12 | CESGRANRIO | `cesgranrio_open` | `banca` | `https://www.cesgranrio.org.br` | Dedicado (`CesgranrioConnector`) | Sim | ✅ Implementado |
| 13 | IDCAP | `idcap_open` | `banca` | `https://www.idcap.org.br` | Declarativo (`ConfigurableHTMLConnector`) | Sim | ✅ Implementado |
| 14 | IBGP | `ibgp_open` | `banca` | `https://novo.ibgpconcursos.com.br` | Dedicado (`IBGPConnector`) | Sim | ✅ Implementado |
| 15 | FUNDEP | `fundep_open` | `banca` | `https://www.gestaodeconcursos.com.br` | Dedicado (`FundepOpenConnector`) | Sim | ✅ Implementado |
| 16 | FUMARC | `fumarc_open` | `banca` | `https://www.fumarc.com.br` | Dedicado (`FumarcConnector` SSL bypass) | Sim | ✅ Implementado |
| 17 | IMESO | `imeso_open` | `banca` | `https://portal.imeso.com.br` | Dedicado (`IMESOOpenConnector`) | Sim | ✅ Implementado |
| 18 | OMNI Concursos | `omni_open` | `banca` | `https://portal.omniconcursospublicos.com.br` | Dedicado (`OmniConnector`) | Sim | ✅ Implementado |
| 19 | ACCESS | `access_open` | `banca` | `https://www.institutoaccess.org.br` | Dedicado (`AccessConnector`) | Sim | ✅ Implementado |
| 20 | EXAME Auditores | `exame_open` | `banca` | `https://www.exameconsultores.com.br` | Declarativo (`ConfigurableHTMLConnector`) | Sim | ✅ Implementado |
| 21 | EPL Concursos | `epl_open` | `banca` | `https://www.eplconcursos.com.br` | Declarativo (`ConfigurableHTMLConnector`) | Sim | ✅ Implementado |
| 22 | ABCP | `abcp_open` | `banca` | `https://www.abcp.org.br` | Declarativo (`ConfigurableHTMLConnector`) | Sim | ✅ Implementado |
| 23 | UNIFIL | `unifil_open` | `banca` | `https://www.institutounifil.com.br` | Declarativo (`ConfigurableHTMLConnector`) | Sim | ✅ Implementado |
| 24 | OBJETIVA Concursos | `objetiva_open` | `banca` | `https://www.objetivas.com.br` | Dedicado (`ObjetivaConnector`) | Sim | ✅ Implementado |
| 25 | Leandro Ferreira | `leandroferreira_open` | `banca` | `https://www.leandroferreira.com.br` | Declarativo (`ConfigurableHTMLConnector`) | Sim | ✅ Implementado |
| 26 | COTEC / FADENOR | `cotec_open` | `banca` | `https://www.cotec.fadenor.com.br` | Dedicado (`COTECConnector`) | Sim | ✅ Implementado |
| 27 | Instituto Águia | `aguia_open` | `banca` | `https://www.institutoaguia.org.br` | Declarativo (`ConfigurableHTMLConnector`) | Sim | ✅ Implementado |
| 28 | IUDS | `iuds_open` | `banca` | `https://www.iuds.org.br` | Declarativo (`ConfigurableHTMLConnector`) | Sim | ✅ Implementado |
| 29 | Reis & Reis | `reisesreis_open` | `banca` | `https://www.reisesreis.com.br` | Declarativo (`ConfigurableHTMLConnector`) | Sim | ✅ Implementado |
| 30 | MS Concursos | `msconcursos_open` | `banca` | `https://www.msconcursos.com.br` | Declarativo (`ConfigurableHTMLConnector`) | Sim | ✅ Implementado |
| 31 | FACET Concursos | `facet_open` | `banca` | `https://www.facetconcursos.com.br` | Declarativo (`ConfigurableHTMLConnector`) | Sim | ✅ Implementado |
| 32 | EDUCA PB | `educapb_open` | `banca` | `https://www.educapb.com.br` | Declarativo (`ConfigurableHTMLConnector`) | Sim | ✅ Implementado |
| 33 | ADM&TEC | `admtec_open` | `banca` | `https://www.admtec.org.br` | Declarativo (`ConfigurableHTMLConnector`) | Sim | ✅ Implementado |
| 34 | CONTEMAX | `contemax_open` | `banca` | `https://www.contemaxconsultoria.com.br` | Declarativo (`ConfigurableHTMLConnector`) | Sim | ✅ Implementado |
| 35 | CPCon / UEPB | `cpcon_open` | `banca` | `https://cpcon.uepb.edu.br` | Dedicado (`CPConConnector`) | Sim | ✅ Implementado |
| 36 | FUNVAPI | `funvapi_open` | `banca` | `https://www.funvapi.com.br` | Declarativo (`ConfigurableHTMLConnector`) | Sim | ✅ Implementado |
| 37 | CONSEP | `consep_open` | `banca` | `https://www.consep-pi.com.br` | Declarativo (`ConfigurableHTMLConnector`) | Sim | ✅ Implementado |
| 38 | Instituto Consulplan | `institutoconsulplan_open` | `banca` | `https://www.institutoconsulplan.org.br` | Dedicado (`ConsulplanConnector` - Canonical) | Sim | ✅ Implementado |
| 39 | Instituto Avalia | `avalia_open` | `banca` | `https://www.avalia.org.br` | Dedicado (`AvaliaConnector`) | Sim | ✅ Implementado |
| 40 | UFU / DIRPS | `ufu_selection` | `institutional_selection` | `https://www.portalselecao.ufu.br` | Dedicado (`UFUConnector`) | Sim | ✅ Implementado |
| 41 | IDGRAN | `idgran_open` | `banca` | `https://idgran.com.br` | Declarativo (`ConfigurableHTMLConnector`) | Sim | ✅ Implementado |
| 42 | Quadrix | `quadrix_open` | `banca` | `https://www.quadrix.org.br` | Dedicado (`QuadrixConnector`) | Sim | ✅ Implementado |
| 43 | Gualimp | `gualimp_open` | `banca` | `https://www.gualimp.com.br` | Declarativo (`ConfigurableHTMLConnector`) | Sim | ✅ Implementado |
| 44 | Instituto Verbena / UFG | `verbena_selection` | `institutional_selection` | `https://institutoverbena.ufg.br` | Dedicado (`VerbenaConnector`) | Sim | ✅ Implementado |
| 45 | IDIB | `idib_open` | `banca` | `https://www.idib.org.br` | Dedicado (`IDIBConnector`) | Sim | ✅ Implementado |
| 46 | JCM Consultoria | `jcm_open` | `banca` | `https://www.jcmconcursos.com.br` | Declarativo (`ConfigurableHTMLConnector`) | Sim | ✅ Implementado |
| 47 | Elo Assessoria | `elo_open` | `banca` | `https://www.eloassessoriaeservicos.com.br` | Declarativo (`ConfigurableHTMLConnector`) | Sim | ✅ Implementado |
| 48 | Apta Assessoria | `apta_open` | `banca` | `https://www.aptaconcursos.com.br` | Declarativo (`ConfigurableHTMLConnector`) | Sim | ✅ Implementado |
| 49 | Legalle Concursos | `legalle_open` | `banca` | `https://legalleconcursos.com.br` | Declarativo (`ConfigurableHTMLConnector`) | Sim | ✅ Implementado |
| 50 | RBO Concursos | `rbo_open` | `banca` | `https://www.rboconcursos.com.br` | Declarativo (`ConfigurableHTMLConnector`) | Sim | ✅ Implementado |
| 51 | SHDias | `shdias_open` | `banca` | `https://www.shdias.com.br` | Declarativo (`ConfigurableHTMLConnector`) | Sim | ✅ Implementado |
| 52 | Zambini | `zambini_open` | `banca` | `https://www.zambini.org.br` | Declarativo (`ConfigurableHTMLConnector`) | Sim | ✅ Implementado |
| 53 | Nosso Rumo | `nossorumo_open` | `banca` | `https://www.nossorumo.org.br` | Dedicado (`NossoRumoConnector`) | Sim | ✅ Implementado |
| 54 | Avança SP | `avancasp_open` | `banca` | `https://www.avancasp.org.br` | Dedicado (`AvancaSPConnector`) | Sim | ✅ Implementado |
| 55 | Instituto Mais | `institutomais_open` | `banca` | `https://www.institutomais.org.br` | Declarativo (`ConfigurableHTMLConnector`) | Sim | ✅ Implementado |
| 56 | Publiconsult | `publiconsult_open` | `banca` | `https://www.publiconsult.com.br` | Declarativo (`ConfigurableHTMLConnector`) | Sim | ✅ Implementado |
| 57 | KLC Concursos | `klc_open` | `banca` | `https://www.klcconcursos.com.br` | Declarativo (`ConfigurableHTMLConnector`) | Sim | ✅ Implementado |
| 58 | Sigma Assessoria | `sigma_open` | `banca` | `https://www.sigmaassessoria.com.br` | Declarativo (`ConfigurableHTMLConnector`) | Sim | ✅ Implementado |
| 59 | W2 Auditores | `w2_open` | `banca` | `https://www.w2concursos.com.br` | Declarativo (`ConfigurableHTMLConnector`) | Sim | ✅ Implementado |
| 60 | Fênix Concursos | `fenix_open` | `banca` | `https://www.fenixconcursos.com.br` | Declarativo (`ConfigurableHTMLConnector`) | Sim | ✅ Implementado |
| 61 | Oppus Concursos | `oppus_open` | `banca` | `https://www.oppusconcursos.com.br` | Declarativo (`ConfigurableHTMLConnector`) | Sim | ✅ Implementado |
| 62 | Instituto Legatus | `legatus_open` | `banca` | `https://www.institutolegatus.com.br` | Dedicado (`LegatusConnector`) | Sim | ✅ Implementado |
| 63 | FEPESE | `fepese_open` | `banca` | `https://fepese.org.br` | Dedicado (`FEPESEConnector`) | Sim | ✅ Implementado |
| 64 | FUNCERN | `funcern_selection` | `institutional_selection` | `https://funcern.br` | Dedicado (`FUNCERNConnector`) | Sim | ✅ Implementado |
| 65 | FAPEMIG | `fapemig_selection` | `institutional_selection` | `https://fapemig.br` | Institucional (`InstitutionalSelectionConnector`) | Sim | ✅ Implementado |
| 66 | FAPES (ES) | `fapes_selection` | `institutional_selection` | `https://fapes.es.gov.br` | Institucional (`InstitutionalSelectionConnector`) | Sim | ✅ Implementado |
| 67 | FAPESQ (PB) | `fapesq_selection` | `institutional_selection` | `https://fapesq.pb.gov.br` | Institucional (`InstitutionalSelectionConnector`) | Sim | ✅ Implementado |
| 68 | Fundação Uniselva | `uniselva_selection` | `institutional_selection` | `https://www.fundacaouniselva.org.br` | Institucional (`InstitutionalSelectionConnector`) | Sim | ✅ Implementado |
| 69 | Fundação FAFIPA | `fafipa_open` | `banca` | `https://www.fundacaofafipa.org.br` | Dedicado (`FAFIPAConnector`) | Sim | ✅ Implementado |
| 70 | IESES | `ieses_open` | `banca` | `https://www.ieses.org` | Dedicado (`IESESConnector`) | Sim | ✅ Implementado |
| 71 | FUNPEC | `funpec_selection` | `institutional_selection` | `https://www.funpec.org.br` | Institucional (`InstitutionalSelectionConnector`) | Sim | ✅ Implementado |
| 72 | FADE | `fade_selection` | `institutional_selection` | `https://fade.org.br` | Institucional (`InstitutionalSelectionConnector`) | Sim | ✅ Implementado |
| 73 | FAPEX | `fapex_selection` | `institutional_selection` | `https://fapex.org.br` | Institucional (`InstitutionalSelectionConnector`) | Sim | ✅ Implementado |
| 74 | FATEC | `fatec_selection` | `institutional_selection` | `https://fatec.org.br` | Institucional (`InstitutionalSelectionConnector`) | Sim | ✅ Implementado |
| 75 | FAPED | `faped_selection` | `institutional_selection` | `https://faped.org.br` | Institucional (`InstitutionalSelectionConnector`) | Sim | ✅ Implementado |
| 76 | FAPESE | `fapese_selection` | `institutional_selection` | `https://fapese.org.br` | Institucional (`InstitutionalSelectionConnector`) | Sim | ✅ Implementado |
| 77 | FAPEPI (PI) | `fapepi_selection` | `institutional_selection` | `https://fapepi.pi.gov.br` | Institucional (`InstitutionalSelectionConnector`) | Sim | ✅ Implementado |
| 78 | FAPEMA (MA) | `fapema_selection` | `institutional_selection` | `https://fapema.br` | Institucional (`InstitutionalSelectionConnector`) | Sim | ✅ Implementado |
| 79 | FAPECE (CE) | `fapece_selection` | `institutional_selection` | `https://fapece.ce.gov.br` | Institucional (`InstitutionalSelectionConnector`) | Sim | ✅ Implementado |
| 80 | FAPERN (RN) | `fapern_selection` | `institutional_selection` | `https://fapern.rn.gov.br` | Institucional (`InstitutionalSelectionConnector`) | Sim | ✅ Implementado |
| 81 | FAPEAL (AL) | `fapeal_selection` | `institutional_selection` | `https://fapeal.br` | Institucional (`InstitutionalSelectionConnector`) | Sim | ✅ Implementado |
| 82 | FACEPE (PE) | `facepe_selection` | `institutional_selection` | `https://facepe.br` | Institucional (`InstitutionalSelectionConnector`) | Sim | ✅ Implementado |
| 83 | FAPESB (BA) | `fapesb_selection` | `institutional_selection` | `https://fapesb.ba.gov.br` | Institucional (`InstitutionalSelectionConnector`) | Sim | ✅ Implementado |
| 84 | FAPERJ (RJ) | `faperj_selection` | `institutional_selection` | `https://faperj.br` | Institucional (`InstitutionalSelectionConnector`) | Sim | ✅ Implementado |
| 85 | FAPESP (SP) | `fapesp_selection` | `institutional_selection` | `https://fapesp.br` | Institucional (`InstitutionalSelectionConnector`) | Sim | ✅ Implementado |
| 86 | FAPPR / Araucária | `fappr_selection` | `institutional_selection` | `https://fappr.pr.gov.br` | Institucional (`InstitutionalSelectionConnector`) | Sim | ✅ Implementado |
| 87 | FAPESC (SC) | `fapesc_selection` | `institutional_selection` | `https://fapesc.sc.gov.br` | Institucional (`InstitutionalSelectionConnector`) | Sim | ✅ Implementado |
| 88 | FAPERGS (RS) | `fapergs_selection` | `institutional_selection` | `https://fapergs.rs.gov.br` | Institucional (`InstitutionalSelectionConnector`) | Sim | ✅ Implementado |
| 89 | FUNDECT (MS) | `fundect_selection` | `institutional_selection` | `https://fundect.ms.gov.br` | Institucional (`InstitutionalSelectionConnector`) | Sim | ✅ Implementado |
| 90 | FAPEMAT (MT) | `fapemat_selection` | `institutional_selection` | `https://fapemat.mt.gov.br` | Institucional (`InstitutionalSelectionConnector`) | Sim | ✅ Implementado |
| 91 | FAPEG (GO) | `fapeg_selection` | `institutional_selection` | `https://fapeg.go.gov.br` | Institucional (`InstitutionalSelectionConnector`) | Sim | ✅ Implementado |
| 92 | FAPDF (DF) | `fapdf_selection` | `institutional_selection` | `https://fap.df.gov.br` | Institucional (`InstitutionalSelectionConnector`) | Sim | ✅ Implementado |
| 93 | FAPT (TO) | `fapt_selection` | `institutional_selection` | `https://fapt.to.gov.br` | Institucional (`InstitutionalSelectionConnector`) | Sim | ✅ Implementado |
| 94 | FAPEAM (AM) | `fapeam_selection` | `institutional_selection` | `https://fapeam.am.gov.br` | Institucional (`InstitutionalSelectionConnector`) | Sim | ✅ Implementado |
| 95 | FAPESPA (PA) | `fapespa_selection` | `institutional_selection` | `https://fapespa.pa.gov.br` | Institucional (`InstitutionalSelectionConnector`) | Sim | ✅ Implementado |
| 96 | FAPEAP (AP) | `fapeap_selection` | `institutional_selection` | `https://fapeap.ap.gov.br` | Institucional (`InstitutionalSelectionConnector`) | Sim | ✅ Implementado |
| 97 | FAPERR (RR) | `faperr_selection` | `institutional_selection` | `https://faperr.rr.gov.br` | Institucional (`InstitutionalSelectionConnector`) | Sim | ✅ Implementado |
| 98 | FAPERO (RO) | `fapero_selection` | `institutional_selection` | `https://fapero.ro.gov.br` | Institucional (`InstitutionalSelectionConnector`) | Sim | ✅ Implementado |
| 99 | FAPAC (AC) | `fapac_selection` | `institutional_selection` | `https://fapac.ac.gov.br` | Institucional (`InstitutionalSelectionConnector`) | Sim | ✅ Implementado |

---

## 3. Endpoints Disponibilizados

- `POST /sources/presets/seed-all`: Sincroniza todas as 99 fontes na tabela `sources`.
- `GET /sources/{source_id}/runs`: Histórico de diagnósticos da fonte.
- `GET /runs/recent`: Feed de execuções de crawler recentes com status (`success`, `empty_valid`, `degraded`, `blocked`, `failed`).
- `POST /crawl-all/sync`: Disparo sequencial seguro de todas as fontes ativas com garantia de não travamento global.
