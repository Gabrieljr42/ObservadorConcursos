from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

import httpx
from bs4 import BeautifulSoup

from app.connectors.base import CandidateItem, CrawlResult, CrawlRunData
from app.publications import parse_publications_from_dom, parse_publications_from_lines

from app.connectors.common import (
    HEADERS,
    build_hash,
    build_summary,
    classify_area,
    classify_area_from_many,
    clean,
    extract_city_uf,
    extract_external_id,
    extract_pdf_fields_if_possible,
    normalize_url,
    parse_date_interval,
    parse_money,
    status_from_dates,
    text_lines,
)


@dataclass(slots=True)
class IMESOCandidate:
    title_hint: str | None
    detail_url: str
    status_hint: str | None = None


class IMESOConnector:
    """Connector for portal.imeso.com.br.

    The IMESO listing page includes all statuses in the same HTML. The first
    implementation collected every "/edital/ver" link, which imported hundreds
    of old/finalized certames and also confused section titles such as
    "EXTRATO E LEGISLAÇÃO" with job names. This connector is intentionally
    conservative: the open preset only captures the "EM INSCRIÇÃO" block, and
    the detail parser ignores navigation/publication labels.
    """

    banca = 'IMESO'
    mode = 'open'  # open | ongoing | all

    SECTION_TITLES = {
        'FUTUROS',
        'EM INSCRIÇÃO',
        'EM INSCRICAO',
        'EM ANDAMENTO',
        'FINALIZADOS',
        'SUSPENSOS E CANCELADOS',
        'CONCURSOS E SELETIVOS',
    }
    BAD_TITLE_LINES = {
        'concursos e seletivos',
        'página inicial',
        'pagina inicial',
        'ver edital',
        'informações',
        'informacoes',
        'arquivos disponíveis',
        'arquivos disponiveis',
        'vagas',
        'extrato e legislação',
        'extrato e legislacao',
        'download',
    }
    FILE_SECTION_LABELS = {
        'extrato e legislação', 'extrato e legislacao', 'download', 'arquivos disponíveis',
        'arquivos disponiveis', 'comunicado', 'errata', 'resultado', 'homologação',
        'homologacao', 'gabarito', 'julgamento', 'recurso', 'lista geral', 'laudos médicos',
        'laudos medicos', 'convocação', 'convocacao', 'mapa de candidato', 'formulário',
        'formulario', 'decreto', 'portaria', 'local e horário', 'local e horario',
    }

    def __init__(self, base_url: str, list_url: str | None = None):
        self.base_url = base_url.rstrip('/')
        self.list_url = list_url or f'{self.base_url}/edital'

    def crawl(self) -> list[dict[str, Any]]:
        return self.crawl_with_diagnostics().items

    def crawl_with_diagnostics(self) -> CrawlResult:
        run_data = CrawlRunData()
        try:
            candidates = self._fetch_candidates()
            run_data.candidates_found = len(candidates)
            run_data.http_status = 200
            items: list[dict[str, Any]] = []
            with httpx.Client(timeout=60.0, follow_redirects=True, headers=HEADERS) as client:
                for candidate in candidates:
                    try:
                        response = client.get(candidate.detail_url)
                        response.raise_for_status()
                        parsed = self._parse_detail(candidate, response.text, client=client)
                        if parsed:
                            items.append(parsed)
                        else:
                            run_data.candidates_rejected += 1
                    except Exception:
                        run_data.candidates_rejected += 1
            if items:
                run_data.status = 'success'
            else:
                run_data.status = 'empty_valid'
                run_data.diagnostics_payload['empty_evidence'] = True
            return CrawlResult(items=items, run_data=run_data)
        except Exception as exc:
            run_data.status = 'failed'
            run_data.error_message = str(exc)
            run_data.error_type = exc.__class__.__name__
            return CrawlResult(items=[], run_data=run_data)

    def _fetch_candidates(self) -> list[IMESOCandidate]:
        with httpx.Client(timeout=60.0, follow_redirects=True, headers=HEADERS) as client:
            response = client.get(self.list_url)
            response.raise_for_status()
        soup = BeautifulSoup(response.text, 'lxml')

        # For the open preset, the reliable detail links are the buttons whose
        # text says "Inscrições Abertas" inside the "EM INSCRIÇÃO" section.
        candidates: list[IMESOCandidate] = []
        seen: set[str] = set()
        anchors = soup.select('a[href]')

        for anchor in anchors:
            href = anchor.get('href', '')
            if '/edital/ver/' not in href:
                continue
            text = clean(anchor.get_text(' ', strip=True)) or ''
            lowered_text = text.lower()
            url = normalize_url(self.list_url, href)
            if not url or url in seen:
                continue

            include = False
            status_hint = None
            if self.mode == 'open':
                include = 'inscri' in lowered_text and 'abert' in lowered_text
                status_hint = 'Inscrições abertas'
            elif self.mode == 'ongoing':
                include = 'mais detalhes' in lowered_text
                status_hint = 'Em andamento'
            else:
                include = True
                status_hint = 'Inscrições abertas' if ('inscri' in lowered_text and 'abert' in lowered_text) else None

            if not include:
                continue
            seen.add(url)
            candidates.append(IMESOCandidate(title_hint=self._nearby_text(anchor), detail_url=url, status_hint=status_hint))

        # Defensive fallback: if the text of the button changes, parse only the
        # lines between EM INSCRIÇÃO and EM ANDAMENTO and pair them with the first
        # /edital/ver links in the same order.
        if not candidates and self.mode == 'open':
            open_links = [normalize_url(self.list_url, a.get('href')) for a in anchors if '/edital/ver/' in (a.get('href') or '')]
            open_links = [u for u in open_links if u]
            blocks = self._listing_blocks(text_lines(soup), target='EM INSCRIÇÃO')
            for idx, block in enumerate(blocks):
                if idx >= len(open_links):
                    break
                url = open_links[idx]
                if url in seen:
                    continue
                seen.add(url)
                candidates.append(IMESOCandidate(title_hint=' | '.join(block[:3]), detail_url=url, status_hint='Inscrições abertas'))

        return candidates

    def _nearby_text(self, anchor) -> str | None:
        for parent in [anchor.parent, anchor.parent.parent if anchor.parent else None, anchor.parent.parent.parent if anchor.parent and anchor.parent.parent else None]:
            if parent:
                value = clean(parent.get_text(' ', strip=True))
                if value and len(value) > 8:
                    return value[:500]
        return clean(anchor.get_text(' ', strip=True))

    def _listing_blocks(self, lines: list[str], *, target: str) -> list[list[str]]:
        target_norm = self._norm(target)
        start = None
        end = len(lines)
        for idx, line in enumerate(lines):
            if self._norm(line) == target_norm:
                start = idx + 1
                continue
            if start is not None and self._norm(line) in {self._norm(v) for v in self.SECTION_TITLES if self._norm(v) != target_norm}:
                end = idx
                break
        if start is None:
            return []
        relevant = [line for line in lines[start:end] if line != '* * *']
        blocks: list[list[str]] = []
        current: list[str] = []
        for line in relevant:
            if re.search(r'^(?:Concurso|Processo Seletivo)', line, flags=re.IGNORECASE) and current:
                blocks.append(current)
                current = []
            current.append(line)
        if current:
            blocks.append(current)
        return blocks

    def _parse_detail(self, candidate: IMESOCandidate, html: str, *, client: httpx.Client) -> dict[str, Any]:
        soup = BeautifulSoup(html, 'lxml')
        lines = text_lines(soup)
        text = '\n'.join(lines)

        title = self._extract_title(lines, candidate.title_hint)
        orgao = self._extract_orgao(lines, title)
        cidade, uf = self._extract_city_uf(lines, orgao)
        modalidade = self._infer_modalidade(title)
        inicio, fim = self._extract_inscricoes(lines, text)
        status = status_from_dates(inicio, fim, fallback=candidate.status_hint or 'Em andamento')
        edital_numero = self._extract_edital_numero(title)
        edital_url = self._extract_download_link(soup, candidate.detail_url)
        inscricao_url = self._extract_inscricao_link(soup, candidate.detail_url)
        external_id = extract_external_id(candidate.detail_url, [r'/edital/ver/(\d+)'])

        pdf_payload, pdf_fields, excerpt, pdf_at = extract_pdf_fields_if_possible(edital_url, title=title, orgao=orgao, client=client)
        cargo_candidates = self._extract_cargo_candidates(lines)
        cargo = pdf_fields.get('cargo') or self._summarize_cargos(cargo_candidates)
        cargo_text = ' '.join(cargo_candidates[:40])
        # Prefer the visible job table over PDF heuristics. PDF text often contains
        # generic education/medical language that misclassifies ACS as educacao.
        area = classify_area_from_many(cargo_candidates, title, orgao, cargo) or pdf_fields.get('area')
        # Prefer the explicit line from the HTML detail page (e.g. "Berilo - MG")
        # over a PDF/errata extraction like "Prefeitura Municipal de Berilo".
        cidade = cidade or pdf_fields.get('cidade')
        html_vagas = None
        m_vagas = re.search(r'(?:total\s+de\s+vagas|vagas\s+ofertadas|vagas)\s*[:\-–]?\s*(\d{1,5})', text, flags=re.IGNORECASE)
        if m_vagas:
            html_vagas = int(m_vagas.group(1))
        vagas = self._sanitize_vagas(pdf_fields.get('vagas') or html_vagas, cargo_candidates)
        salario_min, salario_max = self._extract_salary_range(lines, pdf_fields)
        escolaridade = pdf_fields.get('escolaridade') or self._extract_escolaridade(lines)

        publications = parse_publications_from_dom(soup, candidate.detail_url, source='imeso')
        if not publications:
            publications = parse_publications_from_lines(lines, source='imeso')
        raw_payload = {
            'title_hint': candidate.title_hint,
            'detail_url': candidate.detail_url,
            'cargo_candidates': cargo_candidates[:30],
            'lines_sample': lines[:120],
            'publications': publications,
            'pdf': pdf_payload,
            'pdf_fields': pdf_fields.get('raw_pdf_fields') or {},
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
            'cidade': cidade,
            'uf': uf,
            'status': status,
            'vagas': vagas,
            'salario_min': salario_min,
            'salario_max': salario_max,
            'escolaridade': escolaridade,
            'taxa': pdf_fields.get('taxa'),
            'prova_data': pdf_fields.get('prova_data'),
            'edital_numero': edital_numero,
            'edital_data': None,
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

    def _sanitize_vagas(self, value: Any, cargo_candidates: list[str]) -> int | None:
        try:
            vagas = int(value) if value is not None else None
        except (TypeError, ValueError):
            return None
        if not vagas:
            return None
        # In IMESO PDFs, "1" is commonly a section number/table artifact. If
        # the HTML shows several cargos, storing vagas=1 is worse than unknown.
        if vagas <= 1 and len(cargo_candidates) > 1:
            return None
        return vagas

    def _extract_title(self, lines: list[str], title_hint: str | None) -> str:
        # The detail page repeats the real title just after VER EDITAL and again
        # after INFORMAÇÕES. Ignore portal/menu labels.
        for idx, line in enumerate(lines[:80]):
            if self._norm(line) == 'VER EDITAL':
                for next_line in lines[idx + 1: idx + 8]:
                    if self._looks_like_title(next_line):
                        return next_line
        for idx, line in enumerate(lines[:100]):
            if self._norm(line) in {'INFORMAÇÕES', 'INFORMACOES'}:
                for next_line in lines[idx + 1: idx + 8]:
                    if self._looks_like_title(next_line):
                        return next_line
        if title_hint:
            for part in re.split(r'\s{2,}|\s\|\s', title_hint):
                part = clean(part)
                if part and self._looks_like_title(part):
                    return part
            if clean(title_hint):
                return clean(title_hint)
        return 'Edital IMESO'

    def _looks_like_title(self, line: str | None) -> bool:
        if not line:
            return False
        lowered = self._norm(line).lower()
        if lowered in self.BAD_TITLE_LINES:
            return False
        return bool(re.search(r'\b(?:Concurso|Processo Seletivo|Edital)\b', line, flags=re.IGNORECASE)) and len(line) >= 8

    def _extract_orgao(self, lines: list[str], title: str) -> str | None:
        for idx, line in enumerate(lines[:120]):
            if self._norm(line) in {'INFORMAÇÕES', 'INFORMACOES'}:
                for next_line in lines[idx + 1: idx + 12]:
                    if next_line == title or self._looks_like_title(next_line):
                        continue
                    if self._looks_like_orgao(next_line):
                        return clean(next_line)
        for line in lines[:120]:
            if self._looks_like_orgao(line):
                return clean(line)
        return None

    def _looks_like_orgao(self, line: str | None) -> bool:
        if not line:
            return False
        lowered = line.lower()
        if 'instituto mineiro educar' in lowered:
            return False
        return bool(re.search(r'\b(?:PREFEITURA|CÂMARA|CAMARA|CONSÓRCIO|CONSORCIO|SECRETARIA|CONSELHO)\b', line, flags=re.IGNORECASE))

    def _extract_city_uf(self, lines: list[str], orgao: str | None):
        # Prefer explicit location lines like "Berilo - MG" / "Conselheiro Pena - MG".
        # They are more precise than organization labels such as "PREFEITURA MUNICIPAL DE .../MG".
        for line in lines[:140]:
            cidade, uf = extract_city_uf(line)
            if cidade and uf and not re.search(r'prefeitura|câmara|camara|munic[ií]pio', cidade, flags=re.IGNORECASE):
                return cidade, uf
        for value in [orgao] + lines[:120]:
            cidade, uf = extract_city_uf(value)
            if cidade or uf:
                return cidade, uf
        return None, None

    def _infer_modalidade(self, title: str) -> str | None:
        lowered = title.lower()
        if 'processo seletivo simplificado' in lowered:
            return 'Processo Seletivo Simplificado'
        if 'processo seletivo público' in lowered or 'processo seletivo publico' in lowered:
            return 'Processo Seletivo Público'
        if 'processo seletivo' in lowered:
            return 'Processo Seletivo'
        if 'concurso público' in lowered or 'concurso publico' in lowered:
            return 'Concurso Público'
        return 'Concurso'

    def _extract_inscricoes(self, lines: list[str], text: str):
        for idx, line in enumerate(lines):
            if self._norm(line).lower() == 'inscrições de' or self._norm(line).lower() == 'inscricoes de':
                chunk = ' '.join(lines[idx: idx + 5])
                return parse_date_interval(chunk)
        match = re.search(r'Per[ií]odo de Inscri[cç][aã]o\s+De:\s*([^\n]+)\s+At[eé]:\s*([^\n]+)', text, flags=re.IGNORECASE)
        if match:
            return parse_date_interval(f'{match.group(1)} até {match.group(2)}')
        return parse_date_interval(text[:3000])

    def _extract_edital_numero(self, title: str) -> str | None:
        match = re.search(r'(\d{1,4}/\d{4})', title)
        return match.group(1) if match else None

    def _extract_inscricao_link(self, soup: BeautifulSoup, base_url: str) -> str | None:
        candidates: list[tuple[int, str]] = []
        for anchor in soup.select('a[href]'):
            text = (clean(anchor.get_text(' ', strip=True)) or '').lower()
            href = anchor.get('href') or ''
            if not href or any(token in href.lower() for token in ('.pdf', '.doc', '.docx', 'download')):
                continue
            if 'realizar inscri' in text or 'inscreva-se' in text or 'inscreva' in text:
                priority = 0
            elif 'inscri' in text and 'acompanhar' not in text:
                priority = 1
            else:
                continue
            url = normalize_url(base_url, href)
            if url:
                candidates.append((priority, url))
        return min(candidates, key=lambda item: item[0])[1] if candidates else None

    def _extract_download_link(self, soup: BeautifulSoup, base_url: str) -> str | None:
        # IMESO lists many downloadable files. Prefer the actual edital file,
        # usually the oldest/main file with text like "EDITAL RETIFICADO...".
        # Avoid latest publications such as erratas, recursos, resultados etc.
        scored: list[tuple[int, str]] = []
        bad_terms = ['errata', 'recurso', 'resultado', 'homologação', 'homologacao', 'gabarito', 'laudo', 'lista', 'convocação', 'convocacao', 'resposta', 'formulário', 'formulario']
        for anchor in soup.select('a[href]'):
            href = anchor.get('href')
            url = normalize_url(base_url, href)
            if not url or '#arquivos' in url:
                continue
            own_text = clean(anchor.get_text(' ', strip=True)) or ''
            prev_texts = []
            for prev in anchor.find_all_previous(string=True, limit=8):
                value = clean(str(prev))
                if value:
                    prev_texts.append(value)
            context = ' '.join(reversed(prev_texts[-6:] + [own_text]))
            lowered = f'{context} {url}'.lower()
            if not ('.pdf' in lowered or 'download' in lowered or 's3.' in lowered or 'cdn.' in lowered):
                continue
            score = 0
            if 'edital' in lowered:
                score += 100
            if 'retificado' in lowered or 'conforme errata' in lowered:
                score += 60
            if 'consolidado' in lowered:
                score += 70
            # Penalize erratas/results, but not enough to beat an edital-retificado file.
            for term in bad_terms:
                if term in lowered:
                    score -= 45
            if 'download' in lowered:
                score += 5
            if score > 0:
                scored.append((score, url))
        if not scored:
            return None
        scored.sort(key=lambda item: item[0], reverse=True)
        return scored[0][1]

    def _extract_cargo_candidates(self, lines: list[str]) -> list[str]:
        candidates: list[str] = []
        seen_vagas = False
        for line in lines:
            norm = self._norm(line).lower()
            if norm == 'vagas':
                seen_vagas = True
                continue
            if not seen_vagas:
                continue
            if norm.startswith('sobre a imeso') or norm == 'contato':
                break
            if not self._looks_like_cargo_line(line):
                continue
            candidates.append(self._clean_cargo_label(line))
        # Deduplicate while preserving order.
        deduped: list[str] = []
        seen: set[str] = set()
        for item in candidates:
            key = item.lower()
            if key not in seen:
                seen.add(key)
                deduped.append(item)
        return deduped

    def _looks_like_cargo_line(self, line: str) -> bool:
        lowered = line.lower()
        if any(bad in lowered for bad in self.FILE_SECTION_LABELS):
            return False
        # Avoid treating salary values like "1.500,00" or dates as cargos.
        if re.fullmatch(r'\d{1,3}(?:\.\d{3})*,\d{2}', line.strip()):
            return False
        if re.fullmatch(r'\d{1,2}/\d{1,2}/\d{2,4}', line.strip()):
            return False
        if re.match(r'^\d{1,3}\s*[.\-–]\s*\S.{2,140}$', line):
            return True
        return False

    def _clean_cargo_label(self, line: str) -> str:
        return clean(re.sub(r'^\d{1,3}\s*[.\-–]\s*', '', line)) or line

    def _summarize_cargos(self, cargos: list[str]) -> str | None:
        if not cargos:
            return None
        if len(cargos) == 1:
            return cargos[0]
        return 'Vários cargos'

    def _extract_salary_range(self, lines: list[str], pdf_fields: dict[str, Any]):
        values = []
        for key in ('salario_min', 'salario_max'):
            value = pdf_fields.get(key)
            if value is not None:
                try:
                    values.append(parse_money(str(value)) or value)
                except Exception:
                    pass
        for idx, line in enumerate(lines):
            if self._norm(line).lower() == 'remuneração' or self._norm(line).lower() == 'remuneracao':
                for lookahead in lines[idx + 1: idx + 4]:
                    parsed = parse_money(lookahead)
                    if parsed is not None:
                        values.append(parsed)
                        break
        valid = []
        from decimal import Decimal
        for value in values:
            try:
                dec = Decimal(str(value))
            except Exception:
                continue
            if dec >= Decimal('1000'):
                valid.append(dec)
        return (min(valid), max(valid)) if valid else (None, None)

    def _extract_escolaridade(self, lines: list[str]) -> str | None:
        for line in lines:
            if re.search(r'\b(?:Ensino|Nível|Nivel|Superior|Fundamental|Alfabetizado)\b', line, flags=re.IGNORECASE):
                if len(line) <= 90 and not re.match(r'^\d', line):
                    return clean(line)
        return None

    def _norm(self, value: str | None) -> str:
        return clean(value or '') or ''


class IMESOOpenConnector(IMESOConnector):
    mode = 'open'


class IMESOOngoingConnector(IMESOConnector):
    mode = 'ongoing'


class IMESOAllConnector(IMESOConnector):
    mode = 'all'
