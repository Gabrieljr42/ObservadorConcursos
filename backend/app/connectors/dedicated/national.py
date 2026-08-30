from __future__ import annotations

import logging
import re
from io import BytesIO
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup
from pypdf import PdfReader

from app.connectors.base import BaseConnector, CandidateItem
from app.connectors.common import (
    build_hash,
    build_summary,
    classify_area_from_many,
    clean,
    extract_city_uf,
    extract_external_id,
    first_date,
    extract_pdf_fields_if_possible,
    extract_pdf_link,
    normalize_url,
    parse_date_interval,
    parse_money,
    status_from_dates,
    text_lines,
)
from app.publications import (
    build_publication_hash,
    is_valid_publication_title,
    normalize_publication_type,
    parse_publications_from_dom,
    parse_publications_from_lines,
)

logger = logging.getLogger(__name__)


class GenericDedicatedBancaConnector(BaseConnector):
    """Reusable dedicated connector template for major national institutions."""

    banca = 'Banca Nacional'
    # A detail URL must identify one certame.  The old ``/concurso/`` fallback
    # accepted category/index pages and produced phantom open contests.
    detail_patterns: tuple[str, ...] = (
        r'/concursos?/[^/?#]+/?$', r'/edital/[^/?#]+/?$',
        r'/informacoes/[^/?#]+/?$', r'(?:[?&])(id|codigo|cod)=\d+',
    )
    allowed_hosts: tuple[str, ...] = ()
    candidate_excluded_terms: tuple[str, ...] = (
        'vestibular', 'residência médica', 'residencia medica',
        'proficiência acadêmica', 'proficiencia academica',
    )

    def _fetch_candidates(self) -> list[CandidateItem]:
        candidates: list[CandidateItem] = []
        seen: set[str] = set()

        try:
            html = self._fetch_html(self.list_url)
        except Exception as exc:
            logger.warning('%s: error fetching list %s: %s', self.banca, self.list_url, exc)
            return []

        soup = BeautifulSoup(html, 'lxml')
        # Discover once per anchor and derive status/title from the nearest
        # compact card.  Scanning broad ``article``/``div`` containers caused
        # the status of the first open card to leak into every link on pages
        # such as FUNCERN.
        for a in soup.select('a[href]'):
            href = a.get('href')
            url = normalize_url(self.list_url, href)
            if not url or url in seen or not self._same_domain(url):
                continue
            path_lower = urlparse(url).path.lower()
            if any(bad in path_lower for bad in ['/login', '/contato', '/privacidade', '/institucional', '/noticias', '/noticia']):
                continue
            if not self._is_detail_url(url):
                continue

            nearby_text = self._candidate_context_text(a)
            if not nearby_text or not self._has_candidate_identity(nearby_text, url):
                continue
            if self._candidate_is_excluded(nearby_text):
                continue

            status_hint = self._infer_status(nearby_text)
            if self.mode == 'open' and status_hint == 'Finalizado':
                continue
            seen.add(url)
            candidates.append(CandidateItem(
                title_hint=nearby_text[:500],
                detail_url=url,
                # A link's presence is not evidence that registrations are
                # open; infer only from visible wording in its own card.
                status_hint=status_hint,
                external_id=extract_external_id(url, [r'id=(\d+)', r'codigo=(\d+)', r'/concursos?/([^/?#]+)']),
            ))
            if len(candidates) >= self.max_candidates:
                break

        return candidates

    def _candidate_context_text(self, anchor) -> str | None:
        anchor_text = clean(anchor.get_text(' ', strip=True)) or ''
        options: list[str] = []
        if anchor_text:
            options.append(anchor_text)
        for parent in anchor.parents:
            if getattr(parent, 'name', None) not in {'div', 'article', 'li', 'tr', 'section'}:
                continue
            value = clean(parent.get_text(' ', strip=True)) or ''
            if 12 <= len(value) <= 2500:
                options.append(value)
            if len(options) >= 8:
                break
        if not options:
            return None

        generic = {'saiba mais', 'mais informações', 'mais informacoes', 'ver detalhes', 'clique aqui'}
        identity_re = re.compile(
            r'\b(concurso|sele[cç][aã]o|processo seletivo|processo de sele[cç][aã]o|edital|prefeitura|c[âa]mara|'
            r'secretaria|tribunal|universidade|conselho|autarquia|ag[êe]ncia|munic[ií]pio)\b',
            flags=re.IGNORECASE,
        )

        status_identity_options = [
            value for value in options
            if self._infer_status(value) is not None and identity_re.search(value)
            and value.lower().strip() not in generic
        ]
        if status_identity_options:
            return min(status_identity_options, key=len)
        identity_options = [value for value in options if identity_re.search(value)]
        if identity_options:
            return min(identity_options, key=len)
        return min(options, key=len)

    def _candidate_is_excluded(self, text: str) -> bool:
        lowered = text.lower()
        return any(term.lower() in lowered for term in self.candidate_excluded_terms)

    def _same_domain(self, url: str) -> bool:
        base_host = urlparse(self.base_url).netloc.lower().removeprefix('www.')
        host = urlparse(url).netloc.lower().removeprefix('www.')
        allowed = {h.lower().removeprefix('www.') for h in self.allowed_hosts}
        return not host or host == base_host or host in allowed

    def _is_detail_url(self, url: str) -> bool:
        """Reject navigation, category, index and document links."""
        parsed = urlparse(url)
        if parsed.scheme not in {'http', 'https'} or not self._same_domain(url):
            return False
        path = parsed.path.rstrip('/').lower()
        if not path or url.rstrip('/') == self.list_url.rstrip('/'):
            return False
        if path.endswith(('.pdf', '.doc', '.docx', '.xls', '.xlsx')):
            return False
        if any(token in path.split('/') for token in ('index', 'categoria', 'category', 'arquivo', 'download', 'busca', 'search')):
            return False
        if path.rsplit('/', 1)[-1] in {
            'abertos', 'abertas', 'andamento', 'encerrados', 'encerradas',
            'futuros', 'realizados', 'inscricoes', 'inscrições', 'lista',
        }:
            return False
        if path in {'/concursos', '/concurso', '/editais', '/edital', '/informacoes'}:
            return False
        return any(re.search(pattern, url, flags=re.IGNORECASE) for pattern in self.detail_patterns)

    def _has_candidate_identity(self, text: str | None, url: str) -> bool:
        value = clean(text or '') or ''
        if len(value) < 12:
            return False
        if value.lower() in {'saiba mais', 'mais informações', 'mais informacoes', 'ver detalhes', 'clique aqui', 'concursos', 'editais'}:
            return False
        return bool(re.search(
            r'\b(concurso|processo seletivo|edital|prefeitura|câmara|camara|secretaria|tribunal|universidade|órgão|orgao|polícia|policia)\b',
            value, flags=re.IGNORECASE,
        )) or bool(re.search(r'(?:id|codigo|cod)=\d+|/(?:concursos?|edital|informacoes)/[^/?#]+', url, flags=re.IGNORECASE))

    def _infer_status(self, text: str | None) -> str | None:
        lowered = (text or '').lower()
        if any(k in lowered for k in ['inscrições abertas', 'inscricoes abertas', 'inscrição aberta', 'inscricao aberta', 'aberto']):
            return 'Inscrições abertas'
        if any(k in lowered for k in ['em andamento', 'andamento']):
            return 'Em andamento'
        if any(k in lowered for k in ['encerrado', 'finalizado', 'concluído', 'concluido']):
            return 'Finalizado'
        return None

    def _parse_detail(self, candidate: CandidateItem, html: str, *, client: httpx.Client) -> dict[str, Any] | None:
        soup = BeautifulSoup(html, 'lxml')
        lines = text_lines(soup)
        text = '\n'.join(lines)

        title = self._extract_title(lines, candidate.title_hint)
        orgao = self._extract_orgao(title, lines, candidate.title_hint)
        cidade, uf = extract_city_uf(f'{title} {orgao} {text[:2000]}')
        modalidade_text = f'{title} {text[:2500]}'.lower()
        if 'processo seletivo simplificado' in modalidade_text or re.search(r'\bpss\b', modalidade_text):
            modalidade = 'Processo Seletivo Simplificado'
        elif 'processo seletivo' in modalidade_text or 'seleção pública' in modalidade_text or 'selecao publica' in modalidade_text:
            modalidade = 'Processo Seletivo'
        else:
            modalidade = 'Concurso Público'
        inicio, fim = parse_date_interval(text)
        detail_status = self._extract_detail_status(lines)
        status = status_from_dates(inicio, fim, fallback=detail_status or candidate.status_hint)

        edital_url = extract_pdf_link(soup, candidate.detail_url)
        inscricao_url = self._extract_inscricao_link(soup, candidate.detail_url)
        table_fields = self._extract_structured_vaga_fields(soup)
        cargo_candidates = table_fields['cargos'] or self._extract_cargo_candidates(lines)
        area = classify_area_from_many(cargo_candidates, title, orgao, text[:1500])
        cargo = 'Vários cargos' if len(cargo_candidates) >= 2 else (cargo_candidates[0] if cargo_candidates else None)
        vagas = table_fields['vagas'] or self._extract_vagas(f'{candidate.title_hint or ""}\n{text}')
        salario_min = table_fields['salario_min']
        salario_max = table_fields['salario_max']
        if salario_min is None and salario_max is None:
            salario_min, salario_max = self._extract_salarios(text)
        taxa = table_fields['taxa'] if table_fields['taxa'] is not None else self._extract_taxa(text)
        external_id = candidate.external_id or extract_external_id(candidate.detail_url, [r'id=(\d+)', r'codigo=(\d+)', r'/concursos?/([^/?#]+)'])
        edital_numero = self._extract_edital_numero(text, title)
        edital_data = self._extract_edital_data(text)
        prova_data = self._extract_prova_data(text)

        pdf_payload, pdf_fields, excerpt, pdf_at = extract_pdf_fields_if_possible(edital_url, title=title, orgao=orgao, client=client)
        if pdf_fields:
            cargo = cargo or pdf_fields.get('cargo')
            area = area or pdf_fields.get('area')
            vagas = vagas or pdf_fields.get('vagas')
            salario_min = salario_min or pdf_fields.get('salario_min')
            salario_max = salario_max or pdf_fields.get('salario_max')
            taxa = taxa if taxa is not None else pdf_fields.get('taxa')
        if vagas and 2000 <= vagas <= 2100 and re.search(rf'\b{vagas}\b', title):
            vagas = None

        if not self._is_valid_certame(title, orgao, cidade, uf, inicio, fim, edital_url, cargo_candidates, text):
            return None
        if self.category == 'institutional_selection':
            from app.connectors.institutional import InstitutionalSelectionConnector
            if not InstitutionalSelectionConnector.has_personnel_evidence(title, text):
                return None
        if self.mode == 'open' and status in {'Finalizado', 'Encerrado'}:
            self.mark_empty_evidence('evaluated_closed', f'Status {status} on detail {candidate.detail_url}', candidate.detail_url)
            return None

        publications = parse_publications_from_dom(soup, candidate.detail_url, source=self.banca.lower())
        if not publications:
            publications = parse_publications_from_lines(lines, source=self.banca.lower())
        normative_titles = [
            publication for publication in publications
            if publication.get('link')
            and re.search(r'\bedital\b', publication.get('title') or '', re.I)
            and not re.search(
                r'\b(?:resultado|gabarito|convoca|portaria|homologa|deferimento|'
                r'isen[cç][aã]o|retifica|rerratifica|cronograma|prorroga|altera|anexo)\b',
                publication.get('title') or '',
                re.I,
            )
        ]
        primary_edital = next(
            (
                publication.get('link') for publication in normative_titles
                if re.search(r'\babertura\b', publication.get('title') or '', re.I)
            ),
            None,
        ) or next((publication.get('link') for publication in normative_titles), None)
        if primary_edital:
            edital_url = primary_edital
        raw_payload = {
            'title_hint': candidate.title_hint,
            'detail_url': candidate.detail_url,
            'lines_sample': lines[:120],
            'cargo_candidates': cargo_candidates[:60],
            'publications': publications,
            'pdf': pdf_payload,
            'pdf_fields': pdf_fields.get('raw_pdf_fields') if isinstance(pdf_fields, dict) else {},
            'source_list_url': self.list_url,
        }
        resumo = build_summary(title, modalidade, status, inicio, fim, cargo=cargo, area=area, vagas=vagas, salario_min=salario_min, salario_max=salario_max)

        return {
            'external_id': external_id,
            'banca': self.banca,
            'orgao': orgao,
            'titulo': title,
            'modalidade': modalidade,
            'cargo': cargo,
            'area': area,
            'cidade': cidade or (pdf_fields or {}).get('cidade'),
            'uf': uf or (pdf_fields or {}).get('uf'),
            'status': status,
            'vagas': vagas,
            'salario_min': salario_min,
            'salario_max': salario_max,
            'escolaridade': table_fields['escolaridade'] or (pdf_fields or {}).get('escolaridade'),
            'taxa': taxa,
            'prova_data': prova_data or (pdf_fields or {}).get('prova_data'),
            'edital_numero': edital_numero,
            'edital_data': edital_data,
            'inscricao_inicio': inicio,
            'inscricao_fim': fim,
            'link_pagina': candidate.detail_url,
            'link_edital': edital_url,
            'link_inscricao': inscricao_url,
            'resumo': resumo,
            'raw_data': raw_payload,
            'edital_pdf_text_hash': pdf_payload.get('text_hash'),
            'edital_pdf_pages': pdf_payload.get('pages'),
            'edital_pdf_excerpt': excerpt,
            'pdf_extracted_at': pdf_at,
            'content_hash': build_hash(raw_payload),
            'fetched_at': datetime.now(UTC),
        }

    def _extract_title(self, lines: list[str], hint: str | None) -> str:
        # The detail heading is authoritative.  A list-card hint often also
        # contains status, dates, buttons and vacancy totals.
        candidates = list(lines[:80])
        if hint:
            candidates.append(hint)
        for raw in candidates:
            line = clean(raw)
            if not line or len(line) < 10 or len(line) > 220:
                continue
            if line.lower().strip() in {
                'concurso público', 'concurso publico', 'processo seletivo',
                'processo seletivo simplificado', 'edital',
            }:
                continue
            if re.search(r'\b(?:concurso|processo seletivo|edital|prefeitura|tribunal|secretaria|pol[íi]cia|banco|ministerio|minist[eé]rio)\b', line, flags=re.IGNORECASE):
                return line
        return f'Concurso {self.banca}'

    def _extract_orgao(self, title: str, lines: list[str], hint: str | None) -> str | None:
        for val in [title, hint] + lines[:100]:
            if not val:
                continue
            m = re.search(r'((?:PREFEITURA|C[ÂA]MARA|SECRETARIA|MINIST[ÉE]RIO|TRIBUNAL|DEFENSORIA|POL[ÍI]CIA|CORPO DE BOMBEIROS|CONSELHO|AUTARQUIA|AG[ÊE]NCIA|UNIVERSIDADE|HOSPITAL)[^\n]{3,150})', val, flags=re.IGNORECASE)
            if m:
                orgao = clean(m.group(1))
                if orgao:
                    return re.sub(
                        r'\s+(?:Edital|Inscri[cç][oõ]es|Pedidos?\s+de\s+Isen[cç][aã]o|Quantidade\s+de\s+Vagas)\b.*$',
                        '',
                        orgao,
                        flags=re.IGNORECASE,
                    ).strip()
        return None

    def _extract_detail_status(self, lines: list[str]) -> str | None:
        for index, line in enumerate(lines[:180]):
            normalized = (clean(line) or '').strip()
            match = re.search(
                r'\b(?:situa[cç][aã]o|status)\b\s*[:\-]?\s*'
                r'(inscri[cç][oõ]es?\s+abertas?|em\s+andamento|finalizado|encerrado|homologado|suspenso|cancelado)',
                normalized,
                flags=re.IGNORECASE,
            )
            if match:
                return self._infer_status(match.group(1)) or clean(match.group(1))
            if normalized.lower() in {'situação', 'situacao', 'status'} and index + 1 < len(lines):
                inferred = self._infer_status(lines[index + 1])
                if inferred:
                    return inferred
        return None

    def _extract_structured_vaga_fields(self, soup: BeautifulSoup) -> dict[str, Any]:
        cargos: list[str] = []
        quantities: list[int] = []
        salaries: list[Decimal] = []
        fees: list[Decimal] = []
        educations: list[str] = []
        seen_rows: set[tuple[str, str]] = set()

        def header_index(headers: list[str], terms: tuple[str, ...]) -> int | None:
            return next((i for i, value in enumerate(headers) if any(term in value for term in terms)), None)

        for table in soup.select('table'):
            rows = table.select('tr')
            if not rows:
                continue
            header_cells = rows[0].select('th, td')
            headers = [(clean(cell.get_text(' ', strip=True)) or '').lower() for cell in header_cells]
            cargo_idx = header_index(headers, ('vaga', 'cargo', 'emprego', 'função', 'funcao'))
            qty_idx = header_index(headers, ('qtde', 'quantidade'))
            salary_idx = header_index(headers, ('salário', 'salario', 'remuneração', 'remuneracao'))
            education_idx = header_index(headers, ('escolaridade', 'requisito'))
            fee_idx = header_index(headers, ('taxa',))
            if cargo_idx is None or (qty_idx is None and salary_idx is None):
                continue
            for row in rows[1:]:
                cells = [clean(cell.get_text(' ', strip=True)) or '' for cell in row.select('th, td')]
                if cargo_idx >= len(cells):
                    continue
                cargo_name = cells[cargo_idx].strip()
                if not cargo_name or cargo_name.lower() in {'vaga', 'cargo', 'emprego'}:
                    continue
                qty_text = cells[qty_idx] if qty_idx is not None and qty_idx < len(cells) else ''
                key = (cargo_name.lower(), qty_text.lower())
                if key in seen_rows:
                    continue
                seen_rows.add(key)
                cargos.append(cargo_name)
                qty_values = [int(value) for value in re.findall(r'\b\d{1,5}\b', qty_text)]
                if qty_values:
                    # A numeric cadastro-reserva quantity is part of the
                    # official total; a bare "Cadastro de Reserva" adds zero.
                    quantities.append(sum(qty_values))
                if salary_idx is not None and salary_idx < len(cells):
                    salary = parse_money(cells[salary_idx])
                    if salary is not None:
                        salaries.append(salary)
                if fee_idx is not None and fee_idx < len(cells):
                    fee = parse_money(cells[fee_idx])
                    if fee is not None:
                        fees.append(fee)
                if education_idx is not None and education_idx < len(cells):
                    value = cells[education_idx].strip()
                    if value and value not in educations:
                        educations.append(value)

        return {
            'cargos': cargos,
            'vagas': sum(quantities) if quantities else None,
            'salario_min': min(salaries) if salaries else None,
            'salario_max': max(salaries) if salaries else None,
            'taxa': min(fees) if fees else None,
            'escolaridade': educations[0] if len(educations) == 1 else ('Múltiplas' if educations else None),
        }

    def _extract_inscricao_link(self, soup: BeautifulSoup, base: str) -> str | None:
        candidates: list[tuple[int, str]] = []
        for a in soup.select('a[href]'):
            t = clean(a.get_text(' ', strip=True)) or ''
            href = a.get('href')
            if not href:
                continue
            lowered = f'{t} {href}'.lower()
            normalized = normalize_url(base, href)
            if not normalized or any(token in normalized.lower() for token in ('.pdf', '.doc', '.docx', '/arquivos/', 'download')):
                continue
            if '/painel' in normalized.lower() and '/termo/' not in normalized.lower():
                continue
            if '/termo/' in normalized.lower() or any(token in lowered for token in ('inscreva-se', 'inscreva', 'realizar inscrição', 'realizar inscricao')):
                priority = 0
            elif any(token in lowered for token in ('inscrição', 'inscricao')):
                priority = 1
            elif any(token in lowered for token in ('área do candidato', 'area do candidato', 'candidato')):
                priority = 2
            else:
                continue
            candidates.append((priority, normalized))
        return min(candidates, key=lambda value: value[0])[1] if candidates else None

    def _extract_edital_numero(self, text: str, title: str) -> str | None:
        for value in (text[:5000], title):
            match = re.search(
                r'\bEdital\s*(?:n[º°o.]?\s*)?[:\-]?\s*(\d{1,4}(?:[./-]\d{4})?(?:[-–][A-Z0-9/.-]+)?)',
                value,
                flags=re.IGNORECASE,
            )
            if match:
                return clean(match.group(1))
        return None

    def _extract_edital_data(self, text: str):
        match = re.search(
            r'\bEdital\s*(?:n[º°o.]?\s*)?[:\-]?\s*\d{1,4}(?:[./-]\d{4})?[^\n]{0,50}?\bde\s+'
            r'(\d{1,2}/\d{1,2}/\d{4})',
            text[:6000],
            flags=re.IGNORECASE,
        )
        return first_date(match.group(1)) if match else None

    def _extract_prova_data(self, text: str):
        match = re.search(
            r'(?:data\s+prevista\s+da\s+prova|prova\s+(?:objetiva\s+)?(?:prevista|em))\D{0,40}'
            r'(\d{1,2}/\d{1,2}/\d{4})',
            text,
            flags=re.IGNORECASE,
        )
        return first_date(match.group(1)) if match else None

    def _extract_cargo_candidates(self, lines: list[str]) -> list[str]:
        cargos = []
        for line in lines[:120]:
            norm = (clean(line) or '').strip()
            if not norm or len(norm) < 4 or len(norm) > 120:
                continue
            if re.search(r'\b(assistente|agente|analista|auxiliar|técnico|tecnico|professor|médico|medico|enfermeiro|fiscal|contador|advogado|guarda|motorista|engenheiro|auditor|juiz|promotor|defensor)\b', norm, flags=re.IGNORECASE):
                cargos.append(norm)
            if len(cargos) >= 40:
                break
        return cargos

    def _extract_vagas(self, text: str) -> int | None:
        patterns = (
            r'(\d{1,5})\s+Quantidade\s+de\s+Vagas',
            r'(?:Total\s+de\s+Vagas|Vagas\s+ofertadas)\D{0,20}(\d{1,5})',
            r'(?<![/\d])(\d{1,5})\s+vagas\b',
        )
        for pattern in patterns:
            for m in re.finditer(pattern, text, flags=re.IGNORECASE):
                # Ensure the number and "vagas" are on the same line if matching \s+vagas
                match_str = m.group(0)
                if '\n' in match_str:
                    continue
                value = int(m.group(1))
                context = text[max(0, m.start() - 80):m.end() + 30].lower()
                # If number looks like a 4-digit calendar year (e.g. 2024, 2025, 2026, 2027)
                if 2020 <= value <= 2035:
                    if any(term in context for term in ('edital', 'concurso', 'processo', 'de 20', 'em 20', 'publicado', 'cronograma', '/20')):
                        continue
                if 0 < value <= 50000:
                    return value
        return None

    def _extract_salarios(self, text: str):
        vals = []
        for match in re.finditer(r'R\$\s*\d{1,3}(?:\.\d{3})*,\d{2}', text):
            parsed = parse_money(match.group(0))
            if parsed and parsed >= Decimal('1000'):
                vals.append(parsed)
        if vals:
            return min(vals), max(vals)
        return None, None

    def _extract_taxa(self, text: str):
        m = re.search(r'(?:taxa|inscrição|inscricao).{0,60}(R\$\s*\d{1,3}(?:\.\d{3})*,\d{2})', text, flags=re.IGNORECASE | re.DOTALL)
        if m:
            return parse_money(m.group(1))
        return None


