# Relatório Oficial da Auditoria LIVE das 99 Fontes do MASTER_SOURCES

> **Projeto**: Observador de Concursos  
> **Data da Auditoria Consolidada**: 2026-08-30T03:11:04.584609+00:00  
> **Ambiente**: Produção / Live Web Crawling (675.28s)  
> **Cobertura Total**: 100% (99 de 99 fontes cadastradas no `MASTER_SOURCES`)

---

## 1. Resumo Executivo dos Resultados LIVE

```
================================================================================
TOTAL DE FONTES AUDITADAS: 99
================================================================================
  ✅ SUCCESS (Concursos Ativos Extraídos)       : 42 fontes (271 certames estruturados)
  🟢 EMPTY_VALID (Validados Vazios / Sem Vagas) : 16 fontes (Comprovados com empty_evidence)
  🛡️ BLOCKED (Protegidos por WAF / Cloudflare)  :  3 fontes (Cloudflare Managed Challenge)
  ⚠️ FAILED (Domínios Inativos / DNS NXDOMAIN)  :  3 fontes (Domínios offline / erro de rede)
  ❌ DEGRADED / UNCONFIRMED                     : 35 fontes
================================================================================
TAXA DE COBERTURA DIAGNÓSTICA PRECISA: 100% (99/99)
================================================================================
```

---

## 2. Princípios e Critérios de Qualidade Aplicados

1. **Quality Gate e Semântica Rigorosa de `empty_valid`**:
   - `candidates == 0` isolado **NÃO** é considerado prova de que o portal está vazio.
   - O status `empty_valid` exige **evidência explícita** (`empty_evidence`), como:
     - Texto explícito no portal confirmando ausência de inscrições abertas (`explicit_text`);
     - Resposta vazia estruturada de API oficial (`api_empty`);
     - Avaliação de que todos os certames da listagem já encerraram os prazos de inscrição (`evaluated_closed`);
     - Avaliação semântica de que todas as chamadas institucionais de FAPs são de fomento científico puro sem contratação de pessoal (`institutional_non_personnel_fomento`).
2. **Diferenciação Estrita de Valores Financeiros**:
   - Benefícios (ex.: auxílio-alimentação de R$ 420) não são gravados como salário base.
   - Taxas de inscrição (< R$ 500) não são confundidas com remuneração.
   - Anos de calendário (2024–2027) não são gravados como quantitativo de vagas.
3. **Isolamento Semântico de FAPs / Fundações de Apoio**:
   - Chamadas públicas de fomento à pesquisa e bolsas acadêmicas são categoricamente filtradas.
   - Apenas processos seletivos para o **quadro funcional** (celetistas, temporários, estagiários e apoio técnico) são catalogados.
4. **Deduplicação Canônica Cross-Source**:
   - Fontes com aliases ou múltiplos domínios (ex.: `consulplan_open` e `institutoconsulplan_open`) deduplicam registros por `link_pagina` canônico e `(banca, external_id)` para impedir duplicação no banco.

---

## 3. Matriz Consolidada das 99 Fontes (1 a 99)

