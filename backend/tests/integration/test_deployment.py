"""Production HTTP behavior tests."""

from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy.exc import SQLAlchemyError

from app.api.dependencies import require_pattern_creation
from app.core.config import Settings
from app.infrastructure.database.session import get_database_session
from app.main import create_app


class SessionStub:
    def __init__(self, failure: bool = False) -> None:
        self.failure = failure

    def execute(self, statement) -> None:
        if self.failure:
            raise SQLAlchemyError("private connection detail")


def test_readiness_reports_both_database_states(tmp_path: Path) -> None:
    app = create_app(Settings(frontend_dist_dir=tmp_path))
    app.dependency_overrides[get_database_session] = lambda: SessionStub()
    assert TestClient(app).get("/ready").json() == {"status": "ok"}
    app.dependency_overrides[get_database_session] = lambda: SessionStub(True)
    response = TestClient(app).get("/ready")
    assert response.status_code == 503
    assert response.json() == {"status": "unavailable"}


def test_disabled_creation_rejects_before_image_service(monkeypatch, tmp_path: Path) -> None:
    app = create_app(Settings(frontend_dist_dir=tmp_path, pattern_creation_enabled=False))
    called = False

    def forbidden(*args, **kwargs):
        nonlocal called
        called = True

    monkeypatch.setattr("app.api.routes.image_size.get_image_grid_size", forbidden)
    response = TestClient(app).post(
        "/api/v1/images/size", files={"file": ("x.png", b"data", "image/png")}
    )
    assert response.status_code == 403
    assert response.json() == {"detail": "Pattern creation is currently unavailable"}
    assert called is False


def test_public_config_reflects_creation_flag(tmp_path: Path) -> None:
    app = create_app(Settings(frontend_dist_dir=tmp_path, pattern_creation_enabled=True))
    assert TestClient(app).get("/api/v1/config").json() == {
        "patternCreationEnabled": True
    }


def test_frontend_assets_fallback_and_reserved_routes(tmp_path: Path) -> None:
    (tmp_path / "assets").mkdir()
    (tmp_path / "index.html").write_text("<h1>app</h1>", encoding="utf-8")
    (tmp_path / "assets" / "app.js").write_text("ok", encoding="utf-8")
    client = TestClient(create_app(Settings(frontend_dist_dir=tmp_path)))
    assert client.get("/").text == "<h1>app</h1>"
    assert client.get("/editor/42").text == "<h1>app</h1>"
    assert client.get("/assets/app.js").text == "ok"
    assert client.get("/api/v1/unknown").status_code == 404


def test_missing_frontend_and_security_policy(tmp_path: Path) -> None:
    client = TestClient(create_app(Settings(frontend_dist_dir=tmp_path)))
    response = client.get("/health")
    assert response.status_code == 200
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert "frame-ancestors 'none'" in response.headers["content-security-policy"]
    assert client.get("/").status_code == 404


def test_trusted_host_and_canonical_redirect(tmp_path: Path) -> None:
    app = create_app(Settings(frontend_dist_dir=tmp_path, canonical_host="example.com"))
    client = TestClient(app)
    assert client.get("/health", headers={"host": "evil.example"}).status_code == 400
    response = client.get("/health", headers={"host": "www.example.com"}, follow_redirects=False)
    assert response.status_code == 308
    assert response.headers["location"].startswith("http://example.com/")
