# TenderProof — etapa 10: coleta contínua

Implementada em 07/09/2026. A coleta produz observações e artefatos para revisão.
Nenhum worker contínuo escreve no catálogo, em versões, publicações ou notificações.
O conjunto configurável é derivado do registro comum `SOURCE_ADAPTERS`.
Cadastro de uma fonte no inventário não a habilita. Novas fontes sem demonstração
sintética registrada recusam `mode=mock`, evitando reutilizar material IBGP.

## Habilitação e operação

A operação exige três condições: `TENDERPROOF_CONTINUOUS_ENABLED=true`, ID do
operador em `TENDERPROOF_CONTINUOUS_OPERATOR_USER_IDS` e configuração da fonte com
`enabled=true`. A lista de operadores é vazia por padrão. Revogar o ID bloqueia
agendamento, consumo e novas requisições de jobs existentes. As configurações e
seu histórico continuam acessíveis ao proprietário autenticado.

API e workers precisam compartilhar o diretório local definido por
`TENDERPROOF_ARTIFACT_DIR`. O volume deve abranger seu diretório pai: ali vivem
`continuous.sqlite3`, `operational.sqlite3`, processamento e PDFs. SQLite usa WAL,
transações de escrita imediatas e sincronização completa. É uma implantação num
único host/volume local; não colocar o banco SQLite em NFS/SMB nem distribuir
workers por máquinas com cópias independentes do volume.

O worker consome a fila `tenderproof`. O módulo Celery é
`app.tenderproof.continuous_tasks`; as tarefas se chamam
`app.tenderproof.continuous.tick` e `app.tenderproof.continuous.job`. O beat deve
chamar o tick a cada 30 segundos. A configuração padrão permanece desabilitada,
inclusive com o beat em execução. Nenhuma credencial ou orçamento pago é ativado
pela instalação desta etapa.

Exemplo de corpo para `PUT /tenderproof/continuous/sources/ibgp_open`:

```json
{
  "enabled": true,
  "mode": "real",
  "interval_s": 3600,
  "max_listing_pages": 30,
  "max_candidates": 100,
  "max_attempts": 3,
  "retry_base_s": 30,
  "min_request_gap_s": 2,
  "job_timeout_s": 180,
  "cycle_timeout_s": 7200,
  "max_download_bytes": 31457280,
  "max_pdf_pages": 60,
  "max_documents": 100,
  "allow_browser": false,
  "max_browser_seconds": 0
}
```

Os limites possuem tetos de validação. São congelados no início do ciclo;
desabilitar a fonte, revogar o operador ou suspender o browser têm efeito nas
próximas operações do ciclo existente. A aquisição recebe também o prazo restante
do ciclo. Trabalho já em processamento pode concluir para preservar suas
evidências; ultrapassar o prazo resulta em cobertura parcial. Fontes com histórico
não podem trocar `mock` por `real`, evitando misturar material sintético e oficial.

## Endpoints autenticados

| Endpoint | Finalidade |
| --- | --- |
| `GET /tenderproof/continuous/status` | Opt-in, políticas próprias, ciclos, motivos de cobertura parcial, contagens e suspensão de browser. |
| `PUT /tenderproof/continuous/sources/{source}` | Configurar ou pausar uma fonte do operador. |
| `POST /tenderproof/continuous/sources/{source}/collect` | Enfileirar um ciclo durável, retornando 202 mesmo se o broker estiver indisponível. Repetir devolve o ciclo ativo existente. |
| `POST /tenderproof/continuous/sources/{source}/tracked` | Cadastrar uma URL oficial conhecida e título opcional para acompanhamento. |
| `POST /tenderproof/continuous/sources/{source}/browser/reconcile` | Consultar/solicitar encerramento das sessões pendentes pelo control-plane, sem abrir browser. |
| `GET /tenderproof/continuous/cycles/{cycle_id}` | Jobs, tentativas, progresso, cobertura e reserva de browser. |
| `GET /tenderproof/continuous/snapshots/{job_id}` | HTML preservado como dados JSON e metadados de aquisição, somente para o proprietário. |
| `GET /tenderproof/continuous/observations` | Observações para revisão, com paginação por `limit` e `offset`. |

As execuções completas e PDFs permanecem acessíveis nos endpoints TenderProof
já existentes. A lista de observações não publica dados; a integração de cadastro
e precedência de informações pertence às próximas etapas.