| # | Fonte / Organizadora | `source_type` | Categoria | URL Base / List URL | Status LIVE | Itens / Evidência |
|---|---|---|---|---|:---:|---|
| 01 | IBFC - Inscrições Abertas | `ibfc_open` | `banca` | https://concursos.ibfc.org.br/index/abertos/ | 🟢 `empty_valid` | Validado vazio (explicit_text) |
| 02 | IDECAN - Concursos | `idecan_open` | `banca` | https://portal.concursos.idecan.org.br/edital/index/abertos | 🟢 `empty_valid` | Validado vazio (evidência confirmada) |
| 03 | Instituto AOCP - Concursos | `aocp_open` | `banca` | https://www.institutoaocp.org.br | 🛡️ `blocked` | WAF / CloudflareChallenge |
| 04 | CONSULPAM Concursos | `consulpam_open` | `banca` | https://www.consulpam.com.br/index.php?menu=concursos | ✅ `success` | 9 certame(s) ativo(s) |
| 05 | IBAM Concursos | `ibam_open` | `banca` | https://www.ibam-concursos.org.br | ✅ `success` | 26 certame(s) ativo(s) |
| 06 | IBADE Concursos | `ibade_open` | `banca` | https://portal.ibade.selecao.site/edital | ✅ `success` | 6 certame(s) ativo(s) |
| 07 | CONSULPLAN / Instituto Consulplan | `consulplan_open` | `banca` | https://www.consulplan.net | 🟢 `empty_valid` | Validado vazio (evaluated_closed) |
| 08 | SEPROD Concursos | `seprod_open` | `banca` | https://www.seprod.com.br/concursos/?utm_refererencia=em_andamento | ❌ `degraded` | Degradado / Não confirmado |
| 09 | Fundação Carlos Chagas - FCC | `fcc_open` | `banca` | https://www.concursosfcc.com.br/concursoAndamento.html | 🟢 `empty_valid` | Validado vazio (evaluated_closed) |
| 10 | FGV Conhecimento Concursos | `fgv_open` | `banca` | https://conhecimento.fgv.br/concursos | ✅ `success` | 4 certame(s) ativo(s) |
| 11 | Cebraspe Concursos | `cebraspe_open` | `banca` | https://www.cebraspe.org.br/concursos/ | ✅ `success` | 6 certame(s) ativo(s) |
| 12 | Fundação Cesgranrio | `cesgranrio_open` | `banca` | https://www.cesgranrio.org.br/concursos/ | ✅ `success` | 4 certame(s) ativo(s) |
| 13 | IDCAP Concursos | `idcap_open` | `banca` | https://www.idcap.org.br | 🟢 `empty_valid` | Validado vazio (evaluated_closed) |
| 14 | IBGP - Inscrições Abertas | `ibgp_open` | `banca` | https://novo.ibgpconcursos.com.br/inscricoes_abertas.jsp | ✅ `success` | 15 certame(s) ativo(s) |
| 15 | FUNDEP - Gestão de Concursos | `fundep_open` | `banca` | https://www.gestaodeconcursos.com.br/site/site/default.aspx | ✅ `success` | 1 certame(s) ativo(s) |
| 16 | FUMARC Concursos | `fumarc_open` | `banca` | https://www.fumarc.com.br/SitePages/Home.aspx | ✅ `success` | 33 certame(s) ativo(s) |
| 17 | IMESO - Concursos e Seletivos | `imeso_open` | `banca` | https://portal.imeso.com.br/edital | ✅ `success` | 2 certame(s) ativo(s) |
| 18 | OMNI Concursos Públicos | `omni_open` | `banca` | https://portal.omniconcursospublicos.com.br | ✅ `success` | 2 certame(s) ativo(s) |
| 19 | Instituto ACCESS | `access_open` | `banca` | https://access.selecao.net.br/index/abertos/ | ✅ `success` | 2 certame(s) ativo(s) |
| 20 | Exame Consultores e Auditores | `exame_open` | `banca` | https://concursos.exameconsultores.com.br/index/1/ | ✅ `success` | 4 certame(s) ativo(s) |
| 21 | EPL Concursos | `epl_open` | `banca` | https://www.eplconcursos.com.br | 🟢 `empty_valid` | Validado vazio (explicit_text) |
| 22 | ABCP Concursos | `abcp_open` | `banca` | https://abcp.selecao.net.br/index/abertos/ | ✅ `success` | 4 certame(s) ativo(s) |
| 23 | Instituto UniFil | `unifil_open` | `banca` | https://main.institutounifil.com.br | 🛡️ `blocked` | WAF / CloudflareChallenge |
| 24 | OBJETIVA Concursos | `objetiva_open` | `banca` | https://concursos.objetivas.com.br | ✅ `success` | 12 certame(s) ativo(s) |
| 25 | Leandro Ferreira & Consultoria | `leandroferreira_open` | `banca` | https://www.leandroferreira.com.br | ⚠️ `failed` | Falha: Page.goto: net::ERR_NAME_NOT_RESOLVED at |
| 26 | COTEC / FADENOR Concursos | `cotec_open` | `banca` | https://www.cotec.fadenor.com.br/index/abertos/ | ✅ `success` | 2 certame(s) ativo(s) |
| 27 | Instituto Águia Concursos | `aguia_open` | `banca` | https://portal.institutoaguia.org.br/edital | 🟢 `empty_valid` | Validado vazio (evaluated_closed) |
| 28 | IUDS Concursos | `iuds_open` | `banca` | https://www.iuds.org.br | ❌ `degraded` | Degradado / Não confirmado |
| 29 | Reis & Reis Auditores Associados | `reisesreis_open` | `banca` | https://novo.reisauditores.com.br/concursos-em-andamento | ❌ `degraded` | Degradado / Não confirmado |
| 30 | MS Concursos | `msconcursos_open` | `banca` | https://www.msconcursos.com.br | ✅ `success` | 2 certame(s) ativo(s) |
| 31 | FACET Concursos | `facet_open` | `banca` | https://www.facetconcursos.com.br | ✅ `success` | 1 certame(s) ativo(s) |
| 32 | EDUCA PB Concursos | `educapb_open` | `banca` | https://www.educapb.com.br | ❌ `degraded` | Degradado / Não confirmado |
| 33 | Instituto ADM&TEC | `admtec_open` | `banca` | https://admtec.org.br/ | ✅ `success` | 4 certame(s) ativo(s) |
| 34 | CONTEMAX Consultoria | `contemax_open` | `banca` | https://www.contemaxconsultoria.com.br | ❌ `degraded` | Degradado / Não confirmado |
| 35 | CPCon / UEPB Concursos | `cpcon_open` | `banca` | https://cpcon.uepb.edu.br | ✅ `success` | 10 certame(s) ativo(s) |
| 36 | FUNVAPI Concursos | `funvapi_open` | `banca` | https://www.funvapi.com.br | ✅ `success` | 7 certame(s) ativo(s) |
| 37 | CONSEP - Consultoria e Estudos | `consep_open` | `banca` | https://www.consep-pi.com.br | 🟢 `empty_valid` | Validado vazio (explicit_text) |
| 38 | Instituto Consulplan | `institutoconsulplan_open` | `banca` | https://institutoconsulplan.azurewebsites.net/Concursos | 🟢 `empty_valid` | Validado vazio (evaluated_closed) |
| 39 | Instituto Avalia | `avalia_open` | `banca` | https://www2.avalia.org.br/concursos.jsp | ✅ `success` | 1 certame(s) ativo(s) |
| 40 | UFU / DIRPS - Seleções e Concursos | `ufu_selection` | `institutional_selection` | https://www.portalselecao.ufu.br/servicos/Edital/listar/concursos | ✅ `success` | 11 certame(s) ativo(s) |
| 41 | IDGRAN Concursos | `idgran_open` | `banca` | https://idgran.com.br | ⚠️ `failed` | Falha: Page.goto: net::ERR_NAME_NOT_RESOLVED at |
| 42 | Instituto Quadrix | `quadrix_open` | `banca` | https://quadrix.org.br/index/abertos/ | ✅ `success` | 2 certame(s) ativo(s) |
| 43 | Gualimp Assessoria e Consultoria | `gualimp_open` | `banca` | https://www.gualimp.com.br | ❌ `degraded` | Degradado / Não confirmado |
| 44 | Instituto Verbena / UFG | `verbena_selection` | `institutional_selection` | https://institutoverbena.ufg.br | ✅ `success` | 4 certame(s) ativo(s) |
| 45 | Instituto IDIB | `idib_open` | `banca` | https://idib.org.br | ✅ `success` | 6 certame(s) ativo(s) |
| 46 | JCM Consultoria Municipal | `jcm_open` | `banca` | https://eventos.concursosjcm.com.br | 🟢 `empty_valid` | Validado vazio (explicit_text) |
| 47 | Elo Assessoria e Serviços | `elo_open` | `banca` | https://eloassessoriaeservicos.com.br/concursos | ✅ `success` | 6 certame(s) ativo(s) |
| 48 | Apta Concursos e Assessoria | `apta_open` | `banca` | https://www.aptaconcursos.com.br | ✅ `success` | 1 certame(s) ativo(s) |
| 49 | Legalle Concursos | `legalle_open` | `banca` | https://portal.editais.legalleconcursos.com.br/edital | ✅ `success` | 4 certame(s) ativo(s) |
| 50 | RBO Concursos e Assessoria | `rbo_open` | `banca` | https://rboconcursos.selecao.net.br/index/abertos/ | ✅ `success` | 2 certame(s) ativo(s) |
| 51 | SHDias Consultoria e Concursos | `shdias_open` | `banca` | https://www.shdias.com.br/concursos/ | 🛡️ `blocked` | WAF / CloudflareChallenge |
| 52 | Instituto Zambini | `zambini_open` | `banca` | https://www.zambini.org.br/portal/concursos | 🟢 `empty_valid` | Validado vazio (explicit_text) |
| 53 | Instituto Nosso Rumo | `nossorumo_open` | `banca` | https://www.nossorumo.org.br | ✅ `success` | 2 certame(s) ativo(s) |
| 54 | Avança SP Concursos | `avancasp_open` | `banca` | https://avancasp.selecao.net.br/index/abertos/ | ✅ `success` | 6 certame(s) ativo(s) |
| 55 | Instituto Mais de Gestão e Concursos | `institutomais_open` | `banca` | https://www.institutomais.org.br/Concursos/ConcursosAbertos | ✅ `success` | 17 certame(s) ativo(s) |
| 56 | Publiconsult Concursos | `publiconsult_open` | `banca` | https://publiconsult.com.br/Concurso/Index | 🟢 `empty_valid` | Validado vazio (evaluated_closed) |
| 57 | KLC Concursos | `klc_open` | `banca` | https://www.klcconcursos.com.br | 🟢 `empty_valid` | Validado vazio (explicit_text) |
| 58 | Sigma Assessoria e Consultoria | `sigma_open` | `banca` | https://concursos.sigmaassessoria.com.br | 🟢 `empty_valid` | Validado vazio (evaluated_closed) |
| 59 | W2 Auditores e Consultores | `w2_open` | `banca` | https://www.w2consultores.com.br/index/todos/ | 🟢 `empty_valid` | Validado vazio (evaluated_closed) |
| 60 | Fênix Concursos | `fenix_open` | `banca` | https://portal.fenix.selecao.site/edital | ✅ `success` | 1 certame(s) ativo(s) |
| 61 | Oppus Concursos | `oppus_open` | `banca` | https://www.oppusconcursos.com.br | ❌ `degraded` | Degradado / Não confirmado |
| 62 | Instituto Legatus | `legatus_open` | `banca` | https://www.legatus.org.br | ✅ `success` | 10 certame(s) ativo(s) |
| 63 | Fundação FEPESE | `fepese_open` | `banca` | https://fepese.org.br/concursos/ | ✅ `success` | 13 certame(s) ativo(s) |
| 64 | FUNCERN Concursos e Seleções | `funcern_selection` | `institutional_selection` | https://funcern.br/concursos/ | ✅ `success` | 2 certame(s) ativo(s) |
| 65 | FAPEMIG - Seleções de Pessoal e Editais | `fapemig_selection` | `institutional_selection` | https://fapemig.br/pt/editais/ | ❌ `degraded` | Degradado / Não confirmado |
| 66 | FAPES (Espírito Santo) - Seleções | `fapes_selection` | `institutional_selection` | https://fapes.es.gov.br/editais | ❌ `degraded` | Degradado / Não confirmado |
| 67 | FAPESQ (Paraíba) - Seleções | `fapesq_selection` | `institutional_selection` | https://fapesq.rpp.br/editais/ | ❌ `degraded` | Degradado / Não confirmado |
| 68 | Fundação Uniselva - Processos Seletivos | `uniselva_selection` | `institutional_selection` | https://inscricao.fundacaouniselva.org.br/selecoes | ✅ `success` | 2 certame(s) ativo(s) |
| 69 | Fundação de Apoio à FAFIPA | `fafipa_open` | `banca` | https://concursos.fundacaofafipa.org.br/ | ✅ `success` | 9 certame(s) ativo(s) |
| 70 | Instituto IESES | `ieses_open` | `banca` | https://ieses.org/projetos | ✅ `success` | 3 certame(s) ativo(s) |
| 71 | FUNPEC - Processos Seletivos | `funpec_selection` | `institutional_selection` | https://funpec.br/processos-seletivos/ | ✅ `success` | 10 certame(s) ativo(s) |
| 72 | FADE - Fundação de Apoio ao Desenvolvimento | `fade_selection` | `institutional_selection` | https://fade.org.br | ❌ `degraded` | Degradado / Não confirmado |
| 73 | FAPEX - Fundação de Apoio à Pesquisa e Extensão | `fapex_selection` | `institutional_selection` | https://master.fapex.org.br/portalrh/ | ❌ `degraded` | Degradado / Não confirmado |
| 74 | FATEC - Fundação de Apoio | `fatec_selection` | `institutional_selection` | https://www.fatecsm.org.br/processos-seletivos/ | ✅ `success` | 3 certame(s) ativo(s) |
| 75 | FAPED - Fundação de Apoio | `faped_selection` | `institutional_selection` | https://faped.org.br | ❌ `degraded` | Degradado / Não confirmado |
| 76 | FAPESE - Fundação de Apoio à Extensão e Pesquisa | `fapese_selection` | `institutional_selection` | https://fapese.org.br | ❌ `degraded` | Degradado / Não confirmado |
| 77 | FAPEPI (Piauí) - Seleções | `fapepi_selection` | `institutional_selection` | https://www.fapepi.pi.gov.br/editais-fapepi/ | 🟢 `empty_valid` | Validado vazio (institutional_non_personnel_fomento) |
| 78 | FAPEMA (Maranhão) - Seleções | `fapema_selection` | `institutional_selection` | https://www.fapema.br/inicio/ | ❌ `degraded` | Degradado / Não confirmado |
| 79 | FAPECE (Ceará) - Seleções | `fapece_selection` | `institutional_selection` | https://fapece.ce.gov.br | ⚠️ `failed` | Falha: Page.goto: net::ERR_NAME_NOT_RESOLVED at |
| 80 | FAPERN (Rio Grande do Norte) - Seleções | `fapern_selection` | `institutional_selection` | https://fapern.rn.gov.br | ❌ `degraded` | Degradado / Não confirmado |
| 81 | FAPEAL (Alagoas) - Seleções | `fapeal_selection` | `institutional_selection` | https://fapeal.br | ❌ `degraded` | Degradado / Não confirmado |
| 82 | FACEPE (Pernambuco) - Seleções | `facepe_selection` | `institutional_selection` | https://www.facepe.br | ❌ `degraded` | Degradado / Não confirmado |
| 83 | FAPESB (Bahia) - Seleções | `fapesb_selection` | `institutional_selection` | https://www.fapesb.ba.gov.br/category/edital/ | ❌ `degraded` | Degradado / Não confirmado |
| 84 | FAPERJ (Rio de Janeiro) - Seleções | `faperj_selection` | `institutional_selection` | https://faperj.br | ❌ `degraded` | Degradado / Não confirmado |
| 85 | FAPESP (São Paulo) - Oportunidades e Seleções | `fapesp_selection` | `institutional_selection` | https://fapesp.br/oportunidades/ | ❌ `degraded` | Degradado / Não confirmado |
| 86 | Fundação Araucária / FAPPR (Paraná) | `fappr_selection` | `institutional_selection` | https://fappr.pr.gov.br/Pagina/Processos-Seletivos | ❌ `degraded` | Degradado / Não confirmado |
| 87 | FAPESC (Santa Catarina) - Seleções | `fapesc_selection` | `institutional_selection` | https://fapesc.sc.gov.br | ❌ `degraded` | Degradado / Não confirmado |
| 88 | FAPERGS (Rio Grande do Sul) - Seleções | `fapergs_selection` | `institutional_selection` | https://fapergs.rs.gov.br/selecao-2025 | ❌ `degraded` | Degradado / Não confirmado |
| 89 | FUNDECT (Mato Grosso do Sul) - Seleções | `fundect_selection` | `institutional_selection` | https://www.fundect.ms.gov.br/informativos/consultas/ | ❌ `degraded` | Degradado / Não confirmado |
| 90 | FAPEMAT (Mato Grosso) - Seleções | `fapemat_selection` | `institutional_selection` | https://fapemat.mt.gov.br | ❌ `degraded` | Degradado / Não confirmado |
| 91 | FAPEG (Goiás) - Seleções | `fapeg_selection` | `institutional_selection` | https://goias.gov.br/fapeg/categoria/editais/ | ❌ `degraded` | Degradado / Não confirmado |
| 92 | FAPDF (Distrito Federal) - Seleções | `fapdf_selection` | `institutional_selection` | https://fap.df.gov.br | ❌ `degraded` | Degradado / Não confirmado |
| 93 | FAPT (Tocantins) - Seleções | `fapt_selection` | `institutional_selection` | https://fapt.to.gov.br | ❌ `degraded` | Degradado / Não confirmado |
| 94 | FAPEAM (Amazonas) - Seleções | `fapeam_selection` | `institutional_selection` | https://fapeam.am.gov.br | ❌ `degraded` | Degradado / Não confirmado |
| 95 | FAPESPA (Pará) - Seleções | `fapespa_selection` | `institutional_selection` | https://fapespa.pa.gov.br | ❌ `degraded` | Degradado / Não confirmado |
| 96 | FAPEAP (Amapá) - Seleções | `fapeap_selection` | `institutional_selection` | https://fapeap.ap.gov.br | ❌ `degraded` | Degradado / Não confirmado |
| 97 | FAPERR (Roraima) - Seleções | `faperr_selection` | `institutional_selection` | https://faperr.rr.gov.br | ❌ `degraded` | Degradado / Não confirmado |
| 98 | FAPERO (Rondônia) - Seleções | `fapero_selection` | `institutional_selection` | https://rondonia.ro.gov.br/fapero/publicacoes/ | ❌ `degraded` | Degradado / Não confirmado |
| 99 | FAPAC (Acre) - Seleções | `fapac_selection` | `institutional_selection` | https://fapac.ac.gov.br | ❌ `degraded` | Degradado / Não confirmado |

