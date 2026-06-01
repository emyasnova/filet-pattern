"""Grid detection on preprocessed glyph images."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

from src.domain.models import GridDetectionResult, PreprocessedImage


DARKNESS_SCALE_MAX = 255
DEFAULT_MIN_GRID_STEP = 4
DEFAULT_MAX_GRID_STEP = 24
DEFAULT_REFINEMENT_WINDOW_DIVISOR = 3
DEFAULT_MIN_PEAK_RATIO = 0.25
DEFAULT_STEP_SIMILARITY_RATIO = 0.75
DEFAULT_EDGE_GAP_RATIO_MIN = 0.55
DEFAULT_EDGE_GAP_RATIO_MAX = 1.45
DEFAULT_SINGLE_EDGE_GAP_RATIO_MIN = 0.85
DEFAULT_SINGLE_EDGE_GAP_RATIO_MAX = 1.15
DEFAULT_PROMOTION_SCORE_RATIO = 0.75
DEFAULT_REFINEMENT_MEAN_RATIO = 0.95
DEFAULT_REFINEMENT_COUNT_RATIO = 1.25
DEFAULT_PROMOTED_REFINEMENT_MEAN_RATIO = 0.98
DEFAULT_HARMONIC_KEEP_SMALL_STEP_MIN = 7
DEFAULT_HARMONIC_LARGE_STEP_RATIO = 1.8
DEFAULT_HARMONIC_REFINEMENT_STEP_MIN = 14
DEFAULT_HARMONIC_REFINEMENT_MEAN_RATIO = 0.88
DEFAULT_HARMONIC_REFINEMENT_COUNT_RATIO = 1.8
DEFAULT_PROMOTED_STEP_REFINEMENT_DROP = 1
DEFAULT_LARGE_STEP_REFINEMENT_DROP = 3
DEFAULT_SMALL_STEP_REFINEMENT_DROP = 1
DEFAULT_REFINEMENT_REGULARITY_RATIO = 1.35
DEFAULT_REFINEMENT_REGULARITY_DELTA = 0.35
DEFAULT_REFINEMENT_REGULARITY_GUARD_RATIO = 0.8
DEFAULT_PROMOTED_REFINEMENT_REGULARITY_RATIO = 2.25
DEFAULT_PROMOTED_REFINEMENT_REGULARITY_DELTA = 0.8
DEFAULT_IRREGULAR_GAP_RATIO = 0.7
DEFAULT_MIN_COVERAGE_RATIO = 0.97
DEFAULT_REGULARIZATION_SCORE_IMPROVEMENT = 1.08
DEFAULT_COVERAGE_RECOVERY_SCORE_IMPROVEMENT = 1.01
DEFAULT_MISSING_INTERNAL_LINE_GAP_RATIO = 1.45
DEFAULT_MISSING_INTERNAL_LINE_MIN_SIGNAL_RATIO = 0.65


class GridDetectionError(ValueError):
    """Raised when a usable grid cannot be detected."""


def detect_grid(
    preprocessed_image: PreprocessedImage,
    *,
    min_grid_step: int = DEFAULT_MIN_GRID_STEP,
    max_grid_step: int = DEFAULT_MAX_GRID_STEP,
    expected_columns: int | None = None,
    expected_rows: int | None = None,
    debug_dir: Path | None = None,
    debug_prefix: str | None = None,
) -> GridDetectionResult:
    """Detect grid bounds and line positions from a preprocessed image."""
    width, height = preprocessed_image.binary_image.size
    grayscale_image = preprocessed_image.grayscale_image

    vertical_signal = [
        sum(DARKNESS_SCALE_MAX - grayscale_image.getpixel((x, y)) for y in range(grayscale_image.height))
        / grayscale_image.height
        for x in range(grayscale_image.width)
    ]
    horizontal_signal = [
        sum(DARKNESS_SCALE_MAX - grayscale_image.getpixel((x, y)) for x in range(grayscale_image.width))
        / grayscale_image.width
        for y in range(grayscale_image.height)
    ]

    if expected_columns is not None:
        if expected_columns <= 0:
            raise GridDetectionError("expected_columns must be positive.")
        vertical_lines = _build_even_positions_from_count(
            signal_length=width,
            cell_count=expected_columns,
        )
    else:
        vertical_step_scores = _score_grid_steps(
            signal=vertical_signal,
            min_grid_step=min_grid_step,
            max_grid_step=max_grid_step,
        )
        vertical_step = _estimate_grid_step_from_scores(vertical_step_scores)

    if expected_rows is not None:
        if expected_rows <= 0:
            raise GridDetectionError("expected_rows must be positive.")
        horizontal_lines = _build_even_positions_from_count(
            signal_length=height,
            cell_count=expected_rows,
        )
    else:
        horizontal_step_scores = _score_grid_steps(
            signal=horizontal_signal,
            min_grid_step=min_grid_step,
            max_grid_step=max_grid_step,
        )
        horizontal_step = _estimate_grid_step_from_scores(horizontal_step_scores)

    if expected_columns is not None and expected_rows is not None:
        return _build_grid_detection_result(
            preprocessed_image=preprocessed_image,
            width=width,
            height=height,
            vertical_lines=vertical_lines,
            horizontal_lines=horizontal_lines,
            debug_dir=debug_dir,
            debug_prefix=debug_prefix,
        )

    if expected_columns is not None:
        horizontal_lines = _detect_axis_lines(
            signal=horizontal_signal,
            signal_length=height,
            min_grid_step=min_grid_step,
            max_grid_step=max_grid_step,
        )
        return _build_grid_detection_result(
            preprocessed_image=preprocessed_image,
            width=width,
            height=height,
            vertical_lines=vertical_lines,
            horizontal_lines=horizontal_lines,
            debug_dir=debug_dir,
            debug_prefix=debug_prefix,
        )

    if expected_rows is not None:
        vertical_lines = _detect_axis_lines(
            signal=vertical_signal,
            signal_length=width,
            min_grid_step=min_grid_step,
            max_grid_step=max_grid_step,
        )
        return _build_grid_detection_result(
            preprocessed_image=preprocessed_image,
            width=width,
            height=height,
            vertical_lines=vertical_lines,
            horizontal_lines=horizontal_lines,
            debug_dir=debug_dir,
            debug_prefix=debug_prefix,
        )

    vertical_promoted = False
    horizontal_promoted = False
    smaller_step = min(vertical_step, horizontal_step)
    larger_step = max(vertical_step, horizontal_step)
    keep_small_step = (
        smaller_step >= DEFAULT_HARMONIC_KEEP_SMALL_STEP_MIN
        and larger_step >= smaller_step * DEFAULT_HARMONIC_LARGE_STEP_RATIO
    )

    if keep_small_step:
        pass
    elif vertical_step < horizontal_step * DEFAULT_STEP_SIMILARITY_RATIO:
        vertical_step = _promote_step_towards_reference(
            step_scores=vertical_step_scores,
            reference_step=horizontal_step,
        )
        vertical_promoted = True
    elif horizontal_step < vertical_step * DEFAULT_STEP_SIMILARITY_RATIO:
        horizontal_step = _promote_step_towards_reference(
            step_scores=horizontal_step_scores,
            reference_step=vertical_step,
        )
        horizontal_promoted = True
    else:
        vertical_step, horizontal_step = _harmonize_grid_steps(vertical_step, horizontal_step)

    if keep_small_step:
        base_step = smaller_step
        vertical_lines = _build_regular_positions_from_step(
            signal=vertical_signal,
            signal_length=width,
            grid_step=base_step,
        )
        horizontal_lines = _build_regular_positions_from_step(
            signal=horizontal_signal,
            signal_length=height,
            grid_step=base_step,
        )
    else:
        vertical_step = _refine_grid_step(
            signal=vertical_signal,
            grid_step=vertical_step,
            min_grid_step=min_grid_step,
            max_grid_step=max_grid_step,
            promoted_refinement=vertical_promoted,
            max_step_drop=(
                DEFAULT_PROMOTED_STEP_REFINEMENT_DROP
                if vertical_promoted
                else (
                    DEFAULT_LARGE_STEP_REFINEMENT_DROP
                    if vertical_step >= 10
                    else DEFAULT_SMALL_STEP_REFINEMENT_DROP
                )
            ),
        )
        horizontal_step = _refine_grid_step(
            signal=horizontal_signal,
            grid_step=horizontal_step,
            min_grid_step=min_grid_step,
            max_grid_step=max_grid_step,
            promoted_refinement=horizontal_promoted,
            max_step_drop=(
                DEFAULT_PROMOTED_STEP_REFINEMENT_DROP
                if horizontal_promoted
                else (
                    DEFAULT_LARGE_STEP_REFINEMENT_DROP
                    if horizontal_step >= 10
                    else DEFAULT_SMALL_STEP_REFINEMENT_DROP
                )
            ),
        )

        vertical_lines = _find_line_positions(
            signal=vertical_signal,
            grid_step=vertical_step,
        )
        horizontal_lines = _find_line_positions(
            signal=horizontal_signal,
            grid_step=horizontal_step,
        )
        vertical_lines = _stabilize_line_positions(
            signal=vertical_signal,
            positions=vertical_lines,
            grid_step=vertical_step,
        )
        horizontal_lines = _stabilize_line_positions(
            signal=horizontal_signal,
            positions=horizontal_lines,
            grid_step=horizontal_step,
        )

    return _build_grid_detection_result(
        preprocessed_image=preprocessed_image,
        width=width,
        height=height,
        vertical_lines=vertical_lines,
        horizontal_lines=horizontal_lines,
        debug_dir=debug_dir,
        debug_prefix=debug_prefix,
    )


def _build_grid_detection_result(
    *,
    preprocessed_image: PreprocessedImage,
    width: int,
    height: int,
    vertical_lines: list[int],
    horizontal_lines: list[int],
    debug_dir: Path | None,
    debug_prefix: str | None,
) -> GridDetectionResult:
    """Build and optionally persist a validated grid detection result."""
    if len(vertical_lines) < 2:
        raise GridDetectionError("Unable to detect at least two vertical grid lines.")

    if len(horizontal_lines) < 2:
        raise GridDetectionError("Unable to detect at least two horizontal grid lines.")

    result = GridDetectionResult(
        source_path=preprocessed_image.source_path,
        left=0,
        top=0,
        right=width - 1,
        bottom=height - 1,
        vertical_lines=tuple(vertical_lines),
        horizontal_lines=tuple(horizontal_lines),
        column_count=len(vertical_lines) - 1,
        row_count=len(horizontal_lines) - 1,
    )

    if debug_dir is not None:
        save_grid_debug_image(
            preprocessed_image=preprocessed_image,
            detection_result=result,
            debug_dir=debug_dir,
            prefix=debug_prefix or preprocessed_image.source_path.stem,
        )

    return result


def _build_even_positions_from_count(
    *,
    signal_length: int,
    cell_count: int,
) -> list[int]:
    """Build regular grid line positions when the cell count is provided by the user."""
    if cell_count < 1:
        return []

    return [
        round(index * (signal_length - 1) / cell_count)
        for index in range(cell_count + 1)
    ]


def save_grid_debug_image(
    *,
    preprocessed_image: PreprocessedImage,
    detection_result: GridDetectionResult,
    debug_dir: Path,
    prefix: str,
) -> Path:
    """Persist an overlay with detected grid lines and bounds."""
    debug_dir.mkdir(parents=True, exist_ok=True)

    debug_image = preprocessed_image.binary_image.convert("RGB")
    draw = ImageDraw.Draw(debug_image)

    for x in detection_result.vertical_lines:
        draw.line((x, 0, x, debug_image.height - 1), fill=(255, 0, 0), width=1)

    for y in detection_result.horizontal_lines:
        draw.line((0, y, debug_image.width - 1, y), fill=(0, 0, 255), width=1)

    draw.rectangle(
        (
            detection_result.left,
            detection_result.top,
            detection_result.right,
            detection_result.bottom,
        ),
        outline=(0, 255, 0),
        width=1,
    )

    debug_path = debug_dir / f"{prefix}_grid.png"
    debug_image.save(debug_path, format="PNG")
    return debug_path


def _find_line_positions(
    *,
    signal: list[float],
    grid_step: int,
) -> list[int]:
    """Find periodic grid line positions along one axis from a prepared signal."""
    if not signal or max(signal) <= 0:
        return []

    positions = _collect_periodic_peaks(signal=signal, grid_step=grid_step)
    return _extend_positions_to_edges(
        positions=positions,
        signal_length=len(signal),
        grid_step=grid_step,
    )


def _detect_axis_lines(
    *,
    signal: list[float],
    signal_length: int,
    min_grid_step: int,
    max_grid_step: int,
) -> list[int]:
    """Detect line positions for one axis when the other axis is user-provided."""
    grid_step = _estimate_grid_step(
        signal=signal,
        min_grid_step=min_grid_step,
        max_grid_step=max_grid_step,
    )
    grid_step = _refine_grid_step(
        signal=signal,
        grid_step=grid_step,
        min_grid_step=min_grid_step,
        max_grid_step=max_grid_step,
        promoted_refinement=False,
        max_step_drop=(
            DEFAULT_LARGE_STEP_REFINEMENT_DROP
            if grid_step >= 10
            else DEFAULT_SMALL_STEP_REFINEMENT_DROP
        ),
    )
    positions = _find_line_positions(signal=signal, grid_step=grid_step)
    return _stabilize_line_positions(
        signal=signal,
        positions=positions,
        grid_step=grid_step,
    )


def _estimate_grid_step(*, signal: list[float], min_grid_step: int, max_grid_step: int) -> int:
    """Estimate the repeating distance between grid lines using autocorrelation."""
    return _estimate_grid_step_from_scores(
        _score_grid_steps(
            signal=signal,
            min_grid_step=min_grid_step,
            max_grid_step=max_grid_step,
        )
    )


def _score_grid_steps(
    *,
    signal: list[float],
    min_grid_step: int,
    max_grid_step: int,
) -> list[tuple[int, float]]:
    """Return autocorrelation scores for every candidate grid step."""
    centered_signal = [value - (sum(signal) / len(signal)) for value in signal]
    max_allowed_step = min(max_grid_step, len(signal) - 1)

    return [
        (
            grid_step,
            sum(
                centered_signal[index] * centered_signal[index + grid_step]
                for index in range(len(signal) - grid_step)
            ),
        )
        for grid_step in range(min_grid_step, max_allowed_step + 1)
    ]


def _estimate_grid_step_from_scores(step_scores: list[tuple[int, float]]) -> int:
    """Pick the highest-scoring grid step from an autocorrelation table."""
    return max(step_scores, key=lambda item: item[1])[0]


def _harmonize_grid_steps(vertical_step: int, horizontal_step: int) -> tuple[int, int]:
    """Make X/Y grid steps consistent when one axis falls onto a small harmonic."""
    smaller_step = min(vertical_step, horizontal_step)
    larger_step = max(vertical_step, horizontal_step)

    if smaller_step < larger_step * DEFAULT_STEP_SIMILARITY_RATIO:
        return larger_step, larger_step

    return vertical_step, horizontal_step


def _promote_step_towards_reference(
    *,
    step_scores: list[tuple[int, float]],
    reference_step: int,
) -> int:
    """Promote a harmonic small step to a nearby larger step with comparable score."""
    best_score = max(score for _, score in step_scores)
    promoted_candidates = [
        step
        for step, score in step_scores
        if score >= best_score * DEFAULT_PROMOTION_SCORE_RATIO
    ]
    promoted_step = min(
        promoted_candidates,
        key=lambda step: (abs(step - reference_step), -step),
    )
    return promoted_step


def _refine_grid_step(
    *,
    signal: list[float],
    grid_step: int,
    min_grid_step: int,
    max_grid_step: int,
    promoted_refinement: bool,
    max_step_drop: int,
) -> int:
    """Prefer a smaller nearby step only when it preserves signal quality and adds lines."""
    base_positions = _find_line_positions(signal=signal, grid_step=grid_step)
    base_mean = _mean_signal_at_positions(signal=signal, positions=base_positions)
    base_count = len(base_positions)
    base_gap_mad = _mean_absolute_gap_deviation(base_positions)
    qualifying_steps: list[int] = []

    lower_bound = max(min_grid_step, grid_step - max_step_drop)
    if grid_step >= DEFAULT_HARMONIC_REFINEMENT_STEP_MIN:
        lower_bound = max(
            min_grid_step,
            min(lower_bound, (grid_step // 2) - 1),
        )
    for candidate_step in range(grid_step - 1, lower_bound - 1, -1):
        candidate_positions = _find_line_positions(signal=signal, grid_step=candidate_step)
        if len(candidate_positions) < 2:
            continue

        candidate_mean = _mean_signal_at_positions(
            signal=signal,
            positions=candidate_positions,
        )
        candidate_gap_mad = _mean_absolute_gap_deviation(candidate_positions)
        if candidate_step >= grid_step * DEFAULT_REFINEMENT_REGULARITY_GUARD_RATIO:
            regularity_ratio = (
                DEFAULT_PROMOTED_REFINEMENT_REGULARITY_RATIO
                if promoted_refinement
                else DEFAULT_REFINEMENT_REGULARITY_RATIO
            )
            regularity_delta = (
                DEFAULT_PROMOTED_REFINEMENT_REGULARITY_DELTA
                if promoted_refinement
                else DEFAULT_REFINEMENT_REGULARITY_DELTA
            )
            regularity_limit = max(
                base_gap_mad * regularity_ratio,
                base_gap_mad + regularity_delta,
            )
            if candidate_gap_mad > regularity_limit:
                continue
        if (
            candidate_mean >= base_mean
            and len(candidate_positions) > base_count
        ):
            qualifying_steps.append(candidate_step)
            continue

        if (
            promoted_refinement
            and candidate_mean >= base_mean * DEFAULT_PROMOTED_REFINEMENT_MEAN_RATIO
            and len(candidate_positions) > base_count
        ):
            qualifying_steps.append(candidate_step)
            continue

        if (
            grid_step >= DEFAULT_HARMONIC_REFINEMENT_STEP_MIN
            and candidate_step <= grid_step * 0.6
            and candidate_mean >= base_mean * DEFAULT_HARMONIC_REFINEMENT_MEAN_RATIO
            and len(candidate_positions) >= base_count * DEFAULT_HARMONIC_REFINEMENT_COUNT_RATIO
        ):
            qualifying_steps.append(candidate_step)
            continue

        if (
            candidate_mean >= base_mean * DEFAULT_REFINEMENT_MEAN_RATIO
            and len(candidate_positions) > base_count * DEFAULT_REFINEMENT_COUNT_RATIO
        ):
            qualifying_steps.append(candidate_step)

    if qualifying_steps:
        return max(min_grid_step, min(min(qualifying_steps), max_grid_step))

    return max(min_grid_step, min(grid_step, max_grid_step))


def _mean_signal_at_positions(*, signal: list[float], positions: list[int]) -> float:
    """Return the average signal value at detected line positions."""
    if not positions:
        return 0.0
    return sum(signal[position] for position in positions) / len(positions)


def _mean_absolute_gap_deviation(positions: list[int]) -> float:
    """Measure how evenly spaced the detected grid lines are."""
    if len(positions) < 3:
        return 0.0

    gaps = [right - left for left, right in zip(positions, positions[1:])]
    expected_gap = sum(gaps) / len(gaps)
    return sum(abs(gap - expected_gap) for gap in gaps) / len(gaps)


def _build_regular_positions_from_step(
    *,
    signal: list[float],
    signal_length: int,
    grid_step: int,
) -> list[int]:
    """Build a near-regular grid using the smaller trusted step and local refinement."""
    ratio = (signal_length - 1) / grid_step
    candidate_counts = sorted(
        {
            max(1, int(ratio)),
            max(1, round(ratio)),
            max(1, int(ratio) + 1),
        }
    )

    best_positions: list[int] = []
    best_score = float("-inf")
    for cell_count in candidate_counts:
        candidate_positions = _build_regular_positions_from_count(
            signal=signal,
            signal_length=signal_length,
            cell_count=cell_count,
        )
        candidate_score = _score_regularized_positions(
            signal=signal,
            positions=candidate_positions,
        )
        if candidate_score > best_score:
            best_positions = candidate_positions
            best_score = candidate_score

    if grid_step <= 7:
        best_positions = _fill_large_internal_gaps(
            signal=signal,
            positions=best_positions,
        )

    return best_positions


def _build_regular_positions_from_count(
    *,
    signal: list[float],
    signal_length: int,
    cell_count: int,
) -> list[int]:
    """Build a near-regular grid when the effective cell count is known."""
    if cell_count < 1:
        return []

    approx_step = (signal_length - 1) / cell_count
    refinement_window = max(1, round(approx_step / DEFAULT_REFINEMENT_WINDOW_DIVISOR))
    positions = [0]

    for index in range(1, cell_count):
        expected_position = round(index * (signal_length - 1) / cell_count)
        left = max(0, expected_position - refinement_window)
        right = min(signal_length - 1, expected_position + refinement_window)
        local_peak = max(range(left, right + 1), key=lambda current: signal[current])
        if local_peak <= positions[-1]:
            local_peak = min(signal_length - 1, positions[-1] + 1)
        positions.append(local_peak)

    positions.append(signal_length - 1)
    return positions


def _stabilize_line_positions(
    *,
    signal: list[float],
    positions: list[int],
    grid_step: int,
) -> list[int]:
    """Replace obviously irregular detections with a better near-regular grid."""
    if len(positions) < 3:
        return positions

    gaps = [right - left for left, right in zip(positions, positions[1:])]
    coverage_ratio = _position_coverage_ratio(positions=positions, signal_length=len(signal))
    positions = _fill_large_internal_gaps(signal=signal, positions=positions)
    gaps = [right - left for left, right in zip(positions, positions[1:])]
    coverage_ratio = _position_coverage_ratio(positions=positions, signal_length=len(signal))
    if (
        min(gaps) >= grid_step * DEFAULT_IRREGULAR_GAP_RATIO
        and coverage_ratio >= DEFAULT_MIN_COVERAGE_RATIO
    ):
        return positions

    current_count = len(positions) - 1
    expected_count = max(1, round((len(signal) - 1) / grid_step))
    candidate_count_values = {
        *range(max(1, current_count - 1), current_count + 2),
        *range(max(1, expected_count - 1), expected_count + 2),
    }
    if grid_step <= 7 and _has_tiny_false_line_gap(positions):
        regular_gap_count = _estimate_regular_cell_count_from_positions(
            positions=positions,
            signal_length=len(signal),
        )
        candidate_count_values.update(
            range(max(1, regular_gap_count - 1), regular_gap_count + 2)
        )
    candidate_counts = sorted(candidate_count_values)
    best_positions = positions
    best_score = _score_regularized_positions(signal=signal, positions=positions)

    for candidate_count in candidate_counts:
        candidate_positions = _build_regular_positions_from_count(
            signal=signal,
            signal_length=len(signal),
            cell_count=candidate_count,
        )
        candidate_score = _score_regularized_positions(
            signal=signal,
            positions=candidate_positions,
        )
        candidate_coverage = _position_coverage_ratio(
            positions=candidate_positions,
            signal_length=len(signal),
        )
        score_improvement_threshold = (
            DEFAULT_COVERAGE_RECOVERY_SCORE_IMPROVEMENT
            if coverage_ratio < DEFAULT_MIN_COVERAGE_RATIO
            and candidate_coverage > coverage_ratio
            else DEFAULT_REGULARIZATION_SCORE_IMPROVEMENT
        )
        if candidate_score > best_score * score_improvement_threshold:
            best_positions = candidate_positions
            best_score = candidate_score

    if grid_step <= 7:
        best_positions = _fill_large_internal_gaps(
            signal=signal,
            positions=best_positions,
        )

    return best_positions


def _fill_large_internal_gaps(*, signal: list[float], positions: list[int]) -> list[int]:
    """Insert missed grid lines inside unusually wide internal gaps."""
    if len(positions) < 4:
        return positions

    gaps = [right - left for left, right in zip(positions, positions[1:])]
    sorted_gaps = sorted(gaps)
    typical_gap = sorted_gaps[len(sorted_gaps) // 2]
    if typical_gap <= 0:
        return positions

    line_signals = [signal[position] for position in positions]
    sorted_line_signals = sorted(line_signals)
    typical_line_signal = sorted_line_signals[len(sorted_line_signals) // 2]
    min_insert_signal = typical_line_signal * DEFAULT_MISSING_INTERNAL_LINE_MIN_SIGNAL_RATIO
    refinement_window = max(1, round(typical_gap / DEFAULT_REFINEMENT_WINDOW_DIVISOR))

    filled_positions: list[int] = [positions[0]]
    for left, right, gap in zip(positions, positions[1:], gaps):
        missing_count = round(gap / typical_gap) - 1
        if (
            missing_count > 0
            and gap >= typical_gap * DEFAULT_MISSING_INTERNAL_LINE_GAP_RATIO
        ):
            for index in range(1, missing_count + 1):
                expected_position = round(left + gap * index / (missing_count + 1))
                search_left = max(left + 1, expected_position - refinement_window)
                search_right = min(right - 1, expected_position + refinement_window)
                if search_left > search_right:
                    continue

                local_peak = max(
                    range(search_left, search_right + 1),
                    key=lambda current: signal[current],
                )
                if signal[local_peak] >= min_insert_signal:
                    filled_positions.append(local_peak)
        filled_positions.append(right)

    return filled_positions


def _score_regularized_positions(*, signal: list[float], positions: list[int]) -> float:
    """Prefer positions that land on dark lines while keeping spacing regular."""
    mean_signal = _mean_signal_at_positions(signal=signal, positions=positions)
    gap_mad = _mean_absolute_gap_deviation(positions)
    coverage_ratio = _position_coverage_ratio(positions=positions, signal_length=len(signal))
    return (mean_signal * coverage_ratio) / (1 + gap_mad)


def _position_coverage_ratio(*, positions: list[int], signal_length: int) -> float:
    """Measure how much of the axis is covered by the detected sequence."""
    if len(positions) < 2 or signal_length <= 1:
        return 0.0

    return (positions[-1] - positions[0]) / (signal_length - 1)


def _estimate_regular_cell_count_from_positions(
    *,
    positions: list[int],
    signal_length: int,
) -> int:
    """Estimate cell count from the typical gap, ignoring tiny false-line gaps."""
    if len(positions) < 3:
        return max(1, len(positions) - 1)

    gaps = sorted(right - left for left, right in zip(positions, positions[1:]))
    median_gap = gaps[len(gaps) // 2]
    regular_gaps = [gap for gap in gaps if gap >= median_gap * DEFAULT_IRREGULAR_GAP_RATIO]
    if not regular_gaps:
        return max(1, len(positions) - 1)

    sorted_regular_gaps = sorted(regular_gaps)
    typical_gap = sorted_regular_gaps[min(len(sorted_regular_gaps) - 1, round(len(sorted_regular_gaps) * 0.75))]
    return max(1, round((signal_length - 1) / typical_gap))


def _has_tiny_false_line_gap(positions: list[int]) -> bool:
    """Return true when detected positions contain an implausibly small gap."""
    if len(positions) < 4:
        return False

    gaps = sorted(right - left for left, right in zip(positions, positions[1:]))
    median_gap = gaps[len(gaps) // 2]
    return gaps[0] < median_gap * DEFAULT_IRREGULAR_GAP_RATIO


def _collect_periodic_peaks(*, signal: list[float], grid_step: int) -> list[int]:
    """Collect refined peak positions that repeat with the estimated grid step."""
    max_signal = max(signal)
    if max_signal <= 0:
        return []

    refinement_window = max(1, grid_step // DEFAULT_REFINEMENT_WINDOW_DIVISOR)
    best_score = float("-inf")
    best_positions: list[int] = []

    for offset in range(grid_step):
        raw_positions: list[int] = []
        position = offset
        while position < len(signal):
            left = max(0, position - refinement_window)
            right = min(len(signal) - 1, position + refinement_window)
            local_peak = max(range(left, right + 1), key=lambda index: signal[index])
            raw_positions.append(local_peak)
            position += grid_step

        unique_positions = _deduplicate_close_positions(raw_positions)
        filtered_positions = [
            position
            for position in unique_positions
            if signal[position] >= max_signal * DEFAULT_MIN_PEAK_RATIO
        ]

        score = sum(signal[position] for position in filtered_positions)
        if score > best_score:
            best_score = score
            best_positions = filtered_positions

    return best_positions


def _deduplicate_close_positions(positions: list[int]) -> list[int]:
    """Remove nearly identical neighbor positions produced during local refinement."""
    if not positions:
        return []

    unique_positions = [positions[0]]
    for position in positions[1:]:
        if abs(position - unique_positions[-1]) > 1:
            unique_positions.append(position)
    return unique_positions


def _extend_positions_to_edges(
    *,
    positions: list[int],
    signal_length: int,
    grid_step: int,
) -> list[int]:
    """Add missing boundary lines when edge gaps match the regular grid step."""
    if len(positions) < 3:
        return positions

    extended_positions = list(positions)
    left_gap = extended_positions[0]
    right_gap = (signal_length - 1) - extended_positions[-1]

    if _looks_like_missing_edge_gap(left_gap, grid_step) and _looks_like_missing_edge_gap(
        right_gap, grid_step
    ):
        extended_positions.insert(0, 0)
        extended_positions.append(signal_length - 1)
        return extended_positions

    if (
        extended_positions[0] == 0
        and _looks_like_single_missing_edge_gap(right_gap, grid_step)
    ):
        extended_positions.append(signal_length - 1)
        return extended_positions

    if (
        extended_positions[-1] == signal_length - 1
        and _looks_like_single_missing_edge_gap(left_gap, grid_step)
    ):
        extended_positions.insert(0, 0)

    if (
        extended_positions[0] != 0
        and _looks_like_single_missing_edge_gap(left_gap, grid_step)
    ):
        extended_positions.insert(0, 0)

    if (
        extended_positions[-1] != signal_length - 1
        and _looks_like_single_missing_edge_gap(right_gap, grid_step)
    ):
        extended_positions.append(signal_length - 1)

    if (
        extended_positions[-1] != signal_length - 1
        and grid_step <= 7
        and signal_length >= 100
        and _looks_like_small_grid_missing_edge_gap(right_gap, grid_step)
    ):
        extended_positions.append(signal_length - 1)

    if (
        extended_positions[0] != 0
        and grid_step <= 7
        and signal_length >= 100
        and _looks_like_small_grid_missing_edge_gap(left_gap, grid_step)
    ):
        extended_positions.insert(0, 0)

    return extended_positions


def _looks_like_missing_edge_gap(gap: int, grid_step: int) -> bool:
    """Check whether an edge gap is close enough to one regular cell step."""
    return (
        grid_step * DEFAULT_EDGE_GAP_RATIO_MIN
        <= gap
        <= grid_step * DEFAULT_EDGE_GAP_RATIO_MAX
    )


def _looks_like_single_missing_edge_gap(gap: int, grid_step: int) -> bool:
    """Check whether a single boundary is missing by roughly one regular step."""
    return (
        grid_step * DEFAULT_SINGLE_EDGE_GAP_RATIO_MIN
        <= gap
        <= grid_step * DEFAULT_SINGLE_EDGE_GAP_RATIO_MAX
    )


def _looks_like_small_grid_missing_edge_gap(gap: int, grid_step: int) -> bool:
    """Check whether a cropped small-grid image lost a partial border."""
    return grid_step * 0.35 <= gap <= grid_step * DEFAULT_EDGE_GAP_RATIO_MAX
