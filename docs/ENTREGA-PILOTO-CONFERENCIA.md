# Conferência do limite publicado do piloto

Auditoria somente leitura realizada em 2026-09-09 no container `observador-pilot-api-1`, consultando os endpoints de catálogo/versões e o SQLite persistente da fila. Não houve aprovação, aplicação, nova coleta, download ou alteração de catálogo.

Os três registros publicados permanecem disponíveis no endpoint `/concursos` e têm observações reais com `validation_status=valid` no último documento principal preservado. A observação contínua, porém, continua com estado `pending_review`; isso é esperado para atualizações posteriores e não revoga automaticamente os valores já aplicados.

## ACCESS 183 — Birigui

Registro do catálogo: concurso `1`, fonte `access_open`, external ID `183`, Instituto ACCESS, Prefeitura Municipal de Birigui-SP, edital `179/2026`.

Conteúdo atualmente publicado no catálogo inclui início das inscrições em `31/08/2026` e fim em `08/10/2026`, além de título, órgão e número do edital. A versão aplicada é a versão 4, capturada em `2026-09-08T17:01:23`, que registrou somente a inclusão dessas duas datas; a versão de criação registrou título/órgão/número e o PDF principal.

O documento principal observado é `EDITAL DE ABERTURA 24/08/2026`, SHA-256 `de7a554e58278416d88182054a257b4d1439a46ef0730b2cfb3f0996c3731087`, preservado em `acquired_document_state`. O manifesto atual tem apenas esse edital e `pending_documents=[]`; a observação mais recente continua `valid`, sem documento novo ou retificação detectada.

**Conclusão:** não há evidência local de que as datas publicadas tenham ficado desatualizadas por retificação. A data final permanece utilizável dentro do que foi conferido, mas a fonte ainda não tem cobertura integral nem publicação de documentos derivados comprovada.

## ABCP 2867 — Ibiúna

Registro do catálogo: concurso `2`, fonte `abcp_open`, external ID `2867`, ABCP Concursos, Município de Ibiúna, edital `002/2026`.

Conteúdo atualmente publicado inclui início `25/08/2026` e fim `08/09/2026`, título, órgão e número. A versão aplicada é a versão 5, capturada em `2026-09-08T17:07:47`, que registrou essas datas; a criação também preservou o edital principal e o documento “RESPOSTAS AOS PEDIDOS DE IMPUGNAÇÃO DO EDITAL 01/09/2026`.

Na observação contínua mais recente (`run_id=tp-tcj-38207dd011ed5c40b59187eb7dc35846-1`), foram detectados três documentos novos e `pending=true`: `LISTA PROVISÓRIA DE INSCRIÇÕES DEFERIDAS 09/09/2026`, `LISTA PROVISÓRIA DE INSCRIÇÕES DEFERIDAS E INDEFERIDAS - PcD 09/09/2026` e `LISTA DE SOLICITAÇÕES DE CONDIÇÕES ESPECIAIS PARA REALIZAÇÃO DE PROVA 09/09/2026`. Eles estão no manifesto atual, mas ainda não há efeito revisado sobre campos do catálogo. O edital principal preservado tem SHA-256 `ab10571f0d89399ed24f54e9ea7c41b7d56ebbbad1be70fa12d9f7838ad29c72`.

**Conclusão:** não existe evidência local de que os três documentos de listas alterem as datas de inscrição. A data final `08/09/2026` não deve ser reescrita por inferência; os documentos exigem revisão humana para confirmar se trazem cronograma ou apenas listas. O registro publicado está disponível, mas sua conferência atual está pendente por esses três documentos.

## Fênix 129 — Pedrinhas Paulista

Registro do catálogo: concurso `3`, fonte `fenix_open`, external ID `129`, Fênix Concursos, Prefeitura Municipal de Pedrinhas Paulista, edital `01/2026`.

O catálogo publica início `21/08/2026`, fim `04/09/2026` e dados por cargo para MOTORISTA (uma vaga imediata, cadastro reserva, remuneração R$ 2.108,74, jornada e requisitos). A versão 6 aplicou as datas e a versão 7 aplicou os dados por cargo.

Há, entretanto, uma atualização documental explícita. A observação contínua mais recente (`run_id=tp-tcj-56caf30578375094a0752a891807c7fb-1`) detectou `EDITAL DE PRORROGAÇÃO DAS INCRIÇÕES E ALTERAÇÃO DA DATA DA PROVA`, com `pending=true`; o manifesto contém o edital de abertura e essa prorrogação. O edital principal preservado tem SHA-256 `cb0848ea34d18877d37dd46059306ba6212b9b1c56828e33228fda2c609f84f3`.

**Conclusão:** sim, a data publicada de Pedrinhas está desatualizada para a situação posterior ao ato. Em uma única aquisição HTTP normal, feita somente porque a URL já estava no manifesto local, o PDF retornou 493.855 bytes, SHA-256 `abf214200dfba8427d9597ac905e5b1b6a3e7920f03b642dcdcbbd22060c0bbd` e uma página. A extração textual dessa página estabelece:

- Art. 01: inscrições de `09/09/2026 às 10h00` até `11/09/2026 às 10h00`, horário de Brasília; pagamento até `11/09/2026` (Art. 02).
- Art. 03: homologação das inscrições em `18/09/2026`.
- Art. 04: prova objetiva em `27/09/2026`, das `08h00` às `11h00`.
- Art. 05: gabarito em `28/09/2026`, a partir das `18h00`.

O ato é `EDITAL DE PRORROGAÇÃO DAS INSCRIÇÕES E ALTERAÇÃO DA DATA DA PROVA DO CONCURSO PÚBLICO N° 01/2026`, datado de `08/09/2026`; URL comprovada no manifesto: `https://cdn-fenix.selecao.site/edital/1/129/08d76dcea494860bd7181d1f6b79d884.pdf`. A aplicação deve propor `inscricao_inicio=2026-09-09`, `inscricao_fim=2026-09-11` e `prova_data=2026-09-27`, preservando o edital-base e o histórico anterior. Como o PDF da prorrogação não estava no `acquired_document_state` nem em artefato durável antes desta leitura, não foi criado caso de revisão nem proposta no serviço; a evidência exata está pronta para a próxima preparação/reuso e requer aprovação humana antes de qualquer aplicação.

## Resultado verificável

| Registro | Disponível no catálogo | Documento principal preservado | Pendência atual | Datas potencialmente desatualizadas |
|---|---|---|---|---|
| ACCESS 183 Birigui | Sim | Sim; `valid` | Nenhuma nova | Não evidenciado |
| ABCP 2867 Ibiúna | Sim | Sim; `valid` | 3 documentos novos | Não evidenciado |
| Fênix 129 Pedrinhas | Sim | Sim; `valid` | 1 prorrogação/alteração de prova | Sim; revisão obrigatória |

As três publicações continuam no aplicativo como dados históricos aprovados. Esta conferência não afirma que sejam fonte completa, nem aplica alterações pendentes. Próxima ação segura: revisar o PDF de prorrogação da Fênix e os três documentos novos da ABCP, preparar propostas com proveniência e somente então solicitar aprovação humana.
