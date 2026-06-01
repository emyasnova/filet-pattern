from __future__ import annotations

from pathlib import Path

import pytest

from src.domain.models import ImageFormat
from src.services.image_loader import InvalidImageFormatError, load_image


MINIMAL_PNG = (
    b"\x89PNG\r\n\x1a\n"
    b"\x00\x00\x00\rIHDR"
    b"\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00"
    b"\x90wS\xde"
    b"\x00\x00\x00\x0cIDATx\x9cc`\x00\x00\x00\x02\x00\x01"
    b"\xe5'\xd4\xa2"
    b"\x00\x00\x00\x00IEND\xaeB`\x82"
)

MINIMAL_JPG = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00\xff\xd9"


def test_load_image_reads_png_file(tmp_path: Path) -> None:
    image_path = tmp_path / "glyph.png"
    image_path.write_bytes(MINIMAL_PNG)

    loaded_image = load_image(image_path)

    assert loaded_image.path == image_path.resolve()
    assert loaded_image.image_format is ImageFormat.PNG
    assert loaded_image.content == MINIMAL_PNG


def test_load_image_reads_jpg_file(tmp_path: Path) -> None:
    image_path = tmp_path / "glyph.jpg"
    image_path.write_bytes(MINIMAL_JPG)

    loaded_image = load_image(image_path)

    assert loaded_image.path == image_path.resolve()
    assert loaded_image.image_format is ImageFormat.JPG
    assert loaded_image.content == MINIMAL_JPG


def test_load_image_raises_for_missing_file(tmp_path: Path) -> None:
    image_path = tmp_path / "missing.png"

    with pytest.raises(FileNotFoundError):
        load_image(image_path)


def test_load_image_raises_for_unsupported_extension(tmp_path: Path) -> None:
    image_path = tmp_path / "glyph.bmp"
    image_path.write_bytes(b"BMplaceholder")

    with pytest.raises(InvalidImageFormatError, match=r"Only \.jpg and \.png"):
        load_image(image_path)


def test_load_image_raises_for_invalid_png_signature(tmp_path: Path) -> None:
    image_path = tmp_path / "glyph.png"
    image_path.write_bytes(b"not-a-real-png")

    with pytest.raises(InvalidImageFormatError, match="Invalid PNG file"):
        load_image(image_path)


def test_load_image_raises_for_invalid_jpg_signature(tmp_path: Path) -> None:
    image_path = tmp_path / "glyph.jpg"
    image_path.write_bytes(b"not-a-real-jpg")

    with pytest.raises(InvalidImageFormatError, match="Invalid JPG file"):
        load_image(image_path)