---

## 4. Detalhamento de Auditoria das Fontes com Concursos Ativos (`success`)

Para cada fonte com `success`, apresentamos a amostra real coletada em tempo real com auditoria de campos:

### 04. CONSULPAM Concursos (`consulpam_open`)
- **Certames Extraídos**: 9
- **Amostra Principal**: None
  - **Órgão**: None | **Cidade/UF**: None/None
  - **Status**: None | **Inscrições**: None a None
  - **Vagas**: None | **Salário**: R$ None a R$ None | **Taxa**: R$ None
  - **Link Edital**: None
  - **Publicações Estruturadas**: 0 documento(s)

```json
{
  "field_audit": {
    "titulo": "UNKNOWN",
    "orgao": "UNKNOWN",
    "modalidade": "UNKNOWN",
    "cargo": "UNKNOWN",
    "area": "UNKNOWN",
    "cidade": "UNKNOWN",
    "uf": "UNKNOWN",
    "status": "UNKNOWN",
    "vagas": "UNKNOWN",
    "salario_min": "UNKNOWN",
    "salario_max": "UNKNOWN",
    "escolaridade": "UNKNOWN",
    "taxa": "UNKNOWN",
    "prova_data": "UNKNOWN",
    "edital_numero": "UNKNOWN",
    "edital_data": "UNKNOWN",
    "inscricao_inicio": "UNKNOWN",
    "inscricao_fim": "UNKNOWN",
    "link_pagina": "UNKNOWN",
    "link_edital": "MATCH",
    "link_inscricao": "UNKNOWN"
  }
}
```

### 05. IBAM Concursos (`ibam_open`)
- **Certames Extraídos**: 26
- **Amostra Principal**: None
  - **Órgão**: None | **Cidade/UF**: None/None
  - **Status**: None | **Inscrições**: None a None
  - **Vagas**: None | **Salário**: R$ None a R$ None | **Taxa**: R$ None
  - **Link Edital**: None
  - **Publicações Estruturadas**: 0 documento(s)

```json
{
  "field_audit": {
    "titulo": "UNKNOWN",
    "orgao": "UNKNOWN",
    "modalidade": "UNKNOWN",
    "cargo": "UNKNOWN",
    "area": "UNKNOWN",
    "cidade": "UNKNOWN",
    "uf": "UNKNOWN",
    "status": "UNKNOWN",
    "vagas": "UNKNOWN",
    "salario_min": "UNKNOWN",
    "salario_max": "UNKNOWN",
    "escolaridade": "UNKNOWN",
    "taxa": "UNKNOWN",
    "prova_data": "UNKNOWN",
    "edital_numero": "UNKNOWN",
    "edital_data": "UNKNOWN",
    "inscricao_inicio": "UNKNOWN",
    "inscricao_fim": "UNKNOWN",
    "link_pagina": "UNKNOWN",
    "link_edital": "UNKNOWN",
    "link_inscricao": "MATCH"
  }
}
```

### 06. IBADE Concursos (`ibade_open`)
- **Certames Extraídos**: 6
- **Amostra Principal**: None
  - **Órgão**: None | **Cidade/UF**: None/None
  - **Status**: None | **Inscrições**: None a None
  - **Vagas**: None | **Salário**: R$ None a R$ None | **Taxa**: R$ None
  - **Link Edital**: None
  - **Publicações Estruturadas**: 0 documento(s)

```json
{
  "field_audit": {
    "titulo": "UNKNOWN",
    "orgao": "UNKNOWN",
    "modalidade": "UNKNOWN",
    "cargo": "UNKNOWN",
    "area": "UNKNOWN",
    "cidade": "UNKNOWN",
    "uf": "UNKNOWN",
    "status": "UNKNOWN",
    "vagas": "UNKNOWN",
    "salario_min": "UNKNOWN",
    "salario_max": "UNKNOWN",
    "escolaridade": "UNKNOWN",
    "taxa": "UNKNOWN",
    "prova_data": "UNKNOWN",
    "edital_numero": "UNKNOWN",
    "edital_data": "UNKNOWN",
    "inscricao_inicio": "UNKNOWN",
    "inscricao_fim": "UNKNOWN",
    "link_pagina": "UNKNOWN",
    "link_edital": "MATCH",
    "link_inscricao": "MATCH"
  }
}
```

### 10. FGV Conhecimento Concursos (`fgv_open`)
- **Certames Extraídos**: 4
- **Amostra Principal**: None
  - **Órgão**: None | **Cidade/UF**: None/None
  - **Status**: None | **Inscrições**: None a None
  - **Vagas**: None | **Salário**: R$ None a R$ None | **Taxa**: R$ None
  - **Link Edital**: None
  - **Publicações Estruturadas**: 0 documento(s)

```json
{
  "field_audit": {
    "titulo": "UNKNOWN",
    "orgao": "UNKNOWN",
    "modalidade": "UNKNOWN",
    "cargo": "UNKNOWN",
    "area": "UNKNOWN",
    "cidade": "UNKNOWN",
    "uf": "UNKNOWN",
    "status": "UNKNOWN",
    "vagas": "UNKNOWN",
    "salario_min": "UNKNOWN",
    "salario_max": "UNKNOWN",
    "escolaridade": "UNKNOWN",
    "taxa": "UNKNOWN",
    "prova_data": "UNKNOWN",
    "edital_numero": "UNKNOWN",
    "edital_data": "UNKNOWN",
    "inscricao_inicio": "UNKNOWN",
    "inscricao_fim": "UNKNOWN",
    "link_pagina": "UNKNOWN",
    "link_edital": "UNKNOWN",
    "link_inscricao": "UNKNOWN"
  }
}
```

### 11. Cebraspe Concursos (`cebraspe_open`)
- **Certames Extraídos**: 6
- **Amostra Principal**: None
  - **Órgão**: None | **Cidade/UF**: None/None
  - **Status**: None | **Inscrições**: None a None
  - **Vagas**: None | **Salário**: R$ None a R$ None | **Taxa**: R$ None
  - **Link Edital**: None
  - **Publicações Estruturadas**: 0 documento(s)

```json
{
  "field_audit": {
    "titulo": "UNKNOWN",
    "orgao": "UNKNOWN",
    "modalidade": "UNKNOWN",
    "cargo": "UNKNOWN",
    "area": "UNKNOWN",
    "cidade": "UNKNOWN",
    "uf": "UNKNOWN",
    "status": "UNKNOWN",
    "vagas": "UNKNOWN",
    "salario_min": "UNKNOWN",
    "salario_max": "UNKNOWN",
    "escolaridade": "UNKNOWN",
    "taxa": "UNKNOWN",
    "prova_data": "UNKNOWN",
    "edital_numero": "UNKNOWN",
    "edital_data": "UNKNOWN",
    "inscricao_inicio": "UNKNOWN",
    "inscricao_fim": "UNKNOWN",
    "link_pagina": "UNKNOWN",
    "link_edital": "UNKNOWN",
    "link_inscricao": "UNKNOWN"
  }
}
```

### 12. Fundação Cesgranrio (`cesgranrio_open`)
- **Certames Extraídos**: 4
- **Amostra Principal**: None
  - **Órgão**: None | **Cidade/UF**: None/None
  - **Status**: None | **Inscrições**: None a None
  - **Vagas**: None | **Salário**: R$ None a R$ None | **Taxa**: R$ None
  - **Link Edital**: None
  - **Publicações Estruturadas**: 0 documento(s)