class FCCConnector(GenericDedicatedBancaConnector):
    banca = 'FCC'
    detail_patterns = (r'/concursos/[^/]+/index\.html', r'/concursos/\w+', r'id=\d+')

    def __init__(self, base_url: str = 'https://www.concursosfcc.com.br', list_url: str | None = None):
        super().__init__(base_url=base_url, list_url=list_url or 'https://www.concursosfcc.com.br/concursoAndamento.html')

    def _extract_title(self, lines: list[str], hint: str | None) -> str:
        if hint and len(hint) >= 6 and not any(bad in hint.lower() for bad in ['diversos cargos', 'ver edital', 'saiba mais']):
            return clean(hint)
        return super()._extract_title(lines, hint)

    def _parse_detail(self, candidate: CandidateItem, html: str, *, client) -> dict[str, Any] | None:
        parsed = super()._parse_detail(candidate, html, client=client)
        if not parsed and self.mode == 'open':
            # Evaluated candidate whose registration window has ended
            self.mark_empty_evidence('evaluated_closed', f'Evaluated FCC candidate {candidate.detail_url} whose registration window has ended', candidate.detail_url)
        return parsed


class FGVConnector(GenericDedicatedBancaConnector):
    banca = 'FGV'
    detail_patterns = (r'/concursos/[^/?#]+$', r'/conhecimento/concursos/[^/?#]+$')
    _excluded_slugs = {'nosso-portfolio', 'index', 'buscar', 'busca'}

    def __init__(self, base_url: str = 'https://conhecimento.fgv.br', list_url: str | None = None):
        super().__init__(base_url=base_url, list_url=list_url or 'https://conhecimento.fgv.br/concursos')

    def _fetch_candidates(self) -> list[CandidateItem]:
        """Discover only canonical FGV contest pages.

        The old generic matcher accepted ``/concursos/nosso-portfolio#tabs``
        and other navigation fragments as contests.  FGV's listing uses one
        canonical slug per contest, so require that exact shape and reject
        fragments/query views before creating a candidate.
        """
        html = self._fetch_html(self.list_url)
        soup = BeautifulSoup(html, 'lxml')
        candidates: list[CandidateItem] = []
        seen: set[str] = set()
        for anchor in soup.select('a[href]'):
            raw_href = anchor.get('href') or ''
            url = normalize_url(self.list_url, raw_href)
            if not url:
                continue
            parsed = urlparse(url)
            if parsed.netloc.replace('www.', '') != urlparse(self.base_url).netloc.replace('www.', ''):
                continue
            match = re.fullmatch(r'/concursos/([^/?#]+)', parsed.path.rstrip('/'))
            if not match or parsed.query or parsed.fragment:
                continue
            slug = match.group(1).casefold()
            if slug in self._excluded_slugs or url in seen:
                continue
            title_hint = clean(anchor.get_text(' ', strip=True))
            if not title_hint or len(title_hint) < 12:
                title_hint = self._candidate_context_text(anchor)
            if not title_hint or any(term in title_hint.casefold() for term in (
                'aviso de privacidade', 'aviso de cookies', 'política de privacidade',
                'politica de privacidade', 'nosso portfólio', 'nosso portfolio',
            )):
                continue
            seen.add(url)
            candidates.append(CandidateItem(
                title_hint=title_hint[:500],
                detail_url=url,
                external_id=slug,
            ))
            if len(candidates) >= self.max_candidates:
                break
        return candidates

    def _extract_fgv_heading(self, soup: BeautifulSoup, fallback: str | None) -> str | None:
        for heading in soup.select('h1, h2'):
            value = clean(heading.get_text(' ', strip=True))
            if value and len(value) >= 12 and 'nosso portfolio' not in value.casefold():
                return value
        return clean(fallback)

    def _parse_detail(self, candidate: CandidateItem, html: str, *, client) -> dict[str, Any] | None:
        parsed = super()._parse_detail(candidate, html, client=client)
        if not parsed:
            return None
        soup = BeautifulSoup(html, 'lxml')
        title = self._extract_fgv_heading(soup, parsed.get('titulo'))
        if not title or 'nosso portfolio' in title.casefold() or 'nosso portfólio' in title.casefold():
            return None
        parsed['titulo'] = title

        # Rebuild publications from the official detail DOM after the strict
        # navigation/consent filter.  Privacy and cookie links are never valid
        # publication evidence, even when their URL happens to contain a file.
        publications = [
            pub for pub in parse_publications_from_dom(soup, candidate.detail_url, source='fgv')
            if is_valid_publication_title(pub.get('title'))
        ]
        parsed.setdefault('raw_data', {})['publications'] = publications
        parsed['link_edital'] = next(
            (pub.get('link') for pub in publications if pub.get('publication_type') == 'edital'),
            parsed.get('link_edital'),
        )
        if parsed.get('link_edital') and any(term in parsed['link_edital'].casefold() for term in ('privacidade', 'cookies')):
            parsed['link_edital'] = None
        parsed['content_hash'] = build_hash(parsed.get('raw_data') or {})
        return parsed


