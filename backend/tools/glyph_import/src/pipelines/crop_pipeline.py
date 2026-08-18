"""Pipeline for cropping source images to scheme grid bounds."""

from __future__ import annotations

from pathlib import Path

from src.config import AppConfig
from src.domain.models import (
    BatchCropItemResult,
    BatchCropSummary,
    CropOptions,
    CropResult,
)
from src.services.image_loader import InvalidImageFormatError, SUPPORTED_EXTENSIONS, load_image
from src.services.image_preprocessor import preprocess_image
from src.services.scheme_cropper import SchemeCropError, crop_scheme


class CropPipelineError(ValueError):
    """Raised when crop processing cannot be completed."""


CROP_ERROR_TYPES = (
    FileNotFoundError,
    InvalidImageFormatError,
    SchemeCropError,
    ValueError,
)


def run_crop_pipeline(
    *,
    input_path: str | Path,
    config: AppConfig,
    options: CropOptions,
) -> CropResult:
    """Run image -> preprocess -> scheme crop -> debug overlay for one file."""
    try:
        loaded_image = load_image(input_path)
        preprocessed_image = preprocess_image(
            loaded_image,
            threshold=options.threshold,
            denoise=options.denoise,
            denoise_filter_size=options.denoise_filter_size,
        )
        bounds, output_path, overlay_debug_path, width, height = crop_scheme(
            loaded_image=loaded_image,
            preprocessed_image=preprocessed_image,
            output_dir=config.prepared_dir,
            debug_dir=config.input_debug_dir,
            crop_padding=options.crop_padding,
        )
    except CROP_ERROR_TYPES as exc:
        raise CropPipelineError(str(exc)) from exc

    return CropResult(
        options=options,
        loaded_image=loaded_image,
        preprocessed_image=preprocessed_image,
        bounds=bounds,
        output_path=output_path,
        width=width,
        height=height,
        overlay_debug_path=overlay_debug_path,
    )


def run_batch_crop_pipeline(
    *,
    input_dir: str | Path,
    config: AppConfig,
    options: CropOptions,
) -> BatchCropSummary:
    """Run crop pipeline for every supported image found in the input directory."""
    resolved_input_dir = Path(input_dir).resolve()
    input_paths = _find_crop_input_paths(resolved_input_dir)
    if not input_paths:
        raise CropPipelineError(f"No supported input files found in: {resolved_input_dir}")

    items: list[BatchCropItemResult] = []
    for input_path in input_paths:
        try:
            crop_result = run_crop_pipeline(
                input_path=input_path,
                config=config,
                options=options,
            )
        except CropPipelineError as exc:
            items.append(
                BatchCropItemResult(
                    input_path=input_path,
                    success=False,
                    error_message=str(exc),
                )
            )
            continue

        items.append(
            BatchCropItemResult(
                input_path=input_path,
                success=True,
                crop_result=crop_result,
            )
        )

    success_count = sum(1 for item in items if item.success)
    failure_count = len(items) - success_count
    return BatchCropSummary(
        input_dir=resolved_input_dir,
        processed_count=len(items),
        success_count=success_count,
        failure_count=failure_count,
        items=tuple(items),
    )


def _find_crop_input_paths(input_dir: Path) -> tuple[Path, ...]:
    """Return supported image files from a directory in stable order."""
    if not input_dir.exists() or not input_dir.is_dir():
        return ()

    return tuple(
        sorted(
            (
                path.resolve()
                for path in input_dir.iterdir()
                if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS
            ),
            key=lambda path: (path.stem, path.suffix.lower()),
        )
    )
