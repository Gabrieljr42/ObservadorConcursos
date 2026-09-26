# TenderProof — jobs limitados de processamento

Estado atual da fase 5: **concluída no escopo limitado de processamento**, com
conciliação do dashboard/faturamento ainda pendente. Há integração local com SQLite operacional persistente,
subprocesso PDF real e API autenticada. Após autorização foram exercitados
três Sandboxes reais: criação, arquivos, comando e encerramento funcionaram. A
primeira extração falhou por ausência de `pypdf`; a segunda executou a biblioteca
empacotada, mas recusou uma fixture erradamente gerada com duas páginas. A terceira
extraiu corretamente a fixture corrigida de uma página. Os testes automatizados remotos
continuam usando transporte falso. O processo local Windows não é uma sandbox de segurança do SO: não há
restrição de rede por firewall nem teto de memória aplicado pelo sistema operacional.

## Contrato e operação

`ProcessingService(root, concurrency=1, budget_usd=0, remote=None)` cria somente
`root/jobs.sqlite3` e artefatos operacionais, sem duplicar catálogo de concursos.
`enqueue(owner_id, content, limits=ProcessingLimits(), mode='local')` aceita apenas
`extract_pdf`; comandos de cliente/LLM/documento não são aceitos. `execute` reivindica
o job em transação SQLite `BEGIN IMMEDIATE`. A mesma execução terminal não é repetida.

Estados de job: `queued`, `running`, `succeeded`, `failed`, `cancelled`.
Sucesso significa conclusão da operação, não campos conhecidos, evidência aprovada
ou publicação. Jobs persistem hash de entrada, versão do extrator, limites,
tentativas, hash da saída, erro estruturado, recurso remoto privado, pedido e
confirmação de encerramento separados, duração e estimativa de custo.

O resultado contém `input_sha256`, `extractor_version`, `total_pages` e
`pages: [{page_number, text}]`; páginas físicas começam em 1. O serviço integra pelo
helper `extract_pages_isolated`, retornando os objetos `PageText` existentes.
PDF acima do número permitido de páginas é recusado; não é implicitamente aprovado
como extração completa. Sem OCR. Texto é dado não confiável, nunca uma instrução.

Endpoints usam o JWT normal do app e usuário ativo, não token especial de revisão:

| Método/caminho (prefixo `/tenderproof/processing`) | Efeito |
| --- | --- |
| POST `/from-run/{run_id}` | Enfileira artefato adquirido pelo mesmo usuário, conferindo SHA-256 |
| GET `/{job_id}` | Estado sanitizado do próprio job |
| POST `/{job_id}/execute` | Processa localmente, sem custo Solari |
| POST `/{job_id}/cancel` | Cancela fila ou sinaliza execução ativa |
| GET `/{job_id}/result` | Resultado próprio com hash verificado |
| POST `/recover` | Recupera somente jobs antigos do usuário; não cria recursos |

Nenhum endpoint habilita Solari, expõe capacidades remotas, aceita upload arbitrário,
comando, caminho ou alteração de orçamento. A API retorna 404 para outro proprietário.
Revisores devem usar a API, não acessar o ledger privado diretamente.

## Limites e isolamento real

| Limite | Padrão | Aplicação |
| --- | --- | --- |
| Arquivo | 10 MB | antes de enfileirar; hash verificado antes da execução |
| Páginas | 60 | worker recusa total excedido |
| Tempo total | 60 s | aplicação; com falha de cleanup remoto pode ultrapassar e continuar faturando |
| Operação | 30 s | local: processo morto no prazo; remoto: timeout HTTP e `timeoutMs` de exec |
| Concorrência | 1 | ledger transacional, inclui recursos sem encerramento confirmado |
| Tentativas | 1, máximo 3 | persistidas; retry local explícito; remoto não cria substituto automaticamente |
| Saída | 1 MB | worker limita texto/JSON e executor limita leitura/HTTP |
| Orçamento | US$ 0 | reserva persistente antes de admissão; Solari exige tarifa e orçamento positivo |

O tempo inclui a criação/processamento no fluxo remoto; encerramento recebe até
10 s adicionais por chamada. A estimativa não é um teto financeiro: timeout HTTP
não prova que trabalho remoto parou. O timeout do provedor é janela ociosa renovada
por atividade, não prazo absoluto. Recursos cujo fechamento não foi confirmado
continuam impedindo novas admissões. Nenhum reprocessamento recupera essa reserva
financeira automaticamente; ela é conservadora para o conjunto inteiro do ledger.

Localmente só são fornecidas variáveis mínimas do runtime Windows, sem chave,
DATABASE_URL, proxies ou `.env`. O comando é fixo, usa Python `-I`, stdin/stdout/stderr
descartados, cwd exclusivo e nenhuma shell. Isso reduz exposição, mas não impede
um exploit de parser de acessar arquivos que o usuário do SO pode ler. Para
isolamento de documentos hostis em produção, validar um executor com política de
memória/rede do SO ou a fronteira remota antes de afirmar isolamento forte.

