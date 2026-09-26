"""Extract auditable page excerpts from T010 preserved PDFs.

Read-only helper: it never touches the runtime DB or applies TenderProof proposals.
"""
from pathlib import Path
import hashlib, json, re
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[3]
PDF_DIR = ROOT / "docs/execucao/evidencias/T010"
OUT = PDF_DIR / "T010-extracao.json"
PATTERNS = {
    "identity": r"(?i)(EDITAL.{0,180}|CONCURSO.{0,180}|PROCESSO SELETIVO.{0,180})",
    "cargo": r"(?i)(CARGO.{0,500}|FUNÇÕES.{0,500}|PRESTADOR.{0,500})",
    "vagas": r"(?i)(VAGAS.{0,400}|QUANTITATIVO.{0,400})",
    "salary": r"(?i)(R\$\s*[\d.,]+.{0,180}|VENCIMENTO.{0,300}|REMUNERAÇÃO.{0,300})",
    "requirements": r"(?i)(REQUISITOS?.{0,400}|ESCOLARIDADE.{0,400}|HABILITAÇÃO.{0,300})",
    "fee": r"(?i)(TAXA.{0,250}|VALOR DA INSCRIÇÃO.{0,250})",
    "locality": r"(?i)(realizadas? na cidade.{0,250}|local do exercício.{0,300}|município de [A-ZÀ-Üa-zà-ü /-]{2,80})",
    "dates": r"(?i)(provas?.{0,220}|inscriç(?:ão|ões).{0,220}|CRONOGRAMA.{0,500})",
}

def norm(s):
    return re.sub(r"\s+", " ", s).strip()

rows = []
for pdf in sorted(PDF_DIR.glob("id*.pdf"), key=lambda p: int(p.stem[2:])):
    raw = pdf.read_bytes()
    reader = PdfReader(str(pdf))
    pages = []
    for n, page in enumerate(reader.pages, 1):
        text = page.extract_text() or ""
        hits = {}
        for name, pattern in PATTERNS.items():
            found = []
            for m in list(re.finditer(pattern, text))[:8]:
                found.append(norm(text[max(0, m.start()-90):min(len(text), m.end()+260)]))
            if found:
                hits[name] = found
        if hits:
            pages.append({"page": n, "hits": hits})
    rows.append({"id": int(pdf.stem[2:]), "path": str(pdf), "sha256": hashlib.sha256(raw).hexdigest(), "pages": len(reader.pages), "evidence": pages})
OUT.write_text(json.dumps({"schema_version": 1, "read_only": True, "records": rows}, ensure_ascii=False, indent=2), encoding="utf-8")
print(OUT)
