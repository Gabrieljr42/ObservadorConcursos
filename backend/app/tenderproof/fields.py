"""TenderProof Fase 2 — extração determinística de campos com evidências.

Decisão documentada: extração determinística (regex + contexto) é suficiente
para os campos-alvo do MVP; LLM não é usado por padrão. O módulo
``llm.py`` encapsula o provedor para uso futuro opt-in, sem escrita no banco
e sem autoavaliação como prova.

Regras de segurança semântica:

- O trecho (snippet) deve existir verbatim no material preservado.
- Correspondência textual é necessária mas insuficiente: o trecho deve
  sustentar o significado (ex.: data precisa de contexto de inscrição;
  valor precisa de contexto salarial, não taxa/benefício).
- Remuneração sem contexto suficiente → UNKNOWN com motivo claro. Nunca se
  transforma salário de um cargo em mínimo/máximo global sem escopo provado.
"""

from __future__ import annotations

import hashlib
import json
import re
import uuid
from pathlib import Path
from datetime import datetime, timezone

from app.tenderproof.contracts import (
    Artifact,
    DiscoveredCandidate,
    Evidence,
    EvidenceValidation,
    ExtractedField,
    FieldState,
    PageText,
    TARGET_FIELDS,
)
from app.tenderproof.validation import title_is_corroborated

METHOD = "deterministic-regex"
METHOD_VERSION = "tenderproof-fields/1.23"

_SALARY_CTX = re.compile(r"sal[aá]rio|vencimento|remunera|subs[ií]dio|provento|retribui", re.I)
_FEE_BENEFIT_CTX = re.compile(
    r"taxa(\s+de\s+inscri)?|inscri[çc][aã]o\s+R\$|aux[ií]lio|vale[\s-]?(alimenta|transporte|refei)|benef[ií]cio|gratifica|ajuda\s+de\s+custo",
    re.I,
)
_CARGO_CTX = re.compile(r"cargo|fun[çc][aã]o|emprego|carga\s+hor[aá]ria|n[ií]vel|classe|refer[eê]ncia|padr[aã]o", re.I)
_INSCR_CTX = re.compile(r"inscri[çc]", re.I)
_MONEY = re.compile(r"R\$\s*(\d{1,3}(?:\.\d{3})*|\d+),\d{2}")
_EDITAL_NUM = re.compile(r"edital\s+(?:n?[º°o.]?\s*)?(\d{1,4}/\d{4})", re.I)
_FUMARC_NOTICE = re.compile(r'^[ \t]*CONCURSO P[ÚU]BLICO[ \t]+N[º°o.]?[ \t]*(\d{1,4}/\d{4})[ \t]*$', re.I | re.M)
_DATE = re.compile(r"\b(\d{1,2})/(\d{1,2})/(\d{4})\b")
_MONTHS = {name: index for index, name in enumerate(
    ('janeiro', 'fevereiro', 'março', 'abril', 'maio', 'junho', 'julho',
     'agosto', 'setembro', 'outubro', 'novembro', 'dezembro'), 1)}
_MONTHS['marco'] = 3
_DATE_TOKEN = re.compile(
    r'\b\d{1,2}/\d{1,2}/\d{4}\b|\b\d{1,2}(?:º)?\s+de\s+(?:'
    + '|'.join(_MONTHS) + r')\s+de\s+\d{4}\b', re.I)

_DATED_NOTICE = re.compile(
    r'^[ \t]*EDITAL\s+N[º°o.]?[ \t]*(?P<number>\d{1,4})'
    r'(?:[ \t]+[–—-][ \t]+[A-ZÀ-ÿ][A-ZÀ-ÿ /.-]{1,99})?'
    r',[ \t]+DE[ \t]+(?P<date>\d{1,2}(?:º)?[ \t]+DE[ \t]+(?:'
    + '|'.join(_MONTHS) + r')[ \t]+DE[ \t]+\d{4})[ \t]*\.?[ \t]*$', re.I | re.M)


def _dated_notice_value(match):
    date = _date_value(match['date'])
    return match['number'] + '/' + date[:4] if date else None

# A complete, directly adjacent timetable row. The omitted first year is
# shared only within this explicit range; no year is borrowed from other rows.
_COMPACT_REGISTRATION = re.compile(
    r'^\s*Per[ií]odo de (?:solicita[çc][aã]o de )?inscri[çc](?:[õo]es|[aã]o)'
    r'(?:\s+e de solicita[çc][aã]o\s+de isen[çc][aã]o de taxa de inscri[çc][aã]o)?[ \t]*:?[ \t]*\n'
    r'[ \t]*(?P<start>\d{1,2}/\d{1,2})[ \t]+(?:a|at[eé])[ \t]+'
    r'(?P<end>\d{1,2}/\d{1,2}/\d{4})[ \t]*(?=\n|$)', re.I | re.M)

# Date-first timetable rows: the event label must end the same row. Optional
# line wrapping is allowed only between the two complete dates, never events.
_ROW_TIME = r'(?:(?:[01]?\d|2[0-3])h(?:[0-5]\d)?[ \t]+do[ \t]+dia[ \t]+)?'
_DATE_FIRST_REGISTRATION = re.compile(
    r'^[ \t]*' + _ROW_TIME + r'(?P<start>' + _DATE_TOKEN.pattern + r')'
    r'[ \t]+(?:a|at[eé]|[àa]s)[ \t]*(?:\r?\n[ \t]*)?'
    + _ROW_TIME + r'(?P<end>' + _DATE_TOKEN.pattern + r')'
    r'[ \t]+Per[ií]odo[ \t]+de[ \t]+inscri[çc][õo]es[ \t]*\.?[ \t]*$',
    re.I | re.M)


def _compact_dates(match):
    end = _date_value(match['end'])
    start = _date_value(match['start'] + '/' + match['end'].rsplit('/', 1)[1])
    return (start, end) if start and end and start <= end else None


def _date_value(raw):
    numeric = _DATE.fullmatch(raw)
    if numeric:
        return _parse_date_iso(*numeric.groups())
    parts = re.fullmatch(r'(\d{1,2})(?:º)?\s+de\s+([a-zç]+)\s+de\s+(\d{4})', raw, re.I)
    if parts and parts[2].lower() in _MONTHS:
        return _parse_date_iso(parts[1], str(_MONTHS[parts[2].lower()]), parts[3])
    return None


def _evidence(
    *,
    artifact: Artifact,
    page: PageText,
    snippet: str,
    json_path: str | None = None,
    ok: bool = True,
    code: str | None = None,
    message: str | None = None,
) -> Evidence:
    assert snippet in page.text, "snippet deve existir verbatim na página preservada"
    return Evidence(
        evidence_id=f"ev-{uuid.uuid4().hex[:10]}",
        artifact_id=artifact.artifact_id,
        document_sha256=artifact.sha256,
        source_url=artifact.url_final,
        page_number=page.page_number,
        snippet=snippet,
        json_path=json_path,
        method=METHOD,
        method_version=METHOD_VERSION,
        validation=EvidenceValidation(ok=ok, code=code, message=message),
)

# The municipality name in Cubati's masthead is followed by a normative
# continuation.  Keep that continuation in the verbatim evidence snippet, but
# never promote it into the canonical organization value.
_ORG_NORMATIVE_TAIL = re.compile(
    r"\s+E\s+ADOTA\s+OUTRAS(?:\s+PROVID[ÊE]NCIAS\b.*)?$", re.I | re.S,
)


def _window(text: str, start: int, end: int, radius: int = 220) -> str:
    return text[max(0, start - radius): end + radius]


def _parse_money_br(raw: str) -> str | None:
    match = _MONEY.search(raw)
    if not match:
        return None
    digits = match.group(0).replace("R$", "").strip()
    digits = digits.replace(".", "").replace(",", ".")
    try:
        return f"{float(digits):.2f}"
    except ValueError:
        return None


def _parse_date_iso(day: str, month: str, year: str) -> str | None:
    try:
        datetime(int(year), int(month), int(day))
    except ValueError:
        return None
    return f"{int(year):04d}-{int(month):02d}-{int(day):02d}"


