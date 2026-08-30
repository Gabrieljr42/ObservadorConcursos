# Questões da auditoria LIVE

> Gerado em: 2026-08-30T03:11:04.584609+00:00

Este documento é derivado exclusivamente de `audit_live_99.json`; não contém contagens ou alegações manuais.

## Contagens

### Crawler

- `success`: 42
- `empty_valid`: 16
- `blocked`: 3
- `failed`: 3
- `degraded`: 35

### Verificação

- `VERIFIED`: 23
- `EMPTY_VERIFIED`: 14
- `BLOCKED`: 5
- `FAILED_EXTERNAL`: 3
- `PARTIAL`: 0
- `BROKEN`: 0
- `NOT_AUDITED`: 54

## Fontes que exigem atenção

### 05. IBAM Concursos (`ibam_open`)
- Crawler: `success`; verificação: `NOT_AUDITED`
- Candidatos: 30; processados: 26; visíveis: UNKNOWN
- Erro:
- Nota: NOT_AUDITED_REASON: no_independent_official_observation

### 08. SEPROD Concursos (`seprod_open`)
- Crawler: `degraded`; verificação: `NOT_AUDITED`
- Candidatos: 0; processados: 0; visíveis: UNKNOWN
- Erro: UnconfirmedEmpty No candidates found and no explicit empty-state evidence was recorded
- Nota: crawler sample has no official detail URL
- Nota: NOT_AUDITED_REASON: crawler_status=degraded

### 10. FGV Conhecimento Concursos (`fgv_open`)
- Crawler: `success`; verificação: `NOT_AUDITED`
- Candidatos: 30; processados: 4; visíveis: 33
- Erro:
- Nota: crawler sample has no official detail URL
- Nota: NOT_AUDITED_REASON: no_independent_official_observation
- Evidência de vazio: {'kind': 'evaluated_closed', 'value': 'Status Encerrado on detail https://conhecimento.fgv.br/concursos/pmesqos2022', 'source': 'https://conhecimento.fgv.br/concursos/pmesqos2022'}

### 11. Cebraspe Concursos (`cebraspe_open`)
- Crawler: `success`; verificação: `NOT_AUDITED`
- Candidatos: 6; processados: 6; visíveis: UNKNOWN
- Erro:
- Nota: NOT_AUDITED_REASON: no_independent_official_observation

### 14. IBGP - Inscrições Abertas (`ibgp_open`)
- Crawler: `success`; verificação: `NOT_AUDITED`
- Candidatos: 15; processados: 15; visíveis: UNKNOWN
- Erro:
- Nota: NOT_AUDITED_REASON: no_independent_official_observation

### 16. FUMARC Concursos (`fumarc_open`)
- Crawler: `success`; verificação: `NOT_AUDITED`
- Candidatos: 34; processados: 33; visíveis: UNKNOWN
- Erro:
- Nota: NOT_AUDITED_REASON: no_independent_official_observation

### 25. Leandro Ferreira & Consultoria (`leandroferreira_open`)
- Crawler: `failed`; verificação: `FAILED_EXTERNAL`
- Candidatos: 0; processados: 0; visíveis: UNKNOWN
- Erro: Error Page.goto: net::ERR_NAME_NOT_RESOLVED at https://www.leandroferreira.com.br/ Call log: - navigating to "https://www.leandroferreira.com.br/", waiting until "domcontentloaded"
- Nota: ConnectError: [Errno 11001] getaddrinfo failed

### 28. IUDS Concursos (`iuds_open`)
- Crawler: `degraded`; verificação: `NOT_AUDITED`
- Candidatos: 0; processados: 0; visíveis: UNKNOWN
- Erro: UnconfirmedEmpty No candidates found and no explicit empty-state evidence was recorded
- Nota: crawler sample has no official detail URL
- Nota: NOT_AUDITED_REASON: crawler_status=degraded

### 29. Reis & Reis Auditores Associados (`reisesreis_open`)
- Crawler: `degraded`; verificação: `NOT_AUDITED`
- Candidatos: 0; processados: 0; visíveis: UNKNOWN
- Erro: UnconfirmedEmpty No candidates found and no explicit empty-state evidence was recorded
- Nota: crawler sample has no official detail URL
- Nota: NOT_AUDITED_REASON: crawler_status=degraded

