# TenderProof — fases 4–7

A expansão posterior está documentada em [etapas 8–10](TENDERPROOF-EXPANSION.md):
inventário das 99 fontes, contrato comum IBGP/IMESO e coleta contínua durável.
O relatório abaixo preserva as evidências e o escopo das fases 4–7.

## Estado atual e evidências (2026-09-07)

| Fase | Implementação | Offline | Integração local | Live/provedor | Pendências |
| --- | --- | --- | --- | --- | --- |
| 4 Publicação | Concluída no escopo isolado | Merge/evidências/idempotência/CAS/outbox/rollback | SQLite + 14 testes PostgreSQL; fluxo visual aprovado/aplicado | Catálogo real fora do escopo autorizado | Nenhuma para aceite isolado |
| 5 Processamento | Concluída no escopo limitado | Worker/subprocesso/zipapp, jobs e orçamento | PDF histórico 46 páginas; API JWT | Extração remota 1 página + hashes/texto/encerramento confirmados | Dashboard e cobrança não conciliados |
| 6 Recuperação | Concluída no cenário controlado | 10 cenários, validador separado | SQLite, JWT, revisão/ativação/rollback e hook na aquisição | Não se alega mudança real do portal | IMESO não habilitada para recuperação sem suíte independente |
| 7 Segunda fonte/demo | Concluída no escopo de amostra e demo | IBGP + IMESO sob contratos comuns | Interface de ambas fontes e demo reproduzível | IBGP704 e IMESO139 válidos; 5/5 Browser encerrados | Dashboard, replay e cobrança desconhecidos; não bloqueiam aceite conforme orientação do usuário |

Aceite final: o usuário determinou continuar com base nas APIs, sem condicionar a
entrega à atualização do dashboard. Atualização posterior é hipótese, não causa
comprovada. A conciliação permanece documentada, mas não exige contato com suporte
para encerrar este plano. Não se afirma “Solari validado ponta a ponta” na conta
do console. Não foram criados novos recursos apenas para repetir provas existentes.

Conferência final independente dos artefatos preservados: hashes/bytes corretos,
IBGP 46 páginas e 4/4 trechos verificáveis; IMESO 29 páginas e 5/5 trechos verificáveis.
Resultado: `backend/.tenderproof/final-artifact-revalidation.json`. Isso verifica
proveniência textual, não converte campos desconhecidos em valores corretos.

A suíte integrada final passou com **341 testes, 14 PostgreSQL ignorados, 2 live excluídos**
em 72,39 segundos. Os testes live foram executados por scripts separados e autorizados.
PostgreSQL 17: **14 testes passaram**, em contêiner descartável, removido ao final.
Build Expo web passou. TypeScript mantém erro preexistente de rota em
`mobile/components/ExternalLink.tsx:13`; nenhum erro TenderProof identificado.

### Matriz inicial auditada (antes da implementação)

| Capacidade | Implementada inicialmente | Offline inicial | Local inicial | Provedor inicial |
| --- | --- | --- | --- | --- |
| Fases 0–3 IBGP | Sim, modificações locais preservadas | 210 testes, 2 live excluídos | Snapshot/PDF preservados | Alegações ainda não conciliadas |
| Publicação TenderProof | Não | Não | Não | Não aplicável |
| Jobs isolados/Sandbox | Não | Não | Não | Não exercitado |
| Recuperação declarativa | Não | Não | Não | Não exercitada |
| IMESO TenderProof | Não (coletor tradicional já existia) | Não | Não | Portal ainda a confirmar |

### O que mudou

A revisão cria uma proposta vinculada a usuário, concurso, observação, bytes/hash,
conteúdo e revisão da baseline. Aprovação seleciona campos; `unknown`, `conflict`,
evidência inválida e faixa salarial sem escopo permanecem bloqueados. A aplicação
revalida evidências em worker limitado, compara a baseline por CAS e usa as tabelas
existentes Concurso/ConcursoVersion. Chave persistente evita reaplicar observação.
Outbox cria apenas notificações internas após commit; falhas/retries não duplicam.
Rollback cria versão auditada, preserva histórico e recusa mudanças posteriores.
Não há exclusão implícita de valor nem criação automática de concurso.

