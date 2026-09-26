# Entrega das etapas 11–13

O piloto de dez fontes e o fluxo de publicação foram integrados. A expansão percorreu os portões 10→30→60→99 com aceite restrito às amostras comprovadas e exclusão explícita das fontes impedidas. **Não há99 fontes homologadas nem cobertura integral de qualquer portal.** O relatório estruturado adjacente e a matriz são a referência para contagens e evidências.

## Resultado por fonte

- Inventário completo: **99 entradas**, preservando IDs e categorias originais.
- **70 adaptadores registrados**:69 contratos implementados e1 implementação parcial (IDECAN).
- **61 fontes homologadas para escopo parcial**, com rotas/amostras e restrições individualizadas.
- **38 fontes sem homologação**:29 sem adaptador comprovado e9 com contrato, mas impedimento documental ou de acesso.
- As70 fontes registradas têm evidência de observação do adaptador, incluindo as provas herdadas do piloto. Sondagens das demais URLs são registradas separadamente e não contam como validação de adaptador.

A [matriz das99 fontes](tenderproof-rollout-matrix.md) e seu [JSON](tenderproof-rollout-matrix.json) identificam estado de implementação, offline, observação real, homologação, URLs, evidências, cobertura e próxima ação. Entre os impedimentos estão indisponibilidade/TLS/challenge, documentos não acessíveis ou retificados, portal com conteúdo incompatível e ausência de seleção de pessoas verificável no escopo investigado. Fontes de bolsas, fomento e ingresso em cursos não foram convertidas em concursos para completar contagens.

## Piloto e expansão

O piloto tem dez contratos aceitos no escopo delimitado. Os portões 30 e60 preservam as exclusões e decisões registradas antes da expansão seguinte. O lote final acrescentou 19 contratos:16 com dois ciclos reais válidos e3impedidos (Nosso Rumo, FEPESE e FAPESC). As outras20 entradas do lote final têm investigação e motivo específico, sem adaptadores vazios.

Para as16 novas fontes válidas, os ensaios demonstraram dois ciclos contínuos com uma observação deduplicada, interrupção real após persistência e retomada em outro processo sem download adicional. A fila foi medida em três grupos complementares, sempre com dois consumidores no mesmo host e três falhas controladas. No grupo principal,32 trabalhos escoaram até zero em55,6 s e61,4 s nas duas rodadas. Os grupos adicionais cobriram FATEC, Fundação Araucária e FAPESE; todos os processos terminaram. Essas medições não são uma previsão de capacidade de produção ou prova de armazenamento distribuído.

## Publicação e identidade

Observações verificadas seguem pelo fluxo existente de proposta, comparação, revisão, aplicação, versão e outbox. Novos concursos exigem identidade explícita e campos mínimos sustentados. Atualizações preservam valores desconhecidos/conflitantes, recusam revisão desatualizada e mantêm auditoria e rollback. Retificações detectadas abrem impedimento de revisão; seus efeitos não são aplicados silenciosamente.

No lote final, o PDF real Legatus permitiu criar um concurso no banco descartável. A repetição não criou outra versão ou outbox. Um ensaio separado atualizou uma baseline declaradamente sintética com o título sustentado pelo mesmo PDF, preservou datas/salários, recusou aprovação de data desconhecida e reverteu a mudança de modo idempotente. As15 outras fontes válidas passaram pela revisão canônica e foram impedidas por identidade/campos mínimos insuficientes; validade documental não foi confundida com elegibilidade de cadastro.

A identidade de seleções distintas numa página compartilhada ganhou índices parciais, proteção contra promoção concorrente de IDs legados e auditoria da alteração. A [migração é explícita](tenderproof-batch99-identity-migration.md), foi testada em SQLite/PostgreSQL e não foi executada em produção. Conflitos históricos interrompem a migração sem fusão ou exclusão silenciosa.

O POST público FAPEG preserva método/corpo no documento e no manifesto. A revisão oferece o PDF por rota autenticada existente e a página oficial; o endpoint POST não é apresentado como download GET. Foram testados proprietário correto, ausência de autenticação, outro usuário e artefato incorreto.

## Verificações

- Regressão integrada: **1.050 passaram**,32 opcionais ignorados e2 live excluídos;298,34 s. JUnit: `backend/.tenderproof/batch99-integrated-regression.xml`.
- PostgreSQL final: **89 passaram**, sem falhas/skips. Contêiner descartável removido e ausência confirmada. As suítes se sobrepõem; suas contagens não devem ser somadas como testes únicos.
- Focais posteriores de fundações/codificação, FAPESE, interface POST e TypeScript passaram; falhas intermediárias e suas correções permanecem documentadas.
- Backup e restauração de três volumes: bancos lógicos, referências e hashes dos PDFs preservados; nenhum original alterado ou excluído.16 PDFs únicos somam15.467.606 bytes; as32 cópias em artefatos e32 entradas de processamento somam61.870.424 bytes físicos.
- As provas Redis/Celery e de navegador herdadas estão datadas e separadas dos ensaios atuais no [relatório operacional](tenderproof-batch99-operations-review.json). Não houve nova sessão paga, teste de produção ou garantia de funcionamento distribuído via OneDrive.

## Produção e ações externas

Coleta e publicação em produção permanecem desativadas; nenhuma notificação real foi enviada. Uma futura ativação exige configurar deliberadamente fontes/operadores/limites, realizar backup e aplicar a migração no banco autorizado. Para fontes impedidas, a matriz especifica a necessidade de portal público funcional, original oficial acessível, identidade documental ou seleção de pessoas verificável. A implementação não contorna autenticação, TLS ou desafios de acesso.

Relatórios principais: [resultado estruturado](tenderproof-phases11-13-final.json), [portão final](tenderproof-batch99-gate-validation.json), [auditoria de documentos](tenderproof-batch99-current-validation.json), [publicação](tenderproof-batch99-publication-live.json), [revisão independente](tenderproof-batch99-final-review.json) e [interface validada em banco sintético](tenderproof-ui-validation.json).