### 30. MS Concursos (`msconcursos_open`)
- Crawler: `success`; verificação: `NOT_AUDITED`
- Candidatos: 25; processados: 2; visíveis: 29
- Erro:
- Nota: NOT_AUDITED_REASON: no_comparable_field_match
- Evidência de vazio: {'kind': 'evaluated_closed', 'value': 'Status Encerrado on detail https://www.msconcursos.com.br/concurso/43/processo-seletivo-publico-modalidade-emprego-publico-de-agente-comunitario-de-saude-prefeitura-de-ibiuna-sp', 'source': 'https://www.msconcursos.com.br/concurso/43/processo-seletivo-publico-modalidade-emprego-publico-de-agente-comunitario-de-saude-prefeitura-de-ibiuna-sp'}

### 32. EDUCA PB Concursos (`educapb_open`)
- Crawler: `degraded`; verificação: `NOT_AUDITED`
- Candidatos: 0; processados: 0; visíveis: UNKNOWN
- Erro: UnconfirmedEmpty No candidates found and no explicit empty-state evidence was recorded
- Nota: crawler sample has no official detail URL
- Nota: NOT_AUDITED_REASON: crawler_status=degraded

### 33. Instituto ADM&TEC (`admtec_open`)
- Crawler: `success`; verificação: `NOT_AUDITED`
- Candidatos: 4; processados: 4; visíveis: 4
- Erro:
- Nota: NOT_AUDITED_REASON: no_comparable_field_match

### 34. CONTEMAX Consultoria (`contemax_open`)
- Crawler: `degraded`; verificação: `NOT_AUDITED`
- Candidatos: 0; processados: 0; visíveis: UNKNOWN
- Erro: UnconfirmedEmpty No candidates found and no explicit empty-state evidence was recorded
- Nota: crawler sample has no official detail URL
- Nota: NOT_AUDITED_REASON: crawler_status=degraded

### 35. CPCon / UEPB Concursos (`cpcon_open`)
- Crawler: `success`; verificação: `NOT_AUDITED`
- Candidatos: 10; processados: 10; visíveis: UNKNOWN
- Erro:
- Nota: NOT_AUDITED_REASON: no_independent_visible_valid_count

### 36. FUNVAPI Concursos (`funvapi_open`)
- Crawler: `success`; verificação: `NOT_AUDITED`
- Candidatos: 7; processados: 7; visíveis: UNKNOWN
- Erro:
- Nota: NOT_AUDITED_REASON: no_independent_visible_valid_count

### 39. Instituto Avalia (`avalia_open`)
- Crawler: `success`; verificação: `NOT_AUDITED`
- Candidatos: 2; processados: 1; visíveis: 99
- Erro:
- Nota: NOT_AUDITED_REASON: no_independent_official_observation

### 41. IDGRAN Concursos (`idgran_open`)
- Crawler: `failed`; verificação: `FAILED_EXTERNAL`
- Candidatos: 0; processados: 0; visíveis: UNKNOWN
- Erro: Error Page.goto: net::ERR_NAME_NOT_RESOLVED at https://idgran.com.br/ Call log: - navigating to "https://idgran.com.br/", waiting until "domcontentloaded"
- Nota: ConnectError: [Errno 11001] getaddrinfo failed

### 43. Gualimp Assessoria e Consultoria (`gualimp_open`)
- Crawler: `degraded`; verificação: `NOT_AUDITED`
- Candidatos: 0; processados: 0; visíveis: UNKNOWN
- Erro: UnconfirmedEmpty No candidates found and no explicit empty-state evidence was recorded
- Nota: crawler sample has no official detail URL
- Nota: NOT_AUDITED_REASON: crawler_status=degraded

### 44. Instituto Verbena / UFG (`verbena_selection`)
- Crawler: `success`; verificação: `NOT_AUDITED`
- Candidatos: 5; processados: 4; visíveis: UNKNOWN
- Erro:
- Nota: NOT_AUDITED_REASON: no_independent_visible_valid_count

