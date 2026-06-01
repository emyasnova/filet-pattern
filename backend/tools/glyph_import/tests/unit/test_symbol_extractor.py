from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw

from src.services.image_loader import load_image
from src.services.image_preprocessor import preprocess_image
from src.services.symbol_extractor import extract_symbols


def test_extract_symbols_saves_crops_debug_and_manifest(tmp_path: Path) -> None:
    source_path = tmp_path / "sheet.png"
    _create_two_symbol_image(source_path)

    loaded_image = load_image(source_path)
    preprocessed_image = preprocess_image(loaded_image, denoise=False)

    symbols, binary_debug_path, overlay_debug_path, manifest_path = extract_symbols(
        loaded_image=loaded_image,
        preprocessed_image=preprocessed_image,
        output_dir=tmp_path / "input" / "extracted",
        debug_dir=tmp_path / "input" / "debug",
        manifests_dir=tmp_path / "output" / "manifests",
        min_symbol_width=8,
        min_symbol_height=8,
        min_symbol_area=64,
        crop_padding=1,
    )

    assert len(symbols) == 2
    assert [symbol.index for symbol in symbols] == [1, 2]
    assert symbols[0].bounds.left < symbols[1].bounds.left
    assert all(symbol.output_path.exists() for symbol in symbols)
    assert all(symbol.output_path.suffix == ".png" for symbol in symbols)
    assert binary_debug_path.exists()
    assert overlay_debug_path.exists()
    assert manifest_path.exists()

    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert payload["source_image"] == str(source_path.resolve())
    assert payload["source_format"] == "png"
    assert payload["extracted_count"] == 2
    assert payload["debug"]["binary_image"] == str(binary_debug_path)
    assert payload["debug"]["overlay_image"] == str(overlay_debug_path)
    assert [item["index"] for item in payload["symbols"]] == [1, 2]


def test_extract_symbols_groups_sheet1_into_alphabet_symbols(tmp_path: Path) -> None:
    source_path = Path(__file__).resolve().parents[2] / "input" / "raw" / "sheet1.jpg"
    loaded_image = load_image(source_path)
    preprocessed_image = preprocess_image(loaded_image)

    symbols, _, _, manifest_path = extract_symbols(
        loaded_image=loaded_image,
        preprocessed_image=preprocessed_image,
        output_dir=tmp_path / "input" / "extracted",
        debug_dir=tmp_path / "input" / "debug",
        manifests_dir=tmp_path / "output" / "manifests",
    )

    assert len(symbols) == 26
    assert symbols[0].width > 100
    assert symbols[-1].height > 100
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert payload["extracted_count"] == 26


def test_extract_symbols_keeps_padding_around_sheet1_lower_row_symbols(tmp_path: Path) -> None:
    source_path = Path(__file__).resolve().parents[2] / "input" / "raw" / "sheet1.jpg"
    loaded_image = load_image(source_path)
    preprocessed_image = preprocess_image(loaded_image)

    symbols, _, _, _ = extract_symbols(
        loaded_image=loaded_image,
        preprocessed_image=preprocessed_image,
        output_dir=tmp_path / "input" / "extracted",
        debug_dir=tmp_path / "input" / "debug",
        manifests_dir=tmp_path / "output" / "manifests",
    )

    assert symbols[20].bounds.left == 169
    assert symbols[20].bounds.right == 331
    assert symbols[21].bounds.left == 346
    assert symbols[21].bounds.right == 500
    assert symbols[23].bounds.left == 93
    assert symbols[24].bounds.left == 263


def test_extract_symbols_expands_bounds_when_ink_touches_crop_edge(tmp_path: Path) -> None:
    source_path = Path(__file__).resolve().parents[2] / "input" / "raw" / "sheet1.jpg"
    loaded_image = load_image(source_path)
    preprocessed_image = preprocess_image(loaded_image)

    symbols, _, _, _ = extract_symbols(
        loaded_image=loaded_image,
        preprocessed_image=preprocessed_image,
        output_dir=tmp_path / "input" / "extracted",
        debug_dir=tmp_path / "input" / "debug",
        manifests_dir=tmp_path / "output" / "manifests",
    )

    assert symbols[0].bounds.right == 153
    assert symbols[4].bounds.left == 557
    assert symbols[10].bounds.left == 10
    assert symbols[13].bounds.right == 688
    assert symbols[23].bounds.left == 93


def _create_two_symbol_image(path: Path) -> None:
    image = Image.new("L", (60, 24), 255)
    draw = ImageDraw.Draw(image)
    draw.rectangle((4, 4, 18, 18), outline=0, width=2)
    draw.line((4, 11, 18, 11), fill=0, width=2)
    draw.rectangle((34, 3, 52, 19), outline=0, width=2)
    draw.line((43, 3, 43, 19), fill=0, width=2)
    image.save(path, format="PNG")
