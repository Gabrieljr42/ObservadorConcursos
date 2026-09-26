# TenderProof — conciliação Solari (2026-09-07)

Estado: **parcialmente conciliada**. O gateway oficial reconheceu as duas sessões
armazenadas e informou `released` usando a chave substituta atual. A organização
do dashboard apresentado pelo usuário não foi conferida; o histórico de zero
instâncias continua sem explicação comprovada. Não se afirma validação ponta a ponta.

## Evidência preservada e caminho de código

Snapshot original, não modificado:
`backend/.tenderproof/review/runs/tpr-c84fdce378eb.json`.
SHA-256 do snapshot:
`ca655faa4f4a9af46623cee4c18c6827a2f1c0ae9d7fe114a740e7c38102fcf0`.
Criado em `2026-09-07T17:38:31.331363-03:00`, com modo localmente registrado `real`.
PDF novamente lido: 806.581 bytes, 46 páginas, SHA-256
`ac7a4bbb6ddd42e9e9889f36687c0e1406703bc945e6196d0170fb9a8704078f`.
Isso prova a existência do artefato local, não sua aquisição pela conta mostrada.

O router escolhe `SolariBrowserAdapter` no modo real e `FakeSolariDriver` no mock;
o serviço recebe o driver por injeção, portanto seu argumento `mode` isoladamente
não prova o driver usado. `SolariBrowserAdapter` cria o cliente oficial e chama
`launch`; doubles e substituições existem nos testes. Não foi encontrado override
de driver no servidor de revisão. O estado histórico do processo não foi preservado:
a leitura do código atual não prova ausência de monkeypatch histórico.

O servidor de revisão carrega somente `SOLARI_API_KEY` de `backend/.env`, sem
copiar esse arquivo ao processador. O adaptador geral também aceita região/base
do ambiente do processo; não há snapshot desse ambiente histórico. Existe override
de base no `.env` atual, mas isso não prova que foi usado na execução histórica.
Nenhum valor secreto ou URL com capacidade é reproduzido neste documento.