## Retomada, cobertura e acompanhamento

O SQLite é a autoridade da fila. Redis transporta avisos de trabalho disponível;
nenhum job é marcado definitivamente como enviado. Se a mensagem desaparecer ou
o envio falhar, o tick seguinte tenta novamente. Mensagens repetidas encontram o
job já concluído ou em execução e não repetem os efeitos.

O claim é transacional, permite somente um job por proprietário/fonte e cria um
token com geração crescente e prazo. Após morte do worker, outro processo pode
reivindicar o job quando o prazo vence. O antigo token não pode persistir
checkpoints nem resultados. A aquisição compartilha também o lease global do
TenderProof. Contenção nesse lease adia o job sem gastar tentativas ou reserva
paga. Falhas reais usam tentativas limitadas e backoff exponencial, sem apagar
o último resultado válido conhecido.

O HTML é preservado antes do processamento. Candidatos, novas páginas e avanço
da fila são confirmados juntos numa transação. Após uma queda entre gravar uma
execução concluída e confirmar a fila, o retry reaproveita o resultado existente:
listagens são reanalisadas a partir do snapshot íntegro; detalhes usam o PDF e o
resultado concluído sem outro download. Uma listagem que falhou na interpretação
pode ser adquirida novamente numa tentativa controlada.

Paginação e abas são percorridas somente por URLs observadas e permitidas pelo
adaptador. Laços de navegação não provam cobertura completa: cada família de
rota precisa alcançar um marcador explícito de fim/vazio. Ausência desse
marcador, limite atingido, falha ou interrupção por prazo deixam o ciclo parcial.
"Ciclo concluído" descreve o conjunto de rotas verificado nesse ciclo; não é uma
certificação global de que todo conteúdo da banca foi descoberto.

Candidatos conhecidos são armazenados independentemente das listagens e
revisitados por prazo, mesmo após desaparecerem da página de inscrições abertas.
Quando há mais candidatos conhecidos que o limite por ciclo, os menos
recentemente verificados têm prioridade e a limitação aparece na cobertura.
Novos documentos no manifesto geram outra observação mesmo se o edital original
mantiver os mesmos campos. Retificações são sinalizadas para revisão; esta etapa
não interpreta automaticamente seus efeitos sobre prazos e salários.

Observações iguais por candidato, documento, manifesto, semântica, validação e
versão de extração são deduplicadas. Seus timestamps são atualizados. Um erro
posterior preserva a referência ao último resultado válido.

## Browser e cobrança

HTTP é a primeira via. Fallback pago exige também
`TENDERPROOF_BROWSER_LIVE_ENABLED=true`, `allow_browser=true` e reserva de segundos
suficiente. Antes de cada tentativa é reservada conservadoramente uma janela
`job_timeout_s`. Falha/crash não devolvem essa reserva; somente contenção sem
aquisição pode devolvê-la. O valor representa orçamento operacional de sessão,
não medição confirmada de cobrança em dólares. O processamento de PDF ocorre
após o fechamento do navegador.

Um journal confirma intenção **antes** do launch, o ID assim que recebido e
encerramento somente após confirmação do provedor. Qualquer intenção pendente,
inclusive uma queda sem ID retornado, mantém novas criações suspensas para a
fonte; HTTP pode continuar. Expiração de lease não comprova fechamento remoto.
Intenções sem ID exigem investigação do provedor e permanecem bloqueadas; a API
não as resolve por presunção de timeout. A reconciliação não fecha uma aquisição
local ainda ativa e só libera a suspensão quando todos os encerramentos
conhecidos foram confirmados.

## Evidências de validação

- `backend/tests/test_tenderproof_continuous.py`: atomicidade sob falha de commit,
  leitores em outro processo, fencing, retries, deduplicação, recuperação de
  listagens e resultados, acompanhamento após listagem vazia, limites, ciclos de
  paginação, isolamento por usuário, revogação operacional, contenção sem
  penalidade e journal de browser sobrevivendo à queda.
- `backend/scripts/tenderproof_continuous_probe.py`: Redis e Celery reais, worker
  encerrado após checkpoint de detalhe, outro worker retomando, reentrega
  duplicada, uma observação final e PDF íntegro lido por outro processo.
