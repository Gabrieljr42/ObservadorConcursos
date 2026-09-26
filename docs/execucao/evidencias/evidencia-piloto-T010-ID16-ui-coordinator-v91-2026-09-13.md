# Evidência complementar — T010 / ID16 — UI pós-apply v91

- **Data de registro:** 2026-09-13
- **Classificação:** `ACEITA_COMPLEMENTAR_COORDINATOR_CUA`
- **Atribuição:** `coordinator_cua_observation`
- **Rota:** `http://localhost:13000/concurso/16`
- **Contexto:** dois snapshots UI (antes/depois reload) idênticos.
- **Independência:** não independente; não houve operação própria nesta revisão.
- **Screenshot:** não alegado.

## Estado observado

Título: **Concurso Público - 002/2024 - Prefeitura Municipal de Osvaldo Cruz-SP**. A tela exibiu exatamente 18 cards: **Bibliotecário, Chefe de Controle Interno, Cirurgião Dentista, Contador, Coveiro, Cozinheiro, Dentista, Encanador, Engenheiro de Segurança do Trabalho, Farmacêutico Bioquímico, Fonoaudiólogo, Médico Clínico Geral, Médico Geriatra, Médio Ginecologista, Médico do Trabalho, Médico Pediatra, Padeiro, Tratorista**.

Dez cards mostram **1 vaga imediata + AC 1**; oito mostram **0 + cadastro reserva**. Todos exibem remuneração, jornada, requisitos e taxa. A prova é **12/01/2025**; inscrições: **27/11/2024–29/12/2024**. O histórico de 13/09/2026 informa cargos e prova de **“Não informado” para valor/data**. Não houve `null`, `undefined` ou `NaN`; página oficial/link de edital presentes.

## Reconciliação API/apply

Vinculado ao gate API pós-apply: versão **91**, outbox **91**, notificação **90**, proposta **tpp-1a0fc40cc8df713e6958de0f43efc032**. O número v91 não foi alegado como texto visível na UI.

Referência: [`gate-ID16-pos-apply-20260913.json`](T010/gate-ID16-pos-apply-20260913.json).
