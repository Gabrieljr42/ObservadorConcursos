from sqlalchemy import select, func

from app.tenderproof.contracts import FieldState
from app.tenderproof.fatec_t012 import extract_fields as fatec_extract_fields
from app.tenderproof.fields import extract_fields
from app.tenderproof.store import get_store
from app.tenderproof.processing import extract_pages_isolated
from app.database import SessionLocal
from app.models import Concurso


def test_fatec_fields_parser_verbatim_and_supported():
    store = get_store()
    run = store.get_run("tp-tcj-781928dfcad75126844a68728a4c5b17-1")
    assert run is not None
    cand = next(c for c in run.candidates if c.candidate_id == run.selected_candidate_id)
    content = store.load_artifact_bytes(run.artifact)
    pages, _, _, _, errors = extract_pages_isolated(
        content, artifact_id=run.artifact.artifact_id, owner_id="t012", max_pages=75,
        max_bytes=len(content) + 1000, capacity_wait_s=30, reuse_completed=True
    )
    assert errors == []
    fields = fatec_extract_fields(candidate=cand, artifact=run.artifact, pages=pages)
    by_name = {f.field_name: f for f in fields}

    assert by_name["titulo"].state == FieldState.SUPPORTED
    assert by_name["orgao"].state == FieldState.SUPPORTED
    assert by_name["orgao"].value == "Fundação de Apoio à Tecnologia e Ciência - FATEC"
    assert by_name["edital_numero"].state == FieldState.SUPPORTED
    assert by_name["edital_numero"].value == "2026/5020028-01"
    assert by_name["inscricao_inicio"].value == "2026-04-02"
    assert by_name["inscricao_fim"].value == "2026-04-08"
    assert by_name["prova_data"].value == "2026-04-09"
    assert by_name["cargos"].state == FieldState.SUPPORTED
    assert len(by_name["cargos"].value) == 1
    assert by_name["cargos"].value[0]["nome"] == "Assistente de Laboratório"

    # Verify all evidence snippets are verbatim
    for f in fields:
        for ev in f.evidence:
            page = next(p for p in pages if p.page_number == ev.page_number)
            assert ev.snippet in page.text


def test_fatec_fields_dispatch_in_fields_py():
    store = get_store()
    run = store.get_run("tp-tcj-781928dfcad75126844a68728a4c5b17-1")
    cand = next(c for c in run.candidates if c.candidate_id == run.selected_candidate_id)
    content = store.load_artifact_bytes(run.artifact)
    pages, _, _, _, _ = extract_pages_isolated(
        content, artifact_id=run.artifact.artifact_id, owner_id="t012", max_pages=75,
        max_bytes=len(content) + 1000, capacity_wait_s=30, reuse_completed=True
    )
    dispatched = extract_fields(candidate=cand, artifact=run.artifact, pages=pages)
    by_name = {f.field_name: f for f in dispatched}

    assert by_name["orgao"].value == "Fundação de Apoio à Tecnologia e Ciência - FATEC"
    assert by_name["edital_numero"].value == "2026/5020028-01"
    assert by_name["cargos"].value[0]["nome"] == "Assistente de Laboratório"


def test_t012_milestone_40_distinct_sources_achieved():
    db = SessionLocal()
    try:
        distinct_count = db.scalar(select(func.count(func.distinct(Concurso.source_id))))
        total_concursos = db.scalar(select(func.count(Concurso.id)))
        assert distinct_count >= 40, f"Expected >= 40 distinct sources, got {distinct_count}"
        assert total_concursos >= 41, f"Expected >= 41 concursos, got {total_concursos}"

        c41 = db.get(Concurso, 41)
        assert c41 is not None
        assert c41.source_id == 74
        assert c41.external_id == "2026/5020028-01"
        assert c41.edital_numero == "2026/5020028-01"
    finally:
        db.close()


if __name__ == "__main__":
    print("Running test_fatec_fields_parser_verbatim_and_supported...")
    test_fatec_fields_parser_verbatim_and_supported()
    print("PASS")

    print("Running test_fatec_fields_dispatch_in_fields_py...")
    test_fatec_fields_dispatch_in_fields_py()
    print("PASS")

    print("Running test_t012_milestone_40_distinct_sources_achieved...")
    test_t012_milestone_40_distinct_sources_achieved()
    print("PASS")

    print("ALL 3 TESTS PASSED SUCCESSFULLY!")
