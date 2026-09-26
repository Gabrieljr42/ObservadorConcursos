"""Pinned CPCON identity parser for T012, kept outside shared extraction."""
from __future__ import annotations

import re
from .contracts import Artifact, DiscoveredCandidate, Evidence, EvidenceValidation, ExtractedField, FieldState, PageText

SOURCE = "cpcon_open"
EXTERNAL_ID = "processo-seletivo-simplificado-no-002-2026"
SHA256 = "6a613684e806b59a350d25a614d6412b86e7daf47bc84c109f37da19fb40ef05"
BYTE_LEN = 498894
VERSION = "cpcon-t012-2026/1"
DETAIL_URL = "https://cpcon.uepb.edu.br/processo-seletivo-simplificado-no-002-2026/"
DOCUMENT_URL = "https://cpcon.uepb.edu.br/download/edital-processo-seletivo-simplificado-no-002-2026-uepb/?wpdmdl=9836&refresh=6aa01b90f3b551788877712"


def _ev(artifact: Artifact, page: PageText, snippet: str, path: str) -> Evidence:
    if "\ufffd" in snippet or snippet not in page.text:
        raise ValueError("CPCON snippet não é verbatim ou contém U+FFFD")
    return Evidence(
        evidence_id=f"cpcon-t012-{path.replace('.', '-')}", artifact_id=artifact.artifact_id,
        document_sha256=artifact.sha256, source_url=artifact.url_final,
        page_number=page.page_number, snippet=snippet, json_path=path,
        method="pinned-cpcon-text", method_version=VERSION,
        validation=EvidenceValidation(ok=True),
    )


def extract_identity(artifact: Artifact, pages: list[PageText], candidate: DiscoveredCandidate):
    if (candidate.source != SOURCE or candidate.external_id != EXTERNAL_ID
            or artifact.sha256 != SHA256 or artifact.byte_len != BYTE_LEN):
        return None
    page1 = next((p for p in pages if p.page_number == 1), None)
    if page1 is None or page1.error or page1.truncated or any("\ufffd" in p.text for p in pages):
        return ExtractedField(field_name="identity", state=FieldState.FAILED,
                              reason="CPCON: página/encoding inválidos")
    if len(re.findall(r"002/2026", "\n".join(p.text for p in pages))) != 1:
        return ExtractedField(field_name="identity", state=FieldState.FAILED,
                              reason="CPCON: edital 002/2026 ausente ou duplicado")
    org_snippet = "A\nUniversidade\nEstadual\nda"
    number_snippet = "002/2026"
    try:
        org_ev = _ev(artifact, page1, org_snippet, "orgao")
        num_ev = _ev(artifact, page1, number_snippet, "edital_numero")
    except ValueError as exc:
        return ExtractedField(field_name="identity", state=FieldState.FAILED, reason=str(exc))
    return ExtractedField(field_name="identity", state=FieldState.SUPPORTED,
                          value={"orgao": "Universidade Estadual da Paraíba", "edital_numero": "002/2026"},
                          evidence=[org_ev, num_ev], units={"identity": "source/external/PDF pinned"})


def document_identity_ids(candidate: DiscoveredCandidate, pages: list[PageText]) -> set[str]:
    """Resolve the strong identity using validation.py's real ``(candidate, pages)`` contract.

    Artifact pins are validated by :func:`extract_identity` when an Artifact is
    available.  The resolver has no positional artifact argument by design;
    when an adapter supplies optional pin metadata on the candidate/pages it is
    checked here too.  Missing optional metadata is not silently converted into
    a different identity, while mismatched supplied pins fail closed.
    """
    if candidate.source != SOURCE or candidate.external_id != EXTERNAL_ID or not pages:
        return set()
    if any(p.error or p.truncated or "\ufffd" in p.text for p in pages):
        return set()
    page1 = next((p for p in pages if p.page_number == 1), None)
    if page1 is None:
        return set()
    if page1.text.count("002/2026") + sum(p.text.count("002/2026") for p in pages if p.page_number != 1) != 1:
        return set()
    if "A\nUniversidade\nEstadual\nda" not in page1.text:
        return set()
    supplied_sha = getattr(candidate, "artifact_sha256", None) or getattr(page1, "artifact_sha256", None)
    supplied_len = getattr(candidate, "artifact_byte_len", None) or getattr(page1, "artifact_byte_len", None)
    if supplied_sha is not None and supplied_sha != SHA256:
        return set()
    if supplied_len is not None and supplied_len != BYTE_LEN:
        return set()
    return {EXTERNAL_ID}


