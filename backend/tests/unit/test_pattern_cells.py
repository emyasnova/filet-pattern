"""Tests for automatic pattern transparency."""

from app.domain.services.pattern_cells import normalize_pattern_transparency


def test_normalize_pattern_transparency_preserves_enclosed_hole() -> None:
    """Only empty cells connected to the outside should become transparent."""
    cells = [
        [0, 1, 0, 0, 0],
        [1, 1, 1, 1, 0],
        [0, 1, 0, 1, 0],
        [0, 1, 1, 1, 0],
        [0, 0, 0, 0, 0],
    ]

    result = normalize_pattern_transparency(cells)

    assert result[2][2] == 0
    assert result[0][0] is None
    assert result[4][4] is None


def test_normalize_pattern_transparency_recalculates_existing_nulls() -> None:
    """Existing nulls enclosed by edits should become ordinary empty cells."""
    result = normalize_pattern_transparency(
        [[1, 1, 1], [1, None, 1], [1, 1, 1]]
    )

    assert result[1][1] == 0
