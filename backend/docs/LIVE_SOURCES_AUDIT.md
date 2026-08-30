# Auditoria LIVE das 99 fontes do MASTER_SOURCES

> Gerado em: 2026-08-30T13:26:49.790033+00:00  
> Fontes: 99  
> Duração: 674.3s

## Resumo separado

### CRAWLER STATUS

| Status | Quantidade |
|---|---:|
| `success` | 38 |
| `empty_valid` | 19 |
| `blocked` | 3 |
| `failed` | 4 |
| `degraded` | 35 |

### VERIFICATION STATUS

| Status | Quantidade |
|---|---:|
| `VERIFIED` | 8 |
| `EMPTY_VERIFIED` | 17 |
| `BLOCKED` | 5 |
| `FAILED_EXTERNAL` | 4 |
| `PARTIAL` | 0 |
| `BROKEN` | 0 |
| `NOT_AUDITED` | 65 |

- Candidatos encontrados: 578
- Processados: 265
- Visíveis independentemente: 541

## Política de evidência

A auditoria compara `expected` observado no site/PDF oficial com `actual` retornado pelo crawler. Campo presente apenas em `actual` é `UNKNOWN`; nunca é `MATCH`. `visible_valid_items` é uma observação independente e não é calculado a partir de `processed`.

## Matriz das fontes

| # | Fonte | `source_type` | Crawler | Verificação | Visíveis | Candidatos | Processados |
|---:|---|---|---|---|---:|---:|---:|
| 01 | IBFC - Inscrições Abertas | `ibfc_open` | `empty_valid` | `EMPTY_VERIFIED` | UNKNOWN | 0 | 0 |
| 02 | IDECAN - Concursos | `idecan_open` | `empty_valid` | `EMPTY_VERIFIED` | 5 | 0 | 0 |
| 03 | Instituto AOCP - Concursos | `aocp_open` | `blocked` | `BLOCKED` | UNKNOWN | 0 | 0 |
| 04 | CONSULPAM Concursos | `consulpam_open` | `success` | `NOT_AUDITED` | 9 | 25 | 9 |
| 05 | IBAM Concursos | `ibam_open` | `success` | `NOT_AUDITED` | UNKNOWN | 30 | 26 |
| 06 | IBADE Concursos | `ibade_open` | `success` | `NOT_AUDITED` | 6 | 6 | 6 |
| 07 | CONSULPLAN / Instituto Consulplan | `consulplan_open` | `empty_valid` | `BLOCKED` | UNKNOWN | 0 | 0 |
| 08 | SEPROD Concursos | `seprod_open` | `degraded` | `NOT_AUDITED` | UNKNOWN | 0 | 0 |
| 09 | Fundação Carlos Chagas - FCC | `fcc_open` | `empty_valid` | `EMPTY_VERIFIED` | 19 | 30 | 0 |
| 10 | FGV Conhecimento Concursos | `fgv_open` | `success` | `NOT_AUDITED` | 33 | 30 | 4 |
| 11 | Cebraspe Concursos | `cebraspe_open` | `success` | `NOT_AUDITED` | UNKNOWN | 6 | 6 |
| 12 | Fundação Cesgranrio | `cesgranrio_open` | `degraded` | `NOT_AUDITED` | 4 | 4 | 0 |
| 13 | IDCAP Concursos | `idcap_open` | `empty_valid` | `EMPTY_VERIFIED` | 60 | 25 | 0 |
| 14 | IBGP - Inscrições Abertas | `ibgp_open` | `success` | `NOT_AUDITED` | UNKNOWN | 15 | 15 |
| 15 | FUNDEP - Gestão de Concursos | `fundep_open` | `success` | `NOT_AUDITED` | 1 | 2 | 1 |
| 16 | FUMARC Concursos | `fumarc_open` | `success` | `NOT_AUDITED` | UNKNOWN | 34 | 33 |
| 17 | IMESO - Concursos e Seletivos | `imeso_open` | `success` | `NOT_AUDITED` | 2 | 2 | 2 |
| 18 | OMNI Concursos Públicos | `omni_open` | `success` | `VERIFIED` | 2 | 2 | 2 |
| 19 | Instituto ACCESS | `access_open` | `success` | `VERIFIED` | 2 | 2 | 2 |
| 20 | Exame Consultores e Auditores | `exame_open` | `success` | `NOT_AUDITED` | 4 | 6 | 4 |
| 21 | EPL Concursos | `epl_open` | `empty_valid` | `EMPTY_VERIFIED` | UNKNOWN | 0 | 0 |
| 22 | ABCP Concursos | `abcp_open` | `success` | `VERIFIED` | 4 | 4 | 4 |
| 23 | Instituto UniFil | `unifil_open` | `blocked` | `BLOCKED` | UNKNOWN | 0 | 0 |
| 24 | OBJETIVA Concursos | `objetiva_open` | `success` | `VERIFIED` | 12 | 12 | 12 |
| 25 | Leandro Ferreira & Consultoria | `leandroferreira_open` | `failed` | `FAILED_EXTERNAL` | UNKNOWN | 0 | 0 |
| 26 | COTEC / FADENOR Concursos | `cotec_open` | `success` | `VERIFIED` | 2 | 2 | 2 |
| 27 | Instituto Águia Concursos | `aguia_open` | `empty_valid` | `EMPTY_VERIFIED` | 28 | 25 | 0 |
| 28 | IUDS Concursos | `iuds_open` | `degraded` | `NOT_AUDITED` | UNKNOWN | 0 | 0 |
| 29 | Reis & Reis Auditores Associados | `reisesreis_open` | `degraded` | `NOT_AUDITED` | UNKNOWN | 0 | 0 |
| 30 | MS Concursos | `msconcursos_open` | `success` | `NOT_AUDITED` | 29 | 25 | 2 |
| 31 | FACET Concursos | `facet_open` | `empty_valid` | `EMPTY_VERIFIED` | 1 | 25 | 0 |
| 32 | EDUCA PB Concursos | `educapb_open` | `degraded` | `NOT_AUDITED` | UNKNOWN | 0 | 0 |
| 33 | Instituto ADM&TEC | `admtec_open` | `success` | `NOT_AUDITED` | 4 | 4 | 4 |
| 34 | CONTEMAX Consultoria | `contemax_open` | `failed` | `FAILED_EXTERNAL` | UNKNOWN | 0 | 0 |
| 35 | CPCon / UEPB Concursos | `cpcon_open` | `success` | `NOT_AUDITED` | UNKNOWN | 10 | 10 |
| 36 | FUNVAPI Concursos | `funvapi_open` | `success` | `NOT_AUDITED` | UNKNOWN | 7 | 6 |
| 37 | CONSEP - Consultoria e Estudos | `consep_open` | `empty_valid` | `EMPTY_VERIFIED` | 9 | 0 | 0 |
| 38 | Instituto Consulplan | `institutoconsulplan_open` | `empty_valid` | `BLOCKED` | UNKNOWN | 0 | 0 |
| 39 | Instituto Avalia | `avalia_open` | `success` | `NOT_AUDITED` | 99 | 2 | 1 |
| 40 | UFU / DIRPS - Seleções e Concursos | `ufu_selection` | `success` | `NOT_AUDITED` | 11 | 11 | 11 |
| 41 | IDGRAN Concursos | `idgran_open` | `failed` | `FAILED_EXTERNAL` | UNKNOWN | 0 | 0 |
| 42 | Instituto Quadrix | `quadrix_open` | `success` | `NOT_AUDITED` | 2 | 2 | 2 |
| 43 | Gualimp Assessoria e Consultoria | `gualimp_open` | `degraded` | `NOT_AUDITED` | UNKNOWN | 0 | 0 |
| 44 | Instituto Verbena / UFG | `verbena_selection` | `success` | `NOT_AUDITED` | UNKNOWN | 5 | 4 |
| 45 | Instituto IDIB | `idib_open` | `success` | `NOT_AUDITED` | UNKNOWN | 6 | 6 |
| 46 | JCM Consultoria Municipal | `jcm_open` | `empty_valid` | `EMPTY_VERIFIED` | UNKNOWN | 0 | 0 |
| 47 | Elo Assessoria e Serviços | `elo_open` | `success` | `NOT_AUDITED` | UNKNOWN | 7 | 7 |
| 48 | Apta Concursos e Assessoria | `apta_open` | `empty_valid` | `EMPTY_VERIFIED` | 1 | 25 | 0 |
| 49 | Legalle Concursos | `legalle_open` | `success` | `NOT_AUDITED` | 4 | 25 | 4 |
| 50 | RBO Concursos e Assessoria | `rbo_open` | `success` | `VERIFIED` | 2 | 2 | 2 |
| 51 | SHDias Consultoria e Concursos | `shdias_open` | `blocked` | `BLOCKED` | UNKNOWN | 0 | 0 |
| 52 | Instituto Zambini | `zambini_open` | `empty_valid` | `EMPTY_VERIFIED` | 1 | 0 | 0 |
| 53 | Instituto Nosso Rumo | `nossorumo_open` | `success` | `NOT_AUDITED` | UNKNOWN | 2 | 2 |
| 54 | Avança SP Concursos | `avancasp_open` | `success` | `NOT_AUDITED` | 6 | 6 | 6 |
| 55 | Instituto Mais de Gestão e Concursos | `institutomais_open` | `success` | `NOT_AUDITED` | 17 | 18 | 17 |
| 56 | Publiconsult Concursos | `publiconsult_open` | `empty_valid` | `EMPTY_VERIFIED` | UNKNOWN | 14 | 0 |
| 57 | KLC Concursos | `klc_open` | `empty_valid` | `EMPTY_VERIFIED` | UNKNOWN | 0 | 0 |
| 58 | Sigma Assessoria e Consultoria | `sigma_open` | `empty_valid` | `EMPTY_VERIFIED` | 1 | 1 | 0 |
| 59 | W2 Auditores e Consultores | `w2_open` | `empty_valid` | `EMPTY_VERIFIED` | 10 | 10 | 0 |
| 60 | Fênix Concursos | `fenix_open` | `empty_valid` | `EMPTY_VERIFIED` | 1 | 25 | 0 |
| 61 | Oppus Concursos | `oppus_open` | `degraded` | `NOT_AUDITED` | UNKNOWN | 0 | 0 |
| 62 | Instituto Legatus | `legatus_open` | `success` | `NOT_AUDITED` | UNKNOWN | 12 | 11 |
| 63 | Fundação FEPESE | `fepese_open` | `success` | `NOT_AUDITED` | UNKNOWN | 13 | 13 |
| 64 | FUNCERN Concursos e Seleções | `funcern_selection` | `success` | `VERIFIED` | 2 | 2 | 2 |
| 65 | FAPEMIG - Seleções de Pessoal e Editais | `fapemig_selection` | `degraded` | `NOT_AUDITED` | UNKNOWN | 0 | 0 |
| 66 | FAPES (Espírito Santo) - Seleções | `fapes_selection` | `degraded` | `NOT_AUDITED` | UNKNOWN | 0 | 0 |
| 67 | FAPESQ (Paraíba) - Seleções | `fapesq_selection` | `degraded` | `NOT_AUDITED` | UNKNOWN | 0 | 0 |
| 68 | Fundação Uniselva - Processos Seletivos | `uniselva_selection` | `success` | `NOT_AUDITED` | UNKNOWN | 9 | 2 |
| 69 | Fundação de Apoio à FAFIPA | `fafipa_open` | `success` | `VERIFIED` | 9 | 9 | 9 |
| 70 | Instituto IESES | `ieses_open` | `success` | `NOT_AUDITED` | UNKNOWN | 26 | 3 |
| 71 | FUNPEC - Processos Seletivos | `funpec_selection` | `success` | `NOT_AUDITED` | 10 | 10 | 10 |
| 72 | FADE - Fundação de Apoio ao Desenvolvimento | `fade_selection` | `degraded` | `NOT_AUDITED` | UNKNOWN | 0 | 0 |
| 73 | FAPEX - Fundação de Apoio à Pesquisa e Extensão | `fapex_selection` | `degraded` | `NOT_AUDITED` | UNKNOWN | 0 | 0 |
| 74 | FATEC - Fundação de Apoio | `fatec_selection` | `success` | `NOT_AUDITED` | UNKNOWN | 3 | 3 |
| 75 | FAPED - Fundação de Apoio | `faped_selection` | `degraded` | `NOT_AUDITED` | UNKNOWN | 0 | 0 |
| 76 | FAPESE - Fundação de Apoio à Extensão e Pesquisa | `fapese_selection` | `degraded` | `NOT_AUDITED` | UNKNOWN | 0 | 0 |
| 77 | FAPEPI (Piauí) - Seleções | `fapepi_selection` | `empty_valid` | `EMPTY_VERIFIED` | 106 | 0 | 0 |
| 78 | FAPEMA (Maranhão) - Seleções | `fapema_selection` | `degraded` | `NOT_AUDITED` | UNKNOWN | 0 | 0 |
| 79 | FAPECE (Ceará) - Seleções | `fapece_selection` | `failed` | `FAILED_EXTERNAL` | UNKNOWN | 0 | 0 |
| 80 | FAPERN (Rio Grande do Norte) - Seleções | `fapern_selection` | `degraded` | `NOT_AUDITED` | UNKNOWN | 0 | 0 |
| 81 | FAPEAL (Alagoas) - Seleções | `fapeal_selection` | `degraded` | `NOT_AUDITED` | UNKNOWN | 0 | 0 |
| 82 | FACEPE (Pernambuco) - Seleções | `facepe_selection` | `degraded` | `NOT_AUDITED` | UNKNOWN | 0 | 0 |
| 83 | FAPESB (Bahia) - Seleções | `fapesb_selection` | `degraded` | `NOT_AUDITED` | UNKNOWN | 0 | 0 |
| 84 | FAPERJ (Rio de Janeiro) - Seleções | `faperj_selection` | `degraded` | `NOT_AUDITED` | 23 | 0 | 0 |
| 85 | FAPESP (São Paulo) - Oportunidades e Seleções | `fapesp_selection` | `degraded` | `NOT_AUDITED` | UNKNOWN | 0 | 0 |
| 86 | Fundação Araucária / FAPPR (Paraná) | `fappr_selection` | `degraded` | `NOT_AUDITED` | UNKNOWN | 0 | 0 |
| 87 | FAPESC (Santa Catarina) - Seleções | `fapesc_selection` | `degraded` | `NOT_AUDITED` | UNKNOWN | 0 | 0 |
| 88 | FAPERGS (Rio Grande do Sul) - Seleções | `fapergs_selection` | `degraded` | `NOT_AUDITED` | UNKNOWN | 0 | 0 |
| 89 | FUNDECT (Mato Grosso do Sul) - Seleções | `fundect_selection` | `degraded` | `NOT_AUDITED` | UNKNOWN | 0 | 0 |
| 90 | FAPEMAT (Mato Grosso) - Seleções | `fapemat_selection` | `degraded` | `NOT_AUDITED` | UNKNOWN | 0 | 0 |
| 91 | FAPEG (Goiás) - Seleções | `fapeg_selection` | `degraded` | `NOT_AUDITED` | UNKNOWN | 0 | 0 |
| 92 | FAPDF (Distrito Federal) - Seleções | `fapdf_selection` | `degraded` | `NOT_AUDITED` | UNKNOWN | 0 | 0 |
| 93 | FAPT (Tocantins) - Seleções | `fapt_selection` | `degraded` | `NOT_AUDITED` | UNKNOWN | 0 | 0 |
| 94 | FAPEAM (Amazonas) - Seleções | `fapeam_selection` | `degraded` | `NOT_AUDITED` | UNKNOWN | 0 | 0 |
| 95 | FAPESPA (Pará) - Seleções | `fapespa_selection` | `degraded` | `NOT_AUDITED` | UNKNOWN | 0 | 0 |
| 96 | FAPEAP (Amapá) - Seleções | `fapeap_selection` | `degraded` | `NOT_AUDITED` | UNKNOWN | 0 | 0 |
| 97 | FAPERR (Roraima) - Seleções | `faperr_selection` | `degraded` | `NOT_AUDITED` | UNKNOWN | 0 | 0 |
| 98 | FAPERO (Rondônia) - Seleções | `fapero_selection` | `degraded` | `NOT_AUDITED` | UNKNOWN | 0 | 0 |
| 99 | FAPAC (Acre) - Seleções | `fapac_selection` | `degraded` | `NOT_AUDITED` | UNKNOWN | 0 | 0 |

## Amostras e comparações

### 04. CONSULPAM Concursos (`consulpam_open`)
- Crawler: `success`; verificação: `NOT_AUDITED`
- Visíveis independentemente: 9; processados: 9
- Método: official_html_observer
- URLs de evidência: https://www.consulpam.com.br/index.php?menu=concursos, https://www.consulpam.com.br/index.php?menu=concursos&acao=ver&id=870, https://www.consulpam.com.br/arquivos/20260821_161654_EDITAL 003 - GROAÍRAS - ACE E ACS.pdf

```json
{
  "expected": {
    "link_edital": "https://www.consulpam.com.br/arquivos/20260821_161654_EDITAL 003 - GROAÍRAS - ACE E ACS.pdf"
  },
  "actual": {
    "titulo": "PREFEITURA MUNICIPAL DE GROAÍRAS-CE(003/2026-ACS E ACE-CONCURSO PÚBLICO)",
    "orgao": "PREFEITURA MUNICIPAL DE GROAÍRAS-CE(003/2026-ACS E ACE",
    "modalidade": "Concurso Público",
    "cargo": "Vários cargos",
    "area": "saude",
    "cidade": "Groaíras",
    "uf": "CE",
    "status": "Inscrições abertas",
    "vagas": 2,
    "salario_min": 3242.0,
    "salario_max": 3242.0,
    "escolaridade": null,
    "taxa": 110.0,
    "prova_data": "2026-08-21T00:00:00+00:00",
    "edital_numero": "003/2026",
    "edital_data": "2026-09-09T00:00:00+00:00",
    "inscricao_inicio": "2026-08-21T00:00:00+00:00",
    "inscricao_fim": "2026-09-09T23:59:00+00:00",
    "link_pagina": "https://www.consulpam.com.br/index.php?menu=concursos&acao=ver&id=870",
    "link_edital": "https://www.consulpam.com.br/arquivos/20260821_161654_EDITAL 003 - GROAÍRAS - ACE E ACS.pdf",
    "link_inscricao": null
  },
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
  },
  "publication_audit": {
    "status": "MATCH",
    "expected_count": 4,
    "actual_count": 4,
    "expected_titles": [
      "ADITIVO 001/2026 - ALTERANDO O ANEXO I",
      "EDITAL 003/2026 - RETIFICADO",
      "CRONOGRAMA DE ATIVIDADES",
      "EDITAL 003/2026"
    ],
    "actual_titles": [
      "ADITIVO 001/2026 - ALTERANDO O ANEXO I",
      "EDITAL 003/2026 - RETIFICADO",
      "CRONOGRAMA DE ATIVIDADES",
      "EDITAL 003/2026"
    ],
    "invalid_actual_titles": [],
    "missing_titles": [],
    "missing_links": []
  }
}
```