def extract_fields(
    *,
    candidate: DiscoveredCandidate,
    artifact: Artifact,
    pages: list[PageText],
    observed_json: list | None = None,
    document: dict | None = None,
    _skip_source_dispatch: bool = False,
) -> list[ExtractedField]:
    if not any(page.text.strip() for page in pages):
        return [ExtractedField(field_name=name,state=FieldState.FAILED,
            reason='O documento não forneceu texto para extração. Processamento e conferência pendentes; isso não significa que a informação esteja ausente no PDF.')
            for name in TARGET_FIELDS]
    _ = observed_json  # reservado para evidência via json_path em evolução futura
    fields: list[ExtractedField] = []
    fields.append(_extract_titulo(candidate, artifact, pages))
    fields.append(_extract_orgao(candidate, artifact, pages))
    fields.append(_extract_edital_numero(candidate, artifact, pages))
    inicio, fim = _extract_inscricoes(candidate, artifact, pages)
    from app.tenderproof.registration_lists import extract_lists
    lists = extract_lists(artifact, pages, _evidence, _DATE_TOKEN.pattern, _date_value)
    if lists is not None:
        fields.append(lists)
        for field in (inicio, fim):
            field.state = FieldState.FAILED
            field.value = None
            field.reason = 'Inscrições organizadas em listas; consulte os períodos e condições de cada lista. Publicação como período único exige tratamento.'
            field.evidence = lists.evidence
    fields.extend([inicio, fim])
    prova = _extract_prova_data(artifact, pages)
    if candidate.source == 'idib_open' and candidate.external_id == '362':
        from app.tenderproof.idib_reriutaba_jobs import extract_reriutaba_prova
        source_prova = extract_reriutaba_prova(artifact, pages, _evidence)
        if source_prova is not None:
            prova = source_prova
    if candidate.source in ('quadrix_open', 'msconcursos_open', 'legatus_open', 'funvapi_open', 'funcern_selection', 'fgv_open', 'fcc_open', 'facet_open', 'objetiva_open', 'institutomais_open', 'ibam_open', 'consep_open', 'avancasp_open'):
        source_prova = _extract_source_prova_data(candidate, artifact, pages)
        if source_prova is not None:
            prova = source_prova
    fields.append(prova)
    fields.append(_extract_remuneracao(candidate, artifact, pages))
    if candidate.source == 'fumarc_open':
        from app.tenderproof.fumarc_fees import extract_fees
        fees = extract_fees(artifact, pages, _evidence)
        if fees is not None:
            fields.append(fees)
    targeted_jobs = None
    if candidate.source == 'jcm_open' and candidate.external_id == '268':
        from app.tenderproof.jcm_carmo_cachoeira_jobs import extract_carmo_cachoeira_jobs
        targeted_jobs = extract_carmo_cachoeira_jobs(
            artifact, pages, _evidence, source=candidate.source, external_id=candidate.external_id,
        )
        if targeted_jobs is None:
            targeted_jobs = ExtractedField(
                field_name='cargos', state=FieldState.FAILED, value=None,
                reason='transcrição específica JCM indisponível para o SHA desta versão do edital',
            )
    elif candidate.source == 'cebraspe_open' and candidate.external_id == 'CAMARA_MUNICIPAL_PONTAPORA_MS_26':
        from app.tenderproof.cebraspe_ponta_pora_jobs import extract_ponta_pora_jobs
        targeted_jobs = extract_ponta_pora_jobs(
            artifact, pages, _evidence, source=candidate.source, external_id=candidate.external_id,
        )
        if targeted_jobs is None:
            targeted_jobs = ExtractedField(
                field_name='cargos', state=FieldState.FAILED, value=None,
                reason='transcrição específica Cebraspe indisponível para o SHA desta versão do edital',
            )
    elif candidate.source == 'fepese_open' and candidate.external_id == '2026pscaxambudosul':
        from app.tenderproof.fepese_caxambu_jobs import extract_caxambu_jobs
        targeted_jobs = extract_caxambu_jobs(
            artifact, pages, _evidence, source=candidate.source, external_id=candidate.external_id,
        )
        if targeted_jobs is None:
            targeted_jobs = ExtractedField(
                field_name='cargos', state=FieldState.FAILED, value=None,
                reason='transcrição específica FEPESE indisponível para o SHA desta versão do edital',
            )
    elif candidate.source == 'consulpam_open' and candidate.external_id == '777':
        from app.tenderproof.consulpam_maranguape_jobs import extract_maranguape_jobs
        targeted_jobs = extract_maranguape_jobs(
            artifact, pages, _evidence, source=candidate.source, external_id=candidate.external_id,
        )
        if targeted_jobs is None:
            targeted_jobs = ExtractedField(
                field_name='cargos', state=FieldState.FAILED, value=None,
                reason='transcrição específica Consulpam indisponível para o SHA desta versão do edital',
            )
    elif candidate.source == 'msconcursos_open' and candidate.external_id == '48':
        from app.tenderproof.msconcursos_cris_jobs import extract_cris_jobs
        targeted_jobs = extract_cris_jobs(
            artifact, pages, _evidence, source=candidate.source, external_id=candidate.external_id,
        )
        if targeted_jobs is None:
            targeted_jobs = ExtractedField(field_name='cargos', state=FieldState.FAILED,
                reason='Transcrição CRIS indisponível para o SHA desta versão do edital.')
    elif candidate.source == 'access_open' and candidate.external_id == '183':
        from app.tenderproof.access_birigui_jobs import extract_birigui_jobs
        targeted_jobs = extract_birigui_jobs(
            artifact, pages, _evidence, source=candidate.source, external_id=candidate.external_id,
        )
    elif candidate.source == 'imeso_open' and candidate.external_id == '139':
        from app.tenderproof.imeso_berizal_jobs import extract_berizal_jobs
        targeted_jobs = extract_berizal_jobs(
            artifact, pages, _evidence, source=candidate.source, external_id=candidate.external_id,
        )
    elif candidate.source == 'contemax_open' and candidate.external_id == 'concursos-em-andamento/prefeitura-municipal-de-cubati-pb':
        from app.tenderproof.contemax_cubati_jobs import extract_cubati_jobs
        targeted_jobs = extract_cubati_jobs(
            artifact, pages, _evidence, source=candidate.source, external_id=candidate.external_id,
        )
    elif candidate.source == 'elo_open' and candidate.external_id == '129':
        # T005 Barra Longa is a byte-pinned parser.  The service supplies the
        # preserved artifact path; never downgrade to generic table parsing.
        from app.tenderproof.barra_longa_parser import parse
        try:
            if not artifact.storage_path:
                raise ValueError('artifact storage path ausente')
            stored = Path(artifact.storage_path)
            # Store snapshots persist only a basename; resolve those through
            # the canonical artifact directory, never through process CWD.
            if not stored.is_absolute():
                from app.tenderproof.store import artifact_dir
                stored = artifact_dir() / stored.name
            parsed = parse(stored.read_bytes())
            page_by_number = {page.page_number: page for page in pages}
            jobs = []
            evidences = []
            for cargo in parsed['cargos']:
                for item in cargo['evidence']:
                    page = page_by_number.get(item['page_number'])
                    if page is None:
                        raise ValueError('página de evidência ausente')
                    evidences.append(_evidence(artifact=artifact, page=page, snippet=item['snippet']))
                jobs.append({
                    'nome': cargo['nome'], 'vagas_imediatas': cargo['vagas'],
                    'cadastro_reserva': None, 'vagas_ampla_concorrencia': cargo['vagas_ampla'],
                    'vagas_pcd': cargo['vagas_pcd'], 'remuneracao': cargo['remuneracao'],
                    'moeda': 'BRL', 'remuneracao_observacao': cargo['unidade_remuneracao'],
                    'jornada': cargo['jornada'], 'requisitos': cargo['requisitos'],
                    'taxa_inscricao': cargo['taxa'],
                })
            targeted_jobs = ExtractedField(field_name='cargos', state=FieldState.SUPPORTED,
                value=jobs, evidence=evidences,
                units={'remuneracao': 'BRL/mês', 'jornada': 'horas semanais', 'vagas': {'total': len(jobs), 'pcd': 0}})
        except (OSError, ValueError, KeyError, AssertionError) as exc:
            targeted_jobs = ExtractedField(field_name='cargos', state=FieldState.FAILED,
                reason=f'T005 Barra Longa indisponível ou divergente: {exc}')
    elif candidate.source == 'fapese_selection' and candidate.external_id == '007/2026':
        # ID14 is a documentary PF/cadastro-reserva call.  The targeted parser
        # keeps the item 2.4 role labels and service-unit remuneration; it must
        # never synthesize vacancies or monthly salary.
        from app.tenderproof.fapese_pronera_parser import extract_fapese_jobs
        targeted_jobs = extract_fapese_jobs(
            artifact, pages, _evidence, source=candidate.source, external_id=candidate.external_id,
        )
    elif candidate.source == 'omni_open' and candidate.external_id == '246':
        # ID16 is likewise byte-pinned; resolve persisted basenames through
        # artifact_dir and never use the process working directory.
        from app.tenderproof.omni_osvaldo_cruz_jobs import parse
        try:
            if not artifact.storage_path:
                raise ValueError('artifact storage path ausente')
            stored = Path(artifact.storage_path)
            if not stored.is_absolute():
                from app.tenderproof.store import artifact_dir
                stored = artifact_dir() / stored.name
            parsed = parse(stored.read_bytes(), page_texts=[page.text for page in pages])
            page_by_number = {page.page_number: page for page in pages}
            jobs, evidences = [], []
            for cargo in parsed['cargos']:
                cargo_evidence = []
                for item in cargo.pop('evidence', []):
                    page = page_by_number.get(item['page_number'])
                    if page is None:
                        raise ValueError('página de evidência ausente')
                    ev = _evidence(artifact=artifact, page=page, snippet=item['snippet'])
                    cargo_evidence.append(ev)
                    evidences.append(ev)
                jobs.append(cargo)
            targeted_jobs = ExtractedField(field_name='cargos', state=FieldState.SUPPORTED,
                value=jobs, evidence=evidences,
                units={'remuneracao': 'BRL/mês', 'jornada': 'horas semanais'})
            from app.tenderproof.omni_osvaldo_cruz_jobs import extract_prova_data
            omni_prova = extract_prova_data(artifact, pages, _evidence)
            fields = [omni_prova if field.field_name == 'prova_data' else field for field in fields]
        except (OSError, ValueError, KeyError, AssertionError) as exc:
            targeted_jobs = ExtractedField(field_name='cargos', state=FieldState.FAILED,
                reason=f'OMNI/246 indisponível ou divergente: {exc}')
    elif candidate.source == 'abcp_open' and candidate.external_id == '2868':
        from app.tenderproof.abcp_garca_jobs import extract_garca_jobs
        targeted_jobs = extract_garca_jobs(
            artifact, pages, _evidence, source=candidate.source, external_id=candidate.external_id,
        )
    elif candidate.source == 'idib_open' and candidate.external_id == '362':
        from app.tenderproof.idib_reriutaba_jobs import extract_reriutaba_jobs
        targeted_jobs = extract_reriutaba_jobs(
            artifact, pages, _evidence, source=candidate.source, external_id=candidate.external_id,
        )
    elif (candidate.source in ('consulplan_open', 'institutoconsulplan_open')
          and candidate.external_id == 'unai2026'):
        from app.tenderproof.consulplan_unai_jobs import extract_unai_jobs, extract_unai_prova
        targeted_jobs = extract_unai_jobs(
            artifact, pages, _evidence, source=candidate.source, external_id=candidate.external_id,
        )
        source_prova = extract_unai_prova(
            artifact, pages, _evidence, source=candidate.source, external_id=candidate.external_id,
        )
        if source_prova is not None:
            prova = source_prova
    from app.tenderproof.job_tables import ordered_job_tables
    jobs, unresolved = ordered_job_tables(pages)
    if (candidate.source == 'abcp_open' and candidate.external_id == '2868'
            and targeted_jobs is not None and targeted_jobs.state == FieldState.FAILED):
        # A guarded targeted parser failure must not be replaced by a weaker
        # generic table interpretation.
        jobs, unresolved = [], []
    if candidate.source == 'fumarc_open':
        from app.tenderproof.fumarc_job_tables import extract_fumarc_tables
        fumarc_jobs, fumarc_unresolved = extract_fumarc_tables(pages)
        jobs.extend(fumarc_jobs)
        unresolved.extend(fumarc_unresolved)
    if candidate.source == 'fumarc_open' and not jobs and not unresolved:
        for page in pages:
            reference = re.search(r'Anexo\s+[IVX\d]+\s*[–—-]\s*Quadro\s+de\s+Cargos[^;\n]{0,220}', page.text, re.I)
            if reference:
                unresolved.append((page, 'quadro de cargos publicado em anexo separado; aquisição e interpretação do anexo pendentes'))
                break
    if candidate.source == 'jcm_open':
        from app.tenderproof.jcm_job_tables import extract_jcm_tables
        jcm_jobs, jcm_unresolved = extract_jcm_tables(pages)
        jobs.extend(jcm_jobs)
        unresolved.extend(jcm_unresolved)
    prose_jobs, prose_evidence = [], []
    if targeted_jobs is None and candidate.source == 'cebraspe_open' and unresolved and not jobs:
        from app.tenderproof.prose_jobs import extract_prose_jobs
        prose_jobs, prose_evidence, failure = extract_prose_jobs(pages)
        if failure:
            unresolved = [(page, failure) for page, _ in unresolved]
        else:
            unresolved = []
    if targeted_jobs is not None:
        fields.append(targeted_jobs)
    elif jobs or unresolved or prose_jobs:
        fields.append(ExtractedField(
            field_name='cargos',
            state=FieldState.FAILED if unresolved else FieldState.SUPPORTED,
            value=None if unresolved else prose_jobs or [job for job, _, _, _ in jobs],
            reason='Dados de cargos publicados; interpretação integral pendente: ' + '; '.join(sorted({reason for _, reason in unresolved})) if unresolved else None,
            evidence=[_evidence(artifact=artifact, page=page, snippet=snippet)
                      for _, page, header, row in jobs for snippet in (header, row)]
                     + [_evidence(artifact=artifact, page=page, snippet=snippet)
                        for page, snippet in prose_evidence],
        ))
    if targeted_jobs is None and candidate.source == 'cebraspe_open' and not any(f.field_name == 'cargos' for f in fields):
        from app.tenderproof.joint_jobs import extract_joint_jobs
        joint = extract_joint_jobs(artifact, pages, _evidence)
        if joint is not None:
            fields.append(joint)
    if candidate.source == 'faped_selection':
        from app.tenderproof.faped_fields import extract_faped_fields
        replacements = extract_faped_fields(candidate, artifact, pages, _evidence, _date_value)
        from app.tenderproof.faped_jobs import extract_jobs
        faped_jobs = extract_jobs(artifact, pages, _evidence)
        if faped_jobs is not None:
            replacements['cargos'] = faped_jobs
        fields = [replacements.get(f.field_name, f) for f in fields]
        fields.extend(f for name, f in replacements.items() if not any(existing.field_name == name for existing in fields))
        if not any(f.field_name == 'cargos' for f in fields):
            for page in pages:
                match = re.search(r'Cargo\s+N\.[º°o]\s+de Vagas\s+Carga-horária\s+Salário Base[^\n]*', page.text, re.I)
                if match:
                    fields.append(ExtractedField(field_name='cargos', state=FieldState.FAILED,
                        reason='Quadro de cargo FAPED publicado; vínculo integral de vagas, jornada e requisitos pendente',
                        evidence=[_evidence(artifact=artifact, page=page, snippet=match.group(0))]))
                    break
    # KLC's pending one-page retification is a separate documentary artifact;
    # it must never be sent through the ten-page principal-edital parser.
    if (not _skip_source_dispatch and candidate.source == 'klc_open'
            and candidate.external_id == '632'
            and artifact.sha256 == '0d16e9bc0f61000846c9828340710ee30845191704bc2c888f0d14734a278d60'):
        try:
            stored = Path(artifact.storage_path or '')
            if not stored.is_absolute():
                from app.tenderproof.store import artifact_dir
                stored = artifact_dir() / stored.name
            from app.tenderproof.klc_retificacao_t012 import dispatch as dispatch_klc_ret
            return dispatch_klc_ret(candidate=candidate, artifact=artifact, pages=pages,
                                    content=stored.read_bytes(), document=document)
        except (OSError, ValueError, KeyError, AssertionError, TypeError) as exc:
            return [ExtractedField(field_name='prova_data', state=FieldState.FAILED,
                                   reason=f'KLC retificação indisponível ou divergente: {exc}')]

    # T012 batch-2 parsers are deliberately pinned at the dispatcher boundary.
    # They may replace generic fields only for their exact source/external pair;
    # any pin failure becomes FAILED and never falls through to generic output.
    if not _skip_source_dispatch and candidate.source in {'klc_open', 'epl_open', 'publiconsult_open', 'avancasp_open', 'apta_open'}:
        expected = {
            'klc_open': '632', 'epl_open': '52', 'publiconsult_open': '681',
            'avancasp_open': '272', 'apta_open': '708',
        }[candidate.source]
        if str(candidate.external_id) != expected:
            reason = f'{candidate.source}: external_id fora do pin {expected}'
            fields = [ExtractedField(field_name=field.field_name, state=FieldState.FAILED, reason=reason)
                      for field in fields]
        elif str(candidate.external_id) == expected:
            replacements = {}
            try:
                stored = Path(artifact.storage_path or '')
                if not stored.is_absolute():
                    from app.tenderproof.store import artifact_dir
                    stored = artifact_dir() / stored.name
                content = stored.read_bytes()
                if candidate.source == 'klc_open':
                    from app.tenderproof.klc_t012 import dispatch, ARTIFACT_SHA256, ARTIFACT_BYTE_LEN, DOCUMENT_URL
                    if (artifact.sha256 != ARTIFACT_SHA256 or artifact.byte_len != ARTIFACT_BYTE_LEN
                            or artifact.url_requested != DOCUMENT_URL or artifact.url_final != DOCUMENT_URL):
                        raise ValueError('KLC artifact metadata or URL drift')
                    parsed = dispatch(candidate, artifact, pages, content=content, total_pages=len(pages))
                elif candidate.source == 'epl_open':
                    from app.tenderproof.epl_t012 import extract_identity
                    parsed = extract_identity(artifact, pages, source=candidate.source, external_id=expected)
                elif candidate.source == 'publiconsult_open':
                    from app.tenderproof.publiconsult_t012 import fields_for_run
                    page_records = [{"page_index": index, "page_number": page.page_number,
                                     "error": page.error, "truncated": page.truncated,
                                     "processing_error": bool(page.error)}
                                    for index, page in enumerate(pages)]
                    parsed, _, _ = fields_for_run(content, artifact, source=candidate.source,
                                                  external_id=expected, page_records=page_records)
                elif candidate.source == 'avancasp_open':
                    from app.tenderproof.avancasp_t012 import extract_fields as parse_fields
                    parsed = parse_fields(candidate=candidate, artifact=artifact, pages=pages)
                else:
                    from app.tenderproof.apta_aragarcas_parser import extract_identity, DETAIL_URL, DOCUMENT_URL
                    parsed = extract_identity(artifact, pages, source=candidate.source, external_id=expected,
                                              as_of=datetime.now(timezone.utc).date(),
                                              detail_url=candidate.detail_url_observed,
                                              document_url=artifact.url_final)
                replacements = {field.field_name: field for field in parsed}
                if not replacements or not any(field.state == FieldState.SUPPORTED for field in parsed):
                    raise ValueError('parser retornou campos não suportados')
            except (OSError, ValueError, KeyError, AssertionError, TypeError) as exc:
                names = ('titulo', 'orgao', 'edital_numero', 'inscricao_inicio', 'inscricao_fim', 'prova_data', 'cargos', 'remuneracao')
                for name in names:
                    replacements[name] = ExtractedField(field_name=name, state=FieldState.FAILED,
                        reason=f'{candidate.source}/{expected} indisponível ou divergente: {exc}')
            if candidate.source in {'apta_open', 'publiconsult_open'}:
                # APTA R7 is identity-only by contract: discard generic
                # remuneration/jobs/date guesses rather than exposing them as
                # reviewed output when the pinned parser proves only these 3.
                fields = [replacements[name] for name in ('titulo', 'orgao', 'edital_numero')]
            else:
                fields = [replacements.get(field.field_name, field) for field in fields]
                fields.extend(value for name, value in replacements.items()
                               if not any(field.field_name == name for field in fields))
    if candidate.source == 'fafipa_open' and candidate.external_id == '4208':
        replacements = {}
        try:
            from app.tenderproof.fafipa_t012_r4 import extract_fields as parse_fafipa
            if not artifact.storage_path:
                raise ValueError('artifact storage path ausente')
            stored = Path(artifact.storage_path)
            if not stored.is_absolute():
                from app.tenderproof.store import artifact_dir
                stored = artifact_dir() / stored.name
            parsed = parse_fafipa(artifact=artifact, pages=pages, candidate=candidate,
                                  content=stored.read_bytes())
            replacements = {field.field_name: field for field in parsed}
        except (OSError, ValueError, KeyError, AssertionError, TypeError) as exc:
            for name in ('titulo', 'orgao', 'edital_numero', 'inscricao_inicio', 'inscricao_fim', 'prova_data', 'cargos'):
                replacements[name] = ExtractedField(field_name=name, state=FieldState.FAILED,
                    reason=f'FAFIPA/4208 indisponível ou divergente: {exc}')
        fields = [replacements.get(field.field_name, field) for field in fields]
        fields.extend(value for name, value in replacements.items()
                      if not any(field.field_name == name for field in fields))
    if candidate.source == 'fatec_selection' and candidate.external_id == '2026/5020028-01':
        replacements = {}
        try:
            from app.tenderproof.fatec_t012 import extract_fields as parse_fatec
            parsed = parse_fatec(candidate=candidate, artifact=artifact, pages=pages)
            replacements = {field.field_name: field for field in parsed}
        except (OSError, ValueError, KeyError, AssertionError, TypeError) as exc:
            for name in ('titulo', 'orgao', 'edital_numero', 'inscricao_inicio', 'inscricao_fim', 'prova_data', 'cargos', 'remuneracao'):
                replacements[name] = ExtractedField(field_name=name, state=FieldState.FAILED,
                    reason=f'FATEC/2026/5020028-01 indisponível ou divergente: {exc}')
        fields = [replacements.get(field.field_name, field) for field in fields]
        fields.extend(value for name, value in replacements.items()
                      if not any(field.field_name == name for field in fields))
    if candidate.source == 'sigma_open' and candidate.external_id == '264':
        replacements = {}
        try:
            from app.tenderproof.sigma_t012 import extract_fields as parse_sigma
            parsed = parse_sigma(candidate=candidate, artifact=artifact, pages=pages)
            replacements = {field.field_name: field for field in parsed}
        except (OSError, ValueError, KeyError, AssertionError, TypeError) as exc:
            for name in ('titulo', 'orgao', 'edital_numero', 'inscricao_inicio', 'inscricao_fim', 'prova_data', 'cargos'):
                replacements[name] = ExtractedField(field_name=name, state=FieldState.FAILED,
                    reason=f'Sigma/264 indisponível ou divergente: {exc}')
        fields = [replacements.get(field.field_name, field) for field in fields]
        fields.extend(value for name, value in replacements.items()
                      if not any(field.field_name == name for field in fields))
    if candidate.source == 'idcap_open' and candidate.external_id == '248':
        replacements = {}
        try:
            from app.tenderproof.idcap_t012 import extract_fields as parse_idcap
            parsed = parse_idcap(candidate=candidate, artifact=artifact, pages=pages)
            replacements = {field.field_name: field for field in parsed}
        except (OSError, ValueError, KeyError, AssertionError, TypeError) as exc:
            for name in ('titulo', 'orgao', 'edital_numero', 'cargos'):
                replacements[name] = ExtractedField(field_name=name, state=FieldState.FAILED,
                    reason=f'IDCAP/248 indisponível ou divergente: {exc}')
        fields = [replacements.get(field.field_name, field) for field in fields]
        fields.extend(value for name, value in replacements.items()
                      if not any(field.field_name == name for field in fields))
    if candidate.source == 'uniselva_selection' and candidate.external_id == '1346':
        replacements = {}
        try:
            from app.tenderproof.uniselva_t012 import extract_fields as parse_uniselva
            parsed = parse_uniselva(candidate=candidate, artifact=artifact, pages=pages)
            replacements = {field.field_name: field for field in parsed}
        except (OSError, ValueError, KeyError, AssertionError, TypeError) as exc:
            for name in ('titulo', 'orgao', 'edital_numero', 'inscricao_inicio', 'inscricao_fim', 'cargos'):
                replacements[name] = ExtractedField(field_name=name, state=FieldState.FAILED,
                    reason=f'Uniselva/1346 indisponível ou divergente: {exc}')
        fields = [replacements.get(field.field_name, field) for field in fields]
        fields.extend(value for name, value in replacements.items()
                      if not any(field.field_name == name for field in fields))
    if candidate.source == 'funpec_selection' and candidate.external_id == 'processo-seletivo-06-2026-cuidador-em-saude':
        replacements = {}
        try:
            from app.tenderproof.funpec_t012 import extract_fields as parse_funpec
            parsed = parse_funpec(candidate=candidate, artifact=artifact, pages=pages)
            replacements = {field.field_name: field for field in parsed}
        except (OSError, ValueError, KeyError, AssertionError, TypeError) as exc:
            for name in ('titulo', 'orgao', 'edital_numero', 'inscricao_inicio', 'inscricao_fim', 'cargos'):
                replacements[name] = ExtractedField(field_name=name, state=FieldState.FAILED,
                    reason=f'FUNPEC/06-2026 indisponível ou divergente: {exc}')
        fields = [replacements.get(field.field_name, field) for field in fields]
        fields.extend(value for name, value in replacements.items()
                      if not any(field.field_name == name for field in fields))
    if candidate.source == 'cpcon_open' and candidate.external_id == 'processo-seletivo-simplificado-no-002-2026':
        replacements = {}
        try:
            from app.tenderproof.cpcon_t012 import extract_identity
            identity = extract_identity(artifact, pages, candidate)
            if identity is None or identity.state != FieldState.SUPPORTED:
                raise ValueError(identity.reason if identity is not None else 'pin de identidade rejeitado')
            evidence_by_path = {}
            for item in identity.evidence:
                evidence_by_path.setdefault(item.json_path, []).append(item)
            replacements['orgao'] = ExtractedField(field_name='orgao', state=FieldState.SUPPORTED,
                value=identity.value['orgao'], original_value=identity.value['orgao'], evidence=evidence_by_path.get('orgao', []))
            replacements['edital_numero'] = ExtractedField(field_name='edital_numero', state=FieldState.SUPPORTED,
                value=identity.value['edital_numero'], original_value=identity.value['edital_numero'], evidence=evidence_by_path.get('edital_numero', []))
        except (OSError, ValueError, KeyError, AssertionError, TypeError) as exc:
            for name in ('orgao', 'edital_numero'):
                replacements[name] = ExtractedField(field_name=name, state=FieldState.FAILED,
                    reason=f'CPCON/002 indisponível ou divergente: {exc}')
        fields = [replacements.get(field.field_name, field) for field in fields]
        fields.extend(value for name, value in replacements.items()
                      if not any(field.field_name == name for field in fields))
    if candidate.source == 'cpcon_open' and candidate.external_id == 'processo-seletivo-simplificado-no-002-2026':
        replacements = {}
        try:
            from app.tenderproof.cpcon_t012 import extract_fields as parse_cpcon
            if not artifact.storage_path:
                raise ValueError('artifact storage path ausente')
            stored = Path(artifact.storage_path)
            if not stored.is_absolute():
                from app.tenderproof.store import artifact_dir
                stored = artifact_dir() / stored.name
            parsed = parse_cpcon(artifact, pages, candidate)
            replacements = {field.field_name: field for field in parsed}
        except (OSError, ValueError, KeyError, AssertionError, TypeError) as exc:
            for name in ('titulo', 'orgao', 'edital_numero', 'cargos'):
                replacements[name] = ExtractedField(field_name=name, state=FieldState.FAILED,
                    reason=f'CPCON/002 indisponível ou divergente: {exc}')
        fields = [replacements.get(field.field_name, field) for field in fields]
        fields.extend(value for name, value in replacements.items()
                      if not any(field.field_name == name for field in fields))
    if candidate.source == 'ufu_selection' and candidate.external_id == '1843':
        # UFU/1843 is an official detail HTML fixture.  Promote only the
        # identity and timeline literals proven by its pinned parser; linked
        # edital content, fee, cargos and remuneration remain reference-only.
        replacements = {}
        try:
            from app.tenderproof.ufu_selection_parser import derive as parse_ufu
            if not artifact.storage_path:
                raise ValueError('artifact storage path ausente')
            stored = Path(artifact.storage_path)
            if not stored.is_absolute():
                from app.tenderproof.store import artifact_dir
                stored = artifact_dir() / stored.name
            from app.tenderproof.ufu_selection_parser import EXPECTED_SHA256, EXPECTED_BYTES, DETAIL_URL, DOCUMENT_URL
            if (artifact.sha256 != EXPECTED_SHA256 or artifact.byte_len != EXPECTED_BYTES
                    or artifact.url_requested != DOCUMENT_URL or artifact.url_final != DOCUMENT_URL
                    or candidate.detail_url_observed != DETAIL_URL):
                raise ValueError('UFU artifact metadata drift')
            parsed = parse_ufu(stored.read_bytes(), source=candidate.source,
                               external_id=candidate.external_id)
            def reviewed_field(name, value, evidence_keys):
                evidence = []
                for key in evidence_keys:
                    item = parsed['evidence'][key]
                    page = next((p for p in pages if p.page_number == item['page_number']), None)
                    # UFU evidence snippets are HTML-rendered text spans; the
                    # parser has already verified them after BeautifulSoup
                    # normalization, so only page identity is checked here.
                    if page is None:
                        raise ValueError(f'UFU evidência não reproduzida: {key}')
                    evidence.append(Evidence.model_validate(item))
                return ExtractedField(field_name=name, state=FieldState.SUPPORTED,
                                      value=value, original_value=value, evidence=evidence)
            replacements['titulo'] = reviewed_field('titulo', parsed['identity']['title'], ['titulo'])
            replacements['orgao'] = reviewed_field('orgao', parsed['identity']['orgao'], ['orgao'])
            replacements['edital_numero'] = reviewed_field('edital_numero', parsed['identity']['edital_numero'], ['edital_numero'])
            replacements['inscricao_inicio'] = reviewed_field('inscricao_inicio', parsed['inscricao_inicio'], ['inscricao'])
            replacements['inscricao_fim'] = reviewed_field('inscricao_fim', parsed['inscricao_fim'], ['inscricao'])
            # The pinned page proves the registration window only.  It does
            # not prove a publication date for the exam; do not manufacture
            # a missing parser key or turn that absence into failure of the
            # five supported identity/timeline fields.
        except (OSError, ValueError, KeyError, AssertionError, TypeError) as exc:
            for name in ('titulo', 'orgao', 'edital_numero', 'inscricao_inicio', 'inscricao_fim', 'prova_data'):
                replacements[name] = ExtractedField(field_name=name, state=FieldState.FAILED,
                    reason=f'UFU/1843 indisponível ou divergente: {exc}')
        fields = [replacements.get(field.field_name, field) for field in fields]
        fields.extend(value for name, value in replacements.items()
                      if not any(field.field_name == name for field in fields))
    if candidate.source == 'shdias_open' and candidate.external_id == 'MTEw/MzA4':
        # SHDias/00308 is a reviewed, byte-pinned document.  Re-run its
        # source parser on the canonical stored bytes so publication sees the
        # same orgao/edital identity that review accepted; all other sources
        # continue through the generic path above unchanged.
        replacements = {}
        try:
            from app.tenderproof.shdias_hortolandia import parse
            if not artifact.storage_path:
                raise ValueError('artifact storage path ausente')
            stored = Path(artifact.storage_path)
            if not stored.is_absolute():
                from app.tenderproof.store import artifact_dir
                stored = artifact_dir() / stored.name
            parsed = parse(stored.read_bytes())
            page_by_number = {page.page_number: page for page in pages}
            def reviewed_field(name, value, evidence_keys):
                evidence = []
                for key in evidence_keys:
                    item = parsed['evidence'][key]
                    page = page_by_number.get(item['page_number'])
                    if page is None:
                        raise ValueError('página de evidência ausente')
                    # The pinned parser validates verbatim snippets against a
                    # native pypdf replay.  Keep that exact evidence instead
                    # of re-encoding it through a potentially different
                    # extractor used by the processing cache.
                    evidence.append(Evidence.model_validate(item))
                return ExtractedField(field_name=name, state=FieldState.SUPPORTED,
                                      value=value, original_value=value, evidence=evidence)
            replacements['titulo'] = reviewed_field('titulo', parsed['identity']['title'], ['titulo'])
            replacements['orgao'] = reviewed_field('orgao', parsed['identity']['orgao'], ['orgao'])
            replacements['edital_numero'] = reviewed_field('edital_numero', parsed['identity']['edital_numero'], ['edital_numero'])
            replacements['prova_data'] = reviewed_field('prova_data', parsed['prova_data'], ['prova_data'])
            replacements['taxa'] = reviewed_field('taxa', parsed['taxa'], ['taxa'])
            replacements['remuneracao'] = reviewed_field('remuneracao', parsed['remuneracao'], ['remuneracao'])
            replacements['cargos'] = reviewed_field('cargos', parsed['cargos'], ['cargo_301', 'cargo_302'])
        except (OSError, ValueError, KeyError, AssertionError) as exc:
            for name in ('titulo', 'orgao', 'edital_numero', 'prova_data', 'taxa', 'remuneracao', 'cargos'):
                replacements[name] = ExtractedField(field_name=name, state=FieldState.FAILED,
                    reason=f'SHDias/00308 indisponível ou divergente: {exc}')
        fields = [replacements.get(field.field_name, field) for field in fields]
        fields.extend(value for name, value in replacements.items()
                      if not any(field.field_name == name for field in fields))
    from app.tenderproof.delivery_precise_schedules import extract_precise_schedule
    precise = {field.field_name: field for field in extract_precise_schedule(candidate, artifact, pages, _evidence)}
    fields = [precise.get(field.field_name, field) for field in fields]
    for field in fields:
        if field.state != FieldState.SUPPORTED:
            continue
        snippets = [e.snippet or "" for e in field.evidence]
        if field.field_name in ("inscricao_inicio", "inscricao_fim", "prova_data"):
            if field.original_value is not None:
                continue
            field.original_value = next((m.group(0) for s in snippets for m in _DATE_TOKEN.finditer(s)
                if _date_value(m.group(0)) == field.value), None)
            if field.original_value is None:
                index = 0 if field.field_name == 'inscricao_inicio' else 1
                field.original_value = next((m['start' if index == 0 else 'end']
                    for s in snippets for m in _COMPACT_REGISTRATION.finditer(s)
                    if _compact_dates(m) and _compact_dates(m)[index] == field.value), None)
        elif field.field_name == "edital_numero":
            field.original_value = next((m.group(0) for s in snippets for m in _EDITAL_NUM.finditer(s)
                if m.group(1) == field.value), None)
            if field.original_value is None:
                field.original_value = next((m.group(0) for s in snippets
                    for m in _DATED_NOTICE.finditer(s) if _dated_notice_value(m) == field.value), None)
            if field.original_value is None and candidate.source == 'fumarc_open':
                field.original_value = next((m.group(0) for s in snippets
                    for m in _FUMARC_NOTICE.finditer(s) if m[1] == field.value), None)
        elif field.field_name == "remuneracao":
            field.original_value = list(dict.fromkeys(m.group(0) for s in snippets for m in _MONEY.finditer(s)))
        elif field.field_name == "titulo":
            if field.original_value is None:
                field.original_value = candidate.title_observed
        else:
            raw = str(field.value)
            field.original_value = next((m.group(0) for s in snippets if (m := re.search(re.escape(raw), s, re.I))), None)
    return fields


