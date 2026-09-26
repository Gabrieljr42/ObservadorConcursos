# TenderProof — recuperação assistida (fase 6)

Implementação local com cenários sintéticos controlados. Não houve sessão nova
Solari, mudança real comprovada de layout, publicação canônica ou cobrança nesta
validação. Observação de snapshot preservado é suportada pela fronteira interna;
não prova interação ao vivo nem confirma uma conta do provedor.

## Contrato e segurança

`recovery.Strategy` versão 1 permite somente `locate_cards`, `navigate_details` e
`identify_documents`, nessa ordem. Cada etapa aceita até três seletores simples
(tag, classe ou ID, até 64 caracteres). Campos extras, código, aumento de orçamento,
allowlist, critérios de evidência ou opções para desligar identidade são recusados
por schema. Não existe `eval`, shell, navegador, comando remoto ou chamada LLM no
executor. Conteúdo de HTML é dado, inclusive scripts e instruções hostis.

`RecoveryPolicy` é fornecida pela aplicação: hosts exatos, identidade esperada,
tamanho agregado (128 KiB padrão), passos (20), tempo observado (2 s) e cartões (5).
O tempo é cooperativo entre operações locais; não representa preempção de uma
operação BeautifulSoup nem teto financeiro. O limite de entrada restringe esse
parser. O executor valida destinos e redirects já capturados; o adaptador que
captura a página continua responsável por validar a cadeia **antes** da navegação.

`Snapshot` contém HTML, páginas e documentos já adquiridos. `VerifiedDocument`
deve ser montado pelo validador documental da aplicação, com identidade, tipo,
bytes/hash, página física, texto da página e trecho. O executor confere hash,
assinatura PDF, tipo principal, identidade e trecho dentro do texto fornecido.
Não extrai PDF nem prova que texto arbitrário corresponde aos bytes: a origem
desse texto é uma obrigação explícita do adaptador, não uma declaração aceita
do cliente REST ou do proponente.

Diagnósticos distinguem rede, bloqueio, layout, vazio legítimo, falso vazio,
documento errado, anexo, identidade, extração parcial, evidência e limites.
Vazio legítimo exige confirmação independente e contagem esperada zero. Nunca
provoca exclusões. Diagnóstico guarda etapa, URL sem query/credenciais, contagens,
identidade, limites, versão/hash e trecho sanitizado de até 2.000 caracteres.

## Revisão e persistência

SQLite auxiliar `backend/.tenderproof/recovery.sqlite3` (ou pasta irmã do diretório
configurado de artefatos) mantém propostas, ponteiro ativo e auditoria. O schema é
criado idempotentemente ao abrir o store; não altera o banco canônico. Transações
`BEGIN IMMEDIATE` serializam revisão/ativação/rollback e sobrevivem a reinícios.
Backup deve incluir esse arquivo. Todos os acessos são filtrados por usuário;
revisor é o proprietário autenticado, coerente com revisão TenderProof existente.

Fluxo: `proposed → tested → observed → approved → active`. Falha de validação
gera `validation_failed`; reprovação humana gera `rejected`. Observação malsucedida
mantém `tested`. Aprovação registra motivo, usuário e horário no audit log.
Propostas são imutáveis: correções exigem outra proposta e nova revisão. A
ativação compara a versão ativa com a versão anterior capturada ao propor;
concorrência desatualizada é recusada.

Rollback exige motivo e que a proposta ainda seja a selecionada pelo ponteiro
ativo. Restaura a anterior ou remove a seleção quando não havia anterior. Preserva
toda a auditoria e recusa sobrescrever uma ativação posterior. Não há notificações,
publicação nem alteração de coletor canônico nessa operação.

## API e integração

Registrar `recovery_router.router` na aplicação FastAPI. Endpoints com JWT normal:

