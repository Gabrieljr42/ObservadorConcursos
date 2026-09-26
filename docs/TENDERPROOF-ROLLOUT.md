# Etapas 11–13 — plano de execução e portões

Estado final de 8 de setembro de 2026: 70 adaptadores registrados, 61 fontes homologadas para escopo parcial e 38 sem homologação. Os portões foram avaliados com exclusões explícitas; nenhuma fonte tem certificação de cobertura integral e produção permanece desativada. Consulte [a entrega final](TENDERPROOF-PHASES11-13-FINAL.md) e [a matriz atual](tenderproof-rollout-matrix.md). As listas e estados intermediários abaixo preservam o histórico, não substituem o resultado final.

Plano registrado em 2026-09-07 antes dos ensaios de expansão. A seleção do piloto permanece sujeita a substituição fundamentada em captura oficial. Cada lote subsequente exige aceite do anterior; código registrado ou HTTP 200 não abrem o portão.

## Limites do ensaio

HTTP público primeiro; nenhuma ativação de produção. Por fonte do piloto: até duas listagens e um detalhe inicialmente, documento principal limitado a 30 MiB/60 páginas, duas execuções sequenciais para verificar repetição. Não criar sessões pagas sem autorização aplicável. Descoberta parcial é declarada. A sondagem do inventário usa os limites já documentados e não equivale ao ensaio dos adaptadores.

## Critérios mensuráveis

- Para cada fonte: captura oficial identificada por data/URL/hash; teste de identidade divergente, falso vazio/bloqueio, documento incorreto/ambíguo, limite e retomada.
- Dois ciclos sobre a mesma evidência devem produzir zero cadastros, versões e notificações extras; uma mudança controlada deve produzir outra observação identificada como simulação.
- Todos os candidatos conhecidos da amostra devem ser reenfileirados segundo a política; qualquer exclusão por limite deve aparecer na cobertura.
- Zero tentativas de navegador com encerramento desconhecido ao liberar novo navegador. Nenhuma falha de fonte pode impedir o agendamento das demais.
- Registrar duração de ciclo, páginas, candidatos, documentos, retries, atraso de fila e bytes separadamente. Não exigir percentual arbitrário: cada amostra e cada caso obrigatório deve ter evidência verificável.
- PostgreSQL isolado deve comprovar criação, atualização, concorrência, baseline desatualizada, falha transacional, outbox e rollback.
- Cobertura parcial pode ser homologada somente para rotas/amostras explicitamente nomeadas, nunca como cobertura integral da fonte.

## Lotes propostos

### Lote 1 — total acumulado 10

14 ibgp_open; 17 imeso_open; 19 access_open; 22 abcp_open; 54 avancasp_open; 6 ibade_open; 60 fenix_open; 49 legalle_open; 10 fgv_open; 64 funcern_selection.

Reuso previsto: contratos comprovados no piloto para tenants selecao.net.br e edital/ver; portais próprios exigem inspeção individual. Institucionais exigem seleção de pessoal comprovada; vestibular, bolsas e fomento permanecem excluídos sem evidência de contratação.

Dependências e impedimentos: TLS, DNS, bloqueios e rotas de detalhe constam no inventário por URL. Não transpor regras documentais entre tenants sem observação. A ordem dentro do lote pode mudar após confirmação de disponibilidade; preserve o ID original e registre a mudança.

### Lote 2 — total acumulado 30

4 consulpam_open; 50 rbo_open; 1 ibfc_open; 2 idecan_open; 3 aocp_open; 5 ibam_open; 7 consulplan_open; 8 seprod_open; 9 fcc_open; 11 cebraspe_open; 12 cesgranrio_open; 13 idcap_open; 15 fundep_open; 16 fumarc_open; 18 omni_open; 20 exame_open; 21 epl_open; 23 unifil_open; 24 objetiva_open; 25 leandroferreira_open.

Reuso previsto: contratos comprovados no piloto para tenants selecao.net.br e edital/ver; portais próprios exigem inspeção individual. Institucionais exigem seleção de pessoal comprovada; vestibular, bolsas e fomento permanecem excluídos sem evidência de contratação.

Dependências e impedimentos: TLS, DNS, bloqueios e rotas de detalhe constam no inventário por URL. Não transpor regras documentais entre tenants sem observação. A ordem dentro do lote pode mudar após confirmação de disponibilidade; preserve o ID original e registre a mudança.

### Lote 3 — total acumulado 60

