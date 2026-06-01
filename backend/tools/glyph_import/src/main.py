"""CLI entrypoint for the glyph import tool."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path
from typing import Sequence

from src.domain.models import (
    BatchImportSummary,
    ExtractionOptions,
    ExtractionResult,
    ImportPipelineOptions,
    ImportPipelineResult,
)
from src.services.cell_classifier import DEFAULT_FILL_THRESHOLD
from src.config import get_default_config
from src.pipelines.extraction_pipeline import ExtractionPipelineError, run_extraction_pipeline
from src.pipelines.import_pipeline import (
    ImportPipelineError,
    run_batch_import_pipeline,
    run_import_pipeline,
)
from src.utils.logging_utils import setup_logging


def emit_status(logger: logging.Logger, message: str, *args: object) -> None:
    """Write a status message to console and log file."""
    text = message % args if args else message
    print(text)
    logger.info(text)


def emit_debug(logger: logging.Logger, enabled: bool, message: str, *args: object) -> None:
    """Write a debug-only message to console and log file."""
    if not enabled:
        return
    text = message % args if args else message
    print(text)
    logger.debug(text)


def build_parser() -> argparse.ArgumentParser:
    """Create the CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="glyph-import",
        description="Offline CLI skeleton for glyph import.",
    )
    parser.add_argument(
        "--input",
        type=Path,
        help="Path to the source image file.",
    )
    parser.add_argument(
        "--batch",
        action="store_true",
        help="Process all supported files from input/extracted using filename stems as chars.",
    )
    parser.add_argument(
        "--extract",
        action="store_true",
        help="Extract separate symbol crops from one multi-symbol jpg/png image.",
    )
    parser.add_argument(
        "--char",
        help="Symbol represented by the source image.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate arguments and print the planned operation only.",
    )
    parser.add_argument(
        "--fill-threshold",
        type=float,
        default=DEFAULT_FILL_THRESHOLD,
        help="Black-pixel ratio threshold for classifying a cell as filled.",
    )
    parser.add_argument(
        "--threshold",
        type=int,
        default=128,
        help="Binary threshold for preprocessing in the range 0..255.",
    )
    parser.add_argument(
        "--no-denoise",
        action="store_true",
        help="Disable median denoise before binarization.",
    )
    parser.add_argument(
        "--denoise-size",
        type=int,
        default=3,
        help="Median filter size for denoise; must be a positive odd integer.",
    )
    parser.add_argument(
        "--min-grid-step",
        type=int,
        default=4,
        help="Minimum grid line step to consider during detection.",
    )
    parser.add_argument(
        "--max-grid-step",
        type=int,
        default=24,
        help="Maximum grid line step to consider during detection.",
    )
    parser.add_argument(
        "--expected-columns",
        type=int,
        help="Expected grid width in cells; disables automatic vertical line placement.",
    )
    parser.add_argument(
        "--expected-rows",
        type=int,
        help="Expected grid height in cells; disables automatic horizontal line placement.",
    )
    parser.add_argument(
        "--preview-cell-size",
        type=int,
        default=16,
        help="Preview cell size in pixels.",
    )
    parser.add_argument(
        "--min-symbol-width",
        type=int,
        default=8,
        help="Minimum detected symbol width in extraction mode.",
    )
    parser.add_argument(
        "--min-symbol-height",
        type=int,
        default=8,
        help="Minimum detected symbol height in extraction mode.",
    )
    parser.add_argument(
        "--min-symbol-area",
        type=int,
        default=64,
        help="Minimum black-pixel component area in extraction mode.",
    )
    parser.add_argument(
        "--crop-padding",
        type=int,
        default=2,
        help="Padding in pixels around extracted symbol crops.",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable verbose debug logging and parameter output.",
    )
    return parser


