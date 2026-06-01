"""Build a trimmed glyph matrix from classified cells."""

from __future__ import annotations

from src.domain.models import CellClassificationResult, MatrixBuildResult


class MatrixBuildError(ValueError):
    """Raised when the classified matrix cannot be converted into a glyph matrix."""


def build_matrix(classification_result: CellClassificationResult) -> MatrixBuildResult:
    """Trim empty outer rows and columns from the classified matrix."""
    matrix = classification_result.matrix
    if not matrix:
        raise MatrixBuildError("Classification matrix must not be empty.")

    row_count = len(matrix)
    column_count = len(matrix[0])
    if column_count == 0:
        raise MatrixBuildError("Classification matrix must not contain empty rows.")

    if any(len(row) != column_count for row in matrix):
        raise MatrixBuildError("Classification matrix must be rectangular.")

    non_empty_rows = [index for index, row in enumerate(matrix) if any(row)]
    if not non_empty_rows:
        raise MatrixBuildError("Classification matrix does not contain any filled cells.")

    left, right = _find_non_empty_column_bounds(matrix)
    top = non_empty_rows[0]
    bottom = non_empty_rows[-1]

    trimmed_matrix = tuple(
        tuple(row[left : right + 1]) for row in matrix[top : bottom + 1]
    )

    return MatrixBuildResult(
        source_path=classification_result.source_path,
        matrix=trimmed_matrix,
        width=right - left + 1,
        height=bottom - top + 1,
    )


def _find_non_empty_column_bounds(
    matrix: tuple[tuple[int, ...], ...],
) -> tuple[int, int]:
    """Return left and right bounds of columns containing filled cells."""
    column_count = len(matrix[0])
    non_empty_columns = [
        column_index
        for column_index in range(column_count)
        if any(row[column_index] for row in matrix)
    ]
    return non_empty_columns[0], non_empty_columns[-1]
