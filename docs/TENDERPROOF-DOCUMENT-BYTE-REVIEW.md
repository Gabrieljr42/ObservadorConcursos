# Revisão de documentos alterados na mesma URL

Correção de 08/09/2026. Uma proposta preparada antes da substituição dos bytes do
edital poderia continuar aplicável: o hash produzia outra observação, mas a
pendência documental comparava apenas URL, título e tipo.

O volume operacional agora contém `acquired_document_state`, tabela aditiva por
usuário, fonte, modo, candidato e URL documental normalizada. O primeiro hash
observado estabelece uma referência; mudança posterior registra `bytes_changed`,
URL/título, hashes anterior/novo e IDs das execuções com os artefatos preservados.
Assinaturas temporárias da URL não representam mudança de bytes.

O resultado concluído atualiza esse estado, a pendência e a observação na mesma
transação protegida pelo fencing. Se o processamento falhar depois de preservar
um artefato, seu hash ainda pode gerar pendência por checkpoint autenticado pela
lease; um PDF ilegível novo não torna a proposta antiga segura. Repetições não
duplicam o mesmo evento e a pendência não é eliminada pelo desaparecimento do link.

Na atualização de volumes anteriores, o hash é recuperado de observação histórica
somente quando a associação com a URL é explícita ou existe exatamente um edital
principal no manifesto. Não se inventa vínculo para manifestos ambíguos.

A criação, aprovação e aplicação continuam usando a guarda corrente de revisão
documental, incluindo a última verificação sob lock operacional curto antes do
commit canônico. O original válido continua tendo bytes válidos; a pendência
significa que os efeitos da mudança ainda precisam de revisão.

Prova focal reproduzível, em `backend`:

```powershell
.venv/Scripts/python.exe -m pytest tests/test_tenderproof_document_review_gate.py tests/test_tenderproof_continuous.py tests/test_tenderproof_rollout_operations.py -q --disable-warnings --junitxml=.tenderproof/document-byte-review-focal.xml
```

Os testes usam mudanças controladas no checkpoint: hashes diferentes na mesma
URL, proposta anterior, repetição, atualização de volume, falha transacional e
rotação de assinatura. Não representam alteração real de um portal. As provas
de aquisição e publicação com PDFs oficiais permanecem relatórios separados.

Limite explícito: bytes de documentos complementares que não foram adquiridos
não são monitorados. Alteração silenciosa desses bytes na mesma URL não é
detectada apenas pelo manifesto. Não há interpretação universal de retificações
nem liberação automática da pendência.