def run(argv: Sequence[str] | None = None) -> int:
    """Run the currently implemented phases of the glyph import CLI."""
    parser = build_parser()
    args = parser.parse_args(argv)
    config = get_default_config()
    logger = setup_logging(config.log_file, debug=args.debug)

    if not 0 <= args.threshold <= 255:
        parser.error("threshold must be in the range 0..255.")

    if args.denoise_size <= 0 or args.denoise_size % 2 == 0:
        parser.error("denoise-size must be a positive odd integer.")

    if args.min_grid_step <= 0:
        parser.error("min-grid-step must be positive.")

    if args.max_grid_step <= 0:
        parser.error("max-grid-step must be positive.")

    if args.min_grid_step > args.max_grid_step:
        parser.error("min-grid-step must be less than or equal to max-grid-step.")

    if args.expected_columns is not None and args.expected_columns <= 0:
        parser.error("expected-columns must be positive.")

    if args.expected_rows is not None and args.expected_rows <= 0:
        parser.error("expected-rows must be positive.")

    if args.preview_cell_size <= 0:
        parser.error("preview-cell-size must be positive.")

    if args.min_symbol_width <= 0:
        parser.error("min-symbol-width must be positive.")

    if args.min_symbol_height <= 0:
        parser.error("min-symbol-height must be positive.")

    if args.min_symbol_area <= 0:
        parser.error("min-symbol-area must be positive.")

    if args.crop_padding < 0:
        parser.error("crop-padding must not be negative.")

    if args.extract and args.batch:
        parser.error("--extract cannot be used together with --batch.")

    if args.extract:
        if args.input is None:
            parser.error("--input is required for the extraction command.")
        if args.char:
            parser.error("--char cannot be used together with --extract.")
    elif args.batch:
        if args.input is not None:
            parser.error("--input cannot be used together with --batch.")
        if args.char:
            parser.error("--char cannot be used together with --batch.")
    else:
        if args.input is None:
            parser.error("--input is required for the import command.")
        if not args.char:
            parser.error("--char is required for the import command.")

    options = ImportPipelineOptions(
        threshold=args.threshold,
        denoise=not args.no_denoise,
        denoise_filter_size=args.denoise_size,
        fill_threshold=args.fill_threshold,
        min_grid_step=args.min_grid_step,
        max_grid_step=args.max_grid_step,
        expected_columns=args.expected_columns,
        expected_rows=args.expected_rows,
        preview_cell_size=args.preview_cell_size,
        debug=args.debug,
    )

    if args.extract:
        extraction_options = ExtractionOptions(
            threshold=args.threshold,
            denoise=not args.no_denoise,
            denoise_filter_size=args.denoise_size,
            min_symbol_width=args.min_symbol_width,
            min_symbol_height=args.min_symbol_height,
            min_symbol_area=args.min_symbol_area,
            crop_padding=args.crop_padding,
            debug=args.debug,
        )
        try:
            extraction_result = run_extraction_pipeline(
                input_path=args.input,
                config=config,
                options=extraction_options,
            )
        except ExtractionPipelineError as exc:
            parser.error(str(exc))

        _emit_extraction_result(
            logger,
            extraction_result,
            project_root=config.project_root,
            extracted_dir=config.extracted_dir,
            debug_dir=config.input_debug_dir,
            manifests_dir=config.manifests_dir,
            log_file=config.log_file,
            debug=args.debug,
        )
        logging.shutdown()
        return 0

    if args.batch:
        try:
            batch_summary = run_batch_import_pipeline(
                config=config,
                options=options,
            )
        except ImportPipelineError as exc:
            parser.error(str(exc))

        _emit_batch_summary(logger, batch_summary, debug=args.debug)
        logging.shutdown()
        return 1 if batch_summary.failure_count else 0

    try:
        pipeline_result = run_import_pipeline(
            input_path=args.input,
            char=args.char,
            config=config,
            options=options,
        )
    except ImportPipelineError as exc:
        parser.error(str(exc))

    _emit_pipeline_result(logger, pipeline_result, project_root=config.project_root, json_dir=config.json_dir, previews_dir=config.previews_dir, log_file=config.log_file, debug=args.debug)
    logging.shutdown()

    return 0


