"""Offline proof of R6 failure and signed-query R7 matching semantics."""
from app.tenderproof.document_identity import document_identity


PATH = "/publiconsult/Anexos/681/PM%20VOTUPORANGA%20-%20PS%201-2026%20-EDITAL%20DE%20CONVOCA%C3%87%C3%83O%20TAF.pdf"
TITLE = "Edital de Convocação para o Teste de Aptidão Física para o cargo Técnico em Educação X – Desenvolvimento Infantil II"


def test_r6_raw_only_fails_literal_url_and_r7_signed_query_matches():
    signed = f"https://gsistbucket.s3.amazonaws.com{PATH}?AWSAccessKeyId=KEY&Expires=123&Signature=SIG&raw=1"
    r6 = f"https://gsistbucket.s3.amazonaws.com{PATH}?raw=1"
    manifest = {"title": TITLE, "url": signed, "kind": "outro"}
    r6_doc = {"title": TITLE, "url": r6, "kind": "outro"}
    assert document_identity(r6_doc) == document_identity(manifest)
    assert r6_doc["url"] != manifest["url"]  # later server URL equality is literal
    # document_identity strips recognized AWS signature parameters, but the
    # server's later artifact URL equality check requires the full literal URL.
    assert document_identity(manifest)[3] == (("raw", "1"),)
    assert manifest["url"] == signed
