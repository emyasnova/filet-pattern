from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image, ImageDraw

from src.domain.models import LoadedImage, PreprocessedImage, ImageFormat
from src.services.grid_detector import (
    GridDetectionError,
    _estimate_regular_cell_count_from_positions,
    _extend_positions_to_edges,
    _fill_large_internal_gaps,
    _harmonize_grid_steps,
    _promote_step_towards_reference,
    _refine_grid_step,
    _stabilize_line_positions,
    detect_grid,
    save_grid_debug_image,
)


def test_detect_grid_finds_bounds_and_size() -> None:
    preprocessed_image = _build_preprocessed_grid(
        width=20,
        height=16,
        vertical_lines=[2, 7, 12, 17],
        horizontal_lines=[3, 8, 13],
    )

    result = detect_grid(preprocessed_image)

    assert result.left == 0
    assert result.top == 0
    assert result.right == 19
    assert result.bottom == 15
    assert result.vertical_lines == (2, 7, 12, 17)
    assert result.horizontal_lines == (3, 8, 13)
    assert result.column_count == 3
    assert result.row_count == 2


def test_detect_grid_uses_expected_grid_size_when_provided() -> None:
    preprocessed_image = _build_preprocessed_grid(
        width=21,
        height=16,
        vertical_lines=[0, 5, 10, 15, 20],
        horizontal_lines=[0, 5, 10, 15],
    )

    result = detect_grid(
        preprocessed_image,
        expected_columns=4,
        expected_rows=3,
    )

    assert result.vertical_lines == (0, 5, 10, 15, 20)
    assert result.horizontal_lines == (0, 5, 10, 15)
    assert result.column_count == 4
    assert result.row_count == 3


def test_detect_grid_saves_debug_visualization(tmp_path: Path) -> None:
    preprocessed_image = _build_preprocessed_grid(
        width=20,
        height=16,
        vertical_lines=[2, 7, 12, 17],
        horizontal_lines=[3, 8, 13],
    )
    result = detect_grid(preprocessed_image)

    debug_path = save_grid_debug_image(
        preprocessed_image=preprocessed_image,
        detection_result=result,
        debug_dir=tmp_path,
        prefix="grid_case",
    )

    assert debug_path == tmp_path / "grid_case_grid.png"
    assert debug_path.exists()


def test_detect_grid_rejects_image_without_enough_lines() -> None:
    image = Image.new("L", (10, 10), color=255)
    draw = ImageDraw.Draw(image)
    draw.line((4, 0, 4, 9), fill=0, width=1)
    draw.line((0, 5, 9, 5), fill=0, width=1)

    preprocessed_image = _wrap_binary_image(image)

    with pytest.raises(GridDetectionError, match="vertical grid lines"):
        detect_grid(preprocessed_image)


def test_harmonize_grid_steps_promotes_half_step_to_shared_larger_step() -> None:
    vertical_step, horizontal_step = _harmonize_grid_steps(4, 9)

    assert vertical_step == 9
    assert horizontal_step == 9


def test_extend_positions_to_edges_adds_missing_border_lines() -> None:
    positions = _extend_positions_to_edges(
        positions=[7, 15, 23, 31, 38, 46, 54, 61, 69, 77, 84, 92, 100, 107, 115, 123, 131],
        signal_length=139,
        grid_step=8,
    )

    assert positions[0] == 0
    assert positions[-1] == 138


def test_extend_positions_to_edges_adds_single_missing_right_border_line() -> None:
    positions = _extend_positions_to_edges(
        positions=[0, 11, 23, 34, 44, 50, 61, 74, 85, 96, 106, 116, 126, 130, 140, 150],
        signal_length=160,
        grid_step=10,
    )

    assert positions[-1] == 159


def test_extend_positions_to_edges_adds_missing_top_border_line() -> None:
    positions = _extend_positions_to_edges(
        positions=[8, 15, 22, 28, 35],
        signal_length=147,
        grid_step=7,
    )

    assert positions[0] == 0


def test_extend_positions_to_edges_adds_partial_borders_on_small_grid() -> None:
    positions = _extend_positions_to_edges(
        positions=[3, 10, 17, 23, 30, 37, 44, 51, 58, 64, 71, 78, 85, 92, 98, 105, 112, 119, 125, 132, 139, 142],
        signal_length=146,
        grid_step=7,
    )

    assert positions[0] == 0
    assert positions[-1] == 145