def _extract_titulo(candidate, artifact, pages) -> ExtractedField:
    if candidate.source == 'consep_open' and candidate.external_id == '200':
        hint = (candidate.title_observed or '').strip()
        mojibake = 'SEBASTI\u0102\x83O'
        if mojibake in hint:
            corrected = hint.replace(mojibake, 'SEBASTIÃO')
            for page in pages:
                match = re.search(r'SEBASTIÃO\s+LEAL', page.text, re.I)
                if match:
                    return ExtractedField(
                        field_name='titulo', state=FieldState.SUPPORTED,
                        value=corrected, original_value=hint,
                        evidence=[_evidence(artifact=artifact, page=page,
                                            snippet=_window(page.text, match.start(), match.end()))],
                    )
    from app.tenderproof.cebraspe_identity import masthead
    header = masthead(candidate, pages)
    if header:
        return ExtractedField(field_name='titulo',state=FieldState.SUPPORTED,
            value=header['titulo'],original_value=header['snippet'],
            evidence=[_evidence(artifact=artifact,page=header['page'],snippet=header['snippet'])])
    hint = (candidate.title_observed or "").strip()
    if not hint:
        return ExtractedField(field_name="titulo", state=FieldState.UNKNOWN, reason="sem título observado na listagem")
    words = [w for w in re.findall(r"[A-Za-zÀ-ÿ]{4,}", hint)][:6]
    for page in pages:
        if not page.text.strip():
            continue
        hits = [w for w in words if w.lower() in page.text.lower()]
        if hits and title_is_corroborated(hint, page.text):
            idx = page.text.lower().find(hits[0].lower())
            snippet = page.text[max(0, idx - 120): idx + 200]
            canonical_hint = hint.replace("\x96", "–")
            return ExtractedField(
                field_name="titulo",
                state=FieldState.SUPPORTED,
                value=canonical_hint,
                original_value=hint,
                evidence=[_evidence(artifact=artifact, page=page, snippet=snippet)],
            )
    return ExtractedField(
        field_name="titulo",
        state=FieldState.UNKNOWN,
        reason="título observado não corroborado no texto do edital",
    )


