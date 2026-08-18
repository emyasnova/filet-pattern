"""Services for loading source glyph images from disk."""

from __future__ import annotations

import io
from pathlib import Path

from PIL import Image, UnidentifiedImageError

from ..domain.models import ImageFormat, LoadedImage


PIL_FORMATS_BY_EXTENSION = {
    ImageFormat.PNG: {"PNG"},
    ImageFormat.JPG: {"JPEG", "WEBP"},
}
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
JPEG_SOI = b"\xff\xd8"
JPEG_EOI = b"\xff\xd9"


class InvalidImageFormatError(ValueError):
    """Raised when the source file has an unsupported or invalid image format."""


SUPPORTED_EXTENSIONS = {
    ".jpg": ImageFormat.JPG,
    ".jpeg": ImageFormat.JPG,
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


def load_image_bytes(content: bytes, filename: str) -> LoadedImage:
    """Validate uploaded image bytes without writing them to disk."""
    path = Path(filename)
    image_format = SUPPORTED_EXTENSIONS.get(path.suffix.lower())
    if image_format is None:
        raise InvalidImageFormatError(
            "Unsupported image format. Only .jpg, .jpeg and .png files are allowed."
        )
    if not content:
        raise InvalidImageFormatError("Image file must not be empty.")
    _validate_signature(content=content, image_format=image_format, path=path)
    return LoadedImage(path=path, image_format=image_format, content=content)


def _validate_signature(*, content: bytes, image_format: ImageFormat, path: Path) -> None:
    """Validate the image signature for supported formats."""
    if _has_expected_signature(content=content, image_format=image_format):
        return

    try:
        with Image.open(io.BytesIO(content)) as image:
            image.verify()
            detected_format = image.format
    except (SyntaxError, UnidentifiedImageError, OSError) as exc:
        raise InvalidImageFormatError(
            f"Invalid {image_format.value.upper()} file: {path}"
        ) from exc

    allowed_formats = PIL_FORMATS_BY_EXTENSION.get(image_format)
    if allowed_formats is None or detected_format not in allowed_formats:
        raise InvalidImageFormatError(
            f"Invalid {image_format.value.upper()} file: {path}"
        )


def _has_expected_signature(*, content: bytes, image_format: ImageFormat) -> bool:
    """Return whether content has the standard signature for the declared extension."""
    if image_format is ImageFormat.PNG:
        return content.startswith(PNG_SIGNATURE)
    if image_format is ImageFormat.JPG:
        return content.startswith(JPEG_SOI) and content.endswith(JPEG_EOI)
    return False
