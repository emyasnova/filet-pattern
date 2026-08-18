"""Tests for the in-memory image import used by the preview API."""

from io import BytesIO

from PIL import Image, ImageDraw

from app.domain.services.pattern_service import generate_pattern_preview


def _plus_pattern_png() -> bytes:
    cell_size = 12
    image = Image.new("L", (5 * cell_size + 1, 5 * cell_size + 1), 255)
    draw = ImageDraw.Draw(image)
    for offset in range(0, image.width, cell_size):
        draw.line((offset, 0, offset, image.height), fill=0)
    for offset in range(0, image.height, cell_size):
        draw.line((0, offset, image.width, offset), fill=0)
    for row, column in {(1, 2), (2, 1), (2, 2), (2, 3), (3, 2)}:
        draw.rectangle(
            (
                column * cell_size + 2,
                row * cell_size + 2,
                (column + 1) * cell_size - 2,
                (row + 1) * cell_size - 2,
            ),
            fill=0,
        )
    output = BytesIO()
    image.save(output, format="PNG")
    return output.getvalue()


def test_generate_pattern_preview_trims_and_normalizes_background() -> None:
    """The shared glyph pipeline should return a transparent trimmed matrix."""
    result = generate_pattern_preview(
        image_bytes=_plus_pattern_png(),
        filename="plus.png",
        width=5,
        height=5,
        threshold=128,
        fill_threshold=0.35,
    )

    assert (result.width, result.height) == (3, 3)
    assert result.cells == [[None, 1, None], [1, 1, 1], [None, 1, None]]