def _extract_orgao(candidate, artifact, pages) -> ExtractedField:
    if candidate.source == 'access_open':
        # ACCESS also hosts selections issued by institutes, whose mastheads
        # do not match the municipal issuer patterns below. Require the first
        # page, a nearby selection heading and the same institution observed
        # in the official candidate title before accepting its name.
        title = ' '.join((candidate.title_observed or '').casefold().split())
        for page in pages:
            if page.page_number != 1 or page.error or page.truncated:
                continue
            lines = page.text.splitlines()[:12]
            for index, line in enumerate(lines):
                issuer = ' '.join(line.split())
                if not re.fullmatch(r'INSTITUTO\s+[A-ZÀ-Ý][A-ZÀ-Ý .\-–]{10,180}', issuer):
                    continue
                name = re.split(r'\s+[–-]\s+', issuer, maxsplit=1)[0]
                context = '\n'.join(lines[index:index + 4])
                if name.casefold() not in title or not re.search(r'\b(?:CONCURSO P[ÚU]BLICO|PROCESSO SELETIVO)\b', context):
                    continue
                return ExtractedField(field_name='orgao', state=FieldState.SUPPORTED,
                    value=issuer, evidence=[_evidence(artifact=artifact, page=page, snippet=context)])
    if candidate.source == 'fumarc_open':
        for page in pages:
            if page.page_number != 1 or page.error or page.truncated:
                continue
            header = '\n'.join(page.text.splitlines()[:12])
            match = re.search(r'^(CONSELHO REGIONAL[^\n]{5,180})\nAUTARQUIA FEDERAL\nCONCURSO P[ÚU]BLICO\b', header, re.M)
            if match:
                return ExtractedField(field_name='orgao', state=FieldState.SUPPORTED,
                    value=' '.join(match[1].split()),
                    evidence=[_evidence(artifact=artifact, page=page, snippet=match.group(0))])
    from app.tenderproof.cebraspe_identity import masthead
    header = masthead(candidate, pages)
    if header:
        return ExtractedField(field_name='orgao',state=FieldState.SUPPORTED,
            value=header['orgao'],evidence=[_evidence(artifact=artifact,page=header['page'],snippet=header['snippet'])])
    if candidate.source == 'fapese_selection':
        # The PRONERA call identifies its issuer in a foundation sentence,
        # rather than the municipal/agency masthead patterns above.
        for page in pages:
            match = re.search(
                r'\bA\s+(FUNDAÇÃO\s+DE\s+APOIO\s+À\s+PESQUISA\s+E\s+EXTENSÃO\s+DE\s+SERGIPE)\s*\(FAPESE\)',
                page.text, re.I,
            )
            if match:
                snippet = _window(page.text, match.start(), match.end())
                return ExtractedField(
                    field_name='orgao', state=FieldState.SUPPORTED,
                    value='FUNDAÇÃO DE APOIO À PESQUISA E EXTENSÃO DE SERGIPE (FAPESE)',
                    evidence=[_evidence(artifact=artifact, page=page, snippet=snippet)],
                )
    if candidate.source == 'msconcursos_open':
        for page in pages:
            match = re.search(
                r'(CONS[ÓO]RCIO\s+REGIONAL\s+INTERMUNICIPAL\s+DE\s+SA[ÚU]DE\s*[–-]\s*CRIS)',
                page.text, re.I,
            )
            if match:
                snippet = _window(page.text, match.start(), match.end())
                value = re.sub(r'\s+', ' ', match.group(1)).strip()
                value = re.sub(r'\s*[-–]\s*', ' - ', value)
                return ExtractedField(
                    field_name='orgao', state=FieldState.SUPPORTED,
                    value=value, evidence=[_evidence(artifact=artifact, page=page, snippet=snippet)],
                )
    for page in pages:
        match = re.search(
            r"(PREFEITURA\s+MUNICIPAL\s+DE\s+[A-ZÀ-ÿ][A-ZÀ-ÿ .\-]{2,60}|C[ÂA]MARA\s+MUNICIPAL\s+DE\s+[A-ZÀ-ÿ][A-ZÀ-ÿ .\-]{2,60}|MUNIC[ÍI]PIO\s+DE\s+[A-ZÀ-ÿ][A-ZÀ-ÿ .\-]{2,60})",
            page.text,
        )
        if match:
            snippet = _window(page.text, match.start(), match.end())
            # A flattened masthead can put the selection heading on the same
            # line as the issuer. It is not part of the municipality's name.
            issuer = re.split(r"\s+(?:CONCURSO\s+P[ÚU]BLICO|PROCESSO\s+SELETIVO|EDITAL)\b",
                              match.group(0), maxsplit=1)[0]
            issuer = _ORG_NORMATIVE_TAIL.sub("", issuer).strip()
            value = " ".join(issuer.split()).title()
            return ExtractedField(
                field_name="orgao",
                state=FieldState.SUPPORTED,
                value=value,
                evidence=[_evidence(artifact=artifact, page=page, snippet=snippet)],
            )
    return ExtractedField(
        field_name="orgao", state=FieldState.UNKNOWN, reason="órgão não identificado com contexto suficiente"
    )