def _emit_pipeline_result(
    logger: logging.Logger,
    pipeline_result: ImportPipelineResult,
    *,
    project_root: Path,
    json_dir: Path,
    previews_dir: Path,
    log_file: Path,
    debug: bool,
) -> None:
    """Print the detailed status for a single imported file."""
    input_path = pipeline_result.loaded_image.path
    emit_status(logger, "Project root: %s", project_root)
    emit_status(logger, "Input image: %s", input_path)
    emit_status(logger, "Image format: %s", pipeline_result.loaded_image.image_format)
    emit_status(logger, "Character: %s", pipeline_result.glyph_result.char)
    emit_status(logger, "Output JSON dir: %s", json_dir)
    emit_status(logger, "Preview dir: %s", previews_dir)
    emit_status(logger, "Log file: %s", log_file)
    emit_status(logger, "Grayscale debug image: %s", pipeline_result.grayscale_debug_path)
    emit_status(logger, "Denoised debug image: %s", pipeline_result.denoised_debug_path)
    emit_status(logger, "Binary debug image: %s", pipeline_result.binary_debug_path)
    emit_status(
        logger,
        "Grid bounds: left=%s top=%s right=%s bottom=%s",
        pipeline_result.grid_result.left,
        pipeline_result.grid_result.top,
        pipeline_result.grid_result.right,
        pipeline_result.grid_result.bottom,
    )
    emit_status(
        logger,
        "Grid size: columns=%s rows=%s",
        pipeline_result.grid_result.column_count,
        pipeline_result.grid_result.row_count,
    )
    emit_status(logger, "Grid debug image: %s", pipeline_result.grid_debug_path)
    emit_status(logger, "Extracted cells: %s", len(pipeline_result.cell_result.cells))
    if pipeline_result.cell_result.cells:
        first_cell = pipeline_result.cell_result.cells[0]
        emit_status(
            logger,
            "First cell: row=%s column=%s size=%sx%s",
            first_cell.row_index,
            first_cell.column_index,
            first_cell.image.width,
            first_cell.image.height,
        )
    emit_status(logger, "Fill threshold: %s", pipeline_result.classification_result.fill_threshold)
    emit_status(
        logger,
        "Classification matrix size: columns=%s rows=%s",
        pipeline_result.classification_result.column_count,
        pipeline_result.classification_result.row_count,
    )
    if pipeline_result.classification_result.matrix:
        emit_status(logger, "First matrix row: %s", pipeline_result.classification_result.matrix[0])
    emit_status(
        logger,
        "Trimmed glyph matrix size: width=%s height=%s",
        pipeline_result.matrix_result.width,
        pipeline_result.matrix_result.height,
    )
    if pipeline_result.matrix_result.matrix:
        emit_status(logger, "Trimmed first row: %s", pipeline_result.matrix_result.matrix[0])
    emit_status(logger, "Glyph char: %s", pipeline_result.glyph_result.char)
    emit_status(
        logger,
        "Glyph size: width=%s height=%s",
        pipeline_result.glyph_result.width,
        pipeline_result.glyph_result.height,
    )
    emit_status(logger, "Exported JSON: %s", pipeline_result.exported_glyph.output_path)
    emit_status(logger, "Preview image: %s", pipeline_result.preview_result.output_path)
    emit_debug(logger, debug, "Debug mode: enabled")
    emit_debug(logger, debug, "Preprocess threshold: %s", pipeline_result.options.threshold)
    emit_debug(logger, debug, "Denoise enabled: %s", pipeline_result.options.denoise)
    emit_debug(
        logger,
        debug,
        "Denoise filter size: %s",
        pipeline_result.options.denoise_filter_size,
    )
    emit_debug(
        logger,
        debug,
        "Grid step range: %s..%s",
        pipeline_result.options.min_grid_step,
        pipeline_result.options.max_grid_step,
    )
    emit_debug(
        logger,
        debug,
        "Expected grid size: columns=%s rows=%s",
        pipeline_result.options.expected_columns,
        pipeline_result.options.expected_rows,
    )
    emit_debug(
        logger,
        debug,
        "Preview cell size: %s",
        pipeline_result.options.preview_cell_size,
    )
    emit_status(logger, "Import pipeline completed.")