### 05. IBAM Concursos (`ibam_open`)
- Crawler: `success`; verificação: `NOT_AUDITED`
- Visíveis independentemente: UNKNOWN; processados: 26
- Método: official_html_observer
- URLs de evidência: https://www.ibam-concursos.org.br, https://www.ibam-concursos.org.br/inscricao.asp?task=novo&cod=374&car=1769

```json
{
  "expected": {
    "link_inscricao": "https://www.ibam-concursos.org.br/candidato.asp"
  },
  "actual": {
    "titulo": "Informações do concurso",
    "orgao": "Câmara Municipal de Concordia/SC - Ed. 01/26",
    "modalidade": "Concurso Público",
    "cargo": "Vários cargos",
    "area": "contabilidade_financas",
    "cidade": "Concordia",
    "uf": "SC",
    "status": null,
    "vagas": null,
    "salario_min": null,
    "salario_max": null,
    "escolaridade": null,
    "taxa": null,
    "prova_data": null,
    "edital_numero": null,
    "edital_data": null,
    "inscricao_inicio": null,
    "inscricao_fim": null,
    "link_pagina": "https://www.ibam-concursos.org.br/inscricao.asp?task=novo&cod=374&car=1769",
    "link_edital": null,
    "link_inscricao": "https://www.ibam-concursos.org.br/candidato.asp"
  },
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
  },
  "publication_audit": {
    "status": "UNKNOWN",
    "expected_count": 0,
    "actual_count": 0,
    "expected_titles": [],
    "actual_titles": [],
    "invalid_actual_titles": [],
    "missing_titles": [],
    "missing_links": []
  }
}
```

### 06. IBADE Concursos (`ibade_open`)
- Crawler: `success`; verificação: `NOT_AUDITED`
- Visíveis independentemente: 6; processados: 6
- Método: official_html_observer
- URLs de evidência: https://portal.ibade.selecao.site/edital, https://portal.ibade.selecao.site/edital/ver/126, https://ibade.selecao.site/arquivo.php?file=edital/1/126/130a6c954960dd7b114ee62ea32d4ece.pdf

```json
{
  "expected": {
    "link_edital": "https://ibade.selecao.site/arquivo.php?file=edital/1/126/130a6c954960dd7b114ee62ea32d4ece.pdf",
    "link_inscricao": "https://candidato.ibade.selecao.site/"
  },
  "actual": {
    "titulo": "Concurso Público 001/2026",
    "orgao": "PREFEITURA MUNICIPAL DE ITARANA",
    "modalidade": "Concurso Público",
    "cargo": "Vários cargos",
    "area": "multiplas",
    "cidade": null,
    "uf": null,
    "status": "Em andamento",
    "vagas": null,
    "salario_min": null,
    "salario_max": null,
    "escolaridade": null,
    "taxa": null,
    "prova_data": null,
    "edital_numero": null,
    "edital_data": null,
    "inscricao_inicio": "2026-08-25T00:00:00+00:00",
    "inscricao_fim": "2026-08-25T00:00:00+00:00",
    "link_pagina": "https://portal.ibade.selecao.site/edital/ver/126",
    "link_edital": "https://ibade.selecao.site/arquivo.php?file=edital/1/126/130a6c954960dd7b114ee62ea32d4ece.pdf",
    "link_inscricao": "https://candidato.ibade.selecao.site/"
  },
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
  },
  "publication_audit": {
    "status": "MATCH",
    "expected_count": 18,
    "actual_count": 18,
    "expected_titles": [
      "CONVOCAÇÃO PARA A PROVA DE TÍTULOS",
      "QUANTITATIVO DE INSCRITO POR CARGO",
      "HOMOLOGAÇÃO DAS INSCRIÇÕES",
      "RESULTADO FINAL DOS CANDIDATO QUE DE DECLARARAM COMO PESSOAS COM DEFICIÊNCIA – PcD",
      "RESULTADO FINAL DOS PEDIDOS DE ATENDIMENTO ESPECIAL",
      "RESPOSTAS AOS RECURSOS CONTRA O RESULTADO PRELIMINAR DAS INSCRIÇÕES",
      "RESPOSTAS AOS RECURSOS CONTRA O RESULTADO PRELIMINAR DOS CANDIDATO QUE DE DECLARARAM COMO PESSOAS COM DEFICIÊNCIA – PcD",
      "RESPOSTAS AOS RECURSOS CONTRA O RESULTADO PRELIMINAR DOS PEDIDOS DE ATENDIMENTO ESPECIAL",
      "RESULTADO PRELIMINAR DAS INSCRIÇÕES",
      "RESULTADO PRELIMINAR DOS CANDIDATO QUE DE DECLARARAM COMO PESSOAS COM DEFICIÊNCIA – PcD",
      "RESULTADO PRELIMINAR DOS PEDIDOS DE ATENDIMENTO ESPECIAL",
      "RESULTADO FINAL DOS PEDIDOS DE ISENÇÃO",
      "RESPOSTAS AOS RECURSOS CONTRA O RESULTADO PRELIMINAR DOS PEDIDOS DE ISENÇÃO",
      "resultado preliminar dos pedidos de isenção",
      "ANEXO II - CRONOGRAMA PREVISTO",
      "ANEXO I - QUADRO DE VAGAS",
      "Edital de Abertura",
      "HISTÓRICO DE COMUNICADOS - ATUALIZADO EM 25/08/2026"
    ],
    "actual_titles": [
      "CONVOCAÇÃO PARA A PROVA DE TÍTULOS",
      "QUANTITATIVO DE INSCRITO POR CARGO",
      "HOMOLOGAÇÃO DAS INSCRIÇÕES",
      "RESULTADO FINAL DOS CANDIDATO QUE DE DECLARARAM COMO PESSOAS COM DEFICIÊNCIA – PcD",
      "RESULTADO FINAL DOS PEDIDOS DE ATENDIMENTO ESPECIAL",
      "RESPOSTAS AOS RECURSOS CONTRA O RESULTADO PRELIMINAR DAS INSCRIÇÕES",
      "RESPOSTAS AOS RECURSOS CONTRA O RESULTADO PRELIMINAR DOS CANDIDATO QUE DE DECLARARAM COMO PESSOAS COM DEFICIÊNCIA – PcD",
      "RESPOSTAS AOS RECURSOS CONTRA O RESULTADO PRELIMINAR DOS PEDIDOS DE ATENDIMENTO ESPECIAL",
      "RESULTADO PRELIMINAR DAS INSCRIÇÕES",
      "RESULTADO PRELIMINAR DOS CANDIDATO QUE DE DECLARARAM COMO PESSOAS COM DEFICIÊNCIA – PcD",
      "RESULTADO PRELIMINAR DOS PEDIDOS DE ATENDIMENTO ESPECIAL",
      "RESULTADO FINAL DOS PEDIDOS DE ISENÇÃO",
      "RESPOSTAS AOS RECURSOS CONTRA O RESULTADO PRELIMINAR DOS PEDIDOS DE ISENÇÃO",
      "resultado preliminar dos pedidos de isenção",
      "ANEXO II - CRONOGRAMA PREVISTO",
      "ANEXO I - QUADRO DE VAGAS",
      "Edital de Abertura",
      "HISTÓRICO DE COMUNICADOS - ATUALIZADO EM 25/08/2026"
    ],
    "invalid_actual_titles": [],
    "missing_titles": [],
    "missing_links": []
  }
}
```

### 10. FGV Conhecimento Concursos (`fgv_open`)
- Crawler: `success`; verificação: `NOT_AUDITED`
- Visíveis independentemente: 33; processados: 4
- Método: official_html_observer+official_page_and_pdf_review
- URLs de evidência: https://conhecimento.fgv.br/concursos, https://conhecimento.fgv.br/concursos/pms2026, https://conhecimento.fgv.br/sites/default/files/concursos/edital-preliminar-pref-salvador-prof-e-coordenador-academico-01.2026-09.07-ret2.pdf

```json
{
  "expected": {
    "titulo": "Concurso Público para a Prefeitura Municipal do Salvador 2026",
    "orgao": "Prefeitura Municipal do Salvador",
    "modalidade": "Concurso Público",
    "cidade": "Salvador",
    "uf": "BA",
    "status": "Em Andamento",
    "vagas": 190,
    "salario_min": 2565.32,
    "salario_max": 6156.76,
    "taxa": 220.0,
    "prova_data": "27/09/2026",
    "edital_numero": "01/2026",
    "edital_data": "09/07/2026",
    "inscricao_inicio": "09/07/2026",
    "inscricao_fim": "07/08/2026",
    "link_pagina": "https://conhecimento.fgv.br/concursos/pms2026",
    "link_edital": "https://conhecimento.fgv.br/sites/default/files/concursos/edital-preliminar-pref-salvador-prof-e-coordenador-academico-01.2026-09.07-ret2.pdf"
  },
  "actual": null,
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
  },
  "publication_audit": {
    "status": "UNKNOWN",
    "expected_count": 3,
    "actual_count": null,
    "expected_titles": [
      "Edital (retificado em 07/08/2026)",
      "2ª Retificação",
      "1ª Retificação"
    ],
    "actual_titles": [],
    "invalid_actual_titles": [],
    "missing_titles": [],
    "missing_links": []
  }
}
```

### 11. Cebraspe Concursos (`cebraspe_open`)
- Crawler: `success`; verificação: `NOT_AUDITED`
- Visíveis independentemente: UNKNOWN; processados: 6
- Método: official_html_observer
- URLs de evidência: https://www.cebraspe.org.br/concursos/, https://www.cebraspe.org.br/concursos/CAMARA_MUNICIPAL_PONTAPORA_MS_26

```json
{
  "expected": {},
  "actual": {
    "titulo": "Câmara Municipal de Ponta Porã (MS)",
    "orgao": "CAMARA MUNICIPAL PONTA PORA MS 26",
    "modalidade": "Concurso Público",
    "cargo": "Vários cargos",
    "area": null,
    "cidade": null,
    "uf": null,
    "status": "Inscrições abertas",
    "vagas": 19,
    "salario_min": null,
    "salario_max": 7999.59,
    "escolaridade": null,
    "taxa": null,
    "prova_data": null,
    "edital_numero": null,
    "edital_data": null,
    "inscricao_inicio": "2026-08-21T00:00:00+00:00",
    "inscricao_fim": "2026-09-10T18:00:00+00:00",
    "link_pagina": "https://www.cebraspe.org.br/concursos/CAMARA_MUNICIPAL_PONTAPORA_MS_26",
    "link_edital": "https://cdn.cebraspe.org.br/concursos/CAMARA_MUNICIPAL_PONTAPORA_MS_26/arquivos/4D1A8250B5C31E91D6EF22CD6FFAEAC93329629A1E7618F7A7BCAA271EABA272.pdf",
    "link_inscricao": "https://www.cebraspe.org.br/concursos/CAMARA_MUNICIPAL_PONTAPORA_MS_26"
  },
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
  },
  "publication_audit": {
    "status": "UNKNOWN",
    "expected_count": 0,
    "actual_count": 2,
    "expected_titles": [],
    "actual_titles": [
      "Edital nº 1 - Abertura - Vlibras",
      "Edital nº 1 - Abertura"
    ],
    "invalid_actual_titles": [],
    "missing_titles": [],
    "missing_links": []
  }
}
```

### 14. IBGP - Inscrições Abertas (`ibgp_open`)
- Crawler: `success`; verificação: `NOT_AUDITED`
- Visíveis independentemente: UNKNOWN; processados: 15
- Método: official_html_observer
- URLs de evidência: https://novo.ibgpconcursos.com.br/inscricoes_abertas.jsp, https://novo.ibgpconcursos.com.br/concurso.jsp?cod=704

```json
{
  "expected": {},
  "actual": {
    "titulo": "CONCURSO PÚBLICO DO INSTITUTO DE PREVIDÊNCIA DE ITABIRA/MG - ITABIRAPREV - EDITAL Nº 01/2026",
    "orgao": "INSTITUTO DE PREVIDÊNCIA DE ITABIRA - ITABIRAPREV",
    "modalidade": "Concurso Público",
    "cargo": "Vários cargos",
    "area": "administrativa",
    "cidade": "Concurso Público Do Instituto De Previdência De Itabira",
    "uf": "MG",
    "status": "Inscrições abertas",
    "vagas": null,
    "salario_min": null,
    "salario_max": null,
    "escolaridade": null,
    "taxa": 80.0,
    "prova_data": null,
    "edital_numero": "01/2026",
    "edital_data": null,
    "inscricao_inicio": "2026-08-24T09:00:00+00:00",
    "inscricao_fim": "2026-09-22T16:00:00+00:00",
    "link_pagina": "https://novo.ibgpconcursos.com.br/concurso.jsp?cod=704",
    "link_edital": "https://novo.ibgpconcursos.com.br/rest/concurso/download/edital/23011/?file=site/anexos/704/00 - EDITAL CONCURSO ITABIRAPREV_.pdf",
    "link_inscricao": "https://novo.ibgpconcursos.com.br/candidato/index.jsp?cod=704"
  },
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
  },
  "publication_audit": {
    "status": "UNKNOWN",
    "expected_count": 0,
    "actual_count": 8,
    "expected_titles": [],
    "actual_titles": [
      "EDITAL Nº 01-2026",
      "ANEXO I - CARGOS, ESCOLARIDADES-REQUISITOS PARA INGRESSO, JORNADAS DE TRABALHO, VAGAS (AMPLA CONCORRÊNCIA, PESSOAS COM DEFICIÊNCIA - PcD E PESSOAS NEGRAS) E VENCIMENTO INICIAL",
      "ANEXO II - DESCRIÇÃO E ATRIBUIÇÕES DOS CARGOS",
      "ANEXO III - QUADRO DE PROVAS",
      "ANEXO IV - CONTEUDOS PROGRAMÁTICOS",
      "ANEXO V - DECLARAÇÃO PARA SOLICITAÇÃO DE ISENÇÃO DE PAGAMENTO DA TAXA DE INSCRIÇÃO",
      "ANEXO VI - MODELO DE DECLARAÇÃO E DE LAUDO MÉDICO PARA VAGAS DE PESSOAS COM DEFICIÊNCIA (PcD) E-OU SOLICITAÇÃO DE CONDIÇÃO ESPECIAL PARA REALIZAÇÃO DAS PROVAS",
      "ANEXO VII - CRITÉRIOS DE AVALIAÇÃO PARA A PROVA DE TÍTULOS"
    ],
    "invalid_actual_titles": [],
    "missing_titles": [],
    "missing_links": []
  }
}
```

### 15. FUNDEP - Gestão de Concursos (`fundep_open`)
- Crawler: `success`; verificação: `NOT_AUDITED`
- Visíveis independentemente: 1; processados: 1
- Método: official_html_observer
- URLs de evidência: https://www.gestaodeconcursos.com.br/site/site/default.aspx, https://fundep.selecao.net.br/informacoes/72/, https://anexos-r2.selecao.net.br/uploads/590/concursos/72/anexos/3d865bb2-0455-447d-b254-bf958d7f46ed.pdf

```json
{
  "expected": {
    "link_edital": "https://anexos-r2.selecao.net.br/uploads/590/concursos/72/anexos/3d865bb2-0455-447d-b254-bf958d7f46ed.pdf",
    "link_inscricao": "https://gestaodeconcursos.com.br/candidato/CadastroCandidato.aspx"
  },
  "actual": {
    "titulo": "Concurso Público FUMEP - Edital 01/2026",
    "orgao": "Fundação Municipal de Ensino Profissionalizante de Sete Lagoas - FUMEP",
    "modalidade": "Concurso Público",
    "cargo": null,
    "area": "educacao",
    "cidade": "Sete Lagoas",
    "uf": "MG",
    "status": "Inscrições em breve",
    "vagas": 39,
    "salario_min": 1621.0,
    "salario_max": 2530.56,
    "escolaridade": null,
    "taxa": null,
    "prova_data": null,
    "edital_numero": "01/2026",
    "edital_data": "2026-08-17T00:00:00+00:00",
    "inscricao_inicio": "2026-10-19T00:00:00+00:00",
    "inscricao_fim": "2026-11-18T23:59:00+00:00",
    "link_pagina": "https://fundep.selecao.net.br/informacoes/72/",
    "link_edital": "https://anexos-r2.selecao.net.br/uploads/590/concursos/72/anexos/3d865bb2-0455-447d-b254-bf958d7f46ed.pdf",
    "link_inscricao": "https://gestaodeconcursos.com.br/candidato/CadastroCandidato.aspx"
  },
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
  },
  "publication_audit": {
    "status": "MATCH",
    "expected_count": 1,
    "actual_count": 1,
    "expected_titles": [
      "Edital 01/2026 da Fundação Municipal de Ensino Profissionalizante de Sete Lagoas - FUMEP 17/08/2026"
    ],
    "actual_titles": [
      "Edital 01/2026 da Fundação Municipal de Ensino Profissionalizante de Sete Lagoas - FUMEP 17/08/2026"
    ],
    "invalid_actual_titles": [],
    "missing_titles": [],
    "missing_links": []
  }
}
```

### 16. FUMARC Concursos (`fumarc_open`)
- Crawler: `success`; verificação: `NOT_AUDITED`
- Visíveis independentemente: UNKNOWN; processados: 33
- Método: official_html_observer
- URLs de evidência: https://www.fumarc.com.br/SitePages/Home.aspx, https://www.fumarc.com.br/SitePages/Home.aspx?concurso=54&secao=-1

```json
{
  "expected": {},
  "actual": {
    "titulo": "Concurso Público CREA - MG",
    "orgao": "CONSELHO REGIONAL DE ENGENHARIA E AGRONOMIA DE MINAS GERAIS – CREA-MG",
    "modalidade": "Concurso Público",
    "cargo": null,
    "area": "engenharia_arquitetura",
    "cidade": null,
    "uf": "MG",
    "status": null,
    "vagas": null,
    "salario_min": null,
    "salario_max": null,
    "escolaridade": null,
    "taxa": null,
    "prova_data": "2026-09-20T03:00:00+00:00",
    "edital_numero": null,
    "edital_data": null,
    "inscricao_inicio": null,
    "inscricao_fim": null,
    "link_pagina": "https://www.fumarc.com.br/SitePages/Home.aspx?concurso=54&secao=-1",
    "link_edital": "https://www.fumarc.com.br/Documentos%20Compartilhados/CREA%20-%20MG/Edital%2001.2026%20-%20Consolidado%20com%20Errata%20n%C2%BA01.pdf",
    "link_inscricao": null
  },
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
  },
  "publication_audit": {
    "status": "UNKNOWN",
    "expected_count": 0,
    "actual_count": 18,
    "expected_titles": [],
    "actual_titles": [
      "Resultado Analise de Documentos",
      "Relação de Inscrições Deferidas/Confirmadas",
      "Relação de Inscrições Deferidas/Confirmadas",
      "Relação de Inscrições Deferidas/Confirmadas",
      "Resultado dos Recursos contra",
      "Resultado das Solicitações de Isenção",
      "Edital Nº 01/2026 - Consolidado",
      "Errata Nº 01",
      "Extrato de Publicação",
      "Anexo VIII",
      "Anexo VII",
      "Anexo VI",
      "Anexo V",
      "Anexo IV",
      "Anexo III",
      "ANEXO II",
      "ANEXO I",
      "Edital"
    ],
    "invalid_actual_titles": [],
    "missing_titles": [],
    "missing_links": []
  }
}
```