26 cotec_open; 27 aguia_open; 28 iuds_open; 29 reisesreis_open; 30 msconcursos_open; 31 facet_open; 32 educapb_open; 33 admtec_open; 34 contemax_open; 35 cpcon_open; 36 funvapi_open; 37 consep_open; 38 institutoconsulplan_open; 39 avalia_open; 41 idgran_open; 42 quadrix_open; 43 gualimp_open; 45 idib_open; 46 jcm_open; 47 elo_open; 48 apta_open; 51 shdias_open; 52 zambini_open; 53 nossorumo_open; 55 institutomais_open; 56 publiconsult_open; 57 klc_open; 58 sigma_open; 59 w2_open; 61 oppus_open.

Reuso previsto: contratos comprovados no piloto para tenants selecao.net.br e edital/ver; portais próprios exigem inspeção individual. Institucionais exigem seleção de pessoal comprovada; vestibular, bolsas e fomento permanecem excluídos sem evidência de contratação.

Dependências e impedimentos: TLS, DNS, bloqueios e rotas de detalhe constam no inventário por URL. Não transpor regras documentais entre tenants sem observação. A ordem dentro do lote pode mudar após confirmação de disponibilidade; preserve o ID original e registre a mudança.

### Lote 4 — total acumulado 99

62 legatus_open; 63 fepese_open; 69 fafipa_open; 70 ieses_open; 40 ufu_selection; 44 verbena_selection; 65 fapemig_selection; 66 fapes_selection; 67 fapesq_selection; 68 uniselva_selection; 71 funpec_selection; 72 fade_selection; 73 fapex_selection; 74 fatec_selection; 75 faped_selection; 76 fapese_selection; 77 fapepi_selection; 78 fapema_selection; 79 fapece_selection; 80 fapern_selection; 81 fapeal_selection; 82 facepe_selection; 83 fapesb_selection; 84 faperj_selection; 85 fapesp_selection; 86 fappr_selection; 87 fapesc_selection; 88 fapergs_selection; 89 fundect_selection; 90 fapemat_selection; 91 fapeg_selection; 92 fapdf_selection; 93 fapt_selection; 94 fapeam_selection; 95 fapespa_selection; 96 fapeap_selection; 97 faperr_selection; 98 fapero_selection; 99 fapac_selection.

Reuso previsto: contratos comprovados no piloto para tenants selecao.net.br e edital/ver; portais próprios exigem inspeção individual. Institucionais exigem seleção de pessoal comprovada; vestibular, bolsas e fomento permanecem excluídos sem evidência de contratação.

Dependências e impedimentos: TLS, DNS, bloqueios e rotas de detalhe constam no inventário por URL. Não transpor regras documentais entre tenants sem observação. A ordem dentro do lote pode mudar após confirmação de disponibilidade; preserve o ID original e registre a mudança.

## Estado

Baseline: 476 testes passaram, 14 PostgreSQL opcionais ignorados, 2 live excluídos; comando em backend: `.venv/Scripts/python.exe -m pytest tests -q -m "not live" --disable-warnings --junitxml=.tenderproof/phases11-13-baseline.xml`. Duração 58,60 s. Não constitui aceite do piloto novo.

Lote 1 em implementação e validação. Lotes 2–4 planejados e ainda sem portão aprovado. Coleta e publicação em produção permanecem desabilitadas.

## Revisão do lote 2 após aceite do piloto

O portão de dez foi aceito para contratos e amostras delimitadas, com cobertura
parcial explicitamente preservada. Evidência: `tenderproof-rollout-acceptance.json`.
A lista vinculante dos próximos20 IDs está em `tenderproof-rollout-plan.json`,
revisada antes da implementação do lote2 para aproveitar tenants realmente
observados e incluir portais próprios e seleção de pessoal. A lista preliminar
acima fica como histórico, não como declaração de fontes homologadas.

Fontes do lote2: EXAME, Objetiva, COTEC, Quadrix, RBO, Sigma, FAFIPA, OMNI, W2,
CONSULPAM, IDCAP, IBFC, IDECAN, Águia, Publiconsult, InstitutoMais, Reis & Reis,
ADMTEC, UFU e Uniselva. Limites iniciais: uma listagem e até três detalhes por
fonte/ciclo, duas repetições, documentos30MiB/60p salvo ampliação explícita
registrada após verificar necessidade; HTTP primeiro e zero browser pago.

IDECAN exige estado de implementação parcial: listagem e identidade de detalhe
funcionam, mas três detalhes anunciavam ausência de arquivos nos dois ciclos.
O site institucional aponta um portal ASP.NET alternativo, cujas listagem e
página291 retornaram403. Políticas de privacidade não substituem edital. O
adaptador parcial não é contado como contrato documental implementado completo
na API ou matriz. Impedimento permanece por fonte, sem interromper as demais.

