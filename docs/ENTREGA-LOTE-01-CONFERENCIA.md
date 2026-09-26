# Entrega lote 01 — conferência automatizada independente

**Atualização posterior à conferência:** os sete candidatos foram autorizados, revalidados, publicados e conferidos no aplicativo, nos concursos 4 a 10. O texto abaixo registra o estado de preparação, anterior à aplicação. Consulte `ENTREGA-2026-09-09.md` para o fechamento e suas limitações.

Data da conferência: 2026-09-09. Escopo: sete runs selecionados pelo shortlist preservado em `backend/scripts/delivery_shortlist.py`, consultados em modo somente leitura no banco operacional do serviço API.

Esta conferência confirma coerência interna entre os campos extraídos e os trechos do PDF original. Ela não é aprovação humana, não prova integração de toda a fonte e não prova publicação no catálogo/aplicativo. Os runs trazem `execution_status=completed`, `validation_status=valid`, todas as páginas processadas e comparação sem baseline (`catálogo não alterado`). O `sample_note` de cada run declara coleta limitada ao ciclo e observação para revisão, sem publicação.

## Resultado por candidato

| Fonte / candidato | Run / PDF | Identidade conferida | Datas conferidas | Cobertura e pendências objetivas |
|---|---|---|---|---|
| JCM Carmo da Cachoeira 268 | `tp-tcj-e57a86e6e2ff5da5868acf49a60ac403-4`; 22 páginas; SHA-256 `81a021874d8e426e69ad4018ca468513f5918c4bbfdac648e236465a08fdb4e8` | **Carmo da Cachoeira-MG — Processo Seletivo Público 001/2026 — Prefeitura Municipal**; órgão Prefeitura Municipal de Carmo da Cachoeira; edital 001/2026. Título/órgão p.1; edital p.7. | Inscrições 17/11/2026–17/12/2026 p.22; prova 17/01/2027 p.22. | Coerente. `cargos` falhou e remuneração ficou sem evidência; não publicar esses campos. Não há prova de retificações/escopo completo.
| Instituto Consulplan Unaí | `tp-tcj-706b5bc7f1f75e5cb0c3c05c48bce934-3`; 31 páginas; SHA-256 `9bdb0e77fde501c33363ce636744b8be8107c64a996c1bde6b4aa2faa96dac32` | **Câmara Municipal de Unaí/MG — VIII Concurso Público**; órgão Câmara Municipal de Unaí; edital 1/2026. Tudo p.1, com `EDITAL Nº 1, DE 26 DE AGOSTO DE 2026`. | Inscrições 30/10/2026–01/12/2026 p.31. | Coerente. Prova, cargos e remuneração sem evidência. O título do PDF é “Edital nº 1/2026 - Abertura”; nenhum documento suplementar foi selecionado.
| IMESO Berizal 139 | `tp-tcj-377fa72c32a2587eb20c8e068572a18b-1`; 29 páginas; SHA-256 `8e6fbc48ac7f54c492cc2beba78adc9216ba25fa781ba753d3e9e410fc7dd6dc` | **Processo Seletivo Público — 001/2026 Prefeitura Municipal de Berizal/MG**; órgão Prefeitura Municipal de Berizal; edital 001/2026. Tudo p.1. | Inscrições 13/10/2026–13/11/2026 p.2. | Coerente. Prova, cargos e remuneração sem evidência. O PDF escolhido é “EDITAL.”; não há prova de anexos, retificações ou cobertura de outros documentos.
| ABCP Garça 2868 | `tp-tcj-b7b17f29eeac52a9a43f71c360753e43-1`; 19 páginas; SHA-256 `00dc6e0d8e560b8b0a5aae557016d7e6a169b1ebc00aeb31d7ff95babf497b2a` | **Concurso Público — 001/2026 — Câmara Municipal de Garça-SP**; órgão Câmara Municipal de Garça; edital 001/2026. Tudo p.1. | Inscrições 04/09/2026–07/10/2026 p.2. | Coerente. Prova, cargos e remuneração sem evidência. O título observado inclui “CÂMARA MUNICIPAL DE GARÇA- SP”; normalização para Garça está consistente.
| IDIB Reriutaba 362 | `tp-tcj-b6372819d87e51c185e6427865a5bf62-1`; 75 páginas; SHA-256 `fef17aa38c078810cbfedfa999782c3d02318bd9e5fa764502b5c4bb116ab28a` | **Concurso Público Prefeitura Municipal de Reriutaba/CE — Edital nº 01/2026, de 02 de setembro de 2026**; órgão Prefeitura Municipal de Reriutaba; edital 01/2026. Tudo p.1. | Inscrições 02/09/2026–05/10/2026 p.5. | Coerente. Prova e remuneração sem evidência. Não há prova de retificações nem de que 75 páginas representem todos os documentos da seleção.
| Cebraspe Ponta Porã | `tp-tcj-2b58bacc0b6a5a028ffc292908b9b6da-1`; 62 páginas; SHA-256 `d09cd7a25a66696b4f30b718ee5a0acc3867b6f1892ec1f5c33c3efca6b2dd49` | PDF identifica **Câmara Municipal de Ponta Porã/MS**; órgão Câmara Municipal de Ponta Porã; edital 1/2026. Identidade p.1; edital p.1. | Inscrições 21/08–10/09/2026 p.59 (ano final explicitado no trecho como 2026). | Coerente. Remuneração foi extraída em p.3 para cargos distintos (R$ 7.999,59 e R$ 3.919,59), com escopo por cargo; não tratar como mínimo/máximo global nem como vagas. Prova e cargos sem evidência.
| FEPESE Caxambu do Sul 004/2026 | `tp-tcj-8c4428c810c45812a92132a23bf42958-1`; 44 páginas; SHA-256 `a23c6ecd25f7a80d1bf6ed790673082f21bf45936ef64e1573856448be08dc11` | **2026 — Prefeitura Municipal de Caxambu do Sul**; órgão Município de Caxambu do Sul; edital 004/2026. Identidade/edital p.1. | Inscrições 02/02/2026–04/03/2026 p.1. | Coerente. É processo seletivo para contratação temporária; não converter em concurso efetivo. Prova, cargos e remuneração sem evidência. Nenhum documento suplementar foi selecionado.