class CebraspeConnector(GenericDedicatedBancaConnector):
    banca = 'CEBRASPE'
    api_base = 'https://apis.cebraspe.org.br/cebraspe/eventos'
    mode = 'open'

    def __init__(self, base_url: str = 'https://www.cebraspe.org.br', list_url: str | None = None):
        super().__init__(base_url=base_url, list_url=list_url or 'https://www.cebraspe.org.br/concursos/')

    def _fetch_candidates(self) -> list[CandidateItem]:
        candidates: list[CandidateItem] = []
        seen: set[str] = set()
        phases = ['inscricoes-abertas'] if self.mode == 'open' else ['inscricoes-abertas', 'em-andamento']
        valid_api_payload = False
        try:
            with self._http_client() as client:
                for phase in phases:
                    r = client.get(f'{self.api_base}/tipo/concursos/fase/{phase}')
                    if r.status_code != 200:
                        continue
                    data = r.json()
                    groups = data if isinstance(data, list) else [data]
                    for grp in groups:
                        if not isinstance(grp, dict) or not isinstance(grp.get('eventos'), list):
                            continue
                        valid_api_payload = True
                        for ev in grp.get('eventos', []):
                            slug = ev.get('eventoURL')
                            if not slug or slug in seen:
                                continue
                            seen.add(slug)
                            title = clean(ev.get('eventoNomeCompleto') or ev.get('eventoNomeAbreviado') or slug)
                            status_hint = 'Inscrições abertas' if ev.get('isInscricaoAberta') else 'Em andamento'
                            candidates.append(CandidateItem(
                                title_hint=title,
                                detail_url=f'https://www.cebraspe.org.br/concursos/{slug}',
                                external_id=str(ev.get('idEvento') or slug),
                                status_hint=status_hint,
                                extra={'api_item': ev, 'slug': slug},
                            ))
                            if len(candidates) >= self.max_candidates:
                                break
        except Exception as exc:
            logger.warning('CEBRASPE candidate discovery error: %s', exc)

        # A transport/API failure is not evidence that the official catalog is
        # empty. Only a successfully decoded response with an explicit eventos
        # collection can support api_empty.
        if not candidates and valid_api_payload:
            self.mark_empty_evidence('api_empty', 'CEBRASPE REST API returned zero open events', f'{self.api_base}/tipo/concursos/fase/inscricoes-abertas')

        return candidates

    def _parse_detail(self, candidate: CandidateItem, html: str, *, client) -> dict[str, Any] | None:
        slug = (candidate.extra or {}).get('slug') or candidate.detail_url.rstrip('/').rsplit('/', 1)[-1]
        api_item = (candidate.extra or {}).get('api_item') or {}
        det = api_item
        if client is not None:
            try:
                r_det = client.get(f'{self.api_base}/{slug}')
                if r_det.status_code == 200:
                    det = r_det.json()
            except Exception as exc:
                logger.debug('CEBRASPE detail API error for %s: %s', slug, exc)

        title = clean(det.get('eventoNomeCompleto') or det.get('eventoNomeAbreviado') or candidate.title_hint or slug)
        if not title:
            return None

        city, uf = extract_city_uf(title)
        if not uf:
            m_uf = re.search(r'\b(?:do\s+Estado\s+(?:de|do|da)\s+|/)([A-Za-zÀ-ÿ ]+|[A-Z]{2})\b', title, re.I)
            if m_uf:
                _, uf = extract_city_uf(m_uf.group(0))

        vagas_str = det.get('eventoTotalVagas')
        vagas = int(vagas_str) if vagas_str and str(vagas_str).isdigit() else None
        raw_sal = det.get('eventoSalarioMaximo')
        salario_max = float(raw_sal) if isinstance(raw_sal, (int, float)) and raw_sal > 0 else (parse_money(str(raw_sal)) if raw_sal else None)
        status = 'Inscrições abertas' if det.get('isInscricaoAberta') else 'Em andamento'

        period_text = det.get('periodoInscricao') or ''
        start, end = parse_date_interval(period_text)

        cargos = [clean(c.get('area')) for c in (det.get('eventoCargos') or []) if c.get('area')]
        cargo = 'Vários cargos' if len(cargos) > 1 else (cargos[0] if cargos else None)

        pubs = []
        edital_url = None
        for f in (det.get('arquivosEdital') or []) + (det.get('arquivosGabarito') or []):
            f_title = clean(f.get('descricaoArquivo') or f.get('nome') or f.get('descricao') or 'Documento')
            filename = f.get('nomeArquivo')
            f_link = f.get('link') or f.get('url') or (f'https://cdn.cebraspe.org.br/concursos/{slug}/arquivos/{filename}' if filename else None)
            if f_link:
                p_type = normalize_publication_type(f_title)
                if p_type == 'edital' and not edital_url and f_link.endswith('.pdf'):
                    edital_url = f_link
                pubs.append({
                    'title': f_title,
                    'publication_type': p_type,
                    'link': f_link,
                    'content_hash': build_publication_hash(f_title, None, f_link, p_type),
                    'source': 'cebraspe',
                })

        raw_payload = {'api_detail': det, 'publications': pubs, 'source_list_url': self.list_url}
        resumo = build_summary(
            title, 'Concurso Público', status, start, end,
            cargo=cargo, vagas=vagas, salario_max=salario_max,
        )

        return {
            'external_id': str(det.get('idEvento') or candidate.external_id or slug),
            'banca': self.banca,
            'orgao': det.get('eventoNomeAbreviado') or title,
            'titulo': title,
            'modalidade': 'Concurso Público',
            'cargo': cargo,
            'area': None,
            'cidade': city,
            'uf': uf,
            'status': status,
            'vagas': vagas,
            'salario_min': None,
            'salario_max': salario_max,
            'escolaridade': None,
            'taxa': None,
            'prova_data': None,
            'edital_numero': None,
            'edital_data': None,
            'inscricao_inicio': start,
            'inscricao_fim': end,
            'link_pagina': candidate.detail_url,
            'link_edital': edital_url,
            'link_inscricao': f'https://www.cebraspe.org.br/concursos/{slug}',
            'resumo': resumo,
            'raw_data': raw_payload,
            'edital_pdf_text_hash': None,
            'edital_pdf_pages': None,
            'edital_pdf_excerpt': None,
            'pdf_extracted_at': None,
            'content_hash': build_hash(raw_payload),
            'fetched_at': datetime.now(UTC),
        }