Atualização de 08/09/2026: 30 fontes registradas, sendo 29 contratos implementados e IDECAN parcial; 69 entradas continuam sem adaptador. A regressão atual passou 714 testes, com 14 testes PostgreSQL pulados por ausência de URL descartável explícita e dois testes live excluídos. Os 132 testes focalizados incluem os novos contratos e guardas. A importação circular dos portais próprios foi corrigida usando a base independente do registro; Reis recusa paginação inconsistente e IDs duplicados.

Publiconsult, Instituto Mais, Reis, UFU e Uniselva completaram dois ciclos HTTP com documentos válidos. Publiconsult exige o script observado que inicializa/exibe as abas, mantém os demais conteúdos ocultos excluídos e classifica documentos pelo rótulo da linha. IDs documentais independem da assinatura temporária do link. Capturas sanitizadas têm hashes próprios identificados como tal.

UFU tem prova documental válida para o candidato técnico-administrativo1781. As amostras docentes1843/1837/1836 exigem revisão conjunta dos editais de condições gerais e específicas, mesmo quando apenas um componente está disponível. A prova TA não homologa todo o portal. Uniselva usa a API pública observada no Angular, valida paginação e associação idSelecao/diretório, exclui bolsas/vestibulares e comprovou o edital062/2026 de contratação de estagiário, seleção1363. Primeira página de35: cobertura parcial.

O lote novo tem16 fontes com amostras documentais válidas. RBO, IDECAN, IBFC e ADMTEC mantêm impedimentos documentais. O cabeçalho IBFC em parágrafos/h5 foi corrigido: seleção490 contém três originais distintos e exige seleção explícita;496 oferece retificação. A seleção494 de curso/Jovem Aprendiz não foi homologada para o produto. ADMTEC possui links oficiais com `?` literal no meio do nome de arquivo; guardas de destino permanecem ativas.

O replay offline das16 fontes processou32 ciclos/64 jobs e preservou uma observação válida por fonte após duas repetições. Outro ensaio processou quatro fontes impedidas em8 ciclos/16 jobs, sem downloads nem observações válidas indevidas, preservando candidatos conhecidos. Ambos terminaram sem backlog, retries ou sessões de navegador. Foram64 snapshots/3.295.072 bytes no ensaio válido e16/389.918 bytes no impedido. São medições sequenciais offline; não comprovam vazão concorrente de produção. Reis comprova o fim do filtro atual por totais JSON; isso não prova todos os filtros ou o histórico da fonte.

A publicação dos32 runs preservados em SQLite descartável criou6 concursos,6 versões/outbox, produziu6 repetições sem mudança e bloqueou20 observações por evidência insuficiente. Não houve notificações ou acesso à produção; o banco temporário foi removido. Repetição sem mudança não é prova de atualização material. A guarda atual também passou 37 testes com PostgreSQL descartável, removido e conferido após a execução.

O portão30 ainda não foi aceito. Faltam a prova de atualização material e escoamento misto com falhas, além do tratamento auditável dos efeitos documentais não demonstrados. Interrupção real e recuperação passaram nas16 fontes; desaparecimento e novidade documental foram simulados explicitamente em EXAME. Nenhum trabalho do lote60 foi iniciado. Os critérios não foram reduzidos para tratar registro de adaptadores como homologação.

Evidências principais: `tenderproof-batch30-current-validation.json`, `tenderproof-batch30-all-contracts-regression.json`, `tenderproof-batch30-continuous-replay-verified.json`, `tenderproof-batch30-blocked-replay.json`, `tenderproof-batch30-publication-live.json` e `tenderproof-rollout-matrix.json`. O script `backend/scripts/tenderproof_batch30_evidence.py` consolida evidências sem conceder o portão.

A primeira captura live Reis foi transformada como HTML para sanitização. Ela foi substituída no replay por nova captura que preserva JSON: `tenderproof-batch30-reis-json-live.json`. O relatório inicial de replay abortou por pressupor que toda fonte teria cobertura parcial; o verificador passou a aceitar ciclo completo apenas com evidência terminal explícita do filtro. A execução `verified` repetiu e comprovou as16 fontes com essa condição corrigida.

A guarda documental persiste qualquer documento novo em relação ao manifesto anterior e impede propostas antigas no commit, sem confundir validade do original com efeitos da novidade. A interface mostra títulos/endereços e bloqueia publicação. A simulação de retificação concomitante preservou o PDF válido e recusou cinco runs antigos/novos na publicação isolada (zero efeitos). TypeScript, interação dos componentes e build web23rotas passaram. Não existe liberação automática dessa pendência.