### 17. IMESO - Concursos e Seletivos (`imeso_open`)
- Crawler: `success`; verificação: `NOT_AUDITED`
- Visíveis independentemente: 2; processados: 2
- Método: official_html_observer
- URLs de evidência: https://portal.imeso.com.br/edital, https://portal.imeso.com.br/edital/ver/134, https://s3.us-east-1.amazonaws.com/cdn.imeso.com.br/edital/1/134/43830bf553934703208822752bf8293a.pdf

```json
{
  "expected": {
    "link_edital": "https://s3.us-east-1.amazonaws.com/cdn.imeso.com.br/edital/1/134/43830bf553934703208822752bf8293a.pdf",
    "link_inscricao": "https://candidato.imeso.com.br/inscricao/6e684d376e02a5b69118b37b27b02440"
  },
  "actual": {
    "titulo": "Processo Seletivo Público 001/2026",
    "orgao": "PREFEITURA MUNICIPAL DE URUANA DE MINAS/MG",
    "modalidade": "Processo Seletivo Público",
    "cargo": "Vários cargos",
    "area": "saude",
    "cidade": "Uruana De Minas",
    "uf": "MG",
    "status": "Inscrições abertas",
    "vagas": null,
    "salario_min": 3242.0,
    "salario_max": 3242.0,
    "escolaridade": "Ensino Médio Completo",
    "taxa": null,
    "prova_data": "2026-10-18T00:00:00+00:00",
    "edital_numero": "001/2026",
    "edital_data": null,
    "inscricao_inicio": "2026-08-17T10:00:00+00:00",
    "inscricao_fim": "2026-09-17T17:00:00+00:00",
    "link_pagina": "https://portal.imeso.com.br/edital/ver/134",
    "link_edital": "https://s3.us-east-1.amazonaws.com/cdn.imeso.com.br/edital/1/134/43830bf553934703208822752bf8293a.pdf",
    "link_inscricao": "https://candidato.imeso.com.br/inscricao/6e684d376e02a5b69118b37b27b02440"
  },
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
  },
  "publication_audit": {
    "status": "MATCH",
    "expected_count": 1,
    "actual_count": 1,
    "expected_titles": [
      "EDITAL"
    ],
    "actual_titles": [
      "EDITAL"
    ],
    "invalid_actual_titles": [],
    "missing_titles": [],
    "missing_links": []
  }
}
```

### 18. OMNI Concursos Públicos (`omni_open`)
- Crawler: `success`; verificação: `VERIFIED`
- Visíveis independentemente: 2; processados: 2
- Método: official_html_observer
- URLs de evidência: https://portal.omniconcursospublicos.com.br, https://portal.omniconcursospublicos.com.br/informacoes/239/, https://anexos.cdn.selecao.net.br/uploads/412/concursos/239/anexos/gO2nAYYvz3JvHM2zTe6a6RuSAP7AkEMfdbQIqFVT.pdf

```json
{
  "expected": {
    "titulo": "Concurso Público - 002/2024 - Prefeitura Municipal de Papanduva - SC",
    "modalidade": "Concurso Público",
    "cidade": "Papanduva",
    "uf": "SC",
    "link_edital": "https://anexos.cdn.selecao.net.br/uploads/412/concursos/239/anexos/gO2nAYYvz3JvHM2zTe6a6RuSAP7AkEMfdbQIqFVT.pdf"
  },
  "actual": {
    "titulo": "Concurso Público - 002/2024 - Prefeitura Municipal de Papanduva - SC",
    "orgao": "Prefeitura Municipal de Papanduva - SC",
    "modalidade": "Concurso Público",
    "cargo": "Vários cargos",
    "area": "multiplas",
    "cidade": "Papanduva",
    "uf": "SC",
    "status": "Em andamento",
    "vagas": 96,
    "salario_min": null,
    "salario_max": null,
    "escolaridade": null,
    "taxa": null,
    "prova_data": null,
    "edital_numero": "002/2024",
    "edital_data": "2024-09-03T00:00:00+00:00",
    "inscricao_inicio": "2024-07-16T00:00:00+00:00",
    "inscricao_fim": "2024-09-12T23:59:00+00:00",
    "link_pagina": "https://portal.omniconcursospublicos.com.br/informacoes/239/",
    "link_edital": "https://anexos.cdn.selecao.net.br/uploads/412/concursos/239/anexos/gO2nAYYvz3JvHM2zTe6a6RuSAP7AkEMfdbQIqFVT.pdf",
    "link_inscricao": null
  },
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
  },
  "publication_audit": {
    "status": "MATCH",
    "expected_count": 45,
    "actual_count": 45,
    "expected_titles": [
      "Edital 002/2024 de Abertura",
      "Edital 002/2024 - Retificação 01",
      "Edital de Resultado de Isenção da Taxa de Inscrição",
      "Anexo Único - Resultado de Isenção da Taxa de Inscrição",
      "Edital de Homologação das Inscrições",
      "Anexo I - Inscrições Homologadas - Ampla Concorrência e PCD - Pessoa com Deficiência",
      "Anexo II - Pedidos de Condições Especiais para Realização da Prova",
      "Edital 002/2024 de Reabertura das Inscrições",
      "Edital 002/2024 - Reabertura das Inscrições - Retificado",
      "Edital de Homologação das Inscrições - Pós Reabertura das Inscrições",
      "Anexo I - Inscrições Homologadas - Ampla Concorrência e PCD - Pessoa com Deficiência - Pós Reabertura das Inscrições",
      "Anexo II - Pedidos de Condições Especiais para Realização da Prova - Pós Reabertura das Inscrições",
      "Edital de Homologação das Inscrições - Pós Recurso",
      "Anexo I - Inscrições Homologadas - Ampla Concorrência e PCD - Pessoa com Deficiência - Pós Recurso",
      "Anexo II - Pedidos de Condições Especiais para Realização da Prova - Pós Recurso",
      "Edital de Convocação Prova Objetiva",
      "Anexo Único - Convocação Prova Objetiva",
      "COMUNICADO",
      "Anexo Único - Candidatos que Realizaram mais de uma inscrição",
      "Edital de Homologação das Inscrições - Pós Reabertura das Inscrições - Retificado",
      "Anexo I - Inscrições Homologadas - Ampla Concorrência e PCD - Pessoa com Deficiência - Retificado",
      "Anexo II - Pedidos de Condições Especiais para Realização da Prova - Retificado",
      "Edital de Convocação Prova Objetiva - Retificado",
      "Anexo Único - Convocação Prova Objetiva - Retificado",
      "Edital de Gabarito Preliminar",
      "Anexo Único - Gabarito Preliminar",
      "Edital de Gabarito Oficial",
      "Anexo Único - Gabarito Oficial",
      "Edital de Resultado Preliminar",
      "Anexo I - Resultado Preliminar - Ampla Concorrência e PCD - Pessoa com Deficiência",
      "Anexo II - Resultado Preliminar - PCD - Pessoa com Deficiência",
      "Edital 002/2024 - Retificação 02",
      "Edital de Convocação Prova Prática",
      "Anexo Único - Prova Prática",
      "Edital de Convocação Prova Prática - Analista de Procuradoria",
      "Anexo Único - Prova Prática Analista de Procuradoria",
      "Edital de Gabarito Prova Prática Analista de Procuradoria",
      "Anexo Único - Gabarito Prova Prática Analista de Procuradoria",
      "Edital de Resultado Prova Prática Analista de Procuradoria e Prova Prática",
      "Anexo Único - Resultado Prova Prática Analista de Procuradoria e Prova Prática",
      "Edital de Homologação Resultado Final",
      "Anexo I - Resultado Final - Ampla Concorrência e PCD - Pessoa com Deficiência",
      "Anexo II - Resultado Final - PCD - Pessoa com Deficiência",
      "Edital de Resultado Final - Analista de Procuradoria - Retificado",
      "Anexo Único - Resultado Final - Ampla Concorrência - Analista de Procuradoria - Retificado"
    ],
    "actual_titles": [
      "Edital 002/2024 de Abertura",
      "Edital 002/2024 - Retificação 01",
      "Edital de Resultado de Isenção da Taxa de Inscrição",
      "Anexo Único - Resultado de Isenção da Taxa de Inscrição",
      "Edital de Homologação das Inscrições",
      "Anexo I - Inscrições Homologadas - Ampla Concorrência e PCD - Pessoa com Deficiência",
      "Anexo II - Pedidos de Condições Especiais para Realização da Prova",
      "Edital 002/2024 de Reabertura das Inscrições",
      "Edital 002/2024 - Reabertura das Inscrições - Retificado",
      "Edital de Homologação das Inscrições - Pós Reabertura das Inscrições",
      "Anexo I - Inscrições Homologadas - Ampla Concorrência e PCD - Pessoa com Deficiência - Pós Reabertura das Inscrições",
      "Anexo II - Pedidos de Condições Especiais para Realização da Prova - Pós Reabertura das Inscrições",
      "Edital de Homologação das Inscrições - Pós Recurso",
      "Anexo I - Inscrições Homologadas - Ampla Concorrência e PCD - Pessoa com Deficiência - Pós Recurso",
      "Anexo II - Pedidos de Condições Especiais para Realização da Prova - Pós Recurso",
      "Edital de Convocação Prova Objetiva",
      "Anexo Único - Convocação Prova Objetiva",
      "COMUNICADO",
      "Anexo Único - Candidatos que Realizaram mais de uma inscrição",
      "Edital de Homologação das Inscrições - Pós Reabertura das Inscrições - Retificado",
      "Anexo I - Inscrições Homologadas - Ampla Concorrência e PCD - Pessoa com Deficiência - Retificado",
      "Anexo II - Pedidos de Condições Especiais para Realização da Prova - Retificado",
      "Edital de Convocação Prova Objetiva - Retificado",
      "Anexo Único - Convocação Prova Objetiva - Retificado",
      "Edital de Gabarito Preliminar",
      "Anexo Único - Gabarito Preliminar",
      "Edital de Gabarito Oficial",
      "Anexo Único - Gabarito Oficial",
      "Edital de Resultado Preliminar",
      "Anexo I - Resultado Preliminar - Ampla Concorrência e PCD - Pessoa com Deficiência",
      "Anexo II - Resultado Preliminar - PCD - Pessoa com Deficiência",
      "Edital 002/2024 - Retificação 02",
      "Edital de Convocação Prova Prática",
      "Anexo Único - Prova Prática",
      "Edital de Convocação Prova Prática - Analista de Procuradoria",
      "Anexo Único - Prova Prática Analista de Procuradoria",
      "Edital de Gabarito Prova Prática Analista de Procuradoria",
      "Anexo Único - Gabarito Prova Prática Analista de Procuradoria",
      "Edital de Resultado Prova Prática Analista de Procuradoria e Prova Prática",
      "Anexo Único - Resultado Prova Prática Analista de Procuradoria e Prova Prática",
      "Edital de Homologação Resultado Final",
      "Anexo I - Resultado Final - Ampla Concorrência e PCD - Pessoa com Deficiência",
      "Anexo II - Resultado Final - PCD - Pessoa com Deficiência",
      "Edital de Resultado Final - Analista de Procuradoria - Retificado",
      "Anexo Único - Resultado Final - Ampla Concorrência - Analista de Procuradoria - Retificado"
    ],
    "invalid_actual_titles": [],
    "missing_titles": [],
    "missing_links": []
  }
}
```

### 19. Instituto ACCESS (`access_open`)
- Crawler: `success`; verificação: `VERIFIED`
- Visíveis independentemente: 2; processados: 2
- Método: official_html_observer
- URLs de evidência: https://access.selecao.net.br/index/abertos/, https://access.selecao.net.br/informacoes/180/, https://anexos-r2.selecao.net.br/uploads/422/concursos/180/anexos/f2daed72-249a-4291-b551-f71889d13986.pdf

```json
{
  "expected": {
    "titulo": "Prefeitura Municipal de Guapimirim/RJ",
    "cidade": "Guapimirim",
    "uf": "RJ",
    "link_edital": "https://anexos-r2.selecao.net.br/uploads/422/concursos/180/anexos/f2daed72-249a-4291-b551-f71889d13986.pdf",
    "link_inscricao": "https://access.selecao.net.br/login/sair/?redir=%2Ftermo%2F180%2F"
  },
  "actual": {
    "titulo": "Prefeitura Municipal de Guapimirim/RJ",
    "orgao": "Prefeitura Municipal de Guapimirim/RJ",
    "modalidade": "Concurso Público",
    "cargo": "Vários cargos",
    "area": "educacao",
    "cidade": "Guapimirim",
    "uf": "RJ",
    "status": "Inscrições abertas",
    "vagas": 508,
    "salario_min": 2677.28,
    "salario_max": 2983.47,
    "escolaridade": null,
    "taxa": 53.0,
    "prova_data": "2026-10-18T00:00:00+00:00",
    "edital_numero": "1/2026",
    "edital_data": "2026-07-20T00:00:00+00:00",
    "inscricao_inicio": "2026-07-21T00:00:00+00:00",
    "inscricao_fim": "2026-09-10T23:59:00+00:00",
    "link_pagina": "https://access.selecao.net.br/informacoes/180/",
    "link_edital": "https://anexos-r2.selecao.net.br/uploads/422/concursos/180/anexos/f2daed72-249a-4291-b551-f71889d13986.pdf",
    "link_inscricao": "https://access.selecao.net.br/login/sair/?redir=%2Ftermo%2F180%2F"
  },
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
  },
  "publication_audit": {
    "status": "MATCH",
    "expected_count": 5,
    "actual_count": 5,
    "expected_titles": [
      "EDITAL DE ABERTURA CONSOLIDADO 10/08/2026",
      "RETIFICAÇÃO I 04/08/2026",
      "EDITAL DE ABERTURA 20/07/2026",
      "RESULTADO DEFINITIVO DAS ISENÇÕES 20/08/2026",
      "RESULTADO PRELIMINAR DAS ISENÇÕES 11/08/2026"
    ],
    "actual_titles": [
      "EDITAL DE ABERTURA CONSOLIDADO 10/08/2026",
      "RETIFICAÇÃO I 04/08/2026",
      "EDITAL DE ABERTURA 20/07/2026",
      "RESULTADO DEFINITIVO DAS ISENÇÕES 20/08/2026",
      "RESULTADO PRELIMINAR DAS ISENÇÕES 11/08/2026"
    ],
    "invalid_actual_titles": [],
    "missing_titles": [],
    "missing_links": []
  }
}
```

### 20. Exame Consultores e Auditores (`exame_open`)
- Crawler: `success`; verificação: `NOT_AUDITED`
- Visíveis independentemente: 4; processados: 4
- Método: official_html_observer
- URLs de evidência: https://concursos.exameconsultores.com.br/index/1/, https://concursos.exameconsultores.com.br/informacoes/544/, https://anexos-r2.selecao.net.br/uploads/140/concursos/544/anexos/5ec58b83-6a63-4405-b905-1a1b7ba7770d.pdf

```json
{
  "expected": {
    "titulo": "P.M. de Santana de Pirapama - Concurso Público",
    "modalidade": "Concurso Público",
    "link_edital": "https://anexos-r2.selecao.net.br/uploads/140/concursos/544/anexos/5ec58b83-6a63-4405-b905-1a1b7ba7770d.pdf"
  },
  "actual": {
    "titulo": "P.M. de Santana de Pirapama - Concurso Público",
    "orgao": "P.M. de Santana de Pirapama",
    "modalidade": "Concurso Público",
    "cargo": "Vários cargos",
    "area": "multiplas",
    "cidade": "Santana de Pirapama",
    "uf": "MG",
    "status": "Em andamento",
    "vagas": 79,
    "salario_min": 1593.53,
    "salario_max": 6221.41,
    "escolaridade": "Ensino Fundamental",
    "taxa": 80.0,
    "prova_data": "2026-11-29T00:00:00+00:00",
    "edital_numero": "01/2026",
    "edital_data": "2026-08-10T00:00:00+00:00",
    "inscricao_inicio": "2026-10-12T00:00:00+00:00",
    "inscricao_fim": "2026-11-10T23:59:00+00:00",
    "link_pagina": "https://concursos.exameconsultores.com.br/informacoes/544/",
    "link_edital": "https://anexos-r2.selecao.net.br/uploads/140/concursos/544/anexos/5ec58b83-6a63-4405-b905-1a1b7ba7770d.pdf",
    "link_inscricao": null
  },
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
  },
  "publication_audit": {
    "status": "MATCH",
    "expected_count": 6,
    "actual_count": 6,
    "expected_titles": [
      "RERRATIFICAÇÃO Nº 01 11/08/2026",
      "EDITAL 10/08/2026",
      "PORTARIA Nº 038/2026 - DISPÕE SOBRE A NOMEAÇÃO DE COMISSÃO ESPECIAL DO CONCURSO PÚBLICO 22/06/2026",
      "EXTRATOS DO EDITAL E DA RERRATIFICAÇÃO Nº 01 DO EDITAL NO JORNAL DE GRANDE CIRCULAÇÃO DA REGIÃO/MUNICÍPIO JORNAL SETE DIAS\" 14/08/2026",
      "EXTRATO DA RERRATIFICAÇÃO Nº 01 DO EDITAL NO DIÁRIO OFICIAL DO ESTADO  JORNAL MINAS GERAIS 13/08/2026",
      "EXTRATO DO EDITAL NO DIÁRIO OFICIAL DO ESTADO  JORNAL MINAS GERAIS 11/08/2026"
    ],
    "actual_titles": [
      "RERRATIFICAÇÃO Nº 01 11/08/2026",
      "EDITAL 10/08/2026",
      "PORTARIA Nº 038/2026 - DISPÕE SOBRE A NOMEAÇÃO DE COMISSÃO ESPECIAL DO CONCURSO PÚBLICO 22/06/2026",
      "EXTRATOS DO EDITAL E DA RERRATIFICAÇÃO Nº 01 DO EDITAL NO JORNAL DE GRANDE CIRCULAÇÃO DA REGIÃO/MUNICÍPIO JORNAL SETE DIAS\" 14/08/2026",
      "EXTRATO DA RERRATIFICAÇÃO Nº 01 DO EDITAL NO DIÁRIO OFICIAL DO ESTADO  JORNAL MINAS GERAIS 13/08/2026",
      "EXTRATO DO EDITAL NO DIÁRIO OFICIAL DO ESTADO  JORNAL MINAS GERAIS 11/08/2026"
    ],
    "invalid_actual_titles": [],
    "missing_titles": [],
    "missing_links": []
  }
}
```

