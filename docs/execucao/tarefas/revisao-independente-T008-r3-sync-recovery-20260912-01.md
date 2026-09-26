# Revisão independente T008 r3 — recuperação de sincronização

Data: 2026-09-12. **ACEITO — gate de retry/startup/foreground e ownership.**

Após falha, `syncIfDue(false)` usa janela de 60 s quando há outbox, em vez de bloquear por 1 h; inicialização de sessão e retorno ao foreground chamam `syncIfDue(true)`, sem depender de `navigator.onLine`. A fila/ownership/revalidação A→B anteriores permanecem preservados.

Verificação independente: `npx tsc --noEmit` PASS; `node --test tests/auth-initialization.test.cjs tests/alert-state.test.cjs tests/checkpoint-pending.test.cjs` PASS (9/9). O teste de inicialização confirma sync forçado após reabertura e a suíte confirma fila owner-scoped. Não mutuei executor, build, piloto ou navegador; não criei teste próprio de API mock por não ser necessário para o gate estático/dirigido.

Gate restante: deploy/rebuild serializado e nova corrida real offline→sync com API recuperada.
