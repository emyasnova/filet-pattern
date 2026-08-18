"""Crop source images to the detected scheme grid area."""

from __future__ import annotations

import io
from pathlib import Path

from PIL import Image, ImageDraw

from src.domain.models import CropBounds, LoadedImage, PreprocessedImage


class SchemeCropError(ValueError):
    """Raised when a scheme grid crop cannot be detected or saved."""


MIN_ACTIVE_RATIO = 0.03
MIN_RUN_LENGTH = 12
MAX_GAP_TO_FILL = 3


def crop_scheme(
    *,
    loaded_image: LoadedImage,
    preprocessed_image: PreprocessedImage,
    output_dir: Path,
    debug_dir: Path,
    crop_padding: int = 2,
) -> tuple[CropBounds, Path, Path, int, int]:
    """Detect the outer scheme grid, save the source crop, and save a debug overlay."""
    if crop_padding < 0:
        raise SchemeCropError("crop_padding must not be negative.")

    bounds = detect_scheme_crop_bounds(
        preprocessed_image.binary_image,
        crop_padding=crop_padding,
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    debug_dir.mkdir(parents=True, exist_ok=True)

    source_image = Image.open(io.BytesIO(loaded_image.content))
    source_image.load()
    output_path = output_dir / f"{loaded_image.path.stem}.png"
    overlay_debug_path = debug_dir / f"{loaded_image.path.stem}_crop_overlay.png"

    crop = source_image.crop((bounds.left, bounds.top, bounds.right + 1, bounds.bottom + 1))
    crop.save(output_path, format="PNG")
    _save_overlay_debug_image(
        source_image=source_image,
        bounds=bounds,
        output_path=overlay_debug_path,
    )

    return bounds, output_path, overlay_debug_path, crop.width, crop.height


def detect_scheme_crop_bounds(
    image: Image.Image,
    *,
    crop_padding: int = 2,
) -> CropBounds:
    """Return padded bounds of the largest grid-like dark-pixel band."""
    if crop_padding < 0:
        raise SchemeCropError("crop_padding must not be negative.")

    binary_image = image.convert("L")
    image_width, image_height = binary_image.size
    row_counts = [
        sum(1 for x in range(image_width) if binary_image.getpixel((x, y)) == 0)
        for y in range(image_height)
    ]
    row_band = _find_dominant_axis_band(
        counts=row_counts,
        axis_length=image_height,
        cross_length=image_width,
        min_length=MIN_RUN_LENGTH,
    )

    column_counts = [
        sum(
            1
            for y in range(row_band[0], row_band[1] + 1)
            if binary_image.getpixel((x, y)) == 0
        )
        for x in range(image_width)
    ]
    column_band = _find_dominant_axis_band(
        counts=column_counts,
        axis_length=image_width,
        cross_length=row_band[1] - row_band[0] + 1,
        min_length=MIN_RUN_LENGTH,
    )

    tight_bounds = _tight_dark_bounds(
        binary_image,
        CropBounds(
            left=column_band[0],
            top=row_band[0],
            right=column_band[1],
            bottom=row_band[1],
        ),
    )
    if tight_bounds is None:
        raise SchemeCropError("Unable to detect a scheme grid crop.")

    return _pad_bounds(
        tight_bounds,
        image_width=image_width,
        image_height=image_height,
        padding=crop_padding,
    )


def _find_dominant_axis_band(
    *,
    counts: list[int],
    axis_length: int,
    cross_length: int,
    min_length: int,
) -> tuple[int, int]:
    """Find the dominant contiguous active band on one axis."""
    active_threshold = max(3, round(cross_length * MIN_ACTIVE_RATIO))
    active = [count >= active_threshold for count in counts]
    active = _fill_small_inactive_gaps(active, max_gap=MAX_GAP_TO_FILL)
    runs = _active_runs(active, min_length=min_length)
    if not runs:
        raise SchemeCropError("Unable to detect a scheme grid crop.")

    minimum_span = max(min_length, round(axis_length * 0.15))
    plausible_runs = [
        run for run in runs if run[1] - run[0] + 1 >= minimum_span
    ]
    candidate_runs = plausible_runs or runs
    best_run = max(
        candidate_runs,
        key=lambda run: (
            sum(counts[run[0] : run[1] + 1]),
            run[1] - run[0] + 1,
        ),
    )
    return best_run


def _fill_small_inactive_gaps(active: list[bool], *, max_gap: int) -> list[bool]:
    """Fill tiny inactive gaps inside active projection bands."""
    filled = active[:]
    index = 0
    while index < len(filled):
        if filled[index]:
            index += 1
            continue

        gap_start = index
        while index < len(filled) and not filled[index]:
            index += 1
        gap_end = index - 1
        gap_length = gap_end - gap_start + 1
        has_left = gap_start > 0 and filled[gap_start - 1]
        has_right = index < len(filled) and filled[index]
        if has_left and has_right and gap_length <= max_gap:
            for gap_index in range(gap_start, gap_end + 1):
                filled[gap_index] = True

    return filled


def _active_runs(active: list[bool], *, min_length: int) -> tuple[tuple[int, int], ...]:
    """Return contiguous active index runs."""
    runs: list[tuple[int, int]] = []
    run_start: int | None = None

    for index, is_active in enumerate(active):
        if is_active and run_start is None:
            run_start = index
        if run_start is not None and (not is_active or index == len(active) - 1):
            run_end = index - 1 if not is_active else index
            if run_end - run_start + 1 >= min_length:
                runs.append((run_start, run_end))
            run_start = None

    return tuple(runs)


def _tight_dark_bounds(image: Image.Image, bounds: CropBounds) -> CropBounds | None:
    """Return tight dark-pixel bounds inside a candidate crop rectangle."""
    dark_points: list[tuple[int, int]] = []
    for y in range(bounds.top, bounds.bottom + 1):
        for x in range(bounds.left, bounds.right + 1):
            if image.getpixel((x, y)) == 0:
                dark_points.append((x, y))

    if not dark_points:
        return None

    return CropBounds(
        left=min(x for x, _ in dark_points),
        top=min(y for _, y in dark_points),
        right=max(x for x, _ in dark_points),
        bottom=max(y for _, y in dark_points),
    )


def _pad_bounds(
    bounds: CropBounds,
    *,
    image_width: int,
    image_height: int,
    padding: int,
) -> CropBounds:
    """Expand bounds by padding while keeping them inside the source image."""
    return CropBounds(
        left=max(0, bounds.left - padding),
        top=max(0, bounds.top - padding),
        right=min(image_width - 1, bounds.right + padding),
        bottom=min(image_height - 1, bounds.bottom + padding),
    )


def _save_overlay_debug_image(
    *,
    source_image: Image.Image,
    bounds: CropBounds,
    output_path: Path,
) -> None:
    """Save a source-image overlay with the detected crop box."""
    overlay = source_image.convert("RGB")
    draw = ImageDraw.Draw(overlay)
    draw.rectangle(
        (bounds.left, bounds.top, bounds.right, bounds.bottom),
        outline=(255, 0, 0),
        width=2,
    )
    overlay.save(output_path, format="PNG")
