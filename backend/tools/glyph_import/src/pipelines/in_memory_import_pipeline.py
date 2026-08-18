"""Side-effect-free image-to-matrix pipeline shared with the production API."""

from __future__ import annotations

import io

from PIL import Image

from ..domain.models import ImportPipelineOptions, MatrixBuildResult
from ..services.cell_classifier import classify_cells
from ..services.cell_extractor import extract_cells
from ..services.grid_detector import detect_grid
from ..services.image_loader import load_image_bytes
from ..services.image_preprocessor import preprocess_image
from ..services.matrix_builder import build_matrix

MAX_IMAGE_PIXELS = 25_000_000


class InMemoryImportError(ValueError):
    """Raised when uploaded image processing cannot produce a matrix."""


def build_pattern_matrix_from_bytes(
    *,
    content: bytes,
    filename: str,
    options: ImportPipelineOptions,
) -> MatrixBuildResult:
    """Build a trimmed matrix using the same core stages as the CLI pipeline."""
    try:
        loaded_image = load_image_bytes(content, filename)
        with Image.open(io.BytesIO(content)) as image:
            width, height = image.size
        if width * height > MAX_IMAGE_PIXELS:
            raise InMemoryImportError("Image exceeds the 25 megapixel limit.")
        preprocessed = preprocess_image(
            loaded_image,
            threshold=options.threshold,
            denoise=options.denoise,
            denoise_filter_size=options.denoise_filter_size,
        )
        grid = detect_grid(
            preprocessed,
            min_grid_step=options.min_grid_step,
            max_grid_step=options.max_grid_step,
            expected_columns=options.expected_columns,
            expected_rows=options.expected_rows,
        )
        extracted = extract_cells(preprocessed, grid)
        classified = classify_cells(extracted, fill_threshold=options.fill_threshold)
        return build_matrix(classified)
    except (OSError, ValueError) as exc:
        if isinstance(exc, InMemoryImportError):
            raise
        raise InMemoryImportError(str(exc)) from exc