class CesgranrioConnector(GenericDedicatedBancaConnector):
    banca = 'CESGRANRIO'
    # The public index is the source's current-status authority.  Some legacy
    # detail pages retain historical registration dates even while the index
    # marks the certame as ongoing.
    mode = 'all'
    detail_patterns = (r'/concurso/[^/]+/?', r'/concursos/\w+', r'id=\d+')

    def __init__(self, base_url: str = 'https://www.cesgranrio.org.br', list_url: str | None = None):
        super().__init__(base_url=base_url, list_url=list_url or 'https://www.cesgranrio.org.br/concursos/')

    def _fetch_candidates(self) -> list[CandidateItem]:
        for attempt in range(2):
            try:
                html = self._fetch_html(self.list_url)
            except Exception as exc:
                logger.warning('%s: error fetching list %s: %s', self.banca, self.list_url, exc)
                return []
            candidates = self._candidates_from_list_soup(BeautifulSoup(html, 'lxml'))
            if candidates or attempt == 1:
                return candidates
            logger.warning('%s: list page had no current cards; retrying official list', self.banca)
        return []

    def _candidates_from_list_soup(self, soup: BeautifulSoup) -> list[CandidateItem]:
        candidates: list[CandidateItem] = []
        seen: set[str] = set()
        for heading in soup.select('h3.t-entry-title'):
            anchor = heading.select_one('a[href]')
            card = heading.find_parent(class_='t-entry')
            card_text = clean(card.get_text(' ', strip=True)) if card else ''
            if not anchor or not card_text:
                continue
            if re.search(r'conclu[ií]d|vestibular', card_text, re.I):
                continue
            if not re.search(r'em andamento', card_text, re.I):
                continue
            url = normalize_url(self.list_url, anchor.get('href'))
            if not url or url in seen or not self._same_domain(url):
                continue
            seen.add(url)
            candidates.append(CandidateItem(
                title_hint=clean(heading.get_text(' ', strip=True)),
                detail_url=url,
                status_hint='Em andamento',
            ))
            if len(candidates) >= self.max_candidates:
                break
        return candidates

    def _is_valid_certame(
        self,
        title: str | None,
        orgao: str | None,
        cidade: str | None,
        uf: str | None,
        inicio,
        fim,
        edital_url: str | None,
        cargo_candidates: list[str],
        text: str,
    ) -> bool:
        # The Cesgranrio detail pages for BANESE/BASA/BNDES use a marketing
        # heading such as "Concurso BASA" and contain no municipality.  The
        # official index already supplied the certame identity, so requiring a
        # prefeitura/UF here would reject valid cards from that index.
        if title and re.search(r'\b(?:concurso|banco|transpetro|banese|basa|bndes)\b', title, re.I):
            return bool(edital_url or cargo_candidates or inicio or fim)
        return super()._is_valid_certame(
            title, orgao, cidade, uf, inicio, fim, edital_url, cargo_candidates, text,
        )

    def _parse_detail(self, candidate: CandidateItem, html: str, *, client: httpx.Client) -> dict[str, Any] | None:
        parsed = super()._parse_detail(candidate, html, client=client)
        if not parsed:
            return None

        soup = BeautifulSoup(html, 'lxml')
        article = soup.select_one('article.concurso') or soup
        heading = article.select_one('h1')
        if heading:
            title = clean(heading.get_text(' ', strip=True))
            if title:
                parsed['titulo'] = title
        if candidate.status_hint:
            parsed['status'] = candidate.status_hint
        if isinstance(parsed.get('cargo'), str) and 'armazenamento ou acesso técnico' in parsed['cargo'].casefold():
            parsed['cargo'] = None
            parsed['area'] = None

        # Cesgranrio's detail page carries institutional footer PDFs and menu
        # links.  Only a document row inside the contest article can populate
        # link_edital/publications; otherwise those values remain unknown.
        publications = parse_publications_from_dom(article, candidate.detail_url, source='cesgranrio')
        parsed.setdefault('raw_data', {})['publications'] = publications
        parsed['link_edital'] = next(
            (publication.get('link') for publication in publications
             if publication.get('link') and 'edital' in (publication.get('title') or '').casefold()),
            None,
        )
        parsed['content_hash'] = build_hash(parsed['raw_data'])
        return parsed


