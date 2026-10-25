# Verificação local — 25/10/2026

Verificação funcional em cópia isolada do código público `ac72976` e do aplicativo `9f6067a`, com banco PostgreSQL 15 descartável. O banco do piloto existente não foi aberto nem alterado. A interface web foi exportada e servida com o proxy de mesma origem e os cabeçalhos exigidos pelo SQLite WASM. API e interface ficaram restritas a `127.0.0.1`.

## Coleta oficial e publicação revisada

- A descoberta real em `access_open` retornou cinco candidatos. É uma amostra limitada, não cobertura integral da fonte.
- O candidato IPSEMG, identificador externo `175`, foi observado em `https://access.selecao.net.br/informacoes/175/`.
- O edital oficial foi adquirido com 850.850 bytes e 47 páginas de texto. SHA-256: `169ef2f8a677af8093837eeed079806b9083f2a9e0ccd2c8fa8706fffbf253b6`.
- O título, órgão, edital `2/2026` e período de inscrições de 28/09 a 05/11/2026 foram reproduzidos a partir do documento. Cargos, remuneração, localização e prova sem evidência suficiente continuaram pendentes.
- Foi corrigida a identificação do órgão no cabeçalho de instituto da ACCESS. A regra exige primeira página, título observado correspondente e cabeçalho próximo de concurso/processo seletivo. Casos sem essa corroboração continuam desconhecidos.
- A proposta foi aprovada e aplicada somente no banco isolado. Repetir a aplicação preservou um concurso e uma versão, sem duplicação.
- Birigui (`183`) apresentou edital consolidado que exige revisão dos efeitos das alterações. O fluxo recusou o processamento automático; não foi publicada uma versão incompleta para contornar esse bloqueio.

## Interface, armazenamento local e reconexão

Login, checkpoint, busca por `IPSEMG`, detalhe, período de inscrições e links oficiais foram observados no navegador usando os dados realmente coletados.

Renovação de sessão e consulta autenticada retornaram HTTP 200; checkpoint sem autenticação e login inválido retornaram HTTP 401.

Com a aplicação já carregada, o servidor da origem web foi parado. A interface continuou navegável com seu catálogo local. Foram criados um favorito e um alerta; ambos reapareceram nas telas locais enquanto a API continuava com zero favoritos e zero alertas.

Após religar a origem e reabrir a tela de sincronização, as operações chegaram à API: criação do favorito e do alerta com HTTP 201, seguida de checkpoint HTTP 200. O banco passou a conter exatamente um de cada.

O ciclo inverso também passou: com a origem novamente parada, favorito e alerta foram removidos localmente; o banco ainda continha um de cada. Depois de reconectar, os dois DELETE retornaram HTTP 204 e o checkpoint confirmou zero favoritos e zero alertas.

Isso verifica a aplicação web já carregada com a origem indisponível e a reconciliação posterior. Não comprova instalação/PWA, recarga da página sem rede, reinício de aplicativo nativo, modo avião de dispositivo, entrega de push ou sincronização nativa em segundo plano.

## Correções e verificações automatizadas

- Criação e listagem de fontes retornavam HTTP 500: o schema de resposta exigia campos de revogação que pertencem aos dispositivos push, não ao modelo de fonte. O schema foi corrigido e recebeu teste de criação/listagem pela API.
- Foram adicionados testes positivos e negativos para a identificação do instituto da ACCESS.
- Caminhos de fixtures documentais foram ancorados no arquivo de teste, permitindo a execução a partir da raiz ou de `backend`.
- Os 11 testes do aplicativo passaram; TypeScript e a exportação web concluíram sem erro.
- A suíte focal de fontes, validação, idempotência, publicação revisada e coleta contínua passou com 77 testes. O CI agora inclui as regressões de resposta de fontes e identidade da ACCESS.
- A suíte histórica completa não é autossuficiente em um clone: há testes que dependem de PDFs e resultados de processamento dentro de `backend/.tenderproof/`, ignorado pelo Git e ausente nesta máquina. Exemplo: o PDF preservado de Publiconsult/681. Esses testes não foram considerados aprovados nem convertidos em sucesso por omissão dos artefatos.
- Expectativas históricas de identidade dos envelopes OMNI/Contemax foram alinhadas ao importador atual, que inclui usuário e metadados do artefato; os testes também verificam separação entre usuários. No OMNI, os métodos globais `1.22` e `1.23` produzem a mesma identidade: a expectativa antiga já estava desatualizada antes desta correção.

Para repetir a suíte focal, a partir de `backend` com as dependências instaladas:

```sh
DATABASE_URL=sqlite:// python -m pytest -q tests/test_source_response.py tests/test_access_institute_identity.py tests/test_sanity_validation.py tests/test_idempotency.py tests/test_connectors_fixtures.py tests/test_tenderproof_publication.py tests/test_tenderproof_pilot_operation.py tests/test_tenderproof_continuous.py
```

## Operação e limites

Um trabalhador Celery real foi iniciado contra Redis 7 isolado. Duas tarefas percorreram produtor → Redis → trabalhador → resultado: `heartbeat` respondeu `status=ok`; a tarefa agendada do coletor legado respondeu `status=disabled, processed_sources=0`, conforme a configuração padrão. O coletor legado não foi habilitado, e essa rodada não disparou coleta das 99 fontes.

`api.observador.tech` é um túnel Cloudflare para o computador local do mantenedor. Depende da máquina, API e túnel ativos. O HTTP 530 observado nesta data indica que esse caminho público estava indisponível; não é evidência de hospedagem permanente nem substitui a verificação local acima.

Não foram certificados os 99 portais, todos os campos dos editais, a revisão documental de Birigui, dispositivos Android/iOS, notificações push, tarefas de fundo nativas, backup/restauração ou a execução periódica completa do agendador nesta rodada. As coletas oficiais foram síncronas e a publicação passou pelo fluxo revisado no banco isolado.

Credenciais, tokens, contas descartáveis e registros privados da sessão não fazem parte deste relatório.
