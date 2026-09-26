# Contemax — contrato observado e impedimento documental

Captura em 2026-09-08. Os caminhos oficiais `/site/concursos` e `/site/concursos-em-andamento/prefeitura-municipal-de-cubati-pb` responderam HTTP 200 sobre HTTPS, com TLS verificado e sem redirecionamento. O HTTP histórico do inventário não exige enfraquecer a política global: os caminhos exatos funcionam em HTTPS.

O WordPress publica links documentais legados HTTP. O contrato preserva host e caminho literais observados e troca apenas o esquema para HTTPS no host exato `www.contemaxconsultoria.com.br`, diretório `/site/wp-content/uploads/AAAA/MM/arquivo.pdf`. A validação de destino continua recusando HTTP, hosts alternativos, queries, credenciais, portas alternativas e travessia de caminho. Não existe fallback para HTTP ou TLS desativado.

O candidato observado Cubati é identificado pelo caminho completo categoria/slug e corroborado pelo único `h3.tt-detalhe`. Os PDFs são extraídos apenas do contêiner desse título. O diretório WordPress não possui ID de concurso; associação contextual e validação posterior dos bytes permanecem necessárias. Apenas o rótulo observado `EDITAL REGULAMENTADOR` é principal. Outros editais, retificações, resultados e comunicados permanecem no manifesto como complementares; dois principais são ambíguos. Não se interpreta efeito de retificação.

A listagem mistura concursos em andamento e realizados. Cursos de formação e trabalhos de plano de cargos são excluídos. Ausência de paginação não certifica completude. Texto histórico contém caracteres corrompidos; o título de Cubati e o rótulo original observados são ASCII preservado, e rótulos incompletos não promovem documentos a principal.

## Impedimento real preservado

O original observado é `http://www.contemaxconsultoria.com.br/site/wp-content/uploads/2024/09/Edital-CUBATI.pdf`. Duas tentativas do mesmo caminho HTTPS, sem redirects, com TLS ativo, timeout25s e limite30MiB, falharam antes de receber conteúdo:

1. RemoteProtocolError: servidor desconectou sem resposta (User-Agent padrão httpx).
2. ConnectError / WinError10054 (User-Agent Mozilla/5.0, igual à captura HTML bem-sucedida).

`docs/tenderproof-batch60-contemax-pdf-probe.json` preserva diagnóstico e horário. Não houve PDF adquirido nem extração, proposta, publicação ou homologação. Não se atribui causa TLS específica: as evidências mostram falha de conexão/resposta, sem erro de certificado observado. O limite de processamento60p não foi alcançado e não foi aumentado.

## Evidências e testes

- `backend/tests/fixtures/tenderproof_batch60_contemax/manifest-https.json`: URLs, horários, status, limites e hashes originais/sanitizados.
- `backend/app/tenderproof/batch60_contemax_adapter.py`: contrato isolado, não registrado centralmente por esta tarefa.
- `backend/tests/test_tenderproof_batch60_contemax.py`: 14 testes passaram; seleção de original, exclusões, identidade, ambiguidade, limites, challenge, integridade de fixtures e destinos.
- `backend/.tenderproof/batch60-contemax-contracts.xml`: JUnit focal.

Estado: estratégia implementada com cobertura parcial, aquisição documental HTTPS impedida nesta observação. Nenhuma amostra válida é adicionada à contagem do lote60.