class IBAMConnector(GenericDedicatedBancaConnector):
    banca = 'IBAM'
    detail_patterns = (r'/detalhe\.asp\?cod=\d+', r'/concurso\.asp\?cod=\d+', r'cod=\d+')

    def __init__(self, base_url: str = 'https://www.ibam-concursos.org.br', list_url: str | None = None):
        super().__init__(base_url=base_url, list_url=list_url or 'https://www.ibam-concursos.org.br')


class IBADEConnector(GenericDedicatedBancaConnector):
    banca = 'IBADE'
    detail_patterns = (r'/edital/ver/\d+', r'/concurso\.aspx\?id=\d+', r'id=\d+')
    max_candidates = 30

    def __init__(self, base_url: str = 'https://portal.ibade.selecao.site', list_url: str | None = None):
        super().__init__(base_url=base_url, list_url=list_url or f'{self.base_url}/edital')

    def _fetch_candidates(self) -> list[CandidateItem]:
        try:
            html = self._fetch_html(self.list_url)
        except Exception as exc:
            logger.warning('%s: error fetching list %s: %s', self.banca, self.list_url, exc)
            return []

        soup = BeautifulSoup(html, 'lxml')
        section = soup.select_one('#andamento') or soup
        candidates: list[CandidateItem] = []
        seen: set[str] = set()
        for card in section.select('div.card.rounded'):
            anchor = card.select_one('a[href*="/edital/ver/"]')
            if not anchor:
                continue
            url = normalize_url(self.base_url, anchor.get('href'))
            if not url or url in seen:
                continue
            parts = [clean(node.get_text(' ', strip=True)) for node in card.select('p')]
            parts = [part for part in parts if part]
            title_hint = parts[0] if parts else clean(card.get_text(' ', strip=True))
            context = clean(card.get_text(' ', strip=True)) or ''
            if self._candidate_is_excluded(context):
                continue
            seen.add(url)
            candidates.append(CandidateItem(
                title_hint=title_hint,
                detail_url=url,
                status_hint='Em andamento',
                external_id=extract_external_id(url, [r'/edital/ver/(\d+)']),
            ))
            if len(candidates) >= self.max_candidates:
                break
        return candidates

    def _parse_detail(self, candidate: CandidateItem, html: str, *, client: httpx.Client) -> dict[str, Any] | None:
        parsed = super()._parse_detail(candidate, html, client=client)
        if not parsed:
            return None
        soup = BeautifulSoup(html, 'lxml')
        publications = parse_publications_from_dom(soup, candidate.detail_url, source='ibade')
        parsed.setdefault('raw_data', {})['publications'] = publications
        primary = next(
            (publication.get('link') for publication in publications
             if publication.get('link')
             and re.search(r'\bedital\b', publication.get('title') or '', re.IGNORECASE)
             and not re.search(r'\banexo\b', publication.get('title') or '', re.IGNORECASE)),
            None,
        )
        if primary:
            parsed['link_edital'] = primary
        parsed['content_hash'] = build_hash(parsed['raw_data'])
        return parsed


