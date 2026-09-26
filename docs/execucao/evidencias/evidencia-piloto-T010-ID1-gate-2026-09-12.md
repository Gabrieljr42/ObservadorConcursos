# Evidência de piloto T010/ID1 — gate pós-apply

Decisão: **ACEITA_ID1_GATE** (somente este registro/gate; a falha histórica de 14 rotas permanece na matriz).

## API/checkpoint somente leitura

Login, detalhe, versões e checkpoint retornaram HTTP 200. A proposta `tpp-32d777ecadaaad5a790f95d7d4dd0e05` está `applied`, ação `update`, com `approved_fields=[cargos]` e versão 82. Detalhe e checkpoint coincidem: Professor Auxiliar; 10 vagas imediatas (AC 9, PcD 1); remuneração `30.53 BRL`, observação `por hora-aula`; jornada até 40 horas semanais; requisito completo de Licenciatura Plena em Pedagogia ou Normal Superior com habilitação na Educação Infantil e anos iniciais. Cadastro reserva permanece nulo/não confirmado.

A versão 82 é `updated`, tem `changed_fields=[cargos]`, resumo “Vagas, remuneração, jornada e requisitos por cargo foram atualizados.” e referencia a proposta. Há exatamente **uma alteração material** para este gate.

## UI observada

Em `http://localhost:13000/concurso/1`, a captura do coordenador confirmou título Prefeitura Municipal de Birigui/SP, `CARGO Professor Auxiliar`, seção `Cargos e requisitos`, 10/9/1 vagas, R$ 30,53 por hora-aula, jornada, requisito completo, histórico e diff `Cargos e condições Não informado → Valor estruturado atualizado`.

Artefato estruturado: `evidencia-piloto-T010-ID1-gate-2026-09-12.json`.