### 22. ABCP Concursos (`abcp_open`)
- Crawler: `success`; verificação: `VERIFIED`
- Visíveis independentemente: 4; processados: 4
- Método: official_html_observer
- URLs de evidência: https://abcp.selecao.net.br/index/abertos/, https://abcp.selecao.net.br/informacoes/2867/, https://anexos-r2.selecao.net.br/uploads/567/concursos/2867/anexos/4194043a-894b-4a70-88b8-d5c8ad4a62ce.pdf

```json
{
  "expected": {
    "titulo": "Processo Seletivo Simplificado - 002/2026 - PREFEITURA MUNICIPAL DA ESTÂNCIA TURÍSTICA DE IBIÚNA - SP",
    "modalidade": "Processo Seletivo Simplificado",
    "cidade": "Ibiúna",
    "uf": "SP",
    "link_edital": "https://anexos-r2.selecao.net.br/uploads/567/concursos/2867/anexos/4194043a-894b-4a70-88b8-d5c8ad4a62ce.pdf",
    "link_inscricao": "https://abcp.selecao.net.br/login/sair/?redir=%2Ftermo%2F2867%2F"
  },
  "actual": {
    "titulo": "Processo Seletivo Simplificado - 002/2026 - PREFEITURA MUNICIPAL DA ESTÂNCIA TURÍSTICA DE IBIÚNA - SP",
    "orgao": "PREFEITURA MUNICIPAL DA ESTÂNCIA TURÍSTICA DE IBIÚNA - SP",
    "modalidade": "Processo Seletivo Simplificado",
    "cargo": "Vários cargos",
    "area": "multiplas",
    "cidade": "Ibiúna",
    "uf": "SP",
    "status": "Inscrições abertas",
    "vagas": 33,
    "salario_min": 1638.45,
    "salario_max": 4545.58,
    "escolaridade": "Múltiplas",
    "taxa": 49.0,
    "prova_data": "2026-09-11T00:00:00+00:00",
    "edital_numero": "001/2026",
    "edital_data": "2026-08-25T00:00:00+00:00",
    "inscricao_inicio": "2026-08-25T00:00:00+00:00",
    "inscricao_fim": "2026-09-08T23:59:00+00:00",
    "link_pagina": "https://abcp.selecao.net.br/informacoes/2867/",
    "link_edital": "https://anexos-r2.selecao.net.br/uploads/567/concursos/2867/anexos/4194043a-894b-4a70-88b8-d5c8ad4a62ce.pdf",
    "link_inscricao": "https://abcp.selecao.net.br/login/sair/?redir=%2Ftermo%2F2867%2F"
  },
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
  },
  "publication_audit": {
    "status": "MATCH",
    "expected_count": 1,
    "actual_count": 1,
    "expected_titles": [
      "EDITAL DE ABERTURA 25/08/2026"
    ],
    "actual_titles": [
      "EDITAL DE ABERTURA 25/08/2026"
    ],
    "invalid_actual_titles": [],
    "missing_titles": [],
    "missing_links": []
  }
}
```

### 24. OBJETIVA Concursos (`objetiva_open`)
- Crawler: `success`; verificação: `VERIFIED`
- Visíveis independentemente: 12; processados: 12
- Método: official_html_observer
- URLs de evidência: https://concursos.objetivas.com.br, https://concursos.objetivas.com.br/informacoes/2617/, https://anexos-r2.selecao.net.br/uploads/361/concursos/2617/anexos/d9ea7903-1506-47f2-ae4b-9c077c93af0a.pdf

```json
{
  "expected": {
    "titulo": "GUAPORÉ/RS - Câmara Municipal - Concurso Público 001/2026",
    "modalidade": "Concurso Público",
    "cidade": "Guaporé",
    "uf": "RS",
    "link_edital": "https://anexos-r2.selecao.net.br/uploads/361/concursos/2617/anexos/d9ea7903-1506-47f2-ae4b-9c077c93af0a.pdf",
    "link_inscricao": "https://concursos.objetivas.com.br/login/sair/?redir=%2Ftermo%2F2617%2F"
  },
  "actual": {
    "titulo": "GUAPORÉ/RS - Câmara Municipal - Concurso Público 001/2026",
    "orgao": "Câmara Municipal de GUAPORÉ",
    "modalidade": "Concurso Público",
    "cargo": "Vários cargos",
    "area": "administrativa",
    "cidade": "Guaporé",
    "uf": "RS",
    "status": "Inscrições abertas",
    "vagas": 2,
    "salario_min": 3404.76,
    "salario_max": 4523.47,
    "escolaridade": "Ensino Médio",
    "taxa": 60.0,
    "prova_data": "2026-11-22T00:00:00+00:00",
    "edital_numero": "001/2026",
    "edital_data": null,
    "inscricao_inicio": "2026-08-28T00:00:00+00:00",
    "inscricao_fim": "2026-09-28T23:59:00+00:00",
    "link_pagina": "https://concursos.objetivas.com.br/informacoes/2617/",
    "link_edital": "https://anexos-r2.selecao.net.br/uploads/361/concursos/2617/anexos/d9ea7903-1506-47f2-ae4b-9c077c93af0a.pdf",
    "link_inscricao": "https://concursos.objetivas.com.br/login/sair/?redir=%2Ftermo%2F2617%2F"
  },
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
  },
  "publication_audit": {
    "status": "MATCH",
    "expected_count": 1,
    "actual_count": 1,
    "expected_titles": [
      "Edital N° 001/2026 - Edital de Abertura das Inscrições 20/08/2026"
    ],
    "actual_titles": [
      "Edital N° 001/2026 - Edital de Abertura das Inscrições 20/08/2026"
    ],
    "invalid_actual_titles": [],
    "missing_titles": [],
    "missing_links": []
  }
}
```

### 26. COTEC / FADENOR Concursos (`cotec_open`)
- Crawler: `success`; verificação: `VERIFIED`
- Visíveis independentemente: 2; processados: 2
- Método: official_html_observer
- URLs de evidência: https://www.cotec.fadenor.com.br/index/abertos/, https://www.cotec.fadenor.com.br/informacoes/28/, https://anexos-r2.selecao.net.br/uploads/846/concursos/28/anexos/564c58d4-58da-43ea-b120-23e38c000d71.pdf

```json
{
  "expected": {
    "titulo": "Prefeitura Municipal de Ponto Chique/MG",
    "cidade": "Ponto Chique",
    "uf": "MG",
    "link_edital": "https://anexos-r2.selecao.net.br/uploads/846/concursos/28/anexos/564c58d4-58da-43ea-b120-23e38c000d71.pdf",
    "link_inscricao": "https://www.cotec.fadenor.com.br/login/sair/?redir=%2Ftermo%2F28%2F"
  },
  "actual": {
    "titulo": "Prefeitura Municipal de Ponto Chique/MG",
    "orgao": "Prefeitura Municipal de Ponto Chique/MG",
    "modalidade": "Concurso Público",
    "cargo": "Vários cargos",
    "area": "multiplas",
    "cidade": "Ponto Chique",
    "uf": "MG",
    "status": "Inscrições abertas",
    "vagas": 63,
    "salario_min": null,
    "salario_max": null,
    "escolaridade": "Ensino Superior",
    "taxa": null,
    "prova_data": "2027-01-31T00:00:00+00:00",
    "edital_numero": "01/2026",
    "edital_data": "2026-05-14T00:00:00+00:00",
    "inscricao_inicio": "2026-07-23T00:00:00+00:00",
    "inscricao_fim": "2026-09-18T23:59:00+00:00",
    "link_pagina": "https://www.cotec.fadenor.com.br/informacoes/28/",
    "link_edital": "https://anexos-r2.selecao.net.br/uploads/846/concursos/28/anexos/564c58d4-58da-43ea-b120-23e38c000d71.pdf",
    "link_inscricao": "https://www.cotec.fadenor.com.br/login/sair/?redir=%2Ftermo%2F28%2F"
  },
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
  },
  "publication_audit": {
    "status": "MATCH",
    "expected_count": 8,
    "actual_count": 8,
    "expected_titles": [
      "Edital (Conforme 2ª Retificação) 26/08/2026",
      "1ª_Retificação 16/07/2026",
      "2ª_Retificação 26/08/2026",
      "ANEXO I - ESPECIFICAÇÃO DOS CARGOS (Conforme a 1ª Retificação) 16/07/2026",
      "ANEXO II - ESPECIFICAÇÃO DAS PROVAS DE MÚLTIPLA ESCOLHA (Conforme a 1ª Retificação) 16/07/2026",
      "ANEXO III - ATRIBUIÇÕES DOS CARGOS (Conforme a 1ª Retificação) 16/07/2026",
      "ANEXO IV - PROGRAMA DAS PROVAS DE MÚLTIPLA ESCOLHA (Conforme a 1ª Retificação) 16/07/2026",
      "RESULTADO DO PEDIDO DE ISENÇÃO (APÓS RECURSOS) 14/08/2026"
    ],
    "actual_titles": [
      "Edital (Conforme 2ª Retificação) 26/08/2026",
      "1ª_Retificação 16/07/2026",
      "2ª_Retificação 26/08/2026",
      "ANEXO I - ESPECIFICAÇÃO DOS CARGOS (Conforme a 1ª Retificação) 16/07/2026",
      "ANEXO II - ESPECIFICAÇÃO DAS PROVAS DE MÚLTIPLA ESCOLHA (Conforme a 1ª Retificação) 16/07/2026",
      "ANEXO III - ATRIBUIÇÕES DOS CARGOS (Conforme a 1ª Retificação) 16/07/2026",
      "ANEXO IV - PROGRAMA DAS PROVAS DE MÚLTIPLA ESCOLHA (Conforme a 1ª Retificação) 16/07/2026",
      "RESULTADO DO PEDIDO DE ISENÇÃO (APÓS RECURSOS) 14/08/2026"
    ],
    "invalid_actual_titles": [],
    "missing_titles": [],
    "missing_links": []
  }
}
```

### 30. MS Concursos (`msconcursos_open`)
- Crawler: `success`; verificação: `NOT_AUDITED`
- Visíveis independentemente: 29; processados: 2
- Método: official_html_observer
- URLs de evidência: https://www.msconcursos.com.br, https://msconcursos.com.br/concurso/54/concurso-publico-para-medico-e-medico-plantonista-prefeitura-de-santana-de-parnaiba-sp

```json
{
  "expected": {
    "link_inscricao": "https://msconcursos.com.br/concurso/54/login-area-do-candidato/54/concurso-publico-para-medico-e-medico-plantonista-prefeitura-de-santana-de-parnaiba-sp"
  },
  "actual": {
    "titulo": "CONCURSO PÚBLICO PARA MÉDICO E MÉDICO PLANTONISTA - PREFEITURA DE SANTANA DE PARNAÍBA, SP | Concurso Público | MSCONCURSOS",
    "orgao": "PREFEITURA DE SANTANA DE PARNAÍBA, SP | Concurso Público | MSCONCURSOS",
    "modalidade": "Concurso Público",
    "cargo": "Vários cargos",
    "area": "saude",
    "cidade": null,
    "uf": null,
    "status": "Inscrições abertas",
    "vagas": 1,
    "salario_min": 13087.86,
    "salario_max": 14975.66,
    "escolaridade": null,
    "taxa": 13087.86,
    "prova_data": "2026-09-07T00:00:00+00:00",
    "edital_numero": null,
    "edital_data": null,
    "inscricao_inicio": "2026-08-19T00:00:00+00:00",
    "inscricao_fim": "2026-09-13T00:00:00+00:00",
    "link_pagina": "https://www.msconcursos.com.br/concurso/54/concurso-publico-para-medico-e-medico-plantonista-prefeitura-de-santana-de-parnaiba-sp",
    "link_edital": "https://www.msconcursos.com.br/concurso/54/arquivos/cp0526/documentos/2-edital-de-abertura-n-o-05-2026-concurso-publico-para-medico-e-medico-plantonista.pdf",
    "link_inscricao": "https://www.msconcursos.com.br/concurso/54/login-area-do-candidato/54/concurso-publico-para-medico-e-medico-plantonista-prefeitura-de-santana-de-parnaiba-sp"
  },
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
  },
  "publication_audit": {
    "status": "UNKNOWN",
    "expected_count": 0,
    "actual_count": 0,
    "expected_titles": [],
    "actual_titles": [],
    "invalid_actual_titles": [],
    "missing_titles": [],
    "missing_links": []
  }
}
```

### 33. Instituto ADM&TEC (`admtec_open`)
- Crawler: `success`; verificação: `NOT_AUDITED`
- Visíveis independentemente: 4; processados: 4
- Método: official_html_observer
- URLs de evidência: https://admtec.org.br/, https://admtec.org.br/concursos/publicacoes/MTEz/MTIx

```json
{
  "expected": {
    "titulo": "PREFEITURA MUNICIPAL DE PIRANHAS-ALAGOAS"
  },
  "actual": {
    "titulo": "PREFEITURA MUNICIPAL DE PIRANHAS",
    "orgao": "PREFEITURA MUNICIPAL DE PIRANHAS",
    "modalidade": "Concurso Público",
    "cargo": "GUARDA MUNICIPAL",
    "area": "seguranca_publica",
    "cidade": "Piranhas",
    "uf": "AL",
    "status": "Encerrado",
    "vagas": 6,
    "salario_min": 1621.0,
    "salario_max": 1621.0,
    "escolaridade": "Ensino Médio",
    "taxa": 125.0,
    "prova_data": "2026-05-22T00:00:00+00:00",
    "edital_numero": "06",
    "edital_data": null,
    "inscricao_inicio": "2026-04-10T00:00:00+00:00",
    "inscricao_fim": "2026-05-11T23:59:00+00:00",
    "link_pagina": "https://admtec.org.br/concursos/publicacoes/MTEz/MTIx",
    "link_edital": "https://cdn-arquivo.concursos.srv.br/AdmTec/00121/PUBLICACOES/Edital_de_Piranhas_retificado_22_04_2026_04_22_11_14_52.pdf",
    "link_inscricao": null
  },
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
    "link_inscricao": "UNKNOWN"
  },
  "publication_audit": {
    "status": "UNKNOWN",
    "expected_count": 0,
    "actual_count": 5,
    "expected_titles": [],
    "actual_titles": [
      "Lista preliminar de análise de pedidos de atendimento especial para realização da prova objetiva",
      "Lista preliminar de análise de pedidos de atendimento especial para realização da prova objetiva",
      "Respostas aos recursos da solicitação de isenção da taxa de inscrição",
      "Resultado final da solicitação de isenção da taxa de inscrição",
      "Resultado preliminar da solicitação de isenção da taxa de inscrição"
    ],
    "invalid_actual_titles": [],
    "missing_titles": [],
    "missing_links": []
  }
}
```

### 35. CPCon / UEPB Concursos (`cpcon_open`)
- Crawler: `success`; verificação: `NOT_AUDITED`
- Visíveis independentemente: UNKNOWN; processados: 10
- Método: official_html_observer
- URLs de evidência: https://cpcon.uepb.edu.br, https://cpcon.uepb.edu.br/prefeitura-municipal-de-guarabira/

```json
{
  "expected": {
    "titulo": "PREFEITURA MUNICIPAL DE GUARABIRA",
    "link_pagina": "https://cpcon.uepb.edu.br/prefeitura-municipal-de-guarabira/",
    "link_inscricao": "https://sistemas.cpcon.uepb.edu.br/sigeps-app/login"
  },
  "actual": {
    "titulo": "PREFEITURA MUNICIPAL DE GUARABIRA",
    "orgao": "PREFEITURA MUNICIPAL DE GUARABIRA",
    "modalidade": "Concurso Público",
    "cargo": null,
    "area": "saude",
    "cidade": "GUARABIRA",
    "uf": "PB",
    "status": "Inscrições abertas",
    "vagas": 170,
    "salario_min": 1621.0,
    "salario_max": 8472.0,
    "escolaridade": "Pós-graduação",
    "taxa": null,
    "prova_data": null,
    "edital_numero": null,
    "edital_data": null,
    "inscricao_inicio": "2026-08-13T00:00:00+00:00",
    "inscricao_fim": "2026-08-19T23:59:00+00:00",
    "link_pagina": "https://cpcon.uepb.edu.br/prefeitura-municipal-de-guarabira/",
    "link_edital": "https://cpcon.uepb.edu.br/download/retificacao-edital-normativo-de-concurso-publico-no-001-2026-pmg-pb/?wpdmdl=10225&refresh=6a942dce9947b1788095950",
    "link_inscricao": "https://sistemas.cpcon.uepb.edu.br/sigeps-app/login"
  },
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
  },
  "publication_audit": {
    "status": "UNKNOWN",
    "expected_count": 0,
    "actual_count": 11,
    "expected_titles": [],
    "actual_titles": [
      "Retificacao Anexo Ii Conteudo Programatico",
      "Retificacao Anexo Vi Autodeclaracao De Pessoa Preta Ou Parda Indigena Ou Quilombola",
      "Retificacao Edital Normativo De Concurso Publico No 001 2026 Pmg Pb",
      "Resposta As Impugnacoes 25",
      "Anexo I Cronograma Provisorio 67",
      "Anexo Ii Conteudo Programatico 67",
      "Anexo Iii Atribuicoes Dos Cargos 31",
      "Anexo Iv Declaracao De Uso De Nome Social 43",
      "Anexo V Formulario Para Envio De Titulos 25",
      "Anexo Vi Autodeclaracao De Pessoa Indigena Ou Quilombola",
      "Edital Normativo De Concurso Publico No 001 2026 Pmg Pb"
    ],
    "invalid_actual_titles": [],
    "missing_titles": [],
    "missing_links": []
  }
}
```

### 36. FUNVAPI Concursos (`funvapi_open`)
- Crawler: `success`; verificação: `NOT_AUDITED`
- Visíveis independentemente: UNKNOWN; processados: 6
- Método: official_html_observer
- URLs de evidência: https://www.funvapi.com.br, https://funvapi.com.br/index.php/2026/08/27/prefeitura-municipal-de-belo-jardim-pe/, https://funvapi.com.br/wp-content/uploads/2026/08/EDITAL-DE-CONCURSO-PUBLICO-BELO-JARDIM-PERNAMBUCO-001-2026.pdf

