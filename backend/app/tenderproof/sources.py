"""TenderProof source-specific parsing. IMESO sample, never a full catalogue."""
from datetime import datetime, timezone
import re
from urllib.parse import urljoin, urlsplit

from bs4 import BeautifulSoup

from app.tenderproof.contracts import DiscoveredCandidate, DocumentCandidate

IMESO_SOURCE = "imeso_open"
IMESO_LISTING = "https://portal.imeso.com.br/edital/searchEdital"
SOURCE_LISTINGS = {
    "ibgp_open": "https://novo.ibgpconcursos.com.br/inscricoes_abertas.jsp",
    IMESO_SOURCE: IMESO_LISTING,
}


def imeso_candidates(html: str, base_url: str, limit: int = 5):
    soup = BeautifulSoup(html, "lxml")
    found, seen = [], set()
    for a in soup.select("a[href]"):
        url = urljoin(base_url, a["href"])
        parts = urlsplit(url)
        match = re.fullmatch(r"/edital/ver/(\d+)/?", parts.path)
        if parts.scheme != "https" or parts.netloc != "portal.imeso.com.br" or not match:
            continue
        cod = match[1]
        if cod in seen:
            continue
        seen.add(cod)
        row = a.find_parent(class_="row")
        titles = row.select("p") if row else []
        title = " ".join(p.get_text(" ", strip=True) for p in titles[:2]) or None
        found.append(DiscoveredCandidate(candidate_id=f"imeso-{cod}", external_id=cod,
            title_observed=title, detail_url_observed=url, source=IMESO_SOURCE,
            observed_at=datetime.now(timezone.utc)))
        if len(found) >= limit:
            break
    return found


def imeso_documents(html: str, candidate: DiscoveredCandidate):
    soup = BeautifulSoup(html, "lxml")
    docs = []
    for a in soup.select("a[href]"):
        url = urljoin(candidate.detail_url_observed, a["href"])
        parts = urlsplit(url)
        if not parts.path.lower().endswith(".pdf"):
            continue
        path = parts.path
        if parts.netloc == "s3.us-east-1.amazonaws.com":
            if not path.startswith("/cdn.imeso.com.br/"):
                continue
            path = path.removeprefix("/cdn.imeso.com.br")
        elif parts.netloc != "cdn.imeso.com.br":
            continue
        if not re.fullmatch(rf"/edital/\d+/{re.escape(candidate.external_id or '')}/[^/]+\.pdf", path):
            raise ValueError("documento IMESO pertence a outro concurso")
        row = a.find_parent(class_="row")
        title_node = row.select_one("p") if row else None
        title = title_node.get_text(" ", strip=True) if title_node else a.get_text(" ", strip=True)
        lower = title.casefold()
        kind = "outro"
        if "anexo" in lower:
            kind = "anexo"
        elif "gabarito" in lower:
            kind = "gabarito"
        elif "resultado" in lower:
            kind = "resultado"
        elif re.match(r"^edital\b", lower) and not any(t in lower for t in (
            "errata", "retifica", "convoca", "julgamento", "impugna", "recurso", "comunicado", "isen", "homologa")):
            kind = "edital"
        docs.append(DocumentCandidate(doc_id=f"imeso-doc-{len(docs)+1}", title=title,
                                      url_requested=url, kind=kind))
    return docs


def confirm_imeso_identity(candidate, html, detail_url):
    if detail_url != candidate.detail_url_observed or not re.fullmatch(
        rf"/edital/ver/{re.escape(candidate.external_id or '')}/?", urlsplit(detail_url).path
    ):
        raise ValueError("identidade IMESO inconsistente")
    # Require the selected entity plus the exact contest identifier in document links.
    if not imeso_documents(html, candidate):
        raise ValueError("identidade IMESO sem vínculo documental verificável")


def build_imeso_mock_driver():
    from app.tenderproof.demo_pdf import make_text_pdf
    from app.tenderproof.solari_adapter import FakeSolariDriver, DownloadedBytes
    url = "https://cdn.imeso.com.br/edital/1/42/edital.pdf"
    title = "PREFEITURA MUNICIPAL DE EXEMPLO IMESO"
    listing = f'<div class="row"><p>Concurso Público 01/2026</p><p>{title}</p><a href="/edital/ver/42">Mais detalhes</a></div>'
    detail = f'<h1>{title}</h1><div class="row"><p>Edital de abertura 01/2026</p><a href="{url}">DOWNLOAD</a></div>'
    pdf = make_text_pdf([f"{title}\nConcurso Publico 01/2026\nEdital n. 01/2026 de abertura\nAs inscricoes estarao abertas de 10/03/2026 a 20/04/2026.\nhttps://portal.imeso.com.br/edital/ver/42"])
    return FakeSolariDriver(listing_html=listing, detail_html=detail,
        downloads={url: DownloadedBytes(url_requested=url, url_final=url, content=pdf,
                    content_type="application/pdf", redirect_chain=[url])},
        session_id="mock-imeso-001")
