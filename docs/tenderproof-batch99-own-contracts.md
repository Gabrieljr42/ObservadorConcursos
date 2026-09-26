# Contratos de bancas e Instituto Verbena — lote99

Observações de 8 de setembro de 2026. O registro e os testes não equivalem a homologação. Os relatórios de aquisição preservam os identificadores das execuções, capturas, SHA256 dos PDFs e limites. A auditoria `tenderproof-batch99-current-validation.json` confere os bytes e os registros operacionais sem alterar o portão do lote.

| Fonte original | Contrato e evidência | Cobertura e limitação |
|---|---|---|
| `legatus_open` | Cards oficiais, detalhe160 e documento3181; dois ciclos válidos em `tenderproof-batch99-own-live.json`. | Somente amostra Tanque do Piauí. O manifesto distingue abertura, retificações e resultados. |
| `klc_open` | Aba pública `sub=2`, detalhe632, original com hash de nome observado; dois ciclos válidos em `tenderproof-batch99-klc-live.json`. | 199 candidatos observados; processamento limitado à amostra. Aba `sub=1` tem marcador explícito de ausência. |
| `ieses_open` | API pública `projetos/api?offset=0&limit=12` comprovada pelo componente oficial; dois subportais e diretórios documentais verificados. Dois ciclos válidos SCGÁS001/2026 em `tenderproof-batch99-ieses-final-live.json`. | Dez outros subportais da primeira página permanecem fora do contrato. Paginação vem da fórmula observada no componente. Destinos finais sem `www` foram verificados antes da normalização; a tentativa anterior recusada permanece em `tenderproof-batch99-ieses-live.json`. |
| `verbena_selection` | Banner oficial liga o concurso da Câmara de Pires do Rio2026; título corroborado pela captura do detalhe, original01/2026 no mesmo diretório. Dois ciclos válidos em `tenderproof-batch99-verbena-live.json`. | O banner não oferece título útil: a configuração usa título do detalhe previamente revisado, explicitamente identificado como tal. Não cobre os demais banners, arquivos, vestibulares ou bolsas. |
| `nossorumo_open` | Cards oficiais e API pública `Home/GetPublicacoes?idProjeto=...`, comprovada no JavaScript; IDs do projeto e arquivo conferidos. | Dois ciclos receberam401 nos PDFs de608/606;607 só apresentou alterações. `tenderproof-batch99-nossorumo-live.json`. O helper oficial `getSiteUrl` confirma a base usada. Nenhum login ou documento de terceiros substituiu o original. |
| `oppus_open` | Redirecionamento oficial para domínio sem `www`, resposta200 preservada em `oppus_open-redirect0.html` e manifesto de detalhes observados. | Conteúdo atual de cassino, sem cadeia verificável de concursos. Não foi criado adaptador vazio nem considerada ausência legítima. Necessária identificação de portal oficial funcional. |
| `fepese_open` | Contrato e investigação em relatório próprio FEPESE. | As três amostras iniciais exibem arquivosTR01 mesmo sob rótulo “Edital”; o sufixo impede promoção automática a original. |

As capturas estão em `backend/tests/fixtures/tenderproof_batch99_own`; cada manifesto identifica URL observada, resposta, tamanho e origem. Regressões controladas de título, ano, diretório, duplicidade e ambiguidade são testes sintéticos sobre essas capturas e não representam mudanças reais dos portais.

## Alternativa pública FAPEX revisada na integração

O portal público de editais, encontrado a partir da página oficial, é independente do portal de RH com autenticação. O detalhe `nr2O` oferece seleção de estágio e documento “ABERTURA E INSCRIÇÕES”; dois ciclos reais passaram em `tenderproof-batch99-fapex-live.json`. A revisão excluiu o título de mestrado profissional `nr6L`, anteriormente aceito pela expressão ampla “profissiona”. Estágios vinculados a projetos não são confundidos com ingresso em cursos ou bolsas de pesquisa. Os demais editais requerem as mesmas guardas de título e origem e não têm homologação integral presumida.