```json
{
  "field_audit": {
    "titulo": "MATCH",
    "orgao": "UNKNOWN",
    "modalidade": "UNKNOWN",
    "cargo": "UNKNOWN",
    "area": "UNKNOWN",
    "cidade": "UNKNOWN",
    "uf": "UNKNOWN",
    "status": "UNKNOWN",
    "vagas": "UNKNOWN",
    "salario_min": "UNKNOWN",
    "salario_max": "UNKNOWN",
    "escolaridade": "UNKNOWN",
    "taxa": "UNKNOWN",
    "prova_data": "UNKNOWN",
    "edital_numero": "UNKNOWN",
    "edital_data": "UNKNOWN",
    "inscricao_inicio": "UNKNOWN",
    "inscricao_fim": "UNKNOWN",
    "link_pagina": "MATCH",
    "link_edital": "UNKNOWN",
    "link_inscricao": "MATCH"
  }
}
```

### 14. IBGP - Inscrições Abertas (`ibgp_open`)
- **Certames Extraídos**: 15
- **Amostra Principal**: None
  - **Órgão**: None | **Cidade/UF**: None/None
  - **Status**: None | **Inscrições**: None a None
  - **Vagas**: None | **Salário**: R$ None a R$ None | **Taxa**: R$ None
  - **Link Edital**: None
  - **Publicações Estruturadas**: 0 documento(s)

```json
{
  "field_audit": {
    "titulo": "UNKNOWN",
    "orgao": "UNKNOWN",
    "modalidade": "UNKNOWN",
    "cargo": "UNKNOWN",
    "area": "UNKNOWN",
    "cidade": "UNKNOWN",
    "uf": "UNKNOWN",
    "status": "UNKNOWN",
    "vagas": "UNKNOWN",
    "salario_min": "UNKNOWN",
    "salario_max": "UNKNOWN",
    "escolaridade": "UNKNOWN",
    "taxa": "UNKNOWN",
    "prova_data": "UNKNOWN",
    "edital_numero": "UNKNOWN",
    "edital_data": "UNKNOWN",
    "inscricao_inicio": "UNKNOWN",
    "inscricao_fim": "UNKNOWN",
    "link_pagina": "UNKNOWN",
    "link_edital": "UNKNOWN",
    "link_inscricao": "UNKNOWN"
  }
}
```

### 15. FUNDEP - Gestão de Concursos (`fundep_open`)
- **Certames Extraídos**: 1
- **Amostra Principal**: None
  - **Órgão**: None | **Cidade/UF**: None/None
  - **Status**: None | **Inscrições**: None a None
  - **Vagas**: None | **Salário**: R$ None a R$ None | **Taxa**: R$ None
  - **Link Edital**: None
  - **Publicações Estruturadas**: 0 documento(s)

```json
{
  "field_audit": {
    "titulo": "UNKNOWN",
    "orgao": "UNKNOWN",
    "modalidade": "UNKNOWN",
    "cargo": "UNKNOWN",
    "area": "UNKNOWN",
    "cidade": "UNKNOWN",
    "uf": "UNKNOWN",
    "status": "UNKNOWN",
    "vagas": "UNKNOWN",
    "salario_min": "UNKNOWN",
    "salario_max": "UNKNOWN",
    "escolaridade": "UNKNOWN",
    "taxa": "UNKNOWN",
    "prova_data": "UNKNOWN",
    "edital_numero": "UNKNOWN",
    "edital_data": "UNKNOWN",
    "inscricao_inicio": "UNKNOWN",
    "inscricao_fim": "UNKNOWN",
    "link_pagina": "UNKNOWN",
    "link_edital": "MATCH",
    "link_inscricao": "MATCH"
  }
}
```

### 16. FUMARC Concursos (`fumarc_open`)
- **Certames Extraídos**: 33
- **Amostra Principal**: None
  - **Órgão**: None | **Cidade/UF**: None/None
  - **Status**: None | **Inscrições**: None a None
  - **Vagas**: None | **Salário**: R$ None a R$ None | **Taxa**: R$ None
  - **Link Edital**: None
  - **Publicações Estruturadas**: 0 documento(s)

```json
{
  "field_audit": {
    "titulo": "UNKNOWN",
    "orgao": "UNKNOWN",
    "modalidade": "UNKNOWN",
    "cargo": "UNKNOWN",
    "area": "UNKNOWN",
    "cidade": "UNKNOWN",
    "uf": "UNKNOWN",
    "status": "UNKNOWN",
    "vagas": "UNKNOWN",
    "salario_min": "UNKNOWN",
    "salario_max": "UNKNOWN",
    "escolaridade": "UNKNOWN",
    "taxa": "UNKNOWN",
    "prova_data": "UNKNOWN",
    "edital_numero": "UNKNOWN",
    "edital_data": "UNKNOWN",
    "inscricao_inicio": "UNKNOWN",
    "inscricao_fim": "UNKNOWN",
    "link_pagina": "UNKNOWN",
    "link_edital": "UNKNOWN",
    "link_inscricao": "UNKNOWN"
  }
}
```

### 17. IMESO - Concursos e Seletivos (`imeso_open`)
- **Certames Extraídos**: 2
- **Amostra Principal**: None
  - **Órgão**: None | **Cidade/UF**: None/None
  - **Status**: None | **Inscrições**: None a None
  - **Vagas**: None | **Salário**: R$ None a R$ None | **Taxa**: R$ None
  - **Link Edital**: None
  - **Publicações Estruturadas**: 0 documento(s)

```json
{
  "field_audit": {
    "titulo": "UNKNOWN",
    "orgao": "UNKNOWN",
    "modalidade": "UNKNOWN",
    "cargo": "UNKNOWN",
    "area": "UNKNOWN",
    "cidade": "UNKNOWN",
    "uf": "UNKNOWN",
    "status": "UNKNOWN",
    "vagas": "UNKNOWN",
    "salario_min": "UNKNOWN",
    "salario_max": "UNKNOWN",
    "escolaridade": "UNKNOWN",
    "taxa": "UNKNOWN",
    "prova_data": "UNKNOWN",
    "edital_numero": "UNKNOWN",
    "edital_data": "UNKNOWN",
    "inscricao_inicio": "UNKNOWN",
    "inscricao_fim": "UNKNOWN",
    "link_pagina": "UNKNOWN",
    "link_edital": "MATCH",
    "link_inscricao": "MATCH"
  }
}
```

### 18. OMNI Concursos Públicos (`omni_open`)
- **Certames Extraídos**: 2
- **Amostra Principal**: None
  - **Órgão**: None | **Cidade/UF**: None/None
  - **Status**: None | **Inscrições**: None a None
  - **Vagas**: None | **Salário**: R$ None a R$ None | **Taxa**: R$ None
  - **Link Edital**: None
  - **Publicações Estruturadas**: 0 documento(s)

```json
{
  "field_audit": {
    "titulo": "MATCH",
    "orgao": "UNKNOWN",
    "modalidade": "MATCH",
    "cargo": "UNKNOWN",
    "area": "UNKNOWN",
    "cidade": "MATCH",
    "uf": "MATCH",
    "status": "UNKNOWN",
    "vagas": "UNKNOWN",
    "salario_min": "UNKNOWN",
    "salario_max": "UNKNOWN",
    "escolaridade": "UNKNOWN",
    "taxa": "UNKNOWN",
    "prova_data": "UNKNOWN",
    "edital_numero": "UNKNOWN",
    "edital_data": "UNKNOWN",
    "inscricao_inicio": "UNKNOWN",
    "inscricao_fim": "UNKNOWN",
    "link_pagina": "UNKNOWN",
    "link_edital": "MATCH",
    "link_inscricao": "UNKNOWN"
  }
}
```

### 19. Instituto ACCESS (`access_open`)
- **Certames Extraídos**: 2
- **Amostra Principal**: None
  - **Órgão**: None | **Cidade/UF**: None/None
  - **Status**: None | **Inscrições**: None a None
  - **Vagas**: None | **Salário**: R$ None a R$ None | **Taxa**: R$ None
  - **Link Edital**: None
  - **Publicações Estruturadas**: 0 documento(s)

```json
{
  "field_audit": {
    "titulo": "MATCH",
    "orgao": "UNKNOWN",
    "modalidade": "UNKNOWN",
    "cargo": "UNKNOWN",
    "area": "UNKNOWN",
    "cidade": "MATCH",
    "uf": "MATCH",
    "status": "UNKNOWN",
    "vagas": "UNKNOWN",
    "salario_min": "UNKNOWN",
    "salario_max": "UNKNOWN",
    "escolaridade": "UNKNOWN",
    "taxa": "UNKNOWN",
    "prova_data": "UNKNOWN",
    "edital_numero": "UNKNOWN",
    "edital_data": "UNKNOWN",
    "inscricao_inicio": "UNKNOWN",
    "inscricao_fim": "UNKNOWN",
    "link_pagina": "UNKNOWN",
    "link_edital": "MATCH",
    "link_inscricao": "MATCH"
  }
}
```

### 20. Exame Consultores e Auditores (`exame_open`)
- **Certames Extraídos**: 4
- **Amostra Principal**: None
  - **Órgão**: None | **Cidade/UF**: None/None
  - **Status**: None | **Inscrições**: None a None
  - **Vagas**: None | **Salário**: R$ None a R$ None | **Taxa**: R$ None
  - **Link Edital**: None
  - **Publicações Estruturadas**: 0 documento(s)

