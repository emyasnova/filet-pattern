"""Low-level image processing helpers for filet chart images."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Sequence

import cv2
import numpy as np


def load_image(image_path: Path) -> np.ndarray:
    """Load a PNG or JPEG image and return it as an OpenCV ndarray."""
    path = Path(image_path)
    if not path.exists():
        raise FileNotFoundError(f"Image does not exist: {path}")
    if not path.is_file():
        raise ValueError(f"Image path is not a file: {path}")
    if path.suffix.lower() not in {".png", ".jpg", ".jpeg"}:
        raise ValueError(f"Unsupported image format '{path.suffix}': {path}")

    # imdecode also handles non-ASCII paths reliably on all OpenCV platforms.
    try:
        data = np.fromfile(path, dtype=np.uint8)
        image = cv2.imdecode(data, cv2.IMREAD_UNCHANGED)
    except (OSError, cv2.error) as exc:
        raise ValueError(f"Could not read image '{path}': {exc}") from exc
    if image is None or image.size == 0:
        raise ValueError(f"Could not decode image: {path}")
    return image


def to_grayscale(image: np.ndarray) -> np.ndarray:
    """Convert a grayscale, BGR, or BGRA image to uint8 grayscale."""
    if not isinstance(image, np.ndarray) or image.size == 0:
        raise ValueError("Image must be a non-empty numpy array")
    if image.ndim == 2:
        gray = image
    elif image.ndim == 3 and image.shape[2] == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    elif image.ndim == 3 and image.shape[2] == 4:
        # Composite transparent pixels onto white; otherwise transparent PNG
        # pixels can accidentally become foreground.
        bgr = image[:, :, :3].astype(np.float32)
        alpha = image[:, :, 3:4].astype(np.float32) / 255.0
        composited = bgr * alpha + 255.0 * (1.0 - alpha)
        gray = cv2.cvtColor(composited.astype(np.uint8), cv2.COLOR_BGR2GRAY)
    else:
        raise ValueError(f"Unsupported image array shape: {image.shape}")
    if gray.dtype != np.uint8:
        gray = cv2.normalize(gray, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
    return gray


def binarize_image(gray: np.ndarray) -> np.ndarray:
    """Return a boolean mask where dark chart pixels are foreground."""
    if gray.ndim != 2 or gray.size == 0:
        raise ValueError("Grayscale image must be a non-empty 2D array")
    blurred = cv2.GaussianBlur(gray, (3, 3), 0)
    _, mask = cv2.threshold(
        blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
    )
    return mask.astype(bool)


def find_content_bbox(binary: np.ndarray) -> dict[str, float]:
    """Find the inclusive bounding box of all foreground pixels."""
    names = (
        "content_bbox_x_min", "content_bbox_y_min", "content_bbox_x_max",
        "content_bbox_y_max", "content_bbox_width_px", "content_bbox_height_px",
        "content_bbox_area_px", "content_bbox_aspect_ratio",
    )
    points = np.argwhere(binary.astype(bool))
    if points.size == 0:
        return {name: np.nan for name in names}
    y_min, x_min = points.min(axis=0)
    y_max, x_max = points.max(axis=0)
    width = int(x_max - x_min + 1)
    height = int(y_max - y_min + 1)
    return {
        "content_bbox_x_min": int(x_min),
        "content_bbox_y_min": int(y_min),
        "content_bbox_x_max": int(x_max),
        "content_bbox_y_max": int(y_max),
        "content_bbox_width_px": width,
        "content_bbox_height_px": height,
        "content_bbox_area_px": width * height,
        "content_bbox_aspect_ratio": width / height,
    }


def calculate_margins(
    image_shape: Sequence[int], bbox: dict[str, float]
) -> dict[str, float]:
    """Calculate pixel and relative margins around an inclusive bbox."""
    height, width = int(image_shape[0]), int(image_shape[1])
    if np.isnan(bbox["content_bbox_x_min"]):
        return {name: np.nan for name in (
            "margin_left_px", "margin_right_px", "margin_top_px", "margin_bottom_px",
            "margin_left_ratio", "margin_right_ratio", "margin_top_ratio",
            "margin_bottom_ratio",
        )}
    left = int(bbox["content_bbox_x_min"])
    right = width - 1 - int(bbox["content_bbox_x_max"])
    top = int(bbox["content_bbox_y_min"])
    bottom = height - 1 - int(bbox["content_bbox_y_max"])
    return {
        "margin_left_px": left, "margin_right_px": right,
        "margin_top_px": top, "margin_bottom_px": bottom,
        "margin_left_ratio": left / width, "margin_right_ratio": right / width,
        "margin_top_ratio": top / height, "margin_bottom_ratio": bottom / height,
    }


def _projection_peaks(projection: np.ndarray, perpendicular_size: int) -> np.ndarray:
    """Locate centers of high, possibly multi-pixel projection peaks."""
    values = projection.astype(np.float64)
    if values.size < 3 or float(values.max()) <= 0:
        return np.array([], dtype=int)
    kernel_size = max(1, min(5, values.size // 100 + 1))
    smooth = np.convolve(values, np.ones(kernel_size) / kernel_size, mode="same")
    baseline = float(np.median(smooth))
    threshold = max(
        baseline + 0.35 * (float(smooth.max()) - baseline),
        perpendicular_size * 0.18,
    )
    indices = np.flatnonzero(smooth >= threshold)
    if indices.size == 0:
        return np.array([], dtype=int)
    groups = np.split(indices, np.flatnonzero(np.diff(indices) > 1) + 1)
    return np.array(
        [int(round(np.average(g, weights=smooth[g]))) for g in groups if g.size],
        dtype=int,
    )


def calculate_projection_features(binary: np.ndarray) -> dict[str, int]:
    """Count likely vertical and horizontal grid-line projection peaks."""
    height, width = binary.shape
    vertical = _projection_peaks(binary.sum(axis=0), height)
    horizontal = _projection_peaks(binary.sum(axis=1), width)
    return {
        "vertical_projection_peaks_count": int(vertical.size),
        "horizontal_projection_peaks_count": int(horizontal.size),
    }


def _spacing_features(peaks: np.ndarray, prefix: str, axis_size: int) -> dict[str, float]:
    names = ("mean", "median", "std", "min", "max")
    result: dict[str, Any] = {f"{prefix}_grid_lines_count": int(peaks.size)}
    distances = np.diff(peaks).astype(float)
    distances = distances[(distances >= 2) & (distances <= axis_size / 2)]
    if distances.size < 2:
        result.update({f"{prefix}_spacing_{name}_px": np.nan for name in names})
        result[f"{prefix}_grid_confidence"] = 0.0
        return result

    # Remove gross outliers, while retaining small scale/rounding variations.
    median = float(np.median(distances))
    mad = float(np.median(np.abs(distances - median)))
    tolerance = max(2.0, 3.0 * mad)
    regular = distances[np.abs(distances - median) <= tolerance]
    if regular.size < 2:
        regular = distances
    spacing_median = float(np.median(regular))
    spacing_std = float(np.std(regular))
    result.update({
        f"{prefix}_spacing_mean_px": float(np.mean(regular)),
        f"{prefix}_spacing_median_px": spacing_median,
        f"{prefix}_spacing_std_px": spacing_std,
        f"{prefix}_spacing_min_px": float(np.min(regular)),
        f"{prefix}_spacing_max_px": float(np.max(regular)),
        f"{prefix}_grid_confidence": 1.0 / (1.0 + spacing_std / spacing_median),
    })
    return result


def _projection_period(
    projection: np.ndarray, max_period: int = 64
) -> tuple[float, float]:
    """Estimate a fine grid period from a detrended 1D projection.

    Thin grid lines may be much weaker than the chart motif and therefore fail
    the absolute peak threshold used by ``_projection_peaks``.  Autocorrelation
    detects their repetition even when individual lines are faint.  A period is
    returned only for a strong local maximum, so motif spacing is not treated as
    a grid when the periodic evidence is ambiguous.
    """
    values = projection.astype(np.float64)
    if values.size < 12 or float(np.ptp(values)) == 0:
        return np.nan, 0.0

    window_size = min(101, values.size // 2 * 2 - 1)
    if window_size < 3:
        return np.nan, 0.0
    trend = np.convolve(
        values, np.ones(window_size, dtype=float) / window_size, mode="same"
    )
    signal = values - trend
    signal -= float(np.mean(signal))
    energy = float(np.dot(signal, signal))
    if energy <= 0:
        return np.nan, 0.0

    limit = min(max_period, values.size // 4)
    correlations = np.array([
        float(np.dot(signal[:-lag], signal[lag:]) / energy)
        for lag in range(1, limit + 1)
    ])
    candidates = [
        lag for lag in range(2, limit)
        if correlations[lag - 1] > correlations[lag - 2]
        and correlations[lag - 1] >= correlations[lag]
    ]
    if not candidates:
        return np.nan, 0.0

    # Prefer the smallest fundamental period with a clearly repeated signal.
    strong = [lag for lag in candidates if correlations[lag - 1] >= 0.55]
    if not strong:
        return np.nan, 0.0
    period = float(strong[0])
    return period, float(correlations[int(period) - 1])


def _projection_period_candidates(projection: np.ndarray) -> list[tuple[float, float]]:
    """Return weaker local periods for cross-axis validation.

    A real grid can be weak in each individual projection but repeat at nearly
    the same scale on both axes. Motif-only peaks rarely agree that closely.
    """
    values = projection.astype(np.float64)
    if values.size < 12 or float(np.ptp(values)) == 0:
        return []
    window_size = min(101, values.size // 2 * 2 - 1)
    trend = np.convolve(values, np.ones(window_size) / window_size, mode="same")
    signal = values - trend
    signal -= float(np.mean(signal))
    energy = float(np.dot(signal, signal))
    if energy <= 0:
        return []
    limit = min(64, values.size // 4)
    correlations = np.array([
        float(np.dot(signal[:-lag], signal[lag:]) / energy)
        for lag in range(1, limit + 1)
    ])
    return [
        (float(lag), float(correlations[lag - 1]))
        for lag in range(4, limit)
        if correlations[lag - 1] > correlations[lag - 2]
        and correlations[lag - 1] >= correlations[lag]
        and correlations[lag - 1] >= 0.0
    ]


def _joint_projection_periods(gray: np.ndarray) -> tuple[float, float, float]:
    """Select an X/Y period pair supported by both grayscale projections."""
    darkness = 255.0 - gray.astype(np.float64)
    vertical = _projection_period_candidates(darkness.mean(axis=0))
    horizontal = _projection_period_candidates(darkness.mean(axis=1))
    pairs = []
    for v_period, v_conf in vertical:
        for h_period, h_conf in horizontal:
            ratio = max(v_period, h_period) / min(v_period, h_period)
            if ratio <= 1.20:
                pairs.append((min(v_conf, h_conf), v_period, h_period))
    if not pairs:
        return np.nan, np.nan, 0.0
    confidence, v_period, h_period = max(pairs)
    # Heavy guide lines (commonly every fifth cell) may be more prominent than
    # the actual grid. Reduce such a harmonic only when a smaller period is
    # independently present on both axes with a meaningful fraction of the
    # strongest pair's evidence.
    fundamentals = []
    for candidate_conf, candidate_v, candidate_h in pairs:
        v_multiple = round(v_period / candidate_v)
        h_multiple = round(h_period / candidate_h)
        if (
            v_multiple == h_multiple and v_multiple >= 2
            and abs(v_period / candidate_v - v_multiple) <= 0.15
            and abs(h_period / candidate_h - h_multiple) <= 0.15
            and candidate_conf >= max(0.05, confidence * 0.35)
        ):
            fundamentals.append((candidate_v + candidate_h, candidate_conf, candidate_v, candidate_h))
    if fundamentals:
        _, confidence, v_period, h_period = min(fundamentals)
    return v_period, h_period, confidence


def _fine_gray_grid_spacing(
    gray: np.ndarray, axis: int
) -> tuple[float, float]:
    """Estimate a dense, possibly non-integer grid from faint gray lines."""
    # Printed/scaled charts often have light-gray grid lines while the motif is
    # colored or black.  Restricting the projection to midtones separates those
    # lines and permits subpixel spacing estimates after image resampling.
    midtone = ((gray >= 120) & (gray <= 245)).astype(np.float64)
    projection = midtone.mean(axis=axis)
    threshold = float(np.percentile(projection, 75))
    if threshold <= 0:
        return np.nan, 0.0
    indices = np.flatnonzero(projection >= threshold)
    groups = np.split(indices, np.flatnonzero(np.diff(indices) > 1) + 1)
    centers = np.array([
        float(np.average(group, weights=projection[group]))
        for group in groups if 0 < group.size <= 4
    ])
    axis_size = projection.size
    if centers.size < max(20, axis_size // 10):
        return np.nan, 0.0
    distances = np.diff(centers)
    distances = distances[(distances >= 2.0) & (distances <= 12.0)]
    if distances.size < max(15, centers.size // 3):
        return np.nan, 0.0
    spacing = float(np.median(distances))
    tolerance = max(0.55, spacing * 0.15)
    regular_ratio = float(np.mean(np.abs(distances - spacing) <= tolerance))
    if regular_ratio < 0.55:
        return np.nan, 0.0
    return spacing, regular_ratio


def _image_shift_periods(gray: np.ndarray) -> tuple[float, float, float]:
    """Estimate grid periods from correlation of the complete image.

    Projection averages are easily dominated by a motif or by every fifth
    guide line.  Correlating a high-pass image with shifted copies retains
    short line fragments and dotted grids.  The earliest peak with substantial
    support relative to the strongest peak is the fundamental; later peaks are
    normally its harmonics.
    """
    values = gray.astype(np.float32)
    values -= cv2.GaussianBlur(values, (0, 0), 10.0)

    def axis_candidates(axis: int) -> list[tuple[float, float]]:
        limit = min(64, values.shape[axis] // 3)
        if limit <= 4:
            return []
        scores: list[float] = []
        # Short JPEG block structure is common in downloaded charts and is not
        # a plausible *new* grid period here. Genuine 4--6 px grids are already
        # captured more reliably by the projection/fine-line paths.
        for lag in range(6, limit + 1):
            if axis == 1:
                left, right = values[:, :-lag], values[:, lag:]
            else:
                left, right = values[:-lag, :], values[lag:, :]
            denominator = float(np.linalg.norm(left) * np.linalg.norm(right))
            scores.append(float(np.sum(left * right) / denominator) if denominator else 0.0)
        peaks = [
            (float(lag), scores[lag - 6])
            for lag in range(7, limit)
            if scores[lag - 6] > scores[lag - 7]
            and scores[lag - 6] >= scores[lag - 5]
        ]
        if not peaks:
            return []
        strongest = max(score for _, score in peaks)
        cutoff = max(0.065, strongest * 0.34)
        return [(period, score) for period, score in peaks if score >= cutoff]

    vertical = axis_candidates(1)
    horizontal = axis_candidates(0)
    direct_pairs: list[tuple[float, float, float, float]] = []
    harmonic_pairs: list[tuple[float, float, float, float]] = []
    for v_period, v_score in vertical:
        for h_period, h_score in horizontal:
            ratio = max(v_period, h_period) / min(v_period, h_period)
            if ratio <= 1.35:
                direct_pairs.append((v_period + h_period, min(v_score, h_score), v_period, h_period))
            multiple = round(h_period / v_period)
            if multiple >= 2 and abs(h_period / v_period - multiple) <= 0.12:
                harmonic_pairs.append((2 * v_period, min(v_score, h_score), v_period, v_period))
            multiple = round(v_period / h_period)
            if multiple >= 2 and abs(v_period / h_period - multiple) <= 0.12:
                harmonic_pairs.append((2 * h_period, min(v_score, h_score), h_period, h_period))
    if not direct_pairs and not harmonic_pairs:
        # A guide-line harmonic can hide the fundamental on one axis.  Reuse
        # the other axis only when it divides a well-supported detected period.
        for period, score in vertical:
            for other_period, other_score in horizontal:
                multiple = round(other_period / period)
                if multiple >= 2 and abs(other_period / period - multiple) <= 0.12:
                    return period, period, min(score, other_score)
                multiple = round(period / other_period)
                if multiple >= 2 and abs(period / other_period - multiple) <= 0.12:
                    return other_period, other_period, min(score, other_score)
        return np.nan, np.nan, 0.0
    best_direct = min(direct_pairs) if direct_pairs else None
    best_harmonic = min(harmonic_pairs) if harmonic_pairs else None
    # Do not turn a mildly rectangular grid into a square one merely because
    # a later peak happens to be an integral multiple.  A harmonic correction
    # must be substantially finer than the best direct X/Y agreement.
    if best_harmonic is not None and (
        best_direct is None or best_harmonic[0] <= 0.75 * best_direct[0]
    ):
        _, confidence, v_period, h_period = best_harmonic
    else:
        _, confidence, v_period, h_period = best_direct
    return v_period, h_period, confidence


def estimate_grid_spacing(
    binary: np.ndarray, gray: np.ndarray | None = None
) -> dict[str, float]:
    """Estimate X/Y cell size and regularity from projection peaks."""
    height, width = binary.shape
    vertical_peaks = _projection_peaks(binary.sum(axis=0), height)
    horizontal_peaks = _projection_peaks(binary.sum(axis=1), width)
    vertical = _spacing_features(vertical_peaks, "vertical", width)
    horizontal = _spacing_features(horizontal_peaks, "horizontal", height)
    v_spacing = vertical["vertical_spacing_median_px"]
    h_spacing = horizontal["horizontal_spacing_median_px"]
    v_conf = float(vertical["vertical_grid_confidence"])
    h_conf = float(horizontal["horizontal_grid_confidence"])
    # Grayscale projections preserve faint antialiased grid lines that may
    # disappear during Otsu binarization, especially along one axis.
    period_source = 255.0 - gray.astype(np.float64) if gray is not None else binary
    v_period, v_period_conf = _projection_period(period_source.mean(axis=0))
    h_period, h_period_conf = _projection_period(period_source.mean(axis=1))
    if gray is not None:
        v_fine, v_fine_conf = _fine_gray_grid_spacing(gray, axis=0)
        h_fine, h_fine_conf = _fine_gray_grid_spacing(gray, axis=1)
        # Require agreement across both axes: isolated texture in the motif
        # should not override the projection-based estimate.
        coarse_agrees = (
            np.isfinite(v_spacing) and np.isfinite(h_spacing)
            and max(v_spacing, h_spacing) / min(v_spacing, h_spacing) <= 1.25
            and min(v_conf, h_conf) >= 0.75
        )
        fine_is_plausible = min(v_fine, h_fine) >= 3.5
        if (
            np.isfinite(v_fine) and np.isfinite(h_fine)
            and fine_is_plausible
            and (not coarse_agrees or min(v_fine_conf, h_fine_conf) >= 0.70)
        ):
            v_period, v_period_conf = v_fine, v_fine_conf
            h_period, h_period_conf = h_fine, h_fine_conf
        else:
            # A motif can obscure the faint grid along one axis while the
            # perpendicular projection still exposes its fundamental period.
            # Reuse that period for a square grid only when both coarse periods
            # are clear integral harmonics of it.
            fine_candidates = [
                (v_fine, v_fine_conf), (h_fine, h_fine_conf)
            ]
            usable_fine = [
                (spacing, confidence)
                for spacing, confidence in fine_candidates
                if np.isfinite(spacing) and spacing >= 3.5 and confidence >= 0.55
            ]
            if len(usable_fine) == 1:
                shared_spacing, shared_confidence = usable_fine[0]

                def is_harmonic(period: float) -> bool:
                    if not np.isfinite(period):
                        return False
                    ratio = period / shared_spacing
                    return round(ratio) >= 1 and abs(ratio - round(ratio)) <= 0.10

                if is_harmonic(v_period) and is_harmonic(h_period):
                    v_period = h_period = shared_spacing
                    v_period_conf = max(v_period_conf, shared_confidence)
                    h_period_conf = max(h_period_conf, shared_confidence)
        periods_agree = (
            np.isfinite(v_period) and np.isfinite(h_period)
            and max(v_period, h_period) / min(v_period, h_period) <= 1.25
        )
        joint_v, joint_h, joint_conf = _joint_projection_periods(gray)
        if periods_agree and np.isfinite(joint_v):
            v_multiple = round(v_period / joint_v)
            h_multiple = round(h_period / joint_h)
            if (
                v_multiple == h_multiple and v_multiple >= 2
                and abs(v_period / joint_v - v_multiple) <= 0.15
                and abs(h_period / joint_h - h_multiple) <= 0.15
                and joint_conf >= 0.05
            ):
                v_period, h_period = joint_v, joint_h
                v_period_conf = h_period_conf = joint_conf
        elif not periods_agree:
            if np.isfinite(joint_v) and joint_conf >= 0.05:
                v_period, h_period = joint_v, joint_h
                v_period_conf = h_period_conf = joint_conf
        image_v, image_h, image_conf = _image_shift_periods(gray)
        if np.isfinite(image_v) and image_conf >= 0.065:
            # Only replace a coarser estimate.  This makes the new detector a
            # harmonic correction and leaves already established fine periods
            # (including resampled 4--6 px grids) untouched.
            if not np.isfinite(v_period) or v_period / image_v >= 1.65:
                v_period, v_period_conf = image_v, image_conf
            if not np.isfinite(h_period) or h_period / image_h >= 1.65:
                h_period, h_period_conf = image_h, image_conf
    if np.isfinite(v_period):
        v_spacing = v_period
        v_conf = max(v_conf, v_period_conf)
    if np.isfinite(h_period):
        h_spacing = h_period
        h_conf = max(h_conf, h_period_conf)
    return {
        "estimated_cell_width_px": v_spacing,
        "estimated_cell_height_px": h_spacing,
        **vertical,
        **horizontal,
        "grid_confidence_mean": (v_conf + h_conf) / 2.0,
    }


def calculate_quality_features(
    gray: np.ndarray, binary: np.ndarray
) -> dict[str, float]:
    """Calculate brightness, sharpness, and edge-density indicators."""
    brightness_std = float(np.std(gray))
    edges = cv2.Canny(gray, 100, 200)
    return {
        "brightness_mean": float(np.mean(gray)),
        "brightness_std": brightness_std,
        "contrast": brightness_std,
        "blur_score": float(cv2.Laplacian(gray, cv2.CV_64F).var()),
        "edge_density": float(np.count_nonzero(edges) / binary.size),
    }
