from __future__ import annotations

import importlib

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, String
from sqlalchemy.dialects.postgresql import JSONB as PgJSONB
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.main import app


@compiles(PgJSONB, "sqlite")
def _compile_jsonb_sqlite(type_, compiler, **kw):  # type: ignore[no-untyped-def]
    return "TEXT"


SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:?check_same_thread=False"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def _import_models():
    model_modules = [
        "document",
        "course",
        "lesson",
        "scene",
        "video",
        "agent_run",
    ]
    for module_name in model_modules:
        try:
            importlib.import_module(f"app.models.{module_name}")
        except ImportError:
            pass


_import_models()
Base.metadata.create_all(bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


@pytest.fixture
def db() -> Session:
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def app_fixture():
    app.dependency_overrides[get_db] = override_get_db
    try:
        yield app
    finally:
        app.dependency_overrides.pop(get_db, None)


@pytest.fixture
def client(app_fixture):
    with TestClient(app_fixture) as c:
        yield c


@pytest.fixture
def sample_course(client):
    body = {
        "title": "Curso Prueba Integración",
        "subject": "Testing",
        "level": "intermediate",
        "language": "es",
        "estimated_duration_minutes": 15,
    }
    response = client.post("/api/v1/courses", json=body)
    assert response.status_code == 201
    payload = response.json()
    assert payload.get("success") is True
    return payload["data"]
