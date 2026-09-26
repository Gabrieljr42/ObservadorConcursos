# Evidência — redeploy T007 r2 + T008 r3 (2026-09-12)

Momento: 2026-09-12 18:37 -03:00. Operador serializado: Luna integrador (T001). T010/T011 não publicados.

- Gates prévios: backend T007 r2 **18/18**; `npx tsc --noEmit` PASS; testes mobile T008 r3 **9/9**.
- Bundle web exportado com 23 rotas; API/worker/scheduler reconstruídos e recriados. Web serviu `/inicio` HTTP 200 (17.927 bytes). API `/health` HTTP 200 (`status=ok`). PostgreSQL/Redis healthy; volumes preservados.
- GET autenticado `/tenderproof/publications/proposals/tpr-2abf0ea8e7646be2a47aed6318c682f2`: HTTP 200, `state=applied`.
- Rotas de publicações: 34 linhas em 32 concursos; 30 fallbacks; 30 expostas como `reference_only=true` pelo contrato/API; IDs 3 e 32 têm duas linhas.
- Checkpoint/API: 33 seleções, 32 fontes, 112 cargos, 34 publicações, 81 versões, 80 notificações; checkpoint repetido preservou ações e notificações únicas.
- Diagnóstico SQL somente leitura: 32 versões associadas à proposta, 32 outbox distintos, 32 concursos distintos, duplicatas de versão **0**.
- T008 fica pronto para nova corrida real offline→sync/UI; nenhuma publicação T010/T011 ocorreu.
