from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

from src.config import AppConfig
from src.domain.models import ExtractionOptions
from src.pipelines.extraction_pipeline import run_extraction_pipeline


def test_run_extraction_pipeline_returns_artifacts(tmp_path: Path) -> None:
    config = AppConfig.from_project_root(tmp_path)
    source_path = tmp_path / "input" / "raw" / "sheet.png"
    source_path.parent.mkdir(parents=True, exist_ok=True)
    _create_two_symbol_image(source_path)

    result = run_extraction_pipeline(
        input_path=source_path,
        config=config,
        options=ExtractionOptions(
            denoise=False,
            min_symbol_width=8,
            min_symbol_height=8,
            min_symbol_area=64,
            crop_padding=1,
        ),
    )

    assert result.loaded_image.path == source_path.resolve()
    assert len(result.symbols) == 2
    assert result.binary_debug_path == config.input_debug_dir / "sheet_extraction_binary.png"
    assert result.overlay_debug_path == config.input_debug_dir / "sheet_extraction_overlay.png"
    assert result.manifest_path == config.manifests_dir / "manifest.json"
    assert result.binary_debug_path.exists()
    assert result.overlay_debug_path.exists()
    assert result.manifest_path.exists()
    assert all(symbol.output_path.parent == config.extracted_dir for symbol in result.symbols)


def test_run_extraction_pipeline_auto_thresholds_light_sheet2(tmp_path: Path) -> None:
    config = AppConfig.from_project_root(tmp_path)
    source_path = Path(__file__).resolve().parents[2] / "input" / "raw" / "sheet2.jpg"

    result = run_extraction_pipeline(
        input_path=source_path,
        config=config,
        options=ExtractionOptions(),
    )

    assert result.options.threshold == 170
    assert len(result.symbols) == 13
    assert result.manifest_path.exists()


def test_run_extraction_pipeline_auto_thresholds_sheet3_full_height(tmp_path: Path) -> None:
    config = AppConfig.from_project_root(tmp_path)
    source_path = Path(__file__).resolve().parents[2] / "input" / "raw" / "sheet3.jpg"

    result = run_extraction_pipeline(
        input_path=source_path,
        config=config,
        options=ExtractionOptions(),
    )

    assert result.options.threshold == 190
    assert len(result.symbols) == 13
    assert min(symbol.height for symbol in result.symbols) >= 110


def _create_two_symbol_image(path: Path) -> None:
    image = Image.new("L", (60, 24), 255)
    draw = ImageDraw.Draw(image)
    draw.rectangle((4, 4, 18, 18), outline=0, width=2)
    draw.line((4, 11, 18, 11), fill=0, width=2)
    draw.rectangle((34, 3, 52, 19), outline=0, width=2)
    draw.line((43, 3, 43, 19), fill=0, width=2)
    image.save(path, format="PNG")