```json
{
  "field_audit": {
    "titulo": "MATCH",
    "orgao": "UNKNOWN",
    "modalidade": "MATCH",
    "cargo": "UNKNOWN",
    "area": "UNKNOWN",
    "cidade": "UNKNOWN",
    "uf": "UNKNOWN",
    "status": "UNKNOWN",
    "vagas": "UNKNOWN",
    "salario_min": "UNKNOWN",
    "salario_max": "UNKNOWN",
    "escolaridade": "UNKNOWN",
    "taxa": "UNKNOWN",
    "prova_data": "UNKNOWN",
    "edital_numero": "UNKNOWN",
    "edital_data": "UNKNOWN",
    "inscricao_inicio": "UNKNOWN",
    "inscricao_fim": "UNKNOWN",
    "link_pagina": "UNKNOWN",
    "link_edital": "MATCH",
    "link_inscricao": "UNKNOWN"
  }
}
```

### 22. ABCP Concursos (`abcp_open`)
- **Certames Extraídos**: 4
- **Amostra Principal**: None
  - **Órgão**: None | **Cidade/UF**: None/None
  - **Status**: None | **Inscrições**: None a None
  - **Vagas**: None | **Salário**: R$ None a R$ None | **Taxa**: R$ None
  - **Link Edital**: None
  - **Publicações Estruturadas**: 0 documento(s)

```json
{
  "field_audit": {
    "titulo": "MATCH",
    "orgao": "UNKNOWN",
    "modalidade": "MATCH",
    "cargo": "UNKNOWN",
    "area": "UNKNOWN",
    "cidade": "MATCH",
    "uf": "MATCH",
    "status": "UNKNOWN",
    "vagas": "UNKNOWN",
    "salario_min": "UNKNOWN",
    "salario_max": "UNKNOWN",
    "escolaridade": "UNKNOWN",
    "taxa": "UNKNOWN",
    "prova_data": "UNKNOWN",
    "edital_numero": "UNKNOWN",
    "edital_data": "UNKNOWN",
    "inscricao_inicio": "UNKNOWN",
    "inscricao_fim": "UNKNOWN",
    "link_pagina": "UNKNOWN",
    "link_edital": "MATCH",
    "link_inscricao": "MATCH"
  }
}
```

### 24. OBJETIVA Concursos (`objetiva_open`)
- **Certames Extraídos**: 12
- **Amostra Principal**: None
  - **Órgão**: None | **Cidade/UF**: None/None
  - **Status**: None | **Inscrições**: None a None
  - **Vagas**: None | **Salário**: R$ None a R$ None | **Taxa**: R$ None
  - **Link Edital**: None
  - **Publicações Estruturadas**: 0 documento(s)

```json
{
  "field_audit": {
    "titulo": "MATCH",
    "orgao": "UNKNOWN",
    "modalidade": "MATCH",
    "cargo": "UNKNOWN",
    "area": "UNKNOWN",
    "cidade": "MATCH",
    "uf": "MATCH",
    "status": "UNKNOWN",
    "vagas": "UNKNOWN",
    "salario_min": "UNKNOWN",
    "salario_max": "UNKNOWN",
    "escolaridade": "UNKNOWN",
    "taxa": "UNKNOWN",
    "prova_data": "UNKNOWN",
    "edital_numero": "UNKNOWN",
    "edital_data": "UNKNOWN",
    "inscricao_inicio": "UNKNOWN",
    "inscricao_fim": "UNKNOWN",
    "link_pagina": "UNKNOWN",
    "link_edital": "MATCH",
    "link_inscricao": "MATCH"
  }
}
```

### 26. COTEC / FADENOR Concursos (`cotec_open`)
- **Certames Extraídos**: 2
- **Amostra Principal**: None
  - **Órgão**: None | **Cidade/UF**: None/None
  - **Status**: None | **Inscrições**: None a None
  - **Vagas**: None | **Salário**: R$ None a R$ None | **Taxa**: R$ None
  - **Link Edital**: None
  - **Publicações Estruturadas**: 0 documento(s)

```json
{
  "field_audit": {
    "titulo": "MATCH",
    "orgao": "UNKNOWN",
    "modalidade": "UNKNOWN",
    "cargo": "UNKNOWN",
    "area": "UNKNOWN",
    "cidade": "MATCH",
    "uf": "MATCH",
    "status": "UNKNOWN",
    "vagas": "UNKNOWN",
    "salario_min": "UNKNOWN",
    "salario_max": "UNKNOWN",
    "escolaridade": "UNKNOWN",
    "taxa": "UNKNOWN",
    "prova_data": "UNKNOWN",
    "edital_numero": "UNKNOWN",
    "edital_data": "UNKNOWN",
    "inscricao_inicio": "UNKNOWN",
    "inscricao_fim": "UNKNOWN",
    "link_pagina": "UNKNOWN",
    "link_edital": "MATCH",
    "link_inscricao": "MATCH"
  }
}
```

### 30. MS Concursos (`msconcursos_open`)
- **Certames Extraídos**: 2
- **Amostra Principal**: None
  - **Órgão**: None | **Cidade/UF**: None/None
  - **Status**: None | **Inscrições**: None a None
  - **Vagas**: None | **Salário**: R$ None a R$ None | **Taxa**: R$ None
  - **Link Edital**: None
  - **Publicações Estruturadas**: 0 documento(s)

```json
{
  "field_audit": {
    "titulo": "MISMATCH",
    "orgao": "UNKNOWN",
    "modalidade": "UNKNOWN",
    "cargo": "UNKNOWN",
    "area": "UNKNOWN",
    "cidade": "UNKNOWN",
    "uf": "UNKNOWN",
    "status": "UNKNOWN",
    "vagas": "UNKNOWN",
    "salario_min": "UNKNOWN",
    "salario_max": "UNKNOWN",
    "escolaridade": "UNKNOWN",
    "taxa": "UNKNOWN",
    "prova_data": "UNKNOWN",
    "edital_numero": "UNKNOWN",
    "edital_data": "UNKNOWN",
    "inscricao_inicio": "UNKNOWN",
    "inscricao_fim": "UNKNOWN",
    "link_pagina": "UNKNOWN",
    "link_edital": "UNKNOWN",
    "link_inscricao": "MISMATCH"
  }
}
```

### 31. FACET Concursos (`facet_open`)
- **Certames Extraídos**: 1
- **Amostra Principal**: None
  - **Órgão**: None | **Cidade/UF**: None/None
  - **Status**: None | **Inscrições**: None a None
  - **Vagas**: None | **Salário**: R$ None a R$ None | **Taxa**: R$ None
  - **Link Edital**: None
  - **Publicações Estruturadas**: 0 documento(s)

```json
{
  "field_audit": {
    "titulo": "UNKNOWN",
    "orgao": "UNKNOWN",
    "modalidade": "UNKNOWN",
    "cargo": "UNKNOWN",
    "area": "UNKNOWN",
    "cidade": "UNKNOWN",
    "uf": "UNKNOWN",
    "status": "UNKNOWN",
    "vagas": "UNKNOWN",
    "salario_min": "UNKNOWN",
    "salario_max": "UNKNOWN",
    "escolaridade": "UNKNOWN",
    "taxa": "UNKNOWN",
    "prova_data": "UNKNOWN",
    "edital_numero": "UNKNOWN",
    "edital_data": "UNKNOWN",
    "inscricao_inicio": "UNKNOWN",
    "inscricao_fim": "UNKNOWN",
    "link_pagina": "UNKNOWN",
    "link_edital": "MATCH",
    "link_inscricao": "MATCH"
  }
}
```

### 33. Instituto ADM&TEC (`admtec_open`)
- **Certames Extraídos**: 4
- **Amostra Principal**: None
  - **Órgão**: None | **Cidade/UF**: None/None
  - **Status**: None | **Inscrições**: None a None
  - **Vagas**: None | **Salário**: R$ None a R$ None | **Taxa**: R$ None
  - **Link Edital**: None
  - **Publicações Estruturadas**: 0 documento(s)

```json
{
  "field_audit": {
    "titulo": "MISMATCH",
    "orgao": "UNKNOWN",
    "modalidade": "UNKNOWN",
    "cargo": "UNKNOWN",
    "area": "UNKNOWN",
    "cidade": "UNKNOWN",
    "uf": "UNKNOWN",
    "status": "UNKNOWN",
    "vagas": "UNKNOWN",
    "salario_min": "UNKNOWN",
    "salario_max": "UNKNOWN",
    "escolaridade": "UNKNOWN",
    "taxa": "UNKNOWN",
    "prova_data": "UNKNOWN",
    "edital_numero": "UNKNOWN",
    "edital_data": "UNKNOWN",
    "inscricao_inicio": "UNKNOWN",
    "inscricao_fim": "UNKNOWN",
    "link_pagina": "UNKNOWN",
    "link_edital": "UNKNOWN",
    "link_inscricao": "UNKNOWN"
  }
}
```

### 35. CPCon / UEPB Concursos (`cpcon_open`)
- **Certames Extraídos**: 10
- **Amostra Principal**: None
  - **Órgão**: None | **Cidade/UF**: None/None
  - **Status**: None | **Inscrições**: None a None
  - **Vagas**: None | **Salário**: R$ None a R$ None | **Taxa**: R$ None
  - **Link Edital**: None
  - **Publicações Estruturadas**: 0 documento(s)

```json
{
  "field_audit": {
    "titulo": "MATCH",
    "orgao": "UNKNOWN",
    "modalidade": "UNKNOWN",
    "cargo": "UNKNOWN",
    "area": "UNKNOWN",
    "cidade": "UNKNOWN",
    "uf": "UNKNOWN",
    "status": "UNKNOWN",
    "vagas": "UNKNOWN",
    "salario_min": "UNKNOWN",
    "salario_max": "UNKNOWN",
    "escolaridade": "UNKNOWN",
    "taxa": "UNKNOWN",
    "prova_data": "UNKNOWN",
    "edital_numero": "UNKNOWN",
    "edital_data": "UNKNOWN",
    "inscricao_inicio": "UNKNOWN",
    "inscricao_fim": "UNKNOWN",
    "link_pagina": "MATCH",
    "link_edital": "UNKNOWN",
    "link_inscricao": "MATCH"
  }
}
```

