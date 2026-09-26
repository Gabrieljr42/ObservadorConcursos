"""TenderProof — provedor LLM encapsulado (não usado por padrão no MVP).

Regras se um dia for ativado:

- Saída estruturada exigida; chamadas/tokens/tempo limitados.
- Páginas e documentos tratados como dados não confiáveis.
- Sem execução de código gerado, sem escrita direta no banco.
- Autoavaliação do modelo nunca é prova de correção.
- Testes offline com respostas simuladas.

Decisão do MVP: extração determinística é suficiente; este módulo existe
para manter a fronteira explícita e testável.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(slots=True)
class LLMConfig:
    provider: str = "disabled"
    model: str = ""
    max_calls: int = 4
    max_tokens: int = 2000
    timeout_s: float = 30.0


class LLMProvider(Protocol):
    def extract_fields(self, *, pages_text: list[str], fields: list[str]) -> dict[str, Any]:
        ...


class DisabledLLMProvider:
    def __init__(self, config: LLMConfig | None = None) -> None:
        self.config = config or LLMConfig()

    def extract_fields(self, *, pages_text: list[str], fields: list[str]) -> dict[str, Any]:
        raise RuntimeError("LLM desativado no MVP TenderProof (extração determinística em uso)")


class StubLLMProvider:
    """Respostas simuladas para testes offline."""

    def __init__(self, scripted: dict[str, Any] | None = None) -> None:
        self.scripted = dict(scripted or {})
        self.calls = 0

    def extract_fields(self, *, pages_text: list[str], fields: list[str]) -> dict[str, Any]:
        self.calls += 1
        return {name: self.scripted.get(name) for name in fields}
