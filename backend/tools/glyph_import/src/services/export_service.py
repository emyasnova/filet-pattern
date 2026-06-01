"""Export glyph drafts to JSON files."""

from __future__ import annotations

from pathlib import Path

from src.domain.models import ExportedGlyph, GlyphDraft
from src.utils.json_utils import write_json_file


class GlyphExportError(ValueError):
    """Raised when a glyph cannot be exported to JSON."""


def export_glyph(glyph: GlyphDraft, *, output_dir: Path) -> ExportedGlyph:
    """Serialize a glyph draft to `output/json/<char>.json`."""
    if not glyph.char:
        raise GlyphExportError("Glyph char must not be empty.")

    if glyph.width <= 0 or glyph.height <= 0:
        raise GlyphExportError("Glyph dimensions must be positive.")

    if len(glyph.cells) != glyph.height:
        raise GlyphExportError("Glyph height does not match the cell matrix.")

    if any(len(row) != glyph.width for row in glyph.cells):
        raise GlyphExportError("Glyph width does not match the cell matrix.")

    output_path = output_dir / f"{glyph.char}.json"
    payload = {
        "char": glyph.char,
        "width": glyph.width,
        "height": glyph.height,
        "cells": [list(row) for row in glyph.cells],
    }
    write_json_file(output_path, payload)

    return ExportedGlyph(char=glyph.char, output_path=output_path)
