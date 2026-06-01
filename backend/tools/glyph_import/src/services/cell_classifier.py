"""Classification of extracted cells into empty/filled values."""

from __future__ import annotations

from src.domain.models import CellClassificationResult, CellExtractionResult, ClassifiedCell, ExtractedCell


DEFAULT_FILL_THRESHOLD = 0.35
BLACK_PIXEL_VALUE = 0
DEFAULT_EDGE_ARTIFACT_MARGIN = 0.05


class CellClassificationError(ValueError):
    """Raised when cells cannot be classified into a matrix."""


def classify_cells(
    extraction_result: CellExtractionResult,
    *,
    fill_threshold: float = DEFAULT_FILL_THRESHOLD,
) -> CellClassificationResult:
    """Classify extracted cells and build a raw 0/1 matrix."""
    _validate_fill_threshold(fill_threshold)

    classified_cells = tuple(
        _adjust_edge_artifact_classification(
            cell=cell,
            classified_cell=classify_cell(cell, fill_threshold=fill_threshold),
            row_count=extraction_result.row_count,
            fill_threshold=fill_threshold,
        )
        for cell in extraction_result.cells
    )
    matrix = _build_matrix(
        classified_cells=classified_cells,
        row_count=extraction_result.row_count,
        column_count=extraction_result.column_count,
    )

    return CellClassificationResult(
        source_path=extraction_result.source_path,
        row_count=extraction_result.row_count,
        column_count=extraction_result.column_count,
        fill_threshold=fill_threshold,
        cells=classified_cells,
        matrix=matrix,
    )


def classify_cell(
    cell: ExtractedCell,
    *,
    fill_threshold: float = DEFAULT_FILL_THRESHOLD,
) -> ClassifiedCell:
    """Classify a single cell using the ratio of black pixels in its inner area."""
    _validate_fill_threshold(fill_threshold)

    width, height = cell.image.size
    if width <= 0 or height <= 0:
        raise CellClassificationError("Cell image must have a positive size.")

    fill_ratio = _measure_fill_ratio(cell)
    value = 1 if fill_ratio >= fill_threshold else 0

    return ClassifiedCell(
        row_index=cell.row_index,
        column_index=cell.column_index,
        fill_ratio=fill_ratio,
        value=value,
    )


def _build_matrix(
    *,
    classified_cells: tuple[ClassifiedCell, ...],
    row_count: int,
    column_count: int,
) -> tuple[tuple[int, ...], ...]:
    """Build a rectangular 0/1 matrix from classified cells."""
    expected_cell_count = row_count * column_count
    if len(classified_cells) != expected_cell_count:
        raise CellClassificationError(
            "The number of classified cells does not match the declared matrix size."
        )

    rows: list[list[int]] = [[0 for _ in range(column_count)] for _ in range(row_count)]
    seen_coordinates: set[tuple[int, int]] = set()

    for cell in classified_cells:
        coordinate = (cell.row_index, cell.column_index)
        if coordinate in seen_coordinates:
            raise CellClassificationError("Duplicate classified cell coordinates detected.")
        seen_coordinates.add(coordinate)

        if not (0 <= cell.row_index < row_count and 0 <= cell.column_index < column_count):
            raise CellClassificationError("Classified cell coordinates are out of matrix bounds.")
        rows[cell.row_index][cell.column_index] = cell.value

    return tuple(tuple(row) for row in rows)


def _validate_fill_threshold(fill_threshold: float) -> None:
    """Ensure the fill threshold is a ratio in the inclusive 0..1 range."""
    if not 0 <= fill_threshold <= 1:
        raise CellClassificationError("fill_threshold must be in the range 0..1.")


def _measure_fill_ratio(cell: ExtractedCell) -> float:
    """Measure fill ratio while ignoring thin border artifacts inside a cell."""
    left, top, right, bottom = _get_inner_bounds(cell)
    total_pixels = (right - left) * (bottom - top)
    black_pixels = _count_black_pixels(cell, left=left, top=top, right=right, bottom=bottom)
    return black_pixels / total_pixels


def _adjust_edge_artifact_classification(
    *,
    cell: ExtractedCell,
    classified_cell: ClassifiedCell,
    row_count: int,
    fill_threshold: float,
) -> ClassifiedCell:
    """Suppress marginal fills on the last row when ink appears only in the top half."""
    if classified_cell.value == 0 or cell.row_index != row_count - 1:
        return classified_cell

    if classified_cell.fill_ratio >= fill_threshold + DEFAULT_EDGE_ARTIFACT_MARGIN:
        return classified_cell

    upper_half_ratio, lower_half_ratio = _measure_vertical_half_fill_ratios(cell)
    if upper_half_ratio >= fill_threshold and lower_half_ratio == 0:
        return ClassifiedCell(
            row_index=classified_cell.row_index,
            column_index=classified_cell.column_index,
            fill_ratio=classified_cell.fill_ratio,
            value=0,
        )

    return classified_cell


def _measure_vertical_half_fill_ratios(cell: ExtractedCell) -> tuple[float, float]:
    """Measure fill ratios for the upper and lower halves of the inner cell area."""
    left, top, right, bottom = _get_inner_bounds(cell)
    midpoint = top + ((bottom - top) // 2)
    upper_ratio = _measure_region_fill_ratio(
        cell,
        left=left,
        top=top,
        right=right,
        bottom=midpoint,
    )
    lower_ratio = _measure_region_fill_ratio(
        cell,
        left=left,
        top=midpoint,
        right=right,
        bottom=bottom,
    )
    return upper_ratio, lower_ratio


def _measure_region_fill_ratio(
    cell: ExtractedCell,
    *,
    left: int,
    top: int,
    right: int,
    bottom: int,
) -> float:
    """Measure the black-pixel ratio inside a rectangular cell region."""
    total_pixels = (right - left) * (bottom - top)
    if total_pixels <= 0:
        return 0.0

    black_pixels = _count_black_pixels(
        cell,
        left=left,
        top=top,
        right=right,
        bottom=bottom,
    )
    return black_pixels / total_pixels


def _count_black_pixels(
    cell: ExtractedCell,
    *,
    left: int,
    top: int,
    right: int,
    bottom: int,
) -> int:
    """Count black pixels inside a rectangular region of a cell."""
    return sum(
        1
        for y in range(top, bottom)
        for x in range(left, right)
        if cell.image.getpixel((x, y)) == BLACK_PIXEL_VALUE
    )


def _get_inner_bounds(cell: ExtractedCell) -> tuple[int, int, int, int]:
    """Return inner bounds that skip a thin border when the cell is large enough."""
    width, height = cell.image.size
    left = 1 if width > 2 else 0
    top = 1 if height > 2 else 0
    right = width - 1 if width > 2 else width
    bottom = height - 1 if height > 2 else height
    return left, top, right, bottom