def _emit_batch_summary(
    logger: logging.Logger,
    batch_summary: BatchImportSummary,
    *,
    debug: bool,
) -> None:
    """Print batch-processing results and summary."""
    emit_status(logger, "Batch input dir: %s", batch_summary.input_dir)
    emit_status(logger, "Batch processed files: %s", batch_summary.processed_count)
    emit_status(logger, "Batch successful files: %s", batch_summary.success_count)
    emit_status(logger, "Batch failed files: %s", batch_summary.failure_count)
    for item in batch_summary.items:
        if item.success:
            emit_status(
                logger,
                "Batch item OK: char=%s input=%s json=%s preview=%s",
                item.char,
                item.input_path,
                item.pipeline_result.exported_glyph.output_path if item.pipeline_result else "",
                item.pipeline_result.preview_result.output_path if item.pipeline_result else "",
            )
        else:
            emit_status(
                logger,
                "Batch item ERROR: char=%s input=%s error=%s",
                item.char,
                item.input_path,
                item.error_message,
            )
    emit_debug(logger, debug, "Debug mode: enabled")
    emit_status(logger, "Batch import completed.")


def _emit_extraction_result(
    logger: logging.Logger,
    extraction_result: ExtractionResult,
    *,
    project_root: Path,
    extracted_dir: Path,
    debug_dir: Path,
    manifests_dir: Path,
    log_file: Path,
    debug: bool,
) -> None:
    """Print extraction-mode status and artifact paths."""
    emit_status(logger, "Project root: %s", project_root)
    emit_status(logger, "Extraction input image: %s", extraction_result.loaded_image.path)
    emit_status(logger, "Image format: %s", extraction_result.loaded_image.image_format)
    emit_status(logger, "Extracted symbols dir: %s", extracted_dir)
    emit_status(logger, "Extraction debug dir: %s", debug_dir)
    emit_status(logger, "Manifest dir: %s", manifests_dir)
    emit_status(logger, "Log file: %s", log_file)
    emit_status(logger, "Extraction binary debug image: %s", extraction_result.binary_debug_path)
    emit_status(logger, "Extraction overlay debug image: %s", extraction_result.overlay_debug_path)
    emit_status(logger, "Extraction manifest: %s", extraction_result.manifest_path)
    emit_status(logger, "Extracted symbol count: %s", len(extraction_result.symbols))
    for symbol in extraction_result.symbols:
        emit_status(
            logger,
            "Extracted symbol: index=%s bounds=(%s,%s,%s,%s) size=%sx%s path=%s",
            symbol.index,
            symbol.bounds.left,
            symbol.bounds.top,
            symbol.bounds.right,
            symbol.bounds.bottom,
            symbol.width,
            symbol.height,
            symbol.output_path,
        )
    emit_debug(logger, debug, "Debug mode: enabled")
    emit_debug(logger, debug, "Extraction threshold: %s", extraction_result.options.threshold)
    emit_debug(logger, debug, "Denoise enabled: %s", extraction_result.options.denoise)
    emit_debug(
        logger,
        debug,
        "Minimum symbol size: %sx%s",
        extraction_result.options.min_symbol_width,
        extraction_result.options.min_symbol_height,
    )
    emit_debug(logger, debug, "Minimum symbol area: %s", extraction_result.options.min_symbol_area)
    emit_debug(logger, debug, "Crop padding: %s", extraction_result.options.crop_padding)
    emit_status(logger, "Extraction completed.")


def main() -> None:
    """CLI wrapper used by `python -m src.main` and script entrypoints."""
    raise SystemExit(run())


if __name__ == "__main__":
    main()
