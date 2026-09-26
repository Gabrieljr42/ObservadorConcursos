# Revisão independente T012 — SHDias

**Veredito: `ACCEPT_FOR_ARTIFACT_STAGE` — não liberar importação.**

O pacote identifica de forma consistente `shdias_open`, source 51, `external_id=MTEw/MzA4`, `process_id=00308`, Hortolândia/SP e `Concurso Público 001/2026 - Guarda`. O detalhe preservado contém dois cargos (301 feminino, 12 vagas; 302 masculino, 28 vagas), total de 40 vagas, remuneração até R$ 3.971,37 e o edital de abertura referenciado:

`https://cdn-arquivo.concursos.srv.br/SHDIAS/00308/PUBLICACOES/01_Edital_Completo_2026_07_23_08_20_13.pdf`

O artefato local disponível é somente o HTML de detalhe:
`backend/tests/fixtures/tenderproof_batch60_blockers/shdias_open-cycle1-detail-e633962f88.html`, 31.265 bytes, SHA-256 `CC9E151C7CAE26D0C92BDE911C9D89F5B06706F3DF7EB4FB565FB2F892320D99`. Não há PDF local nem content receipt; `reference_only=true`, `canonical_concurso_id=null` e `apply=false` permanecem corretos. A checagem de duplicidade é apenas no catálogo/fixtures preservados, não autorização de publicação.

Teste executado no diretório `backend`:

`..\backend\.venv\Scripts\python.exe -m pytest -q ..\docs\execucao\evidencias\T012\shdias_open\test_proposal_fail_closed.py` → **3 passed**.

Próximo gate: preservar bytes do PDF, calcular SHA/byte length, alocar source/concurso pelo fluxo normal e só então revisão/importação normal. Sem rede, API, Docker ou mutação nesta revisão.
