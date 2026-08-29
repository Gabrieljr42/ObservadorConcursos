from __future__ import annotations

import re
import unicodedata
from datetime import UTC, datetime, time
from typing import Any

import httpx

from app.connectors.base import BaseConnector, CandidateItem
from app.connectors.common import (
    build_hash,
    build_summary,
    classify_area_from_many,
    clean,
    extract_city_uf,
    extract_pdf_fields_if_possible,
    status_from_dates,
)
from app.connectors.institutional import InstitutionalSelectionConnector
from app.publications import build_publication_hash, normalize_publication_type


class UniselvaAPIConnector(BaseConnector):
    """Current Uniselva portal connector backed by its official REST API."""

    banca = 'Fundação Uniselva'
    category = 'institutional_selection'
    mode = 'open'
    max_candidates = 100
    api_url = 'https://api.fundacaouniselva.org.br/SelecaoSimplificada'

    def __init__(
        self,
        base_url: str = 'https://inscricao.fundacaouniselva.org.br',
        list_url: str | None = None,
    ):
        canonical = 'https://inscricao.fundacaouniselva.org.br'
        super().__init__(canonical, list_url or canonical + '/selecoes')

    @staticmethod
    def _normalized(value: str | None) -> str:
        value = unicodedata.normalize('NFKD', (value or '').lower())
        return ''.join(character for character in value if not unicodedata.combining(character))

    @classmethod
    def _is_eligible_api_item(cls, data: dict[str, Any]) -> bool:
        title = clean(data.get('titulo')) or ''
        description = clean(data.get('descricao')) or ''
        function = clean(data.get('funcaoConsultoria')) or ''
        text = cls._normalized(f'{title} {description} {function}')

        # Consulting contracts and PJ/CNPJ calls are services, not personnel.
        if any(term in text for term in (
            'consultor individual', 'consultoria', 'funcao consultoria',
            'por pessoa juridica', 'vaga de consultoria',
        )):
            return False

        # The portal's two current personnel forms are explicit and auditable.
        if 'estagi' in text and any(term in text for term in ('contratacao', 'selecao', 'vaga')):
            return True
        if 'banco de curriculos' in text and any(term in text for term in ('vaga', 'profissional', 'emprego')):
            return True

        return InstitutionalSelectionConnector.has_personnel_evidence(title, description)

    @staticmethod
    def _api_datetime(value: str | None, *, end_of_day: bool = False) -> datetime | None:
        if not value:
            return None
        try:
            parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
        except ValueError:
            return None
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=UTC)
        else:
            parsed = parsed.astimezone(UTC)
        if end_of_day and parsed.time() == time.min:
            parsed = parsed.replace(hour=23, minute=59, second=59)
        return parsed

    def _fetch_candidates(self) -> list[CandidateItem]:
        params = {
            'pageNumber': 1,
            'pageSize': self.max_candidates,
            'isDescending': 'true',
            'filter.isInscricaoAberta': 'true',
        }
        with self._http_client() as client:
            response = client.get(self.api_url, params=params)
            self.run_data.http_status = response.status_code
            response.raise_for_status()
            payload = response.json()

        items = payload.get('items') if isinstance(payload, dict) else None
        if not isinstance(items, list):
            raise ValueError('Uniselva API did not return an items list')
        self.run_data.diagnostics_payload.update({
            'api': self.api_url,
            'api_total': payload.get('total', len(items)),
            'api_page': payload.get('page'),
            'api_total_pages': payload.get('totalPage'),
        })
        return [
            CandidateItem(
                title_hint=clean(item.get('titulo')),
                detail_url=f'{self.base_url}/selecoes/{item["id"]}',
                external_id=str(item['id']),
                extra={'api_list_item': item},
            )
            for item in items
            if isinstance(item, dict) and item.get('id') is not None
        ]

    @staticmethod
    def _choose_edital(documents: list[dict[str, Any]]) -> str | None:
        ranked: list[tuple[int, str]] = []
        for document in documents:
            url = clean(document.get('arquivo'))
            title = (clean(document.get('descricao')) or '').lower()
            if not url:
                continue
            score = 0
            if 'edital' in title:
                score += 10
            if 'portaria' in title or 'manifestação de interesse' in title or 'manifestacao de interesse' in title:
                score -= 5
            ranked.append((score, url))
        return max(ranked, default=(0, None), key=lambda value: value[0])[1]

    @staticmethod
    def _publication_rows(documents: list[dict[str, Any]]) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        seen: set[str] = set()
        for document in documents:
            title = clean(document.get('descricao')) or 'Documento oficial'
            link = clean(document.get('arquivo'))
            if not link or link in seen:
                continue
            seen.add(link)
            publication_type = normalize_publication_type(title)
            rows.append({
                'title': title,
                'publication_type': publication_type,
                'publication_date': None,
                'link': link,
                'content_hash': build_publication_hash(title, None, link, publication_type),
                'source': 'fundacao_uniselva_api',
            })
        return rows

    @staticmethod
    def _cargo(data: dict[str, Any]) -> str | None:
        function = clean(data.get('funcaoConsultoria'))
        if function:
            return function
        text = f'{data.get("titulo") or ""} {data.get("descricao") or ""}'
        if re.search(r'\bestagi[áa]ri', text, flags=re.IGNORECASE):
            return 'Estagiário(a) de graduação'
        match = re.search(r'\bvaga\s+(?:de|para)\s+([A-Za-zÀ-ÿ ]{3,80})', text, flags=re.IGNORECASE)
        return clean(match.group(1)) if match else None

    @staticmethod
    def _edital_number(data: dict[str, Any]) -> str | None:
        for value in (data.get('processoSmi'), data.get('titulo'), data.get('descricao')):
            match = re.search(
                r'\b(?:EDITAL|SMI)\s*(?:N[º°O.]?\s*)?(\d{1,4}[./]\d{4})',
                value or '',
                flags=re.IGNORECASE,
            )
            if match:
                return match.group(1).replace('.', '/')
        return clean(data.get('processoSmi'))

    def _parse_detail(
        self,
        candidate: CandidateItem,
        html: str,
        *,
        client: httpx.Client,
    ) -> dict[str, Any] | None:
        response = client.get(f'{self.api_url}/{candidate.external_id}')
        response.raise_for_status()
        data = response.json()
        if not isinstance(data, dict):
            return None
        if not self._is_eligible_api_item(data):
            return None

        title = clean(data.get('titulo')) or candidate.title_hint
        description = clean(data.get('descricao')) or ''
        documents = [item for item in (data.get('documentos') or []) if isinstance(item, dict)]
        edital_url = self._choose_edital(documents)
        inicio = self._api_datetime(data.get('inicioInscricao'))
        fim = self._api_datetime(data.get('fimInscricao'), end_of_day=True)
        status = status_from_dates(inicio, fim)
        cargo = self._cargo(data)
        area_label = clean(data.get('area'))
        area = classify_area_from_many([cargo] if cargo else [], area_label, title, description)
        cidade, uf = extract_city_uf(description)
        cidade = cidade or 'Cuiabá'
        uf = uf or 'MT'
        publications = self._publication_rows(documents)

        pdf_payload, pdf_fields, excerpt, pdf_at = extract_pdf_fields_if_possible(
            edital_url,
            title=title,
            orgao='Fundação Uniselva',
            client=client,
        )
        vagas = (pdf_fields or {}).get('vagas')
        if vagas is None:
            match = re.search(r'\bcontrata[cç][aã]o\s+de\s+0?(\d{1,3})\b', description, flags=re.IGNORECASE)
            vagas = int(match.group(1)) if match else None
        salario_min = (pdf_fields or {}).get('salario_min')
        salario_max = (pdf_fields or {}).get('salario_max')
        escolaridade = (pdf_fields or {}).get('escolaridade') or area_label
        taxa = (pdf_fields or {}).get('taxa')
        prova_data = (pdf_fields or {}).get('prova_data')
        raw_payload = {
            'api': data,
            'publications': publications,
            'pdf': pdf_payload,
            'pdf_fields': (pdf_fields or {}).get('raw_pdf_fields', {}),
            'source_list_url': self.list_url,
        }
        modalidade = 'Seleção de Estágio' if 'estagi' in self._normalized(title) else 'Processo Seletivo'
        resumo = build_summary(
            title,
            modalidade,
            status,
            inicio,
            fim,
            cargo=cargo,
            area=area,
            vagas=vagas,
            salario_min=salario_min,
            salario_max=salario_max,
        )
        return {
            'external_id': str(data.get('id') or candidate.external_id),
            'banca': self.banca,
            'orgao': 'Fundação Uniselva',
            'titulo': title,
            'modalidade': modalidade,
            'cargo': cargo or (pdf_fields or {}).get('cargo'),
            'area': area or (pdf_fields or {}).get('area'),
            'cidade': cidade or (pdf_fields or {}).get('cidade'),
            'uf': uf or (pdf_fields or {}).get('uf'),
            'status': status,
            'vagas': vagas,
            'salario_min': salario_min,
            'salario_max': salario_max,
            'escolaridade': escolaridade,
            'taxa': taxa,
            'prova_data': prova_data,
            'edital_numero': self._edital_number(data),
            'edital_data': None,
            'inscricao_inicio': inicio,
            'inscricao_fim': fim,
            'link_pagina': candidate.detail_url,
            'link_edital': edital_url,
            'link_inscricao': f'{self.base_url}/selecoes/inscricao/{candidate.external_id}',
            'resumo': resumo,
            'raw_data': raw_payload,
            'edital_pdf_text_hash': pdf_payload.get('text_hash'),
            'edital_pdf_pages': pdf_payload.get('pages'),
            'edital_pdf_excerpt': excerpt,
            'pdf_extracted_at': pdf_at,
            'content_hash': build_hash(raw_payload),
            'fetched_at': datetime.now(UTC),
        }
