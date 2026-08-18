"""HTTP contract tests for pattern catalog routes."""

from datetime import datetime, timezone
from uuid import UUID

from fastapi.testclient import TestClient

from app.api.schemas.patterns import (
    CategoryResponse,
    PatternPreviewResponse,
    PatternResponse,
    TagResponse,
)
from app.infrastructure.database.session import get_database_session
from app.main import app


def _session_override():
    yield object()


def test_patterns_route_forwards_repeated_filters(monkeypatch) -> None:
    """Repeated tags should reach the service as an AND-filter list."""
    captured = {}

    def fake_get_patterns(repository, search, category, tags):
        captured.update(search=search, category=category, tags=tags)
        return [
            PatternResponse(
                id=UUID("83f9eefc-b6bc-5bdb-b521-c010422068ff"),
                name="Rose",
                category="ornament",
                tags=["flower", "роза"],
                width=1,
                height=1,
                cells=[[1]],
                created_at=datetime(2026, 8, 17, tzinfo=timezone.utc),
            )
        ]

    monkeypatch.setattr("app.api.routes.patterns.get_patterns", fake_get_patterns)
    app.dependency_overrides[get_database_session] = _session_override
    try:
        response = TestClient(app).get(
            "/api/v1/patterns?search=rose&category=ornament&tags=flower&tags=роза"
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert captured == {
        "search": "rose",
        "category": "ornament",
        "tags": ["flower", "роза"],
    }
    assert response.json()[0]["created_at"] == "2026-08-17T00:00:00Z"


def test_catalog_routes_return_public_shapes(monkeypatch) -> None:
    """Category and tag endpoints should return their compact contracts."""
    monkeypatch.setattr(
        "app.api.routes.patterns.get_categories",
        lambda repository: [CategoryResponse(slug="alphabet", name="Алфавит")],
    )
    monkeypatch.setattr(
        "app.api.routes.patterns.get_tags",
        lambda repository: [
            TagResponse(
                id=UUID("6f68ca44-0999-578d-a772-078c702cec67"),
                name="flower",
            )
        ],
    )
    app.dependency_overrides[get_database_session] = _session_override
    try:
        client = TestClient(app)
        categories = client.get("/api/v1/categories")
        tags = client.get("/api/v1/tags")
    finally:
        app.dependency_overrides.clear()

    assert categories.json() == [{"slug": "alphabet", "name": "Алфавит"}]
    assert tags.json() == [
        {"id": "6f68ca44-0999-578d-a772-078c702cec67", "name": "flower"}
    ]


def test_preview_route_forwards_file_and_parameters(monkeypatch) -> None:
    """The preview endpoint should expose the image importer as multipart HTTP."""
    captured = {}

    def fake_generate_pattern_preview(**kwargs):
        captured.update(kwargs)
        return PatternPreviewResponse(
            width=2,
            height=1,
            threshold=140,
            fill_threshold=0.4,
            cells=[[None, 1]],
        )

    monkeypatch.setattr(
        "app.api.routes.patterns.generate_pattern_preview",
        fake_generate_pattern_preview,
    )

    response = TestClient(app).post(
        "/api/v1/patterns/preview",
        files={"file": ("rose.png", b"image-data", "image/png")},
        data={
            "width": "2",
            "height": "1",
            "threshold": "140",
            "fill_threshold": "0.4",
        },
    )

    assert response.status_code == 200
    assert captured == {
        "image_bytes": b"image-data",
        "filename": "rose.png",
        "width": 2,
        "height": 1,
        "threshold": 140,
        "fill_threshold": 0.4,
    }
    assert response.json()["cells"] == [[None, 1]]


def test_create_route_forwards_validated_pattern(monkeypatch) -> None:
    """The create endpoint should return the persisted pattern with status 201."""
    created_at = datetime(2026, 8, 17, tzinfo=timezone.utc)
    pattern_id = UUID("83f9eefc-b6bc-5bdb-b521-c010422068ff")
    captured = {}

    def fake_create_pattern(repository, request):
        captured["request"] = request
        return PatternResponse(
            id=pattern_id,
            name=request.name,
            category=request.category,
            tags=request.tags,
            width=request.width,
            height=request.height,
            cells=request.cells,
            created_at=created_at,
        )

    monkeypatch.setattr("app.api.routes.patterns.create_pattern", fake_create_pattern)
    app.dependency_overrides[get_database_session] = _session_override
    try:
        response = TestClient(app).post(
            "/api/v1/patterns",
            json={
                "name": " Rose ",
                "category": "ornament",
                "tags": ["flower", "Flower", " роза "],
                "width": 2,
                "height": 1,
                "cells": [[None, 1]],
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 201
    assert captured["request"].name == "Rose"
    assert captured["request"].tags == ["flower", "роза"]
    assert response.json() == {
        "id": str(pattern_id),
        "name": "Rose",
        "category": "ornament",
        "tags": ["flower", "роза"],
        "width": 2,
        "height": 1,
        "cells": [[None, 1]],
        "created_at": "2026-08-17T00:00:00Z",
    }
