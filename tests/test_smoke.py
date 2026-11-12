"""Smoke tests for the FastAPI application.

These tests intentionally avoid requiring a live database: /health receives a
small fake session through FastAPI's dependency override.
"""
import os

# Keep the test module runnable locally as well as in GitHub Actions.
os.environ.setdefault("DATABASE_URL", "sqlite+pysqlite:///:memory:")
os.environ.setdefault("JWT_SECRET_KEY", "local_ci_test_secret_key_at_least_32_chars")
os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("UPLOAD_DIR", "/tmp/cho-do-cu-test-uploads")

import pytest
from fastapi.testclient import TestClient

from app.database import get_db
from app.main import app


class FakeDatabaseSession:
    def __init__(self, should_fail: bool = False):
        self.should_fail = should_fail

    def execute(self, _statement):
        if self.should_fail:
            raise RuntimeError("simulated database outage")
        return None


@pytest.fixture
def client():
    previous_overrides = app.dependency_overrides.copy()
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    app.dependency_overrides.update(previous_overrides)


def test_openapi_document_is_available(client):
    response = client.get("/openapi.json")

    assert response.status_code == 200
    document = response.json()
    assert document["info"]["title"]
    assert "/health" in document["paths"]


def test_health_returns_ok_when_database_is_available(client):
    def override_get_db():
        yield FakeDatabaseSession()

    app.dependency_overrides[get_db] = override_get_db

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "up"}


def test_health_returns_503_when_database_is_unavailable(client):
    def override_get_db():
        yield FakeDatabaseSession(should_fail=True)

    app.dependency_overrides[get_db] = override_get_db

    response = client.get("/health")

    assert response.status_code == 503
    assert response.json() == {"status": "degraded", "database": "down"}
