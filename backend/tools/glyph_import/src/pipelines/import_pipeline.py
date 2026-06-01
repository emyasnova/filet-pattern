"""End-to-end glyph import pipeline orchestration."""

from __future__ import annotations

from pathlib import Path

from src.config import AppConfig
from src.domain.models import (
    BatchImportItemResult,
    BatchImportSummary,
    ImportPipelineOptions,
    ImportPipelineResult,
)
from src.services.cell_classifier import (
    CellClassificationError,
    classify_cells,
)
from src.services.cell_extractor import CellExtractionError, extract_cells
from src.services.export_service import GlyphExportError, export_glyph
from src.services.glyph_builder import GlyphBuildError, build_glyph
from src.services.grid_detector import (
    GridDetectionError,
    detect_grid,
    save_grid_debug_image,
)
from src.services.image_loader import (
    InvalidImageFormatError,
    SUPPORTED_EXTENSIONS,
    load_image,
)
from src.services.image_preprocessor import preprocess_image, save_debug_images
from src.services.matrix_builder import MatrixBuildError, build_matrix
from src.services.preview_service import (
    PreviewRenderError,
    render_preview,
    verify_preview_matches_export,
)


class ImportPipelineError(ValueError):
    """Raised when any stage of the import pipeline fails."""


PIPELINE_ERROR_TYPES = (
    FileNotFoundError,
    InvalidImageFormatError,
    GridDetectionError,
    CellExtractionError,
    CellClassificationError,
    MatrixBuildError,
    GlyphBuildError,
    GlyphExportError,
    PreviewRenderError,
    ValueError,
)


def run_import_pipeline(
    *,
    input_path: str | Path,
    char: str,
    config: AppConfig,
    options: ImportPipelineOptions,
) -> ImportPipelineResult:
    """Run the full image -> preprocess -> grid -> cells -> matrix -> JSON pipeline."""
    try:
        loaded_image = load_image(input_path)
        preprocessed_image = preprocess_image(
            loaded_image,
            threshold=options.threshold,
            denoise=options.denoise,
            denoise_filter_size=options.denoise_filter_size,
        )
        grayscale_path, denoised_path, binary_path = save_debug_images(
            preprocessed_image,
            debug_dir=config.debug_dir,
            prefix=loaded_image.path.stem,
        )
        grid_result = detect_grid(
            preprocessed_image,
            min_grid_step=options.min_grid_step,
            max_grid_step=options.max_grid_step,
            expected_columns=options.expected_columns,
            expected_rows=options.expected_rows,
        )
        grid_debug_path = save_grid_debug_image(
            preprocessed_image=preprocessed_image,
            detection_result=grid_result,
            debug_dir=config.debug_dir,
            prefix=loaded_image.path.stem,
        )
        cell_result = extract_cells(preprocessed_image, grid_result)
        classification_result = classify_cells(
            cell_result,
            fill_threshold=options.fill_threshold,
        )
        matrix_result = build_matrix(classification_result)
        glyph_result = build_glyph(matrix_result, char=char)
        exported_glyph = export_glyph(glyph_result, output_dir=config.json_dir)
        preview_result = render_preview(
            glyph_result,
            output_dir=config.previews_dir,
            cell_size=options.preview_cell_size,
        )
        verify_preview_matches_export(
            exported_glyph,
            preview_result,
            cell_size=options.preview_cell_size,
        )
    except PIPELINE_ERROR_TYPES as exc:
        raise ImportPipelineError(str(exc)) from exc

    return ImportPipelineResult(
        options=options,
        loaded_image=loaded_image,
        preprocessed_image=preprocessed_image,
        grayscale_debug_path=grayscale_path,
        denoised_debug_path=denoised_path,
        binary_debug_path=binary_path,
        grid_result=grid_result,
        grid_debug_path=grid_debug_path,
        cell_result=cell_result,
        classification_result=classification_result,
        matrix_result=matrix_result,
        glyph_result=glyph_result,
        exported_glyph=exported_glyph,
        preview_result=preview_result,
    )


def run_batch_import_pipeline(
    *,
    config: AppConfig,
    options: ImportPipelineOptions,
) -> BatchImportSummary:
    """Run the import pipeline for every supported file found in `input/extracted`."""
    input_paths = _find_batch_input_paths(config.extracted_dir)
    if not input_paths:
        raise ImportPipelineError(f"No supported input files found in: {config.extracted_dir}")

    items: list[BatchImportItemResult] = []
    for input_path in input_paths:
        char = input_path.stem
        try:
            pipeline_result = run_import_pipeline(
                input_path=input_path,
                char=char,
                config=config,
                options=options,
            )
        except ImportPipelineError as exc:
            items.append(
                BatchImportItemResult(
                    input_path=input_path,
                    char=char,
                    success=False,
                    error_message=str(exc),
                )
            )
            continue

        items.append(
            BatchImportItemResult(
                input_path=input_path,
                char=char,
                success=True,
                pipeline_result=pipeline_result,
            )
        )

    success_count = sum(1 for item in items if item.success)
    failure_count = len(items) - success_count
    return BatchImportSummary(
        input_dir=config.extracted_dir,
        processed_count=len(items),
        success_count=success_count,
        failure_count=failure_count,
        items=tuple(items),
    )


def _find_batch_input_paths(input_dir: Path) -> tuple[Path, ...]:
    """Return supported one-symbol image files from the input directory in stable order."""
    if not input_dir.exists() or not input_dir.is_dir():
        return ()

    return tuple(
        sorted(
            (
                path
                for path in input_dir.iterdir()
                if (
                    path.is_file()
                    and path.suffix.lower() in SUPPORTED_EXTENSIONS
                    and len(path.stem) == 1
                )
            ),
            key=lambda path: (path.stem, path.suffix.lower()),
        )
    )
