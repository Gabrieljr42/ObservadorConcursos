# Fechamento independente T011 — Luna — 2026-09-12

Classificação read-only dos inputs revisados, sem dispatch, POST, banco ou mutação piloto:

| ID | Estado | Identidade/proveniência | Caminho | Próximo passo |
|---:|---|---|---|---|
| 17 | READY_FOR_PARSER | Cubati/PB; SHA `6caf7901…f7e1f`; `validation_status=valid`, 27 cargos/79 vagas | `/var/lib/observador/tenderproof/artifacts/art-06e60acb05-6caf7901eb5e7a803488d98fa2744167d4de52924784e384857dfe31235f7e1f.pdf`; `T011/reviewed-runs-inputs.json` | Rodar parser/reviewed-run; manter `reference_only` até proposta autorizada |
| 18 | INSUFFICIENT_EVIDENCE | Cristalina/GO; SHA `5f245894…f0ab`; input parcial, cargos desconhecidos | `/var/lib/observador/tenderproof/artifacts/art-d12f25c6ad-5f245894ba03dca5352a79fc991880b95e3fcf907fa38a1218ed2c4a373f0ab3.pdf`; `T011/IDs18-25-conferencia.md` | Transcrever quadro cargo-a-cargo, remuneração associada, taxa e prova |
| 20 | INSUFFICIENT_EVIDENCE | Domingos Mourão/PI; SHA `774a05bb…8ed7ce`; só exemplos/quadro parcial | `/var/lib/observador/tenderproof/artifacts/art-674e6a26bb-774a05bbd92b0505628a8c18f1d272b4297118b4dc1c63ecd4c8c334fe8ed7ce.pdf` | Extrair quadro completo, taxa e unidade remuneratória |
| 22 | INSUFFICIENT_EVIDENCE | Lagoa de Pedras/RN; SHA `8e296b419…1cdcca`; Anexo I não transcrito | `/var/lib/observador/tenderproof/artifacts/art-973e5a960d-8e296b419b83ff91630ca85822b9fb7e6398c379c4e5db4d8e7b0759cf1cdcca.pdf` | Extrair Anexo I, requisitos, taxa e cronograma |
| 23 | INSUFFICIENT_EVIDENCE | Macaé/RJ; SHA `6086daa5…e98681a`; 191 vagas agregadas | `/var/lib/observador/tenderproof/artifacts/art-4a3913b548-6086daa5015ef0052e2cc3b35b81e5de7344d19312726f9594c9e44e4e98681a.pdf` | Extrair cargos, remuneração, requisitos, taxa e prova |
| 24 | INSUFFICIENT_EVIDENCE | Presidente Prudente/SP; SHA `c9e43c7a…aced5c`; poucos cargos/taxa sem associação completa | `/var/lib/observador/tenderproof/artifacts/art-378e5c9cd5-c9e43c7a9e5ed7b13bde0310a4c5dfc935febc3ce992024029ef72db9aced5c3.pdf` | Completar quadro, associação de taxa, prova e unidade temporal |
| 25 | INSUFFICIENT_EVIDENCE | Floresta/PE; SHA `d049b759…0043221`; 432 vagas agregadas/quadro inicial | `/var/lib/observador/tenderproof/artifacts/art-42a610198e-d049b7595f6ed8d7282d82580b0a0de67b24fa8fe2935f1764c3cd5970043221.pdf` | Completar quadro, taxa, prova/local e unidade temporal |
| 21 | DO_NOT_RETRY | Cajueiro/AL; SHA `2a074dea…e8241`; `document_review.pending=true`, quatro retificações; 409 sem proposal | `T011/diagnostico-id21-409-20260912.json` | Conferir retificações, revalidar identidade/revisão e só então novo run/proposta |

Os arquivos `T011/reviewed-runs-inputs.json`, `pacotes-proposta-revisao.json` e `diagnostico-campos-cargo-20260912.json` são parciais para 18, 20, 22–25: preservam lacunas e não promovem campos documentais à API. Não há autorização de aplicação.
