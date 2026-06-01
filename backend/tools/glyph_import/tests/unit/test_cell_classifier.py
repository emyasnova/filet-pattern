from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image

from src.domain.models import CellBounds, CellExtractionResult, ExtractedCell
from src.services.cell_classifier import CellClassificationError, classify_cell, classify_cells


def test_classify_cell_marks_empty_cell_as_zero() -> None:
    cell = _make_cell(row_index=0, column_index=0, pixels=[[255, 255], [255, 255]])

    classified = classify_cell(cell, fill_threshold=0.25)

    assert classified.value == 0
    assert classified.fill_ratio == 0.0


def test_classify_cell_marks_filled_cell_as_one() -> None:
    cell = _make_cell(row_index=0, column_index=1, pixels=[[0, 0], [0, 255]])

    classified = classify_cell(cell, fill_threshold=0.5)

    assert classified.value == 1
    assert classified.fill_ratio == 0.75


def test_classify_cells_builds_matrix() -> None:
    extraction_result = CellExtractionResult(
        source_path=Path("synthetic.png"),
        row_count=2,
        column_count=2,
        cells=(
            _make_cell(0, 0, [[255, 255], [255, 255]]),
            _make_cell(0, 1, [[0, 0], [0, 255]]),
            _make_cell(1, 0, [[0, 255], [255, 255]]),
            _make_cell(1, 1, [[0, 0], [0, 0]]),
        ),
    )

    result = classify_cells(extraction_result, fill_threshold=0.5)

    assert result.matrix == ((0, 1), (0, 1))


def test_classify_cells_uses_configurable_threshold() -> None:
    extraction_result = CellExtractionResult(
        source_path=Path("synthetic.png"),
        row_count=1,
        column_count=1,
        cells=(_make_cell(0, 0, [[0, 255], [255, 255]]),),
    )

    low_threshold = classify_cells(extraction_result, fill_threshold=0.2)
    high_threshold = classify_cells(extraction_result, fill_threshold=0.4)

    assert low_threshold.matrix == ((1,),)
    assert high_threshold.matrix == ((0,),)


def test_classify_cells_rejects_invalid_threshold() -> None:
    extraction_result = CellExtractionResult(
        source_path=Path("synthetic.png"),
        row_count=1,
        column_count=1,
        cells=(_make_cell(0, 0, [[255]]),),
    )

    with pytest.raises(CellClassificationError, match="fill_threshold must be in the range 0..1"):
        classify_cells(extraction_result, fill_threshold=1.2)


def test_classify_cell_ignores_thin_border_artifacts() -> None:
    cell = _make_cell(
        row_index=0,
        column_index=0,
        pixels=[
            [0, 0, 0, 0, 0],
            [0, 255, 255, 255, 0],
            [0, 255, 255, 255, 0],
            [0, 255, 255, 255, 0],
            [0, 0, 0, 0, 0],
        ],
    )

    classified = classify_cell(cell, fill_threshold=0.35)

    assert classified.value == 0
    assert classified.fill_ratio == 0.0


def _make_cell(row_index: int, column_index: int, pixels: list[list[int]]) -> ExtractedCell:
    height = len(pixels)
    width = len(pixels[0])
    image = Image.new("L", (width, height), color=255)

    for y, row in enumerate(pixels):
        for x, value in enumerate(row):
            image.putpixel((x, y), value)

    return ExtractedCell(
        row_index=row_index,
        column_index=column_index,
        bounds=CellBounds(left=0, top=0, right=width, bottom=height),
        image=image,
    )