- `POST /tenderproof/recovery/proposals`: JSON da estratégia.
- `GET /tenderproof/recovery/proposals/{id}`: estado, relatórios e auditoria.
- `POST .../{id}/validate`: executa suíte independente do servidor.
- `POST .../{id}/observe-offline`: snapshot sintético fixo do servidor.
- `POST .../{id}/review`: `{"approve":true,"reason":"verificação humana"}`.
- `POST .../{id}/activate`.
- `POST .../{id}/rollback`: `{"reason":"motivo da reversão"}`.

Estratégia de demonstração correta:

```json
{"schema_version":1,"source":"ibgp","cards":[".old-card",".new-card"],"details":[".detail"],"documents":[".notice"]}
```

Alterar `documents` para `[".annex"]` produz proposta válida no schema, mas
reprovada semanticamente. Usar apenas `[".new-card"]` regride o layout antigo e
também é recusado. Aprovação genérica não contorna nenhum desses bloqueios.

Hook interno para observação documental:

```python
report = store.observe_active(owner_user_id, source, captured_snapshot, trusted_policy)
```

Sem estratégia ativa retorna `None`. Com estratégia ativa retorna diagnóstico
e documentos; nunca escreve catálogo. `store.observe(owner, proposal_id, snapshot,
policy)` permite revisar snapshot preservado antes da aprovação. Marcar
`is_synthetic=False` apenas quando a captura e a proveniência sustentarem isso;
o flag sozinho não prova uso real de Solari. A REST não aceita documentos,
políticas ou atestados de aprovação enviados pelo proponente.

## Evidências reproduzíveis e limites

Executar em `backend`:

```powershell
.venv/Scripts/python.exe -m pytest tests/test_tenderproof_recovery.py -q
```

Corpus runtime: `backend/app/tenderproof/resources/recovery/*.json`, com cópia em
`backend/tests/tenderproof_fixtures/recovery/*.json`, dez cenários
explicitamente sintéticos. A suíte independente requer exatamente dez e recusa
promoção se estiver ausente/incompleta; o corpus deve acompanhar a instalação
que habilitar essa API. Não há suíte IMESO aprovada neste módulo, por isso
estratégias IMESO são recusadas na validação até existir corpus independente.

Integração na aquisição de candidatos:
`recovery_integration.recover_listing_candidates(store, owner_user_id=..., source=...,
html=..., listing_url=..., settings=...)` recebe HTML já capturado pelo driver,
sem abrir sessão ou navegar. Pode ser chamada após resultado vazio do parser
tradicional. Consulta somente a estratégia ativa do proprietário, recupera
cartões com seletores aprovados e retorna candidatos e diagnóstico. A identidade
é derivada da rota oficial exata `/concurso.jsp?cod=NUM`, nunca de título ou de
atributo `data-identity` inventado no HTML. Os candidatos permanecem com evidência
documental pendente e seguem toda a validação existente de detalhe/PDF.

A fixture HTML `ibgp_navigation_changed.html` reproduz essa estrutura sem
marcadores de identidade artificiais. Prova recuperação de seletor antigo
quebrado no cenário controlado, não uma quebra histórica real do portal. Para
executar também os quatro testes dessa integração, acrescentar
`tests/test_tenderproof_recovery_integration.py` ao comando pytest acima.

Casos: layout antigo, novo, vazio verdadeiro, falso vazio, documento de outro
concurso, anexo, instrução maliciosa, identidade semanticamente errada, navegação
recuperada e regressão. Testes adicionais cobrem schema, orçamento, redirects,
hash/trecho/página inválidos, JWT, isolamento, reinício, aprovação, concorrência,
baseline desatualizada e rollback. Os testes HTTP usam aplicação local real com
dependência de usuário substituída após testar ausência de autenticação.

Pendente: exercício em captura oficial e eventual Browser autorizado; comparação
com estratégia anterior real; interface móvel de recuperação se requerida; suíte
independente de recuperação IMESO. A demonstração offline aprova somente o que
seus snapshots controlados mostram, sem afirmar generalização a portais vivos.
