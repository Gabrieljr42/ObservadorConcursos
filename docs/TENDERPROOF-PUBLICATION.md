# TenderProof — publicação controlada (fase 4)

Implementação e integração local verificadas com SQLite e PostgreSQL 17 descartáveis, PDF sintético real e autenticação JWT normal. Nenhuma publicação no catálogo do usuário, envio externo, sessão Solari ou deploy foi executado. A interface integrada tem evidências separadas no relatório principal; os testes deste módulo não as substituem.

## Pipeline e decisões

O catálogo continua em `Concurso`, com a identidade existente por fonte e URL (`uq_concursos_source_link_pagina`). `CrawlService` localiza registros, usa `diff_concurso`, `classify_change` e `build_change_summary`, cria `ConcursoVersion` e notificações internas. TenderProof reutiliza essas funções e tabelas. O ponto de integração explícito é `app.tenderproof.publication.apply_proposal`; não há catálogo paralelo.

`content_hash` nos conectores IBGP e IMESO é `build_hash(raw_payload)`, não o hash de todos os campos canônicos. A publicação preserva `raw_data` e seu `content_hash`; regenerar o hash com outro contrato causaria diff falso no próximo crawl. A versão mantém o hash do material bruto do crawler, e seu `changed_fields` registra os valores efetivamente alterados. A proveniência TenderProof está no ledger da proposta e em `raw_data_snapshot.tenderproof`; não é inserida em campos de negócio. O teste `test_unchanged_traditional_crawl_after_merge_creates_no_version` executa o `CrawlService` real com um conector double retornando os mesmos valores após merge e confirma zero versões adicionais.

São suportadas atualizações de título, órgão, número do edital e datas de inscrição. `unknown`, `conflict`, campo ausente, evidência inválida e campo não aprovado preservam os valores existentes. Remuneração observada permanece bloqueada: remuneração de um cargo não prova mínimo/máximo global. A etapa 12 abaixo acrescenta criação controlada. Exclusão de valor e precedência automática de retificações continuam não suportadas.

## Autorização e configuração

O modelo `User` existente não tem papéis de administrador/revisor. Por isso o módulo usa autenticação JWT normal (`get_current_user`), exige usuário ativo e uma allowlist explícita de IDs do operador. A allowlist vazia recusa toda revisão/publicação. Propostas e execuções continuam isoladas por proprietário; outro revisor autorizado recebe 404 ao tentar acessar a proposta alheia.

Configuração de exemplo, **somente para banco descartável**:

```dotenv
TENDERPROOF_PUBLISHER_USER_IDS=1
TENDERPROOF_PUBLICATION_ENABLED=true
TENDERPROOF_PUBLICATION_ALLOW_SYNTHETIC=true
```

Os dois flags são `false` por padrão; a lista de publicadores é vazia por padrão. O primeiro flag de escrita controla aplicar, reverter e materializar notificações. Criação de proposta e aprovação não alteram o catálogo. Não alteramos `.env` do usuário nem habilitamos publicação real. A configuração da demo existe apenas durante o processo e é restaurada ao terminar.

## API e revisão

Router: `app.tenderproof.publication_router.router`, prefixo `/tenderproof/publications`.

| Método/caminho | Entrada | Resultado |
|---|---|---|
| POST `/proposals` | `run_id`, `concurso_id` opcional, `source_id` opcional | Snapshot imutável do baseline, campos elegíveis/bloqueados, valores e evidências |
| GET `/proposals/{id}` | — | Estado, `stale`, revisão, evidências, aplicação/reversão |
| POST `/proposals/{id}/approve` | `proposal_hash`, `fields` | Aprovação explícita por campos, autor e horário |
| POST `/proposals/{id}/apply` | `proposal_hash` | Aplicação transacional ou `no_change`; diff e versão |
| POST `/proposals/{id}/rollback` | `reason` | Nova versão de reversão, motivo e responsável |
| POST `/outbox/{id}/deliver` | — | Notificações internas no DB, sem transporte externo |

`baseline` contém `values`, `updated_at`, `latest_version_id`, `source_id`, `external_id` e `link_pagina`. `evidences` inclui o valor extraído, estado/motivo, hash documental e evidências com trecho, página física e URL. O trecho preserva o texto original; não se inventa um `original_value` estruturado que o extrator não produziu. `result.diff` usa o mesmo formato `old/new/label` do pipeline. O cliente precisa reenviar o hash recebido e os campos escolhidos; aprovação genérica não existe. 409 exige recarregar/recomparar; POST `/proposals` após mudança de baseline gera proposta distinta e exige nova aprovação.

