from __future__ import annotations

from pathlib import Path

import pytest

from src.domain.models import CellClassificationResult
from src.services.matrix_builder import MatrixBuildError, build_matrix


def test_build_matrix_trims_empty_outer_rows_and_columns() -> None:
    classification_result = CellClassificationResult(
        source_path=Path("synthetic.png"),
        row_count=5,
        column_count=6,
        fill_threshold=0.35,
        cells=(),
        matrix=(
            (0, 0, 0, 0, 0, 0),
            (0, 0, 1, 1, 0, 0),
            (0, 1, 1, 1, 0, 0),
            (0, 0, 1, 0, 0, 0),
            (0, 0, 0, 0, 0, 0),
        ),
    )

    result = build_matrix(classification_result)

    assert result.matrix == (
        (0, 1, 1),
        (1, 1, 1),
        (0, 1, 0),
    )
    assert result.width == 3
    assert result.height == 3


def test_build_matrix_rejects_matrix_without_filled_cells() -> None:
    classification_result = CellClassificationResult(
        source_path=Path("synthetic.png"),
        row_count=2,
        column_count=2,
        fill_threshold=0.35,
        cells=(),
        matrix=((0, 0), (0, 0)),
    )

    with pytest.raises(MatrixBuildError, match="does not contain any filled cells"):
        build_matrix(classification_result)
