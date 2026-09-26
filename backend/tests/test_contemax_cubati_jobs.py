from pathlib import Path
import base64
import hashlib
import json

from app.tenderproof.contemax_cubati_jobs import ARTIFACT_ID, EXTERNAL_ID, SHA256, BYTE_LEN, _ROWS, extract_cubati_jobs
from app.tenderproof.contracts import Artifact, DiscoveredCandidate, PageText
from app.tenderproof.fields import extract_fields
from app.tenderproof.pdf_text import extract_pages
from app.tenderproof import publication as pub
from app.models import Source
from test_tenderproof_publication import env  # noqa: F401


def _artifact(sha=SHA256):
    return Artifact(artifact_id=ARTIFACT_ID, sha256=sha, byte_len=BYTE_LEN,
                    url_requested="preserved://t011/id17.pdf", url_final="preserved://t011/id17.pdf",
                    downloaded_at="2026-09-12T00:00:00Z")


def _evidence(**kwargs):
    from app.tenderproof.fields import _evidence
    return _evidence(**kwargs)


def _pages():
    lines = ["ANEXO I - QUADRO DE VAGAS"]
    for code, name, vacancies, salary, requirement in _ROWS:
        br = salary.replace(".", "X").replace(",", ".").replace("X", ",")
        lines.append(f"{code} | {name} | {vacancies} | 40h | {requirement} | R$ {br}")
    split = len(lines) // 2
    return [PageText(artifact_id="art-06e60acb05", page_number=19, text="\n".join(lines[:split])),
            PageText(artifact_id="art-06e60acb05", page_number=20, text="\n".join(lines[split:]))]


def test_cubati_parser_extracts_27_rows_and_79_vagas_with_aggregate_distribution():
    result = extract_cubati_jobs(_artifact(), _pages(), _evidence,
                                 source="contemax_open", external_id=EXTERNAL_ID)
    assert result.state.value == "supported"
    assert len(result.value) == 27
    assert sum(row["vagas_imediatas"] for row in result.value) == 79
    assert result.units["vagas"] == {"total": 79, "ampla_concorrencia": 74, "pcd": 5}
    assert sum(row["vagas_ampla_concorrencia"] for row in result.value) == 74
    assert sum(row["vagas_pcd"] for row in result.value) == 5
    assert sum(row["vagas_imediatas"] for row in result.value) == 79
    assert result.units["vagas"]["ampla_concorrencia"] != 75
    assert len([row["requisitos"] for row in result.value]) == 27
    assert all(row["requisitos"] and not row["requisitos"].endswith(" R") and "�" not in row["requisitos"]
               for row in result.value)
    assert all(token not in row["requisitos"] for row in result.value
               for token in ("T er", "atua r", "inicia l", "ini cial"))
    assert result.value[0]["nome"] == "Agente de Limpeza"
    assert result.value[-1]["nome"] == "Técnico Agrícola"
    assert result.value[1]["vagas_ampla_concorrencia"] == 13
    assert result.value[1]["vagas_pcd"] == 2
    assert all("�" not in evidence.snippet for evidence in result.evidence)
    assert {e.page_number for e in result.evidence} == {19, 20}


def test_cubati_parser_fails_closed_on_identity_source_or_page_drift():
    pages = _pages()
    assert extract_cubati_jobs(_artifact("0" * 64), pages, _evidence,
                               source="contemax_open", external_id=EXTERNAL_ID) is None
    assert extract_cubati_jobs(_artifact().model_copy(update={"byte_len": 0}), pages, _evidence,
                               source="contemax_open", external_id=EXTERNAL_ID) is None
    assert extract_cubati_jobs(_artifact(), pages, _evidence,
                               source="other_open", external_id="17") is None
    bad = pages[0].model_copy(update={"text": pages[0].text.replace("R$ 1412,00", "R$ 1413,00", 1)})
    result = extract_cubati_jobs(_artifact(), [bad, pages[1]], _evidence,
                                 source="contemax_open", external_id=EXTERNAL_ID)
    assert result.state.value == "failed"
    replacement = pages[0].model_copy(update={"text": pages[0].text.replace("Agente", "Agente�", 1)})
    assert extract_cubati_jobs(_artifact(), [replacement, pages[1]], _evidence,
                               source="contemax_open", external_id=EXTERNAL_ID).state.value == "failed"
    truncated = pages[1].model_copy(update={"truncated": True})
    assert extract_cubati_jobs(_artifact(), [pages[0], truncated], _evidence,
                               source="contemax_open", external_id=EXTERNAL_ID).state.value == "failed"


