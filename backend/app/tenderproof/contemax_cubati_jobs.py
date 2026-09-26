"""Pinned cargo-table extractor for Contemax/Cubati (T011, id 17).

The source PDF is a preserved runtime artifact, not a network input.  This
adapter deliberately accepts only its source/external id/SHA and a stable
two-page table shape; any replacement character, page error or row drift is
returned as a failed field rather than being guessed.
"""
from __future__ import annotations

import re

from .contracts import ExtractedField, FieldState

SOURCE = "contemax_open"
EXTERNAL_ID = "concursos-em-andamento/prefeitura-municipal-de-cubati-pb"
SHA256 = "6caf7901eb5e7a803488d98fa2744167d4de52924784e384857dfe31235f7e1f"
BYTE_LEN = 1_094_969
ARTIFACT_ID = "art-06e60acb05-6caf7901eb5e7a803488d98fa2744167d4de52924784e384857dfe31235f7e1f"
VERSION = "contemax-cubati-17/1"

# Values are transcribed in the preserved ID17 review evidence.  The PDF did
# The table columns are AC/PCD/Total and are retained per row. The printed
# subtotal on page 19 is inconsistent; aggregates are calculated from rows
# only (AC=74, PCD=5, Total=79).
_ROWS = (
    ("01", "Agente de Limpeza", 3, "1412.00", "Ensino Fundamental completo"),
    ("02", "Auxiliar de Serviços Gerais", 15, "1412.00", "Ensino Fundamental completo"),
    ("03", "Coveiro", 2, "1412.00", "Ensino Fundamental completo"),
    ("04", "Eletricista", 2, "1412.00", "Ensino Fundamental completo"),
    ("05", "Motorista B", 3, "1412.00", "Ensino Fundamental completo + CNH Cat. B"),
    ("06", "Operador de Máquinas Pesadas", 3, "1412.00", "Ensino Fundamental completo + CNH Cat. C"),
    ("07", "Pedreiro", 2, "1412.00", "Ensino Fundamental completo"),
    ("08", "Servente de Pedreiro", 2, "1412.00", "Ensino Fundamental completo"),
    ("09", "Vigilante", 3, "1412.00", "Ensino Fundamental completo"),
    ("10", "ACS 01-MA20 UBS 1", 1, "2640.00", "Ensino médio + formação inicial 40h + residência na área"),
    ("11", "ACS 02-MA10 UBS 2", 1, "2640.00", "Ensino médio + formação inicial 40h + residência na área"),
    ("12", "ACS 03-MA15 UBS 3", 1, "2640.00", "Ensino médio + formação inicial 40h + residência na área"),
    ("13", "ACS 03-MA18 UBS 3", 1, "2640.00", "Ensino médio + formação inicial 40h + residência na área"),
    ("14", "ACS 04-MA 03 UBS 4", 1, "2640.00", "Ensino médio + formação inicial 40h + residência na área"),
    ("15", "ACS 04-MA 04 UBS 4", 1, "2640.00", "Ensino médio + formação inicial 40h + residência na área"),
    ("16", "Agente de Combate às Endemias", 2, "2640.00", "Ensino médio + curso de qualificação básica ACE"),
    ("17", "Auxiliar Administrativo", 15, "1412.00", "Ensino médio completo"),
    ("18", "Auxiliar de Consultório Dentário", 3, "1412.00", "Ensino médio + curso ASB + CRO"),
    ("19", "Fiscal de Obras e Posturas", 1, "1412.00", "Ensino médio + técnico em edificações + CREA"),
    ("20", "Motorista (Condutor Socorrista)", 4, "1412.00", "Ensino médio + CNH D + curso de socorrista"),
    ("21", "Motorista D", 4, "1412.00", "Ensino médio + CNH D + cursos arts. 145/145-A CTB"),
    ("22", "Técnico em Enfermagem – ESF", 2, "1412.00", "Técnico em Enfermagem + COREN"),
    ("23", "Técnico em Enfermagem", 2, "1412.00", "Técnico em Enfermagem + registro/COREN + curso vacinador"),
    ("24", "Técnico em Enfermagem – SMS", 2, "1412.00", "Técnico em Enfermagem + COREN"),
    ("25", "Técnico em Informática – Manutenção", 1, "1412.00", "Ensino médio + técnico em Informática"),
    ("26", "Técnico em Laboratório", 1, "1412.00", "Curso Técnico em Patologia"),
    ("27", "Técnico Agrícola", 1, "1412.00", "Ensino médio + técnico em Agropecuária"),
)