SDK instalado: `solari-browser==0.1.3`, `patchright==1.62.3`.
O mapa de região instalado resolve `us-west` para `https://api.getsolari.com`.
Não há `solari-sandbox` instalado. A documentação geral Python consultada menciona
outra faixa do patchright (1.59.x), enquanto o ambiente contém 1.62.3; compatibilidade
de uma nova conexão não foi testada. Referência: [SDK Python oficial](https://docs.getsolari.com/sdk/python).

## Consultas autenticadas, somente leitura

Comando: `backend/.venv/Scripts/python.exe backend/scripts/tenderproof_solari_audit.py`.
O script lê a chave substituta exclusivamente do `.env`, fixa a base oficial,
executa GET de status/replay e só registra campos explicitamente permitidos.
Não imprime exceções, respostas brutas, cabeçalhos, IDs capazes de conexão ou URLs
de replay. Os IDs completos continuam apenas no snapshot original ignorado pelo Git.

Evidência sanitizada: `backend/.tenderproof/solari-audit.json`.
A primeira tentativa restrita não conseguiu consultar a rede. A execução com
permissão de rede retornou os resultados abaixo; uma segunda consulta acrescentou
o hash da organização retornada, sem alterar os resultados.

| Etapa | UTC (2026-09-07) | GET status | Estado retornado | GET replay |
| --- | --- | --- | --- | --- |
| discovery | 21:26:14–15 | 200 | released | 404 |
| detail | 21:26:15–16 | 200 | released | 404 |

As duas respostas de status retornaram a mesma organização, hash SHA-256:
`6dd476887ba5811c72705336df53d15f7d0118cbe3ec14c7ef2a428550ae67b9`.

Conforme a [API Browser oficial](https://docs.getsolari.com/api-reference/browser),
GET consulta a visão do gateway, não o browser em execução. `released` é seu estado
terminal documentado. O endpoint exige chave da mesma organização. Assim, os IDs
armazenados foram reconhecidos e autorizados pela chave atual na organização
retornada. Não se infere que a chave atual é a histórica. Os 404 de replay não
comprovam encerramento, existência de gravação ou motivo da indisponibilidade.

Não foi encontrado endpoint público documentado para identidade humana da conta
ou histórico Browser completo. Não foram inventadas chamadas `/me` ou listagens
de sessões Browser. A API Sandbox possui listagem, mas ela não concilia Browser.

## Discrepância e conferência externa

A [documentação de organizações](https://docs.getsolari.com/organizations) descreve
que o console é escopado pela organização selecionada. Isso é um procedimento de
conferência, não evidência de que o usuário selecionou outra organização.

No console, conferir a organização selecionada em Sessions, API Keys e Usage,
o horário da execução e o período do filtro. Comparar a organização retornada
pelo status com a organização exibida, sem divulgar chave. Se continuar divergente,
enviar ao suporte por canal privado o horário, os IDs do snapshot protegido e os
códigos de resposta. Nenhuma mensagem ao suporte foi enviada.

Não se atribui a divergência a bug, retenção, outra conta ou falta de créditos.
Zero sessões ativas é compatível com `released`; zero instâncias históricas e saldo
zero não foram explicados pelas respostas obtidas. Não houve consulta de faturamento.

## Matriz de evidências

| Capacidade | Implementada | Offline | Integração local | Provedor | Pendente |
| --- | --- | --- | --- | --- | --- |
| Browser aquisição | Sim, preexistente | doubles preexistentes | PDF preservado revalidado | status dos IDs reconhecido | comprovar atribuição dashboard e nova aquisição |
| Encerramento histórico | Sim | testes preexistentes | claims locais preservados | 2/2 released no GET | nenhuma nova sessão testada |
| Replay | Sim | doubles | estados preservados | 2/2 GET 404 | gravações indisponíveis; causa desconhecida |
| Identidade organização | GET documentado | script sanitizado | hashes iguais | 2/2 mesma org retornada | vínculo com console do usuário |
| Sandbox | Fronteira HTTP opt-in | contratos/doubles | subprocesso PDF local | posteriormente 1 sessão autorizada, encerrada | pypdf ausente; extração remota falhou |

Recursos novos nesta auditoria: **0**. Custo confirmado: **não consultado**.
Nenhuma sessão, compra, mudança de plano, encerramento remoto mutante ou edição de
credenciais foi feita. As respostas GET não substituem validação live de aquisição.

Atualização posterior: após autorizações explícitas, houve **três sessões Sandbox**
(não Browser), descrita em [processamento](TENDERPROOF-PROCESSING.md). Criação,
transferência e encerramento confirmados; primeira extração bloqueada por dependência
ausente, segunda pelo limite de páginas devido a erro local na geração da fixture;
a terceira extraiu uma página corretamente, com hash e texto conferidos.
Esses recursos adicionais não explicam o histórico Browser anteriormente divergente.

## Conferência Sandbox após as três tentativas

Comando de leitura:
`backend/.venv/Scripts/python.exe backend/scripts/tenderproof_solari_audit.py --sandbox-history`.
Em **2026-09-07 21:56:12–14 UTC**, cada consulta documentada
`GET /sandboxes?metadata.tenderproof_job=…&limit=10` retornou **200**, zero registros,
sem próxima página. Cada GET do recurso individual retornou **404** após o
fechamento. Evidência: `backend/.tenderproof/solari-sandbox-history-audit.json`.

Essas consultas **não esclarecem a ausência no dashboard**. Foram obtidas respostas
CREATE 201 e DELETE 200 durante cada execução; os 404 posteriores não são usados
como prova de existência ou encerramento. O contrato de consulta Sandbox não
expõe orgId, e suas respostas 404 são opacas. Não se afirma que a listagem é um
extrato de faturamento ou histórico imutável de instâncias já removidas.

A base configurada no `.env` atual foi comparada sem imprimir seu valor e coincide
exatamente com a base oficial de produção usada pelo script. Não há evidência de
override staging nessa configuração atual. O vínculo entre a organização autenticada
pela chave e a organização visualizada no console continua dependendo da conferência
do console; não foi inventado endpoint de conta nem atribuído o resultado a bug.

## Controle negativo de autenticação

Em **2026-09-07 21:58:19.588 UTC**, uma única consulta documentada GET do status
de uma sessão Browser histórica, **sem Authorization**, retornou **401**.
Comando: `backend/.venv/Scripts/python.exe backend/scripts/tenderproof_solari_audit.py --negative-auth`.
Evidência: `backend/.tenderproof/solari-negative-auth-audit.json`.
Não houve tentativa de adivinhar chave nem criação de recurso. Isso confirma que
o endpoint consultado exige autenticação; não identifica o usuário do dashboard.

Contagem de atribuições por nome no `.env`, sem registrar valores:
`SOLARI_API_KEY`: **1**; `SOLARI_BASE_URL`: **1**; `SOLARI_REGION`: **0**.
Não há duplicatas desses nomes na configuração atual e nenhum arquivo de ambiente
foi alterado durante a auditoria.

## Atualização final: Browser real e console autenticado

Orientação posterior do usuário: usar as chamadas API e não bloquear o plano pela
ausência no dashboard. Uma atualização posterior do console é hipótese aceita
para continuidade, não conclusão técnica. Suporte deixa de ser gate de aceite;
o texto abaixo permanece preparado, sem envio. Replay/cobrança continuam desconhecidos.

Cinco Browser adicionais foram criados (IBGP704: quatro tentativas, das quais três
falharam antes do PDF; IMESO139: uma tentativa válida). Todos têm GET 200 com estado
released e o mesmo hash de organização dos dois registros históricos. Há dois PDFs
válidos preservados, descritos em TENDERPROOF.md. Replays retornaram 404, unknown.
O SDK instalado somente envia DELETE em release_and_wait: o adaptador corrigido
exige GET terminal explícito. A matriz acima representa a auditoria inicial.

A conferência visual autenticada foi possível ao final, em 2026-09-07:
- Workspace selecionado: Gabriel's Personal, plano Starter; menu mostrava um workspace.
- Dashboard: zero instâncias no último ano, saldo US$0,00, zero minutos no mês.
- Sessions, filtro All, busca vazia: No sessions yet.
- Usage, últimos 30 dias: zero lançamentos e No usage data for this period.
- API Keys: uma Observador revogada e uma Observador ativa, com Last used preenchido.
- Comparação local sem imprimir chave: prefixo configurado corresponde ao prefixo
  da chave ativa exibida; não corresponde ao da revogada. Um prefixo não demonstra
  igualdade da chave completa nem fornece o orgId, que não apareceu na UI inspecionada.

Isso confirma visualmente a divergência relatada, mesmo com uma chave ativa de
prefixo correspondente no workspace. Não comprova a causa. A API reconhece sessões
que o console não lista. Não se atribui a bug, conta diferente ou retenção.
A próxima ação externa útil é suporte do provedor; nenhum contato foi enviado.

Usage mostra Browser US$0,10/h neste workspace Starter, enquanto as reservas prévias
usaram tarifa pública Free US$0,15/h. Mantemos a estimativa conservadora original,
sem apresentá-la como tarifa aplicada. Uso zero no console também não é confirmação
de gratuidade ou fatura final destas operações. Oito recursos novos (5 Browser +
3 Sandbox), todos encerrados; janelas estimadas somadas US$0,04876667, custo efetivo
não conciliado. Nenhum novo recurso é necessário para repetir essa constatação.

Texto preparado para suporte (não enviado):

> No console autenticado, o workspace pessoal mostra zero Sessions (All) e zero
> Usage nos últimos 30 dias. A chave ativa possui prefixo correspondente à chave
> configurada no nosso cliente e Last used preenchido. Entretanto, o endpoint
> oficial de produção retornou sucesso na criação de cinco Browser e três Sandbox
> em 07/09/2026; os cinco Browser foram depois consultados com GET200/released e os
> Sandbox tiveram DELETE200/ok=true. Também reconhece duas sessões históricas.
> Replays retornam404. Podem conciliar o workspace, os registros de execução e o
> faturamento? Temos IDs e horários em evidência local para enviar por canal privado.
> Nenhuma chave ou URL de conexão precisa ser compartilhada.
