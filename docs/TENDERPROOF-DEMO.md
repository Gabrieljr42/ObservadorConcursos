# TenderProof — demonstração de aproximadamente cinco minutos

Ambiente: servidor `scripts/tenderproof_review_server.py --port 8014`, frontend
localhost:3000 com API em 8014. Banco SQLite descartável, baseline sintética ID1,
usuário local descrito em TENDERPROOF.md. Não conecta ao catálogo real.

| Tempo | Ação | Tipo de evidência |
| --- | --- | --- |
| 0:00–0:40 | Abrir TenderProof, IBGP/Demonstração, candidato42 | Mock offline explicitamente rotulado |
| 0:40–1:20 | Conferir SHA-256 e página física de inscrições; unknown e limites salariais | PDF sintético com texto verificável |
| 1:20–2:10 | Baseline1 → proposta → selecionar apenas fim das inscrições → aprovar → aplicar | Publicação efetiva somente em SQLite descartável; versão1, diff19/04→20/04 |
| 2:10–2:40 | Mostrar relatório demo: repetir aplicação e reprocessar sem nova versão; rollback auditável | Transações reais locais, transporte de notificação interno isolado |
| 2:40–3:40 | Estratégia antiga/alterada, suíte independente, rejeição de proposta errada, revisão e rollback | Mudança sintética controlada; não alegar mudança real no portal |
| 3:40–4:20 | Iniciar IMESO/Demonstração, selecionar candidato, conferir mesmo contrato e remuneração unknown | Mock offline da segunda fonte |
| 4:20–5:00 | Abrir relatórios preservados Browser/Sandbox e comparação IBGP704 | Separar leitura atual do provedor, artefato real, mock e replay indisponível |

Uma execução reproduzível sem interface:

```powershell
# No backend
.venv/Scripts/python.exe scripts/tenderproof_demo.py
```

Gera `backend/.tenderproof/demo-phases4-7.json`. Cria/remova automaticamente apenas
seus bancos temporários. Demonstração sintética pequena; não é benchmark estatístico.

## Métricas e denominadores

- Publicação: 5/5 campos avaliados corretos, 5/5 evidências desses campos válidas.
  O sexto campo (remuneração por cargo) é avaliado separadamente como bloqueado
  para faixa salarial canônica; não está escondido no denominador de cinco.
- Reprocessamento sem mudança: 0/1 diffs falsos; repetição da operação mantém versão.
- Recuperação: 10/10 diagnósticos da suíte controlada. Recuperação de navegação em
  2/3 cenários explicitamente classificados como quebra (02,04,09); o falso vazio04
  é diagnosticado e preservado, não anunciado como recuperado.
- Propostas incorretas aceitas: 0/1 estratégia incorreta na demo; bateria de testes
  cobre ataques adicionais, documentos errados e regressões.
- IMESO offline: 5/6 campos preenchidos; remuneração unknown com motivo.
- Latências por etapa ficam no relatório de cada execução, não valores fixos.
- Intervenção humana: seleção explícita do concurso, escolha/aprovação dos campos
  e revisão/ativação de estratégia. Demo CLI simula essas decisões de forma rotulada.
- Custo offline: nenhum recurso remoto. Custos live são estimativas separadas;
  não representam faturamento confirmado. Ver TENDERPROOF-PROCESSING.md.

## Artefatos reais e limites

`real-baseline-comparison.json` compara o PDF histórico IBGP704 com uma observação
tradicional nova de três endpoints oficiais, preservada em `real-baseline-704.json`.
Ela foi carregada em SQLite descartável com proveniência; não é baseline canônica
histórica nem publicação real. PDF: 46 páginas; título/edital/inscrições sustentados;
órgão/remuneração unknown. Snapshot original do run histórico foi preservado.

O Sandbox teve duas tentativas falhas, mantidas como falhas, e uma tentativa com
extração bem-sucedida. Na primeira faltava pypdf; na segunda o script gerou duas
páginas. A correção tem preflight de página antes de criar recurso. As três
confirmaram encerramento, mas isso não resolve a discrepância do dashboard.

Não apresentar os registros mock de sessão como replays oficiais. Não há animação
local substituindo gravação do provedor. O console ainda precisa ser conciliado
com a organização retornada pela API; GET200 ou `released` não comprova a conta
humana exibida. Novas investigações Browser têm seus próprios relatórios.

## Rollback e operação

Publicação: POST `/tenderproof/publications/proposals/{id}/rollback` com motivo,
JWT do proprietário autorizado. Se houver mudança posterior, recusa a reversão.
Histórico/notificações já emitidas são preservados; evento de reversão é separado.

Estratégia: POST `/tenderproof/recovery/proposals/{id}/rollback` com motivo, JWT.
Ativação posterior impede sobrescrever silenciosamente outra estratégia.

Jobs: cancelamento e reconciliação não criam recursos substitutos. Jobs antigos
interrompidos são recuperados pelo ledger; estado remoto desconhecido continua
explícito. Retenção remove artefatos terminais conforme política, sem apagar
histórico do catálogo. Consulte os documentos operacionais de cada módulo.

Investigações reais adicionais concluídas: IBGP704 (46 páginas, hash histórico
reconfirmado) e IMESO139 (29 páginas). Apresentar seus PDFs como artefatos reais
preservados, sem fingir nova execução durante a demo. Os cinco Browser usados nas
tentativas estão released por GET do provedor. IMESO tem snapshot corrigido offline
separado: taxa não é salário, remuneração unknown. Console autenticado continua
sem sessões/uso, apesar de chave ativa com prefixo correspondente; suporte pendente.