- `docs/tenderproof-continuous-validation.json`: resultados da prova. Material
  explicitamente sintético; banco canônico e browser pago não utilizados.

Reprodução em Redis **dedicado e descartável** na porta local 16497, banco 14:

```text
python scripts/tenderproof_continuous_probe.py --root .tenderproof/continuous-probe-NOVO-ID --broker-url redis://127.0.0.1:16497/14 --report ../docs/tenderproof-continuous-validation.json
```

A prova confirma a morte do processo antes de antecipar, somente no banco
isolado, a expiração dos leases. Isso reduz o tempo do ensaio sem depender de
espera real de 150 segundos e não altera nenhum relógio do sistema. Todos os
workers criados são encerrados. O Redis usado na validação foi removido após
conferência de seu identificador completo.

## Evolução nas etapas 11–13

A API `GET /tenderproof/continuous/catalogue` lista as 99 entradas originais e
separa presença de adaptador de homologação. `GET /metrics` retorna contagens de
jobs por estado, tentativas adicionais, atraso do trabalho pronto, duração dos
ciclos concluídos por fonte, páginas/bytes HTML preservados e tentativas de
navegador sem encerramento. Todos os números são do proprietário autenticado;
a duração de ciclo inclui espera na fila. Não representam tempo de CPU nem
cobrança do provedor. `snapshot_html_bytes` mede HTML, não PDFs ou uso total em disco.

Uma configuração de fonte removida/inválida não impede agendar as demais. Os
trabalhos usam os hosts registrados pelo adaptador específico. Falha na seleção
ou aquisição do edital principal após captura do manifesto mantém uma observação
`document_review_required` para revisão: os links foram observados, seus bytes e
efeitos não foram comprovados. Repetir o mesmo manifesto deduplica essa observação;
o último resultado válido do candidato continua preservado.

A revisão usa as propostas existentes de publicação, agora também para concursos
novos; consultar TENDERPROOF-PUBLICATION.md. Coletar nunca aplica uma proposta.

## Backup e restauração do volume operacional

O utilitário `app.tenderproof.operational_backup` copia todos os artefatos do volume
e usa a API de backup SQLite para incorporar WAL nos bancos de destino. A origem
deve ser o diretório operacional completo, incluindo runs, artifacts, processamento
e todos os ledgers. Não usar somente a pasta de PDFs. O banco canônico PostgreSQL
é separado e precisa de backup próprio coordenado com a parada dos escritores.

1. Pausar fontes; parar scheduler, API e workers que escrevem o volume. Confirmar
   os processos encerrados e reconciliar qualquer sessão remota pendente.
2. Em backend, executar `python -m app.tenderproof.operational_backup backup ORIGEM DESTINO_NOVO --writers-stopped`.
   O flag registra declaração do operador; o utilitário não mata processos e não
   certifica sozinho a ausência de escritores. Usar volume local, fora de OneDrive/NFS.
3. Executar `python -m app.tenderproof.operational_backup verify DESTINO_NOVO`.
4. Para ensaio de recuperação, `python -m app.tenderproof.operational_backup restore DESTINO_NOVO VOLUME_NOVO`.
   Toda a integridade é verificada antes de escrever; destino existente é recusado.
5. Configurar todos os serviços para o volume restaurado, conferir observações,
   bytes dos documentos e journal de sessões; reativar explicitamente apenas após
   conferência. Histórico não implica autorização de criar outra sessão remota.

Não há limpeza automática ou retenção nova. Preserve o backup original, manifesto,
PDFs e snapshots necessários a revisão, auditoria e rollback. Os quatro testes
`tests/test_tenderproof_operational_backup.py` comprovam restauração de fila e
artefato controlados, recusa de corrupção, destino existente e caminhos inválidos.
Isso não é evidência de restauração do banco real ou de armazenamento distribuído.

O ledger operacional agora também contém `document_review_state`, criado
aditivamente. Em volumes anteriores, o checkpoint usa o último manifesto
preservado como referência. Novidades documentais acumulam uma pendência que
não desaparece apenas porque o link saiu da página. Inclua esse banco no backup
integral; mover somente runs/PDFs para outro ambiente descartaria o contexto
necessário para impedir uma proposta antiga. A validade do original continua
separada dessa pendência. Consulte `TENDERPROOF-PUBLICATION.md` para a guarda
transacional e o endpoint autenticado de revisão.