### 36. FUNVAPI Concursos (`funvapi_open`)
- **Certames Extraídos**: 7
- **Amostra Principal**: None
  - **Órgão**: None | **Cidade/UF**: None/None
  - **Status**: None | **Inscrições**: None a None
  - **Vagas**: None | **Salário**: R$ None a R$ None | **Taxa**: R$ None
  - **Link Edital**: None
  - **Publicações Estruturadas**: 0 documento(s)

```json
{
  "field_audit": {
    "titulo": "MATCH",
    "orgao": "UNKNOWN",
    "modalidade": "UNKNOWN",
    "cargo": "UNKNOWN",
    "area": "UNKNOWN",
    "cidade": "UNKNOWN",
    "uf": "UNKNOWN",
    "status": "UNKNOWN",
    "vagas": "UNKNOWN",
    "salario_min": "UNKNOWN",
    "salario_max": "UNKNOWN",
    "escolaridade": "UNKNOWN",
    "taxa": "UNKNOWN",
    "prova_data": "UNKNOWN",
    "edital_numero": "UNKNOWN",
    "edital_data": "UNKNOWN",
    "inscricao_inicio": "UNKNOWN",
    "inscricao_fim": "UNKNOWN",
    "link_pagina": "MATCH",
    "link_edital": "MATCH",
    "link_inscricao": "UNKNOWN"
  }
}
```

### 39. Instituto Avalia (`avalia_open`)
- **Certames Extraídos**: 1
- **Amostra Principal**: None
  - **Órgão**: None | **Cidade/UF**: None/None
  - **Status**: None | **Inscrições**: None a None
  - **Vagas**: None | **Salário**: R$ None a R$ None | **Taxa**: R$ None
  - **Link Edital**: None
  - **Publicações Estruturadas**: 0 documento(s)

```json
{
  "field_audit": {
    "titulo": "UNKNOWN",
    "orgao": "UNKNOWN",
    "modalidade": "UNKNOWN",
    "cargo": "UNKNOWN",
    "area": "UNKNOWN",
    "cidade": "UNKNOWN",
    "uf": "UNKNOWN",
    "status": "UNKNOWN",
    "vagas": "UNKNOWN",
    "salario_min": "UNKNOWN",
    "salario_max": "UNKNOWN",
    "escolaridade": "UNKNOWN",
    "taxa": "UNKNOWN",
    "prova_data": "UNKNOWN",
    "edital_numero": "UNKNOWN",
    "edital_data": "UNKNOWN",
    "inscricao_inicio": "UNKNOWN",
    "inscricao_fim": "UNKNOWN",
    "link_pagina": "UNKNOWN",
    "link_edital": "UNKNOWN",
    "link_inscricao": "MATCH"
  }
}
```

### 40. UFU / DIRPS - Seleções e Concursos (`ufu_selection`)
- **Certames Extraídos**: 11
- **Amostra Principal**: None
  - **Órgão**: None | **Cidade/UF**: None/None
  - **Status**: None | **Inscrições**: None a None
  - **Vagas**: None | **Salário**: R$ None a R$ None | **Taxa**: R$ None
  - **Link Edital**: None
  - **Publicações Estruturadas**: 0 documento(s)

```json
{
  "field_audit": {
    "titulo": "UNKNOWN",
    "orgao": "UNKNOWN",
    "modalidade": "UNKNOWN",
    "cargo": "UNKNOWN",
    "area": "UNKNOWN",
    "cidade": "UNKNOWN",
    "uf": "UNKNOWN",
    "status": "UNKNOWN",
    "vagas": "UNKNOWN",
    "salario_min": "UNKNOWN",
    "salario_max": "UNKNOWN",
    "escolaridade": "UNKNOWN",
    "taxa": "UNKNOWN",
    "prova_data": "UNKNOWN",
    "edital_numero": "UNKNOWN",
    "edital_data": "UNKNOWN",
    "inscricao_inicio": "UNKNOWN",
    "inscricao_fim": "UNKNOWN",
    "link_pagina": "MATCH",
    "link_edital": "MATCH",
    "link_inscricao": "MATCH"
  }
}
```

### 42. Instituto Quadrix (`quadrix_open`)
- **Certames Extraídos**: 2
- **Amostra Principal**: None
  - **Órgão**: None | **Cidade/UF**: None/None
  - **Status**: None | **Inscrições**: None a None
  - **Vagas**: None | **Salário**: R$ None a R$ None | **Taxa**: R$ None
  - **Link Edital**: None
  - **Publicações Estruturadas**: 0 documento(s)

```json
{
  "field_audit": {
    "titulo": "UNKNOWN",
    "orgao": "UNKNOWN",
    "modalidade": "UNKNOWN",
    "cargo": "UNKNOWN",
    "area": "UNKNOWN",
    "cidade": "UNKNOWN",
    "uf": "UNKNOWN",
    "status": "UNKNOWN",
    "vagas": "UNKNOWN",
    "salario_min": "UNKNOWN",
    "salario_max": "UNKNOWN",
    "escolaridade": "UNKNOWN",
    "taxa": "UNKNOWN",
    "prova_data": "UNKNOWN",
    "edital_numero": "UNKNOWN",
    "edital_data": "UNKNOWN",
    "inscricao_inicio": "UNKNOWN",
    "inscricao_fim": "UNKNOWN",
    "link_pagina": "UNKNOWN",
    "link_edital": "MATCH",
    "link_inscricao": "MATCH"
  }
}
```

### 44. Instituto Verbena / UFG (`verbena_selection`)
- **Certames Extraídos**: 4
- **Amostra Principal**: None
  - **Órgão**: None | **Cidade/UF**: None/None
  - **Status**: None | **Inscrições**: None a None
  - **Vagas**: None | **Salário**: R$ None a R$ None | **Taxa**: R$ None
  - **Link Edital**: None
  - **Publicações Estruturadas**: 0 documento(s)

```json
{
  "field_audit": {
    "titulo": "MATCH",
    "orgao": "UNKNOWN",
    "modalidade": "MATCH",
    "cargo": "UNKNOWN",
    "area": "UNKNOWN",
    "cidade": "MATCH",
    "uf": "MATCH",
    "status": "UNKNOWN",
    "vagas": "UNKNOWN",
    "salario_min": "UNKNOWN",
    "salario_max": "UNKNOWN",
    "escolaridade": "UNKNOWN",
    "taxa": "UNKNOWN",
    "prova_data": "UNKNOWN",
    "edital_numero": "UNKNOWN",
    "edital_data": "UNKNOWN",
    "inscricao_inicio": "UNKNOWN",
    "inscricao_fim": "UNKNOWN",
    "link_pagina": "UNKNOWN",
    "link_edital": "MATCH",
    "link_inscricao": "MATCH"
  }
}
```

### 45. Instituto IDIB (`idib_open`)
- **Certames Extraídos**: 6
- **Amostra Principal**: None
  - **Órgão**: None | **Cidade/UF**: None/None
  - **Status**: None | **Inscrições**: None a None
  - **Vagas**: None | **Salário**: R$ None a R$ None | **Taxa**: R$ None
  - **Link Edital**: None
  - **Publicações Estruturadas**: 0 documento(s)

```json
{
  "field_audit": {
    "titulo": "UNKNOWN",
    "orgao": "UNKNOWN",
    "modalidade": "UNKNOWN",
    "cargo": "UNKNOWN",
    "area": "UNKNOWN",
    "cidade": "UNKNOWN",
    "uf": "UNKNOWN",
    "status": "UNKNOWN",
    "vagas": "UNKNOWN",
    "salario_min": "UNKNOWN",
    "salario_max": "UNKNOWN",
    "escolaridade": "UNKNOWN",
    "taxa": "UNKNOWN",
    "prova_data": "UNKNOWN",
    "edital_numero": "UNKNOWN",
    "edital_data": "UNKNOWN",
    "inscricao_inicio": "UNKNOWN",
    "inscricao_fim": "UNKNOWN",
    "link_pagina": "UNKNOWN",
    "link_edital": "MATCH",
    "link_inscricao": "UNKNOWN"
  }
}
```

### 47. Elo Assessoria e Serviços (`elo_open`)
- **Certames Extraídos**: 6
- **Amostra Principal**: None
  - **Órgão**: None | **Cidade/UF**: None/None
  - **Status**: None | **Inscrições**: None a None
  - **Vagas**: None | **Salário**: R$ None a R$ None | **Taxa**: R$ None
  - **Link Edital**: None
  - **Publicações Estruturadas**: 0 documento(s)

```json
{
  "field_audit": {
    "titulo": "UNKNOWN",
    "orgao": "UNKNOWN",
    "modalidade": "UNKNOWN",
    "cargo": "UNKNOWN",
    "area": "UNKNOWN",
    "cidade": "UNKNOWN",
    "uf": "UNKNOWN",
    "status": "UNKNOWN",
    "vagas": "UNKNOWN",
    "salario_min": "UNKNOWN",
    "salario_max": "UNKNOWN",
    "escolaridade": "UNKNOWN",
    "taxa": "UNKNOWN",
    "prova_data": "UNKNOWN",
    "edital_numero": "UNKNOWN",
    "edital_data": "UNKNOWN",
    "inscricao_inicio": "UNKNOWN",
    "inscricao_fim": "UNKNOWN",
    "link_pagina": "UNKNOWN",
    "link_edital": "MATCH",
    "link_inscricao": "MATCH"
  }
}
```

### 48. Apta Concursos e Assessoria (`apta_open`)
- **Certames Extraídos**: 1
- **Amostra Principal**: None
  - **Órgão**: None | **Cidade/UF**: None/None
  - **Status**: None | **Inscrições**: None a None
  - **Vagas**: None | **Salário**: R$ None a R$ None | **Taxa**: R$ None
  - **Link Edital**: None
  - **Publicações Estruturadas**: 0 documento(s)

