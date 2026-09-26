"""Local review server: isolated SQLite, normal authentication, no production DB.

Run from backend: .venv/Scripts/python.exe scripts/tenderproof_review_server.py
Only SOLARI_API_KEY is loaded from backend/.env. Bind is loopback only.
Review login: tenderproof@example.test / TenderProof-local-review
"""
from pathlib import Path
import os
import secrets
import sys
import tempfile

BACKEND = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BACKEND))


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8013)
    parser.add_argument("--without-baseline", action="store_true", help="Seed only the source to visually test a new canonical contest in the disposable DB")
    args = parser.parse_args()
    from dotenv import dotenv_values

    key = dotenv_values(BACKEND / ".env").get("SOLARI_API_KEY")
    if key:
        os.environ["SOLARI_API_KEY"] = key
    with tempfile.TemporaryDirectory(prefix="tenderproof-review-") as directory:
        os.environ["DATABASE_URL"] = "sqlite:///" + str(Path(directory) / "review.sqlite")
        os.environ["SECRET_KEY"] = secrets.token_hex(32)
        os.environ["TENDERPROOF_ARTIFACT_DIR"] = str(BACKEND / ".tenderproof" / "review" / "artifacts")
        os.environ["TENDERPROOF_TOTAL_TIMEOUT_S"] = "240"
        os.environ["TENDERPROOF_REPLAY_DEADLINE_S"] = "10"
        os.environ["TENDERPROOF_BROWSER_LIVE_ENABLED"] = "false"
        os.environ["TENDERPROOF_PUBLICATION_ENABLED"] = "true"
        os.environ["TENDERPROOF_PUBLICATION_ALLOW_SYNTHETIC"] = "true"
        os.environ["TENDERPROOF_PUBLISHER_USER_IDS"] = "1"

        from app.main import app
        from app.auth import hash_password
        from app.database import Base, engine, SessionLocal
        from app.models import User
        from app.models import Source, Concurso
        from app.tenderproof.mock_demo import MOCK_BASELINE
        from app.connectors.common import build_hash
        from datetime import datetime
        from fastapi.middleware.cors import CORSMiddleware
        import uvicorn
        from contextlib import asynccontextmanager

        @asynccontextmanager
        async def review_lifespan(_app):
            # Fresh metadata already creates the isolated schema; production
            # PostgreSQL migrations must not run against this SQLite fixture.
            yield

        app.router.lifespan_context = review_lifespan

        Base.metadata.create_all(engine)
        with SessionLocal() as db:
            db.add(User(name="Revisor local", email="tenderproof@example.test",
                        password_hash=hash_password("TenderProof-local-review")))
            source = Source(name="IBGP — baseline sintética", base_url="https://novo.ibgpconcursos.com.br", source_type="ibgp_open")
            db.add(source)
            db.flush()
            values = dict(MOCK_BASELINE)
            for field in ("inscricao_inicio", "inscricao_fim"):
                values[field] = datetime.fromisoformat(values[field])
            if not args.without_baseline:
                db.add(Concurso(source_id=source.id, external_id="42", banca="IBGP", **values,
                    link_pagina="https://novo.ibgpconcursos.com.br/concurso.jsp?cod=42",
                    content_hash=build_hash({"synthetic": True}), raw_data={"synthetic": True}))
            db.commit()
        app.add_middleware(CORSMiddleware,
                           allow_origins=["http://localhost:8081", "http://localhost:3000"],
                           allow_methods=["GET", "POST", "OPTIONS"],
                           allow_headers=["Authorization", "Content-Type"])
        try:
            uvicorn.run(app, host="127.0.0.1", port=args.port, access_log=False)
        finally:
            engine.dispose()


if __name__ == "__main__":
    main()
