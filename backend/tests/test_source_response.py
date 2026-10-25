from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.database import Base, get_db
from app.main import app


def test_sources_create_and_list_serialize_the_source_model(tmp_path):
    engine = create_engine(f'sqlite:///{tmp_path / "sources.sqlite"}')
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        app.dependency_overrides[get_db] = lambda: db
        try:
            client = TestClient(app)
            response = client.post('/sources', json={
                'name': 'Fonte local de teste', 'base_url': 'https://example.org',
                'list_url': 'https://example.org/concursos', 'source_type': 'html_list',
            })
            assert response.status_code == 201
            source = response.json()
            assert source['name'] == 'Fonte local de teste'
            response = client.get('/sources')
            assert response.status_code == 200
            assert response.json() == [source]
        finally:
            app.dependency_overrides.pop(get_db, None)
    engine.dispose()
