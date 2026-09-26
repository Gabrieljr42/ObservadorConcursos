# Revisão independente Luna — matriz de fontes r4 R2

**Veredito: ACCEPT_MATRIX_R4**

Revisão somente leitura; não alterei matriz, baselines, piloto ou documentos centrais.

- SHA-256 verificados: CSV `316e806f1cfd799d44f16f5bed7609bb08296c59831ae6ffb1239938b09bcad2`; JSON `9049ef1bd8d0cf6cec2c7cc42de16d89a6df057afcbca760aeddda5d260c33ea`.
- CSV/JSON têm 99 linhas equivalentes por `numero`, `fonte`, overlay, estado, versão e ponteiro. Há exatamente 99 IDs e 99 fontes únicas; todos os ponteiros (99 de linha e overlays) resolvem para arquivos existentes. O mapeamento `numero/fonte` coincide integralmente com `docs/entrega-fontes-atual.csv` (99 linhas).
- Snapshot confere: 33 concursos, 32 fontes de catálogo, 180 cargos (regra null→0), 34 publications, 91 versions, 91 outbox, 90 notifications, 95 proposals e push 0/0/0. As colunas históricas da r3 são preservadas no CSV (r4 acrescenta apenas `evidence_pointer`); enums históricos permanecem idênticos.
- Overlays conferidos: fonte19→1/v82, 17→6/v83, 22→7/v84, 34→17/v86, 45→8/v87 cargo + v88 prova, 47→32/v89, 76→14/v90, 18→16/v91.
- Preservações corretas: insuficientes 5,18,20,22–25; mismatch concurso15/fonte6; concurso21 `DO_NOT_RETRY`; bdb86 `NEVER_APPROVE_NEVER_APPLY`. `authoritative=false` e nenhum estado promove integração source-wide.

Liberado apontar os documentos centrais para a matriz r4 R2.
