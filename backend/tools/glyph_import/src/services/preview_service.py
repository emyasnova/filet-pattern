"""Render glyph previews and verify them against exported JSON."""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw

from src.domain.models import ExportedGlyph, ExportedPreview, GlyphDraft

DEFAULT_PREVIEW_CELL_SIZE = 16
GRID_COLOR = "#C8C8C8"
FILLED_COLOR = "#111111"
EMPTY_COLOR = "#FFFFFF"


class PreviewRenderError(ValueError):
    """Raised when a preview cannot be rendered or validated."""


def render_preview(
    glyph: GlyphDraft,
    *,
    output_dir: Path,
    cell_size: int = DEFAULT_PREVIEW_CELL_SIZE,
) -> ExportedPreview:
    """Render a simple black/white preview image for the glyph matrix."""
    if cell_size <= 0:
        raise PreviewRenderError("cell_size must be positive.")

    if glyph.width <= 0 or glyph.height <= 0:
        raise PreviewRenderError("Glyph dimensions must be positive.")

    if len(glyph.cells) != glyph.height:
        raise PreviewRenderError("Glyph height does not match the cell matrix.")

    if any(len(row) != glyph.width for row in glyph.cells):
        raise PreviewRenderError("Glyph width does not match the cell matrix.")

    image_width = glyph.width * cell_size
    image_height = glyph.height * cell_size
    image = Image.new("RGB", (image_width, image_height), EMPTY_COLOR)
    draw = ImageDraw.Draw(image)

    for row_index, row in enumerate(glyph.cells):
        for column_index, value in enumerate(row):
            left = column_index * cell_size
            top = row_index * cell_size
            right = left + cell_size - 1
            bottom = top + cell_size - 1
            fill_color = FILLED_COLOR if value else EMPTY_COLOR
            draw.rectangle((left, top, right, bottom), fill=fill_color)
            draw.rectangle((left, top, right, bottom), outline=GRID_COLOR)

    output_path = output_dir / f"{glyph.char}.png"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path, format="PNG")

    return ExportedPreview(
        char=glyph.char,
        output_path=output_path,
        image_width=image_width,
        image_height=image_height,
    )


def verify_preview_matches_export(
    exported_glyph: ExportedGlyph,
    preview: ExportedPreview,
    *,
    cell_size: int = DEFAULT_PREVIEW_CELL_SIZE,
) -> None:
    """Validate that preview dimensions and file naming match the exported JSON."""
    if cell_size <= 0:
        raise PreviewRenderError("cell_size must be positive.")

    if preview.char != exported_glyph.char:
        raise PreviewRenderError("Preview char does not match exported glyph char.")

    payload = json.loads(exported_glyph.output_path.read_text(encoding="utf-8"))
    width = payload.get("width")
    height = payload.get("height")
    char = payload.get("char")

    if char != preview.char:
        raise PreviewRenderError("Preview char does not match exported JSON.")

    expected_width = width * cell_size
    expected_height = height * cell_size
    if preview.image_width != expected_width or preview.image_height != expected_height:
        raise PreviewRenderError("Preview dimensions do not match exported JSON.")
