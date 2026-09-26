# Snapshot API pós-Garibaldi

Consulta autenticada somente leitura em 2026-09-12T20:31:50Z, após a aplicação e sincronização:

```json
{"contests":33,"sources":32,"structured_jobs":112,"publications":0,"versions":49,"notifications":48,"favorites":0,"alerts":1}
```

`structured_jobs` conta somente arrays `cargos` presentes, sem transformar `null` em um cargo. O detalhe `GET /concursos/33` confirma 13 cargos; o campo `publications` permanece nulo, enquanto a alteração documental está em `raw_data.tenderproof.amendments`.
