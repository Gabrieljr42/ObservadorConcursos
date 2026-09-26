"""Fixed local OCR operation. No provider calls or document-supplied commands."""
import csv
import hashlib
import io
import json
import math
import os
from pathlib import Path
import subprocess
import struct
import sys
import tempfile
import time

VERSION = 'faperr-raster-ocr-v1'


def words_from_tsv(value):
    words = []
    for row in csv.DictReader(io.StringIO(value), delimiter='\t', quoting=csv.QUOTE_NONE):
        if row['level'] != '5' or not (row.get('text') or '').strip():
            continue
        confidence = float(row['conf'])
        if not math.isfinite(confidence) or not 0 <= confidence <= 100:
            continue
        words.append({'text': row['text'], 'confidence': confidence,
                      'line': [int(row[x]) for x in ('block_num', 'par_num', 'line_num')],
                      'bbox': [int(row[x]) for x in ('left', 'top', 'width', 'height')]})
    return words


def text_from_words(words):
    lines = []
    last = None
    for word in words:
        if word['line'] != last:
            lines.append([])
            last = word['line']
        lines[-1].append(word['text'])
    return '\n'.join(' '.join(line) for line in lines)


def main():
    source, destination, pages_limit, output_limit, operation_seconds = sys.argv[1:]
    deadline = time.monotonic() + float(operation_seconds)
    def remaining(cap):
        value = deadline - time.monotonic()
        if value <= 0:
            raise subprocess.TimeoutExpired('fixed_ocr_operation', float(operation_seconds))
        return min(cap, value)
    try:
        from pypdf import PdfReader
        if os.name != 'posix' or not all(Path(x).is_file() for x in ('/usr/bin/tesseract', '/usr/bin/pdftoppm')):
            raise ValueError('dependency_unavailable')
        import resource
        resource.setrlimit(resource.RLIMIT_AS, (1536*1024*1024, 1536*1024*1024))
        resource.setrlimit(resource.RLIMIT_FSIZE, (32*1024*1024, 32*1024*1024))
        cpu_limit = math.ceil(float(operation_seconds)) + 5
        resource.setrlimit(resource.RLIMIT_CPU, (cpu_limit, cpu_limit))
        os.environ['OMP_THREAD_LIMIT'] = '1'
        raw = Path(source).read_bytes()
        if not raw[:21].lstrip(b' \t\r\n').startswith(b'%PDF-'):
            raise ValueError('invalid_document')
        reader = PdfReader(source)
        if reader.is_encrypted:
            raise ValueError('invalid_document')
        if len(reader.pages) > int(pages_limit):
            raise ValueError('page_limit')
        engine = subprocess.run(['/usr/bin/tesseract', '--version'], capture_output=True, check=True, timeout=5).stdout.decode().splitlines()[0]
        renderer = subprocess.run(['/usr/bin/pdftoppm', '-v'], capture_output=True, check=True, timeout=5).stderr.decode().splitlines()[0]
        models = {language: hashlib.sha256(Path('/usr/share/tesseract-ocr/5/tessdata',
                    language+'.traineddata').read_bytes()).hexdigest() for language in ('por', 'eng')}
        pages = []
        consumed = 0
        with tempfile.TemporaryDirectory(prefix='ocr-') as temporary:
            prefix = Path(temporary)/'page'
            for index, page in enumerate(reader.pages):
                remaining(120)
                native = ''  # Raster-only recovery for the preserved FAPERR acquisition failures.
                item = {'page_number': index+1, 'text': native, 'method': 'pdf_text', 'native_text': native}
                if len(''.join(native.split())) < 40:
                    # Bound raster dimensions even for maliciously large media boxes.
                    subprocess.run(['/usr/bin/pdftoppm', '-f', str(index+1), '-l', str(index+1),
                        '-singlefile', '-r', '200', '-scale-to', '3600', '-png', source, str(prefix)],
                        stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                        check=True, timeout=remaining(25))
                    image = prefix.with_suffix('.png')
                    if image.stat().st_size > 32*1024*1024:
                        raise ValueError('output_limit')
                    image_bytes = image.read_bytes()
                    if image_bytes[:8] != b'\x89PNG\r\n\x1a\n':
                        raise ValueError('invalid_document')
                    width, height = struct.unpack('>II', image_bytes[16:24])
                    if not (0 < width <= 3600 and 0 < height <= 3600):
                        raise ValueError('output_limit')
                    output_base = Path(temporary)/'recognized'
                    subprocess.run(['/usr/bin/tesseract', str(image), str(output_base), '-l', 'por+eng', '--psm', '3', 'tsv'],
                        stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                        check=True, timeout=remaining(40))
                    tsv_file = output_base.with_suffix('.tsv')
                    if tsv_file.stat().st_size > int(output_limit):
                        raise ValueError('output_limit')
                    words = words_from_tsv(tsv_file.read_text(encoding='utf-8'))
                    item.update(text=text_from_words(words) if words else native, method='ocr_tesseract', words=words,
                        mean_confidence=sum(w['confidence'] for w in words)/len(words) if words else None,
                        image_sha256=hashlib.sha256(image_bytes).hexdigest(), image_width=width, image_height=height,
                        recognition_empty=not words, review_required=True)
                consumed += len(json.dumps(item, ensure_ascii=False).encode('utf-8'))
                if consumed > int(output_limit):
                    raise ValueError('output_limit')
                pages.append(item)
        result = {'extractor_version': VERSION, 'input_sha256': hashlib.sha256(raw).hexdigest(),
                  'total_pages': len(pages), 'pages': pages,
                  'ocr': {'engine': engine, 'renderer': renderer, 'languages': 'por+eng',
                          'language_model_sha256': models,
                          'psm': 3, 'render_dpi': 200, 'max_dimension_pixels': 3600,
                          'trigger': 'explicit raster recovery after failed bounded extraction',
                          'review_required': True}}
        data = json.dumps(result, ensure_ascii=False).encode('utf-8')
        if len(data) > int(output_limit):
            raise ValueError('output_limit')
        Path(destination).write_bytes(data)
        return 0
    except Exception as exc:
        code = ('dependency_unavailable' if isinstance(exc, ImportError) else
                'timeout' if isinstance(exc, subprocess.TimeoutExpired) else
                str(exc) if str(exc) in ('page_limit', 'output_limit', 'dependency_unavailable') else 'invalid_document')
        Path(destination).write_text(json.dumps({'error': code}), encoding='utf-8')
        return 1


if __name__ == '__main__':
    sys.exit(main())
