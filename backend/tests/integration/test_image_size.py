"""Integration tests for the image size endpoint."""

from fastapi.testclient import TestClient

from app.domain.models.image_size import ImageGridSize
from app.domain.services.image_size_service import ImageSizeDetectionError
from app.main import app


def test_detect_image_size_returns_dimensions(monkeypatch) -> None:
    """The endpoint should return a service result as JSON."""
    monkeypatch.setattr(
        "app.api.routes.image_size.get_image_grid_size",
        lambda image_bytes, filename: ImageGridSize(width=120, height=80),
    )
    client = TestClient(app)

    response = client.post(
        "/api/v1/images/size",
        files={"file": ("chart.png", b"image bytes", "image/png")},
    )

    assert response.status_code == 200
    assert response.json() == {"width": 120, "height": 80}


def test_detect_image_size_requires_file() -> None:
    """A multipart request without a file should fail validation."""
    response = TestClient(app).post("/api/v1/images/size")

    assert response.status_code == 422


def test_detect_image_size_returns_detection_error(monkeypatch) -> None:
    """Domain detection failures should be exposed as HTTP 422."""
    def fail(image_bytes: bytes, filename: str) -> ImageGridSize:
        raise ImageSizeDetectionError("Could not detect a grid")

    monkeypatch.setattr("app.api.routes.image_size.get_image_grid_size", fail)
    response = TestClient(app).post(
        "/api/v1/images/size",
        files={"file": ("chart.png", b"image bytes", "image/png")},
    )

    assert response.status_code == 422
    assert response.json() == {"detail": "Could not detect a grid"}
