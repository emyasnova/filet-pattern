"""Image preprocessing for glyph imports."""

from __future__ import annotations

import io
from pathlib import Path

from PIL import Image, ImageFilter, ImageOps

from src.domain.models import LoadedImage, PreprocessedImage


DEFAULT_THRESHOLD = 128
DEFAULT_MEDIAN_FILTER_SIZE = 3


def preprocess_image(
    loaded_image: LoadedImage,
    *,
    threshold: int = DEFAULT_THRESHOLD,
    denoise: bool = True,
    denoise_filter_size: int = DEFAULT_MEDIAN_FILTER_SIZE,
    debug_dir: Path | None = None,
    debug_prefix: str | None = None,
) -> PreprocessedImage:
    """Convert the source image to grayscale, optionally denoise, and binarize it."""
    if not 0 <= threshold <= 255:
        raise ValueError("Threshold must be in the range 0..255.")
    if denoise_filter_size <= 0 or denoise_filter_size % 2 == 0:
        raise ValueError("denoise_filter_size must be a positive odd integer.")

    source_image = Image.open(io.BytesIO(loaded_image.content))
    source_image.load()

    grayscale_image = ImageOps.grayscale(source_image)
    denoised_image = (
        _denoise_image(grayscale_image, filter_size=denoise_filter_size)
        if denoise
        else grayscale_image.copy()
    )
    binary_image = _binarize_image(denoised_image, threshold=threshold)

    preprocessed_image = PreprocessedImage(
        source_path=loaded_image.path,
        grayscale_image=grayscale_image,
        denoised_image=denoised_image,
        binary_image=binary_image,
    )

    if debug_dir is not None:
        save_debug_images(
            preprocessed_image,
            debug_dir=debug_dir,
            prefix=debug_prefix or loaded_image.path.stem,
        )

    return preprocessed_image


def save_debug_images(
    preprocessed_image: PreprocessedImage,
    *,
    debug_dir: Path,
    prefix: str,
) -> tuple[Path, Path, Path]:
    """Persist preprocessing stages as debug PNG files."""
    debug_dir.mkdir(parents=True, exist_ok=True)

    grayscale_path = debug_dir / f"{prefix}_grayscale.png"
    denoised_path = debug_dir / f"{prefix}_denoised.png"
    binary_path = debug_dir / f"{prefix}_binary.png"

    preprocessed_image.grayscale_image.save(grayscale_path, format="PNG")
    preprocessed_image.denoised_image.save(denoised_path, format="PNG")
    preprocessed_image.binary_image.save(binary_path, format="PNG")
    return grayscale_path, denoised_path, binary_path


def _denoise_image(image: Image.Image, *, filter_size: int) -> Image.Image:
    """Apply a small median filter to remove isolated noise."""
    return image.filter(ImageFilter.MedianFilter(size=filter_size))


def _binarize_image(image: Image.Image, *, threshold: int) -> Image.Image:
    """Convert a grayscale image to a black-and-white mask."""
    return image.point(lambda pixel: 255 if pixel >= threshold else 0, mode="L")