### 45. Instituto IDIB (`idib_open`)
- Crawler: `success`; verificação: `NOT_AUDITED`
- Candidatos: 6; processados: 6; visíveis: UNKNOWN
- Erro:
- Nota: NOT_AUDITED_REASON: no_independent_visible_valid_count

### 47. Elo Assessoria e Serviços (`elo_open`)
- Crawler: `success`; verificação: `NOT_AUDITED`
- Candidatos: 7; processados: 6; visíveis: UNKNOWN
- Erro:
- Nota: NOT_AUDITED_REASON: no_independent_visible_valid_count

### 53. Instituto Nosso Rumo (`nossorumo_open`)
- Crawler: `success`; verificação: `NOT_AUDITED`
- Candidatos: 2; processados: 2; visíveis: UNKNOWN
- Erro:
- Nota: NOT_AUDITED_REASON: no_independent_official_observation

### 61. Oppus Concursos (`oppus_open`)
- Crawler: `degraded`; verificação: `NOT_AUDITED`
- Candidatos: 0; processados: 0; visíveis: UNKNOWN
- Erro: UnconfirmedEmpty No candidates found and no explicit empty-state evidence was recorded
- Nota: crawler sample has no official detail URL
- Nota: NOT_AUDITED_REASON: crawler_status=degraded

### 62. Instituto Legatus (`legatus_open`)
- Crawler: `success`; verificação: `NOT_AUDITED`
- Candidatos: 12; processados: 10; visíveis: UNKNOWN
- Erro:
- Nota: ReadTimeout: The read operation timed out
- Nota: NOT_AUDITED_REASON: no_independent_official_observation
- Evidência de vazio: {'kind': 'evaluated_closed', 'value': 'Status Encerrado on detail https://legatus.org.br/concursos/160/municipio-de-tanque-do-piaui-pi/', 'source': 'https://legatus.org.br/concursos/160/municipio-de-tanque-do-piaui-pi/'}

### 63. Fundação FEPESE (`fepese_open`)
- Crawler: `success`; verificação: `NOT_AUDITED`
- Candidatos: 13; processados: 13; visíveis: UNKNOWN
- Erro:
- Nota: NOT_AUDITED_REASON: no_independent_official_observation

### 65. FAPEMIG - Seleções de Pessoal e Editais (`fapemig_selection`)
- Crawler: `degraded`; verificação: `NOT_AUDITED`
- Candidatos: 0; processados: 0; visíveis: UNKNOWN
- Erro: UnconfirmedEmpty No candidates found and no explicit empty-state evidence was recorded
- Nota: crawler sample has no official detail URL
- Nota: NOT_AUDITED_REASON: crawler_status=degraded

### 66. FAPES (Espírito Santo) - Seleções (`fapes_selection`)
- Crawler: `degraded`; verificação: `NOT_AUDITED`
- Candidatos: 0; processados: 0; visíveis: UNKNOWN
- Erro: UnconfirmedEmpty No candidates found and no explicit empty-state evidence was recorded
- Nota: crawler sample has no official detail URL
- Nota: NOT_AUDITED_REASON: crawler_status=degraded

### 67. FAPESQ (Paraíba) - Seleções (`fapesq_selection`)
- Crawler: `degraded`; verificação: `NOT_AUDITED`
- Candidatos: 0; processados: 0; visíveis: UNKNOWN
- Erro: UnconfirmedEmpty No candidates found and no explicit empty-state evidence was recorded
- Nota: crawler sample has no official detail URL
- Nota: NOT_AUDITED_REASON: crawler_status=degraded

### 68. Fundação Uniselva - Processos Seletivos (`uniselva_selection`)
- Crawler: `success`; verificação: `NOT_AUDITED`
- Candidatos: 9; processados: 2; visíveis: UNKNOWN
- Erro:
- Nota: NOT_AUDITED_REASON: no_independent_official_observation

