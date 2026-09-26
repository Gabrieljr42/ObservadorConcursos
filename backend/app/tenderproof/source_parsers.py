"""Legacy-compatible IBGP parsing helpers shared by source adapters."""
from __future__ import annotations
import re
from datetime import datetime, timezone
from urllib.parse import urljoin, urlsplit, parse_qs
from bs4 import BeautifulSoup
from app.tenderproof.contracts import SUPPORTED_SOURCE, DiscoveredCandidate, DocumentCandidate
from app.tenderproof.solari_adapter import ObservedJson

# Textos de interface que nunca são título de concurso (observado ao vivo:
# cartões IBGP renderizam botões "SAIBA MAIS" como texto da âncora).
_NOISE_ANCHOR_TEXTS = {
    "saiba mais", "clique aqui", "clique", "detalhes", "ver detalhes",
    "ver edital", "acessar", "acesse", "inscreva-se", "inscreva se",
    "inscricao", "ver mais", "leia mais", "confira", "edital",
}


def _anchor_title(anchor) -> str | None:
    """Extrai título honesto da âncora: ignora ruído de interface e busca
    contexto (atributos title/alt e ancestrais próximos)."""
    raw = " ".join(anchor.get_text(" ", strip=True).split())
    folded = raw.casefold().strip()
    if folded and folded not in _NOISE_ANCHOR_TEXTS and len(raw) >= 8:
        return raw
    # Fallback 1: atributos próprios (title / alt de imagem interna).
    for attr in (anchor.get("title"),):
        if attr and len(attr.split()) >= 2 and attr.casefold() not in _NOISE_ANCHOR_TEXTS:
            return " ".join(str(attr).split())
    img = anchor.find("img")
    if img is not None:
        alt = (img.get("alt") or "").strip()
        if len(alt) >= 4 and alt.casefold() not in _NOISE_ANCHOR_TEXTS:
            return " ".join(alt.split())
    # Fallback 2: ancestral próximo com texto substancial (cartão do concurso).
    node = anchor.parent
    for _ in range(3):
        if node is None or getattr(node, "name", None) in ("body", "html", "[document]"):
            break
        for heading in node.find_all(["h1", "h2", "h3", "h4"], limit=3):
            text = " ".join(heading.get_text(" ", strip=True).split())
            if len(text) >= 10 and text.casefold() not in _NOISE_ANCHOR_TEXTS:
                return text[:300]
        block = " ".join(node.get_text(" ", strip=True).split())
        if len(block) >= 30:
            # Remove o próprio ruído do botão para não poluir o hint.
            return block[:300]
        node = node.parent
    return None

_BAD_DOC_TERMS = (
    "gabarito", "resultado", "recurso", "homologa", "convoca", "lista de",
    "laudo", "preliminar", "definitiva", "isenção", "isencao", "comunicado",
    "cronograma", "manual", "formulário", "formulario",
    "julgamento", "impugna",
)


def parse_listing_candidates(html: str, *, base_url: str, limit: int = 5) -> list[DiscoveredCandidate]:
    """Descobre até ``limit`` candidatos com título e URL observados."""
    soup = BeautifulSoup(html, "lxml")
    found: list[DiscoveredCandidate] = []
    seen: set[str] = set()
    now = datetime.now(timezone.utc)
    for anchor in soup.select("a[href]"):
        href = str(anchor.get("href") or "")
        observed_url = urljoin(base_url, href)
        parts = urlsplit(observed_url)
        codes = parse_qs(parts.query).get("cod", [])
        if (parts.scheme != "https" or parts.hostname != "novo.ibgpconcursos.com.br"
                or parts.path != "/concurso.jsp" or len(codes) != 1
                or not re.fullmatch(r"\d+", codes[0])):
            continue
        cod = codes[0]
        if cod in seen:
            continue
        seen.add(cod)
        detail_url = f"https://novo.ibgpconcursos.com.br/concurso.jsp?cod={cod}"
        title = _anchor_title(anchor)
        found.append(
            DiscoveredCandidate(
                candidate_id=f"cand-{cod}",
                title_observed=title,
                detail_url_observed=detail_url,
                external_id=cod,
                observed_at=now,
                source=SUPPORTED_SOURCE,
            )
        )
        if len(found) >= limit:
            break
    return found


