# Identidade documental em links temporários

A aquisição mantém o URL oficial completo nos snapshots e nas execuções. A comparação usa uma cópia normalizada apenas para os contratos de parâmetros temporários comprovados. A normalização nunca troca o endereço usado no download nem dispensa as guardas de destino, origem, bytes e associação ao concurso.

No CPCON, somente o parâmetro `refresh` é descartado do endereço HTTPS oficial `/download/.../`, com a forma exata de query observada. `wpdmdl` continua identificando o documento. Na Cesgranrio, a assinatura SAS é desconsiderada somente no host e diretório oficiais, com identificador de evento, UUID documental e permissões de leitura observadas. Outros parâmetros, hosts e formas conservam a identidade completa. A convenção AWS anterior permanece compatível.

A assinatura da observação inclui manifesto normalizado, validação, hash do artefato, hash semântico e versões dos extratores. A renovação de uma assinatura temporária com os mesmos bytes não cria outra observação. Outro documento ou outro SHA256 continua produzindo alteração, e a pendência de revisão não é removida por uma renovação posterior do link.

Não há migração silenciosa de observações antigas. O coletor compara apenas histórico do mesmo usuário, fonte, modo e candidato, com execução concluída e SHA idêntico. A assinatura antiga precisa ser verificável a partir do conteúdo preservado. Quando o conteúdo normalizado coincide, o ID e a assinatura anteriores são reutilizados, mantendo o run e o resumo originais; apenas `last_seen` avança como na deduplicação normal. O snapshot novo registra `document_signature_match` para auditoria. Histórico não verificável permanece separado.

Provas oficiais: `tenderproof-batch60-major-sas-identity.json` e `tenderproof-batch60-cpcon-refresh-proof.json`. Os testes de rotação, alteração de bytes, persistência de pendência e compatibilidade histórica estão em `backend/tests/test_tenderproof_document_identity.py`. São mutações controladas claramente identificadas, complementares às capturas oficiais.

A regressão de integração de08/09/2026 passou871 testes, com14 opcionais PostgreSQL não executados sem URL descartável explícita e dois live excluídos. Comando em `backend`: `.venv/Scripts/python.exe -m pytest -q -m 'not live' --junitxml=.tenderproof/batch60-integrated-regression.xml`. As provas PostgreSQL anteriores continuam datadas separadamente; essa execução não as repete nem as inclui na contagem.
