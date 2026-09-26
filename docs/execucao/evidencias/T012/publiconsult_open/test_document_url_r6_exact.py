"""Offline proof that raw=1 is part of Publiconsult pending identity."""
from app.tenderproof.document_identity import document_identity


BASE = "https://gsistbucket.s3.amazonaws.com/publiconsult/Anexos/681/PM%20VOTUPORANGA%20-%20PS%201-2026%20-EDITAL%20DE%20CONVOCA%C3%87%C3%83O%20TAF.pdf"
EXACT = BASE + "?raw=1"
TITLE = "Edital de Convocação para o Teste de Aptidão Física para o cargo Técnico em Educação X – Desenvolvimento Infantil II"


def test_manifest_url_is_byte_exact_and_raw_query_is_not_normalized():
    old = {"title": TITLE, "url": BASE, "kind": "outro"}
    current = {"title": TITLE, "url": EXACT, "kind": "outro"}
    assert document_identity(old) != document_identity(current)
    assert document_identity(current)[2] == "/publiconsult/Anexos/681/PM%20VOTUPORANGA%20-%20PS%201-2026%20-EDITAL%20DE%20CONVOCA%C3%87%C3%83O%20TAF.pdf"
    assert document_identity(current)[3] == (("raw", "1"),)
    assert current["url"] == EXACT
    assert current["title"] == TITLE
