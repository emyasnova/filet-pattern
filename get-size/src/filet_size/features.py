"""Feature extraction API for filet chart images and datasets."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .image_processing import (
    binarize_image,
    calculate_margins,
    calculate_projection_features,
    calculate_quality_features,
    estimate_grid_spacing,
    find_content_bbox,
    load_image,
    to_grayscale,
    _projection_period,
)

METADATA_COLUMNS = [
    "image_path", "source_id", "source_type", "split", "width_cells", "height_cells"
]

FEATURE_COLUMNS = [
    "img_width_px", "img_height_px", "img_area_px", "img_aspect_ratio",
    "dark_pixel_ratio", "foreground_pixel_count",
    "content_bbox_x_min", "content_bbox_y_min", "content_bbox_x_max",
    "content_bbox_y_max", "content_bbox_width_px", "content_bbox_height_px",
    "content_bbox_area_px", "content_bbox_aspect_ratio",
    "margin_left_px", "margin_right_px", "margin_top_px", "margin_bottom_px",
    "margin_left_ratio", "margin_right_ratio", "margin_top_ratio", "margin_bottom_ratio",
    "estimated_cell_width_px", "estimated_cell_height_px", "estimated_width_cells",
    "estimated_height_cells", "vertical_grid_lines_count", "horizontal_grid_lines_count",
    "vertical_spacing_mean_px", "vertical_spacing_median_px", "vertical_spacing_std_px",
    "vertical_spacing_min_px", "vertical_spacing_max_px", "horizontal_spacing_mean_px",
    "horizontal_spacing_median_px", "horizontal_spacing_std_px", "horizontal_spacing_min_px",
    "horizontal_spacing_max_px", "vertical_projection_peaks_count",
    "horizontal_projection_peaks_count", "vertical_grid_confidence",
    "horizontal_grid_confidence", "grid_confidence_mean", "brightness_mean",
    "brightness_std", "contrast", "blur_score", "edge_density",
]


def _safe_ratio(numerator: Any, denominator: Any) -> float:
    if pd.isna(numerator) or pd.isna(denominator) or float(denominator) == 0:
        return np.nan
    return float(numerator) / float(denominator)


def extract_features_from_image(image_path: Path) -> dict[str, float]:
    """Extract all numeric model features from one chart image."""
    image = load_image(Path(image_path))
    gray = to_grayscale(image)
    binary = binarize_image(gray)
    height, width = gray.shape
    bbox = find_content_bbox(binary)
    grid = estimate_grid_spacing(binary, gray)

    features: dict[str, float] = {
        "img_width_px": width,
        "img_height_px": height,
        "img_area_px": width * height,
        "img_aspect_ratio": width / height,
        "dark_pixel_ratio": float(np.mean(binary)),
        "foreground_pixel_count": int(np.count_nonzero(binary)),
    }
    features.update(bbox)
    features.update(calculate_margins(gray.shape, bbox))
    features.update(grid)
    estimate_width_px = bbox["content_bbox_width_px"]
    estimate_height_px = bbox["content_bbox_height_px"]
    # When the detected grid step is large, full-width dark framing can make
    # the foreground bbox span the entire screenshot.  Estimate the actual
    # chart rectangle from bright row/column projections instead.
    if (
        grid["estimated_cell_width_px"] >= 8
        and grid["estimated_cell_height_px"] >= 8
        and grid["vertical_grid_confidence"] >= 0.75
        and grid["horizontal_grid_confidence"] >= 0.75
    ):
        bright_rows = np.flatnonzero(np.mean(gray, axis=1) > 100)
        bright_cols = np.flatnonzero(np.mean(gray, axis=0) > 100)
        if bright_rows.size:
            estimate_height_px = int(bright_rows[-1] - bright_rows[0] + 1)
        if bright_cols.size:
            estimate_width_px = int(bright_cols[-1] - bright_cols[0] + 1)
    # A strong grayscale period can reveal a chart grid even when the binary
    # projection is dominated by the motif.  Use complete grid intervals only;
    # this also removes legends/captions outside the chart rectangle.
    darkness = 255.0 - gray.astype(np.float64)
    period_width, period_width_conf = _projection_period(darkness.mean(axis=0))
    period_height, period_height_conf = _projection_period(darkness.mean(axis=1))

    # Autocorrelation can lock onto a strong harmonic (for example every tenth
    # grid line) even though the finer grid step was already found from the
    # grayscale line pattern.  Prefer that established fundamental when the
    # new period is an integral multiple of it.
    def fundamental_period(period: float, cell_size: float) -> float:
        if not (np.isfinite(period) and np.isfinite(cell_size) and cell_size > 0):
            return period
        multiple = round(period / cell_size)
        if multiple >= 2 and abs(period / cell_size - multiple) <= 0.15:
            return float(cell_size)
        return period

    period_width = fundamental_period(
        period_width, grid["estimated_cell_width_px"]
    )
    period_height = fundamental_period(
        period_height, grid["estimated_cell_height_px"]
    )
    if (
        period_width_conf >= 0.60 and period_height_conf >= 0.60
        and period_width >= 3.5 and period_height >= 3.5
    ):
        grid["estimated_cell_width_px"] = period_width
        grid["estimated_cell_height_px"] = period_height
        # Locate the outer grid border among the strongest projection lines.
        # Requiring one candidate near each edge excludes captions underneath.
        def grid_span(projection: np.ndarray, period: float) -> float | None:
            full_intervals = int(np.floor(projection.size / period))
            # Once a strong periodic signal agrees on both axes, the chart
            # normally covers nearly the whole scan. Individual grid lines can
            # be hidden by the motif, so an uninterrupted line fragment is not
            # a reliable measure of the outer border.
            if full_intervals >= 20:
                return full_intervals * period
            rounded_period = int(round(period))
            if abs(period - rounded_period) <= 0.15 and rounded_period >= 2:
                phase = max(
                    range(rounded_period),
                    key=lambda offset: float(np.mean(projection[offset::rounded_period])),
                )
                positions = np.arange(phase, projection.size, rounded_period)
                valid = projection[positions] >= 0.35 * float(np.max(projection))
                valid_groups = np.split(
                    positions[valid], np.flatnonzero(np.diff(positions[valid]) > rounded_period) + 1
                )
                longest = max(valid_groups, key=lambda group: group.size, default=np.array([]))
                if longest.size >= 4:
                    return float(longest[-1] - longest[0])
            cutoff = float(np.percentile(projection, 99))
            candidates = np.flatnonzero(projection >= cutoff)
            edge = max(2, int(projection.size * 0.12))
            left = candidates[candidates <= edge]
            right = candidates[candidates >= projection.size - 1 - edge]
            if left.size and right.size:
                span = float(right[-1] - left[0])
                intervals = round(span / period)
                if intervals >= 3:
                    return intervals * period
            return None

        width_span = grid_span(darkness.mean(axis=0), period_width)
        height_span = grid_span(darkness.mean(axis=1), period_height)
        if width_span is not None and height_span is not None:
            estimate_width_px = width_span
            estimate_height_px = height_span
    # ``features`` was populated before the period refinement above.
    # Keep the exported cell-size fields consistent with the denominators used
    # for the estimated cell counts.
    features["estimated_cell_width_px"] = grid["estimated_cell_width_px"]
    features["estimated_cell_height_px"] = grid["estimated_cell_height_px"]
    features["estimated_width_cells"] = _safe_ratio(
        estimate_width_px, grid["estimated_cell_width_px"]
    )
    features["estimated_height_cells"] = _safe_ratio(
        estimate_height_px, grid["estimated_cell_height_px"]
    )
    features.update(calculate_projection_features(binary))
    features.update(calculate_quality_features(gray, binary))
    return {name: features[name] for name in FEATURE_COLUMNS}


def _resolve_image_path(value: Any, images_root: Path | None) -> Path:
    if pd.isna(value) or not str(value).strip():
        raise ValueError("image_path is empty")
    path = Path(str(value))
    if not path.is_absolute() and images_root is not None:
        path = Path(images_root) / path
    return path


def extract_features_for_dataframe(
    df: pd.DataFrame, images_root: Path | None = None
) -> pd.DataFrame:
    """Extract features for every dataframe row without aborting on bad images."""
    if "image_path" not in df.columns:
        raise ValueError("Input dataframe must contain the 'image_path' column")
    metadata = [name for name in METADATA_COLUMNS if name in df.columns]
    rows: list[dict[str, Any]] = []
    for _, source_row in df.iterrows():
        row = {name: source_row[name] for name in metadata}
        try:
            image_path = _resolve_image_path(source_row["image_path"], images_root)
            row.update(extract_features_from_image(image_path))
            row["feature_extraction_error"] = ""
        except Exception as exc:  # A single corrupt file must not abort a dataset run.
            row.update({name: np.nan for name in FEATURE_COLUMNS})
            row["feature_extraction_error"] = f"{type(exc).__name__}: {exc}"
        rows.append(row)
    columns = metadata + FEATURE_COLUMNS + ["feature_extraction_error"]
    return pd.DataFrame(rows, columns=columns)
