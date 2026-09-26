# Evidência T001 — status vivo do piloto

Data: 2026-09-12. Comando: `scripts/observador-pilot.ps1 -Action Status`.

Leitura executada com acesso Docker autorizado. Os seis serviços estão ativos: API (`127.0.0.1:18000`), web (`127.0.0.1:13000`), worker e scheduler; PostgreSQL e Redis aparecem `healthy`. API, PostgreSQL e Redis subiram há aproximadamente 16 minutos no instante da leitura; imagens locais `observador-product:local`.

## Resultado

| Serviço | Estado observado |
|---|---|
| api | Up, porta 18000 |
| web | Up, porta 13000 |
| worker | Up |
| scheduler | Up |
| postgres | Up (healthy) |
| redis | Up (healthy) |

A primeira tentativa no sandbox falhou por acesso negado ao pipe Docker; a mesma leitura foi repetida com a autorização de execução elevada exigida pelo ambiente e passou. Nenhum serviço foi reiniciado ou alterado por este diagnóstico.

Também foi consultado `GET http://127.0.0.1:18000/health`, com HTTP 200 e corpo `{"status":"ok","app":"Observador de Concursos","env":"local-pilot"}`. A consulta foi somente leitura.
