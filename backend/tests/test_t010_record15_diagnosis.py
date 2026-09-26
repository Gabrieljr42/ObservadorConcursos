"""Read-only reconstruction of the T010 record 15 semantic 422."""
import hashlib
from datetime import datetime, timezone
from pathlib import Path

import pytest
from sqlalchemy import select
from fastapi import HTTPException

from app.models import Source
from app.tenderproof import canonical
from app.tenderproof.contracts import DiscoveredCandidate, DocumentCandidate
from app.tenderproof.source_adapters import get_source_adapter
from app.tenderproof.pdf_text import extract_pages
from app.tenderproof.fields import extract_fields
from test_tenderproof_publication import env


RUN_ID = 'tp-tcj-321b30660a7e58fa918a4fb2839e6cd9-1'
DETAIL_URL = 'https://portal.ibade.selecao.site/edital/ver/99'
DOCUMENT_URL = 'https://s3.sa-east-1.amazonaws.com/cdn-ibade.selecao.site/edital/1/99/0e8c21c11595274c16807ae0bc0eb1c1.pdf?X-Amz-Content-Sha256=UNSIGNED-PAYLOAD&X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=AKIAUIMKZHQL6G7M4UZU%2F20260909%2Fsa-east-1%2Fs3%2Faws4_request&X-Amz-Date=20260909T034212Z&X-Amz-SignedHeaders=host&X-Amz-Expires=600&X-Amz-Signature=00242ff5a7cc0cf64091a51749f6213fddcbfc77a5cc6e4fcb0ea2ee11178cf1'


def test_record15_reconstruction_reports_semantic_guard(env):
    db, _, _, contest, run, store = env
    raw = (Path(__file__).parents[2] / 'docs' / 'execucao' / 'evidencias' / 'T010' / 'id15.pdf').read_bytes()
    source = db.get(Source, contest.source_id)
    source.source_type = 'ibade_open'
    contest.external_id = '99'
    contest.titulo = 'PREFEITURA DE FLORIANÓPOLIS/SC'
    contest.orgao = 'Prefeitura Municipal De Florianópolis'
    contest.edital_numero = '005/2025'
    contest.link_pagina = DETAIL_URL
    candidate = DiscoveredCandidate(candidate_id='t010-15', external_id='99',
                                    title_observed=contest.titulo, detail_url_observed=DETAIL_URL,
                                    observed_at=datetime.now(timezone.utc), source='ibade_open')
    run.run_id = RUN_ID
    run.source = 'ibade_open'
    run.candidates = [candidate]
    run.selected_candidate_id = candidate.candidate_id
    run.document = DocumentCandidate(doc_id='t010-15-doc', title='Edital 010/2025', kind='edital', url_requested=DOCUMENT_URL)
    run.artifact = run.artifact.model_copy(update={'artifact_id': 't010-15-art', 'byte_len': len(raw),
        'sha256': hashlib.sha256(raw).hexdigest(), 'url_requested': DOCUMENT_URL, 'url_final': DOCUMENT_URL})
    store.save_artifact_file(run.artifact, raw)
    pages, *_ = extract_pages(raw, artifact_id=run.artifact.artifact_id)
    full_text = '\n'.join(page.text for page in pages)
    assert 'Edital 010' in full_text and '2025' in full_text
    assert contest.edital_numero == '005/2025'
    run.fields = extract_fields(candidate=candidate, artifact=run.artifact, pages=pages)
    print('record15 extracted identity:', [(f.field_name, f.value, f.state.value) for f in run.fields if f.field_name in ('titulo', 'orgao', 'edital_numero')])
    with pytest.raises(HTTPException) as exc:
        canonical.resolve(db, run, store, target_id=contest.id)
    print('record15 semantic guard:', exc.value.detail)
    assert exc.value.status_code == 422
    assert 'origem documental' in str(exc.value.detail) or 'identidade' in str(exc.value.detail) or 'vínculo' in str(exc.value.detail)
