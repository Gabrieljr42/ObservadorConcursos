# Revisão independente — ID8 suplemento `prova_data`

Data: 2026-09-13. Read-only; nenhum piloto, deploy ou write executado.

## Decisão: ACEITA para importação e proposta somente

O suplemento `T010-reviewed-run-id8-prova-data-supplement.json` é um ReviewedRun novo e imutável: `run_id=tp-reviewed-ea4b278d48957c543fed74edd6b8222b`, envelope SHA `536e464cf6f5d05ccae963086b689e306f5e1e3ef07763c10b41c5869c9b5375`, owner 1, `reference_only=true`, `pending_fields=[]`. O PDF é o mesmo `id8.pdf`, SHA `fef17aa38c078810cbfedfa999782c3d02318bd9e5fa764502b5c4bb116ab28a`, 1.048.994 bytes.

Há exatamente um campo top-level: `prova_data=2026-12-06`, `original_value=06/12/2026`, com evidência literal da p.68: `15 Realização das Provas Objetivas 06/12/2026`. A validação independente confirma hash/bytes, texto literal, modelo ReviewedRun/importer dry-run e receipt com `_revalidate`/`create_proposal` isolados: único `eligible_field=prova_data`, estado `proposed`, banco SQLite descartável. Campos `cargos` e demais identidade/inscrições permanecem bloqueados.

Baseline correto: versão publicada 87 permanece intacta; o reparo não deve reaplicar cargos. Liberar uma única importação e criação de proposta normal contra baseline 87. Approve/apply ficam fora deste aceite e exigem gate posterior específico, com CAS de estado/hash/baseline e revisão pós-apply.

Checks locais: `pytest` reviewed-run/import + exam-date: 12 passed. Nenhuma rede foi usada.