A recuperação atual (`tenderproof-batch30-document-gate-recovery.json`) matou um processo real por fonte após o commit do run e antes da observação, depois retomou em outro PID. As16 fontes preservaram SHA e uma observação, sem novo driver/download, na última tentativa. Vencimento de lease foi controlado e identificado como fixture. As raízes longas que falharam inicialmente foram preservadas; o ensaio válido usa raiz curta compatível com Windows.

Armazenamento medido do replay:32 PDFs,32.892.498 bytes físicos,16 hashes únicos/16.446.249 bytes únicos; volume completo74.481.910 bytes no momento da medição. São artefatos de prova preservados, não política de retenção. Detalhes em `tenderproof-batch30-storage-measurement.json`.

A prova de atualização material passou em SQLite e PostgreSQL descartáveis (`tenderproof-batch30-material-update.json`). O PDF real EXAME544 sustenta o título aplicado sobre uma baseline canônica explicitamente sintética. A data desconhecida não pôde ser aprovada; datas e salários anteriores foram preservados. Aplicação repetida produziu uma versão e um outbox; rollback repetido restaurou a baseline com dois de cada no total, sem notificações. Volume temporário e contêiner PostgreSQL foram removidos e a ausência foi confirmada. Isso comprova atualização material com evidência, não uma alteração histórica observada no portal.

Uma revisão posterior reproduziu uma lacuna na guarda documental: bytes diferentes no mesmo URL geravam outra observação, mas ainda permitiam aplicar uma proposta anterior. A correção e sua validação estão em andamento; o portão30 permanece pendente. O ensaio de fila mista também está em execução, com contenção real entre dois processos e sem antecipar artificialmente os retries.

## Aceite atual do lote30 — 08/09/2026

Os registros de pendências acima representam o histórico anterior a este aceite. A guarda para bytes alterados no mesmo URL foi corrigida: preserva hashes e execuções, bloqueia propostas antigas e mantém a pendência quando o processamento posterior falha. A regressão passou718 testes (14 opcionais pulados, dois live excluídos); a suíte executada com PostgreSQL descartável passou41 e os44 focais passaram. TypeScript e interação da interface passaram. O contêiner descartável foi removido e sua ausência confirmada. Evidência: `tenderproof-batch30-byte-gate-validation.json`.

A retomada após morte real foi repetida nas16 fontes com a última correção: mesmo artefato, uma observação e nenhum novo download em outro processo, inclusive na última tentativa. Evidência: `tenderproof-batch30-byte-gate-recovery.json`.

O ensaio misto com retry30s não escoou no limite de300s:26 jobs concluídos, um impedimento esperado e13 adiados por contenção. O relatório malsucedido foi preservado. Com a configuração suportada `retry_base_s=1`, dois processos no mesmo host escoaram40 jobs por rodada em58,609s e59,016s, sem backlog final. As16 fontes válidas e quatro impedidas mantiveram deduplicação; os quatro subprocessos terminaram com código0. Houve369 e355 adiamentos por contenção, respectivamente. Outros testes rodavam no host, portanto esses tempos não isolam um ganho causal nem certificam vazão em produção. Evidências: `tenderproof-batch30-mixed-validation.json` e `tenderproof-batch30-mixed-retry1-validation.json`.

O portão foi aceito exclusivamente para expansão técnica com escopo delimitado:26 fontes acumuladas homologadas parcialmente, quatro bloqueadas sem homologação e69 pendentes. RBO, IDECAN, IBFC e ADMTEC preservam seus impedimentos oficiais. Há29 contratos implementados e um parcial. Alterações de bytes complementares não adquiridos e interpretação universal de retificações permanecem fora do escopo comprovado; pendências preservam o catálogo e exigem revisão. A coleta e a publicação em produção continuam desabilitadas.

Plano e matriz foram atualizados pelo consolidador com `--accept-bounded`, que exige as provas de aquisição, repetição, recuperação atual, publicação material, regressão e escoamento. O próximo lote de30 IDs já está definido em `tenderproof-rollout-plan.json`; sua implementação ainda não começou. Aceitar este portão não equivale a homologar integralmente30 portais.

## Lote60 em execução — 08/09/2026

O registro histórico acima precede o início deste lote. Agora há51 adaptadores registrados: os30 anteriores e21 novos. O lote60 permanece em implementação e validação; seu portão ainda não foi aceito. As39 entradas do lote99 não foram iniciadas.