def test_estimate_regular_cell_count_ignores_tiny_false_line_gaps() -> None:
    positions = [4, 10, 17, 24, 30, 37, 44, 49, 52, 58, 64, 71, 78, 84, 91, 98, 104, 110, 112, 118, 124, 130]

    cell_count = _estimate_regular_cell_count_from_positions(
        positions=positions,
        signal_length=134,
    )

    assert cell_count == 19


def test_fill_large_internal_gaps_restores_missed_line() -> None:
    signal = [0.0 for _ in range(134)]
    positions = [0, 7, 14, 21, 27, 34, 42, 47, 54, 61, 68, 75, 82, 89, 96, 107, 114, 121, 127, 133]
    for position in positions:
        signal[position] = 80.0
    signal[101] = 90.0

    filled_positions = _fill_large_internal_gaps(signal=signal, positions=positions)

    assert filled_positions == [0, 7, 14, 21, 27, 34, 42, 47, 54, 61, 68, 75, 82, 89, 96, 101, 107, 114, 121, 127, 133]


def test_stabilize_line_positions_restores_missed_line_with_regular_medium_step() -> None:
    signal = [0.0 for _ in range(56)]
    positions = [0, 10, 20, 35, 45, 55]
    for position in positions:
        signal[position] = 80.0
    signal[30] = 90.0

    stabilized_positions = _stabilize_line_positions(
        signal=signal,
        positions=positions,
        grid_step=10,
    )

    assert stabilized_positions == [0, 10, 20, 30, 35, 45, 55]


def test_promote_step_towards_reference_prefers_nearby_large_candidate() -> None:
    promoted_step = _promote_step_towards_reference(
        step_scores=[
            (4, 100.0),
            (7, 82.0),
            (8, 79.0),
            (9, 77.0),
            (10, 74.0),
        ],
        reference_step=9,
    )

    assert promoted_step == 9


def test_refine_grid_step_prefers_smaller_step_when_it_adds_lines_without_losing_quality() -> None:
    source_path = next(p for p in Path("input/raw").iterdir() if p.stem == "С")
    loaded_image = LoadedImage(
        path=source_path.resolve(),
        image_format=ImageFormat.JPG,
        content=source_path.read_bytes(),
    )
    preprocessed_image = _preprocess_loaded_image(loaded_image)
    signal = [
        sum(
            255 - preprocessed_image.grayscale_image.getpixel((x, y))
            for y in range(preprocessed_image.grayscale_image.height)
        )
        / preprocessed_image.grayscale_image.height
        for x in range(preprocessed_image.grayscale_image.width)
    ]

    refined_step = _refine_grid_step(
        signal=signal,
        grid_step=11,
        min_grid_step=4,
        max_grid_step=24,
        promoted_refinement=False,
        max_step_drop=3,
    )

    assert refined_step == 8


def test_detect_grid_matches_known_real_file_sizes() -> None:
    expected_sizes = {
        "A": (22, 19),
        "C": (16, 19),
        "B": (18, 19),
        "D": (17, 19),
        "F": (19, 19),
        "J": (16, 19),
        "P": (20, 19),
        "А": (17, 15),
        "С": (16, 19),
    }

    for char, expected_size in expected_sizes.items():
        source_path = next(p for p in Path("input/raw").iterdir() if p.stem == char)
        loaded_image = LoadedImage(
            path=source_path.resolve(),
            image_format=ImageFormat.JPG,
            content=source_path.read_bytes(),
        )
        preprocessed_image = _preprocess_loaded_image(loaded_image)

        result = detect_grid(preprocessed_image)

        assert (result.column_count, result.row_count) == expected_size


def _build_preprocessed_grid(
    *,
    width: int,
    height: int,
    vertical_lines: list[int],
    horizontal_lines: list[int],
) -> PreprocessedImage:
    image = Image.new("L", (width, height), color=255)
    draw = ImageDraw.Draw(image)

    for x in vertical_lines:
        draw.line((x, 0, x, height - 1), fill=0, width=1)

    for y in horizontal_lines:
        draw.line((0, y, width - 1, y), fill=0, width=1)

    return _wrap_binary_image(image)


def _wrap_binary_image(image: Image.Image) -> PreprocessedImage:
    path = Path("synthetic-grid.png").resolve()
    loaded_image = LoadedImage(path=path, image_format=ImageFormat.PNG, content=b"")
    return PreprocessedImage(
        source_path=loaded_image.path,
        grayscale_image=image.copy(),
        denoised_image=image.copy(),
        binary_image=image.copy(),
    )


def _preprocess_loaded_image(loaded_image: LoadedImage) -> PreprocessedImage:
    from src.services.image_preprocessor import preprocess_image

    return preprocess_image(loaded_image)
