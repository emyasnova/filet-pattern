"""Exercise the real creation gate using environment-backed settings."""

from pathlib import Path
from unittest.mock import AsyncMock, Mock

import pytest
from fastapi.testclient import TestClient

from app.api.routes import image_size, patterns
from app.core.config import Settings
from app.core.uploads import read_limited_upload
from app.domain.models.image_size import ImageGridSize
from app.infrastructure.database.session import get_database_session
from app.main import create_app


@pytest.fixture(params=[False, True], ids=["disabled", "enabled"])
def creation_client(
    request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
):
    """Isolate each app without overriding its authorization dependency."""
    enabled = request.param
    monkeypatch.setenv("PATTERN_CREATION_ENABLED", str(enabled).lower())
    settings = Settings(
        _env_file=None,
        frontend_dist_dir=tmp_path,
        canonical_host=None,
        public_origin=None,
        public_read_rate_limit=120,
    )
    assert settings.pattern_creation_enabled is enabled
    app = create_app(settings)
    session = Mock()
    app.dependency_overrides[get_database_session] = lambda: session
    with TestClient(app) as client:
        yield client, enabled, session


@pytest.mark.parametrize("endpoint", ["images/size", "patterns/preview", "patterns"])
def test_creation_posts_obey_flag(creation_client, monkeypatch, endpoint: str) -> None:
    """Disabled POSTs must not read uploads, process images, or save patterns."""
    client, enabled, session = creation_client
    payload = {
        "name": "Rose", "category": "ornament", "tags": [],
        "width": 2, "height": 1, "cells": [[None, 1]],
    }
    saved = {
        **payload,
        "id": "83f9eefc-b6bc-5bdb-b521-c010422068ff",
        "created_at": "2026-08-17T00:00:00Z",
    }
    preview = {
        "width": 2, "height": 1, "cells": [[None, 1]],
        "threshold": 128, "fill_threshold": 0.35,
    }
    services = {
        "images/size": Mock(return_value=ImageGridSize(width=2, height=1)),
        "patterns/preview": Mock(return_value=preview),
        "patterns": Mock(return_value=saved),
    }
    monkeypatch.setattr(image_size, "get_image_grid_size", services["images/size"])
    monkeypatch.setattr(patterns, "generate_pattern_preview", services["patterns/preview"])
    monkeypatch.setattr(patterns, "create_pattern", services["patterns"])
    upload_reader = AsyncMock(wraps=read_limited_upload)
    monkeypatch.setattr(image_size, "read_limited_upload", upload_reader)
    monkeypatch.setattr(patterns, "read_limited_upload", upload_reader)

    if endpoint == "patterns":
        response = client.post("/api/v1/patterns", json=payload)
    else:
        response = client.post(
            f"/api/v1/{endpoint}",
            files={"file": ("rose.png", b"image-data", "image/png")},
            data={"width": "2", "height": "1"},
        )

    if not enabled:
        assert response.status_code == 403
        assert response.json() == {"detail": "Pattern creation is currently unavailable"}
        upload_reader.assert_not_called()
        for service in services.values():
            service.assert_not_called()
        assert session.mock_calls == []
        return

    assert response.status_code == (201 if endpoint == "patterns" else 200)
    services[endpoint].assert_called_once()
    for name, service in services.items():
        if name != endpoint:
            service.assert_not_called()
    if endpoint == "patterns":
        upload_reader.assert_not_called()
        assert services[endpoint].call_args.args[1].model_dump() == payload
        assert response.json() == saved
    else:
        upload_reader.assert_awaited_once()
        if endpoint == "images/size":
            services[endpoint].assert_called_once_with(b"image-data", "rose.png")
            assert response.json() == {"width": 2, "height": 1}
        else:
            services[endpoint].assert_called_once_with(
                image_bytes=b"image-data", filename="rose.png",
                width=2, height=1, threshold=128, fill_threshold=0.35,
            )
            assert response.json() == preview


def test_public_catalog_and_config_remain_available(creation_client, monkeypatch) -> None:
    """Both flag values leave the catalog and public configuration accessible."""
    client, enabled, _ = creation_client
    for endpoint, service_name in (
        ("patterns", "get_patterns"),
        ("categories", "get_categories"),
        ("tags", "get_tags"),
    ):
        service = Mock(return_value=[])
        monkeypatch.setattr(patterns, service_name, service)
        response = client.get(f"/api/v1/{endpoint}")
        assert response.status_code == 200
        assert response.json() == []
        service.assert_called_once()
    response = client.get("/api/v1/config")
    assert response.status_code == 200
    assert response.json() == {"patternCreationEnabled": enabled}


def test_creation_is_disabled_without_explicit_setting(monkeypatch) -> None:
    """A deployment must opt in to creation explicitly."""
    monkeypatch.delenv("PATTERN_CREATION_ENABLED", raising=False)
    assert Settings(_env_file=None).pattern_creation_enabled is False