```json
{
  "expected": {
    "titulo": "PREFEITURA MUNICIPAL DE BELO JARDIM – PE",
    "link_pagina": "https://funvapi.com.br/index.php/2026/08/27/prefeitura-municipal-de-belo-jardim-pe/",
    "link_edital": "https://funvapi.com.br/wp-content/uploads/2026/08/EDITAL-DE-CONCURSO-PUBLICO-BELO-JARDIM-PERNAMBUCO-001-2026.pdf"
  },
  "actual": {
    "titulo": "PREFEITURA MUNICIPAL DE BELO JARDIM – PE",
    "orgao": "PREFEITURA MUNICIPAL DE BELO JARDIM – PE – Fundação Vale do Piauí",
    "modalidade": "Concurso Público",
    "cargo": null,
    "area": "assistencia_social",
    "cidade": "Belo Jardim",
    "uf": "PE",
    "status": "Em andamento",
    "vagas": 150,
    "salario_min": 1800.0,
    "salario_max": 4500.0,
    "escolaridade": null,
    "taxa": 121.8,
    "prova_data": null,
    "edital_numero": null,
    "edital_data": null,
    "inscricao_inicio": "2026-05-29T00:00:00+00:00",
    "inscricao_fim": "2026-05-29T23:59:00+00:00",
    "link_pagina": "https://funvapi.com.br/index.php/2026/08/27/prefeitura-municipal-de-belo-jardim-pe/",
    "link_edital": "https://funvapi.com.br/wp-content/uploads/2026/08/EDITAL-DE-CONCURSO-PUBLICO-BELO-JARDIM-PERNAMBUCO-001-2026.pdf",
    "link_inscricao": null
  },
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
  },
  "publication_audit": {
    "status": "MATCH",
    "expected_count": 1,
    "actual_count": 1,
    "expected_titles": [
      "EDITAL DE CONCURSO PÚBLICO Nº 001/2026"
    ],
    "actual_titles": [
      "EDITAL DE CONCURSO PÚBLICO Nº 001/2026"
    ],
    "invalid_actual_titles": [],
    "missing_titles": [],
    "missing_links": []
  }
}
```

### 39. Instituto Avalia (`avalia_open`)
- Crawler: `success`; verificação: `NOT_AUDITED`
- Visíveis independentemente: 99; processados: 1
- Método: official_html_observer
- URLs de evidência: https://www2.avalia.org.br/concursos.jsp, https://www2.avalia.org.br/concurso.jsp?id=630

```json
{
  "expected": {
    "link_inscricao": "https://link.avalia.org.br/open?chave=jG2b886%2B%2FY2BULGuSK4lXqHc2ugVtjcB4KIPk1Pwz6%2BOYWblVub87e3PH4jCE3gKscLHKNIZLfjmTCkRB2O8iUErLKCPXsLWe3j%2FE2OTaXxWeHS2QSetH5i1%2BFMMF3MlrVt3Zy%2BnJlYjQXs%2B5RBuh7RF7PHUyh0JWd3Fr%2FceOqDugXZRhZW4fpb1GGffS9KwFe5L%2FW2bKjmS3WF9%2Bt8hPGuYFZKyBzeyin60OIYXKGuzV6%2BH4I6RbtlXiAlG43vA3d6%2BOXwV9uULQtsClTR%2BS%2FDihFSdrvWaYA29ld5Gl9%2FetXF7hqNAwz1%2FY4v5RtL%2FYOaKIGjcUWLuZxeP0WC9AASLmGULlkfzOaX%2BOYFDALvDpMXLV8YdhOhAnUAxJlpURrYnhhcYSaCOFxq9eBIEIDRBCHWxACQ7ThCDm2bhNJwRu%2FyOeAjr0opIbX2fx%2B2R%2F2%2Btrmz63y4tHDavOsYLhhV%2FPmspraVCXBAfHzBLV76oglChwHor4RfcMMoUIns7kFrgLCXhcIbAJ1ZBgP5KIi%2FFQyg4VwsXXgadNUadhW3NdQ11NaQK%2F9fROfR3iGbyGKW1IM4z3yLBhsPBuVf6V1EJRZmYpGBCuIczdjkIYzhlvweJ4dyX8Pvcz9oTibN%2ByZW7vk7p93%2F%2BWoOAD1ny33NnGbtgHrgtcjpWvuc4XE6e2idp6DH0U1F7K5c4bDBzZARWiWh4t00i7ClJxRGQfLvi7wGHK6TUjn26ZBu3Etac7v%2F20iZwd1IVqZoCpAHH6Wk%2FAOA3LsA4vBh7rur%2FzMIfzFQh45zkKaoYWJDjhJoasAiH7MUaBR83czsf0SLnmMXcPeHqS1PjOhzNaKMJX2sWOw%2FhbXFupI2%2BPqqUbYgVWJEHmzgBSV%2Bv0D9dYD%2FSbXHonkbS6GbAW%2B7ZddP3gamhCQHZoUYLKZc4jzOABaiX7Fqzzn56URDHq%2BP9lDcqU5ri5tFRFkLxzSc01CIpCunlyO924fB4HhXITc1jNPoy%2B4FLmwLAZyd4AzFSghtszowD190aLDARrUULCEWJ96YZv3snxAo1tH0ywLUhNSsA1ednf3W4Ud74QeQbhuJe6MUITViH8HzwFu3QPUEnkr4hdSO%2BeM93H2Ai1yw43yeTnwxE8z33zzzuaCF0esBknMclWvKOvZi3eihN93ZVCMPqSVO8WTWE%2FtpEMxwUq8BBGNcw4Anb2fDarLaHcGg8WoUtE1JuAZMvU2nimL3gH4my7hwCHbuX%2FuukcqYimCQGVCluRYQsd5nmi%2FVZxfeRnvtfka9bu2w7FBclmjxAI6YWZl4SYpGcMY9yyf%2FaNSA%2FvgYFxwa%2BLBGuowF9HCBuANXnZ391uFHe%2BEHkG4biXujFCE1Yh%2FB88Bbt0D1BJ5K%2BIXUjvnjPdx9gItcsON8nk58MRPM998887mghdHrAZBkmIHRO4MiRQnyadsat9F%2B1gWuorX%2B6aWQkYFTZAY%2FPrazU2YocXwKfL7buZ4KmDqreEmJjd8z7yGPMzBBup%2BNam1mXEcF7Uhc%2FtcNUfiXvh7L0vGodXkq4OmkYH9n2qMaulUkHo8sgr3RA5%2BY9J5jXBVHHcy9CZi1pmXChYvn%2Fb9VEcli59IikHq5CJDxZhMoUnkupBVqK234Ajg00mzJIs%2F4TrcHgAYiH4jyDQTcSvtI%2BGR3lqad4PNikiv8iTnUGNB6XPKx9BLa14oowy%2BpQcemnpbNRQc1QVNCr%2BqYwBmAa10UPaYiraCPATjnFItAssTZdxtEwChZDpYEvL6aYJWRb7Uwb6ggV2IOjiYHB4l6OADjbIPwLA3loZawNMt1wmJfu6n%2FqYGKEGWIa93%2FU25r9n1jNBdB%2BJEgOxvCBl0%2B3VbToRrWJgnUDgXp4972LJa%2FfZn210lcS0jsHtd1f8kdcycK4erYH040ik6j4pJGHW2D2Ua1EUBheLxt8m1mpeczJ4ER9OFXFkQXDyk5pCJYonmHkNIZYEdv9qIO%2BHtyf1HNz3cPiTGo%2FtVa7axiWzRHB4vi5n2hxcn3P%2FC4edyk99tjpyL4n%2BQ%2BihAYHOSfpLPNNZV0IMcXhD2zNxaEr0TTfgpmxq21aORSwcVhTFz0RmkOZOFe959ydPFqSkFpT1553swruqLbvpr652MOliGhrWrLsWj3lIlKKKdQBJksV0PbT0llJP146hAi7cyXnt6x1RVxpPrgc0YpnKeyjyFI5F2%2Brup67Ycqj%2FHp3mpwkVDWww%2Bfrv22kQBtbUZHeGxZSspD8Sd5xYzBWRhiS0pvN3PQ6k1sWV0FykvF7mTpHvR7qujCwDevKr%2BmzKKfgb%2FVMMJJuIh4l1ZqOv6gsiE9GZ4kiwmBr6HeXUNzUIKbCdOv37Yz73Ca0XjcdCJzUXMvdPGvVMLPzkCeFwNceBceWOnY0SMomTwrwjdp3K27WsVcDNVEgQTxnIKM39fd%2BHs3olH7aGta3tHFJ14VWXhi0u6llv1PA6bbJXONzj3M7wm5KNItWqJanNVT7Gi7zqxTKJ3QAnuZOjWoF7f3IzEzk0FAmYKdgAUY3zdEUinNDltI2AyMGnXYJrLv5AAmZs4R41ZuABej92ArFyQQW%2FYdTlqA1UUozko9nsyeJDIle7qJ7KulbcnhC1nCM7IgSU%2BxsTAXIE6eUMOv0xNAx2x000kaACt8oW7Cgk6fEQdPQ4jAxj49Wd%2B9mv8Kc6qFeBc9CDTuD8xz%2FcQ2IIhQJpfzNctPGr%2B8dmxRPl4VX97Nhs3gsF1HX%2Ft0DHWDo3OhLDxzIy2%2BvdW%2BSWJlXLGe5pq2tS8TaBHxVCm1ftlnCvFSlm0gXJoliucmkuBaXZe6%2FrmxzOPAUoWzvDoW9bZUbwBfQ7djTK51Jy%2F2M5Ih1Fyu4fbtYkP3%2Fhw1CagCzCq4VCxkOSf2mFGCXfV64X8WA5rKMmHuzuJ87n%2BRoRD1UOXQUfCMh4bfAqnq6%2FHiH%2Fn5vaNd70JjJmjvA271Z35C7wpcqZ6VwCKdOS6yYmvB11PGZXa0I97l30xOklBsvGBaGrkifrxJTe7rjBXVhGv176roAIHNEL61z4%2FuAe6o%3D"
  },
  "actual": {
    "titulo": "Concurso Público EPAGRI - Edital 001/2026",
    "orgao": "EPAGRI",
    "modalidade": "Concurso Público",
    "cargo": null,
    "area": "juridica",
    "cidade": null,
    "uf": "SC",
    "status": "Inscrições abertas",
    "vagas": 40,
    "salario_min": 4362.02,
    "salario_max": 16990.33,
    "escolaridade": null,
    "taxa": 200.0,
    "prova_data": null,
    "edital_numero": null,
    "edital_data": null,
    "inscricao_inicio": "2026-09-24T00:00:00+00:00",
    "inscricao_fim": "2026-09-25T00:00:00+00:00",
    "link_pagina": "https://www2.avalia.org.br/concurso.jsp?id=630",
    "link_edital": "https://arquivos-site.avalia.org.br/publicacoes/f68d5d73-0940-4165-8488-fb9c750cc23c.pdf",
    "link_inscricao": "https://link.avalia.org.br/open?chave=jG2b886%2B%2FY2BULGuSK4lXqHc2ugVtjcB4KIPk1Pwz6%2BOYWblVub87e3PH4jCE3gKscLHKNIZLfjmTCkRB2O8iUErLKCPXsLWe3j%2FE2OTaXxWeHS2QSetH5i1%2BFMMF3MlrVt3Zy%2BnJlYjQXs%2B5RBuh7RF7PHUyh0JWd3Fr%2FceOqDugXZRhZW4fpb1GGffS9KwFe5L%2FW2bKjmS3WF9%2Bt8hPGuYFZKyBzeyin60OIYXKGuzV6%2BH4I6RbtlXiAlG43vA3d6%2BOXwV9uULQtsClTR%2BS%2FDihFSdrvWaYA29ld5Gl9%2FetXF7hqNAwz1%2FY4v5RtL%2FYOaKIGjcUWLuZxeP0WC9AASLmGULlkfzOaX%2BOYFDALvDpMXLV8YdhOhAnUAxJlpURrYnhhcYSaCOFxq9eBIEIDRBCHWxACQ7ThCDm2bhNJwRu%2FyOeAjr0opIbX2fx%2B2R%2F2%2Btrmz63y4tHDavOsYLhhV%2FPmspraVCXBAfHzBLV76oglChwHor4RfcMMoUIns7kFrgLCXhcIbAJ1ZBgP5KIi%2FFQyg4VwsXXgadNUadhW3NdQ11NaQK%2F9fROfR3iGbyGKW1IM4z3yLBhsPBuVf6V1EJRZmYpGBCuIczdjkIYzhlvweJ4dyX8Pvcz9oTibN%2ByZW7vk7p93%2F%2BWoOAD1ny33NnGbtgHrgtcjpWvuc4XE6e2idp6DH0U1F7K5c4bDBzZARWiWh4t00i7ClJxRGQfLvi7wGHK6TUjn26ZBu3Etac7v%2F20iZwd1IVqZoCpAHH6Wk%2FAOA3LsA4vBh7rur%2FzMIfzFQh45zkKaoYWJDjhJoasAiH7MUaBR83czsf0SLnmMXcPeHqS1PjOhzNaKMJX2sWOw%2FhbXFupI2%2BPqqUbYgVWJEHmzgBSV%2Bv0D9dYD%2FSbXHonkbS6GbAW%2B7ZddP3gamhCQHZoUYLKZc4jzOABaiX7Fqzzn56URDHq%2BP9lDcqU5ri5tFRFkLxzSc01CIpCunlyO924fB4HhXITc1jNPoy%2B4FLmwLAZyd4AzFSghtszowD190aLDARrUULCEWJ96YZv3snxAo1tH0ywLUhNSsA1ednf3W4Ud74QeQbhuJe6MUITViH8HzwFu3QPUEnkr4hdSO%2BeM93H2Ai1yw43yeTnwxE8z33zzzuaCF0esBknMclWvKOvZi3eihN93ZVCMPqSVO8WTWE%2FtpEMxwUq8BBGNcw4Anb2fDarLaHcGg8WoUtE1JuAZMvU2nimL3gH4my7hwCHbuX%2FuukcqYimCQGVCluRYQsd5nmi%2FVZxfeRnvtfka9bu2w7FBclmjxAI6YWZl4SYpGcMY9yyf%2FaNSA%2FvgYFxwa%2BLBGuowF9HCBuANXnZ391uFHe%2BEHkG4biXujFCE1Yh%2FB88Bbt0D1BJ5K%2BIXUjvnjPdx9gItcsON8nk58MRPM998887mghdHrAZBkmIHRO4MiRQnyadsat9F%2B1gWuorX%2B6aWQkYFTZAY%2FPrazU2YocXwKfL7buZ4KmDqreEmJjd8z7yGPMzBBup%2BNam1mXEcF7Uhc%2FtcNUfiXvh7L0vGodXkq4OmkYH9n2qMaulUkHo8sgr3RA5%2BY9J5jXBVHHcy9CZi1pmXChYvn%2Fb9VEcli59IikHq5CJDxZhMoUnkupBVqK234Ajg00mzJIs%2F4TrcHgAYiH4jyDQTcSvtI%2BGR3lqad4PNikiv8iTnUGNB6XPKx9BLa14oowy%2BpQcemnpbNRQc1QVNCr%2BqYwBmAa10UPaYiraCPATjnFItAssTZdxtEwChZDpYEvL6aYJWRb7Uwb6ggV2IOjiYHB4l6OADjbIPwLA3loZawNMt1wmJfu6n%2FqYGKEGWIa93%2FU25r9n1jNBdB%2BJEgOxvCBl0%2B3VbToRrWJgnUDgXp4972LJa%2FfZn210lcS0jsHtd1f8kdcycK4erYH040ik6j4pJGHW2D2Ua1EUBheLxt8m1mpeczJ4ER9OFXFkQXDyk5pCJYonmHkNIZYEdv9qIO%2BHtyf1HNz3cPiTGo%2FtVa7axiWzRHB4vi5n2hxcn3P%2FC4edyk99tjpyL4n%2BQ%2BihAYHOSfpLPNNZV0IMcXhD2zNxaEr0TTfgpmxq21aORSwcVhTFz0RmkOZOFe959ydPFqSkFpT1553swruqLbvpr652MOliGhrWrLsWj3lIlKKKdQBJksV0PbT0llJP146hAi7cyXnt6x1RVxpPrgc0YpnKeyjyFI5F2%2Brup67Ycqj%2FHp3mpwkVDWww%2Bfrv22kQBtbUZHeGxZSspD8Sd5xYzBWRhiS0pvN3PQ6k1sWV0FykvF7mTpHvR7qujCwDevKr%2BmzKKfgb%2FVMMJJuIh4l1ZqOv6gsiE9GZ4kiwmBr6HeXUNzUIKbCdOv37Yz73Ca0XjcdCJzUXMvdPGvVMLPzkCeFwNceBceWOnY0SMomTwrwjdp3K27WsVcDNVEgQTxnIKM39fd%2BHs3olH7aGta3tHFJ14VWXhi0u6llv1PA6bbJXONzj3M7wm5KNItWqJanNVT7Gi7zqxTKJ3QAnuZOjWoF7f3IzEzk0FAmYKdgAUY3zdEUinNDltI2AyMGnXYJrLv5AAmZs4R41ZuABej92ArFyQQW%2FYdTlqA1UUozko9nsyeJDIle7qJ7KulbcnhC1nCM7IgSU%2BxsTAXIE6eUMOv0xNAx2x000kaACt8oW7Cgk6fEQdPQ4jAxj49Wd%2B9mv8Kc6qFeBc9CDTuD8xz%2FcQ2IIhQJpfzNctPGr%2B8dmxRPl4VX97Nhs3gsF1HX%2Ft0DHWDo3OhLDxzIy2%2BvdW%2BSWJlXLGe5pq2tS8TaBHxVCm1ftlnCvFSlm0gXJoliucmkuBaXZe6%2FrmxzOPAUoWzvDoW9bZUbwBfQ7djTK51Jy%2F2M5Ih1Fyu4fbtYkP3%2Fhw1CagCzCq4VCxkOSf2mFGCXfV64X8WA5rKMmHuzuJ87n%2BRoRD1UOXQUfCMh4bfAqnq6%2FHiH%2Fn5vaNd70JjJmjvA271Z35C7wpcqZ6VwCKdOS6yYmvB11PGZXa0I97l30xOklBsvGBaGrkifrxJTe7rjBXVhGv176roAIHNEL61z4%2FuAe6o%3D"
  },
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
  },
  "publication_audit": {
    "status": "UNKNOWN",
    "expected_count": 0,
    "actual_count": 0,
    "expected_titles": [],
    "actual_titles": [],
    "invalid_actual_titles": [],
    "missing_titles": [],
    "missing_links": []
  }
}
```