### 70. Instituto IESES (`ieses_open`)
- Crawler: `success`; verificação: `NOT_AUDITED`
- Candidatos: 26; processados: 3; visíveis: UNKNOWN
- Erro:
- Nota: NOT_AUDITED_REASON: no_independent_visible_valid_count

### 72. FADE - Fundação de Apoio ao Desenvolvimento (`fade_selection`)
- Crawler: `degraded`; verificação: `NOT_AUDITED`
- Candidatos: 0; processados: 0; visíveis: UNKNOWN
- Erro: UnconfirmedEmpty No candidates found and no explicit empty-state evidence was recorded
- Nota: crawler sample has no official detail URL
- Nota: NOT_AUDITED_REASON: crawler_status=degraded

### 73. FAPEX - Fundação de Apoio à Pesquisa e Extensão (`fapex_selection`)
- Crawler: `degraded`; verificação: `NOT_AUDITED`
- Candidatos: 0; processados: 0; visíveis: UNKNOWN
- Erro: UnconfirmedEmpty No candidates found and no explicit empty-state evidence was recorded
- Nota: crawler sample has no official detail URL
- Nota: NOT_AUDITED_REASON: crawler_status=degraded

### 74. FATEC - Fundação de Apoio (`fatec_selection`)
- Crawler: `success`; verificação: `NOT_AUDITED`
- Candidatos: 3; processados: 3; visíveis: UNKNOWN
- Erro:
- Nota: NOT_AUDITED_REASON: no_independent_official_observation

### 75. FAPED - Fundação de Apoio (`faped_selection`)
- Crawler: `degraded`; verificação: `NOT_AUDITED`
- Candidatos: 0; processados: 0; visíveis: UNKNOWN
- Erro: UnconfirmedEmpty No candidates found and no explicit empty-state evidence was recorded
- Nota: crawler sample has no official detail URL
- Nota: NOT_AUDITED_REASON: crawler_status=degraded

### 76. FAPESE - Fundação de Apoio à Extensão e Pesquisa (`fapese_selection`)
- Crawler: `degraded`; verificação: `NOT_AUDITED`
- Candidatos: 0; processados: 0; visíveis: UNKNOWN
- Erro: UnconfirmedEmpty No candidates found and no explicit empty-state evidence was recorded
- Nota: crawler sample has no official detail URL
- Nota: NOT_AUDITED_REASON: crawler_status=degraded

### 78. FAPEMA (Maranhão) - Seleções (`fapema_selection`)
- Crawler: `degraded`; verificação: `NOT_AUDITED`
- Candidatos: 0; processados: 0; visíveis: UNKNOWN
- Erro: UnconfirmedEmpty No candidates found and no explicit empty-state evidence was recorded
- Nota: crawler sample has no official detail URL
- Nota: NOT_AUDITED_REASON: crawler_status=degraded

### 79. FAPECE (Ceará) - Seleções (`fapece_selection`)
- Crawler: `failed`; verificação: `FAILED_EXTERNAL`
- Candidatos: 0; processados: 0; visíveis: UNKNOWN
- Erro: Error Page.goto: net::ERR_NAME_NOT_RESOLVED at https://fapece.ce.gov.br/ Call log: - navigating to "https://fapece.ce.gov.br/", waiting until "domcontentloaded"
- Nota: ConnectError: [Errno 11001] getaddrinfo failed

### 80. FAPERN (Rio Grande do Norte) - Seleções (`fapern_selection`)
- Crawler: `degraded`; verificação: `NOT_AUDITED`
- Candidatos: 0; processados: 0; visíveis: UNKNOWN
- Erro: UnconfirmedEmpty No candidates found and no explicit empty-state evidence was recorded
- Nota: HTTPStatusError: Server error '503 Service Unavailable' for url 'https://www.fapern.rn.gov.br/' For more information check: https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/503
- Nota: NOT_AUDITED_REASON: crawler_status=degraded

### 81. FAPEAL (Alagoas) - Seleções (`fapeal_selection`)
- Crawler: `degraded`; verificação: `NOT_AUDITED`
- Candidatos: 0; processados: 0; visíveis: UNKNOWN
- Erro: UnconfirmedEmpty No candidates found and no explicit empty-state evidence was recorded
- Nota: crawler sample has no official detail URL
- Nota: NOT_AUDITED_REASON: crawler_status=degraded