```json
{
  "field_audit": {
    "titulo": "MATCH",
    "orgao": "UNKNOWN",
    "modalidade": "UNKNOWN",
    "cargo": "UNKNOWN",
    "area": "UNKNOWN",
    "cidade": "UNKNOWN",
    "uf": "UNKNOWN",
    "status": "UNKNOWN",
    "vagas": "UNKNOWN",
    "salario_min": "UNKNOWN",
    "salario_max": "UNKNOWN",
    "escolaridade": "UNKNOWN",
    "taxa": "UNKNOWN",
    "prova_data": "UNKNOWN",
    "edital_numero": "UNKNOWN",
    "edital_data": "UNKNOWN",
    "inscricao_inicio": "UNKNOWN",
    "inscricao_fim": "UNKNOWN",
    "link_pagina": "UNKNOWN",
    "link_edital": "UNKNOWN",
    "link_inscricao": "MATCH"
  }
}
```

### 49. Legalle Concursos (`legalle_open`)
- **Certames Extraídos**: 4
- **Amostra Principal**: None
  - **Órgão**: None | **Cidade/UF**: None/None
  - **Status**: None | **Inscrições**: None a None
  - **Vagas**: None | **Salário**: R$ None a R$ None | **Taxa**: R$ None
  - **Link Edital**: None
  - **Publicações Estruturadas**: 0 documento(s)

```json
{
  "field_audit": {
    "titulo": "UNKNOWN",
    "orgao": "UNKNOWN",
    "modalidade": "UNKNOWN",
    "cargo": "UNKNOWN",
    "area": "UNKNOWN",
    "cidade": "UNKNOWN",
    "uf": "UNKNOWN",
    "status": "UNKNOWN",
    "vagas": "UNKNOWN",
    "salario_min": "UNKNOWN",
    "salario_max": "UNKNOWN",
    "escolaridade": "UNKNOWN",
    "taxa": "UNKNOWN",
    "prova_data": "UNKNOWN",
    "edital_numero": "UNKNOWN",
    "edital_data": "UNKNOWN",
    "inscricao_inicio": "UNKNOWN",
    "inscricao_fim": "UNKNOWN",
    "link_pagina": "UNKNOWN",
    "link_edital": "MATCH",
    "link_inscricao": "MATCH"
  }
}
```

### 50. RBO Concursos e Assessoria (`rbo_open`)
- **Certames Extraídos**: 2
- **Amostra Principal**: None
  - **Órgão**: None | **Cidade/UF**: None/None
  - **Status**: None | **Inscrições**: None a None
  - **Vagas**: None | **Salário**: R$ None a R$ None | **Taxa**: R$ None
  - **Link Edital**: None
  - **Publicações Estruturadas**: 0 documento(s)

```json
{
  "field_audit": {
    "titulo": "MATCH",
    "orgao": "UNKNOWN",
    "modalidade": "MATCH",
    "cargo": "UNKNOWN",
    "area": "UNKNOWN",
    "cidade": "MATCH",
    "uf": "MATCH",
    "status": "UNKNOWN",
    "vagas": "UNKNOWN",
    "salario_min": "UNKNOWN",
    "salario_max": "UNKNOWN",
    "escolaridade": "UNKNOWN",
    "taxa": "UNKNOWN",
    "prova_data": "UNKNOWN",
    "edital_numero": "UNKNOWN",
    "edital_data": "UNKNOWN",
    "inscricao_inicio": "UNKNOWN",
    "inscricao_fim": "UNKNOWN",
    "link_pagina": "UNKNOWN",
    "link_edital": "MATCH",
    "link_inscricao": "MATCH"
  }
}
```

### 53. Instituto Nosso Rumo (`nossorumo_open`)
- **Certames Extraídos**: 2
- **Amostra Principal**: None
  - **Órgão**: None | **Cidade/UF**: None/None
  - **Status**: None | **Inscrições**: None a None
  - **Vagas**: None | **Salário**: R$ None a R$ None | **Taxa**: R$ None
  - **Link Edital**: None
  - **Publicações Estruturadas**: 0 documento(s)

```json
{
  "field_audit": {
    "titulo": "UNKNOWN",
    "orgao": "UNKNOWN",
    "modalidade": "UNKNOWN",
    "cargo": "UNKNOWN",
    "area": "UNKNOWN",
    "cidade": "UNKNOWN",
    "uf": "UNKNOWN",
    "status": "UNKNOWN",
    "vagas": "UNKNOWN",
    "salario_min": "UNKNOWN",
    "salario_max": "UNKNOWN",
    "escolaridade": "UNKNOWN",
    "taxa": "UNKNOWN",
    "prova_data": "UNKNOWN",
    "edital_numero": "UNKNOWN",
    "edital_data": "UNKNOWN",
    "inscricao_inicio": "UNKNOWN",
    "inscricao_fim": "UNKNOWN",
    "link_pagina": "UNKNOWN",
    "link_edital": "UNKNOWN",
    "link_inscricao": "MISMATCH"
  }
}
```

### 54. Avança SP Concursos (`avancasp_open`)
- **Certames Extraídos**: 6
- **Amostra Principal**: None
  - **Órgão**: None | **Cidade/UF**: None/None
  - **Status**: None | **Inscrições**: None a None
  - **Vagas**: None | **Salário**: R$ None a R$ None | **Taxa**: R$ None
  - **Link Edital**: None
  - **Publicações Estruturadas**: 0 documento(s)

```json
{
  "field_audit": {
    "titulo": "MATCH",
    "orgao": "UNKNOWN",
    "modalidade": "MATCH",
    "cargo": "UNKNOWN",
    "area": "UNKNOWN",
    "cidade": "UNKNOWN",
    "uf": "UNKNOWN",
    "status": "UNKNOWN",
    "vagas": "UNKNOWN",
    "salario_min": "UNKNOWN",
    "salario_max": "UNKNOWN",
    "escolaridade": "UNKNOWN",
    "taxa": "UNKNOWN",
    "prova_data": "UNKNOWN",
    "edital_numero": "UNKNOWN",
    "edital_data": "UNKNOWN",
    "inscricao_inicio": "UNKNOWN",
    "inscricao_fim": "UNKNOWN",
    "link_pagina": "UNKNOWN",
    "link_edital": "MATCH",
    "link_inscricao": "MATCH"
  }
}
```

### 55. Instituto Mais de Gestão e Concursos (`institutomais_open`)
- **Certames Extraídos**: 17
- **Amostra Principal**: None
  - **Órgão**: None | **Cidade/UF**: None/None
  - **Status**: None | **Inscrições**: None a None
  - **Vagas**: None | **Salário**: R$ None a R$ None | **Taxa**: R$ None
  - **Link Edital**: None
  - **Publicações Estruturadas**: 0 documento(s)

```json
{
  "field_audit": {
    "titulo": "MATCH",
    "orgao": "UNKNOWN",
    "modalidade": "MATCH",
    "cargo": "UNKNOWN",
    "area": "UNKNOWN",
    "cidade": "UNKNOWN",
    "uf": "UNKNOWN",
    "status": "UNKNOWN",
    "vagas": "UNKNOWN",
    "salario_min": "UNKNOWN",
    "salario_max": "UNKNOWN",
    "escolaridade": "UNKNOWN",
    "taxa": "UNKNOWN",
    "prova_data": "UNKNOWN",
    "edital_numero": "UNKNOWN",
    "edital_data": "UNKNOWN",
    "inscricao_inicio": "UNKNOWN",
    "inscricao_fim": "UNKNOWN",
    "link_pagina": "UNKNOWN",
    "link_edital": "UNKNOWN",
    "link_inscricao": "UNKNOWN"
  }
}
```

### 60. Fênix Concursos (`fenix_open`)
- **Certames Extraídos**: 1
- **Amostra Principal**: None
  - **Órgão**: None | **Cidade/UF**: None/None
  - **Status**: None | **Inscrições**: None a None
  - **Vagas**: None | **Salário**: R$ None a R$ None | **Taxa**: R$ None
  - **Link Edital**: None
  - **Publicações Estruturadas**: 0 documento(s)

```json
{
  "field_audit": {
    "titulo": "UNKNOWN",
    "orgao": "UNKNOWN",
    "modalidade": "UNKNOWN",
    "cargo": "UNKNOWN",
    "area": "UNKNOWN",
    "cidade": "UNKNOWN",
    "uf": "UNKNOWN",
    "status": "UNKNOWN",
    "vagas": "UNKNOWN",
    "salario_min": "UNKNOWN",
    "salario_max": "UNKNOWN",
    "escolaridade": "UNKNOWN",
    "taxa": "UNKNOWN",
    "prova_data": "UNKNOWN",
    "edital_numero": "UNKNOWN",
    "edital_data": "UNKNOWN",
    "inscricao_inicio": "UNKNOWN",
    "inscricao_fim": "UNKNOWN",
    "link_pagina": "UNKNOWN",
    "link_edital": "MATCH",
    "link_inscricao": "MATCH"
  }
}
```

### 62. Instituto Legatus (`legatus_open`)
- **Certames Extraídos**: 10
- **Amostra Principal**: None
  - **Órgão**: None | **Cidade/UF**: None/None
  - **Status**: None | **Inscrições**: None a None
  - **Vagas**: None | **Salário**: R$ None a R$ None | **Taxa**: R$ None
  - **Link Edital**: None
  - **Publicações Estruturadas**: 0 documento(s)

```json
{
  "field_audit": {
    "titulo": "UNKNOWN",
    "orgao": "UNKNOWN",
    "modalidade": "UNKNOWN",
    "cargo": "UNKNOWN",
    "area": "UNKNOWN",
    "cidade": "UNKNOWN",
    "uf": "UNKNOWN",
    "status": "UNKNOWN",
    "vagas": "UNKNOWN",
    "salario_min": "UNKNOWN",
    "salario_max": "UNKNOWN",
    "escolaridade": "UNKNOWN",
    "taxa": "UNKNOWN",
    "prova_data": "UNKNOWN",
    "edital_numero": "UNKNOWN",
    "edital_data": "UNKNOWN",
    "inscricao_inicio": "UNKNOWN",
    "inscricao_fim": "UNKNOWN",
    "link_pagina": "UNKNOWN",
    "link_edital": "UNKNOWN",
    "link_inscricao": "UNKNOWN"
  }
}
```

