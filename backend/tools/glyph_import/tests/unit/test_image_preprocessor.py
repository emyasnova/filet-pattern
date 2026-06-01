from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image

from src.services.image_loader import load_image
from src.services.image_preprocessor import preprocess_image


def test_preprocess_image_converts_to_grayscale_and_binary(tmp_path: Path) -> None:
    source_path = tmp_path / "source.png"
    image = Image.new("RGB", (2, 1))
    image.putdata([(0, 0, 0), (255, 255, 255)])
    image.save(source_path, format="PNG")

    loaded_image = load_image(source_path)
    preprocessed_image = preprocess_image(loaded_image, threshold=128, denoise=False)

    assert preprocessed_image.grayscale_image.mode == "L"
    assert preprocessed_image.binary_image.mode == "L"
    assert preprocessed_image.grayscale_image.getpixel((0, 0)) == 0
    assert preprocessed_image.grayscale_image.getpixel((1, 0)) == 255
    assert preprocessed_image.binary_image.getpixel((0, 0)) == 0
    assert preprocessed_image.binary_image.getpixel((1, 0)) == 255


def test_preprocess_image_applies_median_denoise(tmp_path: Path) -> None:
    source_path = tmp_path / "noise.png"
    image = Image.new("RGB", (3, 3), color=(255, 255, 255))
    image.putpixel((1, 1), (0, 0, 0))
    image.save(source_path, format="PNG")

    loaded_image = load_image(source_path)
    preprocessed_image = preprocess_image(loaded_image, denoise=True, denoise_filter_size=3)

    assert preprocessed_image.grayscale_image.getpixel((1, 1)) == 0
    assert preprocessed_image.denoised_image.getpixel((1, 1)) == 255


def test_preprocess_image_saves_debug_artifacts(tmp_path: Path) -> None:
    source_path = tmp_path / "glyph.png"
    debug_dir = tmp_path / "debug"
    image = Image.new("RGB", (1, 1), color=(80, 80, 80))
    image.save(source_path, format="PNG")

    loaded_image = load_image(source_path)
    preprocess_image(loaded_image, debug_dir=debug_dir, debug_prefix="glyph_a")

    assert (debug_dir / "glyph_a_grayscale.png").exists()
    assert (debug_dir / "glyph_a_denoised.png").exists()
    assert (debug_dir / "glyph_a_binary.png").exists()


def test_preprocess_image_rejects_invalid_threshold(tmp_path: Path) -> None:
    source_path = tmp_path / "glyph.png"
    image = Image.new("RGB", (1, 1), color=(255, 255, 255))
    image.save(source_path, format="PNG")

    loaded_image = load_image(source_path)

    with pytest.raises(ValueError, match="Threshold must be in the range 0..255"):
        preprocess_image(loaded_image, threshold=300)


def test_preprocess_image_rejects_even_denoise_size(tmp_path: Path) -> None:
    source_path = tmp_path / "glyph.png"
    image = Image.new("RGB", (1, 1), color=(255, 255, 255))
    image.save(source_path, format="PNG")

    loaded_image = load_image(source_path)

    with pytest.raises(ValueError, match="positive odd integer"):
        preprocess_image(loaded_image, denoise_filter_size=4)
