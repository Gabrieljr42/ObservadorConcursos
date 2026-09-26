# IDs 23–25 — auditoria Luna bounded offline (2026-09-13)

Escopo limitado aos artefatos e fixtures já presentes no workspace. Não houve rede, Docker, nova pesquisa, escrita no banco, piloto ou edição de T010. A conferência usa [`IDs18-25-conferencia.md`](IDs18-25-conferencia.md), [`reviewed-runs-inputs.json`](reviewed-runs-inputs.json) e [`manifesto-propostas-offline.json`](manifesto-propostas-offline.json).

Os três `artifact.path` registrados nos reviewed inputs apontam para `/var/lib/observador/tenderproof/artifacts/...`, mas não há PDF correspondente em `docs/execucao/evidencias/T011/artifacts` nem fixture local com esses bytes. Assim, a identidade documental pode ser confirmada pelo registro preservado; a extração cargo-a-cargo não pode ser reexecutada nem promovida.

## ID 23 — FGV / Macaé-RJ

- **Identidade:** comprovável no trecho preservado da p.1: Prefeitura de Macaé/RJ, Edital 01/2026 de 27/03/2026, FGV; SHA-256 `6086daa5015ef0052e2cc3b35b81e5de7344d19312726f9594c9e44e4e98681a`.
- **Comprovável:** 191 vagas agregadas; prova objetiva para todos e títulos para nível superior (p.1).
- **Ausente:** nomes e linhas cargo-a-cargo, remuneração/unidade, requisitos, taxa, data e local detalhados da prova.
- **Classificação:** `SPECIFIC_BLOCKER` — o próprio reviewed input marca `cargos=unknown` porque só há total agregado; sem PDF local não há base para parser FGV nem envelope publicável.
- **Condição para avançar:** preservar o PDF exato ligado ao SHA acima (ou fixture byte-equivalente) e extrair/revalidar o quadro completo, sem converter 191 em cargos individuais.

## ID 24 — FCC / Câmara de Presidente Prudente-SP

- **Identidade:** comprovável nas p.1–4 preservadas: Câmara Municipal de Presidente Prudente/SP, Edital 01/2026, Fundação Carlos Chagas; SHA-256 `c9e43c7a9e5ed7b13bde0310a4c5dfc935febc3ce992024029ef72db9aced5c3`.
- **Comprovável:** carga mínima de 40h semanais (p.1); taxa de nível médio R$100; Assistente Legislativo de Contabilidade, 1 vaga, R$5.311,00; Técnico Legislativo, R$5.940,53; ambos com ensino médio (p.2–4).
- **Ambíguo:** taxa de nível superior R$150 está registrada sem associação a cargo; não associar taxa/salário fora das linhas explicitamente citadas.
- **Ausente:** demais linhas de cargos/vagas, associação taxa↔cargo, unidade temporal das remunerações, prova/data/local e cronograma.
- **Classificação:** `SPECIFIC_BLOCKER` — há campos parciais, mas não um quadro cargo-a-cargo reexecutável; sem PDF local não é seguro preparar reviewed-run.
- **Condição para avançar:** obter/preservar o PDF SHA-bound e transcrever o quadro completo, mantendo R$150 como não associado até prova literal.

## ID 25 — FACET / Floresta-PE

- **Identidade:** comprovável nas p.1–2 preservadas: Prefeitura de Floresta/PE, Edital 01/2026, FACET; SHA-256 `d049b7595f6ed8d7282d82580b0a0de67b24fa8fe2935f1764c3cd5970043221`.
- **Comprovável:** 432 vagas agregadas; exemplos nominais com quantidades (Auxiliar de Serviços Gerais 100, Cuidador 60, Professor I Fundamental 30, Professor I Infantil 25, Merendeira 15, Motorista D 16); inscrições 24/08–01/10/2026; início do quadro de requisitos/cargas/salários (p.1–3).
- **Ausente:** quadro completo, remuneração/unidade cargo-a-cargo, taxa, prova/data/local e demais requisitos.
- **Classificação:** `SPECIFIC_BLOCKER` — exemplos e total não substituem o quadro completo; sem PDF local não há parser FACET auditável.
- **Condição para avançar:** preservar o PDF exato ligado ao SHA acima e extrair o quadro integral; não promover os exemplos como lista completa nem inferir campos ausentes.

## Resultado

| ID | identidade | campos parciais | decisão |
|---:|---|---|---|
| 23 | comprovável | 191 vagas agregadas; etapas | `SPECIFIC_BLOCKER` |
| 24 | comprovável | duas linhas de cargo; taxas parcialmente não associadas | `SPECIFIC_BLOCKER` |
| 25 | comprovável | 432 vagas e exemplos; inscrições | `SPECIFIC_BLOCKER` |

Nenhum runner, envelope, import, proposta ou teste específico foi criado: a condição objetiva de suficiência — PDF/bytes locais reproduzíveis e quadro completo — não está satisfeita para nenhum dos três.