def _extract_edital_numero(candidate, artifact, pages) -> ExtractedField:
    hits: list[tuple[PageText, str, str]] = []
    dated_principal = []
    for page in pages:
        if page.page_number == 1:
            if candidate.source == 'fumarc_open' and not page.error and not page.truncated:
                for match in _FUMARC_NOTICE.finditer('\n'.join(page.text.splitlines()[:12])):
                    dated_principal.append(match[1])
                    hits.append((page, match[1], match.group(0)))
            for match in _DATED_NOTICE.finditer(page.text):
                value = _dated_notice_value(match)
                if value:
                    dated_principal.append(value)
                    hits.append((page, value, match.group(0)))
        for match in _EDITAL_NUM.finditer(page.text):
            snippet = _window(page.text, match.start(), match.end())
            hits.append((page, match.group(1), snippet))
    if not hits:
        return ExtractedField(
            field_name="edital_numero", state=FieldState.UNKNOWN, reason="número do edital não observado"
        )
    distinct = sorted({h[1] for h in hits})
    # Principal identification in a heading on the first physical page.
    principal = list(dated_principal)
    for page in pages:
        if page.page_number == 1:
            for line in page.text.splitlines():
                match = _EDITAL_NUM.match(line.strip())
                if match:
                    principal.append(match[1])
    if len(set(principal)) == 1:
        hits = [h for h in hits if h[1] == principal[0]]
        distinct = [principal[0]]
    if len(distinct) > 1:
        page, _, snippet = hits[0]
        return ExtractedField(
            field_name="edital_numero",
            state=FieldState.CONFLICT,
            reason=f"números conflitantes no documento: {', '.join(distinct)}",
            evidence=[_evidence(artifact=artifact, page=page, snippet=snippet, ok=False, code="conflict")],
        )
    page, numero, snippet = hits[0]
    return ExtractedField(
        field_name="edital_numero",
        state=FieldState.SUPPORTED,
        value=numero,
        evidence=[_evidence(artifact=artifact, page=page, snippet=snippet)],
    )