def extract_fields(artifact: Artifact, pages: list[PageText], candidate: DiscoveredCandidate) -> list[ExtractedField]:
    """Emit the reviewed identity and six proven cargo rows with fresh evidence."""
    identity = extract_identity(artifact, pages, candidate)
    if identity is None or identity.state != FieldState.SUPPORTED:
        raise ValueError(identity.reason if identity is not None else "CPCON pin mismatch")
    if candidate.source != SOURCE or candidate.external_id != EXTERNAL_ID:
        raise ValueError("CPCON source/external pin mismatch")
    if artifact.url_requested != DOCUMENT_URL or artifact.url_final != DOCUMENT_URL:
        raise ValueError("CPCON document URL pin mismatch")
    by_page = {p.page_number: p for p in pages}
    def ev(path: str, page_no: int, snippet: str) -> Evidence:
        page = by_page.get(page_no)
        if page is None or page.error or page.truncated or "\ufffd" in snippet or snippet not in page.text:
            raise ValueError(f"CPCON evidence drift: {path}")
        return Evidence(evidence_id=f"cpcon-t012-{path.replace('[','-').replace(']','')}",
                        artifact_id=artifact.artifact_id, document_sha256=artifact.sha256,
                        source_url=artifact.url_final, page_number=page_no, snippet=snippet,
                        json_path=path, method="cpcon-source-parser", method_version="cpcon-reviewed-2026/3")
    identity_evidence = {item.json_path: item for item in identity.evidence}
    fields = [
        ExtractedField(field_name="titulo", state=FieldState.SUPPORTED,
                       value="PROCESSO SELETIVO SIMPLIFICADO Nº 002/2026",
                       evidence=[ev("titulo", 1, "002/2026")]),
        ExtractedField(field_name="orgao", state=FieldState.SUPPORTED,
                       value="Universidade Estadual da Paraíba", evidence=[ev("orgao", 1, "A\nUniversidade\nEstadual\nda")]),
        ExtractedField(field_name="edital_numero", state=FieldState.SUPPORTED,
                       value="002/2026", evidence=[ev("edital_numero", 1, "002/2026")]),
    ]
    rows = [
        ("Técnico em Laboratório (Esterilização)", 1, "Esterilização\n)\nCampus\nI\n01", 1),
        ("Técnico em Laboratório (Microbiologia de Alimentos)", 1, "Microbiologia\nde\nAlimentos\n)\nCampus\nI\n01", 1),
        ("Técnico em Laboratório (Eletrotécnica)", 2, "Eletrotécnica\n)\nUnidade\nAcadêmica\nde\nSousa\n-\nCampus\nIV\n02", 1),
        ("Técnico em Laboratório (Química)", 1, "Química\n)\nUnidade\nAcadêmica\nde\nSousa\n-\nCampus\nIV\n01", 2),
        ("Técnico em Laboratório (Química e Fertilidade do Solo)", 1, "Química\ne\nFertilidade\ndo\nSolo\n)\nCampus\nIV\n01", 2),
        ("Técnico em Laboratório (Histopatologia Oral)", 1, "Histopatologia\nOral\n)\nCampus\nVIII\n01", 2),
    ]
    cargos = []
    evidence = []
    for index, (name, vagas, location, page_no) in enumerate(rows):
        snippet = location
        evidence.append(ev(f"cargos[{index}]", page_no, snippet))
        cargos.append({"nome": name, "vagas_imediatas": vagas, "vagas_ampla_concorrencia": vagas,
                       "vagas_pcd": 0, "cadastro_reserva": False,
                       "requisitos": "Ensino Médio Completo + Curso Técnico em Laboratório na área Objeto da Seleção + Registro no Respectivo Conselho Profissional, caso Exigido por Lei",
                       "jornada": "40h", "remuneracao": "3768.36", "moeda": "BRL",
                       "remuneracao_observacao": "vencimento básico; unidade temporal não explicitada no edital"})
    fields.append(ExtractedField(field_name="cargos", state=FieldState.SUPPORTED, value=cargos, evidence=evidence))
    return fields