## Evidência e identidade

Criar, aprovar e aplicar revalidam os bytes preservados: tamanho, SHA-256, leitura do PDF, página física, trecho literal e vínculo com o artefato. O valor deve ser reproduzido pelo extrator atual, e a evidência apresentada deve corresponder à evidência contextual reproduzida. Mudança de extrator que deixe de sustentar um valor bloqueia a aplicação. Nenhum acesso de rede ocorre nessa revalidação.

O concurso alvo exige fonte, identificador externo e URL de detalhe correspondentes. Documento principal deve ser `edital`, com origem na allowlist. Anexo, gabarito, resultado e retificação são recusados. Sobreposição de título não basta: exige-se código explícito no PDF, ou órgão e número de edital reproduzidos e correspondentes ao baseline. Para IMESO, também se reconhece `/edital/ver/{id}` no PDF; o caminho documental verificado `/edital/1/{id}/` só serve como vínculo quando a URL final é exatamente o edital principal já presente no baseline e o texto não cita outro ID. Um PDF real preservado pode ficar bloqueado por falta desse vínculo; isso não é contornado para favorecer a demo.

Limites de bytes e páginas usam `TenderProofSettings`; revalidação completa bloqueia leitura truncada/com erro. A revalidação usa `extract_pages_isolated` da fase 5, com job por proprietário, processo local separado e timeout/limites de saída; falhas recusam publicação com 422. Isso não constitui prova de sandbox de segurança do sistema operacional ou processamento remoto no provedor.

## Transações, concorrência e notificações

As propostas ficam em `tenderproof_publication_proposals`; a combinação proprietário/observação/alvo/hash deduplica reenvios. A chave única `applied_observation` impede duas aplicações da mesma observação ao mesmo concurso, inclusive propostas distintas. Aplicação sem diff registra `no_change`, sem versão ou outbox. Reprocessamento com nova observação e mesmos valores também não gera versão.

Revisão e aplicação usam transações e comparação condicional de estado/horário da aprovação. A escrita canônica usa lock de linha onde suportado e compare-and-swap de todos os valores versionados, identidade, timestamp e última versão. Uma mudança do crawler entre leitura e escrita causa 409. Falha após escrever campos ou criar versão desfaz também o claim e a outbox.

`tenderproof_publication_outbox` tem uma linha única por versão. Nada é enviado ou materializado antes do commit. Um operador pode drenar o evento em outra transação, reutilizando `create_notifications_for_version`. Claim, notificações internas e recibo `delivered` são confirmados juntos; falha reverte os três, mantendo evento pendente. Repetição e dois consumidores concorrentes criam uma única notificação por alerta/versão. Não existe worker automático nem email/push. A garantia transacional se aplica ao transporte **DB interno** existente, e não seria suficiente para email/push arbitrário; um futuro transporte externo precisará aceitar chave de idempotência.

## Reversão e migração

Rollback exige motivo e revisor autorizado, mantém a versão aplicada e adiciona outra versão com diff inverso. Mudanças posteriores, inclusive nova versão, bloqueiam reversão automática. O evento original ainda pendente é marcado `superseded`; notificações já materializadas continuam como histórico. A reversão cria seu próprio evento, com outra versão, e pode produzir notificação de correção interna. Repetir rollback retorna o mesmo resultado. Para um registro `no_change`, não existe alteração a reverter.

Migração aditiva: `app.tenderproof.publication_migration.upgrade(engine)` (`tenderproof-publication-002`), equivalente a `ensure_publication_schema(engine)`. Usa o `Base` existente, acrescenta a tabela de identidades e permite alvo nulo no ledger até a criação ser aplicada; não modifica o schema das tabelas canônicas. Pode ser chamada após as tabelas canônicas ou os modelos podem ser importados antes de `Base.metadata.create_all`. Foi exercitada e repetida em SQLite e PostgreSQL 17, incluindo criação das tabelas TenderProof sobre schema canônico existente. Não há downgrade destrutivo: desabilitar os flags preserva o ledger de auditoria.

## Reprodução e evidências

