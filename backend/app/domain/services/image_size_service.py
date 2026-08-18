"""Estimate filet chart dimensions from uploaded image bytes."""

from __future__ import annotations

import math
from pathlib import Path

import cv2
import numpy as np

from app.domain.models.image_size import ImageGridSize
from app.domain.services.image_processing import (
    _projection_period,
    binarize_image,
    estimate_grid_spacing,
    find_content_bbox,
    to_grayscale,
)

SUPPORTED_IMAGE_SUFFIXES = frozenset({".png", ".jpg", ".jpeg"})
MAX_IMAGE_PIXELS = 25_000_000


class ImageSizeDetectionError(ValueError):
    """Raised when an uploaded image cannot produce valid grid dimensions."""


def _decode_image(image_bytes: bytes, filename: str) -> np.ndarray:
    """Decode a supported PNG or JPEG upload into an OpenCV image."""
    suffix = Path(filename).suffix.lower()
    if suffix not in SUPPORTED_IMAGE_SUFFIXES:
        raise ImageSizeDetectionError("Supported image formats are PNG and JPEG")
    if not image_bytes:
        raise ImageSizeDetectionError("Uploaded image is empty")

    encoded = np.frombuffer(image_bytes, dtype=np.uint8)
    try:
        image = cv2.imdecode(encoded, cv2.IMREAD_UNCHANGED)
    except cv2.error as exc:
        raise ImageSizeDetectionError("Could not decode the uploaded image") from exc
    if image is None or image.size == 0:
        raise ImageSizeDetectionError("Could not decode the uploaded image")
    if image.shape[0] * image.shape[1] > MAX_IMAGE_PIXELS:
        raise ImageSizeDetectionError("Image exceeds the 25 megapixel limit")
    return image


def _safe_ratio(numerator: float, denominator: float) -> float:
    """Divide finite values, returning NaN when no estimate is possible."""
    if not (np.isfinite(numerator) and np.isfinite(denominator)) or denominator == 0:
        return float("nan")
    return float(numerator) / float(denominator)


def _fundamental_period(period: float, cell_size: float) -> float:
    """Prefer an already detected fundamental over its integral harmonic."""
    if not (np.isfinite(period) and np.isfinite(cell_size) and cell_size > 0):
        return period
    multiple = round(period / cell_size)
    if multiple >= 2 and abs(period / cell_size - multiple) <= 0.15:
        return float(cell_size)
    return period


def _grid_span(projection: np.ndarray, period: float) -> float | None:
    """Estimate the chart span from periodic projection lines."""
    full_intervals = int(np.floor(projection.size / period))
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
        valid_positions = positions[valid]
        valid_groups = np.split(
            valid_positions,
            np.flatnonzero(np.diff(valid_positions) > rounded_period) + 1,
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


def _estimate_cell_counts(image: np.ndarray) -> tuple[float, float]:
    """Run the transferred feature-extraction logic needed for cell counts."""
    gray = to_grayscale(image)
    binary = binarize_image(gray)
    bbox = find_content_bbox(binary)
    grid = estimate_grid_spacing(binary, gray)
    estimate_width_px = bbox["content_bbox_width_px"]
    estimate_height_px = bbox["content_bbox_height_px"]

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

    darkness = 255.0 - gray.astype(np.float64)
    period_width, period_width_conf = _projection_period(darkness.mean(axis=0))
    period_height, period_height_conf = _projection_period(darkness.mean(axis=1))
    period_width = _fundamental_period(period_width, grid["estimated_cell_width_px"])
    period_height = _fundamental_period(period_height, grid["estimated_cell_height_px"])

    if (
        period_width_conf >= 0.60
        and period_height_conf >= 0.60
        and period_width >= 3.5
        and period_height >= 3.5
    ):
        grid["estimated_cell_width_px"] = period_width
        grid["estimated_cell_height_px"] = period_height
        width_span = _grid_span(darkness.mean(axis=0), period_width)
        height_span = _grid_span(darkness.mean(axis=1), period_height)
        if width_span is not None and height_span is not None:
            estimate_width_px = width_span
            estimate_height_px = height_span

    return (
        _safe_ratio(estimate_width_px, grid["estimated_cell_width_px"]),
        _safe_ratio(estimate_height_px, grid["estimated_cell_height_px"]),
    )


def _round_half_up(value: float) -> int:
    """Round a positive estimate to the nearest integer, with halves upward."""
    return math.floor(value + 0.5)


def get_image_grid_size(image_bytes: bytes, filename: str) -> ImageGridSize:
    """Return an uploaded chart's width and height measured in cells."""
    image = _decode_image(image_bytes, filename)
    width_estimate, height_estimate = _estimate_cell_counts(image)
    if not (
        np.isfinite(width_estimate)
        and np.isfinite(height_estimate)
        and width_estimate > 0
        and height_estimate > 0
    ):
        raise ImageSizeDetectionError("Could not detect a grid in the uploaded image")

    width = _round_half_up(width_estimate)
    height = _round_half_up(height_estimate)
    if width <= 0 or height <= 0:
        raise ImageSizeDetectionError("Could not detect a grid in the uploaded image")
    return ImageGridSize(width=width, height=height)
