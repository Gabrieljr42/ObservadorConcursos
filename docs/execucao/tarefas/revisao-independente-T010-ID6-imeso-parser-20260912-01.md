# Revisão independente T010/ID6 — IMESO Berizal

Status: DEVOLVIDA.

Passaram `tests/test_imeso_berizal_jobs.py` (3/3) e a regressão direcionada publication/reviewed-run (sem falhas observadas). O PDF local tem SHA `8e6f…dd6dc`, 597314 bytes e 29 páginas; a extração usa a página física 22, produz 11 linhas individuais, 1 imediata + CR, AC 1/PcD 0, R$3242/mês, 40h, requisito/taxa R$120, sem prova/data inventada. O wiring `fields.py` é exclusivo para `imeso_open`/`139`; drift, SHA, erro/truncamento e estrutura falham fechado; evidências são 11 snippets verbatim da página 22. O teste de integração cobre `extract_fields → _revalidate → create_proposal` sem apply.

Achado P1: a exclusividade pedida inclui bytes, mas o parser valida somente `(source, external_id, artifact.sha256)`. Reproduzi com o PDF correto e `Artifact.byte_len=0`: retornou `supported`, embora o contrato do artefato declare bytes incorretos. Adicionar `EXPECTED_BYTE_LEN=597314`, validar `artifact.byte_len`, e testar esse drift; manter SHA como pin de conteúdo. Depois repetir a suíte e o gate de proposta.