No diretório `backend`:

```powershell
.venv/Scripts/python.exe -m pytest tests/test_tenderproof_publication.py -q --disable-warnings
.venv/Scripts/python.exe scripts/tenderproof_publication_demo.py
```

A demo usa um diretório temporário e banco SQLite eliminado ao encerrar. O resultado JSON contém baseline rotulada como sintética, diff de uma data, aplicação repetida com a mesma versão, reprocessamento `no_change`, reversão e métricas com denominadores. O arquivo `backend/.tenderproof/publication-demo-report.json` foi produzido por essa execução local; não é evidência de conta Solari. O utilitário `seed_isolated_baseline` também aceita snapshot canônico preservado ou observação de conector tradicional, mas exige origem/timestamp explícitos e nunca transforma uma extração TenderProof em baseline real anterior.

Os testes cobrem os dez critérios da fase 4: aplicação duplicada, ausência de mudança, diff válido, metadados, preservação de unknown/conflict, baseline desatualizada, falha transacional, retry de notificação, autorização com JWT normal e rollback auditável. Também cobrem concorrência em sessões DB separadas, adulteração de bytes/valor/página/trecho/origem, identidade errada, anexo, isolamento entre revisores, migração aditiva e regressão com `CrawlService`. Fixtures e conector double são explicitamente sintéticos; nenhum teste depende de uma sessão paga.

## Aceite PostgreSQL descartável — 07/09/2026

Foi criada uma instância nova da imagem local `postgres:17-alpine` (`sha256:cc4c61127125de9f69aa50f7d78b54686576d5d3d835de03128b064d12b97154`), exposta somente em `127.0.0.1` numa porta aleatória. Banco `tenderproof_acceptance`, usuário e senha de fixture, nenhum mount de dados do usuário. Cada caso recebeu schema privado `tp_acceptance_<uuid>`, removido no teardown. O contêiner criado foi `tenderproof-acceptance-6ebf0b46699447dcbb3ce6c1b9b04e1e`, ID `f635f0c5590fe827ef79dd99e0b900b704aa26c8fbb680eb580cf73a16faba26`; ao final foi removido juntamente com seu volume anônimo, depois de conferir o ID exato. Nenhum contêiner preexistente foi alterado.

Com `TENDERPROOF_TEST_POSTGRES_URL` apontando explicitamente para essa fixture:

```powershell
.venv/Scripts/python.exe -m pytest tests/test_tenderproof_publication_postgres.py -q --disable-warnings
```

Resultado final: **14 passed em 39,88 s**. Inclui migração aditiva repetível, merge, preservação unknown/conflict, baseline obsoleta, falha transacional, aplicação concorrente, entrega concorrente, retry, rollback antes/depois de notificação, JWT/isolamento de usuário e `CrawlService` sem nova versão por valores idênticos. A primeira execução teve 11 aprovações e três falhas exclusivamente em expectativas de timezone dos testes: PostgreSQL retorna `timestamptz` com UTC e SQLite devolve datetime sem tzinfo. As expectativas agora comparam o instante em UTC, preservando verificação de data e horário; nenhuma regra funcional foi afrouxada.

Sem a variável opt-in, `test_tenderproof_publication_postgres.py` fica skipped. A fixture recusa host diferente de `127.0.0.1`, database diferente de `tenderproof_acceptance` e usuário diferente de `fixture`; não usa o `DATABASE_URL` da aplicação. Para reproduzir, crie **outro** contêiner novo, mantenha esses nomes de banco/usuário, mapeie uma porta loopback disponível e forneça sua URL `postgresql+psycopg` apenas ao processo pytest. Remova somente o contêiner criado nessa reprodução. Não reutilize a instância descartável descrita acima: ela já foi removida.

Regressão SQLite após essa integração: **25 passed, 14 skipped em 39,93 s**. A prova de interface e documento real com baseline correspondente continua dependendo das evidências integradas registradas pelo agente principal; a suite PostgreSQL não as substitui.


## Etapa 12 — criação e identidade canônica (07/09/2026)

A mesma proposta, aprovação por campo, transação, versão e outbox agora atendem
`action=create` e `action=update`. O POST aceita `concurso_id=null` para identificar
automaticamente a origem exata ou preparar um novo cadastro. `source_id` é
obrigatório apenas quando mais de uma linha Source corresponde à estratégia da
observação. O catálogo não muda ao criar/aprovar uma proposta. A resposta inclui
`action`, `identity`, `required_fields`, `rollback_effect` e a revisão anterior.

