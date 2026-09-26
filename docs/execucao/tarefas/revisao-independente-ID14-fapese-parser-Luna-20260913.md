# Revisão independente ID14 — FAPESE/PRONERA

Data: 2026-09-13. Read-only; sem deploy, importação, proposta, piloto ou rede.

## Decisão: ACEITA para deploy do código

O parser `backend/app/tenderproof/fapese_pronera_parser.py` está pinado para `source=fapese_selection`, `external_id=007/2026`, `concurso_id=14`, `source_id=76`, SHA `c713476b…71217b`, 345.974 bytes e 17 páginas. `preflight` valida SHA, bytes e páginas antes de extrair; a rota em `fields.py` só aciona o módulo para o par exato source/external. Artefato ausente, caminho ausente, drift, identidade ou evidência inválida retornam `FAILED`/não promovem fallback genérico. Caminhos relativos são resolvidos via `artifact_dir` pelo basename e continuam sujeitos ao SHA.

O modelo canônico representa corretamente prestação PF/cadastro reserva: dois papéis, `cadastro_reserva=true`, vagas imediatas/AC/PcD nulas, jornada nula, remuneração em unidade de serviço (R$60/h e limite R$7.488 por etapa) com observação explícita “não mensal”, sem sintetizar emprego, salário mensal ou quantidade de vagas. `funcao_observacao`, requisitos e evidências documentais são preservados.

Checks: `backend/.venv/Scripts/python.exe -m pytest -q` direcionado ID14 + T005 + ID8 + ID16: 6 passed; `compileall` PASS. A integração ID16 e T005/ID8 não regrediu nos testes executados. O artefato/evidência T010 confirma a mesma identidade, SHA e bytes; não houve mutação operacional.

Nota não bloqueante: `parse()` sem `page_texts` depende do sidecar relativo `docs/execucao/evidencias/T010/id14.txt`; a rota produtiva fornece páginas preservadas e o gate de artefato permanece fail-closed. Se o helper for chamado fora da raiz do workspace, usar caminho absoluto/configurado antes de produção.
