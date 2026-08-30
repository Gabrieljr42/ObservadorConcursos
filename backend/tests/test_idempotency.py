from datetime import datetime, timezone
from unittest.mock import MagicMock, patch
import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.connectors.base import CrawlResult, CrawlRunData
from app.database import Base
from app.models import Concurso, ConcursoPublication, ConcursoVersion, Source
from app.services import CrawlService


def test_crawl_service_idempotency():
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    try:
        source = Source(
            name='Test Banca',
            base_url='https://example.com',
            list_url='https://example.com/concursos',
            source_type='test_open',
            active=True,
        )
        db.add(source)
        db.commit()
        db.refresh(source)

        mock_items = [
            {
                'external_id': '1001',
                'banca': 'Test Banca',
                'orgao': 'Prefeitura de Teste',
                'titulo': 'Concurso Público 01/2026',
                'modalidade': 'Concurso Público',
                'cargo': 'Analista Administrativo',
                'area': 'administrativa',
                'cidade': 'Teste City',
                'uf': 'MG',
                'status': 'Inscrições abertas',
                'vagas': 10,
                'salario_min': None,
                'salario_max': None,
                'escolaridade': 'Superior',
                'taxa': None,
                'prova_data': None,
                'edital_numero': '01/2026',
                'edital_data': None,
                'inscricao_inicio': datetime.now(timezone.utc),
                'inscricao_fim': datetime.now(timezone.utc),
                'link_pagina': 'https://example.com/concurso/1001',
                'link_edital': 'https://example.com/edital1001.pdf',
                'link_inscricao': None,
                'resumo': 'Concurso teste',
                'raw_data': {
                    'publications': [
                        {
                            'title': 'Convocação',
                            'publication_type': 'convocacao',
                            'publication_date': '2026-08-01T00:00:00+00:00',
                            'link': 'https://example.com/convocacao.pdf',
                            'content_hash': 'publication_hash_1',
                        },
                        # The same publication can appear twice in one
                        # connector payload.  It must be inserted once.
                        {
                            'title': 'Convocação',
                            'publication_type': 'convocacao',
                            'publication_date': '2026-08-01T00:00:00+00:00',
                            'link': 'https://example.com/convocacao.pdf',
                            'content_hash': 'publication_hash_1',
                        },
                    ]
                },
                'content_hash': 'hash_test_123',
                'fetched_at': datetime.now(timezone.utc),
            }
        ]

        mock_connector = MagicMock()
        mock_connector.crawl_with_diagnostics.return_value = CrawlResult(
            items=mock_items,
            run_data=CrawlRunData(
                candidates_found=1,
                status='success',
                browser_used=False,
                http_status=200,
            ),
        )

        with patch('app.services.get_connector', return_value=mock_connector):
            service = CrawlService(db)

            # First run: should insert 1 item and create 1 version
            res1 = service.crawl_source(source.id)
            assert res1['processed'] == 1
            assert res1['inserted'] == 1
            assert res1['updated'] == 0
            assert res1['unchanged'] == 0
            assert res1['versions_created'] == 1

            concursos = db.execute(select(Concurso)).scalars().all()
            assert len(concursos) == 1
            versions = db.execute(select(ConcursoVersion)).scalars().all()
            assert len(versions) == 1
            publications = db.execute(select(ConcursoPublication)).scalars().all()
            assert len(publications) == 1

            # Second run with exact same data: should be 100% idempotent
            res2 = service.crawl_source(source.id)
            assert res2['processed'] == 1
            assert res2['inserted'] == 0
            assert res2['updated'] == 0
            assert res2['unchanged'] == 1
            assert res2['versions_created'] == 0

            concursos_after = db.execute(select(Concurso)).scalars().all()
            assert len(concursos_after) == 1
            versions_after = db.execute(select(ConcursoVersion)).scalars().all()
            assert len(versions_after) == 1
            publications_after = db.execute(select(ConcursoPublication)).scalars().all()
            assert len(publications_after) == 1

    finally:
        db.close()
