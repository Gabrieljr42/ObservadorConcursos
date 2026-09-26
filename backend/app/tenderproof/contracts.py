"""TenderProof Fase 0 — contratos tipados.

Camada de aquisição e verificação com evidências oficiais, em modo de
comparação e revisão. Não publica no catálogo, não atualiza ``Concurso``,
não cria versões nem notificações.

Separação deliberada de estados:

- ``ExecutionStatus``: onde o fluxo de aquisição está.
- ``ValidationStatus``: o que a validação concluiu sobre o documento.
- ``FieldState``: situação de cada campo extraído.
- ``Agreement``: resultado da comparação baseline × TenderProof por campo.

O resultado do crawler existente é baseline (observação anterior), nunca a
verdade usada para validar o TenderProof.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field, computed_field

TARGET_FIELDS: tuple[str, ...] = (
    "titulo",
    "orgao",
    "edital_numero",
    "inscricao_inicio",
    "inscricao_fim",
    "prova_data",
    "cargos",
    "remuneracao",
)

SUPPORTED_SOURCE = "ibgp_open"
SAMPLE_LIMIT = 5


class ExecutionStatus(str, Enum):
    CREATED = "created"
    DISCOVERING = "discovering"
    AWAITING_SELECTION = "awaiting_selection"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ValidationStatus(str, Enum):
    PENDING = "pending"
    VALID = "valid"
    PARTIAL = "partial"
    WRONG_CONTEST = "wrong_contest"
    NON_EDITAL = "non_edital"
    UNREADABLE = "unreadable"


class FieldState(str, Enum):
    """Diferenciação exigida pela Fase 0.

    - SUPPORTED: valor sustentado por evidência verificável.
    - UNKNOWN: não observado (motivo claro; resultado válido).
    - FAILED: extração falhou (motivo claro).
    - CONFLICT: informações conflitantes no material.
    """

    SUPPORTED = "supported"
    UNKNOWN = "unknown"
    FAILED = "failed"
    CONFLICT = "conflict"


class Agreement(str, Enum):
    AGREE = "agree"
    DIVERGE = "diverge"
    NO_EVIDENCE = "no_evidence"
    NO_BASELINE = "no_baseline"


class DiscoveredCandidate(BaseModel):
    candidate_id: str
    title_observed: str | None = None
    selection_label_observed: str | None = None
    detail_url_observed: str
    external_id: str | None = None
    observed_at: datetime
    source: str = SUPPORTED_SOURCE


class DocumentAcquisitionRequest(BaseModel):
    """Observed public PDF export only; no arbitrary headers or credentials."""
    model_config = {"extra": "forbid"}
    method: Literal["POST"] = "POST"
    body: str = Field(min_length=3, max_length=32, pattern=r"^[1-9][0-9]{0,8},(?:0|[1-9][0-9]{0,8})$")
    content_type: Literal["application/x-www-form-urlencoded"] = "application/x-www-form-urlencoded"


class DocumentCandidate(BaseModel):
    doc_id: str
    title: str
    url_requested: str
    url_final: str | None = None
    kind: Literal["edital", "consolidado", "retificacao", "prorrogacao", "anexo", "resultado", "gabarito", "outro"] = "outro"
    reason_chosen: str = ""
    acquisition_request: DocumentAcquisitionRequest | None = None
    file_format: Literal['pdf','xlsx'] = 'pdf'


class Artifact(BaseModel):
    artifact_id: str
    sha256: str
    byte_len: int
    url_requested: str
    url_final: str
    content_type: str | None = None
    downloaded_at: datetime
    # Caminho relativo dentro do diretório de artefatos do TenderProof.
    # Nunca aponta para tabelas canônicas.
    storage_path: str | None = None


class PageText(BaseModel):
    artifact_id: str
    # Página física do PDF (1-indexed), preservada da ordem do documento.
    page_number: int
    text: str = ""
    char_count: int = 0
    truncated: bool = False
    error: str | None = None
    extraction_method: Literal["pdf_text", "ocr_tesseract"] = "pdf_text"
    processing_job_id: str | None = None
    extractor_version: str | None = None
    ocr: dict[str, Any] | None = None


class EvidenceValidation(BaseModel):
    ok: bool
    code: str | None = None
    message: str | None = None


class Evidence(BaseModel):
    evidence_id: str
    artifact_id: str | None = None
    document_sha256: str | None = None
    source_url: str
    # Página física do PDF quando aplicável.
    page_number: int | None = None
    # Trecho textual que DEVE existir verbatim no material preservado.
    snippet: str | None = None
    # Caminho do campo em resposta JSON observada (ex.: "meta.nome").
    json_path: str | None = None
    method: str
    method_version: str
    validation: EvidenceValidation = Field(default_factory=lambda: EvidenceValidation(ok=True))


class ExtractedField(BaseModel):
    field_name: str
    state: FieldState
    # Valor normalizado (ISO para datas, "1234.56" para dinheiro, texto p/ demais).
    value: Any | None = None
    original_value: Any | None = None
    evidence: list[Evidence] = Field(default_factory=list)
    reason: str | None = None
    validation: EvidenceValidation = Field(default_factory=lambda: EvidenceValidation(ok=True))
    # Provenance for values whose meaning depends on an explicit unit (for
    # example 40h or R$ per hour).  It is never inferred by publication.
    units: dict[str, Any] | None = None


class ValidationResult(BaseModel):
    status: ValidationStatus = ValidationStatus.PENDING
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    checks: list[str] = Field(default_factory=list)


class ComparisonField(BaseModel):
    field_name: str
    baseline_value: Any | None = None
    tenderproof_value: Any | None = None
    tenderproof_state: FieldState | None = None
    agreement: Agreement
    explanation: str = ""


class ComparisonResult(BaseModel):
    status: Literal["pending", "compared"] = "pending"
    baseline_collected_at: datetime | None = None
    baseline_origin: str = ""
    fields: list[ComparisonField] = Field(default_factory=list)


class SessionRecord(BaseModel):
    """Uma sessão Solari associada a uma etapa (discovery usa sessão curta
    própria; detalhe/download compartilham outra). O browser nunca fica
    aberto esperando a seleção humana."""

    phase: Literal["discovery", "detail"]
    session_id: str | None = None
    replay_url: str | None = None
    replay_status: Literal["available", "pending", "disabled", "failed"] = "pending"
    replay_note: str | None = None
    closed: bool = False
    close_requested: bool = False

    @computed_field
    @property
    def closure_status(self) -> Literal["confirmed", "requested", "unknown"]:
        return "confirmed" if self.closed else "requested" if self.close_requested else "unknown"


class SupplementaryDocument(BaseModel):
    document: DocumentCandidate
    artifact: Artifact
    reading: dict[str,Any] | None = None


class TenderProofRun(BaseModel):
    run_id: str
    owner_user_id: int | None = None
    source: str = SUPPORTED_SOURCE
    # Modo vinculado à execução: "mock" (sintético) ou "real" (Solari).
    # Não é permitido iniciar em um modo e selecionar em outro.
    mode: Literal["mock", "real"] = "mock"
    # Amostra limitada identificada explicitamente: nunca é o catálogo da banca.
    sample_note: str = "Amostra limitada de até 5 candidatos; não é o catálogo completo da banca."
    execution_status: ExecutionStatus = ExecutionStatus.CREATED
    validation_status: ValidationStatus = ValidationStatus.PENDING
    comparison_status: Literal["pending", "compared"] = "pending"
    candidates: list[DiscoveredCandidate] = Field(default_factory=list)
    # Acquisition scope is independent of whether individual PDF fields validate.
    coverage: dict[str, Any] = Field(default_factory=dict)
    selected_candidate_id: str | None = None
    document: DocumentCandidate | None = None
    artifact: Artifact | None = None
    supplementary_documents: list[SupplementaryDocument] = Field(default_factory=list)
    document_selection: dict[str, Any] | None = None
    total_pages: int | None = None
    processed_pages: int | None = None
    truncated: bool = False
    page_errors: list[str] = Field(default_factory=list)
    fields: list[ExtractedField] = Field(default_factory=list)
    validation: ValidationResult = Field(default_factory=ValidationResult)
    comparison: ComparisonResult = Field(default_factory=ComparisonResult)
    session_id: str | None = None
    replay_url: str | None = None
    replay_available: bool = False
    # Histórico por etapa (compatível com os campos únicos acima, que refletem
    # a sessão mais recente para a interface existente).
    sessions: list[SessionRecord] = Field(default_factory=list)
    # Diagnóstico operacional (mecanismos usados, fallbacks, replay). Nunca
    # contém credenciais, cookies, endpoints CDP ou cabeçalhos sensíveis.
    diagnostics: list[str] = Field(default_factory=list)
    # Verdadeiro quando o material é sintético (mocks/fixtures) e não observação oficial.
    is_synthetic_sample: bool = False
    semantic_hash: str | None = None
    error: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now().astimezone())
    updated_at: datetime = Field(default_factory=lambda: datetime.now().astimezone())

    def field_map(self) -> dict[str, ExtractedField]:
        return {f.field_name: f for f in self.fields}