def test_extract_fields_routes_only_pinned_id17_targeted_jobs():
    candidate = DiscoveredCandidate(candidate_id="contemax-17", title_observed="PREFEITURA MUNICIPAL DE CUBATI-PB",
                                    detail_url_observed="https://www.contemaxconsultoria.com.br/site/concursos-em-andamento/prefeitura-municipal-de-cubati-pb", external_id=EXTERNAL_ID,
                                    observed_at="2026-09-12T00:00:00Z", source="contemax_open")
    fields = extract_fields(candidate=candidate, artifact=_artifact(), pages=_pages())
    cargos = next(field for field in fields if field.field_name == "cargos")
    assert cargos.state.value == "supported"
    assert len(cargos.value) == 27 and sum(row["vagas_imediatas"] for row in cargos.value) == 79
    assert cargos.units["vagas"]["ampla_concorrencia"] == 74


def test_cubati_parser_validates_preserved_primary_pdf():
    pdf = Path("../docs/execucao/evidencias/T011/artifacts/T011-ID17-contemax-001-2024-art-06e60acb05.pdf")
    content = pdf.read_bytes()
    assert len(content) == 1_094_969
    artifact = _artifact().model_copy(update={"byte_len": len(content)})
    pages, total, processed, truncated, errors = extract_pages(content, artifact_id=ARTIFACT_ID)
    assert (total, processed, truncated, errors) == (50, 50, False, [])
    result = extract_cubati_jobs(artifact, pages, _evidence, source="contemax_open", external_id=EXTERNAL_ID)
    assert result.state.value == "supported"
    assert len(result.value) == 27 and sum(row["vagas_imediatas"] for row in result.value) == 79
    assert [(result.value[i]["vagas_ampla_concorrencia"], result.value[i]["vagas_pcd"]) for i in (1, 8, 16)] == [(13, 2), (2, 1), (13, 2)]
    assert {e.page_number for e in result.evidence} == {19, 20}
    assert sum(row["vagas_ampla_concorrencia"] for row in result.value) == 74
    assert sum(row["vagas_pcd"] for row in result.value) == 5
    expected = {
        **{f"0{i}": "Ensino Fundamental completo" for i in range(1, 5)},
        "05": "Ensino Fundamental completo + CNH Cat. B",
        "06": "Ensino Fundamental completo + CNH Cat. C",
        "07": "Ensino Fundamental completo", "08": "Ensino Fundamental completo",
        "09": "Ensino Fundamental completo",
        "10": "Residir na área da comunidade em que atuar, desde a data da publicação do edital do processo seletivo público; Ter concluído, com aproveitamento, curso de formação inicial, com carga horária mínima de quarenta horas; (Redação dada pela Lei nº 13.595, de 2018) e ter concluído o ensino médio. (Redação dada pela Lei nº 13.595, de 2018)",
        "11": "Residir na área da comunidade em que atuar, desde a data da publicação do edital do processo seletivo público; Ter concluído, com aproveitamento, curso de formação inicial, com carga horária mínima de quarenta horas; (Redação dada pela Lei nº 13.595, de 2018) e ter concluído o ensino médio. (Redação dada pela Lei nº 13.595, de 2018)",
        "12": "Residir na área da comunidade em que atuar, desde a data da publicação do edital do processo seletivo público; Ter concluído, com aproveitamento, curso de formação inicial, com carga horária mínima de quarenta horas; (Redação dada pela Lei nº 13.595, de 2018) e ter concluído o ensino médio. (Redação dada pela Lei nº 13.595, de 2018)",
        "13": "Residir na área da comunidade em que atuar, desde a data da publicação do edital do processo seletivo público; Ter concluído, com aproveitamento, curso de formação inicial, com carga horária mínima de quarenta horas; (Redação dada pela Lei nº 13.595, de 2018) e ter concluído o ensino médio. (Redação dada pela Lei nº 13.595, de 2018)",
        "14": "Residir na área da comunidade em que atuar, desde a data da publicação do edital do processo seletivo público; Ter concluído, com aproveitamento, curso de formação inicial, com carga horária mínima de quarenta horas; (Redação dada pela Lei nº 13.595, de 2018) e ter concluído o ensino médio. (Redação dada pela Lei nº 13.595, de 2018)",
        "15": "Residir na área da comunidade em que atuar, desde a data da publicação do edital do processo seletivo público; Ter concluído, com aproveitamento, curso de formação inicial, com carga horária mínima de quarenta horas; (Redação dada pela Lei nº 13.595, de 2018) e ter concluído o ensino médio. (Redação dada pela Lei nº 13.595, de 2018)",
        "16": "Ter concluído, com aproveitamento, curso de qualificação básica para a formação de Agente de Combate às Endemias; ter concluído o ensino médio.",
        "17": "Ensino médio completo.", "18": "Ensino médio completo e curso de Auxiliar em Saúde Bucal + CRO.",
        "19": "Ensino médio completo e curso técnico em edificações + CREA",
        "20": "Ensino médio completo + CNH Categoria D + Curso de Socorrista",
        "21": "Ensino médio completo + CNH Categoria D + Ter concluído com aproveitamento os cursos especializados exigidos para o exercício do cargo conforme arts. 145 e145-A do Código de Trânsito Brasileiro",
        "22": "Curso Técnico em Enfermagem e + COREN", "23": "Curso Técnico em Enfermagem e registro + COREN e curso de Vacinador",
        "24": "Curso Técnico em Enfermagem + COREN.", "25": "Ensino médio e Curso técnico em Informática",
        "26": "Curso Técnico em Patologia.", "27": "Ensino médio completo + Curso técnico em Agropecuária.",
    }
    assert {row["codigo"]: row["requisitos"] for row in result.value} == expected


