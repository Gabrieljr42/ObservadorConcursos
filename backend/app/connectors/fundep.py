from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import httpx
from bs4 import BeautifulSoup

from app.connectors.base import CandidateItem, CrawlResult, CrawlRunData
from app.publications import parse_publications_from_lines

from app.connectors.common import (
    HEADERS,
    build_hash,
    build_summary,
    classify_area,
    clean,
    extract_city_uf,
    extract_external_id,
    extract_pdf_fields_if_possible,
    extract_pdf_link,
    normalize_url,
    parse_date_interval,
    parse_money,
    status_from_dates,
    text_lines,
)


@dataclass(slots=True)
class FundepCandidate:
    title_hint: str | None
    detail_url: str
    status_hint: str | None = None


class FundepConnector:
    banca = 'FUNDEP'
    mode = 'open'  # open | all

    def __init__(self, base_url: str, list_url: str | None = None):
        self.base_url = base_url.rstrip('/')
        # The old Concursos.aspx page is essentially the historical/all listing.
        # For the MVP source "fundep_open", use the home/default page, which
        # contains Inscrições Abertas and Em Andamento cards with Saiba Mais links.
        if not list_url or 'Concursos.aspx' in list_url:
            self.list_url = f'{self.base_url}/site/site/default.aspx'
        else:
            self.list_url = list_url

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

    def _fetch_candidates(self) -> list[FundepCandidate]:
        with httpx.Client(timeout=60.0, follow_redirects=True, headers=HEADERS) as client:
            response = client.get(self.list_url)
            response.raise_for_status()
        soup = BeautifulSoup(response.text, 'lxml')
        candidates: list[FundepCandidate] = []
        seen: set[str] = set()

        anchors = soup.select('a[href]')
        for anchor in anchors:
            href = anchor.get('href', '')
            url = normalize_url(self.list_url, href)
            if not url:
                continue
            lowered_url = url.lower()
            text = clean(anchor.get_text(' ', strip=True)) or ''
            lowered_text = text.lower()
            if not (('detalheconcurso.aspx' in lowered_url and 'codigoconcurso=' in lowered_url) or '/informacoes/' in lowered_url):
                continue
            if url in seen:
                continue

            parent_text = self._nearby_text(anchor)
            status_hint = self._infer_status_from_card(parent_text)

            # On the default home page, the first cards are: inscrições abertas,
            # em andamento, homologados. For fundep_open, keep open + ongoing,
            # skip homologados and historical lists.
            if self.mode == 'open' and status_hint == 'Homologado':
                continue
            if self.mode == 'open' and 'vestibular' in (parent_text or '').lower():
                continue
            if self.mode == 'open' and 'Concursos.aspx' in self.list_url and 'detalheconcurso' in lowered_url:
                # Defensive: if someone forces the historical page, only collect
                # recent/active-looking 2026 items instead of thousands of old rows.
                if '2026' not in parent_text and '2025/2026' not in parent_text:
                    continue

            seen.add(url)
            candidates.append(FundepCandidate(title_hint=parent_text, detail_url=url, status_hint=status_hint))

        # If the default page has 3 cards, keep only the first two for the open
        # preset (Inscrições Abertas + Em Andamento), unless status labels were clear.
        if self.mode == 'open' and self.list_url.lower().endswith('default.aspx') and len(candidates) > 2:
            non_homologados = [c for c in candidates if c.status_hint != 'Homologado']
            candidates = non_homologados[:2]

        return candidates

    def _nearby_text(self, anchor) -> str | None:
        for parent in [anchor.parent, anchor.parent.parent if anchor.parent else None, anchor.parent.parent.parent if anchor.parent and anchor.parent.parent else None]:
            if parent:
                value = clean(parent.get_text(' ', strip=True))
                if value and len(value) > 8:
                    return value[:700]
        return clean(anchor.get_text(' ', strip=True))

    def _infer_status_from_card(self, text: str | None) -> str | None:
        lowered = (text or '').lower()
        if 'homologado' in lowered:
            return 'Homologado'
        if 'inscrições abertas' in lowered or 'inscricoes abertas' in lowered or 'iniciou em' in lowered:
            return 'Inscrições abertas'
        if 'em andamento' in lowered or 'publicado em' in lowered:
            return 'Em andamento'
        return None

    def _parse_detail(self, candidate: FundepCandidate, html: str, *, client: httpx.Client) -> dict[str, Any]:
        soup = BeautifulSoup(html, 'lxml')
        lines = text_lines(soup)
        text = '\n'.join(lines)
        title = self._extract_title(lines, candidate.title_hint)
        orgao = self._extract_orgao(title, lines, candidate.title_hint)
        cidade, uf = self._extract_city_uf(title, orgao, text)
        modalidade = self._infer_modalidade(title, text)
        if self._is_excluded_certame(title, modalidade, text):
            return None
        inicio, fim = self._extract_inscricoes(text)
        status = status_from_dates(inicio, fim, fallback=candidate.status_hint or 'Em andamento')
        edital_url = extract_pdf_link(soup, candidate.detail_url)
        inscricao_url = self._extract_inscricao_link(soup, candidate.detail_url)
        external_id = extract_external_id(candidate.detail_url, [r'CodigoConcurso=(\d+)', r'/informacoes/(\d+)'])

        pdf_payload, pdf_fields, excerpt, pdf_at = extract_pdf_fields_if_possible(edital_url, title=title, orgao=orgao, client=client)
        cargo_candidates = self._extract_cargo_candidates(lines)
        cargo = pdf_fields.get('cargo') or self._extract_cargo(text, cargo_candidates)
        cargo_text = ' '.join(cargo_candidates[:40])
        area = classify_area(cargo_text, title, orgao, cargo) or pdf_fields.get('area')
        vagas = pdf_fields.get('vagas') or self._extract_vagas(text, lines)
        salario_min, salario_max = self._extract_salarios(text, pdf_fields)
        taxa = pdf_fields.get('taxa') or self._extract_taxa(text)
        prova_data = pdf_fields.get('prova_data') or self._extract_prova_data(text)

        publications = parse_publications_from_lines(lines, source='fundep')
        raw_payload = {
            'title_hint': candidate.title_hint,
            'detail_url': candidate.detail_url,
            'lines_sample': lines[:140],
            'cargo_candidates': cargo_candidates[:60],
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
            'cidade': cidade or pdf_fields.get('cidade'),
            'uf': uf or pdf_fields.get('uf'),
            'status': status,
            'vagas': vagas,
            'salario_min': salario_min,
            'salario_max': salario_max,
            'escolaridade': pdf_fields.get('escolaridade'),
            'taxa': taxa,
            'prova_data': prova_data,
            'edital_numero': self._extract_edital_numero(title, text),
            'edital_data': self._extract_edital_data(text),
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

    def _is_excluded_certame(self, title: str | None, modalidade: str | None, text: str | None) -> bool:
        haystack = f'{title or ""} {modalidade or ""} {(text or "")[:2500]}'.lower()
        excluded_terms = [
            'vestibular',
            'faculdade de medicina de barbacena',
            'fame/funjob',
            'funjobe',
            'curso de medicina',
            'processo seletivo - 2º semestre',
        ]
        return any(term in haystack for term in excluded_terms)

    def _extract_title(self, lines: list[str], hint: str | None) -> str:
        bad = {'home', 'concursos', 'detalhes do concurso', 'informações gerais', 'informacoes gerais', 'concurso público', 'concurso publico', 'processo seletivo', 'vestibular'}
        # Prefer the descriptive line immediately after the generic modalidade.
        best: str | None = None
        for line in lines[:100]:
            lowered = line.lower().strip()
            if lowered in bad:
                continue
            if re.search(r'\b(?:Concurso|Processo Seletivo|Edital)\b', line, flags=re.IGNORECASE) and len(line) > 12:
                if len(line) > 30 or re.search(r'PREFEITURA|C[ÂA]MARA|SECRETARIA|EDITAL|P\.M\.', line, flags=re.IGNORECASE):
                    best = line
                    break
        if best:
            return best
        if hint:
            for part in re.split(r'\s{2,}|\s\|\s', hint):
                part = clean(part)
                if part and re.search(r'\b(?:Concurso|Processo Seletivo|Edital)\b', part, flags=re.IGNORECASE) and part.lower() not in bad:
                    return part
        # As a last resort, keep the modality but avoid using the site title.
        for line in lines[:100]:
            if re.search(r'\b(?:Concurso|Processo Seletivo)\b', line, flags=re.IGNORECASE):
                return line
        return 'Concurso FUNDEP'

    def _extract_orgao(self, title: str, lines: list[str], hint: str | None) -> str | None:
        for value in [hint, title] + lines[:120]:
            if not value:
                continue
            match = re.search(r'((?:PREFEITURA|C[ÂA]MARA|FACULDADE|FUNDA[CÇ][AÃ]O|UNIVERSIDADE|SECRETARIA|COMPANHIA|CEMIG|EMESCAM)[^\n]{3,140})', value, flags=re.IGNORECASE)
            if match:
                orgao = clean(match.group(1))
                if orgao:
                    orgao = re.sub(r'\s*-\s*EDITAL\s+\d{1,4}/\d{4}.*$', '', orgao, flags=re.IGNORECASE).strip()
                    orgao = re.sub(r'\s*-\s*(?:CONCURSO|PROCESSO SELETIVO).*$','', orgao, flags=re.IGNORECASE).strip()
                    if orgao.lower() != title.lower():
                        return orgao
        return None

    def _extract_city_uf(self, title: str, orgao: str | None, text: str):
        for value in [orgao, title]:
            if value:
                cidade, uf = extract_city_uf(value)
                if cidade or uf:
                    return cidade, uf or 'MG'
        if 'Sete Lagoas' in f'{orgao} {title} {text[:1500]}':
            return 'Sete Lagoas', 'MG'
        if 'Arcos' in f'{orgao} {title}':
            return 'Arcos', 'MG'
        if 'Lavras' in f'{orgao} {title}':
            return 'Lavras', 'MG'
        return None, 'MG'

    def _infer_modalidade(self, title: str, text: str) -> str | None:
        lowered = f'{title} {text[:800]}'.lower()
        if 'processo seletivo' in lowered:
            return 'Processo Seletivo'
        if 'concurso público' in lowered or 'concurso publico' in lowered:
            return 'Concurso Público'
        if 'vestibular' in lowered:
            return 'Vestibular'
        return 'Concurso'

    def _extract_inscricoes(self, text: str):
        match = re.search(r'Per[ií]odo\s+das\s+Inscri[cç][oõ]es\s*\n([^#]{10,700}?)(?:\n\s*(?:Cargos/Vagas|Valor da Inscri[cç][aã]o|Remunera[cç][aã]o|Data das Provas|Fases do Concurso))', text, flags=re.IGNORECASE)
        if match:
            return parse_date_interval(match.group(1))
        return parse_date_interval(text[:3500])

    def _extract_cargo_candidates(self, lines: list[str]) -> list[str]:
        candidates: list[str] = []
        in_vagas = False
        for line in lines:
            norm = line.strip().lower()
            if norm == 'vagas':
                in_vagas = True
                continue
            if not in_vagas:
                continue
            if norm in {'voltar', 'contato', 'concursos', 'realizados'} or '© sistema' in norm:
                break
            # FUNDEP tables usually look like: "301 - ASSISTENTE ADMINISTRATIVO", city, quantity.
            if re.match(r'^\d{1,4}\s*[-–.]\s*\S.{2,160}$', line):
                cargo = clean(re.sub(r'^\d{1,4}\s*[-–.]\s*', '', line))
                if cargo:
                    candidates.append(cargo)
        deduped: list[str] = []
        seen: set[str] = set()
        for item in candidates:
            key = item.lower()
            if key not in seen:
                seen.add(key)
                deduped.append(item)
        return deduped

    def _extract_cargo(self, text: str, cargo_candidates: list[str] | None = None) -> str | None:
        if cargo_candidates:
            return cargo_candidates[0] if len(cargo_candidates) == 1 else 'Vários cargos'
        match = re.search(r'Cargos/Vagas\s*\n([^\n]{3,180})', text, flags=re.IGNORECASE)
        if match:
            candidate = clean(match.group(1))
            if candidate and not candidate.lower().startswith('ver anexo') and not candidate.lower().startswith('verificar'):
                return candidate
        return None

    def _extract_vagas(self, text: str, lines: list[str] | None = None) -> int | None:
        # Try to sum the quantities in the visible Vagas table.
        if lines:
            total = 0
            in_vagas = False
            last_was_cargo = False
            for line in lines:
                norm = line.strip().lower()
                if norm == 'vagas':
                    in_vagas = True
                    continue
                if not in_vagas:
                    continue
                if norm in {'voltar', 'contato', 'concursos', 'realizados'}:
                    break
                if re.match(r'^\d{1,4}\s*[-–.]\s*\S', line):
                    last_was_cargo = True
                    continue
                if last_was_cargo and re.fullmatch(r'\d{1,4}', line.strip()):
                    total += int(line.strip())
                    last_was_cargo = False
                    continue
                if last_was_cargo and re.search(r'^[A-ZÁÉÍÓÚÂÊÔÃÕÇ .\-/]+$', line.strip()):
                    # city/location cell between cargo and quantity
                    continue
                last_was_cargo = False
            if total > 0:
                return total
        patterns = [r'(\d{1,5})\s*\([^)]*\)\s*vagas', r'(\d{1,5})\s+vagas', r'provimento\s+de\s+(\d{1,5})\s+vagas']
        for pattern in patterns:
            match = re.search(pattern, text, flags=re.IGNORECASE)
            if match:
                value = int(match.group(1))
                if 0 < value < 10000:
                    return value
        return None

    def _extract_salarios(self, text: str, pdf_fields: dict[str, Any]):
        values: list[Decimal] = []

        raw_pdf = pdf_fields.get('raw_pdf_fields') or {}
        for raw in raw_pdf.get('salarios_extraidos') or []:
            parsed = parse_money(str(raw))
            if parsed is not None:
                values.append(parsed)

        for key in ('salario_min', 'salario_max'):
            value = pdf_fields.get(key)
            if value is not None:
                try:
                    values.append(Decimal(str(value)))
                except Exception:
                    pass

        section = self._section_after(text, 'Remuneração') or self._section_after(text, 'Remuneracao') or ''
        for match in re.finditer(r'R\$\s*\d{1,3}(?:\.\d{3})*,\d{2}', section):
            parsed = parse_money(match.group(0))
            if parsed is not None:
                values.append(parsed)

        # Values below 1000 are usually table artifacts, carga horária, fees, or
        # installment values, not salary/remuneration for concurso cards.
        valid = [value for value in values if value >= Decimal('1000')]
        return (min(valid), max(valid)) if valid else (None, None)

    def _extract_taxa(self, text: str):
        section = self._section_after(text, 'Valor da Inscrição') or self._section_after(text, 'Valor da Inscricao') or ''
        if 'gratuit' in section.lower():
            from decimal import Decimal
            return Decimal('0')
        values = [parse_money(match.group(0)) for match in re.finditer(r'R\$\s*\d{1,3}(?:\.\d{3})*,\d{2}', section)]
        values = [v for v in values if v is not None]
        return min(values) if values else None

    def _extract_prova_data(self, text: str):
        from app.connectors.common import first_date
        section = self._section_after(text, 'Data das Provas') or self._section_after(text, 'DATAS DAS PROVAS') or ''
        return first_date(section)

    def _section_after(self, text: str, heading: str) -> str | None:
        idx = text.lower().find(heading.lower())
        if idx == -1:
            return None
        return text[idx: idx + 900]

    def _extract_edital_numero(self, title: str, text: str) -> str | None:
        match = re.search(r'Edital\s*(?:n[º°o.]?\s*)?(\d{1,4}/\d{4})', f'{title}\n{text[:2000]}', flags=re.IGNORECASE)
        return match.group(1) if match else None

    def _extract_edital_data(self, text: str):
        from app.connectors.common import first_date
        match = re.search(r'Edital\s*\n?\s*\d{1,4}/\d{4}\s+de\s*\n?\s*(\d{1,2}/\d{1,2}/\d{4})', text, flags=re.IGNORECASE)
        if match:
            return first_date(match.group(1))
        match = re.search(r'EDITAL[^\n]{0,80}?(\d{1,2}/\d{1,2}/\d{4})', text, flags=re.IGNORECASE)
        return first_date(match.group(1)) if match else None

    def _extract_inscricao_link(self, soup: BeautifulSoup, base_url: str) -> str | None:
        for anchor in soup.select('a[href]'):
            text = (clean(anchor.get_text(' ', strip=True)) or '').lower()
            href = anchor.get('href')
            if 'inscri' in text or 'candidato' in (href or '').lower() or 'boleto' in (href or '').lower():
                return normalize_url(base_url, href)
        return None


class FundepOpenConnector(FundepConnector):
    mode = 'open'


class FundepAllConnector(FundepConnector):
    mode = 'all'