### 82. FACEPE (Pernambuco) - Seleções (`facepe_selection`)
- Crawler: `degraded`; verificação: `NOT_AUDITED`
- Candidatos: 0; processados: 0; visíveis: UNKNOWN
- Erro: UnconfirmedEmpty No candidates found and no explicit empty-state evidence was recorded
- Nota: crawler sample has no official detail URL
- Nota: NOT_AUDITED_REASON: crawler_status=degraded

### 83. FAPESB (Bahia) - Seleções (`fapesb_selection`)
- Crawler: `degraded`; verificação: `NOT_AUDITED`
- Candidatos: 0; processados: 0; visíveis: UNKNOWN
- Erro: UnconfirmedEmpty No candidates found and no explicit empty-state evidence was recorded
- Nota: crawler sample has no official detail URL
- Nota: NOT_AUDITED_REASON: crawler_status=degraded

### 84. FAPERJ (Rio de Janeiro) - Seleções (`faperj_selection`)
- Crawler: `degraded`; verificação: `NOT_AUDITED`
- Candidatos: 0; processados: 0; visíveis: 23
- Erro: UnconfirmedEmpty No candidates found and no explicit empty-state evidence was recorded
- Nota: crawler sample has no official detail URL
- Nota: NOT_AUDITED_REASON: crawler_status=degraded

### 85. FAPESP (São Paulo) - Oportunidades e Seleções (`fapesp_selection`)
- Crawler: `degraded`; verificação: `NOT_AUDITED`
- Candidatos: 0; processados: 0; visíveis: UNKNOWN
- Erro: UnconfirmedEmpty No candidates found and no explicit empty-state evidence was recorded
- Nota: crawler sample has no official detail URL
- Nota: NOT_AUDITED_REASON: crawler_status=degraded

### 86. Fundação Araucária / FAPPR (Paraná) (`fappr_selection`)
- Crawler: `degraded`; verificação: `NOT_AUDITED`
- Candidatos: 0; processados: 0; visíveis: UNKNOWN
- Erro: UnconfirmedEmpty No candidates found and no explicit empty-state evidence was recorded
- Nota: crawler sample has no official detail URL
- Nota: NOT_AUDITED_REASON: crawler_status=degraded

### 87. FAPESC (Santa Catarina) - Seleções (`fapesc_selection`)
- Crawler: `degraded`; verificação: `NOT_AUDITED`
- Candidatos: 0; processados: 0; visíveis: UNKNOWN
- Erro: UnconfirmedEmpty No candidates found and no explicit empty-state evidence was recorded
- Nota: crawler sample has no official detail URL
- Nota: NOT_AUDITED_REASON: crawler_status=degraded

### 88. FAPERGS (Rio Grande do Sul) - Seleções (`fapergs_selection`)
- Crawler: `degraded`; verificação: `NOT_AUDITED`
- Candidatos: 0; processados: 0; visíveis: UNKNOWN
- Erro: UnconfirmedEmpty No candidates found and no explicit empty-state evidence was recorded
- Nota: crawler sample has no official detail URL
- Nota: NOT_AUDITED_REASON: crawler_status=degraded

### 89. FUNDECT (Mato Grosso do Sul) - Seleções (`fundect_selection`)
- Crawler: `degraded`; verificação: `NOT_AUDITED`
- Candidatos: 0; processados: 0; visíveis: UNKNOWN
- Erro: UnconfirmedEmpty No candidates found and no explicit empty-state evidence was recorded
- Nota: crawler sample has no official detail URL
- Nota: NOT_AUDITED_REASON: crawler_status=degraded

### 90. FAPEMAT (Mato Grosso) - Seleções (`fapemat_selection`)
- Crawler: `degraded`; verificação: `NOT_AUDITED`
- Candidatos: 0; processados: 0; visíveis: UNKNOWN
- Erro: UnconfirmedEmpty No candidates found and no explicit empty-state evidence was recorded
- Nota: crawler sample has no official detail URL
- Nota: NOT_AUDITED_REASON: crawler_status=degraded

