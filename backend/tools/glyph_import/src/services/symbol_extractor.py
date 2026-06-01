"""Extract separate symbol images from a multi-symbol source image."""

from __future__ import annotations

import io
from collections import deque
from pathlib import Path

from PIL import Image, ImageDraw

from src.domain.models import DetectedSymbol, LoadedImage, PreprocessedImage, SymbolBounds
from src.utils.json_utils import write_json_file


class SymbolExtractionError(ValueError):
    """Raised when separate symbols cannot be extracted from the source image."""


def extract_symbols(
    *,
    loaded_image: LoadedImage,
    preprocessed_image: PreprocessedImage,
    output_dir: Path,
    debug_dir: Path,
    manifests_dir: Path,
    min_symbol_width: int = 8,
    min_symbol_height: int = 8,
    min_symbol_area: int = 64,
    crop_padding: int = 2,
) -> tuple[tuple[DetectedSymbol, ...], Path, Path, Path]:
    """Find symbol components, save crops/debug artifacts, and write a manifest."""
    _validate_options(
        min_symbol_width=min_symbol_width,
        min_symbol_height=min_symbol_height,
        min_symbol_area=min_symbol_area,
        crop_padding=crop_padding,
    )

    bounds = _find_symbol_bounds(
        preprocessed_image.binary_image,
        min_symbol_width=min_symbol_width,
        min_symbol_height=min_symbol_height,
        min_symbol_area=min_symbol_area,
        crop_padding=crop_padding,
    )
    if not bounds:
        raise SymbolExtractionError("No symbol regions found in the source image.")

    output_dir.mkdir(parents=True, exist_ok=True)
    debug_dir.mkdir(parents=True, exist_ok=True)
    manifests_dir.mkdir(parents=True, exist_ok=True)

    source_image = Image.open(io.BytesIO(loaded_image.content))
    source_image.load()
    _remove_previous_symbol_crops(output_dir=output_dir, source_stem=loaded_image.path.stem)
    symbols = _save_symbol_crops(
        source_image=source_image,
        source_stem=loaded_image.path.stem,
        bounds=bounds,
        output_dir=output_dir,
    )
    binary_debug_path = debug_dir / f"{loaded_image.path.stem}_extraction_binary.png"
    overlay_debug_path = debug_dir / f"{loaded_image.path.stem}_extraction_overlay.png"
    manifest_path = manifests_dir / "manifest.json"

    preprocessed_image.binary_image.save(binary_debug_path, format="PNG")
    _save_overlay_debug_image(
        source_image=source_image,
        symbols=symbols,
        output_path=overlay_debug_path,
    )
    _write_manifest(
        manifest_path=manifest_path,
        loaded_image=loaded_image,
        symbols=symbols,
        binary_debug_path=binary_debug_path,
        overlay_debug_path=overlay_debug_path,
    )

    return symbols, binary_debug_path, overlay_debug_path, manifest_path


def _validate_options(
    *,
    min_symbol_width: int,
    min_symbol_height: int,
    min_symbol_area: int,
    crop_padding: int,
) -> None:
    """Validate extraction thresholds."""
    if min_symbol_width <= 0:
        raise SymbolExtractionError("min_symbol_width must be positive.")
    if min_symbol_height <= 0:
        raise SymbolExtractionError("min_symbol_height must be positive.")
    if min_symbol_area <= 0:
        raise SymbolExtractionError("min_symbol_area must be positive.")
    if crop_padding < 0:
        raise SymbolExtractionError("crop_padding must not be negative.")


def _find_symbol_bounds(
    image: Image.Image,
    *,
    min_symbol_width: int,
    min_symbol_height: int,
    min_symbol_area: int,
    crop_padding: int,
) -> tuple[SymbolBounds, ...]:
    """Find symbol boxes by splitting the page into rows and row segments."""
    binary_image = image.convert("L")
    width, height = binary_image.size
    row_bands = _find_row_bands(
        binary_image,
        min_symbol_height=min_symbol_height,
        min_symbol_area=min_symbol_area,
    )
    row_bounds: list[SymbolBounds] = []

    for row_band in row_bands:
        row_bounds.extend(
            _find_bounds_in_row(
                binary_image,
                row_band=row_band,
                min_symbol_width=min_symbol_width,
                min_symbol_area=min_symbol_area,
                crop_padding=crop_padding,
            )
        )

    if row_bounds:
        return _sort_bounds_reading_order(tuple(row_bounds))

    return _find_component_bounds(
        binary_image,
        image_width=width,
        image_height=height,
        min_symbol_width=min_symbol_width,
        min_symbol_height=min_symbol_height,
        min_symbol_area=min_symbol_area,
        crop_padding=crop_padding,
    )


