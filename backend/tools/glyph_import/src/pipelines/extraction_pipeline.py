"""Pipeline for extracting individual symbols from one source image."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from src.config import AppConfig
from src.domain.models import (
    DetectedSymbol,
    ExtractionOptions,
    ExtractionResult,
    LoadedImage,
    PreprocessedImage,
)
from src.services.image_loader import InvalidImageFormatError, load_image
from src.services.image_preprocessor import preprocess_image
from src.services.symbol_extractor import SymbolExtractionError, extract_symbols


class ExtractionPipelineError(ValueError):
    """Raised when extraction cannot be completed."""


EXTRACTION_ERROR_TYPES = (
    FileNotFoundError,
    InvalidImageFormatError,
    SymbolExtractionError,
    ValueError,
)


def run_extraction_pipeline(
    *,
    input_path: str | Path,
    config: AppConfig,
    options: ExtractionOptions,
) -> ExtractionResult:
    """Run image -> preprocess -> symbol crops -> debug -> manifest extraction."""
    try:
        loaded_image = load_image(input_path)
        (
            effective_options,
            preprocessed_image,
            symbols,
            binary_debug_path,
            overlay_debug_path,
            manifest_path,
        ) = _run_extraction_with_threshold_fallback(
            loaded_image=loaded_image,
            config=config,
            options=options,
        )
    except EXTRACTION_ERROR_TYPES as exc:
        raise ExtractionPipelineError(str(exc)) from exc

    return ExtractionResult(
        options=effective_options,
        loaded_image=loaded_image,
        preprocessed_image=preprocessed_image,
        symbols=symbols,
        binary_debug_path=binary_debug_path,
        overlay_debug_path=overlay_debug_path,
        manifest_path=manifest_path,
    )


def _run_extraction_with_threshold_fallback(
    *,
    loaded_image: LoadedImage,
    config: AppConfig,
    options: ExtractionOptions,
) -> tuple[
    ExtractionOptions,
    PreprocessedImage,
    tuple[DetectedSymbol, ...],
    Path,
    Path,
    Path,
]:
    """Try several thresholds and keep the most plausible extraction result."""
    thresholds = tuple(dict.fromkeys((options.threshold, 150, 170, 190, 210, 230)))
    last_error: SymbolExtractionError | None = None
    candidates: list[
        tuple[
            tuple[int, float, float],
            ExtractionOptions,
            PreprocessedImage,
            tuple[DetectedSymbol, ...],
        ]
    ] = []

    for threshold in thresholds:
        effective_options = replace(options, threshold=threshold)
        preprocessed_image = preprocess_image(
            loaded_image,
            threshold=effective_options.threshold,
            denoise=effective_options.denoise,
            denoise_filter_size=effective_options.denoise_filter_size,
        )
        try:
            symbols, binary_debug_path, overlay_debug_path, manifest_path = extract_symbols(
                loaded_image=loaded_image,
                preprocessed_image=preprocessed_image,
                output_dir=config.extracted_dir,
                debug_dir=config.input_debug_dir,
                manifests_dir=config.manifests_dir,
                min_symbol_width=effective_options.min_symbol_width,
                min_symbol_height=effective_options.min_symbol_height,
                min_symbol_area=effective_options.min_symbol_area,
                crop_padding=effective_options.crop_padding,
            )
        except SymbolExtractionError as exc:
            last_error = exc
            continue

        candidates.append(
            (
                _score_extraction_candidate(
                    symbols=symbols,
                    min_symbol_height=effective_options.min_symbol_height,
                    image_width=preprocessed_image.binary_image.width,
                    image_height=preprocessed_image.binary_image.height,
                ),
                effective_options,
                preprocessed_image,
                symbols,
            )
        )

    if candidates:
        plausible_candidates = [
            candidate for candidate in candidates if candidate[0][0] == 1
        ]
        _, best_options, best_preprocessed_image, _ = (
            max(plausible_candidates, key=lambda item: item[0])
            if plausible_candidates
            else max(candidates, key=lambda item: item[0])
        )
        symbols, binary_debug_path, overlay_debug_path, manifest_path = extract_symbols(
            loaded_image=loaded_image,
            preprocessed_image=best_preprocessed_image,
            output_dir=config.extracted_dir,
            debug_dir=config.input_debug_dir,
            manifests_dir=config.manifests_dir,
            min_symbol_width=best_options.min_symbol_width,
            min_symbol_height=best_options.min_symbol_height,
            min_symbol_area=best_options.min_symbol_area,
            crop_padding=best_options.crop_padding,
        )
        return (
            best_options,
            best_preprocessed_image,
            symbols,
            binary_debug_path,
            overlay_debug_path,
            manifest_path,
        )

    raise last_error or SymbolExtractionError("No symbol regions found in the source image.")


def _score_extraction_candidate(
    *,
    symbols: tuple[DetectedSymbol, ...],
    min_symbol_height: int,
    image_width: int,
    image_height: int,
) -> tuple[int, float, float]:
    """Prefer many full-height symbol boxes and reject page-wide artifacts."""
    if not symbols:
        return (0, 0.0, 0.0)

    average_height = sum(symbol.height for symbol in symbols) / len(symbols)
    page_area = image_width * image_height
    largest_area_ratio = max(symbol.width * symbol.height for symbol in symbols) / page_area
    plausible_height = 1 if average_height >= min_symbol_height * 4 else 0
    full_height_count = sum(
        1 for symbol in symbols if symbol.height >= min_symbol_height * 10
    )
    average_height = sum(symbol.height for symbol in symbols) / len(symbols)
    height_variance = sum(
        (symbol.height - average_height) ** 2 for symbol in symbols
    ) / len(symbols)
    height_cv = (height_variance ** 0.5) / average_height
    return (
        plausible_height,
        1 if full_height_count >= 3 else 0,
        -height_cv,
        float(full_height_count),
        float(len(symbols)),
        -largest_area_ratio,
    )