### 40. UFU / DIRPS - Seleções e Concursos (`ufu_selection`)
- Crawler: `success`; verificação: `NOT_AUDITED`
- Visíveis independentemente: 11; processados: 11
- Método: official_html_observer
- URLs de evidência: https://www.portalselecao.ufu.br/servicos/Edital/listar/concursos, https://www.portalselecao.ufu.br/servicos/Edital/cronograma/1843, https://www.portalselecao.ufu.br/servicos/ArquivoAdministrativo/download/0981a060af516a1cb54f2f9a1ed5473e

```json
{
  "expected": {
    "link_pagina": "https://www.portalselecao.ufu.br/servicos/Edital/cronograma/1843",
    "link_edital": "https://www.portalselecao.ufu.br/servicos/ArquivoAdministrativo/download/0981a060af516a1cb54f2f9a1ed5473e",
    "link_inscricao": "https://www.portalselecao.ufu.br/servicos/Edital/listar/colaboradores"
  },
  "actual": {
    "titulo": "Processo Seletivo Simplificado Visitante INFIS - Edital Nº 144/2026",
    "orgao": "Universidade Federal de Uberlândia",
    "modalidade": "Processo Seletivo Simplificado",
    "cargo": "Processo Seletivo Simplificado para a contratação de Professor(a) Visitante e Professor(a) e Pesquisador(a) Visitante.",
    "area": "educacao",
    "cidade": "Uberlândia",
    "uf": "MG",
    "status": "Inscrições abertas",
    "vagas": null,
    "salario_min": null,
    "salario_max": null,
    "escolaridade": null,
    "taxa": null,
    "prova_data": null,
    "edital_numero": "144/2026",
    "edital_data": null,
    "inscricao_inicio": "2026-08-10T00:00:00+00:00",
    "inscricao_fim": "2026-08-10T16:00:00+00:00",
    "link_pagina": "https://www.portalselecao.ufu.br/servicos/Edital/cronograma/1843",
    "link_edital": "https://www.portalselecao.ufu.br/servicos/ArquivoAdministrativo/download/0981a060af516a1cb54f2f9a1ed5473e",
    "link_inscricao": "https://www.portalselecao.ufu.br/servicos/Edital/listar/colaboradores"
  },
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
  },
  "publication_audit": {
    "status": "MATCH",
    "expected_count": 4,
    "actual_count": 4,
    "expected_titles": [
      "15:53 Retificação do Edital de Condições Gerais",
      "09:43 Formulário de Inscrição",
      "16:05 Edital de Condições Gerais",
      "16:05 Edital de Condições Específicas"
    ],
    "actual_titles": [
      "15:53 Retificação do Edital de Condições Gerais",
      "09:43 Formulário de Inscrição",
      "16:05 Edital de Condições Gerais",
      "16:05 Edital de Condições Específicas"
    ],
    "invalid_actual_titles": [],
    "missing_titles": [],
    "missing_links": []
  }
}
```

### 42. Instituto Quadrix (`quadrix_open`)
- Crawler: `success`; verificação: `NOT_AUDITED`
- Visíveis independentemente: 2; processados: 2
- Método: official_html_observer
- URLs de evidência: https://quadrix.org.br/index/abertos/, https://quadrix.org.br/informacoes/3070/, https://anexos-r2.selecao.net.br/uploads/861/concursos/3070/anexos/f196fabd-7d4e-49e6-bb8c-1fcc400cab06.pdf

```json
{
  "expected": {
    "link_edital": "https://anexos-r2.selecao.net.br/uploads/861/concursos/3070/anexos/f196fabd-7d4e-49e6-bb8c-1fcc400cab06.pdf",
    "link_inscricao": "https://quadrix.org.br/login/sair/?redir=%2Ftermo%2F3070%2F"
  },
  "actual": {
    "titulo": "Conselho Regional de Educação Física da 20ª Região (CREF-SE)",
    "orgao": "Conselho Regional de Educação Física da 20ª Região (CREF-SE)",
    "modalidade": "Concurso Público",
    "cargo": "Vários cargos",
    "area": "multiplas",
    "cidade": "Aracaju",
    "uf": "SE",
    "status": "Inscrições abertas",
    "vagas": 170,
    "salario_min": 2499.78,
    "salario_max": 5416.2,
    "escolaridade": null,
    "taxa": 60.0,
    "prova_data": "2026-10-13T00:00:00+00:00",
    "edital_numero": "01/2026",
    "edital_data": "2026-08-17T00:00:00+00:00",
    "inscricao_inicio": "2026-08-17T00:00:00+00:00",
    "inscricao_fim": "2026-09-21T23:59:00+00:00",
    "link_pagina": "https://quadrix.org.br/informacoes/3070/",
    "link_edital": "https://anexos-r2.selecao.net.br/uploads/861/concursos/3070/anexos/f196fabd-7d4e-49e6-bb8c-1fcc400cab06.pdf",
    "link_inscricao": "https://quadrix.org.br/login/sair/?redir=%2Ftermo%2F3070%2F"
  },
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
  },
  "publication_audit": {
    "status": "MATCH",
    "expected_count": 2,
    "actual_count": 2,
    "expected_titles": [
      "Edital nº 1 (abertura) 17/08/2026",
      "Cronograma 17/08/2026"
    ],
    "actual_titles": [
      "Edital nº 1 (abertura) 17/08/2026",
      "Cronograma 17/08/2026"
    ],
    "invalid_actual_titles": [],
    "missing_titles": [],
    "missing_links": []
  }
}
```

### 44. Instituto Verbena / UFG (`verbena_selection`)
- Crawler: `success`; verificação: `NOT_AUDITED`
- Visíveis independentemente: UNKNOWN; processados: 4
- Método: official_html_observer
- URLs de evidência: https://institutoverbena.ufg.br, https://sistemas.institutoverbena.ufg.br/2026/concurso-prefeitura-minacu/, https://sistemas.institutoverbena.ufg.br/2026/concurso-prefeitura-minacu/9-edital/178-edital-de-abertura-nº-01-2026-consolidado-pelo-edital-complementar-nº-02-2026.html

```json
{
  "expected": {
    "titulo": "IV - Concurso Público da Prefeitura Municipal de Minaçu - GO",
    "modalidade": "Concurso Público",
    "cidade": "Minaçu",
    "uf": "GO",
    "link_edital": "https://sistemas.institutoverbena.ufg.br/2026/concurso-prefeitura-minacu/9-edital/178-edital-de-abertura-nº-01-2026-consolidado-pelo-edital-complementar-nº-02-2026.html",
    "link_inscricao": "https://sistemas.institutoverbena.ufg.br/2026/concurso-prefeitura-minacu/10-comunicados/170-realizar-inscrição.html"
  },
  "actual": {
    "titulo": "IV - Concurso Público da Prefeitura Municipal de Minaçu - GO",
    "orgao": "Prefeitura Municipal de Minaçu - GO",
    "modalidade": "Concurso Público",
    "cargo": null,
    "area": "saude",
    "cidade": "Minaçu",
    "uf": "GO",
    "status": "Inscrições abertas",
    "vagas": null,
    "salario_min": 21783.92,
    "salario_max": 21783.92,
    "escolaridade": null,
    "taxa": null,
    "prova_data": "2026-08-30T00:00:00+00:00",
    "edital_numero": null,
    "edital_data": null,
    "inscricao_inicio": "2026-08-26T00:00:00+00:00",
    "inscricao_fim": "2026-09-16T00:00:00+00:00",
    "link_pagina": "https://sistemas.institutoverbena.ufg.br/2026/concurso-prefeitura-minacu/",
    "link_edital": "https://sistemas.institutoverbena.ufg.br/2026/concurso-prefeitura-minacu/9-edital/178-edital-de-abertura-nº-01-2026-consolidado-pelo-edital-complementar-nº-02-2026.html",
    "link_inscricao": "https://sistemas.institutoverbena.ufg.br/2026/concurso-prefeitura-minacu/10-comunicados/170-realizar-inscrição.html"
  },
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
  },
  "publication_audit": {
    "status": "MATCH",
    "expected_count": 32,
    "actual_count": 33,
    "expected_titles": [
      "Edital Complementar Nº 02/2026",
      "Edital Complementar Nº 02/2026",
      "Edital de Abertura Nº 01/2026 - Consolidado pelo Edital Complementar Nº 02/2026",
      "Edital de Abertura Nº 01/2026 - Consolidado pelo Edital Complementar Nº 02/2026",
      "Edital Complementar Nº 01/2026",
      "Edital Complementar Nº 01/2026",
      "Realizar Inscrição - Cronograma B",
      "Realizar Inscrição - Cronograma B",
      "Local e Horário de Realização da Prova Objetiva",
      "Solicitar a Devolução de Pagamento da Taxa de Inscrição - para os Cargos de Médico Anestesista, Médico Cardiologista, Médico, Médico Dermatologista, Médico Endocrinologista, Médico Ortopedista/Traumatologista, Médico Pediatra, Médico Psiquiatra",
      "Solicitar a Devolução de Pagamento da Taxa de Inscrição - para os Cargos de Médico Anestesista, Médico Cardiologista, Médico, Médico Dermatologista, Médico Endocrinologista, Médico Ortopedista/Traumatologista, Médico Pediatra, Médico Psiquiatra",
      "Resultado Final da Análise da Documentação Comprobatória de ter Exercido a Função de Jurado(a)",
      "Resultado Final da Análise da Documentação Comprobatória de ter Exercido a Função de Jurado(a)",
      "Resultado Final da Análise da Documentação para Concorrer à Reserva de Vagas (PcD) e/ou Requerer Tempo Adicional e/ou Correção Diferenciada",
      "Resultado Final da Análise da Documentação para Concorrer à Reserva de Vagas (PcD) e/ou Requerer Tempo Adicional e/ou Correção Diferenciada",
      "Resultado Final das Inscrições Homologadas",
      "Resultado Final das Inscrições Homologadas",
      "COMUNICADO Nº 01/2026 - Orientações Sobre o Procedimento para Solicitação de Devolução do Valor da Taxa de Inscrição Paga Exclusivamente para os Cargos de Médico",
      "COMUNICADO Nº 01/2026 - Orientações Sobre o Procedimento para Solicitação de Devolução do Valor da Taxa de Inscrição Paga Exclusivamente para os Cargos de Médico",
      "Resultado Preliminar da Análise da Documentação Comprobatória de ter Exercido a Função de Jurado(a)",
      "Resultado Preliminar da Análise da Documentação Comprobatória de ter Exercido a Função de Jurado(a)",
      "Resultado Preliminar da Análise da Documentação para Concorrer à Reserva de Vagas (PcD) e/ou Requerer Tempo Adicional e/ou Correção Diferenciada",
      "Resultado Preliminar da Análise da Documentação para Concorrer à Reserva de Vagas (PcD) e/ou Requerer Tempo Adicional e/ou Correção Diferenciada",
      "Resultado Preliminar das Inscrições Homologadas",
      "Resultado Preliminar das Inscrições Homologadas",
      "Resultado Final da Solicitação de Isenção do Pagamento da Taxa de Inscrição - Portal do(a) Candidato(a)",
      "Resultado Final da Solicitação de Isenção do Pagamento da Taxa de Inscrição - Portal do(a) Candidato(a)",
      "Resultado Final da Solicitação de Isenção do Pagamento da Taxa de Inscrição - Lista",
      "Resultado Final da Solicitação de Isenção do Pagamento da Taxa de Inscrição - Lista",
      "Resultado Preliminar da Solicitação de Isenção do Pagamento da Taxa de Inscrição - Portal do(a) Candidato(a)",
      "Resultado Preliminar da Solicitação de Isenção do Pagamento da Taxa de Inscrição - Lista",
      "Resultado Preliminar da Solicitação de Isenção do Pagamento da Taxa de Inscrição - Lista"
    ],
    "actual_titles": [
      "Edital Complementar Nº 02/2026",
      "Edital Complementar Nº 02/2026",
      "Edital de Abertura Nº 01/2026 - Consolidado pelo Edital Complementar Nº 02/2026",
      "Edital de Abertura Nº 01/2026 - Consolidado pelo Edital Complementar Nº 02/2026",
      "Edital Complementar Nº 01/2026",
      "Edital Complementar Nº 01/2026",
      "Realizar Inscrição - Cronograma B",
      "Realizar Inscrição - Cronograma B",
      "Local e Horário de Realização da Prova Objetiva",
      "Local e Horário de Realização da Prova Objetiva",
      "Solicitar a Devolução de Pagamento da Taxa de Inscrição - para os Cargos de Médico Anestesista, Médico Cardiologista, Médico, Médico Dermatologista, Médico Endocrinologista, Médico Ortopedista/Traumatologista, Médico Pediatra, Médico Psiquiatra",
      "Solicitar a Devolução de Pagamento da Taxa de Inscrição - para os Cargos de Médico Anestesista, Médico Cardiologista, Médico, Médico Dermatologista, Médico Endocrinologista, Médico Ortopedista/Traumatologista, Médico Pediatra, Médico Psiquiatra",
      "Resultado Final da Análise da Documentação Comprobatória de ter Exercido a Função de Jurado(a)",
      "Resultado Final da Análise da Documentação Comprobatória de ter Exercido a Função de Jurado(a)",
      "Resultado Final da Análise da Documentação para Concorrer à Reserva de Vagas (PcD) e/ou Requerer Tempo Adicional e/ou Correção Diferenciada",
      "Resultado Final da Análise da Documentação para Concorrer à Reserva de Vagas (PcD) e/ou Requerer Tempo Adicional e/ou Correção Diferenciada",
      "Resultado Final das Inscrições Homologadas",
      "Resultado Final das Inscrições Homologadas",
      "COMUNICADO Nº 01/2026 - Orientações Sobre o Procedimento para Solicitação de Devolução do Valor da Taxa de Inscrição Paga Exclusivamente para os Cargos de Médico",
      "COMUNICADO Nº 01/2026 - Orientações Sobre o Procedimento para Solicitação de Devolução do Valor da Taxa de Inscrição Paga Exclusivamente para os Cargos de Médico",
      "Resultado Preliminar da Análise da Documentação Comprobatória de ter Exercido a Função de Jurado(a)",
      "Resultado Preliminar da Análise da Documentação Comprobatória de ter Exercido a Função de Jurado(a)",
      "Resultado Preliminar da Análise da Documentação para Concorrer à Reserva de Vagas (PcD) e/ou Requerer Tempo Adicional e/ou Correção Diferenciada",
      "Resultado Preliminar da Análise da Documentação para Concorrer à Reserva de Vagas (PcD) e/ou Requerer Tempo Adicional e/ou Correção Diferenciada",
      "Resultado Preliminar das Inscrições Homologadas",
      "Resultado Preliminar das Inscrições Homologadas",
      "Resultado Final da Solicitação de Isenção do Pagamento da Taxa de Inscrição - Portal do(a) Candidato(a)",
      "Resultado Preliminar da Solicitação de Isenção do Pagamento da Taxa de Inscrição - Portal do(a) Candidato(a)",
      "Resultado Final da Solicitação de Isenção do Pagamento da Taxa de Inscrição - Lista",
      "Resultado Final da Solicitação de Isenção do Pagamento da Taxa de Inscrição - Lista",
      "Resultado Preliminar da Solicitação de Isenção do Pagamento da Taxa de Inscrição - Portal do(a) Candidato(a)",
      "Resultado Preliminar da Solicitação de Isenção do Pagamento da Taxa de Inscrição - Lista",
      "Resultado Preliminar da Solicitação de Isenção do Pagamento da Taxa de Inscrição - Lista"
    ],
    "invalid_actual_titles": [],
    "missing_titles": [],
    "missing_links": []
  }
}
```

### 45. Instituto IDIB (`idib_open`)
- Crawler: `success`; verificação: `NOT_AUDITED`
- Visíveis independentemente: UNKNOWN; processados: 6
- Método: official_html_observer
- URLs de evidência: https://idib.org.br, https://concurso.idib.org.br/Concurso.aspx?ID=355, https://concurso.idib.org.br/ConcursoDownloadArquivo.aspx?ID2=1&ID=6RSM3SMNO8WAIPSXXGMALX7W1PSKSK48G0RN8QL8KQUW67XJ5409HR8ESO2G8RSCNRFT4QQIK3KLWOFB8749.pdf

```json
{
  "expected": {
    "link_edital": "https://concurso.idib.org.br/ConcursoDownloadArquivo.aspx?ID2=1&ID=6RSM3SMNO8WAIPSXXGMALX7W1PSKSK48G0RN8QL8KQUW67XJ5409HR8ESO2G8RSCNRFT4QQIK3KLWOFB8749.pdf"
  },
  "actual": {
    "titulo": "CONCURSO PÚBLICO DA PREFEITURA MUNICIPAL DE MARCO/CE",
    "orgao": "PREFEITURA MUNICIPAL DE MARCO/CE",
    "modalidade": "Concurso Público",
    "cargo": "Vários cargos",
    "area": "multiplas",
    "cidade": "Marco",
    "uf": "CE",
    "status": "Em andamento",
    "vagas": 238,
    "salario_min": 1621.0,
    "salario_max": 12308.33,
    "escolaridade": null,
    "taxa": null,
    "prova_data": null,
    "edital_numero": null,
    "edital_data": null,
    "inscricao_inicio": "2026-07-15T00:00:00+00:00",
    "inscricao_fim": "2026-08-24T23:59:00+00:00",
    "link_pagina": "https://concurso.idib.org.br/Concurso.aspx?ID=355",
    "link_edital": "https://concurso.idib.org.br/ConcursoDownloadArquivo.aspx?ID2=1&ID=6RSM3SMNO8WAIPSXXGMALX7W1PSKSK48G0RN8QL8KQUW67XJ5409HR8ESO2G8RSCNRFT4QQIK3KLWOFB8749.pdf",
    "link_inscricao": null
  },
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
  },
  "publication_audit": {
    "status": "MATCH",
    "expected_count": 8,
    "actual_count": 8,
    "expected_titles": [
      "EDITAL Nº 001/2026",
      "RESULTADO DAS IMPUGNAÇÃO AO EDITAL",
      "RETIFICAÇÃO N°01/2026, DE 03 DE AGOSTO DE 2026, CONTEÚDO PROGRAMÁTICO DE TERAPEUTA OCUPACIONAL",
      "RETIFICAÇÃO N°02/2026, DE 10 DE AGOSTO DE 2026, ALTERAÇÃO NO NÚMERO DE QUESTÕES E PONTOS",
      "RETIFICAÇÃO N°03/2026, DE 18 DE AGOSTO DE 2026 - PRORROGAÇÃO NO PERÍODO DE INSCRIÇÕES",
      "RESULTADO PRELIMINAR DE LISTAS (ATEND. ESPECIAL E PCD)",
      "LINK - RESULTADO PRELIMINAR DE LISTAS (PCD)",
      "www.idib.org.br"
    ],
    "actual_titles": [
      "EDITAL Nº 001/2026",
      "RESULTADO DAS IMPUGNAÇÃO AO EDITAL",
      "RETIFICAÇÃO N°01/2026, DE 03 DE AGOSTO DE 2026, CONTEÚDO PROGRAMÁTICO DE TERAPEUTA OCUPACIONAL",
      "RETIFICAÇÃO N°02/2026, DE 10 DE AGOSTO DE 2026, ALTERAÇÃO NO NÚMERO DE QUESTÕES E PONTOS",
      "RETIFICAÇÃO N°03/2026, DE 18 DE AGOSTO DE 2026 - PRORROGAÇÃO NO PERÍODO DE INSCRIÇÕES",
      "RESULTADO PRELIMINAR DE LISTAS (ATEND. ESPECIAL E PCD)",
      "LINK - RESULTADO PRELIMINAR DE LISTAS (PCD)",
      "www.idib.org.br"
    ],
    "invalid_actual_titles": [],
    "missing_titles": [],
    "missing_links": []
  }
}
```