def _find_component_bounds(
    image: Image.Image,
    *,
    image_width: int,
    image_height: int,
    min_symbol_width: int,
    min_symbol_height: int,
    min_symbol_area: int,
    crop_padding: int,
) -> tuple[SymbolBounds, ...]:
    """Fallback: find connected black-pixel components large enough to be symbols."""
    visited: set[tuple[int, int]] = set()
    bounds: list[SymbolBounds] = []

    for y in range(image_height):
        for x in range(image_width):
            point = (x, y)
            if point in visited or image.getpixel(point) != 0:
                continue

            component_bounds, component_area = _collect_component(
                image=image,
                start=point,
                visited=visited,
            )
            component_width = component_bounds.right - component_bounds.left + 1
            component_height = component_bounds.bottom - component_bounds.top + 1
            if (
                component_width < min_symbol_width
                or component_height < min_symbol_height
                or component_area < min_symbol_area
            ):
                continue

            bounds.append(
                _pad_bounds(
                    component_bounds,
                    image_width=image_width,
                    image_height=image_height,
                    padding=crop_padding,
                )
            )

    return _sort_bounds_reading_order(tuple(bounds))


def _find_row_bands(
    image: Image.Image,
    *,
    min_symbol_height: int,
    min_symbol_area: int,
) -> tuple[SymbolBounds, ...]:
    """Find horizontal bands that contain symbol ink."""
    width, height = image.size
    row_counts = [
        sum(1 for x in range(width) if image.getpixel((x, y)) == 0)
        for y in range(height)
    ]
    blank_runs = _find_low_runs(
        row_counts,
        threshold=3,
        min_length=max(5, min_symbol_height // 2),
    )
    bands: list[SymbolBounds] = []
    previous_bottom = 0

    for blank_start, blank_end in blank_runs:
        if blank_start - previous_bottom >= min_symbol_height:
            bands.append(
                SymbolBounds(
                    left=0,
                    top=previous_bottom,
                    right=width - 1,
                    bottom=blank_start - 1,
                )
            )
        previous_bottom = blank_end + 1

    if height - previous_bottom >= min_symbol_height:
        bands.append(
            SymbolBounds(
                left=0,
                top=previous_bottom,
                right=width - 1,
                bottom=height - 1,
            )
        )

    return tuple(
        band
        for band in bands
        if _count_dark_pixels(image, band) >= min_symbol_area
    )


def _find_bounds_in_row(
    image: Image.Image,
    *,
    row_band: SymbolBounds,
    min_symbol_width: int,
    min_symbol_area: int,
    crop_padding: int,
) -> tuple[SymbolBounds, ...]:
    """Split one row band into symbol boxes using low-ink vertical separators."""
    image_width, image_height = image.size
    ink_bounds = _tight_dark_bounds(image, row_band)
    if ink_bounds is None:
        return ()

    row_height = row_band.bottom - row_band.top + 1
    column_counts = [
        sum(
            1
            for y in range(row_band.top, row_band.bottom + 1)
            if image.getpixel((x, y)) == 0
        )
        for x in range(image_width)
    ]
    expected_segment_count = max(
        1,
        round((ink_bounds.right - ink_bounds.left + 1) / (row_height * 0.9)),
    )
    bounds = _split_row_with_thresholds(
        image,
        row_band=row_band,
        ink_bounds=ink_bounds,
        column_counts=column_counts,
        thresholds=(1,),
        min_symbol_width=min_symbol_width,
        min_symbol_area=min_symbol_area,
        crop_padding=crop_padding,
    )
    if len(bounds) < min(2, expected_segment_count) or len(bounds) < expected_segment_count:
        bounds = _split_row_with_thresholds(
            image,
            row_band=row_band,
            ink_bounds=ink_bounds,
            column_counts=column_counts,
            thresholds=tuple(sorted({3, 8, max(3, round(row_height * 0.08))})),
            min_symbol_width=min_symbol_width,
            min_symbol_area=min_symbol_area,
            crop_padding=crop_padding,
        )

    merged_bounds = _merge_centered_tail_segments(
        _merge_leading_short_segments(tuple(bounds), row_height=row_height),
        row_height=row_height,
    )
    return _expand_edge_touching_bounds(
        image,
        bounds=merged_bounds,
        row_band=row_band,
        row_height=row_height,
    )


def _merge_leading_short_segments(
    bounds: tuple[SymbolBounds, ...],
    *,
    row_height: int,
) -> tuple[SymbolBounds, ...]:
    """Merge a narrow leading split with its neighbor on sparse lower rows."""
    if len(bounds) < 2:
        return bounds

    first = bounds[0]
    second = bounds[1]
    first_width = first.right - first.left + 1
    gap = second.left - first.right - 1
    if first_width > row_height * 0.7 or gap > row_height * 0.15:
        return bounds

    merged = SymbolBounds(
        left=max(first.left, first.right - round(row_height * 0.35)),
        top=min(first.top, second.top),
        right=second.right,
        bottom=max(first.bottom, second.bottom),
    )
    return (merged, *bounds[2:])


def _split_row_with_thresholds(
    image: Image.Image,
    *,
    row_band: SymbolBounds,
    ink_bounds: SymbolBounds,
    column_counts: list[int],
    thresholds: tuple[int, ...],
    min_symbol_width: int,
    min_symbol_area: int,
    crop_padding: int,
) -> tuple[SymbolBounds, ...]:
    """Split a row using separators found at the given projection thresholds."""
    image_width, image_height = image.size
    row_height = row_band.bottom - row_band.top + 1
    effective_crop_padding = max(crop_padding, round(row_height * 0.07))
    separator_positions = _find_column_separator_positions(
        column_counts=column_counts,
        left=ink_bounds.left,
        right=ink_bounds.right,
        thresholds=thresholds,
        min_symbol_width=min_symbol_width,
    )
    segment_edges = _choose_segment_edges(
        left=ink_bounds.left,
        right=ink_bounds.right + 1,
        separator_positions=separator_positions,
        row_height=row_height,
        min_symbol_width=min_symbol_width,
    )
    if not segment_edges:
        segment_edges = (ink_bounds.right + 1,)

    bounds: list[SymbolBounds] = []
    previous_left = ink_bounds.left
    for segment_right in segment_edges:
        segment = SymbolBounds(
            left=previous_left,
            top=row_band.top,
            right=segment_right - 1,
            bottom=row_band.bottom,
        )
        symbol_bounds = _tight_symbol_bounds(
            image,
            segment,
            row_height=row_height,
        )
        if (
            symbol_bounds is not None
            and _count_dark_pixels(image, symbol_bounds) >= min_symbol_area
            and symbol_bounds.bottom - symbol_bounds.top + 1 >= row_height * 0.5
        ):
            padded_bounds = _pad_bounds(
                symbol_bounds,
                image_width=image_width,
                image_height=image_height,
                padding=effective_crop_padding,
            )
            bounds.append(
                SymbolBounds(
                    left=max(padded_bounds.left, segment.left),
                    top=max(padded_bounds.top, row_band.top),
                    right=min(padded_bounds.right, segment.right),
                    bottom=min(padded_bounds.bottom, row_band.bottom),
                )
            )
        previous_left = segment_right

    return tuple(bounds)


def _expand_edge_touching_bounds(
    image: Image.Image,
    *,
    bounds: tuple[SymbolBounds, ...],
    row_band: SymbolBounds,
    row_height: int,
) -> tuple[SymbolBounds, ...]:
    """Expand crops into separator gaps when ink reaches a crop edge."""
    if not bounds:
        return bounds

    expansion = max(3, round(row_height * 0.04))
    expanded_bounds: list[SymbolBounds] = []
    for index, current in enumerate(bounds):
        previous_bound = bounds[index - 1] if index > 0 else None
        next_bound = bounds[index + 1] if index + 1 < len(bounds) else None
        left_limit = previous_bound.right + 1 if previous_bound is not None else row_band.left
        right_limit = next_bound.left - 1 if next_bound is not None else row_band.right

        left = current.left
        right = current.right
        if _edge_has_dark_pixels(image, current, side="left"):
            left = max(left_limit, left - expansion)
        if _edge_has_dark_pixels(image, current, side="right"):
            right = min(right_limit, right + expansion)

        expanded_bounds.append(
            SymbolBounds(left=left, top=current.top, right=right, bottom=current.bottom)
        )

    return tuple(expanded_bounds)


def _edge_has_dark_pixels(image: Image.Image, bounds: SymbolBounds, *, side: str) -> bool:
    """Return true when dark pixels touch the requested vertical edge."""
    x = bounds.left if side == "left" else bounds.right
    return any(image.getpixel((x, y)) == 0 for y in range(bounds.top, bounds.bottom + 1))


def _merge_centered_tail_segments(
    bounds: tuple[SymbolBounds, ...],
    *,
    row_height: int,
) -> tuple[SymbolBounds, ...]:
    """Merge a trailing decorative split on centered short rows."""
    if len(bounds) != 4 or bounds[0].left <= row_height * 0.6:
        return bounds

    previous = bounds[-2]
    last = bounds[-1]
    merged_width = last.right - previous.left + 1
    if merged_width > row_height * 1.8:
        return bounds

    merged = SymbolBounds(
        left=previous.left,
        top=min(previous.top, last.top),
        right=last.right,
        bottom=max(previous.bottom, last.bottom),
    )
    return (*bounds[:-2], merged)


def _find_column_separator_positions(
    *,
    column_counts: list[int],
    left: int,
    right: int,
    thresholds: tuple[int, ...],
    min_symbol_width: int,
) -> tuple[int, ...]:
    """Return candidate vertical separators inside a row."""
    candidates: list[int] = []

    for threshold in thresholds:
        for run_left, run_right in _find_low_runs(
            column_counts[left : right + 1],
            threshold=threshold,
            min_length=max(6, min_symbol_width // 2),
        ):
            absolute_left = left + run_left
            absolute_right = left + run_right
            separator = (absolute_left + absolute_right + 1) // 2
            if separator - left <= min_symbol_width or right - separator <= min_symbol_width:
                continue
            if all(abs(separator - existing) > 5 for existing in candidates):
                candidates.append(separator)

    return tuple(sorted(candidates))


def _choose_segment_edges(
    *,
    left: int,
    right: int,
    separator_positions: tuple[int, ...],
    row_height: int,
    min_symbol_width: int,
) -> tuple[int, ...]:
    """Pick separators that produce plausible symbol-width segments."""
    positions = (left, *separator_positions, right)
    min_width = max(min_symbol_width, round(row_height * 0.35))
    max_width = max(min_width + 1, round(row_height * 1.7), min_symbol_width * 3)
    ideal_width = max(float(min_symbol_width), row_height * 0.95)
    segment_penalty = 0.08

    best: list[tuple[float, tuple[int, ...]]] = [
        (float("inf"), ()) for _ in positions
    ]
    best[0] = (0.0, ())

    for left_index, position_left in enumerate(positions):
        current_cost, current_path = best[left_index]
        if current_cost == float("inf"):
            continue

        for right_index in range(left_index + 1, len(positions)):
            position_right = positions[right_index]
            width = position_right - position_left
            if width < min_width:
                continue
            if width > max_width:
                break

            width_score = ((width - ideal_width) / ideal_width) ** 2
            candidate_cost = current_cost + width_score + segment_penalty
            if candidate_cost < best[right_index][0]:
                best[right_index] = (
                    candidate_cost,
                    (*current_path, position_right),
                )

    return best[-1][1]


def _find_low_runs(
    values: list[int],
    *,
    threshold: int,
    min_length: int,
) -> tuple[tuple[int, int], ...]:
    """Find contiguous runs where projection values stay below threshold."""
    runs: list[tuple[int, int]] = []
    run_start: int | None = None

    for index, value in enumerate(values):
        if value < threshold and run_start is None:
            run_start = index
        if run_start is not None and (value >= threshold or index == len(values) - 1):
            run_end = index - 1 if value >= threshold else index
            if run_end - run_start + 1 >= min_length:
                runs.append((run_start, run_end))
            run_start = None

    return tuple(runs)


def _tight_dark_bounds(image: Image.Image, bounds: SymbolBounds) -> SymbolBounds | None:
    """Return tight dark-pixel bounds inside the given search rectangle."""
    dark_points: list[tuple[int, int]] = []
    for y in range(bounds.top, bounds.bottom + 1):
        for x in range(bounds.left, bounds.right + 1):
            if image.getpixel((x, y)) == 0:
                dark_points.append((x, y))

    if not dark_points:
        return None

    return SymbolBounds(
        left=min(x for x, _ in dark_points),
        top=min(y for _, y in dark_points),
        right=max(x for x, _ in dark_points),
        bottom=max(y for _, y in dark_points),
    )


def _tight_symbol_bounds(
    image: Image.Image,
    bounds: SymbolBounds,
    *,
    row_height: int,
) -> SymbolBounds | None:
    """Return tight bounds while ignoring small artifacts at segment edges."""
    components = _collect_components_in_bounds(image, bounds)
    if not components:
        return None

    max_area = max(area for area, _ in components)
    edge_margin = max(2, round(row_height * 0.08))
    max_edge_artifact_area = max(12, round(max_area * 0.45))
    kept_bounds: list[SymbolBounds] = []

    for area, component_bounds in components:
        touches_left_edge = component_bounds.left <= bounds.left + edge_margin
        touches_right_edge = component_bounds.right >= bounds.right - edge_margin
        component_width = component_bounds.right - component_bounds.left + 1
        component_height = component_bounds.bottom - component_bounds.top + 1
        looks_like_edge_artifact = (
            (touches_left_edge or touches_right_edge)
            and area <= max_edge_artifact_area
            and component_width <= row_height * 0.45
            and component_height <= row_height * 0.16
        )
        if not looks_like_edge_artifact:
            kept_bounds.append(component_bounds)

    if not kept_bounds:
        kept_bounds = [component_bounds for _, component_bounds in components]

    return SymbolBounds(
        left=min(item.left for item in kept_bounds),
        top=min(item.top for item in kept_bounds),
        right=max(item.right for item in kept_bounds),
        bottom=max(item.bottom for item in kept_bounds),
    )


def _collect_components_in_bounds(
    image: Image.Image,
    bounds: SymbolBounds,
) -> tuple[tuple[int, SymbolBounds], ...]:
    """Collect dark connected components inside a rectangle."""
    visited: set[tuple[int, int]] = set()
    components: list[tuple[int, SymbolBounds]] = []

    for y in range(bounds.top, bounds.bottom + 1):
        for x in range(bounds.left, bounds.right + 1):
            point = (x, y)
            if point in visited or image.getpixel(point) != 0:
                continue

            component_bounds, area = _collect_component_in_bounds(
                image=image,
                start=point,
                search_bounds=bounds,
                visited=visited,
            )
            components.append((area, component_bounds))

    return tuple(components)


def _collect_component_in_bounds(
    *,
    image: Image.Image,
    start: tuple[int, int],
    search_bounds: SymbolBounds,
    visited: set[tuple[int, int]],
) -> tuple[SymbolBounds, int]:
    """Collect one 4-connected dark component constrained to bounds."""
    queue: deque[tuple[int, int]] = deque([start])
    visited.add(start)
    left = right = start[0]
    top = bottom = start[1]
    area = 0

    while queue:
        x, y = queue.popleft()
        area += 1
        left = min(left, x)
        right = max(right, x)
        top = min(top, y)
        bottom = max(bottom, y)

        for neighbor in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
            nx, ny = neighbor
            if (
                nx < search_bounds.left
                or ny < search_bounds.top
                or nx > search_bounds.right
                or ny > search_bounds.bottom
            ):
                continue
            if neighbor in visited or image.getpixel(neighbor) != 0:
                continue
            visited.add(neighbor)
            queue.append(neighbor)

    return SymbolBounds(left=left, top=top, right=right, bottom=bottom), area


def _count_dark_pixels(image: Image.Image, bounds: SymbolBounds) -> int:
    """Count dark pixels inside bounds."""
    return sum(
        1
        for y in range(bounds.top, bounds.bottom + 1)
        for x in range(bounds.left, bounds.right + 1)
        if image.getpixel((x, y)) == 0
    )


def _collect_component(
    *,
    image: Image.Image,
    start: tuple[int, int],
    visited: set[tuple[int, int]],
) -> tuple[SymbolBounds, int]:
    """Collect one 4-connected dark component from the binary image."""
    width, height = image.size
    queue: deque[tuple[int, int]] = deque([start])
    visited.add(start)
    left = right = start[0]
    top = bottom = start[1]
    area = 0

    while queue:
        x, y = queue.popleft()
        area += 1
        left = min(left, x)
        right = max(right, x)
        top = min(top, y)
        bottom = max(bottom, y)

        for neighbor in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
            nx, ny = neighbor
            if nx < 0 or ny < 0 or nx >= width or ny >= height:
                continue
            if neighbor in visited or image.getpixel(neighbor) != 0:
                continue
            visited.add(neighbor)
            queue.append(neighbor)

    return SymbolBounds(left=left, top=top, right=right, bottom=bottom), area


def _sort_bounds_reading_order(bounds: tuple[SymbolBounds, ...]) -> tuple[SymbolBounds, ...]:
    """Sort bounds top-to-bottom by rows and left-to-right inside each row."""
    if not bounds:
        return ()

    average_height = sum(item.bottom - item.top + 1 for item in bounds) / len(bounds)
    row_tolerance = max(1, round(average_height / 2))
    rows: list[list[SymbolBounds]] = []

    for item in sorted(bounds, key=lambda current: current.top):
        matching_row = next(
            (
                row
                for row in rows
                if abs(item.top - min(row_item.top for row_item in row)) <= row_tolerance
            ),
            None,
        )
        if matching_row is None:
            rows.append([item])
        else:
            matching_row.append(item)

    ordered: list[SymbolBounds] = []
    for row in sorted(rows, key=lambda current: min(item.top for item in current)):
        ordered.extend(sorted(row, key=lambda current: current.left))

    return tuple(ordered)


def _pad_bounds(
    bounds: SymbolBounds,
    *,
    image_width: int,
    image_height: int,
    padding: int,
) -> SymbolBounds:
    """Expand bounds by padding while keeping them inside the source image."""
    return SymbolBounds(
        left=max(0, bounds.left - padding),
        top=max(0, bounds.top - padding),
        right=min(image_width - 1, bounds.right + padding),
        bottom=min(image_height - 1, bounds.bottom + padding),
    )


def _save_symbol_crops(
    *,
    source_image: Image.Image,
    source_stem: str,
    bounds: tuple[SymbolBounds, ...],
    output_dir: Path,
) -> tuple[DetectedSymbol, ...]:
    """Persist each detected symbol as a separate PNG crop."""
    symbols: list[DetectedSymbol] = []
    for index, symbol_bounds in enumerate(bounds, start=1):
        output_path = output_dir / f"{source_stem}_{index:03d}.png"
        crop = source_image.crop(
            (
                symbol_bounds.left,
                symbol_bounds.top,
                symbol_bounds.right + 1,
                symbol_bounds.bottom + 1,
            )
        )
        crop.save(output_path, format="PNG")
        symbols.append(
            DetectedSymbol(
                index=index,
                bounds=symbol_bounds,
                output_path=output_path,
                width=crop.width,
                height=crop.height,
            )
        )

    return tuple(symbols)


def _remove_previous_symbol_crops(*, output_dir: Path, source_stem: str) -> None:
    """Remove stale crops for the same source before writing a fresh extraction."""
    if not output_dir.exists():
        return

    for path in output_dir.glob(f"{source_stem}_*.png"):
        if path.is_file():
            path.unlink()


def _save_overlay_debug_image(
    *,
    source_image: Image.Image,
    symbols: tuple[DetectedSymbol, ...],
    output_path: Path,
) -> None:
    """Save a source-image overlay with detected symbol boxes."""
    overlay = source_image.convert("RGB")
    draw = ImageDraw.Draw(overlay)
    for symbol in symbols:
        draw.rectangle(
            (
                symbol.bounds.left,
                symbol.bounds.top,
                symbol.bounds.right,
                symbol.bounds.bottom,
            ),
            outline=(255, 0, 0),
            width=2,
        )
        draw.text((symbol.bounds.left + 2, symbol.bounds.top + 2), str(symbol.index), fill=(255, 0, 0))

    overlay.save(output_path, format="PNG")


def _write_manifest(
    *,
    manifest_path: Path,
    loaded_image: LoadedImage,
    symbols: tuple[DetectedSymbol, ...],
    binary_debug_path: Path,
    overlay_debug_path: Path,
) -> None:
    """Write extraction metadata for manual review."""
    write_json_file(
        manifest_path,
        {
            "source_image": str(loaded_image.path),
            "source_format": loaded_image.image_format.value,
            "extracted_count": len(symbols),
            "debug": {
                "binary_image": str(binary_debug_path),
                "overlay_image": str(overlay_debug_path),
            },
            "symbols": [
                {
                    "index": symbol.index,
                    "output_path": str(symbol.output_path),
                    "width": symbol.width,
                    "height": symbol.height,
                    "bounds": {
                        "left": symbol.bounds.left,
                        "top": symbol.bounds.top,
                        "right": symbol.bounds.right,
                        "bottom": symbol.bounds.bottom,
                    },
                }
                for symbol in symbols
            ],
        },
    )