class QuadrixConnector(GenericDedicatedBancaConnector):
    banca = 'Quadrix'
    detail_patterns = (r'/informacoes/\d+/?', r'/concurso/\d+', r'id=\d+')

    def __init__(self, base_url: str = 'https://quadrix.org.br', list_url: str | None = None):
        # /index/1/ is the historical archive, not the current open feed.
        super().__init__(base_url=base_url, list_url=list_url or f'{base_url}/index/abertos/')

    def _fetch_candidates(self) -> list[CandidateItem]:
        candidates: list[CandidateItem] = []
        seen: set[str] = set()
        for tab in [self.list_url]:
            try:
                html = self._fetch_html(tab)
                soup = BeautifulSoup(html, 'lxml')
                for anchor in soup.select('a[href]'):
                    href = anchor.get('href', '').strip()
                    if '/informacoes/' in href:
                        url = normalize_url(self.base_url, href)
                        anchor_text = clean(anchor.get_text(' ', strip=True))
                        if url and url in seen and anchor_text and re.search(r'prefeitura|secretaria|conselho|tribunal|universidade', anchor_text, re.I):
                            for existing in candidates:
                                if existing.detail_url == url:
                                    existing.title_hint = anchor_text
                                    break
                        elif url and url not in seen:
                            seen.add(url)
                            title_hint = anchor_text
                            candidates.append(CandidateItem(
                                title_hint=title_hint or None,
                                detail_url=url,
                                external_id=extract_external_id(url, [r'/informacoes/(\d+)']),
                            ))
            except Exception as exc:
                logger.warning('Quadrix candidate fetch error for %s: %s', tab, exc)
        return candidates

    def _parse_detail(self, candidate: CandidateItem, html: str, *, client: httpx.Client) -> dict[str, Any] | None:
        parsed = super()._parse_detail(candidate, html, client=client)
        if not parsed:
            return None
        if candidate.title_hint and re.search(r'prefeitura|secretaria|conselho|tribunal|universidade', candidate.title_hint, re.I):
            parsed['titulo'] = candidate.title_hint
        soup = BeautifulSoup(html, 'lxml')
        pdf_text = ''
        pdf_url = parsed.get('link_edital')
        if pdf_url:
            try:
                response = client.get(pdf_url, headers={'Referer': candidate.detail_url})
                if response.content[:4] == b'%PDF':
                    pdf_text = '\n'.join((page.extract_text() or '') for page in PdfReader(BytesIO(response.content)).pages)
            except Exception as exc:
                logger.debug('Quadrix PDF extraction failed for %s: %s', pdf_url, exc)
        # 1. Cristalina / standard Quadrix multi-column table style (2 DAS VAGAS)
        quadrix_table_totals: list[int] = []
        vagas_table_section = re.search(r'\b(?:DAS\s+VAGAS|QUADRO\s+DE\s+VAGAS)\b', pdf_text, re.I)
        if vagas_table_section:
            end_section = re.search(r'\b(?:DOS\s+CARGOS|DAS\s+INSCRIÇÕES|DAS\s+PROVAS|DA\s+DIVULGAÇÃO)\b', pdf_text[vagas_table_section.start():], re.I)
            sub = pdf_text[vagas_table_section.start(): vagas_table_section.start() + end_section.start()] if end_section else pdf_text[vagas_table_section.start(): vagas_table_section.start() + 25000]
            for line in sub.splitlines():
                m_row = re.search(r'(?:Nível\s+[A-Za-z]+|[A-Za-zÀ-ÿ]+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d{1,4})\s*$', line)
                if m_row:
                    quadrix_table_totals.append(int(m_row.group(7)))
                elif re.search(r'^\s*\d{3}\b', line):
                    digits = re.findall(r'\b\d{1,4}\b', line)
                    if len(digits) >= 7:
                        quadrix_table_totals.append(int(digits[-1]))
        if quadrix_table_totals and sum(quadrix_table_totals) > 0:
            parsed['vagas'] = sum(quadrix_table_totals)
        else:
            # 2. Quadrix single/dual location row style (e.g. "... 50 Aracaju 40h")
            row_totals = []
            for line in pdf_text.splitlines():
                match = re.search(r'\b(\d{1,4})\s+([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ .\'-]{2,45})\s+\d{1,3}h\b', line)
                if match and not re.search(r'carga|horária|semanal|total de vagas', line, re.I):
                    row_totals.append(int(match.group(1)))
            if row_totals and sum(row_totals) > 0:
                parsed['vagas'] = sum(row_totals)
            elif parsed.get('vagas') and 2020 <= parsed['vagas'] <= 2035:
                parsed['vagas'] = None

        # Prefer an explicit exam-location statement from the edital when available
        location = re.search(r'(?:realizadas?|aplicadas?)\s+(?:na|em)\s+(?:cidade de\s+)?([^\n,;]{2,50}?)/(\w{2})\b', pdf_text, re.I)
        if location:
            parsed['cidade'], parsed['uf'] = clean(location.group(1)), location.group(2).upper()

        publications = parse_publications_from_dom(soup, candidate.detail_url, source=self.banca.lower())
        parsed.setdefault('raw_data', {})['publications'] = publications
        return parsed


class IDIBConnector(GenericDedicatedBancaConnector):
    banca = 'IDIB'
    detail_patterns = (r'Concurso\.aspx\?ID=\d+', r'/concurso/\d+', r'id=\d+')

    def __init__(self, base_url: str = 'https://idib.org.br', list_url: str | None = None):
        super().__init__(base_url=base_url, list_url=list_url or 'https://idib.org.br')

    def _same_domain(self, url: str) -> bool:
        return 'idib.org.br' in url.lower()

    def _parse_detail(self, candidate: CandidateItem, html: str, *, client: httpx.Client) -> dict[str, Any] | None:
        parsed = super()._parse_detail(candidate, html, client=client)
        if not parsed:
            return None
        # The landing page also contains older publication dates and a global
        # badge.  Prefer the date pair attached to the registration wording.
        detail_text = '\n'.join(text_lines(BeautifulSoup(html, 'lxml')))
        registration = re.search(
            r'inscri(?:ç|c)[õo]es?[^\n]{0,180}?\b\d{1,2}/\d{1,2}/\d{2,4}\b[^\n]{0,80}?\b\d{1,2}/\d{1,2}/\d{2,4}\b',
            detail_text, re.I,
        )
        if registration:
            start, end = parse_date_interval(registration.group(0))
            if start or end:
                parsed['inscricao_inicio'], parsed['inscricao_fim'] = start, end
                parsed['status'] = status_from_dates(start, end, fallback='Em andamento')
        # IDIB publishes the authoritative vacancy/pay tables only in the PDF;
        # its HTML detail often contains no structured table.  Recover the
        # common aggregate forms from the already downloaded PDF excerpt.
        excerpt = parsed.get('edital_pdf_excerpt') or ''
        full_text = excerpt
        pdf_url = parsed.get('link_edital')
        # IDIB requires the detail-page referer for downloads.  The generic
        # helper consequently receives HTML, so retry here in the same client
        # session and parse the complete text table when available.
        if pdf_url:
            try:
                response = client.get(pdf_url, headers={'Referer': candidate.detail_url})
                if 'pdf' in response.headers.get('content-type', '').lower() or response.content[:4] == b'%PDF':
                    full_text = '\n'.join((page.extract_text() or '') for page in PdfReader(BytesIO(response.content)).pages)
            except Exception as exc:
                logger.debug('IDIB PDF referer extraction failed for %s: %s', pdf_url, exc)
        if parsed.get('vagas') is None:
            matches = re.findall(r'(?:destinado ao provimento de|total(?:s+de)?|quantidade(?:s+total)?)[^\n]{0,120}?\b(\d{1,5})\s*(?:\([^\n]{0,80}\))?\s*vagas?', full_text, re.I)
            if matches:
                parsed['vagas'] = max(int(value) for value in matches)
        # Salary values in the IDIB table are line-separated from the label;
        # collect values from the remuneration/vencimento section and use the
        # complete table rather than the 4k-character excerpt.
        table_start = full_text.lower().find('quadro de cargos')
        table_end = full_text.lower().find('modelo de requerimento', table_start + 1) if table_start >= 0 else -1
        salary_text = full_text[table_start:table_end if table_end > table_start else None] if table_start >= 0 else full_text
        money = [parse_money(value) for value in re.findall(r'R\s*\$?\s*[\d.]+,\d{2}', salary_text)]
        money = [value for value in money if value is not None]
        fees = [v for v in money if v < 500]
        if fees and not parsed.get('taxa'):
            parsed['taxa'] = min(fees)
        salaries = [v for v in money if v >= 1000]
        if salaries:
            parsed['salario_min'] = min(salaries)
            parsed['salario_max'] = max(salaries)
        else:
            parsed['salario_min'] = None
            parsed['salario_max'] = None
        return parsed


