# Revisão independente T010/ID6 — IMESO Berizal r2

Status: ACEITA.

Correção confirmada: `EXPECTED_BYTE_LEN = 597314` participa da guarda junto de source `imeso_open`, external_id `139` e SHA esperado. Os testes agora cobrem byte lengths 0, 597313 e 597315, todos falhando fechado; o comprimento correto continua suportado. `tests/test_imeso_berizal_jobs.py` passou 3/3, e a suíte combinada informada pelo executor passou 9/9.

O delta remove o único achado P1 da revisão anterior. Permanecem preservados: página 22, 11 microáreas literais, 1+CR/AC1/PcD0, remuneração/jornada/requisito/taxa, ausência de prova/data inventada e integração `extract_fields → _revalidate → create_proposal` sem aplicação/persistência.

Gate: ACEITA. Sem mutações de piloto, serviços ou quadro.