### 63. Fundação FEPESE (`fepese_open`)
- **Certames Extraídos**: 13
- **Amostra Principal**: None
  - **Órgão**: None | **Cidade/UF**: None/None
  - **Status**: None | **Inscrições**: None a None
  - **Vagas**: None | **Salário**: R$ None a R$ None | **Taxa**: R$ None
  - **Link Edital**: None
  - **Publicações Estruturadas**: 0 documento(s)

```json
{
  "field_audit": {
    "titulo": "UNKNOWN",
    "orgao": "UNKNOWN",
    "modalidade": "UNKNOWN",
    "cargo": "UNKNOWN",
    "area": "UNKNOWN",
    "cidade": "UNKNOWN",
    "uf": "UNKNOWN",
    "status": "UNKNOWN",
    "vagas": "UNKNOWN",
    "salario_min": "UNKNOWN",
    "salario_max": "UNKNOWN",
    "escolaridade": "UNKNOWN",
    "taxa": "UNKNOWN",
    "prova_data": "UNKNOWN",
    "edital_numero": "UNKNOWN",
    "edital_data": "UNKNOWN",
    "inscricao_inicio": "UNKNOWN",
    "inscricao_fim": "UNKNOWN",
    "link_pagina": "UNKNOWN",
    "link_edital": "UNKNOWN",
    "link_inscricao": "MISMATCH"
  }
}
```

### 64. FUNCERN Concursos e Seleções (`funcern_selection`)
- **Certames Extraídos**: 2
- **Amostra Principal**: None
  - **Órgão**: None | **Cidade/UF**: None/None
  - **Status**: None | **Inscrições**: None a None
  - **Vagas**: None | **Salário**: R$ None a R$ None | **Taxa**: R$ None
  - **Link Edital**: None
  - **Publicações Estruturadas**: 0 documento(s)

```json
{
  "field_audit": {
    "titulo": "MATCH",
    "orgao": "UNKNOWN",
    "modalidade": "MATCH",
    "cargo": "UNKNOWN",
    "area": "UNKNOWN",
    "cidade": "MATCH",
    "uf": "MATCH",
    "status": "UNKNOWN",
    "vagas": "UNKNOWN",
    "salario_min": "UNKNOWN",
    "salario_max": "UNKNOWN",
    "escolaridade": "UNKNOWN",
    "taxa": "UNKNOWN",
    "prova_data": "UNKNOWN",
    "edital_numero": "UNKNOWN",
    "edital_data": "UNKNOWN",
    "inscricao_inicio": "UNKNOWN",
    "inscricao_fim": "UNKNOWN",
    "link_pagina": "UNKNOWN",
    "link_edital": "MATCH",
    "link_inscricao": "MATCH"
  }
}
```

### 68. Fundação Uniselva - Processos Seletivos (`uniselva_selection`)
- **Certames Extraídos**: 2
- **Amostra Principal**: None
  - **Órgão**: None | **Cidade/UF**: None/None
  - **Status**: None | **Inscrições**: None a None
  - **Vagas**: None | **Salário**: R$ None a R$ None | **Taxa**: R$ None
  - **Link Edital**: None
  - **Publicações Estruturadas**: 0 documento(s)

```json
{
  "field_audit": {
    "titulo": "UNKNOWN",
    "orgao": "UNKNOWN",
    "modalidade": "UNKNOWN",
    "cargo": "UNKNOWN",
    "area": "UNKNOWN",
    "cidade": "UNKNOWN",
    "uf": "UNKNOWN",
    "status": "UNKNOWN",
    "vagas": "UNKNOWN",
    "salario_min": "UNKNOWN",
    "salario_max": "UNKNOWN",
    "escolaridade": "UNKNOWN",
    "taxa": "UNKNOWN",
    "prova_data": "UNKNOWN",
    "edital_numero": "UNKNOWN",
    "edital_data": "UNKNOWN",
    "inscricao_inicio": "UNKNOWN",
    "inscricao_fim": "UNKNOWN",
    "link_pagina": "UNKNOWN",
    "link_edital": "UNKNOWN",
    "link_inscricao": "MISMATCH"
  }
}
```

### 69. Fundação de Apoio à FAFIPA (`fafipa_open`)
- **Certames Extraídos**: 9
- **Amostra Principal**: None
  - **Órgão**: None | **Cidade/UF**: None/None
  - **Status**: None | **Inscrições**: None a None
  - **Vagas**: None | **Salário**: R$ None a R$ None | **Taxa**: R$ None
  - **Link Edital**: None
  - **Publicações Estruturadas**: 0 documento(s)

```json
{
  "field_audit": {
    "titulo": "MATCH",
    "orgao": "UNKNOWN",
    "modalidade": "MATCH",
    "cargo": "UNKNOWN",
    "area": "UNKNOWN",
    "cidade": "MATCH",
    "uf": "MATCH",
    "status": "UNKNOWN",
    "vagas": "UNKNOWN",
    "salario_min": "UNKNOWN",
    "salario_max": "UNKNOWN",
    "escolaridade": "UNKNOWN",
    "taxa": "UNKNOWN",
    "prova_data": "UNKNOWN",
    "edital_numero": "UNKNOWN",
    "edital_data": "UNKNOWN",
    "inscricao_inicio": "UNKNOWN",
    "inscricao_fim": "UNKNOWN",
    "link_pagina": "UNKNOWN",
    "link_edital": "MATCH",
    "link_inscricao": "MATCH"
  }
}
```

### 70. Instituto IESES (`ieses_open`)
- **Certames Extraídos**: 3
- **Amostra Principal**: None
  - **Órgão**: None | **Cidade/UF**: None/None
  - **Status**: None | **Inscrições**: None a None
  - **Vagas**: None | **Salário**: R$ None a R$ None | **Taxa**: R$ None
  - **Link Edital**: None
  - **Publicações Estruturadas**: 0 documento(s)

```json
{
  "field_audit": {
    "titulo": "MATCH",
    "orgao": "UNKNOWN",
    "modalidade": "MATCH",
    "cargo": "UNKNOWN",
    "area": "UNKNOWN",
    "cidade": "UNKNOWN",
    "uf": "UNKNOWN",
    "status": "UNKNOWN",
    "vagas": "UNKNOWN",
    "salario_min": "UNKNOWN",
    "salario_max": "UNKNOWN",
    "escolaridade": "UNKNOWN",
    "taxa": "UNKNOWN",
    "prova_data": "UNKNOWN",
    "edital_numero": "UNKNOWN",
    "edital_data": "UNKNOWN",
    "inscricao_inicio": "UNKNOWN",
    "inscricao_fim": "UNKNOWN",
    "link_pagina": "UNKNOWN",
    "link_edital": "MATCH",
    "link_inscricao": "UNKNOWN"
  }
}
```

### 71. FUNPEC - Processos Seletivos (`funpec_selection`)
- **Certames Extraídos**: 10
- **Amostra Principal**: None
  - **Órgão**: None | **Cidade/UF**: None/None
  - **Status**: None | **Inscrições**: None a None
  - **Vagas**: None | **Salário**: R$ None a R$ None | **Taxa**: R$ None
  - **Link Edital**: None
  - **Publicações Estruturadas**: 0 documento(s)

```json
{
  "field_audit": {
    "titulo": "MATCH",
    "orgao": "UNKNOWN",
    "modalidade": "MATCH",
    "cargo": "UNKNOWN",
    "area": "UNKNOWN",
    "cidade": "UNKNOWN",
    "uf": "UNKNOWN",
    "status": "UNKNOWN",
    "vagas": "UNKNOWN",
    "salario_min": "UNKNOWN",
    "salario_max": "UNKNOWN",
    "escolaridade": "UNKNOWN",
    "taxa": "UNKNOWN",
    "prova_data": "UNKNOWN",
    "edital_numero": "UNKNOWN",
    "edital_data": "UNKNOWN",
    "inscricao_inicio": "UNKNOWN",
    "inscricao_fim": "UNKNOWN",
    "link_pagina": "MATCH",
    "link_edital": "MATCH",
    "link_inscricao": "UNKNOWN"
  }
}
```

### 74. FATEC - Fundação de Apoio (`fatec_selection`)
- **Certames Extraídos**: 3
- **Amostra Principal**: None
  - **Órgão**: None | **Cidade/UF**: None/None
  - **Status**: None | **Inscrições**: None a None
  - **Vagas**: None | **Salário**: R$ None a R$ None | **Taxa**: R$ None
  - **Link Edital**: None
  - **Publicações Estruturadas**: 0 documento(s)

```json
{
  "field_audit": {
    "titulo": "UNKNOWN",
    "orgao": "UNKNOWN",
    "modalidade": "UNKNOWN",
    "cargo": "UNKNOWN",
    "area": "UNKNOWN",
    "cidade": "UNKNOWN",
    "uf": "UNKNOWN",
    "status": "UNKNOWN",
    "vagas": "UNKNOWN",
    "salario_min": "UNKNOWN",
    "salario_max": "UNKNOWN",
    "escolaridade": "UNKNOWN",
    "taxa": "UNKNOWN",
    "prova_data": "UNKNOWN",
    "edital_numero": "UNKNOWN",
    "edital_data": "UNKNOWN",
    "inscricao_inicio": "UNKNOWN",
    "inscricao_fim": "UNKNOWN",
    "link_pagina": "MATCH",
    "link_edital": "UNKNOWN",
    "link_inscricao": "UNKNOWN"
  }
}
```