O hash `content_hash` preexistente é do payload bruto do crawler, não dos campos
canônicos. Ele é preservado quando raw_data não muda. O diff/versionamento semântico
usa as regras existentes; teste CrawlService prova ausência de versão falsa no
reprocessamento. Sessões, timestamps e replay não viram alterações de negócio.

Jobs e recuperação usam ledgers SQLite operacionais, não outro catálogo. O worker
local recebe somente PDF e variáveis mínimas do SO; não recebe .env/chaves. Limites
incluem bytes, páginas, saída, tempo, tentativas, concorrência e orçamento remoto.
Limite de páginas passa a rejeitar o job; a função antiga de extração continua
capaz de truncar para consumidores existentes. **Subprocesso local não é sandbox de
segurança do Windows**: bloqueio de rede/memória do SO não foi implementado.

Estratégias declarativas aceitam seletores simples e operações fixas, sem código
arbitrário. Corpus independente acompanha o runtime. Todas exigem teste, observação,
revisão humana e ativação; rollback registra autor/motivo. O fallback usa HTML já
capturado e ainda submete cada documento aos controles de identidade/evidência.
Lista vazia não apaga catálogo. IMESO adapta cartões e documentos por fonte;
links ambíguos, anexos e retificações não viram edital principal automaticamente.

### Correção das afirmações históricas

O texto das fases 0–3 abaixo é histórico, não foi reescrito como evidência atual.
`mode=real`, PDF local e duas sessões não bastavam para associar o uso ao dashboard.
A nova auditoria consultou o gateway oficial: **2/2 GET 200, released**, mesma
organização reportada. Replays: **2/2 GET 404**, sem inferir motivo ou inexistência.
O vínculo da organização com o console apresentado e o histórico zero instâncias
continuam desconhecidos. Não se afirma “Solari validado ponta a ponta”.

Novo relatório separado compara o artefato real `tpr-c84fdce378eb` com observação
tradicional IBGP do candidato 704 (três GET públicos 200), em SQLite descartável.
Isso é uma nova observação do conector, **não uma baseline canônica histórica**.
Página física 6 sustenta 24/08/2026–22/09/2026; extrator anterior misturava pagamento,
deferimento e outras etapas. Edital 01/2026 agora usa identificação principal da
página 1. Título, edital e duas datas suportados; órgão/remuneração unknown.
Snapshot histórico permanece intacto; não há documento que prove retificação.

### Investigações reais adicionais e correções

Cinco Browser foram criados: quatro tentativas IBGP704 (três falhas antes de obter
PDF) e uma IMESO139. Todos tiveram GET 200 com estado `released`. O SDK instalado
apenas envia DELETE em `release_and_wait`; agora o adaptador exige consulta terminal
explícita, inclusive em emergência e reconciliação. Replay 404 permanece `unknown`.

IBGP704 voltou a produzir exatamente o hash histórico, 806.581 bytes/46 páginas,
com 4/6 campos sustentados. IMESO139 produziu 597.314 bytes/29 páginas, hash
`8e6fbc48ac7f54c492cc2beba78adc9216ba25fa781ba753d3e9e410fc7dd6dc`.
Uma taxa de inscrição na tabela IMESO foi inicialmente confundida com salário.
O extrator 1.2 recusa páginas que misturam taxa/benefício e remuneração; o novo
snapshot offline tem 5/6 campos sustentados e remuneração `unknown`. O original
incorreto foi preservado e a correção não criou recursos remotos.

Oito recursos novos no total: cinco Browser e três Sandbox, todos encerrados com
resposta explícita do provedor. Estimativa conservadora das janelas autorizadas:
Browser 5 × 210 s × US$0,15/h = US$0,04375; Sandbox 3 × 70 s × US$0,086/h =
US$0,00501667. Total US$0,04876667, **não cobrança confirmada nem teto garantido**.
As falhas estão incluídas. Os limites não autorizam execução automática contínua.
Evidências sanitizadas e limitações: [relatório final](tenderproof-phases4-7-validation.json).

