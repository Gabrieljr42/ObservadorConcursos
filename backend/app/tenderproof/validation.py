"""TenderProof Fase 2 — validação de identidade do edital.

Distingue: concurso e edital corretos; documento de outro concurso;
resultado/gabarito confundido com edital; página HTML no lugar de PDF;
documento sem texto extraível.
"""

from __future__ import annotations

import re
import unicodedata


def distinctive_title_words(title: str) -> list[str]:
    normalized = unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode().lower()
    generic = {"concurso", "publico", "publica", "prefeitura", "municipal", "municipio", "camara", "instituto", "previdencia", "processo", "seletivo", "edital", "abertura", "inscricoes", "abertas", "saiba", "mais", "para", "pelo", "estado"}
    return [w for w in re.findall(r"[a-z]{4,}", normalized) if w not in generic]


def title_is_corroborated(title: str, text: str) -> bool:
    words = distinctive_title_words(title)
    normalized = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().lower()
    return bool(words) and all(re.search(rf"\b{re.escape(w)}\b", normalized) for w in words)


def document_identity_ids(adapter, candidate, pages):
    if getattr(adapter, 'source', None) == 'cpcon_open':
        # CPCON's reviewed parser owns the pinned candidate/PDF contract and
        # exposes the resolver with the common (candidate, pages) signature.
        from app.tenderproof.cpcon_t012 import document_identity_ids as cpcon_ids
        return cpcon_ids(candidate, pages)
    if getattr(adapter, 'source', None) == 'avancasp_open':
        from app.tenderproof.avancasp_t012 import document_identity_ids as avancasp_ids
        return avancasp_ids(candidate, pages)
    if getattr(adapter, 'source', None) == 'apta_open':
        from app.tenderproof.apta_aragarcas_parser import document_identity_ids as apta_ids
        return apta_ids(candidate, pages)
    if getattr(adapter, 'source', None) == 'publiconsult_open':
        from app.tenderproof.publiconsult_t012 import document_identity_ids as publiconsult_ids
        return publiconsult_ids(candidate, pages)
    if getattr(adapter, 'source', None) == 'klc_open':
        from app.tenderproof.klc_t012 import document_identity_ids as klc_ids
        return klc_ids(candidate, pages)
    resolver=getattr(adapter,'document_identity_ids',None)
    if callable(resolver):
        values = resolver(candidate,pages)
    else:
        values = set(re.findall(adapter.document_identity_pattern,'\n'.join(p.text for p in pages),re.I))
    # A PDF line may print an official URL followed by sentence punctuation;
    # punctuation is not part of the contest slug and must not create a false
    # second identity (observed in the preserved FGV Macaé edital).
    return {value.rstrip('.,;:!?)]}') for value in values}

from app.tenderproof.contracts import (
    DiscoveredCandidate,
    PageText,
    ValidationResult,
    ValidationStatus,
)


def validate_identity(
    *,
    candidate: DiscoveredCandidate,
    pages: list[PageText],
    document_title: str,
    document_url: str,
    document_kind: str = 'edital',
) -> ValidationResult:
    checks: list[str] = []
    errors: list[str] = []
    warnings: list[str] = []
    from app.tenderproof.document_labels import individual_administrative_act, publication_label
    if individual_administrative_act(document_title):
        return ValidationResult(status=ValidationStatus.NON_EDITAL,
            errors=['ato administrativo posterior ou individual; não é edital de abertura'], checks=checks)
    if re.match(r'^(?:prorrogacao\b|(?:ampliacao|reducao)\s+(?:do numero\s+)?de vagas\b)',
                publication_label(document_title)):
        return ValidationResult(status=ValidationStatus.NON_EDITAL,
            errors=['alteração de prazo ou vagas; não é edital de abertura ou consolidado'], checks=checks)

    lowered_title = f"{document_title} {document_url}".lower()
    if any(term in lowered_title for term in ("gabarito", "resultado final", "resultado_preliminar")):
        checks.append("titulo_documento_sugere_nao_edital")

    full_text = "\n".join(p.text for p in pages)
    folded = full_text.lower()
    first_content = next((p.text.strip() for p in pages if p.text.strip()), "")
    title_exclusions = r"anexo|gabarito|resultado|errata" if document_kind == 'consolidado' else r"anexo|gabarito|resultado|retifica|errata"
    classification_title = document_title
    if document_kind == 'consolidado':
        classification_title = re.sub(r'\bconsolidado\s+com\s+(?:a\s+)?errata\b', 'consolidado', document_title, flags=re.I)
    if re.search(r"^\s*(?:anexo\s+[ivx\d]+|gabarito\s+oficial|resultado\s+(?:final|preliminar))\b", first_content[:500], re.I | re.M) or re.search(title_exclusions, classification_title, re.I):
        return ValidationResult(status=ValidationStatus.NON_EDITAL,
            errors=["documento identificado como anexo, resultado ou alteração; não é edital principal"], checks=checks)
    checks.append(f"paginas_com_texto={sum(1 for p in pages if p.text.strip())}/{len(pages)}")

    if not full_text.strip():
        return ValidationResult(
            status=ValidationStatus.UNREADABLE,
            errors=["documento sem texto extraível"],
            warnings=warnings,
            checks=checks,
        )

    # Resultado/gabarito confundido com edital: corpo fala de resultado/gabarito
    # sem apresentar abertura de edital.
    mentions_result = bool(re.search(r"resultado\s+(final|preliminar)|gabarito\s+oficial", folded))
    mentions_opening = bool(re.search(r"edital\s+de\s+abertura|abre\s+inscri", folded)) or "edital" in folded
    if mentions_result and not mentions_opening:
        errors.append("documento parece resultado/gabarito, não edital de abertura")
        return ValidationResult(
            status=ValidationStatus.NON_EDITAL, errors=errors, warnings=warnings, checks=checks
        )

    # Documento de outro concurso: o texto cita outro código IBGP explícito.
    cod = (candidate.external_id or "").strip()
    from app.tenderproof.source_adapters import get_source_adapter
    other_cods = document_identity_ids(get_source_adapter(candidate.source),candidate,pages)
    if cod and other_cods and other_cods != {cod}:
        errors.append(f"documento cita outro concurso (cod {sorted(other_cods)[:3]}), esperado cod={cod}")
        return ValidationResult(
            status=ValidationStatus.WRONG_CONTEST, errors=errors, warnings=warnings, checks=checks
        )

    # Corroboração fraca do vínculo (título/órgão aparecem no texto).
    title_words = [w for w in re.findall(r"[A-Za-zÀ-ÿ]{4,}", candidate.title_observed or "")][:6]
    hits = sum(1 for w in title_words if w.lower() in folded)
    structured_title = getattr(get_source_adapter(candidate.source), 'document_title_corroborated', None)
    if not (title_is_corroborated(candidate.title_observed or "", full_text)
            or (callable(structured_title) and structured_title(candidate, pages))):
        warnings.append("título do candidato não localizado no texto do documento")
    else:
        checks.append(f"titulo_corroborado={hits}/{len(title_words)}")

    if errors:
        return ValidationResult(
            status=ValidationStatus.WRONG_CONTEST, errors=errors, warnings=warnings, checks=checks
        )
    if warnings:
        return ValidationResult(
            status=ValidationStatus.PARTIAL, errors=errors, warnings=warnings, checks=checks
        )
    return ValidationResult(status=ValidationStatus.VALID, errors=errors, warnings=warnings, checks=checks)