Configuração local opcional, sem segredos:

```dotenv
TENDERPROOF_PROCESSING_DIR=.tenderproof/processing
TENDERPROOF_PROCESSING_CONCURRENCY=1
TENDERPROOF_PROCESSING_TOTAL_SECONDS=60
TENDERPROOF_PROCESSING_OPERATION_SECONDS=30
TENDERPROOF_PROCESSING_MAX_OUTPUT_BYTES=1000000
```

## Recuperação, artefatos e retenção

`recover()` só marca execuções antigas (prazo total e idade mínima de 120 s) como
interrompidas, consultando recursos conhecidos sem criar novos. Aplicar após parada
do worker antigo; não é mecanismo de eleição de líder. Recurso desconhecido fica
desconhecido. `reconcile_close(..., request_close=False)` consulta; `True` pede novo
fechamento somente quando esse efeito estiver autorizado. 404 não confirma encerramento.
Criação com resposta perdida mantém `creation_unknown=True` e bloqueia novas
admissões. Reconciliar manualmente por metadata do job/listagem documentada antes
de desbloquear; o serviço não abre outro recurso para resolver a dúvida.

Diretórios usam hash do usuário e UUID gerado do job. Entrada/saída são gravadas
com temporário exclusivo, flush/fsync e replace atômico. `result()` verifica o hash
novamente e funciona após recriar o serviço. Não há reutilização entre usuários;
o resultado terminal pode ser relido sem nova execução. A versão do extrator faz
parte do contrato, sem cache compatível automático entre jobs diferentes.

`cleanup(retention_seconds=86400)` remove entradas/saídas expiradas de jobs terminais
sem recurso desconhecido, preservando ledger, hashes e histórico. Retenção é uma
ação operacional explícita, não um agendamento instalado. Não limpa catálogo nem
snapshots históricos de aquisição. Faça backup e aplique permissões de diretório
adequadas ao serviço; IDs remotos armazenados no ledger são capacidades privadas.

## Fronteira Solari e preparação histórica da primeira tentativa

Esta seção registra a preparação anterior às três tentativas. O executor atual
transfere o zipapp com pypdf fixado, descrito abaixo; não depende de pypdf instalado
na imagem. As restrições de autorização citadas aqui representam aquele momento,
substituídas pela autorização posterior do usuário para testes adicionais.

