# T004 — inventário bounded de lacunas de adaptadores — 13/09/2026

Auditoria somente local, sem rede, Docker, piloto ou implementação. Foram comparadas as 99 configurações da matriz candidata com `backend/app/tenderproof/connectors/registry.py`, `source_adapters.py`, `fields.py`, módulos `*_adapter.py`/`*_jobs.py` e fixtures preservadas.

Resultado agregado: 71 configurações marcadas `implemented`, 20 `partial`, 8 `pending`; 8 têm `adapter_current=null` histórico na matriz de fontes (`matrix_source_number`: #3 AOCP, #8 SEPROD, #23 UniFil, #25 Leandro Ferreira, #28 IUDS, #41 IDGRAN, #61 Oppus e #90 FAPEMAT). A revisão runtime independente confirmou factory/classe instanciável para todas: AOCP usa `AOCPConnector`; as demais usam `ConfigurableHTMLConnector`, exceto FAPEMAT com `InstitutionalSelectionConnector`. Portanto, zero lacunas comprovadas de factory/instanciação. Isso é namespace de fonte, não ID de concurso; `implementation_state`/integração permanecem não certificados.

## Lote já aberto e casos prioritários

| Nº/fonte | Estado técnico | Lacuna precisa | Evidência local | Owner/prioridade |
|---|---|---|---|---|
| concurso 5 `institutoconsulplan_open` (matrix source #38) | adapter/runner não identificado na distribuição | campos de cargo ausentes no API; não confundir com source #5 `ibam_open` | índice/distribuição; bytes a localizar | T004-content / P1 |
| concurso 18 `quadrix_open` (matrix source #42) | adapter/runner não identificado na distribuição | campos de cargo ausentes no API; não confundir com source #18 `omni_open` | índice/distribuição; bytes a localizar | T004-content / P1 |
| concurso 20 `legatus_open` (matrix source #62) | adapter/runner não identificado na distribuição | campos de cargo ausentes no API | índice/distribuição; bytes a localizar | T004-content / P1 |
| concurso 22 `funcern_selection` (matrix source #64) | adapter/runner não identificado na distribuição | campos de cargo ausentes no API | índice/distribuição; bytes a localizar | T004-content / P1 |
| concurso 23 `fgv_open` (matrix source #10) | adapter/runner não identificado na distribuição | campos de cargo ausentes no API | índice/distribuição; bytes a localizar | T004-content / P1 |
| concurso 24 `fcc_open` (matrix source #9) | adapter/runner não identificado na distribuição | campos de cargo ausentes no API | índice/distribuição; bytes a localizar | T004-content / P1 |
| concurso 25 `facet_open` (matrix source #31) | adapter/runner não identificado na distribuição | campos de cargo ausentes no API | índice/distribuição; bytes a localizar | T004-content / P1 |
| concurso 33 `legalle_open` / Garibaldi (matrix source #49) | `EditalVerAdapter`, implementado | cargo desconhecido e três retificações com efeitos ainda não compostos | `docs/T004-LOTE-GARIBALDI-20260912.json` + fixtures Legalle | T004-conteudo / P0 |

O concurso 32 `elo_open`/Barra Longa (matrix source #47) está fechado em T005 e não é uma lacuna restante: parser pinado, sete microáreas, sete vagas e evidência documental aceitos.

## Distinções de aceite

- “Adapter ausente” não é mais uma conclusão válida apenas por `adapter_current=null`; o runtime/factory deve ser consultado. Nesta revisão, zero ausências de factory/instanciação foram comprovadas.
- As lacunas reais remanescentes são classificadas como aquisição, identidade, escopo, homologação, detalhe ou runner/documento de conteúdo quando há fixture suficiente; não são convertidas automaticamente em implementação completa.
- `matrix_source_number` nunca é `concurso_id`: por exemplo, matrix source #5 é `ibam_open`, enquanto concurso ID 5 é `institutoconsulplan_open`; concurso ID 18 é `quadrix_open`, enquanto matrix source #18 é `omni_open`.
- “Runner de conteúdo ausente” significa adapter registrado, mas nenhum parser/branch específico capaz de extrair os campos do caso focal; isso não invalida o adapter HTML.
- “Documento insuficiente/conflitante” significa que há adapter e, às vezes, fixture, mas a evidência não permite decidir identidade, retificação ou cargo sem autoridade/revisão.

Os 91 demais registros têm adapter/configuração presente ou estado parcial; não foram rotulados como ausentes sem prova específica. O inventário é uma triagem bounded para revisão independente, não autorização para novo lote ou publicação.
