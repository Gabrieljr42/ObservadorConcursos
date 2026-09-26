from types import SimpleNamespace
import pytest
from app.tenderproof.msconcursos_cris_jobs import SHA, extract_cris_jobs

@pytest.mark.parametrize('source,external_id,sha', [
    ('quadrix_open', '48', SHA), ('msconcursos_open', '49', SHA),
    ('msconcursos_open', '48', 'b' * 64),
])
def test_cannot_transcribe_other_identity_or_revised_document(source, external_id, sha):
    assert extract_cris_jobs(SimpleNamespace(sha256=sha), [], None,
        source=source, external_id=external_id) is None

def test_claimed_hash_without_reproducible_rows_fails_closed():
    result = extract_cris_jobs(SimpleNamespace(sha256=SHA), [], None,
        source='msconcursos_open', external_id='48')
    assert result.state.value == 'failed' and result.value is None
