from unittest.mock import MagicMock, patch
import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.connectors.base import CrawlResult, CrawlRunData
from app.database import Base
from app.models import CrawlRun, Source
from app.services import CrawlService


def test_crawl_diagnostics_empty_valid():
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    try:
        source = Source(
            name='Test Empty Banca',
            base_url='https://example.com',
            list_url='https://example.com/concursos',
            source_type='test_empty_open',
            active=True,
        )
        db.add(source)
        db.commit()
        db.refresh(source)

        mock_connector = MagicMock()
        mock_connector.crawl_with_diagnostics.return_value = CrawlResult(
            items=[],
            run_data=CrawlRunData(
                candidates_found=0,
                candidates_rejected=0,
                status='empty_valid',
                http_status=200,
                browser_used=False,
            ),
        )

        with patch('app.services.get_connector', return_value=mock_connector):
            service = CrawlService(db)
            res = service.crawl_source(source.id)

            assert res['status'] == 'empty_valid'
            assert res['processed'] == 0
            assert res['inserted'] == 0

            runs = db.execute(select(CrawlRun)).scalars().all()
            assert len(runs) == 1
            assert runs[0].status == 'empty_valid'
            assert runs[0].http_status == 200
            assert runs[0].duration_ms is not None

    finally:
        db.close()


def test_crawl_diagnostics_failed_handles_gracefully():
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()

    try:
        source = Source(
            name='Test Crashing Banca',
            base_url='https://example.com',
            list_url='https://example.com/concursos',
            source_type='test_crash_open',
            active=True,
        )
        db.add(source)
        db.commit()
        db.refresh(source)

        mock_connector = MagicMock()
        mock_connector.crawl_with_diagnostics.side_effect = ConnectionResetError('Remote host closed connection')

        with patch('app.services.get_connector', return_value=mock_connector):
            service = CrawlService(db)
            res = service.crawl_source(source.id)

            # Never raises, returns failed diagnostic
            assert res['status'] == 'failed'
            assert 'ConnectionResetError' in res['error']

            runs = db.execute(select(CrawlRun)).scalars().all()
            assert len(runs) == 1
            assert runs[0].status == 'failed'
            assert runs[0].error_type == 'ConnectionResetError'

    finally:
        db.close()
