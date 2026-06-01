"""Integration tests for health endpoint."""

from fastapi.testclient import TestClient

from app.main import app


def test_healthcheck_returns_ok_status() -> None:
    """Health endpoint should return the expected status payload."""
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