def test_real_pdf_reviewed_run_dry_run_and_isolated_proposal(env):
    db, _, user, contest, _, store = env
    pdf = Path("../docs/execucao/evidencias/T011/artifacts/T011-ID17-contemax-001-2024-art-06e60acb05.pdf")
    content = pdf.read_bytes()
    detail_url = "https://www.contemaxconsultoria.com.br/site/concursos-em-andamento/prefeitura-municipal-de-cubati-pb"
    document_url = "https://www.contemaxconsultoria.com.br/site/wp-content/uploads/2024/09/Edital-CUBATI.pdf"
    artifact = _artifact().model_copy(update={"byte_len": len(content), "url_requested": document_url, "url_final": document_url})
    pages, *_ = extract_pages(content, artifact_id=ARTIFACT_ID)
    candidate = DiscoveredCandidate(candidate_id="contemax-17", title_observed="Concurso Público n.º 001/2024 — Prefeitura Municipal de Cubati/PB",
                                    detail_url_observed=detail_url, external_id=EXTERNAL_ID,
                                    observed_at="2026-09-12T00:00:00Z", source="contemax_open")
    cargos = extract_cubati_jobs(artifact, pages, _evidence, source="contemax_open", external_id=EXTERNAL_ID)
    page1 = next(page for page in pages if page.page_number == 1)
    page2 = next(page for page in pages if page.page_number == 2)
    identity_evidence = [
        {"field_name": "titulo", "value": "Concurso Público n.º 001/2024 — Prefeitura Municipal de Cubati/PB",
         "evidence": [_evidence(artifact=artifact, page=page1, snippet="Concurso Público n.º 001/2024").model_dump(mode="json")]},
        {"field_name": "orgao", "value": "PREFEITURA MUNICIPAL DE CUBATI-PB",
         "evidence": [_evidence(artifact=artifact, page=page2, snippet="PREFEITURA MUNICIPAL DE CUBATI E ADOTA OUTRAS").model_dump(mode="json")]},
        {"field_name": "edital_numero", "value": "001/2024",
         "evidence": [_evidence(artifact=artifact, page=page1, snippet="Concurso Público n.º 001/2024").model_dump(mode="json")]},
    ]
    envelope = {"schema": "tenderproof.reviewed-run.v1", "source": "contemax_open", "concurso_id": contest.id,
                "external_id": EXTERNAL_ID, "title": candidate.title_observed, "detail_url": candidate.detail_url_observed,
                "artifact": {k: v for k, v in artifact.model_dump(mode="json").items() if v is not None} | {"content_base64": base64.b64encode(content).decode()},
                "fields": identity_evidence + [{"field_name": "cargos", "value": cargos.value, "evidence": [e.model_dump(mode="json") for e in cargos.evidence], "units": cargos.units}],
                "pending_fields": [], "reference_only": True, "owner_user_id": user.id,
                "observed_at": "2026-09-12T00:00:00Z"}
    from app.tenderproof.reviewed_run_import import import_reviewed_run, _run_id, ReviewedRun
    reviewed = ReviewedRun.model_validate(envelope)
    derived_run_id = _run_id(reviewed)
    assert derived_run_id == _run_id(reviewed)
    assert derived_run_id.startswith("tp-reviewed-")
    assert derived_run_id != "t011-reviewed-17-6caf7901"
    dry = import_reviewed_run(envelope, store, dry_run=True)
    assert dry["status"] == "validated" and dry["fields"] == ["titulo", "orgao", "edital_numero", "cargos"]
    imported = import_reviewed_run(envelope, store, dry_run=False)
    run = store.get_run(derived_run_id)
    assert imported["status"] == "imported" and run is not None
    source = db.get(Source, contest.source_id)
    source.source_type = "contemax_open"; source.name = "Contemax"
    contest.external_id = EXTERNAL_ID; contest.titulo = candidate.title_observed; contest.orgao = "Prefeitura Municipal De Cubati"
    contest.edital_numero = "001/2024"; contest.link_pagina = candidate.detail_url_observed
    eligible, blocked = pub._revalidate(run, contest, source, store)
    assert "cargos" not in blocked and len(eligible["cargos"]) == 27
    proposal = pub.create_proposal(db, run=run, concurso_id=contest.id, user=user, store=store)
    assert proposal["state"] == "proposed" and "cargos" in proposal["eligible_fields"]


def test_checked_in_reviewed_run_envelope_is_deterministic():
    path = Path("../docs/execucao/evidencias/T011/T011-reviewed-run-id17.json")
    raw = path.read_bytes()
    payload = json.loads(raw)
    from app.tenderproof.reviewed_run_import import ReviewedRun, _run_id
    model = ReviewedRun.model_validate(payload)
    assert hashlib.sha256(raw).hexdigest() == "60afc4ad5b0f8eba96def9817e04f994b9abafad3819815fd8ee392ce3182174"
    assert _run_id(model) == "tp-reviewed-b64ff5228138c8157f8c5e4960046c79"
    assert payload["owner_user_id"] == 1 and payload["reference_only"] is True
    assert [field["field_name"] for field in payload["fields"]] == ["titulo", "orgao", "edital_numero", "cargos"]