### 47. Elo Assessoria e Serviços (`elo_open`)
- Crawler: `success`; verificação: `NOT_AUDITED`
- Visíveis independentemente: UNKNOWN; processados: 7
- Método: official_html_observer
- URLs de evidência: https://eloassessoriaeservicos.com.br/concursos, https://novo.eloassessoriaeservicos.com.br//concurso/137, https://s3.amazonaws.com/sgs.eloassessoriaeservicos.com.br/cimag/1/1-2026/anexos/edital.pdf

```json
{
  "expected": {
    "link_edital": "https://s3.amazonaws.com/sgs.eloassessoriaeservicos.com.br/cimag/1/1-2026/anexos/edital.pdf",
    "link_inscricao": "https://elo.candidato.gestaoselecoes.com.br"
  },
  "actual": {
    "titulo": "Concurso Público - 1/2026 - CIMAG - CONSÓRCIO PÚBLICO INTERMUNICIPAL MULTIFINALITÁRIO DA MICRORREGIÃO DO CIRCUITO DAS ÁGUAS",
    "orgao": "CIMAG",
    "modalidade": "Concurso Público",
    "cargo": "Vários cargos",
    "area": "saude",
    "cidade": null,
    "uf": "MG",
    "status": "Inscrições em breve",
    "vagas": 2,
    "salario_min": null,
    "salario_max": null,
    "escolaridade": null,
    "taxa": 120.0,
    "prova_data": "2027-01-12T00:00:00+00:00",
    "edital_numero": "1/2026",
    "edital_data": null,
    "inscricao_inicio": "2026-10-24T00:00:00+00:00",
    "inscricao_fim": "2026-11-23T23:59:59+00:00",
    "link_pagina": "https://eloassessoriaeservicos.com.br/concurso/137",
    "link_edital": "https://s3.amazonaws.com/sgs.eloassessoriaeservicos.com.br/cimag/1/1-2026/anexos/edital.pdf",
    "link_inscricao": "https://elo.candidato.gestaoselecoes.com.br"
  },
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
  },
  "publication_audit": {
    "status": "MATCH",
    "expected_count": 1,
    "actual_count": 1,
    "expected_titles": [
      "Baixar Edital"
    ],
    "actual_titles": [
      "Baixar Edital"
    ],
    "invalid_actual_titles": [],
    "missing_titles": [],
    "missing_links": []
  }
}
```

### 49. Legalle Concursos (`legalle_open`)
- Crawler: `success`; verificação: `NOT_AUDITED`
- Visíveis independentemente: 4; processados: 4
- Método: official_html_observer
- URLs de evidência: https://portal.editais.legalleconcursos.com.br/edital, https://portal.editais.legalleconcursos.com.br/edital/ver/2557, https://s3.sa-east-1.amazonaws.com/cdn.legalle.com.br/edital/1/2557/36cdf58c0636416345eed85237af7977.pdf

```json
{
  "expected": {
    "link_edital": "https://s3.sa-east-1.amazonaws.com/cdn.legalle.com.br/edital/1/2557/36cdf58c0636416345eed85237af7977.pdf",
    "link_inscricao": "https://candidato.editais.legalleconcursos.com.br/inscricao/f7470ee07f5f3591f24e5f87a9e3695e"
  },
  "actual": {
    "titulo": "Detalhes do edital",
    "orgao": "Instituto Legalle",
    "modalidade": "Concurso Público",
    "cargo": "Vários cargos",
    "area": "multiplas",
    "cidade": "Relvado",
    "uf": "RS",
    "status": "Inscrições abertas",
    "vagas": null,
    "salario_min": null,
    "salario_max": null,
    "escolaridade": null,
    "taxa": null,
    "prova_data": null,
    "edital_numero": null,
    "edital_data": null,
    "inscricao_inicio": "2026-08-14T00:00:00+00:00",
    "inscricao_fim": "2026-09-13T18:00:00+00:00",
    "link_pagina": "https://portal.editais.legalleconcursos.com.br/edital/ver/2557",
    "link_edital": "https://s3.sa-east-1.amazonaws.com/cdn.legalle.com.br/edital/1/2557/36cdf58c0636416345eed85237af7977.pdf",
    "link_inscricao": "https://candidato.editais.legalleconcursos.com.br/inscricao/f7470ee07f5f3591f24e5f87a9e3695e"
  },
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
  },
  "publication_audit": {
    "status": "MATCH",
    "expected_count": 1,
    "actual_count": 1,
    "expected_titles": [
      "Edital de Abertura e Inscrições"
    ],
    "actual_titles": [
      "Edital de Abertura e Inscrições"
    ],
    "invalid_actual_titles": [],
    "missing_titles": [],
    "missing_links": []
  }
}
```

### 50. RBO Concursos e Assessoria (`rbo_open`)
- Crawler: `success`; verificação: `VERIFIED`
- Visíveis independentemente: 2; processados: 2
- Método: official_html_observer
- URLs de evidência: https://rboconcursos.selecao.net.br/index/abertos/, https://rboconcursos.selecao.net.br/informacoes/203/, https://anexos-r2.selecao.net.br/uploads/814/concursos/203/anexos/e1331b90-f1d9-440c-bb77-b17908b26cb8.pdf

```json
{
  "expected": {
    "titulo": "Concurso Público - 02/2026 - Prefeitura da Estância Turística de Jahu- SP",
    "modalidade": "Concurso Público",
    "cidade": "Jahu",
    "uf": "SP",
    "link_edital": "https://anexos-r2.selecao.net.br/uploads/814/concursos/203/anexos/e1331b90-f1d9-440c-bb77-b17908b26cb8.pdf",
    "link_inscricao": "https://rboconcursos.selecao.net.br/login/sair/?redir=%2Ftermo%2F203%2F"
  },
  "actual": {
    "titulo": "Concurso Público - 02/2026 - Prefeitura da Estância Turística de Jahu- SP",
    "orgao": "Prefeitura da Estância Turística de Jahu",
    "modalidade": "Concurso Público",
    "cargo": "Vários cargos",
    "area": "multiplas",
    "cidade": "Jahu",
    "uf": "SP",
    "status": "Inscrições abertas",
    "vagas": 10,
    "salario_min": 60.0,
    "salario_max": 4751.52,
    "escolaridade": null,
    "taxa": null,
    "prova_data": null,
    "edital_numero": null,
    "edital_data": null,
    "inscricao_inicio": "2026-08-24T00:00:00+00:00",
    "inscricao_fim": "2026-09-25T23:59:00+00:00",
    "link_pagina": "https://rboconcursos.selecao.net.br/informacoes/203/",
    "link_edital": "https://anexos-r2.selecao.net.br/uploads/814/concursos/203/anexos/e1331b90-f1d9-440c-bb77-b17908b26cb8.pdf",
    "link_inscricao": "https://rboconcursos.selecao.net.br/login/sair/?redir=%2Ftermo%2F203%2F"
  },
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
  },
  "publication_audit": {
    "status": "MATCH",
    "expected_count": 2,
    "actual_count": 2,
    "expected_titles": [
      "EDITAL DE ABERTURA RETIFICADO 18/08/2026",
      "RETIFICAÇÃO Nº 01 DO EDITAL DE ABERTURA 25/08/2026"
    ],
    "actual_titles": [
      "EDITAL DE ABERTURA RETIFICADO 18/08/2026",
      "RETIFICAÇÃO Nº 01 DO EDITAL DE ABERTURA 25/08/2026"
    ],
    "invalid_actual_titles": [],
    "missing_titles": [],
    "missing_links": []
  }
}
```

### 53. Instituto Nosso Rumo (`nossorumo_open`)
- Crawler: `success`; verificação: `NOT_AUDITED`
- Visíveis independentemente: UNKNOWN; processados: 2
- Método: official_html_observer
- URLs de evidência: https://www.nossorumo.org.br, https://nossorumo.org.br/#emandamento

```json
{
  "expected": {
    "link_inscricao": "https://nossorumo.org.br/Inscricao/ValidarCpf"
  },
  "actual": {
    "titulo": "CONCURSO PÚBLICO - PREFEITURA MUNICIPAL DE MAIRIPORÃ/SP - 01/2026",
    "orgao": "PREFEITURA MUNICIPAL DE MAIRIPORÃ",
    "modalidade": "Concurso Público",
    "cargo": "Vários cargos",
    "area": null,
    "cidade": "Mairiporã",
    "uf": "SP",
    "status": "Inscrições abertas",
    "vagas": 5,
    "salario_min": 2265.97,
    "salario_max": 5574.03,
    "escolaridade": "Múltiplas",
    "taxa": null,
    "prova_data": null,
    "edital_numero": null,
    "edital_data": null,
    "inscricao_inicio": "2026-08-06T00:00:00+00:00",
    "inscricao_fim": "2026-09-03T00:00:00+00:00",
    "link_pagina": "https://nossorumo.org.br/#emandamento",
    "link_edital": "https://nossorumo.org.br/Arquivos/Projetos/599-3731-639211150807491021.pdf",
    "link_inscricao": "https://nossorumo.org.br/Inscricao/ValidarCpf/NTk5"
  },
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
  },
  "publication_audit": {
    "status": "UNKNOWN",
    "expected_count": 0,
    "actual_count": 1,
    "expected_titles": [],
    "actual_titles": [
      "Edital de Abertura"
    ],
    "invalid_actual_titles": [],
    "missing_titles": [],
    "missing_links": []
  }
}
```

### 54. Avança SP Concursos (`avancasp_open`)
- Crawler: `success`; verificação: `NOT_AUDITED`
- Visíveis independentemente: 6; processados: 6
- Método: official_html_observer
- URLs de evidência: https://avancasp.selecao.net.br/index/abertos/, https://avancasp.selecao.net.br/informacoes/251/, https://anexos-r2.selecao.net.br/uploads/301/concursos/251/anexos/efe61c61-d019-4e6e-aa15-91530d3c07cc.pdf

```json
{
  "expected": {
    "titulo": "Concurso Público - 01/2026 - CONSELHO REGIONAL DE CORRETORES DE IMÓVEIS DO ESTADO DE SÃO PAULO - CRECI/SP",
    "modalidade": "Concurso Público",
    "link_edital": "https://anexos-r2.selecao.net.br/uploads/301/concursos/251/anexos/efe61c61-d019-4e6e-aa15-91530d3c07cc.pdf",
    "link_inscricao": "https://avancasp.selecao.net.br/login/sair/?redir=%2Ftermo%2F251%2F"
  },
  "actual": {
    "titulo": "Concurso Público - 01/2026 - CONSELHO REGIONAL DE CORRETORES DE IMÓVEIS DO ESTADO DE SÃO PAULO - CRECI/SP",
    "orgao": "CONSELHO REGIONAL DE CORRETORES DE IMÓVEIS DO ESTADO DE SÃO PAULO - CRECI/SP",
    "modalidade": "Concurso Público",
    "cargo": "Vários cargos",
    "area": "administrativa",
    "cidade": "Americana",
    "uf": "SP",
    "status": "Inscrições abertas",
    "vagas": 34,
    "salario_min": 3920.0,
    "salario_max": 9940.0,
    "escolaridade": "Múltiplas",
    "taxa": 53.5,
    "prova_data": "2026-11-29T00:00:00+00:00",
    "edital_numero": null,
    "edital_data": null,
    "inscricao_inicio": "2026-08-21T00:00:00+00:00",
    "inscricao_fim": "2026-09-21T23:59:00+00:00",
    "link_pagina": "https://avancasp.selecao.net.br/informacoes/251/",
    "link_edital": "https://anexos-r2.selecao.net.br/uploads/301/concursos/251/anexos/efe61c61-d019-4e6e-aa15-91530d3c07cc.pdf",
    "link_inscricao": "https://avancasp.selecao.net.br/login/sair/?redir=%2Ftermo%2F251%2F"
  },
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
  },
  "publication_audit": {
    "status": "MATCH",
    "expected_count": 3,
    "actual_count": 3,
    "expected_titles": [
      "EDITAL COMPLETO 10/08/2026",
      "RESULTADO DAS IMPUGNAÇÕES CONTRA O EDITAL COMPLETO 19/08/2026",
      "RETIFICAÇÃO I DO EDITAL COMPLETO 19/08/2026"
    ],
    "actual_titles": [
      "EDITAL COMPLETO 10/08/2026",
      "RESULTADO DAS IMPUGNAÇÕES CONTRA O EDITAL COMPLETO 19/08/2026",
      "RETIFICAÇÃO I DO EDITAL COMPLETO 19/08/2026"
    ],
    "invalid_actual_titles": [],
    "missing_titles": [],
    "missing_links": []
  }
}
```

### 55. Instituto Mais de Gestão e Concursos (`institutomais_open`)
- Crawler: `success`; verificação: `NOT_AUDITED`
- Visíveis independentemente: 17; processados: 17
- Método: official_html_observer
- URLs de evidência: https://www.institutomais.org.br/Concursos/ConcursosAbertos, https://www.institutomais.org.br/Concursos/Detalhe/10645

```json
{
  "expected": {
    "titulo": "São Sebastião PREV - Concurso Público – Edital Nº 01/2026",
    "modalidade": "Concurso Público"
  },
  "actual": {
    "titulo": "São Sebastião PREV - Concurso Público – Edital Nº 01/2026",
    "orgao": "INSTITUTO PREVIDENCIÁRIO DO MUNICÍPIO",
    "modalidade": "Concurso Público",
    "cargo": "Vários cargos",
    "area": "multiplas",
    "cidade": "Brasília",
    "uf": "DF",
    "status": "Inscrições abertas",
    "vagas": null,
    "salario_min": 69.0,
    "salario_max": 69.0,
    "escolaridade": null,
    "taxa": 69.0,
    "prova_data": null,
    "edital_numero": "01/2026",
    "edital_data": null,
    "inscricao_inicio": "2026-08-17T00:00:00+00:00",
    "inscricao_fim": "2026-10-08T23:59:00+00:00",
    "link_pagina": "https://www.institutomais.org.br/Concursos/Detalhe/10645",
    "link_edital": "https://www.institutomais.org.br/ckfinder/userfiles/files/Retifica%c3%a7%c3%a3o%20002%20ao%20Edital%200012026.pdf",
    "link_inscricao": "https://www.institutomais.org.br/Cargos/Inscrever/58684"
  },
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
  },
  "publication_audit": {
    "status": "UNKNOWN",
    "expected_count": 0,
    "actual_count": 0,
    "expected_titles": [],
    "actual_titles": [],
    "invalid_actual_titles": [],
    "missing_titles": [],
    "missing_links": []
  }
}
```

### 62. Instituto Legatus (`legatus_open`)
- Crawler: `success`; verificação: `NOT_AUDITED`
- Visíveis independentemente: UNKNOWN; processados: 11
- Método: official_html_observer
- URLs de evidência: https://www.legatus.org.br, https://www.legatus.org.br/concursos/160/municipio-de-tanque-do-piaui-pi/, https://www.legatus.org.br/concursos/3221/download/

```json
{
  "expected": {
    "titulo": "Concurso e Seleções",
    "link_edital": "https://www.legatus.org.br/concursos/3221/download/",
    "link_inscricao": "https://www.legatus.org.br/candidatos/login/"
  },
  "actual": {
    "titulo": "Concurso e Seleções",
    "orgao": null,
    "modalidade": "Concurso Público",
    "cargo": "Vários cargos",
    "area": "educacao",
    "cidade": "Tanque Do Piauí",
    "uf": "PI",
    "status": "Inscrições abertas",
    "vagas": 50,
    "salario_min": null,
    "salario_max": null,
    "escolaridade": null,
    "taxa": 140.0,
    "prova_data": null,
    "edital_numero": "01/2026",
    "edital_data": null,
    "inscricao_inicio": "2026-08-03T00:00:00+00:00",
    "inscricao_fim": "2026-08-03T00:00:00+00:00",
    "link_pagina": "https://www.legatus.org.br/concursos/160/municipio-de-tanque-do-piaui-pi/",
    "link_edital": "https://www.legatus.org.br/concursos/3221/download/",
    "link_inscricao": "https://www.legatus.org.br/candidatos/login/"
  },
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
    "link_edital": "MATCH",
    "link_inscricao": "MATCH"
  },
  "publication_audit": {
    "status": "MATCH",
    "expected_count": 8,
    "actual_count": 8,
    "expected_titles": [
      "EDITAL Nº 03/2026 - ALTERA O CRONOGRAMA",
      "RELAÇÃO PRELIMINAR DE CANDIDATOS CONCORRENTES ÀS VAGAS DESTINADAS A PESSOAS COM DEFICIÊNCIA",
      "RELAÇÃO PRELIMINAR DE CANDIDATOS COM PEDIDO DE ATENDIMENTO ESPECIAL",
      "EDITAL N° 02/2026 - PRORROGAÇÃO DAS INSCRIÇÕES",
      "RESULTADO DA ANÁLISE DE RECURSOS INTERPOSTOS CONTRA O RESULTADO DOS PEDIDOS DE ISENÇÃO",
      "RESULTADO DA ANÁLISE DOS PEDIDOS DE ISENÇÃO DE PAGAMENTO DA TAXA DE INSCRIÇÃO",
      "RETIFICAÇÃO Nº 01 AO EDITAL Nº 01/2026",
      "EDITAL Nº 01/2026 - ABERTURA DO CONCURSO"
    ],
    "actual_titles": [
      "EDITAL Nº 03/2026 - ALTERA O CRONOGRAMA",
      "RELAÇÃO PRELIMINAR DE CANDIDATOS CONCORRENTES ÀS VAGAS DESTINADAS A PESSOAS COM DEFICIÊNCIA",
      "RELAÇÃO PRELIMINAR DE CANDIDATOS COM PEDIDO DE ATENDIMENTO ESPECIAL",
      "EDITAL N° 02/2026 - PRORROGAÇÃO DAS INSCRIÇÕES",
      "RESULTADO DA ANÁLISE DE RECURSOS INTERPOSTOS CONTRA O RESULTADO DOS PEDIDOS DE ISENÇÃO",
      "RESULTADO DA ANÁLISE DOS PEDIDOS DE ISENÇÃO DE PAGAMENTO DA TAXA DE INSCRIÇÃO",
      "RETIFICAÇÃO Nº 01 AO EDITAL Nº 01/2026",
      "EDITAL Nº 01/2026 - ABERTURA DO CONCURSO"
    ],
    "invalid_actual_titles": [],
    "missing_titles": [],
    "missing_links": []
  }
}
```