def _extract_inscricoes(candidate, artifact, pages) -> tuple[ExtractedField, ExtractedField]:
    if candidate.source == 'fapese_selection':
        # FAPESE's 2026 call places the registration period in a split table
        # row (item 9.2), with the label and dates on separate text lines.
        # Keep this contract source-specific so dates from appeals, interviews
        # and result publication cannot be mistaken for the registration span.
        row = re.compile(
            r'9\.2\s+Inscri[çc][ãa]o\s+(?P<start>\d{2}/\d{2}/\d{4})\s+a\s+'
            r'(?P<end>\d{2}/\d{2}/\d{4})', re.I | re.S,
        )
        found = []
        for page in pages:
            match = row.search(page.text)
            if match:
                dates = (_date_value(match['start']), _date_value(match['end']))
                found.append((page, dates, match.group(0)))
        if found:
            pairs = {tuple(item[1]) for item in found}
            page, dates, snippet = found[0]
            # Keep a stable ASCII prefix because this preserved FAPESE PDF is
            # decoded with replacement glyphs by some pypdf builds; the full
            # row remains validated above and the parser pins the date pair.
            stable_snippet = '9.2 Ins'
            valid = len(pairs) == 1 and all(dates) and dates[0] <= dates[1]
            return tuple(ExtractedField(
                field_name=name, state=FieldState.SUPPORTED if valid else FieldState.CONFLICT,
                value=dates[i] if valid else None,
                reason=None if valid else 'períodos explícitos de inscrição conflitantes ou inválidos',
                evidence=[_evidence(artifact=artifact, page=p, snippet=stable_snippet, ok=valid,
                                     code=None if valid else 'conflict') for p, _, s in found],
            ) for i, name in enumerate(('inscricao_inicio', 'inscricao_fim')))
    source_row = None
    if candidate.source == 'quadrix_open':
        source_row = re.compile(
            r'Per[ií]odo\s+de\s+solicita[çc][aã]o\s+de\s+inscri[çc][aã]o'
            r'[^\d]{0,260}(?P<start>\d{1,2}/\d{1,2})\s+a\s+'
            r'(?P<end>\d{1,2}/\d{1,2}/\d{4})', re.I | re.S,
        )
    elif candidate.source == 'msconcursos_open':
        source_row = re.compile(
            r'Per[ií]odo\s+de\s+inscri[çc][oõ]es?\s*[.:]?\s*'
            r'(?P<start>\d{1,2}/\d{1,2}/\d{4})\s+a\s+'
            r'(?P<end>\d{1,2}/\d{1,2}/\d{4})', re.I | re.S,
        )
    elif candidate.source == 'legatus_open':
        source_row = re.compile(
            r'per[ií]odo\s+de\s+(?P<start>\d{1,2}\s+de\s+(?:' + '|'.join(_MONTHS) + r'))\s+a\s+'
            r'(?P<end>\d{1,2}\s+de\s+(?:' + '|'.join(_MONTHS) + r'))\s+de\s+(?P<year>\d{4})', re.I,
        )
    elif candidate.source == 'funvapi_open':
        source_row = re.compile(
            r'inscri[çc][õo]es[\s\S]{0,500}?do\s+dia\s+(?P<start>' + _DATE_TOKEN.pattern + r')[\s\S]{0,220}?do\s+dia\s+(?P<end>' + _DATE_TOKEN.pattern + r')', re.I,
        )
    elif candidate.source == 'funcern_selection':
        source_row = re.compile(
            r'\binscri[çc][õo]es\s+(?P<start>\d{1,2}/\d{1,2}/\d{4})\s+a\s+(?P<end>\d{1,2}/\d{1,2}/\d{4})', re.I,
        )
    elif candidate.source == 'fgv_open':
        source_row = re.compile(
            r'inscri[çc][õo]es[\s\S]{0,140}?per[ií]odo\s+de\s+(?P<start>' + _DATE_TOKEN.pattern + r')\s+a\s+(?P<end>' + _DATE_TOKEN.pattern + r')', re.I,
        )
    elif candidate.source == 'fcc_open':
        source_row = re.compile(
            r'inscri[çc][õo]es\s+ficar[aã]o\s+abertas[\s\S]{0,320}?do\s+dia\s+(?P<start>\d{1,2}/\d{1,2}/\d{4})[\s\S]{0,100}?do\s+dia\s+(?P<end>\d{1,2}/\d{1,2}/\d{4})', re.I,
        )
    elif candidate.source == 'facet_open':
        source_row = re.compile(
            r'inscri[çc][õo]es[\s\S]{0,200}?(?P<start>\d{1,2}\s+de\s+(?:' + '|'.join(_MONTHS) + r'))\s+a\s+'
            r'(?P<end>\d{1,2}\s+de\s+(?:' + '|'.join(_MONTHS) + r'))\s+de\s+(?P<year>\d{4})', re.I,
        )
    elif candidate.source == 'consep_open':
        source_row = re.compile(
            r'As\s+inscri[çc][õo]es\s+ser[aã]o\s+realizadas\s+no\s+per[ií]odo\s+de\s+'
            r'(?P<sd>\d{1,2})\s+a\s+(?P<ed>\d{1,2})\s+de\s+janeiro\s+de\s+(?P<year>\d{4})', re.I,
        )
    elif candidate.source == 'avancasp_open':
        source_row = re.compile(
            r'Per[ií]odo\s+de\s+Inscri[çc][õo]es[\s\S]{0,100}?(?P<start>\d{1,2}/\d{1,2})\s+a\s+'
            r'(?P<end>\d{1,2}/\d{1,2}/\d{4})', re.I,
        )
    elif candidate.source == 'objetiva_open':
        source_row = re.compile(
            r'(?P<start>' + _DATE_TOKEN.pattern + r')\s+Abertura\s+do\s+per[ií]odo\s+para\s+solicita[çc][aã]o\s+de\s+inscri[çc][aã]o'
            r'[\s\S]{0,1400}?(?P<end>' + _DATE_TOKEN.pattern + r')\s+Encerramento\s+do\s+per[ií]odo\s+para\s+solicita[çc][aã]o\s+de\s+inscri[çc][aã]o', re.I,
        )
    elif candidate.source == 'institutomais_open':
        source_row = re.compile(
            r'no\s+per[ií]odo\s+de\s+(?P<sd>\d{1,2})\s+de\s+(?P<sm>' + '|'.join(_MONTHS) + r')\s+a\s+'
            r'(?P<ed>\d{1,2})\s+de\s+(?P<em>' + '|'.join(_MONTHS) + r')\s+de\s+(?P<year>\d{4})', re.I,
        )
    elif candidate.source == 'ibam_open':
        source_row = re.compile(
            r'inscri[çc][õo]es\s+ser[aã]o\s+realizadas\s+no\s+per[ií]odo\s+de\s+'
            r'(?P<sd>\d{1,2})/(?P<sm>\d{1,2})\s+a\s+(?P<ed>\d{1,2})/(?P<em>\d{1,2})/(?P<year>\d{2,4})', re.I,
        )
    if source_row is not None:
        found = []
        for page in pages:
            for match in source_row.finditer(page.text):
                if candidate.source == 'institutomais_open':
                    year = match['year']
                    start = _parse_date_iso(match['sd'], str(_MONTHS[match['sm'].lower()]), year)
                    end = _parse_date_iso(match['ed'], str(_MONTHS[match['em'].lower()]), year)
                    if start and end:
                        found.append((page, (start, end), match.group(0)))
                    continue
                if candidate.source == 'ibam_open':
                    year = match['year'] if len(match['year']) == 4 else '20' + match['year']
                    start = _parse_date_iso(match['sd'], match['sm'], year)
                    end = _parse_date_iso(match['ed'], match['em'], year)
                    if start and end:
                        found.append((page, (start, end), match.group(0)))
                    continue
                if candidate.source == 'consep_open':
                    start = _parse_date_iso(match['sd'], '1', match['year'])
                    end = _parse_date_iso(match['ed'], '1', match['year'])
                    if start and end:
                        found.append((page, (start, end), match.group(0)))
                    continue
                start_raw = match['start']
                year = match.groupdict().get('year')
                if year and not re.search(r'\d{4}', start_raw):
                    start_raw = start_raw + ' de ' + year
                if '/' not in start_raw or len(start_raw.split('/')) != 2:
                    start = _date_value(start_raw)
                else:
                    start = _date_value(start_raw + '/' + match['end'].rsplit('/', 1)[1])
                end_raw = match['end']
                if year and not re.search(r'\d{4}', end_raw):
                    end_raw = end_raw + ' de ' + year
                end = _date_value(end_raw)
                if start and end:
                    found.append((page, (start, end), match.group(0)))
        if found:
            pairs = {tuple(item[1]) for item in found}
            page, dates, snippet = found[0]
            valid = len(pairs) == 1 and dates[0] <= dates[1]
            return tuple(ExtractedField(
                field_name=name, state=FieldState.SUPPORTED if valid else FieldState.CONFLICT,
                value=dates[i] if valid else None,
                reason=None if valid else 'períodos específicos de inscrição conflitantes ou inválidos',
                evidence=[_evidence(artifact=artifact, page=p, snippet=s, ok=valid,
                                    code=None if valid else 'conflict') for p, _, s in found],
            ) for i, name in enumerate(('inscricao_inicio', 'inscricao_fim')))
    # Prefer a direct registration clause; payment, exemptions and appeals are
    # different events even if the word inscrição occurs nearby.
    direct = []
    clause = re.compile(
        r"(?:(?:per[ií]odo\s+de\s+inscri[çc][õo]es\s*:)|"
        r"(?:as\s+)?inscri[çc][õo]es\s+(?:estar[aã]o\s+abertas|"
        r"(?:dever[aã]o|poder[aã]o)\s+ser\s+(?:realizadas|efetuadas)|ser[aã]o\s+(?:realizadas|efetuadas)|de\s+))"
        r"(?:[\s\S]{0,380}?)(?:" + _DATE_TOKEN.pattern + r")"
        r"(?:[\s\S]{0,70}?)(?:" + _DATE_TOKEN.pattern + r")", re.I)
    for page in pages:
        for match in _DATE_FIRST_REGISTRATION.finditer(page.text):
            dates = [_date_value(match['start']), _date_value(match['end'])]
            direct.append((page, dates, match.group(0)))
        for match in _COMPACT_REGISTRATION.finditer(page.text):
            compact_dates = _compact_dates(match)
            direct.append((page, compact_dates or (None, None), match.group(0)))
        for match in clause.finditer(page.text):
            snippet = match.group(0)
            prefix = re.split(r"[.\n]", page.text[max(0, match.start()-100):match.start()])[-1]
            if re.search(r"isen[çc]|recurso|pagamento|deferid|resultado|prova", prefix + snippet, re.I):
                continue
            tokens = list(_DATE_TOKEN.finditer(snippet))
            if len(tokens) != 2 or not re.match(r'^\s*(?:a|ao|até|e|às)\b',
                    snippet[tokens[0].end():tokens[1].start()], re.I):
                continue
            dates = [_date_value(m.group(0)) for m in tokens]
            if len(dates) == 2:
                direct.append((page, dates, snippet))
    if direct:
        if any(p.error or p.truncated or not all(dates) for p, dates, _ in direct):
            return tuple(ExtractedField(field_name=name, state=FieldState.FAILED,
                reason='Período de inscrição publicado, mas data ou página inválida/incompleta; interpretação pendente',
                evidence=[_evidence(artifact=artifact,page=p,snippet=s,ok=False,code='incomplete_registration') for p,_,s in direct])
                for name in ('inscricao_inicio','inscricao_fim'))
        pairs = {tuple(item[1]) for item in direct}
        page, dates, snippet = direct[0]
        valid = len(pairs) == 1 and dates[0] <= dates[1]
        return tuple(ExtractedField(field_name=name,
            state=FieldState.SUPPORTED if valid else FieldState.CONFLICT,
            value=dates[i] if valid else None,
            reason=None if valid else "períodos explícitos de inscrição conflitantes",
            evidence=[_evidence(artifact=artifact, page=p, snippet=s, ok=valid,
                                code=None if valid else "conflict") for p, _, s in direct])
            for i, name in enumerate(("inscricao_inicio", "inscricao_fim")))
    return tuple(ExtractedField(field_name=name, state=FieldState.UNKNOWN,
        reason="período direto de inscrição não identificado; datas de outras etapas não são inscrições")
        for name in ("inscricao_inicio", "inscricao_fim"))


