from __future__ import annotations

import pytest

from pathlib import Path

from src.domain.models import MatrixBuildResult
from src.services.glyph_builder import GlyphBuildError, build_glyph


def test_build_glyph_creates_draft_from_trimmed_matrix() -> None:
    matrix_result = MatrixBuildResult(
        source_path=Path("synthetic.png"),
        matrix=((0, 1, 1), (1, 1, 1), (0, 1, 0)),
        width=3,
        height=3,
    )

    glyph = build_glyph(matrix_result, char="A")

    assert glyph.char == "A"
    assert glyph.width == 3
    assert glyph.height == 3
    assert glyph.cells == ((0, 1, 1), (1, 1, 1), (0, 1, 0))


def test_build_glyph_rejects_empty_char() -> None:
    matrix_result = MatrixBuildResult(
        source_path=Path("synthetic.png"),
        matrix=((1,),),
        width=1,
        height=1,
    )

    with pytest.raises(GlyphBuildError, match="char must not be empty"):
        build_glyph(matrix_result, char="")