class FEPESEConnector(GenericDedicatedBancaConnector):
    banca = 'FEPESE'
    detail_patterns = (r'/\?go=concurso&chave=\d+', r'/concursos/\d+', r'chave=\d+')

    def __init__(self, base_url: str = 'https://fepese.org.br', list_url: str | None = None):
        super().__init__(base_url=base_url, list_url=list_url or 'https://fepese.org.br/concursos/')

    def _extract_title(self, lines: list[str], hint: str | None) -> str:
        # Portal navigation begins with generic labels (Edital/Publicação do
        # Edital); the official index link is the safer identity source.
        if hint and re.search(r'processo seletivo|concurso público', hint, re.I):
            if re.search(r'prefeitura|secretaria|conselho|tribunal|universidade|município|fundação', hint, re.I):
                return hint
            return f'Processo Seletivo - Fundação FEPESE - {hint}'
        return super()._extract_title(lines, hint)

    def _same_domain(self, url: str) -> bool:
        host = urlparse(url).netloc.lower().removeprefix('www.')
        return host == 'fepese.org.br' or host.endswith('.fepese.org.br')

    def _is_detail_url(self, url: str) -> bool:
        parsed = urlparse(url)
        host = parsed.netloc.lower().removeprefix('www.')
        # FEPESE's current WordPress index links directly to one canonical
        # subdomain per certame (e.g. 2026cpcelesc.fepese.org.br), whose root
        # page is the detail/listing for that process.
        if host.endswith('.fepese.org.br') and host != 'fepese.org.br':
            return True
        return super()._is_detail_url(url)

    def _fetch_candidates(self) -> list[CandidateItem]:
        candidates: list[CandidateItem] = []
        seen: set[str] = set()
        try:
            html = self._fetch_html(self.list_url)
            soup = BeautifulSoup(html, 'lxml')
            for anchor in soup.select('a[href]'):
                url = normalize_url(self.list_url, anchor.get('href'))
                if not url or not self._is_detail_url(url):
                    continue
                parsed_url = urlparse(url)
                host = parsed_url.netloc.lower().removeprefix('www.')
                # The WordPress page also links to transparency/navigation
                # subdomains and to anchors inside portal pages.  A canonical
                # FEPESE certame is represented by the bare root of one
                # process subdomain only.
                if not host.endswith('.fepese.org.br') or host in {
                    'transparencia.fepese.org.br', 'fiscais.fepese.org.br',
                } or parsed_url.path not in {'', '/'} or parsed_url.query or parsed_url.fragment:
                    continue
                if host in seen:
                    continue
                anchor_text = clean(anchor.get_text(' ', strip=True)) or ''
                if anchor_text.lower() in {'saiba mais', 'mais informações', 'mais informacoes', 'clique aqui'}:
                    continue
                context = anchor_text if len(anchor_text) >= 15 and anchor_text.lower() not in {
                    'publicação do edital', 'publicacao do edital',
                } else None
                nearby = self._candidate_context_text(anchor) or ''
                if self._candidate_is_excluded(f'{context or ""} {nearby}'):
                    continue
                seen.add(host)
                candidates.append(CandidateItem(
                    title_hint=(context[:500] if context else f'Processo Seletivo FEPESE {host}'), detail_url=url,
                    status_hint=None,
                    external_id=extract_external_id(url, [r'^https?://([^./]+)\.fepese\.org\.br']),
                ))
                if len(candidates) >= self.max_candidates:
                    break
        except Exception as exc:
            logger.warning('FEPESE candidate fetch error: %s', exc)
        return candidates

    def _parse_detail(self, candidate: CandidateItem, html: str, *, client: httpx.Client) -> dict[str, Any] | None:
        root_soup = BeautifulSoup(html, 'lxml')
        page_title = clean(root_soup.title.get_text(' ', strip=True)) if root_soup.title else ''
        text = root_soup.get_text(' ', strip=True)

        # 1. Discover edital and cronograma tab URLs
        edital_tab_url = None
        cronograma_tab_url = None
        for a in root_soup.select('a[href]'):
            href = a.get('href') or ''
            if 'go=edital' in href.lower():
                edital_tab_url = urljoin(candidate.detail_url, href)
            elif 'go=cronograma' in href.lower():
                cronograma_tab_url = urljoin(candidate.detail_url, href)

        # 2. Extract registration interval from cronograma
        inicio, fim = None, None
        if cronograma_tab_url:
            try:
                crono_resp = client.get(cronograma_tab_url)
                crono_text = BeautifulSoup(crono_resp.content, 'lxml').get_text(' ', strip=True)
                m_dates = re.search(r'Período\s+de\s+inscrições[^\d]*(\d{1,2}/\d{1,2}/\d{4})[^\d]*(\d{1,2}/\d{1,2}/\d{4})', crono_text, re.I)
                if m_dates:
                    inicio, fim = parse_date_interval(f'{m_dates.group(1)} a {m_dates.group(2)}')
            except Exception as exc:
                logger.debug('FEPESE cronograma fetch failed for %s: %s', candidate.detail_url, exc)

        status = status_from_dates(inicio, fim, fallback='Em andamento')

        # 3. Document downloads from edital tab and root
        document_link = None
        publications = []
        seen_links = set()

        edital_html = ''
        if edital_tab_url:
            try:
                ed_resp = client.get(edital_tab_url)
                edital_html = ed_resp.text
                ed_soup = BeautifulSoup(ed_resp.content, 'lxml')
                for a in ed_soup.select('a[href]'):
                    hr = a.get('href') or ''
                    txt = clean(a.get_text(' ', strip=True)) or 'Documento'
                    if 'go=download' in hr.lower() or '.pdf' in hr.lower():
                        full_link = urljoin(candidate.detail_url, hr)
                        if full_link not in seen_links:
                            seen_links.add(full_link)
                            if not document_link:
                                document_link = full_link
                            p_type = normalize_publication_type(txt)
                            date_m = re.search(r'(\d{1,2}/\d{1,2}/\d{4})', txt)
                            p_date = datetime.strptime(date_m.group(1), '%d/%m/%Y').replace(tzinfo=UTC).isoformat() if date_m else None
                            publications.append({
                                'title': txt,
                                'publication_type': p_type,
                                'publication_date': p_date,
                                'link': full_link,
                                'content_hash': build_publication_hash(txt, p_date, full_link, p_type),
                                'source': self.banca.lower(),
                            })
            except Exception as exc:
                logger.debug('FEPESE edital tab fetch failed for %s: %s', candidate.detail_url, exc)

        # 4. Title, organ, city, UF
        host = urlparse(candidate.detail_url).netloc.lower()
        title_body = re.sub(r'^\d{4}\s*[-–]\s*', '', page_title).strip()
        if not title_body or len(title_body) < 4:
            title_body = candidate.title_hint or host
        modalidade = 'Processo Seletivo' if 'seletiv' in f'{host} {title_body} {text}'.lower() else 'Concurso Público'
        title = f'{modalidade} - {title_body}' if modalidade.lower() not in title_body.lower() else title_body

        m_org = re.search(r'\b(?:Município|Prefeitura|Câmara|Secretaria|CELESC|COMCAP|Fundação)\s+(?:de\s+)?[A-Za-zÀ-ÿ0-9 .\'’\-]{2,60}', f'{title_body} {text}', re.I)
        orgao = clean(m_org.group(0)) if m_org else title_body
        orgao = re.sub(r'\s+(?:torna|para|destinado|com|edital|inscri).*$', '', orgao or '', flags=re.I).strip(' ,-–')

        city, uf = extract_city_uf(f'{orgao} {title_body}')
        if not uf:
            uf = 'SC'
        if not city and orgao:
            m_city = re.search(r'(?:de|do|da)\s+([A-Za-zÀ-ÿ ]+)', orgao, re.I)
            if m_city:
                city = clean(m_city.group(1))

        # 5. Extract PDF fields if possible
        vagas = None
        salario_min = None
        salario_max = None
        taxa = None
        escolaridade = None
        prova_data = None
        pdf_payload, pdf_fields, excerpt, pdf_at = extract_pdf_fields_if_possible(document_link, title=title, orgao=orgao, client=client)
        if pdf_fields:
            vagas = pdf_fields.get('vagas')
            salario_min = pdf_fields.get('salario_min')
            salario_max = pdf_fields.get('salario_max')
            taxa = pdf_fields.get('taxa')
            escolaridade = pdf_fields.get('escolaridade')
            prova_data = pdf_fields.get('prova_data')
            if pdf_fields.get('cidade') and not city:
                city = pdf_fields.get('cidade')

        raw_payload = {
            'title_hint': candidate.title_hint,
            'detail_url': candidate.detail_url,
            'publications': publications,
            'pdf': pdf_payload,
            'pdf_fields': pdf_fields.get('raw_pdf_fields') if isinstance(pdf_fields, dict) else {},
            'source_list_url': self.list_url,
        }
        resumo = build_summary(title, modalidade, status, inicio, fim, vagas=vagas, salario_min=salario_min, salario_max=salario_max)

        return {
            'external_id': candidate.external_id,
            'banca': self.banca,
            'orgao': orgao,
            'titulo': title,
            'modalidade': modalidade,
            'cargo': None,
            'area': None,
            'cidade': city,
            'uf': uf,
            'status': status,
            'vagas': vagas,
            'salario_min': salario_min,
            'salario_max': salario_max,
            'escolaridade': escolaridade,
            'taxa': taxa,
            'prova_data': prova_data,
            'edital_numero': None,
            'edital_data': None,
            'inscricao_inicio': inicio,
            'inscricao_fim': fim,
            'link_pagina': candidate.detail_url,
            'link_edital': document_link,
            'link_inscricao': None,
            'resumo': resumo,
            'raw_data': raw_payload,
            'edital_pdf_text_hash': pdf_payload.get('text_hash'),
            'edital_pdf_pages': pdf_payload.get('pages'),
            'edital_pdf_excerpt': excerpt,
            'pdf_extracted_at': pdf_at,
            'content_hash': build_hash(raw_payload),
            'fetched_at': datetime.now(UTC),
        }


