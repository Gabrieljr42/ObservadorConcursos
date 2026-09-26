# Parecer arquitetural — ID16 / documento oficial desaparecido

Data: 2026-09-13. Read-only; não executei endpoints nem alterei o piloto.

## Diagnóstico

O caminho normal é `POST /tenderproof/continuous/document-review/{run_id}/prepare`, seguido de `current`, `draft` e `approve`. `review_cases.prepare()` reabre a página oficial e exige igualdade exata entre o manifesto atual e o manifesto preservado; se a retificação deixou de aparecer, retorna **“Documento pendente não está mais disponível na lista oficial”**. `select-document` não resolve este caso: só seleciona `edital`/`consolidado`, rejeita `retificacao` e substitui o documento principal, o que seria semântico e operacionalmente incorreto.

O artefato ID16, porém, está preservado e SHA-bound (`e5d57b…b38f05`, 397.534 bytes, 23 páginas) e sua identidade já constava no manifesto/pending do catálogo. A lacuna é do fluxo de revalidação, não autorização para URL arbitrária.

## Critério de aceite para patch

Adicionar uma via explícita de “revisão de documento preservado desaparecido” (ou extensão restrita de `prepare`) que:

1. aceite somente documento `retificacao` já presente no `manifest` e `pending_documents` da revisão, com owner/source/mode/candidate/external_id e URL exatos; não aceite URL, título ou SHA fornecidos livremente pelo cliente;
2. carregue o artefato da store por referência persistida, verifique bytes, SHA, tamanho, páginas, limites e evidência literal; rejeite arquivo ausente/divergente;
3. mantenha o edital-base/run/catálogo intactos, registre a retificação como documento suplementar do caso e preserve revisão CAS/hash/owner;
4. exija decisão por documento (`no_field_change` ou `field_changes`) com trecho/proveniência; para no-op, `approve` deve limpar pending sem criar proposta/versão. Para mudança, mantenha pending até aplicação canônica e exija `finalize_field_changes`;
5. revalide que somente a ausência do documento pendente mudou; qualquer divergência do restante do manifesto continua 409 e exige nova coleta.

O patch só é aceito com testes de URL arbitrária rejeitada, owner/candidate cross-user rejeitados, SHA/path drift rejeitado, documento desaparecido preservado aceito como no-op, documento não-preservado rejeitado, CAS/replay e zero mutação de catálogo. Após isso, o draft ID16 pode ser enviado pelo endpoint normal; até lá, o 409 permanece bloqueio correto.
