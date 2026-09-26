import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[5]
EVIDENCE = ROOT / "docs/execucao/evidencias/T012/avancasp_open"

DOCUMENTS = [
    {
        "slug": "bbc8f6fc-a0a1-49ef-aa1d-7d5d2403f7ce",
        "sha256": "c60fcc60f0037c4f28907460cf8a60ec6832b115b28988e81d77ebbb66441637",
        "bytes": 750381,
        "pages": 48,
        "chronology": "ANEXO V - CRONOGRAMA",
    },
    {
        "slug": "6d52089a-0ad3-4a18-bef5-306c27315785",
        "sha256": "49b2137790ee4915ef3ef058e15d94bde937e8bd766840681a278b59d5eb5cfd",
        "bytes": 749582,
        "pages": 49,
        "chronology": "ANEXO VI - CRONOGRAMA",
    },
]


def _load(item):
    pdf = EVIDENCE / f"avancasp-open-272-{item['slug']}.pdf"
    pages_file = EVIDENCE / f"avancasp-open-272-{item['slug']}-pages.json"
    pages = json.loads(pages_file.read_text(encoding="utf-8"))
    return pdf, pages


def test_each_pending_document_is_the_principal_opening_edital():
    for item in DOCUMENTS:
        pdf, pages = _load(item)
        raw = pdf.read_bytes()
        assert raw.startswith(b"%PDF-")
        assert len(raw) == item["bytes"]
        assert hashlib.sha256(raw).hexdigest() == item["sha256"]
        assert len(pages["pages"]) == item["pages"]
        first = pages["pages"][0]["text"]
        assert "PREFEITURA MUNICIPAL DE CABREÚVA" in first
        assert "CONCURSO PÚBLICO 01/2026" in first
        assert "EDITAL DE ABERTURA DE INSCRIÇÕES PARA CONCURSO PÚBLICO" in first


def test_same_selection_but_distinct_revision_not_duplicate():
    loaded = [_load(item)[1] for item in DOCUMENTS]
    assert loaded[0]["sha256"] != loaded[1]["sha256"]
    assert loaded[0]["byte_len"] != loaded[1]["byte_len"]
    assert len(loaded[0]["pages"]) != len(loaded[1]["pages"])
    first_a = loaded[0]["pages"][0]["text"]
    first_b = loaded[1]["pages"][0]["text"]
    assert "CABREÚVA" in first_a and "CABREÚVA" in first_b
    assert "01/2026" in first_a and "01/2026" in first_b
    text_a = "\n".join(page["text"] for page in loaded[0]["pages"])
    text_b = "\n".join(page["text"] for page in loaded[1]["pages"])
    assert "ANEXO V - CRONOGRAMA" in text_a
    assert "ANEXO VI - CRONOGRAMA" in text_b
    assert text_a != text_b


def test_decision_keeps_both_provenance_and_does_not_promote_fields():
    decision = json.loads(
        (EVIDENCE / "document-review-decision-r1.json").read_text(encoding="utf-8")
    )
    assert decision["state"] == "AVANCASP_DOCUMENT_DECISIONS_READY_FOR_REVIEW"
    assert len(decision["pending_documents"]) == 2
    assert all(doc["duplicate_of_other_pending"] is False for doc in decision["pending_documents"])
    assert decision["dedupe_test"]["result"] == "PASS_DISTINCT_REVISIONS_SAME_SELECTION"
    assert decision["guardrails"]["fields_promoted"] is False
    assert decision["guardrails"]["prepare_called"] is False
    assert decision["guardrails"]["approve_called"] is False
