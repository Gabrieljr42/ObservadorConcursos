# Identidade de concursos em páginas compartilhadas

A revisão do lote99 reproduziu uma falha real: duas seleções FATEC ou FAPPR possuem números distintos e a mesma URL pública, mas a restrição antiga `UNIQUE(source_id, link_pagina)` impedia inserir a segunda seleção. O resolvedor canônico já exigia também o identificador externo; o impedimento estava na persistência.

A revisão `concurso-section-identity-001` substitui essa restrição por dois índices únicos parciais:

- `uq_concursos_source_external_known`: `(source_id, external_id)` quando o identificador não é NULL nem vazio após remoção do conjunto explícito de whitespace Unicode, compartilhado com a aplicação.
- `uq_concursos_source_link_legacy`: `(source_id, link_pagina)` quando o identificador é NULL ou vazio após remoção do conjunto explícito de whitespace Unicode, compartilhado com a aplicação.

Assim, IDs explícitos distintos podem compartilhar a mesma página. Observações legadas sem ID continuam limitadas a uma por fonte e URL. Um registro legado sem ID pode coexistir com registros identificados na mesma página; a seleção apenas por URL é recusada quando houver mais de um candidato. O coletor tradicional também recusa a fusão por URL de IDs explícitos diferentes e não apaga um ID existente quando uma observação posterior omite esse campo. As chaves de associação canônica e seus históricos de reversão permanecem intactos.

## Upgrade explícito

Antes de implantar contratos de páginas compartilhadas em um volume existente, configurar a conexão do banco autorizado e executar, a partir de `backend`:

```powershell
.venv/Scripts/python.exe -m app.concurso_identity_migration --apply
```

Não há chamada automática dessa migração no boot. `create_all` sozinho não remove a restrição antiga. A execução foi validada somente em SQLite temporário e PostgreSQL16 descartável; nenhum banco de produção foi migrado.

O upgrade verifica previamente duplicações de `(source_id, external_id)` e duplicações legadas sem ID. Encontrando conflitos, aborta sem reconciliar ou excluir registros. Esses conflitos exigem revisão explícita. PostgreSQL usa transação e bloqueio exclusivo da tabela durante a troca de índices. SQLite usa `BEGIN IMMEDIATE` e reconstrução transacional quando existe a restrição antiga, preservando valores, IDs, índices auxiliares, gatilhos e referências; executa `foreign_key_check` antes de confirmar. Há breve bloqueio de escrita: programar a operação com os coletores pausados e backup verificado.

## Downgrade seguro

```powershell
.venv/Scripts/python.exe -m app.concurso_identity_migration --apply --downgrade
```

O downgrade recusa qualquer duplicação de `(source_id, link_pagina)`, inclusive as novas seleções válidas que compartilham uma URL. Não apaga uma das seleções, não inventa fragmentos e não remove históricos para satisfazer a restrição antiga. Se já existirem páginas compartilhadas, conservar a nova revisão até uma estratégia explícita de compatibilidade ser aprovada. Quando não existem conflitos, reinstala a proteção antiga antes de remover os novos índices; operações repetidas são idempotentes.

## Evidências e limites

- SQLite: 82 testes passaram e sete casos PostgreSQL foram ignorados por falta de configuração nessa execução; cobrem migração, coletores, publicação, aliases concorrentes e reversão. Posteriormente, os 31 testes finais das fundações passaram, incluindo publicação completa de duas seleções na mesma URL.
- PostgreSQL16: 69 testes passaram em schemas privados; dois testes adicionais passaram com PDFs sintéticos revalidados pelo processamento isolado, criação de dois concursos distintos, repetição idempotente de aplicação e reversão sem apagar vínculos ou concursos.
- Um teste adicional de coleta sem ID confirmou atualização seguida de repetição sem versão nova, preservando o identificador revisado, em SQLite.
- Os PDFs da prova de publicação de seções são explicitamente sintéticos. A prova não substitui os dois ciclos HTTP reais exigidos por contrato.
- Os containers próprios usaram apenas tmpfs, sem volumes de dados do usuário; foram removidos e sua ausência foi verificada. Logs e resultados: `tenderproof-batch99-identity-postgres.json` e `tenderproof-batch99-identity-publication-postgres.json`.

## Correção após revisão independente

A promoção de um concurso legado sem identificador usa comparação condicional do valor carregado (`UPDATE WHERE id AND external_id original`) antes de escrever publicações ou versões. O bloqueio de escrita permanece até o término da transação. Se outro coletor ganhou a promoção, o perdedor aborta e deve repetir a resolução em nova transação; não sobrescreve o ID vencedor. A nova resolução permite inserir o segundo edital como outro concurso na mesma URL. A promoção registra old/new do identificador na versão, inclusive quando nenhum campo documental mudou. O guard preserva updated_at se não houver mudança efetiva.

O conjunto de whitespace é explícito em `app/concurso_identity.py`: inclui tabs, CR/LF e espaços Unicode usados por Python. IDs não vazios permanecem opacos, sem strip, lowercase ou reescrita. Os índices SQLite usam trim com esse conjunto, PostgreSQL usa btrim com o mesmo conjunto; o preflight compartilha esses predicados. Reexecutar o upgrade explícito substitui índices da primeira versão. Se um volume anterior contiver NULL e tab-only duplicados para a mesma fonte/URL, o preflight recusa a troca e preserva as linhas; não há reconciliação silenciosa.

As provas concorrentes usam duas sessões/threads que observam o mesmo registro legado antes de uma barreira. Exigem um vencedor e um abortado, preservam o ID vencedor e comprovam que uma nova resolução do perdedor cria o segundo registro. Esses ensaios são limitados a dois escritores e não equivalem a benchmark de produção.
