from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image, ImageDraw

from src.domain.models import GridDetectionResult, ImageFormat, LoadedImage, PreprocessedImage
from src.services.cell_extractor import CellExtractionError, extract_cells


def test_extract_cells_splits_grid_into_expected_number_of_cells() -> None:
    preprocessed_image = _build_preprocessed_grid(
        width=20,
        height=16,
        vertical_lines=[2, 7, 12, 17],
        horizontal_lines=[3, 8, 13],
    )
    grid_result = GridDetectionResult(
        source_path=preprocessed_image.source_path,
        left=0,
        top=0,
        right=19,
        bottom=15,
        vertical_lines=(2, 7, 12, 17),
        horizontal_lines=(3, 8, 13),
        column_count=3,
        row_count=2,
    )

    result = extract_cells(preprocessed_image, grid_result)

    assert result.column_count == 3
    assert result.row_count == 2
    assert len(result.cells) == 6
    assert result.cells[0].row_index == 0
    assert result.cells[0].column_index == 0
    assert result.cells[0].bounds.left == 3
    assert result.cells[0].bounds.top == 4
    assert result.cells[0].bounds.right == 7
    assert result.cells[0].bounds.bottom == 8
    assert result.cells[0].image.size == (4, 4)


def test_extract_cells_preserves_cell_content() -> None:
    image = Image.new("L", (12, 12), color=255)
    draw = ImageDraw.Draw(image)

    for x in [0, 6, 11]:
        draw.line((x, 0, x, 11), fill=0, width=1)
    for y in [0, 6, 11]:
        draw.line((0, y, 11, y), fill=0, width=1)

    for x in range(7, 11):
        for y in range(1, 6):
            image.putpixel((x, y), 0)

    preprocessed_image = _wrap_binary_image(image)
    grid_result = GridDetectionResult(
        source_path=preprocessed_image.source_path,
        left=0,
        top=0,
        right=11,
        bottom=11,
        vertical_lines=(0, 6, 11),
        horizontal_lines=(0, 6, 11),
        column_count=2,
        row_count=2,
    )

    result = extract_cells(preprocessed_image, grid_result)

    top_left = result.cells[0]
    top_right = result.cells[1]

    assert top_left.image.getextrema() == (255, 255)
    assert top_right.image.getextrema() == (0, 0)


def test_extract_cells_rejects_invalid_cell_geometry() -> None:
    preprocessed_image = _wrap_binary_image(Image.new("L", (10, 10), color=255))
    grid_result = GridDetectionResult(
        source_path=preprocessed_image.source_path,
        left=0,
        top=0,
        right=9,
        bottom=9,
        vertical_lines=(4, 4),
        horizontal_lines=(0, 9),
        column_count=1,
        row_count=1,
    )

    with pytest.raises(CellExtractionError, match="empty or negative-sized cell region"):
        extract_cells(preprocessed_image, grid_result)


def _build_preprocessed_grid(
    *,
    width: int,
    height: int,
    vertical_lines: list[int],
    horizontal_lines: list[int],
) -> PreprocessedImage:
    image = Image.new("L", (width, height), color=255)
    draw = ImageDraw.Draw(image)

    for x in vertical_lines:
        draw.line((x, 0, x, height - 1), fill=0, width=1)

    for y in horizontal_lines:
        draw.line((0, y, width - 1, y), fill=0, width=1)

    return _wrap_binary_image(image)


def _wrap_binary_image(image: Image.Image) -> PreprocessedImage:
    path = Path("synthetic-cells.png").resolve()
    loaded_image = LoadedImage(path=path, image_format=ImageFormat.PNG, content=b"")
    return PreprocessedImage(
        source_path=loaded_image.path,
        grayscale_image=image.copy(),
        denoised_image=image.copy(),
        binary_image=image.copy(),
    )
