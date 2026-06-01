"""Split detected grids into individual cells."""

from __future__ import annotations

from src.domain.models import (
    CellBounds,
    CellExtractionResult,
    ExtractedCell,
    GridDetectionResult,
    PreprocessedImage,
)


class CellExtractionError(ValueError):
    """Raised when grid lines cannot be converted into valid cell regions."""


def extract_cells(
    preprocessed_image: PreprocessedImage,
    grid_result: GridDetectionResult,
) -> CellExtractionResult:
    """Cut the binary image into per-cell images using detected grid lines."""
    if len(grid_result.vertical_lines) < 2 or len(grid_result.horizontal_lines) < 2:
        raise CellExtractionError("Grid must contain at least two vertical and horizontal lines.")

    cells: list[ExtractedCell] = []
    for row_index in range(grid_result.row_count):
        top_line = grid_result.horizontal_lines[row_index]
        bottom_line = grid_result.horizontal_lines[row_index + 1]

        for column_index in range(grid_result.column_count):
            left_line = grid_result.vertical_lines[column_index]
            right_line = grid_result.vertical_lines[column_index + 1]

            bounds = _build_cell_bounds(
                left_line=left_line,
                top_line=top_line,
                right_line=right_line,
                bottom_line=bottom_line,
            )
            cropped_image = preprocessed_image.binary_image.crop(
                (bounds.left, bounds.top, bounds.right, bounds.bottom)
            )
            cells.append(
                ExtractedCell(
                    row_index=row_index,
                    column_index=column_index,
                    bounds=bounds,
                    image=cropped_image,
                )
            )

    return CellExtractionResult(
        source_path=preprocessed_image.source_path,
        row_count=grid_result.row_count,
        column_count=grid_result.column_count,
        cells=tuple(cells),
    )


def _build_cell_bounds(
    *,
    left_line: int,
    top_line: int,
    right_line: int,
    bottom_line: int,
) -> CellBounds:
    """Create inner cell bounds between neighboring grid lines."""
    left = left_line + 1
    top = top_line + 1
    right = right_line
    bottom = bottom_line

    if left >= right or top >= bottom:
        raise CellExtractionError(
            "Detected grid lines produce an empty or negative-sized cell region."
        )

    return CellBounds(left=left, top=top, right=right, bottom=bottom)
