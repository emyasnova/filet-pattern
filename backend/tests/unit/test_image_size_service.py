"""Unit tests for chart image size detection."""

import cv2
import numpy as np
import pytest

from app.domain.services.image_size_service import (
    ImageSizeDetectionError,
    _round_half_up,
    get_image_grid_size,
)


def _grid_image(
    width_cells: int,
    height_cells: int,
    cell_size: int = 10,
    extension: str = ".png",
) -> bytes:
    image = np.full(
        (height_cells * cell_size + 1, width_cells * cell_size + 1),
        255,
        dtype=np.uint8,
    )
    image[::cell_size, :] = 0
    image[:, ::cell_size] = 0
    encoded, data = cv2.imencode(extension, image)
    assert encoded
    return data.tobytes()


def test_get_image_grid_size_detects_known_grid() -> None:
    """A regular chart should produce its dimensions in cells."""
    result = get_image_grid_size(_grid_image(12, 8), "chart.png")

    assert result.width == 12
    assert result.height == 8


def test_get_image_grid_size_accepts_jpeg() -> None:
    """JPEG charts should use the same detection pipeline as PNG charts."""
    result = get_image_grid_size(_grid_image(10, 7, extension=".jpg"), "chart.jpeg")

    assert result.width == 10
    assert result.height == 7


def test_get_image_grid_size_composites_transparent_png() -> None:
    """Transparent pixels should be treated as white, not as chart content."""
    cell_size = 10
    image = np.zeros((81, 121, 4), dtype=np.uint8)
    image[::cell_size, :, :3] = 0
    image[::cell_size, :, 3] = 255
    image[:, ::cell_size, :3] = 0
    image[:, ::cell_size, 3] = 255
    encoded, data = cv2.imencode(".png", image)
    assert encoded

    result = get_image_grid_size(data.tobytes(), "transparent.png")

    assert result.width == 12
    assert result.height == 8


@pytest.mark.parametrize(
    ("value", "expected"),
    [(1.49, 1), (1.5, 2), (2.5, 3)],
)
def test_round_half_up(value: float, expected: int) -> None:
    """Positive estimates should use the documented rounding rule."""
    assert _round_half_up(value) == expected


@pytest.mark.parametrize(
    ("image_bytes", "filename", "message"),
    [
        (b"", "chart.png", "empty"),
        (b"not an image", "chart.png", "decode"),
        (b"not an image", "chart.gif", "PNG and JPEG"),
    ],
)
def test_get_image_grid_size_rejects_invalid_uploads(
    image_bytes: bytes,
    filename: str,
    message: str,
) -> None:
    """Invalid uploads should become stable domain errors."""
    with pytest.raises(ImageSizeDetectionError, match=message):
        get_image_grid_size(image_bytes, filename)


def test_get_image_grid_size_rejects_image_without_grid() -> None:
    """A blank image should not produce invented dimensions."""
    blank = np.full((100, 100), 255, dtype=np.uint8)
    encoded, data = cv2.imencode(".jpg", blank)
    assert encoded

    with pytest.raises(ImageSizeDetectionError, match="detect a grid"):
        get_image_grid_size(data.tobytes(), "blank.jpg")