### Reproduzir

No diretório backend:

```powershell
.venv/Scripts/python.exe -m pytest tests -q -m "not live" --disable-warnings
.venv/Scripts/python.exe scripts/tenderproof_demo.py
.venv/Scripts/python.exe scripts/tenderproof_review_server.py --port 8014
```

Em outro terminal, no mobile:

```powershell
$env:EXPO_PUBLIC_API_BASE_URL='http://127.0.0.1:8014'
node node_modules/expo/bin/cli start --web --port 3000 --offline
```

Servidor de revisão usa SQLite temporário e baseline **sintética** ID 1. Login
` tenderproof@example.test ` / ` TenderProof-local-review ` é exclusivamente local.
A porta 8014 evita interferir no servidor histórico 8013. Browser pago fica
explicitamente desabilitado nesse servidor. Publicação habilitada somente em seu
banco descartável. Não copie essas credenciais para produção.

Abrir `/tenderproof`, escolher IBGP/Demonstração, selecionar candidato42, informar
baseline1, preparar proposta, selecionar fim das inscrições, aprovar e aplicar.
Fluxo validado visualmente: `tpr-716ffe1fb518`, estado applied, versão1 e apenas
19/04→20/04. IMESO usa o mesmo fluxo (sem atribuir baseline IBGP a IMESO).
Ver [roteiro de cinco minutos](TENDERPROOF-DEMO.md).

### Operação, migração e segurança

Configuração de exemplo em backend/.env.example. Publicação e Browser live são
fail-closed por padrão; somente IDs em TENDERPROOF_PUBLISHER_USER_IDS revisam/publicam.
Todos endpoints usam JWT normal; observações, propostas, jobs e estratégias são
isolados por proprietário. Artefatos conferem hash/tamanho também na leitura,
e snapshots/bytes novos são escritos atomicamente. O armazenamento de runs ainda
é local por processo: use **um worker de aquisição**, sem prometer coordenação
distribuída. Jobs/estratégias/publicação têm suas próprias garantias persistentes.

Migração aditiva: `python -m app.tenderproof.publication_migration --apply` (somente no
banco autorizado). Startup também registra as tabelas novas no Base existente.
Não executamos migração no banco real. Backups/migração do catálogo real requerem
planejamento operacional próprio. Veja procedimentos em
[publicação e rollback](TENDERPROOF-PUBLICATION.md),
[processamento e orçamento](TENDERPROOF-PROCESSING.md),
[recuperação](TENDERPROOF-RECOVERY.md) e
[conciliação Solari](TENDERPROOF-SOLARI-AUDIT.md).

Relatórios locais protegidos em backend/.tenderproof: solari-audit.json,
publication-demo-report.json, publication-postgres-validation.json,
real-baseline-704.json, real-baseline-comparison.json, demo-phases4-7.json e ledgers
Sandbox. Relatório público sanitizado: docs/tenderproof-phases4-7-validation.json.
Não versionar diretório .tenderproof nem expor capacidades/IDs privados de recursos.
Nenhum deploy, push, merge remoto, publicação real ou notificação externa foi feito.

---

# Histórico preservado — fases 0–3

# TenderProof — fases 0–3

Fluxo de revisão: IBGP → até cinco candidatos → seleção explícita de um
concurso → aquisição de um edital → texto por página física → seis campos
com evidência → comparação com baseline quando fornecida → revisão.
Não publica nem altera concursos, versões ou notificações.

## Executar

No backend: `.venv/Scripts/python.exe -m pytest -q -m "not live"`.
Configure SOLARI_API_KEY apenas no ambiente local. Nunca versionar a chave.
Dependência instalada: `solari-browser==0.1.3`. Modo mock não precisa de chave.

API com autenticação normal do app:

