"""Reproduce annex fields using separate immutable artifacts and identity evidence."""
import hashlib
import re
from app.tenderproof.contracts import FieldState
from app.tenderproof.fields import _evidence, extract_fields
from app.tenderproof.processing import extract_pages_isolated
from app.tenderproof.source_adapters import get_source_adapter


def supplement_fields(candidate, fields, supplements, store, settings, owner_id):
    if not supplements:
        return fields
    if candidate.source == 'ibam_open' and candidate.external_id == '364' and len(supplements) == 1:
        # IBAM Caruaru publishes Anexo I as a separate PDF.  Keep the base
        # edital provenance for fee/cronogram fields and the annex provenance
        # for every cargo-table row; never bind annex pages to the base SHA.
        from datetime import datetime, timezone
        from app.tenderproof.contracts import Artifact
        from app.tenderproof.ibam_caruaru_jobs import (
            ANEXO_I_URL,
            EXPECTED_ARTIFACT_SHA256,
            EXPECTED_ANNEX_ARTIFACT_SHA256,
            extract_caruaru_jobs,
        )
        extra = supplements[0]
        if (extra.document.kind != 'anexo'
                or extra.document.url_requested != ANEXO_I_URL
                or extra.artifact.url_requested != ANEXO_I_URL
                or extra.artifact.url_final != ANEXO_I_URL
                or extra.artifact.sha256 != EXPECTED_ANNEX_ARTIFACT_SHA256):
            raise ValueError('Anexo I IBAM Caruaru fora do vínculo documental preservado')
        adapter = get_source_adapter(candidate.source)
        adapter.validate_document_url(ANEXO_I_URL, candidate)
        content = store.load_artifact_bytes(extra.artifact)
        if (not content or len(content) != extra.artifact.byte_len
                or len(content) > settings.limits.max_download_bytes
                or hashlib.sha256(content).hexdigest() != EXPECTED_ANNEX_ARTIFACT_SHA256):
            raise ValueError('bytes do Anexo I IBAM ausentes ou hash inválido')
        pages, total, processed, truncated, errors = extract_pages_isolated(
            content, artifact_id=extra.artifact.artifact_id, owner_id=str(owner_id),
            max_bytes=settings.limits.max_download_bytes, max_pages=settings.limits.max_pages,
            reuse_completed=True,
        )
        if truncated or errors or total != processed or not pages:
            raise ValueError('Anexo I IBAM incompleto ou ilegível')
        extra.reading = {
            'processor': 'extract_pages_isolated',
            'pages': len(pages),
            'sha256': extra.artifact.sha256,
        }
        jobs = extract_caruaru_jobs(
            extra.artifact, pages, _evidence,
            source=candidate.source, external_id=candidate.external_id,
        )
        if jobs is None or jobs.state != FieldState.SUPPORTED:
            raise ValueError('quadro de cargos do Anexo I IBAM não reproduzido')

        # The fee is stated by the base edital (item 5.1.1, physical p. 8).
        # Reuse the base evidence identity and bind the exact short snippet to
        # that page/SHA; the cargo rows retain only the annex SHA evidence.
        main_evidence = next(
            (item for field in fields for item in field.evidence
             if item.document_sha256 == EXPECTED_ARTIFACT_SHA256),
            None,
        )
        if main_evidence is None:
            raise ValueError('evidência do edital-base necessária para a taxa IBAM ausente')
        fee_evidence = main_evidence.model_copy(update={
            'page_number': 8,
            'snippet': 'R$ 97,00 (noventa e sete reais)',
        })
        # The cargo rows carry proof date/time literals from the base edital,
        # not merely constants copied into the payload.  Re-open and normally
        # process the preserved base artifact so these snippets remain bound
        # to the base SHA and physical pages 3/13 on every proposal replay.
        base_bytes = store.get_blob(main_evidence.artifact_id)
        if (not base_bytes or hashlib.sha256(base_bytes).hexdigest() != EXPECTED_ARTIFACT_SHA256):
            raise ValueError('bytes do edital-base IBAM ausentes ou hash inválido')
        base_artifact = Artifact(
            artifact_id=main_evidence.artifact_id,
            sha256=EXPECTED_ARTIFACT_SHA256,
            byte_len=len(base_bytes),
            url_requested=main_evidence.source_url,
            url_final=main_evidence.source_url,
            content_type='application/pdf',
            downloaded_at=datetime.now(timezone.utc),
        )
        base_pages, base_total, base_processed, base_truncated, base_errors = extract_pages_isolated(
            base_bytes, artifact_id=base_artifact.artifact_id, owner_id=str(owner_id),
            max_bytes=settings.limits.max_download_bytes, max_pages=settings.limits.max_pages,
            reuse_completed=True,
        )
        if (base_truncated or base_errors or base_total != base_processed
                or len(base_pages) != 24):
            raise ValueError('edital-base IBAM incompleto ou ilegível')
        base_page3 = next((page for page in base_pages if page.page_number == 3), None)
        base_page13 = next((page for page in base_pages if page.page_number == 13), None)
        timezone_snippet = '1.9. Os horários estabelecidos neste Edital seguem o horário oficial de Brasília/DF.'
        morning_snippet = (
            'Data: 29 de novembro de 2026\n'
            'Abertura do portão: 8h00\n'
            'Fechamento do portão: 9h00\n'
            'Início das provas: 9h10\n'
            'Duração das provas: 4 horas'
        )
        afternoon_snippet = (
            'Data: 29 de novembro de 2026\n'
            'Abertura do portão: 15h00\n'
            'Fechamento do portão: 16h00\n'
            'Início das provas: 16h10\n'
            'Duração das provas: 4 horas'
        )
        if (base_page3 is None or timezone_snippet not in base_page3.text
                or base_page13 is None or morning_snippet not in base_page13.text
                or afternoon_snippet not in base_page13.text):
            raise ValueError('cronograma/fuso do edital-base IBAM não corroborado nas páginas 3/13')
        schedule_evidence = [
            _evidence(artifact=base_artifact, page=base_page3, snippet=timezone_snippet),
            _evidence(artifact=base_artifact, page=base_page13, snippet=morning_snippet),
            _evidence(artifact=base_artifact, page=base_page13, snippet=afternoon_snippet),
        ]
        jobs = jobs.model_copy(update={'evidence': [*jobs.evidence, fee_evidence, *schedule_evidence]})
        return [f for f in fields if f.field_name != 'cargos'] + [jobs]
    if candidate.source=='fapeg_selection' and any(extra.document.file_format=='xlsx' for extra in supplements):
        from app.tenderproof.xlsx_processing import extract_xlsx_isolated
        from app.tenderproof.contracts import ExtractedField
        adapter=get_source_adapter(candidate.source)
        for extra in supplements:
            if extra.document.file_format!='xlsx' or extra.document.kind!='anexo' or extra.document.url_requested!=extra.artifact.url_requested:
                raise ValueError('Anexo FAPEG fora do contrato de planilha')
            adapter.validate_document_url(extra.document.url_requested,candidate)
            content=store.load_artifact_bytes(extra.artifact)
            if not content or len(content)!=extra.artifact.byte_len or hashlib.sha256(content).hexdigest()!=extra.artifact.sha256:
                raise ValueError('Bytes da planilha FAPEG ausentes ou divergentes')
            extra.reading=extract_xlsx_isolated(content)
        return fields+[ExtractedField(field_name='anexos_estruturados',state=FieldState.FAILED,
            reason='Células das planilhas preservadas com origem; interpretação e conferência com edital/retificações pendentes. Vagas acadêmicas não são vagas de emprego.')]
    if candidate.source == 'cotec_open' and candidate.external_id == '32' and len(supplements) == 1:
        # COTEC publishes the cargo table as a separate, identity-bound Anexo I.
        # Keep this branch narrow: a different COTEC contest must not inherit
        # the Itacarambi transcription merely because its labels look alike.
        from app.tenderproof.cotec_itacarambi_jobs import (
            EXPECTED_ARTIFACT_SHA256,
            EXPECTED_URL,
            extract_itacarambi_jobs,
            extract_itacarambi_jobs_v2,
        )
        extra = supplements[0]
        if (extra.document.kind != 'anexo'
                or extra.document.url_requested != EXPECTED_URL
                or extra.artifact.url_requested != EXPECTED_URL
                or extra.artifact.url_final != EXPECTED_URL
                or extra.artifact.sha256 != EXPECTED_ARTIFACT_SHA256):
            raise ValueError('Anexo I COTEC fora do vínculo documental preservado')
        if not extra.document.reason_chosen.startswith("v2:"):
            # The v1 payload is historical and deliberately remains stored for
            # auditability, but its generic CR flag conflates PcD reserve with
            # broad reserve.  Never let a later approval revalidate it.
            from fastapi import HTTPException
            raise HTTPException(status_code=422, detail="superseded_document_interpretation")
        adapter = get_source_adapter(candidate.source)
        adapter.validate_document_url(EXPECTED_URL, candidate)
        content = store.load_artifact_bytes(extra.artifact)
        if (not content or len(content) != extra.artifact.byte_len
                or len(content) > settings.limits.max_download_bytes
                or hashlib.sha256(content).hexdigest() != EXPECTED_ARTIFACT_SHA256):
            raise ValueError('bytes do Anexo I COTEC ausentes ou hash inválido')
        pages, total, processed, truncated, errors = extract_pages_isolated(
            content, artifact_id=extra.artifact.artifact_id,
            owner_id=str(owner_id), max_bytes=settings.limits.max_download_bytes,
            max_pages=settings.limits.max_pages, reuse_completed=True,
        )
        if truncated or errors or total != processed or not pages:
            raise ValueError('Anexo I COTEC incompleto ou ilegível')
        extractor = (extract_itacarambi_jobs_v2
                     if extra.document.reason_chosen.startswith("v2:")
                     else extract_itacarambi_jobs)
        jobs = extractor(
            extra.artifact, pages, _evidence,
            source=candidate.source, external_id=candidate.external_id,
        )
        if jobs is None or jobs.state != FieldState.SUPPORTED:
            raise ValueError('quadro de cargos COTEC não reproduzido')
        return [f for f in fields if f.field_name != 'cargos'] + [jobs]
    if candidate.source != 'fumarc_open' or len(supplements) != 1:
        raise ValueError('conjunto adicional fora do contrato de extração')
    extra = supplements[0]
    adapter = get_source_adapter(candidate.source)
    if adapter.supplementary_documents([extra.document], None) != [extra.document]:
        raise ValueError('documento adicional não é quadro de cargos')
    if extra.document.url_requested != extra.artifact.url_requested:
        raise ValueError('artefato adicional difere do documento associado')
    for url in (extra.artifact.url_requested, extra.artifact.url_final):
        adapter.validate_document_url(url, candidate)
    content = store.load_artifact_bytes(extra.artifact)
    if (not content or len(content) != extra.artifact.byte_len
            or len(content) > settings.limits.max_download_bytes
            or hashlib.sha256(content).hexdigest() != extra.artifact.sha256):
        raise ValueError('bytes adicionais ausentes ou hash inválido')
    pages, total, processed, truncated, errors = extract_pages_isolated(content,
        artifact_id=extra.artifact.artifact_id, owner_id=str(owner_id),
        max_bytes=settings.limits.max_download_bytes, max_pages=settings.limits.max_pages)
    if truncated or errors or total != processed or not pages:
        raise ValueError('anexo incompleto ou ilegível')
    extra_fields = {f.field_name: f for f in extract_fields(candidate=candidate, artifact=extra.artifact, pages=pages)}
    main_fields = {f.field_name: f for f in fields}
    identity_evidence = []
    for key in ('orgao', 'edital_numero'):
        main, annex = main_fields.get(key), extra_fields.get(key)
        if (not main or not annex or main.state != FieldState.SUPPORTED or annex.state != FieldState.SUPPORTED
                or main.value != annex.value):
            raise ValueError('órgão ou número do anexo não coincide com o edital')
        identity_evidence.extend(main.evidence + annex.evidence)
    jobs = extra_fields.get('cargos')
    if jobs is None:
        raise ValueError('quadro de cargos não reconhecido no anexo')
    previous = main_fields.get('cargos')
    if previous and previous.state == FieldState.SUPPORTED:
        if jobs.state != FieldState.SUPPORTED or previous.value != jobs.value:
            jobs = jobs.model_copy(update={'state': FieldState.CONFLICT, 'value': None,
                'reason': 'quadro de cargos do anexo diverge do edital; revisão necessária'})
    jobs = jobs.model_copy(update={'evidence': jobs.evidence + identity_evidence})
    fees = main_fields.get('taxas_inscricao')
    if jobs.state == FieldState.SUPPORTED and fees and fees.state == FieldState.SUPPORTED:
        enriched = []
        for job in jobs.value:
            requirements = job.get('requisitos', '')
            level = ('superior' if re.match(r'^Ensino\s+Superior\b', requirements, re.I)
                     else 'medio_tecnico' if re.match(r'^Ensino\s+(Médio|Técnico)\b', requirements, re.I) else None)
            enriched.append(dict(job, taxa_inscricao=fees.value[level] if level else None))
        jobs = jobs.model_copy(update={'value': enriched, 'evidence': jobs.evidence + fees.evidence})
    return [f for f in fields if f.field_name != 'cargos'] + [jobs]