### 63. Fundação FEPESE (`fepese_open`)
- Crawler: `success`; verificação: `NOT_AUDITED`
- Visíveis independentemente: UNKNOWN; processados: 13
- Método: official_html_observer
- URLs de evidência: https://fepese.org.br/concursos/, https://2026pseducasj.fepese.org.br

```json
{
  "expected": {
    "link_inscricao": "https://2026pseducasj.fepese.org.br/inscricao/#!/edital/39693d61db1f8c777c9c7e4b7cc49bbc"
  },
  "actual": {
    "titulo": "Processo Seletivo - Município de São José",
    "orgao": "Município de São José 2026 - Município de São José",
    "modalidade": "Processo Seletivo",
    "cargo": null,
    "area": null,
    "cidade": "São José",
    "uf": "SC",
    "status": "Inscrições abertas",
    "vagas": 16,
    "salario_min": 2490.97,
    "salario_max": 5355.59,
    "escolaridade": null,
    "taxa": 110.0,
    "prova_data": null,
    "edital_numero": null,
    "edital_data": null,
    "inscricao_inicio": "2026-08-24T00:00:00+00:00",
    "inscricao_fim": "2026-09-23T00:00:00+00:00",
    "link_pagina": "https://2026pseducasj.fepese.org.br",
    "link_edital": "https://2026pseducasj.fepese.org.br?go=download&arquivo=2026_005_PS_Sao_Jose_Educa.pdf&inline=1",
    "link_inscricao": null
  },
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
  },
  "publication_audit": {
    "status": "UNKNOWN",
    "expected_count": 0,
    "actual_count": 1,
    "expected_titles": [],
    "actual_titles": [
      "Edital 005/2026"
    ],
    "invalid_actual_titles": [],
    "missing_titles": [],
    "missing_links": []
  }
}
```

### 64. FUNCERN Concursos e Seleções (`funcern_selection`)
- Crawler: `success`; verificação: `VERIFIED`
- Visíveis independentemente: 2; processados: 2
- Método: official_html_observer
- URLs de evidência: https://funcern.br/concursos/, https://funcern.br/concursos/concurso-lagoa-de-pedras-2026/, https://funcern.br/documents/2722/Edital_LagoadePedrasRN_retifica%C3%A7%C3%A3o_1_e_2.pdf

```json
{
  "expected": {
    "titulo": "Concurso Público Lagoa de Pedras/RN",
    "modalidade": "Concurso Público",
    "cidade": "Lagoa De Pedras",
    "uf": "RN",
    "link_edital": "https://funcern.br/documents/2722/Edital_LagoadePedrasRN_retifica%C3%A7%C3%A3o_1_e_2.pdf",
    "link_inscricao": "https://inscricoes.funcern.org/e/concurso-lagoa-de-pedras-2026/"
  },
  "actual": {
    "titulo": "Concurso Público Lagoa de Pedras/RN",
    "orgao": "PREFEITURA MUNICIPAL DE LAGOA DE PEDRAS/RN,",
    "modalidade": "Concurso Público",
    "cargo": null,
    "area": "administrativa",
    "cidade": "Lagoa De Pedras",
    "uf": "RN",
    "status": "Inscrições abertas",
    "vagas": 74,
    "salario_min": 1621.0,
    "salario_max": 8000.0,
    "escolaridade": null,
    "taxa": 90.0,
    "prova_data": null,
    "edital_numero": "01/2026",
    "edital_data": null,
    "inscricao_inicio": "2026-08-03T00:00:00+00:00",
    "inscricao_fim": "2026-08-31T00:00:00+00:00",
    "link_pagina": "https://funcern.br/concursos/concurso-lagoa-de-pedras-2026/",
    "link_edital": "https://funcern.br/documents/2722/Edital_LagoadePedrasRN_retifica%C3%A7%C3%A3o_1_e_2.pdf",
    "link_inscricao": "https://inscricoes.funcern.org/e/concurso-lagoa-de-pedras-2026/"
  },
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
  },
  "publication_audit": {
    "status": "MATCH",
    "expected_count": 9,
    "actual_count": 9,
    "expected_titles": [
      "Edital 01/2026",
      "Resultado Preliminar – Isenção por Doação de Medula Óssea",
      "Resultado Preliminar – Isenção por Doação de Sangue",
      "Resultado Preliminar – Isenção por Prestação de Serviço Eleitoral",
      "Resultado Preliminar – Isenção por CadÚnico",
      "Resultado Definitivo - Isenção por Prestação de Serviço Eleitoral",
      "Resultado Definitivo - Isenção por Doação de Sangue",
      "Resultado Definitivo - Isenção por CadÚnico",
      "Resultado Definitivo - Isenção por Doação de Medula Óssea"
    ],
    "actual_titles": [
      "Edital de Abertura (Retificado)",
      "Resultado Preliminar – Isenção por Doação de Medula Óssea",
      "Resultado Preliminar – Isenção por Doação de Sangue",
      "Resultado Preliminar – Isenção por Prestação de Serviço Eleitoral",
      "Resultado Preliminar – Isenção por CadÚnico",
      "Resultado Definitivo - Isenção por Prestação de Serviço Eleitoral",
      "Resultado Definitivo - Isenção por Doação de Sangue",
      "Resultado Definitivo - Isenção por CadÚnico",
      "Resultado Definitivo - Isenção por Doação de Medula Óssea"
    ],
    "invalid_actual_titles": [],
    "missing_titles": [],
    "missing_links": []
  }
}
```

### 68. Fundação Uniselva - Processos Seletivos (`uniselva_selection`)
- Crawler: `success`; verificação: `NOT_AUDITED`
- Visíveis independentemente: UNKNOWN; processados: 2
- Método: official_html_observer
- URLs de evidência: https://inscricao.fundacaouniselva.org.br/selecoes, https://inscricao.fundacaouniselva.org.br/selecoes/1363

```json
{
  "expected": {
    "link_inscricao": "https://inscricao.fundacaouniselva.org.br/cdn-cgi/content?id=Wa8UJGi01x_XeTEqj1dsFrpCBO9ZRR6ccfOAP0.GklM-1788096268.0631468-1.2.1.1-X0.np4crey8u5REhj3XVldb9HbNUUnJ4my_OxeOJU5mmj1LoQh.Wa7DX2uAai6D4"
  },
  "actual": {
    "titulo": "EDITAL 062/2026 CONTRATAÇÃO DE ESTAGIÁRIO(A) GRADUAÇÃO EM SECRETARIADO, ADMINISTRAÇÃO OU COMUNICAÇÃO SOCIAL",
    "orgao": "Fundação Uniselva",
    "modalidade": "Seleção de Estágio",
    "cargo": "Estagiário(a) de graduação",
    "area": "administrativa",
    "cidade": "Cuiabá",
    "uf": "MT",
    "status": "Inscrições abertas",
    "vagas": null,
    "salario_min": null,
    "salario_max": null,
    "escolaridade": "SECRETARIADO, ADMINISTRAÇÃO OU COMUNICAÇÃO SOCIAL",
    "taxa": null,
    "prova_data": null,
    "edital_numero": "062/2026",
    "edital_data": null,
    "inscricao_inicio": "2026-08-27T00:00:00+00:00",
    "inscricao_fim": "2026-09-07T23:59:59+00:00",
    "link_pagina": "https://inscricao.fundacaouniselva.org.br/selecoes/1363",
    "link_edital": "https://web.fundacaouniselva.org.br/Editais/1363/EDITAL 062.2026 CONTRATAÇÃO DE ESTAGIÁRIO(A) DE GRADUAÇÃO EM SECRETARIADO, ADMINISTRAÇÃO OU COMUNICAÇÃO SOCIAL.pdf",
    "link_inscricao": "https://inscricao.fundacaouniselva.org.br/selecoes/inscricao/1363"
  },
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
  },
  "publication_audit": {
    "status": "UNKNOWN",
    "expected_count": 0,
    "actual_count": 2,
    "expected_titles": [],
    "actual_titles": [
      "EDITAL 062.2026 PORTARIA COMISSÃO DE SELEÇÃO.pdf",
      "EDITAL 062.2026 CONTRATAÇÃO DE ESTAGIÁRIO(A) DE GRADUAÇÃO EM SECRETARIADO, ADMINISTRAÇÃO OU COMUNICAÇÃO SOCIAL.pdf"
    ],
    "invalid_actual_titles": [],
    "missing_titles": [],
    "missing_links": []
  }
}
```

### 69. Fundação de Apoio à FAFIPA (`fafipa_open`)
- Crawler: `success`; verificação: `VERIFIED`
- Visíveis independentemente: 9; processados: 9
- Método: official_html_observer
- URLs de evidência: https://concursos.fundacaofafipa.org.br/, https://concursos.fundacaofafipa.org.br/informacoes/4207/, https://anexos-r2.selecao.net.br/uploads/281/concursos/4207/anexos/bffabe06-9ef0-44cd-8986-95abfc804cf5.pdf

```json
{
  "expected": {
    "titulo": "Concurso Público do Município de Calmon - SC",
    "modalidade": "Concurso Público",
    "cidade": "Calmon",
    "uf": "SC",
    "link_edital": "https://anexos-r2.selecao.net.br/uploads/281/concursos/4207/anexos/bffabe06-9ef0-44cd-8986-95abfc804cf5.pdf",
    "link_inscricao": "https://concursos.fundacaofafipa.org.br/login/sair/?redir=%2Ftermo%2F4207%2F"
  },
  "actual": {
    "titulo": "Concurso Público do Município de Calmon - SC",
    "orgao": null,
    "modalidade": "Concurso Público",
    "cargo": "Vários cargos",
    "area": "multiplas",
    "cidade": "Calmon",
    "uf": "SC",
    "status": "Inscrições abertas",
    "vagas": 100,
    "salario_min": null,
    "salario_max": null,
    "escolaridade": null,
    "taxa": null,
    "prova_data": null,
    "edital_numero": "02/2026",
    "edital_data": "2026-08-19T00:00:00+00:00",
    "inscricao_inicio": "2026-08-23T00:00:00+00:00",
    "inscricao_fim": "2026-09-14T23:59:00+00:00",
    "link_pagina": "https://concursos.fundacaofafipa.org.br/informacoes/4207/",
    "link_edital": "https://anexos-r2.selecao.net.br/uploads/281/concursos/4207/anexos/bffabe06-9ef0-44cd-8986-95abfc804cf5.pdf",
    "link_inscricao": "https://concursos.fundacaofafipa.org.br/login/sair/?redir=%2Ftermo%2F4207%2F"
  },
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
  },
  "publication_audit": {
    "status": "MATCH",
    "expected_count": 3,
    "actual_count": 3,
    "expected_titles": [
      "Edital n.º 02.02/2026 - Deferimento das solicitações de isenção da taxa de inscrição 27/08/2026",
      "Edital de abertura n.º 01.02/2026 CP PM Calmon - SC 19/08/2026",
      "Anexo Único do Edital n.° 02.02/2026 - Deferimento das solicitações de isenção da taxa de inscrição 27/08/2026"
    ],
    "actual_titles": [
      "Edital n.º 02.02/2026 - Deferimento das solicitações de isenção da taxa de inscrição 27/08/2026",
      "Edital de abertura n.º 01.02/2026 CP PM Calmon - SC 19/08/2026",
      "Anexo Único do Edital n.° 02.02/2026 - Deferimento das solicitações de isenção da taxa de inscrição 27/08/2026"
    ],
    "invalid_actual_titles": [],
    "missing_titles": [],
    "missing_links": []
  }
}
```

### 70. Instituto IESES (`ieses_open`)
- Crawler: `success`; verificação: `NOT_AUDITED`
- Visíveis independentemente: UNKNOWN; processados: 3
- Método: official_html_observer
- URLs de evidência: https://ieses.org/projetos, https://scgas2026.ieses.org/, https://iesesconcursos.nyc3.cdn.digitaloceanspaces.com/2026/scgas0012026/documentos/edital_20260810_101748.pdf

```json
{
  "expected": {
    "titulo": "Concurso Público - Edital 001/2026",
    "modalidade": "Concurso Público",
    "link_edital": "https://iesesconcursos.nyc3.cdn.digitaloceanspaces.com/2026/scgas0012026/documentos/edital_20260810_101748.pdf"
  },
  "actual": {
    "titulo": "Concurso Público - Edital 001/2026",
    "orgao": "SCGÁS - Companhia de Gás de Santa Catarina",
    "modalidade": "Concurso Público",
    "cargo": null,
    "area": "administrativa",
    "cidade": "Florianópolis",
    "uf": "SC",
    "status": "Inscrições abertas",
    "vagas": 2,
    "salario_min": 5429.62,
    "salario_max": 5429.62,
    "escolaridade": "Ensino Médio",
    "taxa": 95.0,
    "prova_data": null,
    "edital_numero": "001/2026",
    "edital_data": null,
    "inscricao_inicio": "2026-08-10T00:00:00+00:00",
    "inscricao_fim": "2026-09-11T00:00:00+00:00",
    "link_pagina": "https://www.scgas2026.ieses.org/",
    "link_edital": "https://iesesconcursos.nyc3.cdn.digitaloceanspaces.com/2026/scgas0012026/documentos/edital_20260810_101748.pdf",
    "link_inscricao": "https://www.scgas2026.ieses.org/#passo02"
  },
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
  },
  "publication_audit": {
    "status": "MATCH",
    "expected_count": 3,
    "actual_count": 3,
    "expected_titles": [
      "Portaria 001 - Deferimento e Indeferimento de Isenção",
      "Edital 001/2026",
      "Edital 001/2026 - Publicação DOESC"
    ],
    "actual_titles": [
      "Portaria 001 - Deferimento e Indeferimento de Isenção",
      "Edital 001/2026",
      "Edital 001/2026 - Publicação DOESC"
    ],
    "invalid_actual_titles": [],
    "missing_titles": [],
    "missing_links": []
  }
}
```

### 71. FUNPEC - Processos Seletivos (`funpec_selection`)
- Crawler: `success`; verificação: `NOT_AUDITED`
- Visíveis independentemente: 10; processados: 10
- Método: official_html_observer
- URLs de evidência: https://funpec.br/processos-seletivos/, https://funpec.br/processo-seletivo/processo-seletivo-12-2026-cuidador-em-saude-nei-cadastro-de-reserva/, https://funpec.br/wp-content/uploads/2026/08/2.-EDITAL-13.2026-VF-2.pdf

```json
{
  "expected": {
    "titulo": "PROCESSO SELETIVO 12/2026 – CUIDADOR EM SAÚDE – NEI (CADASTRO DE RESERVA)",
    "modalidade": "Processo Seletivo",
    "link_pagina": "https://funpec.br/processo-seletivo/processo-seletivo-12-2026-cuidador-em-saude-nei-cadastro-de-reserva/",
    "link_edital": "https://funpec.br/wp-content/uploads/2026/08/2.-EDITAL-13.2026-VF-2.pdf"
  },
  "actual": {
    "titulo": "PROCESSO SELETIVO 12/2026 – CUIDADOR EM SAÚDE – NEI (CADASTRO DE RESERVA)",
    "orgao": "FUNPEC",
    "modalidade": "Processo Seletivo",
    "cargo": null,
    "area": "saude",
    "cidade": "Natal",
    "uf": "RN",
    "status": null,
    "vagas": null,
    "salario_min": null,
    "salario_max": null,
    "escolaridade": "Ensino Médio",
    "taxa": null,
    "prova_data": null,
    "edital_numero": "13/2026",
    "edital_data": null,
    "inscricao_inicio": null,
    "inscricao_fim": null,
    "link_pagina": "https://funpec.br/processo-seletivo/processo-seletivo-12-2026-cuidador-em-saude-nei-cadastro-de-reserva/",
    "link_edital": "https://funpec.br/wp-content/uploads/2026/08/2.-EDITAL-13.2026-VF-2.pdf",
    "link_inscricao": null
  },
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
  },
  "publication_audit": {
    "status": "MATCH",
    "expected_count": 1,
    "actual_count": 1,
    "expected_titles": [
      "EDITAL 13/2026"
    ],
    "actual_titles": [
      "EDITAL 13/2026"
    ],
    "invalid_actual_titles": [],
    "missing_titles": [],
    "missing_links": []
  }
}
```

### 74. FATEC - Fundação de Apoio (`fatec_selection`)
- Crawler: `success`; verificação: `NOT_AUDITED`
- Visíveis independentemente: UNKNOWN; processados: 3
- Método: official_html_observer
- URLs de evidência: https://www.fatecsm.org.br/processos-seletivos/, https://www.fatecsm.org.br/processos-seletivos/#processo-2026-3010088-01

```json
{
  "expected": {
    "link_pagina": "https://www.fatecsm.org.br/processos-seletivos/"
  },
  "actual": {
    "titulo": "Processo Seletivo 2026/3010088-01 - CONTRATAÇÃO CLT: ANALISTA DE PROJETOS E AÇÕES EM GÊNERO, DIREITOS HUMANOS E ENFRENTAMENTO ÀS VIOLÊNCIAS – ÁREA: PSICOLOGIA e direito.",
    "orgao": "Fundação de Apoio à Tecnologia e Ciência - FATEC",
    "modalidade": "Processo Seletivo",
    "cargo": "ANALISTA DE PROJETOS E AÇÕES EM GÊNERO, DIREITOS HUMANOS E ENFRENTAMENTO ÀS VIOLÊNCIAS – ÁREA: PSICOLOGIA e direito.",
    "area": "psicologia",
    "cidade": "Santa Maria",
    "uf": "RS",
    "status": "Em andamento",
    "vagas": null,
    "salario_min": null,
    "salario_max": null,
    "escolaridade": null,
    "taxa": null,
    "prova_data": null,
    "edital_numero": "2026/3010088-01",
    "edital_data": null,
    "inscricao_inicio": "2026-07-10T00:00:00+00:00",
    "inscricao_fim": "2026-07-24T00:00:00+00:00",
    "link_pagina": "https://www.fatecsm.org.br/processos-seletivos/#processo-2026-3010088-01",
    "link_edital": "https://www.fatecsm.org.br/doc.licitacoes/edital_090726130859-fatec.pdf",
    "link_inscricao": null
  },
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
  },
  "publication_audit": {
    "status": "UNKNOWN",
    "expected_count": 0,
    "actual_count": 0,
    "expected_titles": [],
    "actual_titles": [],
    "invalid_actual_titles": [],
    "missing_titles": [],
    "missing_links": []
  }
}
```