Criação exige título, órgão e número do edital com valores reproduzidos sobre o
PDF preservado e aprovação explícita dos três. Banca vem da Source selecionada;
URL do detalhe vem do candidato validado, URL do edital do artefato verificado.
Demais dados ausentes permanecem nulos. A primeira aplicação cria Concurso,
ConcursoVersion e outbox na mesma transação. A revisão depois do INSERT é lida do
banco antes de ser registrada, incluindo a normalização de timestamptz no
PostgreSQL. Repetições da aplicação devolvem a mesma versão.

A identidade tem duas reservas únicas em `tenderproof_canonical_identities`:
fonte/identificador externo e órgão/número de edital exatos após normalização de
caixa e espaços. A segunda reserva evita criações concorrentes entre fontes, mas
**não autoriza fusão automática**. Um possível correspondente exige escolha
explícita de concurso_id e revisão; valores de órgão e edital devem ser
reproduzidos e corresponder ao alvo. A origem canônica original é preservada e a
nova associação fica no ledger de identidade. Nomes parecidos não são usados.
Colisões de órgãos homônimos sem contexto suficiente ficam impedidas, não viram
fusão. Órgão e edital divergindo simultaneamente numa origem já conhecida também
impedem aplicação como possível reaproveitamento do ID. URL ou ID divergentes na
mesma Source exigem revisão de identidade externa ao fluxo: esta versão não
oferece alteração manual irrestrita desses vínculos.

A allowlist, a rota documental e o padrão de identidade no texto vêm do adaptador
registrado para a fonte. ACCESS e outras estratégias do piloto não dependem da
antiga allowlist global IBGP/IMESO. Hosts auxiliares não autorizam outro tenant ou
concurso. Datas unknown/conflict continuam preservadas. Documentos classificados
como retificação, resultado, gabarito ou anexo continuam recusados para aplicação
de campos; detectar esses documentos não atribui automaticamente seus efeitos.

Rollback de criação **arquiva** o registro (`status=arquivado`) em nova versão,
preservando título, origem, associações e histórico. A interface informa esse
efeito. Qualquer versão ou mudança canônica posterior impede essa reversão
automática. Não se apaga concurso para desfazer criação nem se libera sua
identidade para gerar outro cadastro equivalente.

### Migração e operação

A revisão 002 torna `PublicationProposal.concurso_id` nullable e acrescenta o
índice de identidades. Execute com API/workers de publicação pausados e backup do
banco. PostgreSQL usa ALTER; SQLite usa batch Alembic dentro de BEGIN IMMEDIATE,
preserva as linhas, verifica todas as foreign keys antes do commit e restaura o
PRAGMA da conexão. O teste migra um ledger já aplicado com versão e outbox e repete
a migração. Não executamos essa migração no banco real. Nenhum flag de produção foi
ativado e nenhum transporte externo de notificações foi usado.

### Provas desta alteração

Fixtures são PDFs sintéticos identificados como tais, processados pelo extrator
real em subprocesso. Incluem criação, repetição, mínimos de aprovação, falha na
transação, arquivo por rollback, associação explícita entre fontes, concorrência
em sessões distintas e migração com ledger existente. A fixture ACCESS usa o
contrato SelecaoNet, host documental auxiliar e tenant 422; depois associa uma
observação IBGP ao mesmo concurso. Outra fixture recusa tenant documental errado.
Essas provas não homologam documentos reais nem cobertura de nenhuma fonte.

Comandos reproduzíveis a partir da raiz:

```powershell
backend/.venv/Scripts/python.exe -m pytest backend/tests/test_tenderproof_publication.py backend/tests/test_tenderproof_canonical.py -q --disable-warnings
# Apenas com PostgreSQL novo/descartável na URL opt-in validada pela fixture:
backend/.venv/Scripts/python.exe -m pytest backend/tests/test_tenderproof_publication_postgres.py backend/tests/test_tenderproof_canonical.py -q --disable-warnings
```

A corrida de criação configura dois slots de processamento **apenas no teste**,
para alcançar a disputa transacional; com um slot a segunda revalidação pode ser
recusada antes do banco pelo limite operacional. Não alteramos o limite padrão.

