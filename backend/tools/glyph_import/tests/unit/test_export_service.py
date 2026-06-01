from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.domain.models import GlyphDraft
from src.services.export_service import GlyphExportError, export_glyph


def test_export_glyph_writes_json_file(tmp_path: Path) -> None:
    glyph = GlyphDraft(
        char="A",
        width=3,
        height=2,
        cells=((1, 0, 1), (0, 1, 0)),
    )

    result = export_glyph(glyph, output_dir=tmp_path)

    assert result.output_path == tmp_path / "A.json"
    payload = json.loads(result.output_path.read_text(encoding="utf-8"))
    assert payload == {
        "char": "A",
        "width": 3,
        "height": 2,
        "cells": [[1, 0, 1], [0, 1, 0]],
    }


def test_export_glyph_rejects_inconsistent_dimensions(tmp_path: Path) -> None:
    glyph = GlyphDraft(
        char="A",
        width=4,
        height=2,
        cells=((1, 0, 1), (0, 1, 0)),
    )

    with pytest.raises(GlyphExportError, match="Glyph width does not match"):
        export_glyph(glyph, output_dir=tmp_path)
