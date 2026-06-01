"""Domain models for the glyph import tool."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from PIL.Image import Image as PILImage


class ImageFormat(StrEnum):
    """Supported source image formats."""

    JPG = "jpg"
    PNG = "png"


@dataclass(frozen=True, slots=True)
class LoadedImage:
    """Raw source image loaded from disk."""

    path: Path
    image_format: ImageFormat
    content: bytes


@dataclass(frozen=True, slots=True)
class PreprocessedImage:
    """Intermediate image artifacts produced during preprocessing."""

    source_path: Path
    grayscale_image: PILImage
    denoised_image: PILImage
    binary_image: PILImage


@dataclass(frozen=True, slots=True)
class GridDetectionResult:
    """Detected grid geometry on a binary image."""

    source_path: Path
    left: int
    top: int
    right: int
    bottom: int
    vertical_lines: tuple[int, ...]
    horizontal_lines: tuple[int, ...]
    column_count: int
    row_count: int


@dataclass(frozen=True, slots=True)
class CellBounds:
    """Pixel bounds for a single extracted cell."""

    left: int
    top: int
    right: int
    bottom: int


@dataclass(frozen=True, slots=True)
class ExtractedCell:
    """Single cell image extracted from the detected grid."""

    row_index: int
    column_index: int
    bounds: CellBounds
    image: PILImage


@dataclass(frozen=True, slots=True)
class CellExtractionResult:
    """Result of splitting the grid into individual cells."""

    source_path: Path
    row_count: int
    column_count: int
    cells: tuple[ExtractedCell, ...]


@dataclass(frozen=True, slots=True)
class ClassifiedCell:
    """Single extracted cell with a binary filled/empty label."""

    row_index: int
    column_index: int
    fill_ratio: float
    value: int


@dataclass(frozen=True, slots=True)
class CellClassificationResult:
    """Classification output for all extracted cells and the raw 0/1 matrix."""

    source_path: Path
    row_count: int
    column_count: int
    fill_threshold: float
    cells: tuple[ClassifiedCell, ...]
    matrix: tuple[tuple[int, ...], ...]


@dataclass(frozen=True, slots=True)
class MatrixBuildResult:
    """Trimmed glyph matrix with derived dimensions."""

    source_path: Path
    matrix: tuple[tuple[int, ...], ...]
    width: int
    height: int


@dataclass(frozen=True, slots=True)
class GlyphDraft:
    """Draft glyph object ready for export in later phases."""

    char: str
    width: int
    height: int
    cells: tuple[tuple[int, ...], ...]


@dataclass(frozen=True, slots=True)
class ExportedGlyph:
    """Glyph draft serialized to a JSON file on disk."""

    char: str
    output_path: Path


@dataclass(frozen=True, slots=True)
class ExportedPreview:
    """Glyph preview image rendered to disk."""

    char: str
    output_path: Path
    image_width: int
    image_height: int


@dataclass(frozen=True, slots=True)
class ImportPipelineOptions:
    """Tunable parameters for the end-to-end glyph import pipeline."""

    threshold: int = 128
    denoise: bool = True
    denoise_filter_size: int = 3
    fill_threshold: float = 0.35
    min_grid_step: int = 4
    max_grid_step: int = 24
    expected_columns: int | None = None
    expected_rows: int | None = None
    preview_cell_size: int = 16
    debug: bool = False


@dataclass(frozen=True, slots=True)
class ImportPipelineResult:
    """Combined result of the full glyph import pipeline."""

    options: ImportPipelineOptions
    loaded_image: LoadedImage
    preprocessed_image: PreprocessedImage
    grayscale_debug_path: Path
    denoised_debug_path: Path
    binary_debug_path: Path
    grid_result: GridDetectionResult
    grid_debug_path: Path
    cell_result: CellExtractionResult
    classification_result: CellClassificationResult
    matrix_result: MatrixBuildResult
    glyph_result: GlyphDraft
    exported_glyph: ExportedGlyph
    preview_result: ExportedPreview


@dataclass(frozen=True, slots=True)
class BatchImportItemResult:
    """Result of processing one file in batch mode."""

    input_path: Path
    char: str
    success: bool
    pipeline_result: ImportPipelineResult | None = None
    error_message: str | None = None


@dataclass(frozen=True, slots=True)
class BatchImportSummary:
    """Summary of processing all supported files from the batch input directory."""

    input_dir: Path
    processed_count: int
    success_count: int
    failure_count: int
    items: tuple[BatchImportItemResult, ...]


@dataclass(frozen=True, slots=True)
class SymbolBounds:
    """Pixel bounds for one detected symbol region."""

    left: int
    top: int
    right: int
    bottom: int


@dataclass(frozen=True, slots=True)
class DetectedSymbol:
    """One symbol candidate found on a multi-symbol source image."""

    index: int
    bounds: SymbolBounds
    output_path: Path
    width: int
    height: int


@dataclass(frozen=True, slots=True)
class ExtractionOptions:
    """Tunable parameters for extracting individual symbols from a source image."""

    threshold: int = 128
    denoise: bool = True
    denoise_filter_size: int = 3
    min_symbol_width: int = 8
    min_symbol_height: int = 8
    min_symbol_area: int = 64
    crop_padding: int = 2
    debug: bool = False


@dataclass(frozen=True, slots=True)
class ExtractionResult:
    """Result of extracting individual symbol images and metadata."""

    options: ExtractionOptions
    loaded_image: LoadedImage
    preprocessed_image: PreprocessedImage
    symbols: tuple[DetectedSymbol, ...]
    binary_debug_path: Path
    overlay_debug_path: Path
    manifest_path: Path
