# Evidência T001 — build e testes integrados

- Backend direcionado executado em container temporário com `pytest` instalado apenas nessa execução e `backend/tests` montado somente leitura: `test_publication_fallback.py`, `test_idempotency.py`, `test_crawl_resilience.py` — **13 passed**, 66 warnings, 4,90 s.
- Imagem backend reconstruída com `docker compose ... build api worker scheduler` — **api Built, scheduler Built, worker Built**.
- `api`, `worker` e `scheduler` recriados com a imagem nova e iniciados.
- Build web Expo concluído com 23 rotas em `mobile/dist-local-pilot`; serviço web reiniciado.
- Saúde pós-deploy: `GET http://127.0.0.1:18000/health` HTTP 200 (`status=ok`, `env=local-pilot`); `GET http://127.0.0.1:13000/inicio` HTTP 200 contendo o bundle web.
- Rotas T007 aparecem no OpenAPI vivo: proposta, aprovação e aplicação de `/tenderproof/publications/normalized-link`.
- A tentativa inicial sem `pytest` falhou por ausência do pacote na imagem; a execução isolada seguinte passou, sem alterar produção ou banco do piloto.