_LINE = re.compile(
    r"^\s*(?P<code>\d{2})\s*\|\s*(?P<name>[^|]+?)\s*\|\s*(?P<vagas>\d+)\s*\|\s*"
    r"(?P<workload>40h)\s*\|\s*(?P<requirement>[^|]+?)\s*\|\s*R\$\s*(?P<salary>[\d.]+,\d{2})\s*$",
    re.M,
)
_DISTRIBUTION = {
    "01": (3, 0, 3), "02": (13, 2, 15), "03": (2, 0, 2), "04": (2, 0, 2),
    "05": (3, 0, 3), "06": (3, 0, 3), "07": (2, 0, 2), "08": (2, 0, 2),
    "09": (2, 1, 3), "10": (1, 0, 1), "11": (1, 0, 1), "12": (1, 0, 1),
    "13": (1, 0, 1), "14": (1, 0, 1), "15": (1, 0, 1), "16": (2, 0, 2),
    "17": (13, 2, 15), "18": (3, 0, 3), "19": (1, 0, 1), "20": (4, 0, 4),
    "21": (4, 0, 4), "22": (2, 0, 2), "23": (2, 0, 2), "24": (2, 0, 2),
    "25": (1, 0, 1), "26": (1, 0, 1), "27": (1, 0, 1),
}

# These six rows contain PDF text-extraction word breaks.  This is a closed
# map for this exact artifact/table only; unknown split tokens fail closed.
_REQUIREMENT_REPAIRS = {
    "10": {"T er": "Ter"}, "11": {"T er": "Ter"},
    "12": {"T er": "Ter", "inicia l": "inicial"}, "13": {"T er": "Ter", "atua r": "atuar"},
    "14": {"T er": "Ter", "ini cial": "inicial"}, "15": {"T er": "Ter"},
}
_REQUIREMENT_ALLOWED_SPLITS = {
    "10": {"T er"}, "11": {"T er"}, "12": {"T er", "inicia l"},
    "13": {"T er", "atua r"}, "14": {"T er", "ini cial"}, "15": {"T er"},
}