O [contrato Sandbox oficial](https://docs.getsolari.com/api-reference/sandboxes)
permite create com CPU/memória e lifecycle kill; transferência por URLs assinadas,
exec binário/argv e DELETE com confirmação `200 {ok:true}`. A fronteira usa caminhos
fixos, não envia bearer nas URLs de arquivo, recusa hosts/redirects alternativos e
usa chave de idempotência igual ao job. Ela não instala pacotes nem usa shell.
`base` precisa conter `python3` e `pypdf`; a tentativa real encontrou Python, mas
não conseguiu importar pypdf. O SDK
Sandbox não está instalado, portanto o adaptador usa a API HTTP documentada, não
simula um SDK existente.

Operação concreta preparada para eventual autorização: **1 Sandbox**, `base`,
**1 vCPU / 2 GB**, **1 PDF fixture de uma página**, no máximo **60 s** de criação e
processamento, mais **10 s** para encerramento, **1 tentativa**, sem Browser,
Desktop, snapshot, volume, proxy, CAPTCHA ou instalação de dependências. Transfere
apenas o worker fixo e a fixture. Se pypdf não existir, falha e encerra; não instala.

Tarifa conservadora consultada em 2026-09-07: plano Free, **US$ 0,086/h** para
1 vCPU/2 GB. 60 s ≈ **US$ 0,00144**; 70 s ≈ **US$ 0,00168**, sem garantia de teto
em falha remota. Usar reserva mínima de **US$ 0,002** para essa operação.
Fonte: [preços oficiais Solari](https://docs.getsolari.com/pricing).
Essa operação recebeu autorização explícita posteriormente e foi executada uma
única vez conforme o registro abaixo. Não há autorização para segunda sessão,
instalação, template customizado ou ampliação de orçamento.

## Verificação reproduzível

Dentro de `backend`: `.venv/Scripts/python.exe -m pytest tests/test_tenderproof_processing.py -q`.
Resultado em 2026-09-07: **26 passed**, 4 avisos existentes de datetime SQLAlchemy.

Inclui subprocesso PDF real e SQLite descartável/reaberto, limites de páginas,
tamanho, saída e timeout, cancelamento ativo, concorrência/admissão, reserva
persistente concorrente de orçamento, falhas/encerramento com doubles, restart,
hash adulterado, retenção, ambiente sem segredos e API com JWT real e dois usuários.
HTTP Sandbox é MockTransport explicitamente falso. Isso não comprova infraestrutura
Solari, permissões reais, isolamento remoto ou faturamento.

Também foi processado **localmente**, em diretório/SQLite temporário descartável,
o PDF histórico preservado da execução `tpr-c84fdce378eb`: sucesso, 46 páginas,
3,547 s observados, hash de entrada `ac7a4bbb6ddd42e9e9889f36687c0e1406703bc945e6196d0170fb9a8704078f`,
zero recursos remotos. Essa execução valida a operação local sobre o artefato real
preservado; não é uma nova investigação Solari.

## Resultado da tentativa Sandbox real autorizada

Em 2026-09-07, **21:42:54–21:42:57 UTC**, executou-se
`backend/.venv/Scripts/python.exe backend/scripts/tenderproof_sandbox_live_check.py`.
O script tem marcador persistente de uso único; executá-lo novamente não cria recurso.
Chave: somente a substituta atual do `backend/.env`. Sem valores em logs/relatórios.

Job: `4c78b68f1a7241bcb7d494e9f9052f93`. Evidência local protegida:
`backend/.tenderproof/sandbox-live-authorized-20260907/report.json` e
`jobs/jobs.sqlite3`; capacidade remota completa apenas no ledger privado.
Hash da fixture sintética de uma página:
`4214e3e2c50db4211f0842a71d74b5cd9c42b67d62a762d118f2f1e9a7bffcc6`.

| Operação real | Resposta | Conclusão limitada |
| --- | --- | --- |
| Criar 1 Sandbox base / 1 vCPU / 2 GB | HTTP 201 | recurso criado |
| Upload do worker e PDF | 2 URLs HTTP 200, 2 PUT HTTP 200 | transferência realizada |
| Comando Python fixo | HTTP 200, exitCode 1 | worker executado, operação falhou |
| Download do resultado | URL HTTP 200, GET HTTP 200 | erro estruturado `dependency_unavailable` |
| Encerramento | DELETE HTTP 200, `ok:true` | encerramento confirmado pelo contrato Sandbox |

O worker usa apenas um import externo, `pypdf`; sua ausência impediu a extração.
Não se tratou HTTP 200 de comando como sucesso da extração. O job ficou `failed`,
`close_requested=true`, `close_confirmed=true`. Nenhum pacote foi instalado; nenhum
Browser, recurso substituto, template, snapshot ou volume foi criado.

**1 recurso, 1 tentativa**, 3,422 s observados pelo serviço, 5,219 s no script
incluindo preparação. Reserva/estimativa conservadora: **US$ 0,0016722222** para
70 s, dentro da autorização de US$ 0,002. **Faturamento confirmado: indisponível**.
Não se apresenta a reserva como cobrança; também não se usa tempo do cliente para
inferir a duração faturada pelo provedor.

Prova live obtida: lifecycle, transferência, execução do worker e encerramento.
Prova não obtida: extração PDF remota bem-sucedida. A próxima validação depende de
runtime que já contenha pypdf ou de autorização específica para instalar/preparar
essa dependência e abrir nova sessão. A autorização atual está consumida.

## Correção offline preparada após a tentativa (sem segunda sessão)

`processing_bundle.py` monta um zipapp determinístico com o worker fixo, as
**57 fontes Python de pypdf 6.16.2** e a licença. Verifica a versão instalada e
o fingerprint das fontes antes de qualquer criação remota; recusa divergências.
Não inclui `.env`, site-packages inteiro, extensões nativas, caches ou arquivos
do usuário. O processo remoto passa a executar `python3 -I -S` sobre esse zipapp,
sem pip, resolução de dependências ou acesso à rede para instalação.

Artefato preparado: `backend/.tenderproof/sandbox-prepared-zipapp/tenderproof-worker.pyz`.
Manifesto: `backend/.tenderproof/sandbox-prepared-zipapp/manifest.json`.
Tamanho: **376.355 bytes**. SHA-256 do zipapp:
`88f4f0e21e33f048c55b410c67d016a917a6912a918f02e576675831e7d7a2d8`.
Fingerprint pypdf:
`86ac853161260359fbb55490ac05da42109d757f30b7dce6174642682ee97c82`.

Verificação atualizada: **28 testes aprovados** em 14,18 s, incluindo execução real
local do zipapp com `-I -S` (sem site-packages), hash e texto da página conferidos,
além do contrato HTTP com MockTransport. Não houve novo recurso remoto durante a
correção, nem alteração do relatório histórico da primeira tentativa.

A próxima operação proposta continua limitada a **1 Sandbox / 1 vCPU / 2 GB**,
**1 PDF sintético de uma página**, upload do zipapp acima e da fixture, **1 tentativa**,
**60 s + 10 s para fechar**, reserva **US$ 0,002** (estimativa 70 s **US$ 0,0016722222**).
Precisa de **nova autorização específica**: a autorização anterior foi consumida.
A correção foi posteriormente autorizada e exercitada conforme a segunda tentativa
abaixo; não se reclassifica a primeira tentativa falha como sucesso.

## Segunda tentativa e correção da fixture

A segunda autorização específica foi consumida em **2026-09-07 21:48:44–48 UTC**.
Job `754ed36b22ba4a799ece27409a9fdc28`, evidência separada em
`backend/.tenderproof/sandbox-live-authorized-20260907-zipapp-v2/report.json`.
CREATE **201**, uploads **200**, comando **200 / exitCode 1**, download **200**,
DELETE **200 / ok:true**. Erro estruturado: **`page_limit`**. Um recurso criado e
encerrado, **4,046 s** observados no serviço, **4,921 s** no script.

**Erro de preparação identificado:** `make_text_pdf` interpreta cada item da lista
como uma página. O script forneceu duas strings em vez de uma string com quebra
de linha. Por isso, **as fixtures das duas tentativas tinham duas páginas**, embora
os relatórios originais as rotulassem incorretamente como uma página. A primeira
tentativa parou no import de pypdf; a segunda aplicou corretamente `max_pages=1` e
recusou o documento. Isso foi erro do script local, não falha do provedor.

Os relatórios originais foram preservados. Cada pasta agora contém
`fixture-correction.json` registrando a contagem física conferida, sem alterar a
evidência histórica. As menções anteriores deste documento a fixture live de uma
página descrevem a intenção autorizada e estão corrigidas por este registro.

A fixture corrigida tem **1 página**, **720 bytes**, SHA-256
`b09020b187cb638c9f809603ac2e95893ceca88c2462c1c52b48cdb74e76e92f`.
Artefato e prova: `backend/.tenderproof/sandbox-prepared-zipapp/corrected-one-page-fixture.pdf`
e `fixture-preflight.json`. O script agora conta páginas antes de construir o
cliente remoto ou consumir o marcador. Um teste injeta fixture de duas páginas e
prova que nenhum cliente/recurso é construído. Outro executa exatamente a fixture
corrigida pelo zipapp `-I -S`, conferindo 1 página, hash e texto esperado.

**Acumulado naquele momento: 2 recursos criados, ambos com encerramento confirmado.** Reservas
autorizadas: US$ 0,004; estimativas conservadoras registradas: US$ 0,0033444444.
**Custos faturados: desconhecidos.** Até esse registro não havia terceira sessão
nem nova instalação. A autorização e a extração subsequentes estão registradas
na seção seguinte; o preflight e a fixture foram corrigidos exclusivamente offline.

## Terceira tentativa: extração remota conferida

Após o usuário autorizar persistentemente os testes adicionais, foi executada
**uma terceira sessão limitada**, em **2026-09-07 21:54:53–56 UTC**, sem ampliar
os limites técnicos por sessão. Revisão explícita do script: `zipapp-v3-one-page`.
Job `fc99d8e0cc894f2b87b3f4e097281a0b`, relatório/ledger/artefatos separados em
`backend/.tenderproof/sandbox-live-authorized-20260907-zipapp-v3-one-page/`.

CREATE **201**, dois uploads **200**, comando **200 / exitCode 0**, download **200**,
DELETE **200 / ok:true**. O job concluiu `succeeded`, `close_requested=true`,
`close_confirmed=true`. A fixture foi conferida com **uma página antes de criar**.
A saída também contém **uma página**, hash de entrada correto e o texto esperado.
SHA-256 da saída:
`b109008351770d5005b3e8531f6e2cf648f376fb0bbe188ce3a1c8a19c1de72a`.
Tempo do serviço **3,750 s**; script **5,062 s**. Nenhuma instalação ou acesso a
portal oficial foi necessário; esse é um **teste sintético real no Sandbox**.

**Acumulado atualizado: 3 recursos criados e 3 encerramentos confirmados** pelas
respostas DELETE documentadas. Reserva conservadora utilizada para admissão:
**US$ 0,0050166667** no total, com limite de US$ 0,002 por tentativa.
**Faturamento confirmado continua desconhecido.** A autorização adicional existe;
não há necessidade de repetir testes já comprovados nem manter recursos abertos.

Prova obtida: processamento de uma página, hashes, dependência empacotada, arquivos,
comando e fechamento reais. Sucesso da terceira tentativa não apaga a falta de
dependência na primeira nem o erro de fixture da segunda. A suíte offline atual
tem **30 testes aprovados**; cenários destrutivos/timeout do provedor continuam
identificados como doubles, não foram deliberadamente reproduzidos com recursos pagos.