Resultados finais: **34 passed** na regressão SQLite (68,51 s), **23 passed** em
PostgreSQL 17 descartável (49,34 s), e **9 passed** na repetição focalizada SQLite
após a última alteração de auditoria/stale (26,56 s). O contêiner desta rodada foi
`tenderproof-canonical-20260907-b6f41`, ID
`0e58badceb2f57e5bd0e88191fe67f6bbc48316767ce695dbe564dc210a3ece0`, imagem local
`postgres:17-alpine`, porta `127.0.0.1:52885`, database `tenderproof_acceptance`,
usuário/senha de fixture, sem mount de dados do usuário. Schemas temporários foram
removidos pelos testes; o contêiner e seu volume anônimo foram removidos ao fim.
A listagem filtrada pelo ID confirmou ausência. A reprodução precisa criar outra
instância, pois esta já não existe. A primeira execução PG identificou snapshot
pré-normalização timestamptz e limite de um slot de processamento na prova
concorrente; ambos foram corrigidos/testados sem afrouxar a identidade documental.

### Observações reais do piloto até criação canônica isolada

O replay em `docs/tenderproof-publication-live.json` usa **25 observações reais**
concluídas e validadas do operacional preservado do piloto, sem aquisição nova e
sem transformar campos ausentes em valores. Seu SQLite canônico foi criado em um
diretório temporário e eliminado ao fim. Usuário revisor e Sources foram criados
somente nessa fixture; os nomes das fontes vêm do inventário. Os PDFs e registros
originais foram abertos somente para leitura; processamento ocorreu no diretório
temporário separado. Nenhuma notificação foi materializada ou enviada.

Resultado: **6 concursos, 6 versões, 6 outboxes, 0 notificações**. ACCESS (Birigui),
ABCP (Garça e Ibiúna) e Fênix (Pedrinhas Paulista, Monções e Glicério) chegaram à
criação com campos obrigatórios e evidências reproduzidos. As seis observações
correspondentes do segundo ciclo produziram `update/no_change`, sem versões ou
cadastros adicionais. Repetir cada aplicação devolveu o mesmo ID e versão.

As **13 observações impedidas** incluem repetições de candidatos: ABCP Conchal,
AvançaSP e Legalle sem número de edital reproduzido/vínculo forte; FGV e IBADE sem
órgão reproduzido; FUNCERN com PDF62p acima do limite padrão60 na publicação. Não
se alega homologação de criação para essas fontes. O PDF ACCESS distingue concurso
01/2026 de edital179/2026; o número publicado é o edital do cabeçalho documental.
Não houve alteração temporal real durante os dois ciclos; atualização com diff,
rollback e disputa são comprovados separadamente pelas fixtures controladas.

Reprodução na raiz (não usa DATABASE_URL nem rede):

```powershell
$env:PYTHONPATH='backend'
backend/.venv/Scripts/python.exe -m app.tenderproof.canonical_live_validation --preserved-root backend/.tenderproof/pilot-live-20260907 --inventory docs/tenderproof-sources-99.json --output docs/tenderproof-publication-live.json
```

A última verificação focalizada SQLite após ajustar a classificação da primeira
versão para `created` passou **9/9 em 25,09s**. A assinatura temporária de download
não é incluída no relatório público; hashes e run_id referenciam os artefatos.

### Recuperação explícita FUNCERN na publicação

O ensaio complementar aceitou **explicitamente 80 páginas**, somente no processo
isolado, após a amostra oficial exigir62p. O padrão continua60. Resultado em
`docs/tenderproof-publication-funcern-live.json`: run `tpr-831aba3f31cc`, hash
`8e296b419b83ff91630ca85822b9fb7e6398c379c4e5db4d8e7b0759cf1cdcca`, **1 concurso,
1 versão,1 outbox,0 notificações**; repetição com mesmo ID/versão e remoção do banco
temporário confirmadas. Assim FUNCERN passa de impedimento por limite na primeira
prova para criação comprovada no escopo configurado de80p. Não reprocessamos as
outras25 observações nesta recuperação.

```powershell
$env:PYTHONPATH='backend'
backend/.venv/Scripts/python.exe -m app.tenderproof.canonical_live_validation --preserved-root backend/.tenderproof/pilot-live-20260907 --inventory docs/tenderproof-sources-99.json --output docs/tenderproof-publication-funcern-live.json --sources funcern_selection --max-pages 80
```