As novas famílias incluem os portais próprios MSConcursos/CONSEP/FUNVAPI, a plataforma Seleção para FUNDEP/FACET/EDUCA, os contratos EPL/APTA/SHDIAS, IBAM/FCC/Cebraspe/Cesgranrio/Avalia, Consulplan/Instituto Consulplan/Zambini, CPCON, ELO e Contemax. Os dois identificadores Consulplan permanecem separados no inventário; apontar para um portal comum não autoriza fusão canônica. Zambini foi observado no arquivo histórico, após marcador explícito de ausência na listagem corrente.

Há19 fontes novas com amostras documentais válidas em dois ciclos preservados. FUNDEP147p, FACET83p e Cesgranrio81p excederam inicialmente o limite60; os mesmos bytes foram recuperados offline com limites explícitos160/120/100. Esses limites não alteram o padrão da coleta. ELO validou o edital CIMAG em dois ciclos; CPCON validou PSS002/2026, enquanto UEPB002/2026 permanece impedido por oferecer apenas retificações.

Gualimp tem contrato AJAX comprovado, mas as aquisições posteriores receberam desafio403; não há amostra documental homologada. Contemax tem listagem e detalhe HTTPS acessíveis, porém o PDF HTTPS falhou por desconexão; não foi usado fallbackHTTP. AOCP/UniFil, SEPROD/IUDS/FUMARC, Leandro Ferreira/IDGRAN e IDIB/JCM preservam, respectivamente, bloqueios de acesso, TLS, DNS ou ausência de contrato documental público demonstrado. Não contam como adaptadores implementados.

A normalização de links temporários reconhece somente os contratos comprovados: SAS Cesgranrio e refresh CPCON, além da convenção AWS já existente. URLs e bytes originais ficam preservados. Os ensaios de repetição, morte real de processo, compatibilidade histórica, regressão e publicação compatível ainda compõem o portão em andamento. A coleta e a publicação em produção permanecem desabilitadas.

## Aceite delimitado do lote60 — 08/09/2026

O portão passou após as provas registradas em `tenderproof-batch60-gate-validation.json`. A matriz acumula45 fontes com homologação parcial,15 bloqueadas e39 pendentes. Há51 adaptadores registrados, dos quais50 implementados e IDECAN parcial; nove fontes consideradas no lote60 continuam sem contrato. Este aceite permite a expansão técnica e não homologa essas nove entradas nem os PDFs indisponíveis de Gualimp/Contemax.

Nas19 novas fontes válidas, dois ciclos offline preservaram uma observação por fonte. A interrupção real seguida de retomada em outro processo passou19/19, sem novo download;38 subprocessos encerrados. A fila de21 fontes (19 válidas e duas falhas controladas) escoou42 trabalhos por rodada em83,922s e90,313s. Todos626 drivers e quatro workers encerraram;1.150 disputas de aquisição foram registradas. Nove fontes sem contrato ficaram fora dessa fila. Não há certificação de vazão em produção.

A regressão passou871 testes,14 opcionais pulados e dois live excluídos. A suíte canônica/publicação executada com PostgreSQL descartável passou36 testes sem skips. A revisão posterior corrigiu uma contradição de número/ano no Gualimp e passou28 testes focais; o detalhe estruturado agora recusa999/2099 quando a listagem declara002/2019. Essa correção não modifica o core nem os cenários de fila com falha403. Contêiner e volumes temporários foram removidos.

A publicação isolada criou cinco concursos (FUNVAPI, FACET, IBAM, Consulplan e Zambini), com cinco versões, cinco outboxes e zero notificações. Repetições não criaram efeitos extras. Treze fontes foram impedidas por vínculo documental forte insuficiente; Instituto Consulplan foi impedido por possível duplicidade do mesmo edital já criado via Consulplan. Os19 PDFs válidos não equivalem a19 cadastros publicáveis. A atualização material e o rollback do IBAM passaram em SQLite e PostgreSQL, preservando datas e salários anteriores quando não aprovados ou desconhecidos.

O replay ocupa92.494.822 bytes no volume medido, com38 arquivos PDF e18 hashes únicos (19 IDs de fonte incluem o par Consulplan). Artefatos de auditoria foram preservados; nenhuma retenção destrutiva foi aplicada. Evidências: `tenderproof-batch60-storage-measurement.json`, `tenderproof-batch60-publication-live.json`, `tenderproof-batch60-material-update.json` e `tenderproof-batch60-postgres-validation.json`.
