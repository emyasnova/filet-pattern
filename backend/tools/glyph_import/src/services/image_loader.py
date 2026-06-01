"""Services for loading source glyph images from disk."""

from __future__ import annotations

from pathlib import Path

from src.domain.models import ImageFormat, LoadedImage


PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
JPEG_SOI = b"\xff\xd8"
JPEG_EOI = b"\xff\xd9"


class InvalidImageFormatError(ValueError):
    """Raised when the source file has an unsupported or invalid image format."""


SUPPORTED_EXTENSIONS = {
    ".jpg": ImageFormat.JPG,
    ".png": ImageFormat.PNG,
}


def load_image(path: str | Path) -> LoadedImage:
    """Load a JPG or PNG image from disk and validate its format."""
    image_path = Path(path).resolve()

    if not image_path.exists():
        raise FileNotFoundError(f"Image file does not exist: {image_path}")

    if not image_path.is_file():
        raise FileNotFoundError(f"Image path is not a file: {image_path}")

    image_format = SUPPORTED_EXTENSIONS.get(image_path.suffix.lower())
    if image_format is None:
        raise InvalidImageFormatError(
            "Unsupported image format. Only .jpg and .png files are allowed."
        )

    content = image_path.read_bytes()
    _validate_signature(content=content, image_format=image_format, path=image_path)
    return LoadedImage(path=image_path, image_format=image_format, content=content)


def _validate_signature(*, content: bytes, image_format: ImageFormat, path: Path) -> None:
    """Validate the image signature for supported formats."""
    if image_format is ImageFormat.PNG:
        if not content.startswith(PNG_SIGNATURE):
            raise InvalidImageFormatError(f"Invalid PNG file: {path}")
        return

    if image_format is ImageFormat.JPG:
        if not (content.startswith(JPEG_SOI) and content.endswith(JPEG_EOI)):
            raise InvalidImageFormatError(f"Invalid JPG file: {path}")
        return

    raise InvalidImageFormatError(f"Unsupported image format: {path}")
