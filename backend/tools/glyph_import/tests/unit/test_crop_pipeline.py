from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

from src.config import AppConfig
from src.domain.models import CropOptions
from src.pipelines.crop_pipeline import run_batch_crop_pipeline, run_crop_pipeline


def test_run_crop_pipeline_returns_artifacts(tmp_path: Path) -> None:
    config = AppConfig.from_project_root(tmp_path)
    source_path = tmp_path / "input" / "raw" / "scheme.png"
    source_path.parent.mkdir(parents=True, exist_ok=True)
    _create_scheme_with_caption(source_path)

    result = run_crop_pipeline(
        input_path=source_path,
        config=config,
        options=CropOptions(denoise=False, crop_padding=1),
    )

    assert result.loaded_image.path == source_path.resolve()
    assert result.output_path == config.prepared_dir / "scheme.png"
    assert result.overlay_debug_path == config.input_debug_dir / "scheme_crop_overlay.png"
    assert result.output_path.exists()
    assert result.overlay_debug_path.exists()
    assert (result.width, result.height) == (83, 63)


def test_run_batch_crop_pipeline_processes_supported_files(tmp_path: Path) -> None:
    config = AppConfig.from_project_root(tmp_path)
    input_dir = tmp_path / "input" / "raw"
    input_dir.mkdir(parents=True, exist_ok=True)
    _create_scheme_with_caption(input_dir / "a.png")
    _create_scheme_with_caption(input_dir / "b.jpg")
    (input_dir / "ignore.txt").write_text("skip", encoding="utf-8")

    summary = run_batch_crop_pipeline(
        input_dir=input_dir,
        config=config,
        options=CropOptions(denoise=False),
    )

    assert summary.input_dir == input_dir.resolve()
    assert summary.processed_count == 2
    assert summary.success_count == 2
    assert summary.failure_count == 0
    assert (config.prepared_dir / "a.png").exists()
    assert (config.prepared_dir / "b.png").exists()


def test_run_batch_crop_pipeline_reports_item_errors(tmp_path: Path) -> None:
    config = AppConfig.from_project_root(tmp_path)
    input_dir = tmp_path / "input" / "raw"
    input_dir.mkdir(parents=True, exist_ok=True)
    _create_scheme_with_caption(input_dir / "ok.png")
    (input_dir / "bad.jpg").write_bytes(b"not-a-real-jpg")

    summary = run_batch_crop_pipeline(
        input_dir=input_dir,
        config=config,
        options=CropOptions(denoise=False),
    )

    assert summary.processed_count == 2
    assert summary.success_count == 1
    assert summary.failure_count == 1
    assert any(not item.success and item.input_path.name == "bad.jpg" for item in summary.items)


def _create_scheme_with_caption(path: Path) -> None:
    image = Image.new("RGB", (130, 110), "white")
    draw = ImageDraw.Draw(image)
    left, top, right, bottom = 20, 16, 100, 76
    step = 10
    for x in range(left, right + 1, step):
        draw.line((x, top, x, bottom), fill="black", width=1)
    for y in range(top, bottom + 1, step):
        draw.line((left, y, right, y), fill="black", width=1)
    draw.rectangle((42, 28, 58, 44), fill="black")
    draw.rectangle((72, 48, 88, 64), fill="black")
    draw.text((24, 92), "Created by Stitchboard", fill="black")
    image.save(path)