1. POST `/tenderproof/runs` com `{"mode":"mock"}` ou `{"mode":"real"}`.
2. POST `/tenderproof/runs/{run_id}/select` com candidate_id e o mesmo mode.
3. GET `/tenderproof/runs/{run_id}/result`.
4. POST `/tenderproof/runs/{run_id}/replay/refresh` consulta o controle remoto;
   não abre browser. POST `.../sessions/reconcile` solicita confirmação de
   encerramento quando ainda não foi obtida.
5. GET `/tenderproof/runs/{run_id}/artifacts/{artifact_id}` devolve o PDF
   autenticado. A interface confere tamanho, assinatura e SHA-256 recebido.
Na web, depois da conferência aparece a opção Baixar PDF autenticado. O
visualizador interno experimental foi removido para manter o foco da etapa
na integração Solari e no acesso autenticado ao artefato. Não é necessário
um leitor de PDF embutido para a aquisição ou a verificação de evidências.

Menu mobile: TenderProof (IBGP). O run pode ser retomado pela rota
`/tenderproof?runId=...`. O modo fica vinculado ao run no servidor. A segunda
seleção no mesmo run é rejeitada. Só o proprietário autenticado pode consultar
ou operar seu run, inclusive PDF, replay e reconciliação. Snapshots antigos sem
proprietário não são expostos pela API.

## Ambiente isolado de revisão

`backend/scripts/tenderproof_review_server.py` inicia a API no loopback 8013,
com SQLite descartável e autenticação normal. Carrega somente SOLARI_API_KEY
do backend/.env. Não conecta ao banco canônico. O script cria seu usuário
local descartável; as credenciais estão no cabeçalho do script e não devem
ser usadas em produção. As migrações PostgreSQL não rodam nessa fixture.

A interface usa EXPO_PUBLIC_API_BASE_URL=http://127.0.0.1:8013.
O armazenamento de revisão fica em `backend/.tenderproof/review/`, ignorado
pelo Git. Os testes usam diretórios temporários separados. Na API normal,
artefatos e snapshots ficam em `backend/.tenderproof/`; é armazenamento local
por processo, sem migração do catálogo. Execute somente um worker para
preservar a trava de concorrência de processo.

## Aquisição e limites

- Discovery usa uma sessão curta; detalhe e download compartilham outra.
  Nenhuma sessão fica aberta esperando a seleção humana.
- Downloads remotos usam `save_as` e aguardam `failure()`. `path()` não
  funciona em conexões remotas do SDK instalado.
- Ausência real de âncora permite fallback HTTP no mesmo contexto. TypeError
  ou AttributeError na busca da âncora não se tornam ausência de link.
- Fallback usa max_redirects=0. Cada Location é validado antes da próxima
  requisição; há teto e detecção de ciclo. Rotas do browser não interceptam
  APIRequestContext. Os doubles dos testes refletem essa separação.
- HTML, PDF inválido e excesso de tamanho são rejeitados. Temporários locais
  e artefatos do SDK são limpos. O SDK materializa a transferência; a checagem
  de tamanho não é um limite de streaming. Content-Length é checado antes de
  ler o corpo quando fornecido.
- Detalhe/download compartilham prazo de até 240 segundos; encerramento tem
  prazo próprio. Interface aguarda até 400 segundos. Falhas devolvem run com
  diagnóstico; timeout do cliente não autoriza repetir uma execução.
- Replay: available/pending/disabled/failed. Consulta limitada e independente
  do browser. GET 404 da sessão não prova encerramento. `release()` do SDK
  oculta falhas; a reconciliação usa `release_and_wait()` para confirmação.

## Evidência independente — 7 de setembro de 2026

**Offline:** 210 testes aprovados, dois testes live não executados pelo pytest.
Cobertura inclui autenticação, isolamento por usuário, ausência de escrita
canônica, redirects proibidos antes da requisição, transferência remota,
limpeza, fallback, erros de programação, evidências e estados de replay.
TypeScript: erro preexistente em components/ExternalLink.tsx:13; nenhum erro
TenderProof na verificação realizada.