A proposta create também expõe `creation_metadata={banca,link_edital}` antes da
aprovação. Esses valores fazem parte do hash imutável revisado e são revalidados
antes de aprovar/aplicar, impedindo que uma alteração posterior do nome da Source
mude silenciosamente a banca criada. Documento consolidado permanece impedido na
revalidação de publicação, inclusive para observações preservadas anteriores.

Após integrar metadados de criação e impedimento de consolidado: **10 testes
focalizados passaram em26,17s**. Um teste adicional confirmou que mudar Source.name
depois da aprovação retorna409 e deixa zero concursos/versões (**1 passed em2,96s**).

### Pendência documental posterior à proposta — 08/09/2026

O checkpoint contínuo persiste, por usuário/fonte/modo/candidato, documentos
novos em relação ao manifesto anterior. A regra inclui retificações, documentos
classificados como `outro` e segundos editais principais. Assinaturas temporárias
de download não constituem novidade. O primeiro manifesto histórico não gera
automaticamente essa pendência; desaparecimento posterior não a elimina.

Validade do PDF original e efeitos dos documentos novos são estados separados.
Uma observação pode ter identidade documental válida e publicação impedida.
`GET /tenderproof/continuous/document-review/{run_id}` exige autenticação e posse
da execução e retorna `document_review={pending,reason,documents,detected_at}`.
Observações e propostas também expõem o estado atual, inclusive propostas
preparadas antes da novidade. A interface mostra títulos/endereços e impede
preparar, aprovar ou aplicar enquanto houver pendência.

O backend reconsulta o estado na criação, aprovação e aplicação. Depois da
revalidação pesada do PDF, uma transação operacional curta serializa a última
checagem com o commit canônico; um checkpoint não pode inserir novidade entre
essa checagem e a publicação. Os valores, versões e outbox permanecem intactos
quando a guarda recusa a operação. Não há botão de ignorar nem liberação
automática: aquisição/interpretação/revisão auditável dos efeitos ainda exige
trabalho específico, sem alegação de interpretação universal de retificações.

A simulação EXAME acrescentou uma retificação ao original válido: observações
deduplicadas, pendência persistente e cinco runs antigos/novos impedidos na
publicação isolada, zero concursos/versões/outbox/notificações. O helper copia o
ledger operacional para o ambiente descartável via backup SQLite, preservando
pendências e WAL sem escrever na origem. Evidências:
`tenderproof-batch30-complementary-change-validation.json`,
`tenderproof-batch30-document-hold-publication.json` e
`tenderproof-batch30-document-gate-validation.json`.

## Documentos obtidos por POST público — lote99

O endpoint público FAPEG exporta versões diferentes conforme o corpo da requisição. Método, corpo e tipo de conteúdo ficam no documento persistido e no manifesto; uma troca de corpo não é tratada como o mesmo documento apenas porque a URL é igual. A publicação revalida esse contrato antes de preparar/aprovar/aplicar a proposta.

Uma URL de exportação POST isolada não é um link GET para o PDF. Por isso, nesses casos, novos cadastros recebem a página oficial observada como `link_edital`. A proposta expõe `document_access` com página oficial, hash e caminho do artefato preservado. A interface usa o cliente autenticado existente para baixar esse artefato. A rota exige autenticação e propriedade da execução; um usuário diferente recebe404. Propostas antigas de criação que prepararam o endpoint isolado são consideradas desatualizadas e precisam de nova revisão.

O PDF real FAPEG foi usado para verificar200 e SHA exato para o proprietário,401 sem autenticação e404 para outro proprietário/artefato. Criação e atualização POST foram exercitadas com observações sintéticas explicitamente identificadas. A amostra real FAPEG continua impedida de criar concurso quando faltam identidade/campos mínimos; acesso correto ao arquivo não elimina essa guarda. Relatórios: `tenderproof-batch99-post-review.json` e `tenderproof-batch99-publication-live.json`.

Concursos distintos na mesma URL agora contam com índices por identidade externa e proteção contra promoção concorrente de registros legados. A migração é explícita, sem alteração automática de produção: consultar `tenderproof-batch99-identity-migration.md` antes de ativar os contratos de páginas compartilhadas em banco existente.