### 91. FAPEG (Goiás) - Seleções (`fapeg_selection`)
- Crawler: `degraded`; verificação: `NOT_AUDITED`
- Candidatos: 0; processados: 0; visíveis: UNKNOWN
- Erro: UnconfirmedEmpty No candidates found and no explicit empty-state evidence was recorded
- Nota: crawler sample has no official detail URL
- Nota: NOT_AUDITED_REASON: crawler_status=degraded

### 92. FAPDF (Distrito Federal) - Seleções (`fapdf_selection`)
- Crawler: `degraded`; verificação: `NOT_AUDITED`
- Candidatos: 0; processados: 0; visíveis: UNKNOWN
- Erro: UnconfirmedEmpty No candidates found and no explicit empty-state evidence was recorded
- Nota: crawler sample has no official detail URL
- Nota: NOT_AUDITED_REASON: crawler_status=degraded

### 93. FAPT (Tocantins) - Seleções (`fapt_selection`)
- Crawler: `degraded`; verificação: `NOT_AUDITED`
- Candidatos: 0; processados: 0; visíveis: UNKNOWN
- Erro: UnconfirmedEmpty No candidates found and no explicit empty-state evidence was recorded
- Nota: crawler sample has no official detail URL
- Nota: NOT_AUDITED_REASON: crawler_status=degraded

### 94. FAPEAM (Amazonas) - Seleções (`fapeam_selection`)
- Crawler: `degraded`; verificação: `NOT_AUDITED`
- Candidatos: 0; processados: 0; visíveis: UNKNOWN
- Erro: UnconfirmedEmpty No candidates found and no explicit empty-state evidence was recorded
- Nota: crawler sample has no official detail URL
- Nota: NOT_AUDITED_REASON: crawler_status=degraded

### 95. FAPESPA (Pará) - Seleções (`fapespa_selection`)
- Crawler: `degraded`; verificação: `NOT_AUDITED`
- Candidatos: 0; processados: 0; visíveis: UNKNOWN
- Erro: UnconfirmedEmpty No candidates found and no explicit empty-state evidence was recorded
- Nota: crawler sample has no official detail URL
- Nota: NOT_AUDITED_REASON: crawler_status=degraded

### 96. FAPEAP (Amapá) - Seleções (`fapeap_selection`)
- Crawler: `degraded`; verificação: `NOT_AUDITED`
- Candidatos: 0; processados: 0; visíveis: UNKNOWN
- Erro: UnconfirmedEmpty No candidates found and no explicit empty-state evidence was recorded
- Nota: crawler sample has no official detail URL
- Nota: NOT_AUDITED_REASON: crawler_status=degraded

### 97. FAPERR (Roraima) - Seleções (`faperr_selection`)
- Crawler: `degraded`; verificação: `NOT_AUDITED`
- Candidatos: 0; processados: 0; visíveis: UNKNOWN
- Erro: UnconfirmedEmpty No candidates found and no explicit empty-state evidence was recorded
- Nota: crawler sample has no official detail URL
- Nota: NOT_AUDITED_REASON: crawler_status=degraded

### 98. FAPERO (Rondônia) - Seleções (`fapero_selection`)
- Crawler: `degraded`; verificação: `NOT_AUDITED`
- Candidatos: 0; processados: 0; visíveis: UNKNOWN
- Erro: UnconfirmedEmpty No candidates found and no explicit empty-state evidence was recorded
- Nota: crawler sample has no official detail URL
- Nota: NOT_AUDITED_REASON: crawler_status=degraded

### 99. FAPAC (Acre) - Seleções (`fapac_selection`)
- Crawler: `degraded`; verificação: `NOT_AUDITED`
- Candidatos: 0; processados: 0; visíveis: UNKNOWN
- Erro: UnconfirmedEmpty No candidates found and no explicit empty-state evidence was recorded
- Nota: crawler sample has no official detail URL
- Nota: NOT_AUDITED_REASON: crawler_status=degraded

