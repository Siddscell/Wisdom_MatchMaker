import os
from pathlib import Path

import pytest

# Settings are read at import time, so the environment is fixed before `app` is imported.
TEST_DB = os.environ.get("TEST_DATABASE_URL")
os.environ["DATABASE_URL"] = TEST_DB or "postgresql+psycopg://unused@localhost:1/unused"
os.environ.update(GEOCODER="none", EMAIL_BACKEND="outbox", ENV="development")

MIGRATIONS = Path(__file__).resolve().parents[2] / "supabase" / "migrations"


def pytest_collection_modifyitems(config, items):
    if TEST_DB:
        return
    skip = pytest.mark.skip(reason="set TEST_DATABASE_URL to run database tests")
    for item in items:
        if "db" in item.keywords:
            item.add_marker(skip)


@pytest.fixture(scope="session")
def _schema():
    from sqlalchemy.engine import make_url

    from app.db import engine

    # The schema is dropped below: refuse anything that is not clearly a test database.
    database = make_url(engine.url).database or ""
    assert "test" in database, "TEST_DATABASE_URL must point at a *test* database"
    with engine.begin() as conn:
        conn.exec_driver_sql("drop schema public cascade; create schema public")
        for sql_file in sorted(MIGRATIONS.glob("*.sql")):
            conn.exec_driver_sql(sql_file.read_text(encoding="utf-8"))


@pytest.fixture
def db(_schema, monkeypatch):
    from factories import FAKE_VECTOR

    from app.db import SessionLocal, engine
    from app.services import matching

    monkeypatch.setattr(matching, "embed", lambda text: FAKE_VECTOR)
    with engine.begin() as conn:
        conn.exec_driver_sql(
            "truncate requirements, offerings, matches, notifications, email_outbox, "
            "geocode_cache cascade"
        )
    with SessionLocal() as session:
        yield session


@pytest.fixture
def client():
    from fastapi.testclient import TestClient

    from app.main import app

    return TestClient(app)
