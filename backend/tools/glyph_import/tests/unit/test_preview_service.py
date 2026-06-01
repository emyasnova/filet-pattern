from __future__ import annotations

import json
from pathlib import Path

import pytest
from PIL import Image

from src.domain.models import ExportedGlyph, GlyphDraft
from src.services.preview_service import (
    DEFAULT_PREVIEW_CELL_SIZE,
    PreviewRenderError,
    render_preview,
    verify_preview_matches_export,
)


def test_render_preview_writes_png_with_expected_size(tmp_path: Path) -> None:
    glyph = GlyphDraft(
        char="A",
        width=3,
        height=2,
        cells=((1, 0, 1), (0, 1, 0)),
    )

    preview = render_preview(glyph, output_dir=tmp_path, cell_size=10)

    assert preview.output_path == tmp_path / "A.png"
    with Image.open(preview.output_path) as image:
        assert image.size == (30, 20)


def test_verify_preview_matches_export_accepts_matching_files(tmp_path: Path) -> None:
    exported_path = tmp_path / "A.json"
    exported_path.write_text(
        json.dumps(
            {
                "char": "A",
                "width": 3,
                "height": 2,
                "cells": [[1, 0, 1], [0, 1, 0]],
            }
        ),
        encoding="utf-8",
    )
    exported_glyph = ExportedGlyph(char="A", output_path=exported_path)
    glyph = GlyphDraft(
        char="A",
        width=3,
        height=2,
        cells=((1, 0, 1), (0, 1, 0)),
    )
    preview = render_preview(
        glyph,
        output_dir=tmp_path,
        cell_size=DEFAULT_PREVIEW_CELL_SIZE,
    )

    verify_preview_matches_export(exported_glyph, preview)


def test_verify_preview_matches_export_rejects_size_mismatch(tmp_path: Path) -> None:
    exported_path = tmp_path / "A.json"
    exported_path.write_text(
        json.dumps(
            {
                "char": "A",
                "width": 4,
                "height": 2,
                "cells": [[1, 0, 1, 0], [0, 1, 0, 1]],
            }
        ),
        encoding="utf-8",
    )
    exported_glyph = ExportedGlyph(char="A", output_path=exported_path)
    glyph = GlyphDraft(
        char="A",
        width=3,
        height=2,
        cells=((1, 0, 1), (0, 1, 0)),
    )
    preview = render_preview(
        glyph,
        output_dir=tmp_path,
        cell_size=DEFAULT_PREVIEW_CELL_SIZE,
    )

    with pytest.raises(PreviewRenderError, match="Preview dimensions do not match"):
        verify_preview_matches_export(exported_glyph, preview)