def _extract_prova_data(artifact, pages):
    # A complete timetable event, not publication of exam locations/results.
    row = re.compile(r'^[ \t]*(?P<date>' + _DATE_TOKEN.pattern + r')'
        r'[ \t]+Aplica[çc][aã]o[ \t]+da[ \t]+prova[ \t]+objetiva[ \t]*[;.]?[ \t]*$', re.I | re.M)
    event_first = re.compile(r'^[ \t]*Aplica[çc][aã]o[ \t]+da[ \t]+prova[ \t]+objetiva'
        r'[ \t]+(?P<date>' + _DATE_TOKEN.pattern + r')[ \t]*[;.]?[ \t]*$', re.I | re.M)
    found = []
    for page in pages:
        for pattern in (row, event_first):
            for match in pattern.finditer(page.text):
                value = _date_value(match['date'])
                found.append((page, match.group(0), value))
    if not found:
        return ExtractedField(field_name='prova_data',state=FieldState.UNKNOWN,
            reason='data de aplicação da prova não identificada em cronograma compatível; requer conferência')
    if any(not value or p.truncated or p.error for p, _, value in found):
        return ExtractedField(field_name='prova_data',state=FieldState.FAILED,
            reason='data ou página do cronograma inválida/incompleta; conferência pendente')
    valid = len({value for _, _, value in found}) == 1
    return ExtractedField(field_name='prova_data',state=FieldState.SUPPORTED if valid else FieldState.CONFLICT,
        value=found[0][2] if valid else None,
        reason=None if valid else 'datas distintas de aplicação; não há data única comprovada',
        evidence=[_evidence(artifact=artifact,page=p,snippet=s,ok=valid,
        code=None if valid else 'conflict') for p,s,_ in found])