**Interface/API:** login normal no ambiente isolado, navegação pelo menu,
modo demonstração, seleção, seis campos, cinco concordâncias e uma divergência.
Conferência SHA-256 dos bytes autenticados exibida na interface. O visualizador interno foi retirado após falhar no teste manual; o usuário
redirecionou o foco para a integração Solari. A API devolve o PDF autenticado
e a interface confere seu SHA-256. A abertura em leitor externo/download do
navegador não foi validada pela automação; isso fica separado da validação de
aquisição. Compartilhamento nativo não foi exercitado em aparelho. O build web
final passou sem a dependência PDF.js.

**Real pela interface:** uma tentativa, run `tpr-c84fdce378eb`, iniciado em
2026-09-07 às 20:38:31 UTC e concluído às 20:39:39 UTC. Discovery retornou
ITABIRAPREV, Bom Despacho, Dores do Indaiá, Faria Lemos e Paracatu. Selecionado
cand-704 (ITABIRAPREV). Um edital adquirido via fallback legítimo por ausência
de âncora correspondente, sem TypeError mascarado. Nenhuma segunda tentativa.

- PDF oficial: endpoint IBGP `/rest/concurso/download/edital/23011/`.
- 806.581 bytes; SHA-256
  `ac7a4bbb6ddd42e9e9889f36687c0e1406703bc945e6196d0170fb9a8704078f`.
- 46/46 páginas; validação de identidade valid.
- Título e edital_numero supported; inscrições conflict;
  órgão e remuneração unknown com motivos.
- Sem baseline fornecida: interface mostra os seis campos e a ausência de
  baseline. Não atribui divergências automaticamente ao crawler.
- Duas sessões com close confirmado. Replay pending após prazo inicial de
  10 segundos por etapa e atualização autenticada pela interface, limitada
  a 20 segundos por sessão. IDs completos ficam no snapshot local protegido.
- Resultado reaberto por link autenticado após reinício, sem nova aquisição.
- Bytes salvos conferidos novamente contra o hash. O caminho de clique remoto
  foi testado offline; esta aquisição real usou request.

Os três runs históricos do relatório anterior não foram reconciliados: os
snapshots locais encontrados só continham IDs de mocks/doubles. Faltam os
IDs reais históricos. Não tratar a ausência de registros como prova de
encerramento. Preço e custo não foram verificados no faturamento do provedor.

## Escopo e pendências

Replay pode permanecer pending como limitação externa, com consulta e estados
verificados. Visualização do PDF em leitor externo é uma limitação de verificação da interface, não um bloqueio da integração Solari. Não houve
publicação, deploy ou push. Fora do escopo: OCR, outros sites/bancas,
retificações automáticas, todos os cargos, Sandbox/Desktop, self-healing e
refatorações amplas. Conflitos e valores desconhecidos permanecem explícitos.


## Fechamento da auditoria

Evidência legível por máquina: `docs/tenderproof-validation.json`. Em
2026-09-07T21:05:25Z, login normal, resultado, PDF e atualização de replay
responderam 200. Hash dos bytes conferido novamente. Nenhuma sessão nova
foi criada nessa consulta. As duas sessões permaneciam com encerramento
confirmado e replay pending.

O contrato agora expõe closure_status como confirmed/requested/unknown,
derivado de confirmação e solicitação efetivas; timeout não confirma close.
Testes verificam os três estados. Erros do serviço passam pela sanitização
antes de aparecer no run, com teste de credencial sintética em URL do SDK.

Correção adicional da guarda do clique: route.fetch(max_redirects=0) impede
redirecionamento automático. Uma resposta 3xx é abortada, deixando o download
usar a cadeia HTTP validada. O handler de rotas não é considerado uma guarda
por hop: conforme a documentação oficial, só recebe o primeiro URL de um
redirect. Testes exercitam respostas 200 e 302 e liberação de recursos.
Referências: https://playwright.dev/python/docs/api/class-page#page-route e
https://playwright.dev/python/docs/api/class-route#route-fetch.

A execução real acima comprovou o fallback request. O caminho de clique com
transferência remota e a última guarda de redirects foram verificados offline
com doubles do SDK, sem alegar uma nova execução real desse caminho. Não foi
necessário consumir a segunda tentativa autorizada.
