from pathlib import Path

from app.tenderproof.contracts import Artifact, PageText
from app.tenderproof.imeso_berizal_jobs import EXPECTED_SHA256, extract_berizal_jobs
from app.tenderproof.pdf_text import extract_pages
from app.tenderproof import publication as pub
from app.tenderproof.fields import extract_fields
from app.tenderproof.contracts import DiscoveredCandidate, DocumentCandidate
from app.models import Source
from test_tenderproof_publication import env  # noqa: F401 - isolated DB fixture


def _evidence(**kwargs):
    from app.tenderproof.fields import _evidence
    return _evidence(**kwargs)


def _inputs():
    content = (Path(__file__).parents[2] / "docs/execucao/evidencias/T010/id6.pdf").read_bytes()
    artifact = Artifact(artifact_id="id6", sha256=EXPECTED_SHA256, byte_len=len(content),
                        url_requested="https://s3.us-east-1.amazonaws.com/cdn.imeso.com.br/edital/1/139/402c39f4f7ecc38a1905e41163fdc4be.pdf",
                        url_final="https://s3.us-east-1.amazonaws.com/cdn.imeso.com.br/edital/1/139/402c39f4f7ecc38a1905e41163fdc4be.pdf",
                        downloaded_at="2026-09-08T00:00:00Z")
    pages, *_ = extract_pages(content, artifact_id="id6")
    return artifact, pages


def test_berizal_extracts_all_eleven_rows_and_literals():
    artifact, pages = _inputs()
    result = extract_berizal_jobs(artifact, pages, _evidence, source="imeso_open", external_id="139")
    assert result.state.value == "supported"
    assert len(result.value) == 11
    assert [row["vagas_imediatas"] for row in result.value] == [1] * 11
    assert [row["vagas_pcd"] for row in result.value] == [0] * 11
    assert result.value[0]["nome"].endswith("Micro Área 1 UBS Beriza")
    assert result.value[-1]["nome"].endswith("Micro Área 11 UBS Barreiros")
    assert all(row["remuneracao"] == "3242.00" and row["taxa_inscricao"] == "120.00" for row in result.value)
    assert len(result.evidence) == 11 and all(e.page_number == 22 for e in result.evidence)


def test_berizal_fails_closed_on_identity_sha_or_page_drift():
    artifact, pages = _inputs()
    assert extract_berizal_jobs(artifact, pages, _evidence, source="access_open", external_id="139") is None
    bad = artifact.model_copy(update={"sha256": "0" * 64})
    assert extract_berizal_jobs(bad, pages, _evidence, source="imeso_open", external_id="139") is None
    for byte_len in (0, 597313, 597315):
        wrong_length = artifact.model_copy(update={"byte_len": byte_len})
        assert extract_berizal_jobs(wrong_length, pages, _evidence, source="imeso_open", external_id="139") is None
    page22 = next(p for p in pages if p.page_number == 22)
    drift = page22.model_copy(update={"text": page22.text.replace("1+CR", "2+CR", 1)})
    drifted = [drift if p.page_number == 22 else p for p in pages]
    assert extract_berizal_jobs(artifact, drifted, _evidence, source="imeso_open", external_id="139").state.value == "failed"
    truncated = page22.model_copy(update={"truncated": True})
    assert extract_berizal_jobs(artifact, [truncated], _evidence, source="imeso_open", external_id="139").state.value == "failed"


def test_berizal_fields_revalidate_and_create_material_proposal(env):
    db, _, user, contest, run, store = env
    source = db.get(Source, contest.source_id)
    source.source_type = "imeso_open"
    contest.external_id = "139"
    contest.link_pagina = "https://portal.imeso.com.br/edital/ver/139"
    document_url = "https://s3.us-east-1.amazonaws.com/cdn.imeso.com.br/edital/1/139/402c39f4f7ecc38a1905e41163fdc4be.pdf"
    artifact, pages = _inputs()
    artifact.url_requested = artifact.url_final = document_url
    content = (Path(__file__).parents[2] / "docs/execucao/evidencias/T010/id6.pdf").read_bytes()
    store.save_artifact_file(artifact, content)
    candidate = DiscoveredCandidate(candidate_id="imeso-139", external_id="139",
                                    title_observed="PREFEITURA MUNICIPAL DE BERIZAL/MG",
                                    detail_url_observed=contest.link_pagina,
                                    observed_at="2026-09-12T00:00:00Z", source="imeso_open")
    run.source = "imeso_open"; run.owner_user_id = user.id
    run.candidates = [candidate]; run.selected_candidate_id = candidate.candidate_id
    run.document = DocumentCandidate(doc_id="imeso-doc-1", title="Edital 001/2026",
                                     url_requested=document_url, url_final=document_url, kind="edital")
    run.artifact = artifact
    run.fields = extract_fields(candidate=candidate, artifact=artifact, pages=pages)
    extracted = run.field_map()
    contest.orgao = extracted["orgao"].value
    contest.edital_numero = extracted["edital_numero"].value
    contest.link_edital = document_url
    eligible, blocked = pub._revalidate(run, contest, source, store)
    assert "cargos" not in blocked and len(eligible["cargos"]) == 11
    proposal = pub.create_proposal(db, run=run, concurso_id=contest.id, user=user, store=store)
    assert "cargos" in proposal["eligible_fields"]