class IESESConnector(GenericDedicatedBancaConnector):
    banca = 'IESES'
    mode = 'all'  # Current-project filtering is API based below.
    detail_patterns = (r'https?://(?:www\.)?[a-z0-9.]+\.ieses\.org/?$',)
    allowed_hosts = ('ieses.org',)

    def __init__(self, base_url: str = 'https://ieses.org', list_url: str | None = None):
        canonical = 'https://ieses.org'
        super().__init__(base_url=canonical, list_url=list_url or canonical + '/projetos')
        self._historical_rejected = 0

    def _fetch_candidates(self) -> list[CandidateItem]:
        api_url = f'{self.base_url}/projetos/api'
        with self._http_client() as client:
            response = client.get(api_url, params={'offset': 0, 'limit': 100})
            self.run_data.http_status = response.status_code
            response.raise_for_status()
            payload = response.json()
        projects = payload.get('projetos') if isinstance(payload, dict) else None
        if not isinstance(projects, list):
            raise ValueError('IESES API did not return a projetos list')

        current_year = datetime.now(UTC).year
        candidates: list[CandidateItem] = []
        historical = 0
        for project in projects:
            if not isinstance(project, dict):
                continue
            initial = clean(project.get('dataInicial')) or ''
            year_match = re.search(r'\b(20\d{2})\b', initial)
            if not year_match or int(year_match.group(1)) < current_year:
                historical += 1
                continue
            detail_url = (clean(project.get('url')) or '').replace('\r', '').strip()
            if not detail_url:
                historical += 1
                continue
            title = clean(f'{project.get("evento") or ""} - {project.get("entidade") or ""}')
            external_id = ':'.join(filter(None, [
                clean(project.get('projectTokenKey')),
                clean(project.get('pasta')),
            ]))
            candidates.append(CandidateItem(
                title_hint=title,
                detail_url=detail_url,
                external_id=external_id or None,
                extra={'api_project': project},
            ))
        self._historical_rejected = historical
        self.run_data.diagnostics_payload.update({
            'api': api_url,
            'api_total': len(projects),
            'current_projects': len(candidates),
            'historical_projects': historical,
        })
        return candidates

    def crawl_with_diagnostics(self):
        result = super().crawl_with_diagnostics()
        result.run_data.candidates_found += self._historical_rejected
        result.run_data.candidates_rejected += self._historical_rejected
        return result

    def _is_valid_certame(
        self,
        title: str | None,
        orgao: str | None,
        cidade: str | None,
        uf: str | None,
        inicio,
        fim,
        edital_url: str | None,
        cargo_candidates: list[str],
        text: str,
    ) -> bool:
        # Candidate identity is supplied by the official /projetos API. Some
        # project pages use a generic H2 and no city, so the generic identity
        # gate would incorrectly reject an otherwise documented certame.
        return bool(
            title
            and edital_url
            and re.search(r'\b(?:concurso|processo\s+seletivo)\b', title, flags=re.IGNORECASE)
        )

    @staticmethod
    def _pdf_inscription_interval(excerpt: str | None):
        if not excerpt:
            return None, None
        match = re.search(
            r'(?:no\s+per[íi]odo\s+de|in[íi]cio\s+do\s+per[íi]odo\s+de\s+inscri[^\n]{0,60})'
            r'.{0,120}?(\d{1,2}\s+de\s+[A-Za-zÀ-ÿ]+\s+de\s+\d{4})'
            r'.{0,160}?(\d{1,2}\s+de\s+[A-Za-zÀ-ÿ]+\s+de\s+\d{4})',
            excerpt,
            flags=re.IGNORECASE | re.DOTALL,
        )
        if not match:
            return None, None
        return first_date(match.group(1)), first_date(match.group(2))

    @staticmethod
    def _ieses_publications(soup: BeautifulSoup, base_url: str) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        seen: set[str] = set()
        for anchor in soup.select('a[href]'):
            href = clean(anchor.get('href'))
            if not href or '.pdf' not in href.lower():
                continue
            section = anchor.find_parent('section')
            section_id = section.get('id') if section else None
            title = clean(anchor.get_text(' ', strip=True)) or 'Documento oficial'
            title = re.sub(r'^\d{1,2}/\d{1,2}/\d{4}\s*[-–]?\s*', '', title)
            title = re.sub(r'\s*\(abre em nova janela\)\s*$', '', title, flags=re.IGNORECASE)
            if section_id == 'passo04' and 'gabarito' not in title.lower():
                continue
            if section_id not in {'passo03', 'passo04', 'passo06', 'passo01'}:
                continue
            link = normalize_url(base_url, href)
            if not link or link in seen:
                continue
            seen.add(link)
            date_tag = anchor.find('time')
            date_value = clean(date_tag.get('datetime')) if date_tag else None
            parsed_date = first_date(date_value)
            publication_date = parsed_date.isoformat() if parsed_date else None
            publication_type = normalize_publication_type(title)
            results.append({
                'title': title,
                'publication_type': publication_type,
                'publication_date': publication_date,
                'link': link,
                'content_hash': build_publication_hash(title, publication_date, link, publication_type),
                'source': 'ieses',
            })
        return results[:120]

    def _parse_detail(self, candidate: CandidateItem, html: str, *, client: httpx.Client) -> dict[str, Any] | None:
        project = candidate.extra.get('api_project') or {}
        parsed = super()._parse_detail(candidate, html, client=client)
        if not parsed:
            return None

        soup = BeautifulSoup(html, 'lxml')
        is_registration_open = bool(re.search(
            r'window\.INSCRICOES_ABERTA\s*=\s*true',
            html,
            flags=re.IGNORECASE,
        ))
        pdf_inicio, pdf_fim = self._pdf_inscription_interval(parsed.get('edital_pdf_excerpt'))
        status = status_from_dates(
            pdf_inicio,
            pdf_fim,
            fallback='Inscrições abertas' if is_registration_open else 'Em andamento',
        )
        page_title = next(
            (
                clean(node.get_text(' ', strip=True))
                for node in soup.select('h1, h2, h3')
                if re.search(r'\b(?:concurso|processo\s+seletivo)\b', node.get_text(' ', strip=True), re.I)
                and re.search(r'\bedital\b', node.get_text(' ', strip=True), re.I)
            ),
            None,
        )
        title = page_title or clean(f'{project.get("evento") or ""} - {project.get("entidade") or ""}') or parsed['titulo']
        orgao = clean(project.get('entidade')) or clean(project.get('orgao')) or parsed.get('orgao')
        publications = self._ieses_publications(soup, candidate.detail_url)
        raw_payload = parsed.get('raw_data') or {}
        raw_payload.update({
            'api_project': project,
            'publications': publications,
            'registration_open_marker': is_registration_open,
            'source_list_url': self.list_url,
        })
        inicio = pdf_inicio or parsed.get('inscricao_inicio')
        fim = pdf_fim or parsed.get('inscricao_fim')
        if inicio and fim and fim < inicio:
            inicio = None
            fim = None
        parsed.update({
            'external_id': candidate.external_id,
            'titulo': title,
            'orgao': orgao,
            'status': status,
            'inscricao_inicio': inicio,
            'inscricao_fim': fim,
            'raw_data': raw_payload,
            'resumo': build_summary(
                title,
                parsed.get('modalidade'),
                status,
                inicio,
                fim,
                cargo=parsed.get('cargo'),
                area=parsed.get('area'),
                vagas=parsed.get('vagas'),
                salario_min=parsed.get('salario_min'),
                salario_max=parsed.get('salario_max'),
            ),
            'content_hash': build_hash(raw_payload),
        })
        return parsed


class FAFIPAConnector(GenericDedicatedBancaConnector):
    banca = 'Fundação FAFIPA'
    detail_patterns = (r'/informacoes/\d+/?', r'/concurso\.aspx\?id=\d+', r'id=\d+')

    def __init__(self, base_url: str = 'https://concursos.fundacaofafipa.org.br', list_url: str | None = None):
        super().__init__(base_url=base_url, list_url=list_url or f'{self.base_url}/')

    def _fetch_candidates(self) -> list[CandidateItem]:
        candidates = super()._fetch_candidates()
        # The public root mixes expired and upcoming cards with the live
        # section.  FAFIPA explicitly marks the rows in scope with
        # "Inscrições Abertas"; retain only those rows for this *_open source.
        return [candidate for candidate in candidates if candidate.status_hint == 'Inscrições abertas']