def _extract_source_prova_data(candidate, artifact, pages):
    patterns = []
    if candidate.source == 'quadrix_open':
        patterns.append(re.compile(
            r'Aplica[çc][aã]o\s+das\s+provas\s+objetiva\s+e\s+discursiva'
            r'[^\d]{0,180}(?P<date>' + _DATE_TOKEN.pattern + r')', re.I | re.S,
        ))
    elif candidate.source == 'msconcursos_open':
        patterns.append(re.compile(
            r'Realiza[çc][aã]o\s+da\s+prova\s+objetiva\s*[.:]?\s*'
            r'(?P<date>' + _DATE_TOKEN.pattern + r')', re.I | re.S,
        ))
    elif candidate.source == 'legatus_open':
        patterns.append(re.compile(
            r'prova\s+escrita\s+objetiva\s+ser[aá]\s+realizada\s+na\s+data\s+prevista\s+de\s*'
            r'(?P<date>' + _DATE_TOKEN.pattern + r')', re.I | re.S,
        ))
    elif candidate.source == 'funvapi_open':
        patterns.append(re.compile(
            r'aplica[çc][aã]o\s+da\s+prova\s+escrita\s+objetiva\s+e\s+prova\s+de\s+t[ií]tulos[\s\S]{0,300}?'
            r'(?P<date>\d{1,2}[./]\d{1,2}[./]\d{4})', re.I,
        ))
    elif candidate.source == 'funcern_selection':
        patterns.append(re.compile(
            r'aplica[çc][aã]o\s+da\s+prova\s+escrita\s*'
            r'(?P<date>' + _DATE_TOKEN.pattern + r')', re.I | re.S,
        ))
    elif candidate.source == 'fgv_open':
        patterns.append(re.compile(
            r'prova\s+objetiva[\s\S]{0,180}?realizada\s+na\s+data\s+prov[aá]vel\s+de\s*'
            r'(?P<date>' + _DATE_TOKEN.pattern + r')', re.I,
        ))
    elif candidate.source == 'fcc_open':
        patterns.append(re.compile(
            r'previs[aã]o\s+de\s+aplica[çc][aã]o\s+para\s+o\s+dia\s*'
            r'(?P<date>\d{1,2}/\d{1,2}/\d{4})', re.I,
        ))
    elif candidate.source == 'facet_open':
        patterns.append(re.compile(
            r'prova\s+est[aá]\s+prevista\s+para\s+ser\s+realizada\s+em\s*'
            r'(?P<date>' + _DATE_TOKEN.pattern + r')', re.I,
        ))
    elif candidate.source == 'consep_open':
        patterns.append(re.compile(
            r'Aplica[çc][aã]o\s+da\s+Prova\s+Objetiva\s+(?P<date>\d{1,2}[./]\d{1,2}[./]\d{4})', re.I,
        ))
    elif candidate.source == 'avancasp_open':
        patterns.append(re.compile(
            r'(?P<date>\d{1,2}/\d{1,2}/\d{4})\s+Realiza[çc][aã]o\s+da\s+Prova\s+Objetiva', re.I,
        ))
    elif candidate.source == 'institutomais_open':
        patterns.append(re.compile(
            r'(?P<date>' + _DATE_TOKEN.pattern + r')\s+Aplica[çc][aã]o\s+das\s+Provas\s+Objetivas\s+e\s+Dissertativa', re.I,
        ))
    elif candidate.source == 'ibam_open':
        patterns.append(re.compile(
            r'Data:\s*(?P<date>' + _DATE_TOKEN.pattern + r')', re.I,
        ))
    found = []
    for page in pages:
        for pattern in patterns:
            for match in pattern.finditer(page.text):
                value = _date_value(match['date'].replace('.', '/'))
                if value:
                    found.append((page, match.group(0), value))
    if not found:
        return None
    valid = len({value for _, _, value in found}) == 1
    return ExtractedField(
        field_name='prova_data', state=FieldState.SUPPORTED if valid else FieldState.CONFLICT,
        value=found[0][2] if valid else None,
        reason=None if valid else 'datas distintas de aplicação; não há data única comprovada',
        evidence=[_evidence(artifact=artifact, page=p, snippet=s, ok=valid,
                            code=None if valid else 'conflict') for p, s, _ in found],
    )


def _extract_remuneracao(candidate, artifact, pages) -> ExtractedField:
    observations: list[tuple[PageText, str, str, str]] = []  # (page, normalized, snippet, escopo)
    for page in pages:
        # Flattened PDF tables lose column associations. A page mixing fee or
        # benefit headers with salaries cannot prove which column a number came
        # from via a nearby text window. Preserve unknown instead of fee-as-pay.
        if _FEE_BENEFIT_CTX.search(page.text):
            continue
        for match in _MONEY.finditer(page.text):
            snippet = _window(page.text, match.start(), match.end(), radius=260)
            has_salary = bool(_SALARY_CTX.search(snippet))
            has_fee = bool(_FEE_BENEFIT_CTX.search(snippet))
            has_cargo = bool(_CARGO_CTX.search(snippet))
            if not has_salary or not has_cargo or has_fee:
                continue  # contexto insuficiente ou ambíguo (taxa/benefício)
            normalized = _parse_money_br(match.group(0))
            if not normalized:
                continue
            cargo_match = _CARGO_CTX.search(snippet)
            escopo = "cargo mencionado no contexto"
            if cargo_match:
                escopo = " ".join(snippet[max(0, cargo_match.start() - 60): cargo_match.end() + 80].split())
            observations.append((page, normalized, snippet, escopo))
    if not observations:
        return ExtractedField(
            field_name="remuneracao",
            state=FieldState.UNKNOWN,
            reason="remuneração sem contexto suficiente para distinguir salário de taxa/benefício",
        )
    # Não colapsar em min/max global sem escopo provado: devolve observações com escopo.
    valores = sorted({o[1] for o in observations})
    first = observations[0]
    value = {
        "valores_observados": valores,
        "escopo": first[3][:300],
        "nota": "Valores por cargo conforme contexto; não inferir mínimo/máximo global.",
    }
    return ExtractedField(
        field_name="remuneracao",
        state=FieldState.SUPPORTED,
        value=value,
        evidence=[_evidence(artifact=artifact, page=observation[0], snippet=observation[2]) for observation in observations],
    )


def semantic_hash(fields: list[ExtractedField]) -> str:
    """Hash semântico estável: só depende dos dados, nunca de sessão/tempo/URL.

    IDs de sessão, timestamps e URLs temporárias não alteram este hash.
    """
    canonical = [
        {
            "field": f.field_name,
            "state": f.state.value,
            "value": _canon_value(f.value),
        }
        for f in sorted(fields, key=lambda item: item.field_name)
    ]
    raw = json.dumps(canonical, ensure_ascii=False, sort_keys=True, default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _canon_value(value) -> str:
    if value is None:
        return ""
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)
    return str(value).strip()
