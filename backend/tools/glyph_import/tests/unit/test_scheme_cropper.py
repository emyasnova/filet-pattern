from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image, ImageDraw

from src.services.image_loader import load_image
from src.services.image_preprocessor import preprocess_image
from src.services.scheme_cropper import (
    SchemeCropError,
    crop_scheme,
    detect_scheme_crop_bounds,
)


def test_detect_scheme_crop_bounds_keeps_only_outer_grid() -> None:
    image = _create_scheme_with_caption()

    bounds = detect_scheme_crop_bounds(image, crop_padding=0)

    assert bounds.left == 20
    assert bounds.top == 16
    assert bounds.right == 100
    assert bounds.bottom == 76


def test_detect_scheme_crop_bounds_applies_padding_inside_image() -> None:
    image = _create_scheme_with_caption()

    bounds = detect_scheme_crop_bounds(image, crop_padding=5)

    assert bounds.left == 15
    assert bounds.top == 11
    assert bounds.right == 105
    assert bounds.bottom == 81


def test_detect_scheme_crop_bounds_rejects_image_without_grid() -> None:
    image = Image.new("L", (80, 60), 255)
    draw = ImageDraw.Draw(image)
    draw.text((10, 20), "caption", fill=0)

    with pytest.raises(SchemeCropError, match="scheme grid crop"):
        detect_scheme_crop_bounds(image)


def test_crop_scheme_saves_crop_and_overlay(tmp_path: Path) -> None:
    source_path = tmp_path / "source.png"
    _create_scheme_with_caption().save(source_path, format="PNG")
    loaded_image = load_image(source_path)
    preprocessed_image = preprocess_image(loaded_image, denoise=False)

    bounds, output_path, overlay_path, width, height = crop_scheme(
        loaded_image=loaded_image,
        preprocessed_image=preprocessed_image,
        output_dir=tmp_path / "input" / "prepared",
        debug_dir=tmp_path / "input" / "debug",
        crop_padding=1,
    )

    assert bounds.left == 19
    assert bounds.top == 15
    assert bounds.right == 101
    assert bounds.bottom == 77
    assert output_path == tmp_path / "input" / "prepared" / "source.png"
    assert overlay_path == tmp_path / "input" / "debug" / "source_crop_overlay.png"
    assert output_path.exists()
    assert overlay_path.exists()
    assert (width, height) == (83, 63)


def _create_scheme_with_caption() -> Image.Image:
    image = Image.new("L", (130, 110), 255)
    draw = ImageDraw.Draw(image)
    left, top, right, bottom = 20, 16, 100, 76
    step = 10
    for x in range(left, right + 1, step):
        draw.line((x, top, x, bottom), fill=0, width=1)
    for y in range(top, bottom + 1, step):
        draw.line((left, y, right, y), fill=0, width=1)
    draw.rectangle((42, 28, 58, 44), fill=0)
    draw.rectangle((72, 48, 88, 64), fill=0)
    draw.text((24, 92), "Created by Stitchboard", fill=0)
    return image
