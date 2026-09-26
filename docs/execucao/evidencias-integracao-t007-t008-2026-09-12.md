# Evidência — integração operacional T007/T008 (2026-09-12)

Momento da consolidação: 2026-09-12 18:19 -03:00. Operador único: Luna integrador (T001). T010/T011 não foram publicados.

## Gates e proteção

- Runtime `backend/.venv/Scripts/python.exe`, Python 3.12.0, pytest 9.1.1.
- Suíte direcionada: `test_publication_fallback.py` + `test_tenderproof_publication_post.py`: **16 passed**; PostgreSQL descartável `postgres:17-alpine`: **15 passed**, conforme recibo fresco em `evidencias-t007-atomicidade-correcao-2026-09-12.md`.
- Backup pré-mutação: `/backups/pilot-20260912T211029155Z-operational`; manifesto/verificação: **11.425 arquivos**. Restauração isolada `/backups/t007-restore-20260912T211029155Z`: **11.425 arquivos**.

## Deploy e aplicação

- Web exportado com 23 rotas; API/worker/scheduler reconstruídos e recriados somente no projeto `observador-pilot`.
- Health após aquecimento: HTTP 200, `status=ok`; PostgreSQL/Redis healthy.
- Proposta normal T007: `tpr-2abf0ea8e7646be2a47aed6318c682f2`, hash `2abf0ea8e7646be2a47aed6318c682f25cd252f2c813ae6a1847d71d6aa37d1d`; 32/32 elegíveis; aprovação e aplicação normais; `state=applied`, `skipped=[]`, `reference_only=true` no recibo, versões 50–81.

## Validação e riscos

- `delivery_verify_api.py`: login/refresh/checkpoint HTTP 200; 33 seleções, 32 fontes, 112 cargos, 34 publicações, 81 versões, 48 notificações; ações preservadas e notificações únicas.
- Rota `/concursos/{id}/publications`: 34 linhas, 30 fallback, IDs 3 e 32 com duas linhas.
- Risco aberto: `GET /tenderproof/publications/proposals/{id}` retorna 500 (`KeyError: 'run'`); linhas fallback existentes não expõem `provenance.reference_only=true` na leitura, embora o apply registre `reference_only=true`. T007 permanece em revisão até corrigir/explicar esses pontos sem SQL ad hoc.
