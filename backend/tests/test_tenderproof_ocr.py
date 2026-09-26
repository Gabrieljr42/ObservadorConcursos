import hashlib
import os

import pytest

from app.tenderproof.demo_pdf import make_text_pdf
from app.tenderproof.ocr_processing_worker import words_from_tsv, text_from_words
from app.tenderproof.processing import ProcessingService, ProcessingError


@pytest.mark.parametrize('timeout', [0, 9, 601, float('inf'), float('nan')])
def test_invalid_ocr_deadline_cannot_create_processing_job(tmp_path, monkeypatch, timeout):
    from app.tenderproof import processing
    monkeypatch.setattr(processing, 'get_processing_service', lambda: pytest.fail('invalid deadline created a job'))
    with pytest.raises(ValueError, match='prazo OCR'):
        processing.extract_pages_isolated(make_text_pdf(['Hello']), artifact_id='a', owner_id='o',
                                         operation='ocr_pdf', ocr_timeout_s=timeout)


def test_tsv_preserves_word_positions_confidence_and_line_boundaries():
    header = 'level\tpage_num\tblock_num\tpar_num\tline_num\tword_num\tleft\ttop\twidth\theight\tconf\ttext\n'
    tsv = header + '5\t1\t1\t1\t1\t1\t20\t30\t50\t10\t95.3\tFACEPE\n'
    tsv += '5\t1\t1\t1\t2\t1\t20\t45\t70\t10\t70.2\tInscrições\n'
    tsv += '5\t1\t1\t1\t2\t2\t95\t45\t60\t10\tnan\tInvalid\n'
    words = words_from_tsv(tsv)
    assert words[0]['bbox'] == [20, 30, 50, 10]
    assert words[0]['confidence'] == 95.3
    assert text_from_words(words) == 'FACEPE\nInscrições'


def test_ocr_is_distinct_local_operation_and_never_silent_solari_fallback(tmp_path):
    service = ProcessingService(tmp_path)
    pdf = make_text_pdf(['Original source text'])
    job = service.enqueue('owner', pdf, operation='ocr_pdf')
    assert job['operation'] == 'ocr_pdf'
    assert job['extractor_version'] == 'tenderproof-ocr-v1'
    assert job['input_sha256'] == hashlib.sha256(pdf).hexdigest()
    with pytest.raises(ProcessingError, match='provider_unavailable'):
        service.enqueue('owner', pdf, mode='solari', operation='ocr_pdf')


@pytest.mark.skipif(os.name != 'nt', reason='Native OCR intentionally unavailable on Windows host')
def test_unavailable_ocr_remains_explicit_failure(tmp_path):
    service = ProcessingService(tmp_path)
    job = service.enqueue('owner', make_text_pdf(['Hello']), operation='ocr_pdf')
    result = service.execute(job['id'], 'owner')
    assert result['state'] == 'failed'
    assert result['error']['code'] == 'dependency_unavailable'
