# Revisão contínua e publicação — interface da etapa 12

Validação: 07/09/2026. Implementação integrada à rota `/tenderproof` existente.

O painel consulta fontes configuradas, ciclos, limites de cobertura e observações paginadas em blocos de vinte. O inventário mostra todas as fontes retornadas pela API e distingue adaptador implementado de homologação. Fontes sem configuração ou sem observação não são apresentadas como vazias ou homologadas. O seletor de aquisição usa somente adaptadores implementados; demonstração fica restrita às fontes com fixture disponível.

Cada observação exibe fonte, título, data, manifesto documental, material real/sintético, validação e truncamentos. Falha após captura de manifesto mantém acesso à observação e informa quando apenas links foram observados, sem bytes verificados. O operador abre a execução preservada para conferir PDF e páginas; não é disparada nova aquisição ao abrir uma observação.

A proposta usa o mecanismo de publicação existente: ID vazio pede resolução de identidade ao servidor; ID explícito pede associação ao concurso indicado com revalidação. A revisão mostra cadastro novo ou atualização, identidade, endereço oficial, valores atuais e propostos, evidências por campo, páginas físicas, SHA-256, impedimentos e preservação de valores desconhecidos/conflitantes. Criação exige selecionar todos os campos mínimos informados pelo servidor. A aprovação por campos precede um botão de aplicação que descreve criar/atualizar. Uma resposta incerta ou rejeitada exige consultar a situação; uma proposta desatualizada exige recomparação. A reversão pede motivo e explica que a reversão de criação arquiva o cadastro preservando histórico. Estados, versão, diff e situação declarada das notificações aparecem após aplicação.

Arquivos: `mobile/app/tenderproof.tsx`, `mobile/src/components/TenderProofReview.tsx`, `mobile/src/api/tenderproof.ts`. A correção de tipo em `mobile/components/ExternalLink.tsx` restringe o contrato de link externo a HTTP(S), resolvendo erro TypeScript anterior identificado na validação. Nenhum arquivo local anterior foi restaurado ou descartado.

## Evidências reproduzíveis

No diretório `mobile`:

```powershell
node node_modules/typescript/bin/tsc --noEmit
node scripts/test-tenderproof-review.cjs
$env:EXPO_PUBLIC_API_BASE_URL='http://127.0.0.1:8011'
$env:EXPO_NO_DOTENV='1'
node node_modules/expo/bin/cli export -p web --clear --output-dir dist-tenderproof-stage12
```

TypeScript: passou. Teste de componentes: passou, exercitando seleção mínima para criar, consequências visíveis, trecho documental, aprovação, aplicação rejeitada com 409, consulta posterior desatualizada, reversão com motivo, cobertura parcial e documento não verificado. O teste usa React Test Renderer já instalado e API sintética em memória; não faz HTTP nem publica dados. Aviso de depreciação do React Test Renderer permanece, sem falha. Expo export: passou, 23 rotas, incluindo TenderProof. O build usa URL loopback explícita e não altera `.env`. A exportação não demonstra funcionamento de dispositivos iOS/Android físicos.

No diretório `backend`:

```powershell
.venv/Scripts/python.exe -m pytest tests/test_tenderproof_compare_api.py::test_review_interface_files_exist_with_required_markers -q
```

Passou (1 teste). Essa verificação é estrutural e não substitui o teste comportamental do componente.

## Prova visual autenticada e limpeza

O usuário autorizou explicitamente o login sintético após a revisão automática inicialmente recusá-lo. O ensaio usou localhost:3000 e servidor de testes em127.0.0.1:8011, autenticação normal, sem injeção de token. O cache Metro inicialmente manteve a porta8013 de exportação antiga; foi corrigido com `--clear` e `EXPO_NO_DOTENV=1`, e o literal8011 foi conferido no bundle. O SQLite web mostrou `Invalid VFS state` ao gravar cache após autenticar. A navegação normal para TenderProof utilizou a sessão autenticada legitimamente salva e permitiu completar as ações abaixo. A falha do cache local continua uma limitação de integração web; não impede a revisão autenticada da API e não foi ocultada.

1. Banco descartável com baseline: mock IBGP, observação `tpr-bb9d13b0844f`, seleção do edital42, autoidentificação do concurso1, revisão do prazo19→20/04/2026 com trecho e SHA-256, aprovação de somente esse campo, aplicação versão1 e reversão versão2 com motivo. Prazo original19/04 restaurado, zero notificações materializadas.
2. Outro banco descartável sem baseline (`--without-baseline`): mesma observação preservada reaberta sem aquisição; proposta de novo cadastro com banca/URL documental e três campos mínimos explícitos; aprovação, criação do concurso1 versão1, reversão versão2 arquivando o concurso. Datas não selecionadas permaneceram nulas, zero notificações materializadas.

Evidências visuais e árvore de acessibilidade: `tenderproof-ui-update-rollback-20260907.png/.txt`, `tenderproof-ui-create-20260907.png/.txt`, `tenderproof-ui-create-rollback-20260907.png/.txt`. A verificação SQL somente leitura está em `tenderproof-ui-validation.json`. O dia local é07/09; aplicação da criação ocorreu após00h UTC de08/09. Todos os dados são fixtures sintéticas, sem comprovação documental de fonte ao vivo.

A aba CUA e ambos os servidores próprios foram encerrados. As duas pastas temporárias criadas neste ensaio (`tenderproof-review-g9xffejn`, `tenderproof-review-ee4bp4po`) foram conferidas por origem/data e conteúdo fixture e removidas após preservar o relatório SQL; pastas anteriores não foram tocadas. Portas3000 e8011 sem listeners ao encerrar. Os PDFs/execução sintéticos preservados permanecem no armazenamento de evidências TenderProof de revisão.

Coleta e publicação em produção permanecem inalteradas. Não houve deploy, notificação real nem ativação de novas fontes pela interface.
