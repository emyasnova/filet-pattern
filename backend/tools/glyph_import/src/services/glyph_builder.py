"""Build a draft glyph object from a trimmed matrix."""

from __future__ import annotations

from src.domain.models import GlyphDraft, MatrixBuildResult


class GlyphBuildError(ValueError):
    """Raised when a glyph draft cannot be created."""


def build_glyph(matrix_result: MatrixBuildResult, *, char: str) -> GlyphDraft:
    """Create a glyph draft using the trimmed matrix and explicit character."""
    if not char:
        raise GlyphBuildError("char must not be empty.")

    if matrix_result.width <= 0 or matrix_result.height <= 0:
        raise GlyphBuildError("Matrix dimensions must be positive.")

    return GlyphDraft(
        char=char,
        width=matrix_result.width,
        height=matrix_result.height,
        cells=matrix_result.matrix,
    )
