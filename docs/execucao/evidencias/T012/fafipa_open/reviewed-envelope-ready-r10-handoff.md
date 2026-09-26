# FAFIPA T012 R10 handoff

O envelope imutável R9 continua contendo `concurso_id=null`, owner 1, source 69, external 4208, sete campos elegíveis e 14 cargos. O estado nulo é válido como pré-alocação sob o contrato atual; a alocação normal deve ocorrer antes de `ReviewedRun.model_validate`/dry-run.

Run canônico derivado para integração: `tp-reviewed-fefe8924b68403d795a4d43b73e85e1c`. O identificador `tp-reviewed-187a43fbfc355834ff54dbcb6adb4fc1` fica marcado como stale/mismatch e não deve ser reutilizado.

Dois probes independentes confirmaram hash/bytes, replay determinístico, rejeição de owner 0 e rejeição de byte drift. Nenhuma proposta, versão, outbox, notificação ou alteração live foi criada.
