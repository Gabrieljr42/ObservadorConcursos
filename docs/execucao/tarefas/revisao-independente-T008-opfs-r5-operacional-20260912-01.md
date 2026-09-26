# Revisão independente T008 — OPFS/SQLite web r5

Data: 2026-09-12

## Gate código — ACEITA

Mantém-se o aceite r4: singleton único, nenhuma abertura/fecho auxiliar, serialização sem deadlock, rollback preservando o erro original, retry posterior, isolamento/outbox T008 e native inalterado. Evidências automatizadas anteriores: testes dirigidos 24/24, suíte mobile 41/41, `tsc` e export web PASS.

## Gate operacional/deploy — ACEITA

Smoke do coordenador no build `BA7C7308…A6143B`, sem limpar OPFS: localhost aba A abriu ID6; aba B na mesma origem reproduziu `NoModificationAllowedError` e exibiu erro acessível com retry; após fechar A, aguardar 2 s e clicar `Tentar novamente`, B abriu ID6 completo; reload permaneceu estável. Isso prova lock externo, recuperação e preservação dos dados. `127.0.0.1` continua bloqueado por handle externo não visível nesta sessão e deve permanecer documentado como condição ambiental, não defeito desta correção.