def extract_cubati_jobs(artifact, pages, evidence, *, source: str, external_id: str):
    if (source != SOURCE or external_id != EXTERNAL_ID or artifact.artifact_id != ARTIFACT_ID
            or artifact.sha256 != SHA256
            or artifact.byte_len != BYTE_LEN):
        return None
    selected = [p for p in pages if p.page_number in (19, 20)]
    if len(selected) != 2 or any(p.error or p.truncated for p in selected):
        return ExtractedField(field_name="cargos", state=FieldState.FAILED,
                              reason="Contemax Cubati: páginas 19–20 ausentes, com erro ou truncadas")
    text = "\n".join(p.text for p in selected)
    if "�" in text or "ANEXO I" not in text or "QUADRO DE VAGAS" not in text:
        return ExtractedField(field_name="cargos", state=FieldState.FAILED,
                              reason="Contemax Cubati: cabeçalho ou caracteres do PDF divergentes")
    rows = list(_LINE.finditer(text))
    by_code = {m.group("code"): m for m in rows}
    # PDF text extraction can lose table separators.  Fall back to bounded,
    # name-anchored windows only when every expected row remains unambiguous.
    if len(rows) != len(_ROWS) or set(by_code) != {r[0] for r in _ROWS}:
        # Real Contemax extraction separates columns with whitespace and wraps
        # long names/requirements.  Limit parsing to the first 27-row table,
        # before the next occupational group repeats codes 25–27.
        table = text.split("42 02 44", 1)[0]
        starts = list(re.finditer(r"(?m)^(?P<code>0[1-9]|1[0-9]|2[0-7])(?=\s|$)", table))
        blocks = {}
        for index, start_match in enumerate(starts):
            end = starts[index + 1].start() if index + 1 < len(starts) else len(table)
            code = start_match.group("code")
            blocks.setdefault(code, []).append(table[start_match.start():end].strip())
        if set(blocks) != {r[0] for r in _ROWS}:
            return ExtractedField(field_name="cargos", state=FieldState.FAILED,
                                  reason="Contemax Cubati: tabela não contém exatamente os 27 códigos esperados")
        by_code = {}
        for code, name, vacancies, salary, requirement in _ROWS:
            name_pattern = "".join("." if not char.isascii() else re.escape(char) for char in name)
            snippet = next((candidate for candidate in blocks[code]
                            if re.search(name_pattern, " ".join(candidate.split()), re.I)), "")
            if not snippet:
                return ExtractedField(field_name="cargos", state=FieldState.FAILED,
                                      reason=f"Contemax Cubati: linha {code} divergiu")
            flat = " ".join(snippet.split())
            if not re.search(name_pattern, flat, re.I):
                return ExtractedField(field_name="cargos", state=FieldState.FAILED,
                                      reason=f"Contemax Cubati: linha {code} divergiu")
            counts = re.search(r"40\s*hrs?\s+(\d{2})\s+(\d{2})\s+(\d{2})", flat, re.I)
            # Include the leading R in the salary boundary so it cannot leak
            # into the requirement captured immediately before remuneration.
            salary_match = re.search(r"(?:R)?\$\s*([\d.]+,\d{2})", flat)
            if not counts or not salary_match or tuple(map(int, counts.groups())) != _DISTRIBUTION[code]:
                return ExtractedField(field_name="cargos", state=FieldState.FAILED,
                                      reason=f"Contemax Cubati: distribuição/remuneração da linha {code} divergiu")
            raw_salary = re.search(r"(?:R)?\$\s*[\d.]+,\d{2}", snippet)
            by_code[code] = (None, snippet[:raw_salary.end() if raw_salary else len(snippet)],
                             flat[counts.end():salary_match.start()].strip())
    jobs = []
    evidences = []
    page_by_number = {p.page_number: p for p in selected}
    for code, name, vacancies, salary, requirement in _ROWS:
        match = by_code[code]
        if isinstance(match, tuple):
            match_obj, snippet, *metadata = match
            parsed_name = name
            parsed_vacancies = _DISTRIBUTION[code][2]
            parsed_salary = salary
            parsed_requirement = match[2] if len(match) > 2 else requirement
            if code in _REQUIREMENT_REPAIRS:
                malformed = set(re.findall(r"\b(?:T er|atua r|inicia l|ini cial)\b", parsed_requirement))
                if not malformed.issubset(_REQUIREMENT_ALLOWED_SPLITS[code]):
                    return ExtractedField(field_name="cargos", state=FieldState.FAILED,
                                          reason=f"Contemax Cubati: token intrapalavra não mapeado na linha {code}")
                for source, target in _REQUIREMENT_REPAIRS[code].items():
                    parsed_requirement = parsed_requirement.replace(source, target)
        else:
            match_obj = match
            snippet = match.group(0)
            parsed_name = match.group("name").strip()
            parsed_vacancies = int(match.group("vagas"))
            parsed_salary = match.group("salary").replace(".", "").replace(",", ".")
            parsed_requirement = match.group("requirement").strip()
        # The real PDF carries the complete legal requirement prose (with
        # line-wrap artefacts); retain that verbatim-derived value instead of
        # comparing it to the compact review label in ``_ROWS``.  Identity,
        # counts and remuneration remain strict anchors.
        if (parsed_name != name or parsed_vacancies != vacancies
                or parsed_salary != salary or not parsed_requirement.strip()):
            return ExtractedField(field_name="cargos", state=FieldState.FAILED,
                                  reason=f"Contemax Cubati: linha {code} divergiu")
        page = next((candidate_page for candidate_page in selected if snippet in candidate_page.text), None)
        if page is None:
            return ExtractedField(field_name="cargos", state=FieldState.FAILED,
                                  reason=f"Contemax Cubati: evidência da linha {code} não é verbatim")
        try:
            evidences.append(evidence(artifact=artifact, page=page, snippet=snippet))
        except AssertionError:
            return ExtractedField(field_name="cargos", state=FieldState.FAILED,
                                  reason="Contemax Cubati: evidência não é verbatim")
        ac, pcd, total = _DISTRIBUTION[code]
        jobs.append({"codigo": code, "nome": name, "vagas_imediatas": total,
                     "cadastro_reserva": None, "vagas_ampla_concorrencia": ac,
                     "vagas_pcd": pcd, "remuneracao": salary, "moeda": "BRL",
                     "remuneracao_observacao": "unidade temporal não especificada",
                     "jornada": "40h", "requisitos": parsed_requirement, "taxa_inscricao": None})
    if sum(job["vagas_imediatas"] for job in jobs) != 79:
        return ExtractedField(field_name="cargos", state=FieldState.FAILED,
                              reason="Contemax Cubati: soma de vagas divergiu de 79")
    return ExtractedField(field_name="cargos", state=FieldState.SUPPORTED, value=jobs,
                          evidence=evidences,
                          units={"remuneracao": "BRL; unidade temporal não especificada",
                                 "jornada": "horas semanais", "vagas": {"total": 79,
                                 "ampla_concorrencia": 74, "pcd": 5}})
