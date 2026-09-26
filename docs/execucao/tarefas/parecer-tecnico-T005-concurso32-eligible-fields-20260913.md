# Parecer técnico T005/concurso 32 — divergência `eligible_fields=[]`

Data: 2026-09-13. Diagnóstico independente, read-only; sem serviço, piloto ou mutação.

A proposta `tpp-f1a450209aec0ad7af09922440daf557` está corretamente `proposed`, mas o gate registra `eligible_fields=[]` e `MISMATCH_REVIEW_REQUIRED`. O envelope/import preserva o mesmo artefato (`a5a7ff…ef5a2`, 429261 bytes), sete cargos e run `tp-reviewed-9b6433a0…`; portanto não há divergência semântica mínima entre envelope e parser offline.

A divergência está na integração: `fields.py` chama o parser Barra Longa lendo `Path(artifact.storage_path).read_bytes()`. O teste unitário fornece `storage_path` absoluto e passa; o importador aceita `content_path`, mas `commit_run_artifact` materializa no ledger apenas o nome relativo `art-07b137af65-a5a7…pdf`. Assim, no `_revalidate` deployado o parser não encontra o arquivo no CWD, retorna `FAILED`, e `cargos` é bloqueado como não reproduzido. O `store.load_artifact_bytes` já consegue ler os bytes, mas esse conteúdo não chega ao parser.

**Reparo aceitável:** fazer a rota integrada fornecer ao parser os bytes já carregados (ou resolver `storage_path` pelo `artifact_dir()` antes de `extract_fields`), mantendo SHA/byte_len e fail-closed; depois repetir somente `_revalidate → create_proposal` e registrar receipt. Não copiar/alterar envelope, relaxar hash ou aplicar a proposta. Até esse receipt, T005 fica DEVOLVIDO para proposta.