## Erros óbvios e decisões de tratamento

- Não encontrei contradição textual óbvia entre título, órgão e número do edital nos sete PDFs. A normalização de caixa, acentos e separadores não muda a identidade.
- As datas foram mantidas como campos de inscrição; não foram interpretadas como data de publicação, validade, prova ou nomeação.
- O único campo de remuneração suportado nesta seleção é o do Cebraspe. Ele contém valores por cargo e deve permanecer com o escopo contextual registrado. Valores de remuneração não foram usados para inferir quantidade de vagas.
- A coleta escolheu um documento principal por candidato. A ausência de evidência de retificação, convocação, anexos ou outros tipos documentais é uma lacuna de cobertura, não evidência de inexistência desses documentos.

## Status de entrega

Os sete candidatos têm coleta e extração automatizada válidas, com SHA-256, páginas e trechos de evidência reproduzíveis no payload do run. Eles estão aptos a uma revisão humana dirigida dos campos listados. Nenhum deve ser contado aqui como fonte concluída ou como conteúdo já disponível no aplicativo: o run registra explicitamente catálogo não alterado e sem publicação.

Pendências para fechar o lote no produto: revisão/aprovação humana; tratamento e conferência de retificações e demais documentos por candidato; publicação autorizada; sincronização; verificação visual no aplicativo; e repetição de ciclo/recovery conforme a fonte. Também falta decidir, na revisão humana, se os campos ausentes devem permanecer ausentes ou receber processamento adicional.

Fonte dos dados desta nota: payloads dos sete run IDs no `operational.sqlite3` do container `observador-pilot-api-1`, consultados em modo leitura em 2026-09-09; shortlist em `backend/scripts/delivery_shortlist.py`. Nenhum arquivo de coleta foi rebaixado, sobrescrito ou removido.
