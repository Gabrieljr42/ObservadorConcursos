"""TenderProof: pacote de aquisição e verificação com evidências (fases 0–3).

Modo de comparação e revisão. Não publica no catálogo, não atualiza
``Concurso``, não cria versões ou notificações.
"""

from app.tenderproof.contracts import (
    SUPPORTED_SOURCE,
    TARGET_FIELDS,
)

__all__ = ["SUPPORTED_SOURCE", "TARGET_FIELDS"]