def parse_document_candidates(html: str, *, base_url: str) -> list[DocumentCandidate]:
    """Identifica documentos candidatos no detalhe e classifica o tipo."""
    soup = BeautifulSoup(html, "lxml")
    docs: list[DocumentCandidate] = []
    seq = 0
    for anchor in soup.select("a[href]"):
        href = str(anchor.get("href") or "").strip()
        if not href or href.startswith(("javascript:", "#")):
            continue
        url = urljoin(base_url, href)
        target, current = urlsplit(url), urlsplit(base_url)
        if (target.scheme, target.netloc, target.path, target.query) == (current.scheme, current.netloc, current.path, current.query):
            continue  # page controls/accordions are not downloadable documents
        title = " ".join(anchor.get_text(" ", strip=True).split())
        row = anchor.find_parent("tr")
        if not title and row is not None:
            # IBGP uses an image-only download anchor; label is the same row's
            # non-date text cell. The directory /site/anexos/ is not a doc type.
            labels = [" ".join(cell.get_text(" ", strip=True).split()) for cell in row.find_all("td") if cell.find("a") is None]
            title = next((label for label in labels if label and not re.fullmatch(r"\d{2}/\d{2}/\d{4}", label)), "")
        title = title or href
        lowered = f"{title} {url}".lower()
        looks_doc = ".pdf" in lowered or "download" in lowered or "edital" in lowered or "anexo" in lowered
        if not looks_doc:
            continue
        if any(term in lowered for term in ("politica-de-privacidade", "privacy", "cookie", "termos-de-uso")):
            continue
        kind: str = "outro"
        if "gabarito" in lowered:
            kind = "gabarito"
        elif "resultado" in lowered:
            kind = "resultado"
        elif re.search(r"\banexo(?:\s|_|-|$)", title.lower()):
            kind = "anexo"
        elif "edital" in lowered and not any(term in title.lower() for term in (*_BAD_DOC_TERMS, "retifica", "errata")):
            kind = "edital"
        seq += 1
        docs.append(
            DocumentCandidate(
                doc_id=f"doc-{seq:02d}",
                title=title[:300],
                url_requested=url,
                kind=kind,  # type: ignore[arg-type]
            )
        )
    return docs


def choose_edital(docs: list[DocumentCandidate]) -> tuple[DocumentCandidate, str]:
    """Escolhe o edital e explica a decisão (evita gabarito/resultado)."""
    if not docs:
        raise ValueError("nenhum documento candidato observado no detalhe")
    editais = [d for d in docs if d.kind == "edital"]
    if not editais:
        consolidated = [d for d in docs if d.kind == 'consolidado']
        if len({d.url_requested for d in consolidated}) == 1:
            chosen = consolidated[0]
            reason = 'Edital consolidado único observado; aquisição para conferência. Efeitos das retificações exigem revisão antes da publicação.'
            chosen.reason_chosen = reason
            return chosen, reason
    # Preferência ao endpoint oficial de download IBGP (serve o PDF direto em
    # vez de página visualizadora/HTML).
    direct = [d for d in editais if "/rest/concurso/download/" in d.url_requested]
    # A direct endpoint can replace an explicitly linked viewer of that same
    # document. It cannot hide another principal PDF/edital from the decision.
    def same_viewer(viewer, document):
        view = urlsplit(viewer.url_requested)
        target = urlsplit(document.url_requested)
        match = re.search(r"/rest/concurso/download/[^/]+/(\d+)/?", target.path)
        query = parse_qs(view.query)
        return (view.hostname == target.hostname and bool(match)
                and bool(re.search(r"leitor|visualiz|viewer", view.path, re.I))
                and any(query.get(key) == [match[1]] for key in ("doc", "id", "documento")))
    pool = [d for d in editais if not direct or d in direct or not any(same_viewer(d, target) for target in direct)]
    if not pool:
        raise ValueError("nenhum edital principal inequívoco; anexos e retificações exigem revisão")
    if len({d.url_requested for d in pool}) > 1:
        raise ValueError("links de edital ambíguos; seleção documental explícita necessária")
    chosen = pool[0]
    ignored = len(docs) - 1
    if chosen.kind != "edital":
        reason = (
            f"Nenhum link com 'edital' no título/URL; escolhido '{chosen.title}' "
            f"({chosen.kind}) entre {len(docs)} documentos. Revisão manual recomendada."
        )
    else:
        skipped = [d.title for d in docs if d.doc_id != chosen.doc_id][:5]
        reason = (
            f"Escolhido '{chosen.title}' por conter 'edital' no título/URL; "
            f"{ignored} documento(s) ignorado(s)"
            + (f" (ex.: {'; '.join(skipped)})" if skipped else "")
            + "."
        )
    chosen.reason_chosen = reason
    return chosen, reason


def confirm_identity(*, candidate: DiscoveredCandidate, detail_html: str, detail_url: str) -> None:
    """Confirma que o detalhe aberto corresponde ao candidato selecionado."""
    cod = candidate.external_id or ""
    if cod and parse_qs(urlsplit(detail_url).query).get("cod") != [cod]:
        raise ValueError(f"detalhe {detail_url} não corresponde ao candidato cod={cod}")
    title = " ".join((candidate.title_observed or "").split())
    text = " ".join(BeautifulSoup(detail_html, "lxml").get_text(" ", strip=True).split())
    explicit_code = bool(cod and re.search(rf"\bcod\s*=\s*['\"]?{re.escape(cod)}(?!\d)", detail_html, re.I))
    if cod and not explicit_code and not (title and title in text):
        raise ValueError("identidade do concurso não confirmada no detalhe")


def filter_structured_observations(observed: list[ObservedJson]) -> list[ObservedJson]:
    return [o for o in observed if "/rest/concurso" in o.url]

